"""Run the prepared quality case or a structured package and export reproducible reports."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
import tempfile

from eqcr.drawio_export import architecture_graph_to_drawio
from eqcr.pipeline import validate_project_package
from eqcr.project_io import load_project_json
from eqcr.quality_worked_example import get_quality_worked_example
from eqcr.storage import make_export_zip, verify_export_zip


def _canonical(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def _sha(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _summary(artifacts: dict) -> dict:
    report = artifacts["quality_decomposition"]
    return {
        "selected_display_candidate": artifacts["partitions"]["selected_candidate_id"],
        "objective_minimum": artifacts["partitions"]["objective_minimum"],
        "candidate_count": report["candidate_count"],
        "candidates": [{
            "candidate_id": item["candidate_id"], "groups": item["groups"], "cost_vector": item["cost_vector"],
            "modes": {edge["id"]: edge["mode"] for edge in item["interaction_matrix"]},
        } for item in report["candidates"]],
    }


def export_quality_run(project: dict, directory: Path, *, before: dict | None = None) -> dict:
    artifacts = validate_project_package(project)
    report = artifacts.get("quality_decomposition")
    if not report:
        raise ValueError("The project has no quality_decomposition configuration.")
    repeat = validate_project_package(project)
    if _canonical(artifacts) != _canonical(repeat):
        raise ValueError("A repeated run on the same inputs produced different artifacts.")
    output = _summary(artifacts)
    comparison = {"after": output}
    if before is not None:
        comparison = {
            "provenance": "PREPARED_WORKED_EXAMPLE",
            "changed": "Explicit source statement and timing citation for I-RESERVE",
            "before": _summary(validate_project_package(before)),
            "after": output,
        }
    bundle = make_export_zip(artifacts)
    verify_export_zip(bundle)
    directory = directory.resolve()
    if directory.exists():
        raise FileExistsError(f"Choose a new output directory: {directory}")
    directory.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".quality-run-", dir=directory.parent) as workspace:
        results = Path(workspace) / "results"
        results.mkdir()
        files = {
            "input.json": _canonical(project),
            "quality-decomposition.json": _canonical(report),
            "validation.json": _canonical(artifacts["validation_report"]),
            "before-after.json": _canonical(comparison),
            "artifacts.zip": bundle,
        }
        if before is not None:
            files["input-before.json"] = _canonical(before)
        for item in report["candidates"]:
            key = item["candidate_id"]
            graph = item["architecture_graph"]
            files[f"{key}-architecture.json"] = _canonical(graph)
            files[f"{key}-architecture.drawio"] = architecture_graph_to_drawio(graph).encode("utf-8")
        files["reproducibility.json"] = _canonical({
            "python_version": sys.version.split()[0], "solver": artifacts["metadata"]["optimizer_backend"],
            "policy": report["policy"], "same_input_artifacts_match": True,
            "bundle_verified": True, "measurement_status": report["measurement_status"],
            "files_sha256": {name: _sha(content) for name, content in files.items()},
        })
        for name, content in files.items():
            (results / name).write_bytes(content)
        results.rename(directory)
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, help="Structured project JSON containing quality_decomposition.")
    parser.add_argument("--output", type=Path, required=True, help="New directory for the reports.")
    options = parser.parse_args()
    project = load_project_json(options.project.read_bytes()) if options.project else get_quality_worked_example()
    before = None if options.project else get_quality_worked_example(explicit_wait_evidence=False)
    print(json.dumps(export_quality_run(project, options.output, before=before), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
