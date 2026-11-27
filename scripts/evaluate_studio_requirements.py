"""Verify the synthetic input provenance and rerun the Studio's partition analysis.

Run from the repo root with `python -m scripts.evaluate_studio_requirements`.
"""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path

from eqcr.quantum_example import ticket_example
from eqcr.studio_cases import case_requirements, ticket_requirement_cases
from eqcr.quantum_tradeoff import Architecture, Preferences, QualityAllocation, Ranking, analyze, group_index


def verify_record(case: dict, run: Path) -> None:
    location = run / case["id"].lower()
    request = (location / "request.json").read_bytes()
    response = json.loads((location / "response.json").read_text(encoding="utf-8"))
    text = response["message"]["content"]
    if (sha256(request).hexdigest() != case["request_sha256"]
            or sha256(text.encode("utf-8")).hexdigest() != case["response_sha256"]
            or (response["model"], response["created_at"], response["eval_count"], response["done_reason"])
            != (case["model"], case["created_at"], case["generated_tokens"], "stop")):
        raise ValueError(f"Request or response provenance mismatch for {case['id']}.")
    raw = json.loads(text)
    schema = json.loads(request)["format"]["properties"]
    fields = ("text", "component_ids", "characteristic", "quote")
    for proposal in case["proposals"]:
        key = f"r{proposal['proposal_number']}"
        original = raw[key]
        expected_kind = "FR" if schema[key]["properties"]["characteristic"]["enum"] == [None] else "NFR"
        if proposal["kind"] != expected_kind or any(original[field] != proposal[field] for field in fields):
            raise ValueError(f"Proposal text or mapping modified in {case['id']}/{proposal['proposal_number']}.")


def snapshot(architecture: Architecture, weights: Preferences, ranking: Ranking) -> dict:
    result = analyze(architecture, weights, ranking=ranking)
    topology = {item.id: item for item in result.feasible}
    for candidate in topology.values():
        q = group_index(candidate.groups)
        if (any(q[rule.left] == q[rule.right] for rule in architecture.keep_apart)
                or any(q[e.source] != q[e.target] for e in architecture.interactions if e.local_transaction)
                or any(len({q[member] for member in store.members}) > 1 for store in architecture.stores
                       if store.policy == "KEEP_SHARED")):
            raise ValueError(f"Hard constraint violated by {candidate.id}.")
    winner = result.ranked[0]
    return {
        "partitions": result.enumerated, "feasible": len(topology), "pareto": [c.id for c in result.ranked],
        "winner": winner.id, "groups": winner.groups, "vector": winner.vector, "score": winner.score(weights),
        "candidates": topology,
    }


def simulate_allocations(architecture: Architecture) -> Architecture:
    data = architecture.model_dump()
    for item, raw in zip(architecture.requirements, data["requirements"], strict=True):
        if suggestion := item.model_suggestion:
            label, quote = suggestion
            raw["quality_allocations"] = [QualityAllocation(characteristic=label, source_quote=quote,
                                                            component_ids=item.component_ids)]
    return Architecture.model_validate(data)


def evaluate(cases: dict) -> list[dict]:
    settings: list[tuple[Ranking, Preferences]] = [("SYNC_FIRST", Preferences()), ("CHARACTERISTIC_FIRST", Preferences()),
                                                   ("WEIGHTED", Preferences()), ("WEIGHTED", Preferences(characteristics=4))]
    baseline = ticket_example()
    cohorts = {key: case_requirements(case) for key, case in cases.items()}
    cohorts["ALL"] = [item for pack in cohorts.values() for item in pack]
    results = []
    for ranking, weights in settings:
        before = snapshot(baseline, weights, ranking)
        before_candidates = before.pop("candidates")
        for name, items in cohorts.items():
            draft = Architecture.model_validate({**baseline.model_dump(), "requirements": [*baseline.requirements, *items]})
            loaded = snapshot(draft, weights, ranking)
            if before_candidates != loaded.pop("candidates") or loaded != before:
                raise ValueError(f"Draft requirements changed the solver for {name}.")
            what_if = simulate_allocations(draft)
            after = snapshot(what_if, weights, ranking)
            after_candidates = after.pop("candidates")
            if before_candidates.keys() != after_candidates.keys():
                raise ValueError(f"Quality allocations modified hard constraints for {name}.")
            results.append({
                "case": name, "ranking": ranking, "weights": weights.vector, "inputs": len(items),
                "unconfirmed_equals_baseline": True, "simulated_allocations": [item.id for item in items if item.model_suggestion],
                "before": before, "after_what_if": after,
                "before_winner_after_vector": after_candidates[before["winner"]].vector,
                "before_winner_after_score": after_candidates[before["winner"]].score(weights),
                "changed_candidate_vectors": sum(item.vector != before_candidates[key].vector
                                                 for key, item in after_candidates.items()),
            })
    return results


def sensitivity_checks(cases: dict) -> dict:
    base = ticket_example().model_dump()
    drafted = [item for case in cases.values() for item in case_requirements(case)]
    driver_id = "LLM-RECOVERY-07"
    isolated = [*base["keep_apart"], {"left": "REPORT", "right": "ROUTE", "basis": "Sensitivity test only"}]
    results = {}
    for key, requirements, rules in (
        ("omit_backlog_latency", [item for item in drafted if item.id != driver_id], base["keep_apart"]),
        ("only_backlog_latency", [item for item in drafted if item.id == driver_id], base["keep_apart"]),
        ("enforce_report_isolation", drafted, isolated),
    ):
        model = Architecture.model_validate({**base, "requirements": [*base["requirements"], *requirements], "keep_apart": rules})
        results[key] = snapshot(simulate_allocations(model), Preferences(), "WEIGHTED")
        results[key].pop("candidates")
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-run-dir", type=Path)
    args = parser.parse_args()
    cases = ticket_requirement_cases()
    if args.raw_run_dir:
        for case in cases.values():
            verify_record(case, args.raw_run_dir)
    print(json.dumps({"raw_provenance_verified": args.raw_run_dir is not None,
                      "quality_status": "NOT_MEASURED", "results": evaluate(cases),
                      "sensitivity": sensitivity_checks(cases)}, indent=2))


if __name__ == "__main__":
    main()
