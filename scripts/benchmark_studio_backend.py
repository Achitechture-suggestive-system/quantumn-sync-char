"""Run bounded synthetic Studio scale experiments, separate from semantic/model evaluation."""

import argparse
from datetime import datetime, timezone
from hashlib import sha256
from importlib.metadata import version
import json
from pathlib import Path
import platform
import sys
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from eqcr import storage
from eqcr.quantum_tradeoff import Preferences, analyze, group_index, hard_constraints
from eqcr.studio_scale_cases import scale_case


def main():
    parser = argparse.ArgumentParser(description="Prepared scale workloads; no LLM or semantic accuracy")
    parser.add_argument("--sizes", nargs="+", type=int, default=[9, 12, 20, 50])
    parser.add_argument("--family", nargs="+", choices=["chain", "pressure"], default=["chain", "pressure"])
    parser.add_argument("--seconds", type=float, default=8)
    arguments = parser.parse_args()
    identifier = f"scale-{uuid4().hex}"
    folder = storage.ARTIFACT_ROOT / "quantum-studio" / "scale" / identifier
    folder.mkdir(parents=True, exist_ok=False)
    records = []
    for family in arguments.family:
        for size in arguments.sizes:
            model = scale_case(size, family)
            result = analyze(model, Preferences(), time_limit_seconds=arguments.seconds)
            valid = all(not rule.violated_by(group_index(candidate.groups)) for candidate in result.feasible for rule in hard_constraints(model))
            record = {"size": size, "family": family, "input_provenance": "PREPARED_FIXTURE", "output_provenance": "DETERMINISTIC_TRANSFORMATION",
                      "search": result.search, "candidate_count_lower_bound": len(result.feasible), "hard_constraints_satisfied": valid,
                      "best_found_score": min(item.score(Preferences()) for item in result.feasible), "enumerated": result.enumerated,
                      "candidates": [{"id": item.id, "groups": item.groups, "vector": item.vector} for item in result.feasible]}
            (folder / f"{family}-{size}-input.json").write_text(model.model_dump_json(indent=2), encoding="utf-8")
            (folder / f"{family}-{size}-result.json").write_text(json.dumps(record, indent=2), encoding="utf-8")
            records.append(record)
            print(json.dumps({key: record[key] for key in ("size", "family", "candidate_count_lower_bound", "hard_constraints_satisfied", "best_found_score")}
                             | {"primary_status": result.search.get("primary_status"), "seconds": result.search.get("elapsed_seconds")}), flush=True)
    report = {"id": identifier, "recorded_at": datetime.now(timezone.utc).isoformat(), "python": sys.version, "platform": platform.platform(),
              "ortools": version("ortools"), "arguments": vars(arguments), "input_provenance": "PREPARED_FIXTURE", "model_inference": False,
              "semantic_accuracy": None, "quality_measurement_status": "NOT_MEASURED", "records": records,
              "code_hashes": {path.name: sha256(path.read_bytes()).hexdigest() for path in [Path(__file__),
                              Path(__file__).parents[1] / "eqcr" / "studio_cpsat.py", Path(__file__).parents[1] / "eqcr" / "studio_scale_cases.py"]}}
    (folder / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({"run_id": identifier, "records": len(records)}))


if __name__ == "__main__":
    main()
