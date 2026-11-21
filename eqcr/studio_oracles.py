"""Replay the authored Ticket Support test fixtures through the Studio model."""

from __future__ import annotations

from functools import cache
import json
from pathlib import Path

from .quantum_example import ticket_example
from .quantum_tradeoff import Analysis, Architecture, Preferences


REPLAY_MODES = {
    "draft": "Chỉ nạp nguồn",
    "oracle": "Áp dụng oracle",
    "saved_model": "Đầu ra Ollama đã lưu",
}


@cache
def oracle_ticket_cases() -> dict:
    path = Path(__file__).with_name("studio_demo") / "oracle_ticket_cases.json"
    return {case["id"]: case for case in json.loads(path.read_text(encoding="utf-8"))["cases"]}


def replay_architecture(case: dict, mode: str) -> Architecture:
    if mode not in REPLAY_MODES or (mode == "saved_model" and "saved_model" not in case):
        raise ValueError(f"Unsupported replay mode: {mode} for {case['id']}")
    data = ticket_example().model_dump(mode="json")
    case_id = case["id"]
    allocations = case["allocations"] if mode == "oracle" else []
    data["requirements"].extend({**item, "kind": "NFR"} for item in case["context"])
    data["requirements"].append({
        "id": case_id, "text": case["text"], "kind": "NFR" if case["kind"] == "NFR" else "UNSPECIFIED",
        "component_ids": list(dict.fromkeys(cid for item in allocations for cid in item["component_ids"])),
        "quality_allocations": allocations,
    })
    if mode != "draft":
        changes = case["saved_model"] if mode == "saved_model" else case
        source = "Ollama" if mode == "saved_model" else "Oracle"
        edges = {(edge["source"], edge["target"]): edge for edge in data["interactions"]}
        for relation in changes["relations"]:
            edge = edges[relation["source"], relation["target"]]
            quote = relation["quote"]
            if not quote or quote not in case["text"]:
                raise ValueError(f"Interaction replay has invalid source evidence: {case_id}")
            edge.update(mode=relation["mode"], local_transaction=relation["local_transaction"],
                        basis=f"{source} {case_id} · {quote}")
        for pair in changes["keep_apart"]:
            quote = pair["quote"]
            if not quote or quote not in case["text"]:
                raise ValueError(f"Isolation replay has invalid source evidence: {case_id}")
            data["keep_apart"].append({"left": pair["left"], "right": pair["right"], "basis": f"{source} {case_id} · {quote}"})
    return Architecture.model_validate(data)


def replay_outcome(analysis: Analysis) -> dict:
    leader = analysis.ranked[0] if analysis.ranked else None
    return {"feasible": len(analysis.feasible), "leader": leader.id if leader else None,
            "score": leader.score(Preferences()) if leader else None}


def matches_oracle(analysis: Analysis, expected: dict) -> bool:
    if any(expected[key] != value for key, value in replay_outcome(analysis).items()):
        return False
    if probe := expected.get("probe"):
        return any(item.id == probe["id"] and item.vector == tuple(probe["vector"]) for item in analysis.feasible)
    return True
