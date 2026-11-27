"""Live inference on already-known development cases; no semantic accuracy or reference labels."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from eqcr import storage
from eqcr.quantum_example import ticket_example
from eqcr.quantum_tradeoff import Architecture
from eqcr.studio_extraction import extract_proposals
from eqcr.studio_oracles import oracle_ticket_cases


def main():
    parser = argparse.ArgumentParser(description="Development-only live Ollama clause smoke; never independent evaluation")
    parser.add_argument("--model", default="qwen3:4b")
    parser.add_argument("--case", nargs="+", default=["OC-02", "OC-03", "OC-07", "OC-12"])
    arguments = parser.parse_args()
    cases = oracle_ticket_cases()
    if not 1 <= len(arguments.case) <= 8 or any(item not in cases for item in arguments.case):
        parser.error("Choose 1..8 existing development case IDs.")
    data = ticket_example().model_dump(mode="json")
    source_ids = []
    for identifier in arguments.case:
        source_id = f"DEV-{identifier}"
        source_ids.append(source_id)
        data["requirements"].append({"id": source_id, "kind": "NFR", "text": cases[identifier]["text"]})
    model = Architecture.model_validate(data)
    run = extract_proposals(model, source_ids, "QUALITY", arguments.model)
    folder = storage.ARTIFACT_ROOT / "quantum-studio" / "extractions" / run["id"]
    (folder / "architecture.json").write_text(model.model_dump_json(indent=2), encoding="utf-8")
    report = {"purpose": "DEVELOPMENT_ONLY_NOT_HELD_OUT", "input_provenance": "PREPARED_FIXTURE",
              "proposal_provenance": "LLM_PROPOSAL", "run_id": run["id"], "prompt_version": run["prompt_version"],
              "model": run["model"], "model_digest": run["model_digest"], "cases": arguments.case,
              "independent_labels": "UNAVAILABLE", "semantic_accuracy": None, "optimizer_mutated": False,
              "script_sha256": sha256(Path(__file__).read_bytes()).hexdigest(),
              "proposals": [{"source_id": item["source_id"], "disposition": item["payload"].get("disposition"),
                             "characteristic": item["payload"].get("characteristic"), "scope": item["payload"].get("component_ids"),
                             "issues": item["issues"]} for item in run["proposals"]]}
    (folder / "development-check.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report))


if __name__ == "__main__":
    main()
