"""Bounds under explicit independent SYNC/ASYNC hypotheses, without probabilities."""

from __future__ import annotations

from dataclasses import dataclass

from .quantum_tradeoff import Architecture, Candidate, Interaction, Preferences, group_index


def cases_are_current(architecture: Architecture, edge: Interaction) -> bool:
    sources = {item.id: item for item in architecture.requirements}
    return bool(edge.cases) and all(
        case.source_id in sources
        and sources[case.source_id].input_digest() == case.source_digest
        and case.source_quote in sources[case.source_id].text for case in edge.cases
    )


def possible_modes(architecture: Architecture, edge: Interaction) -> set[str]:
    if edge.mode != "UNKNOWN":
        return {edge.mode}
    if cases_are_current(architecture, edge):
        return {case.mode for case in edge.cases}
    return {"SYNC", "ASYNC"}


@dataclass(frozen=True)
class ScoreBounds:
    lower: int
    upper: int
    unresolved_edges: int
    conditional_edges: int


def score_bounds(architecture: Architecture, candidate: Candidate, weights: Preferences) -> ScoreBounds:
    """Exact endpoints for a fixed partition under independent per-edge mode choices."""
    lower = upper = candidate.score(weights)
    unresolved = conditional = 0
    assignment = group_index(candidate.groups)
    for edge in architecture.interactions:
        if edge.mode != "UNKNOWN":
            continue
        conditional += int(cases_are_current(architecture, edge))
        unresolved += int(not cases_are_current(architecture, edge))
        crosses = assignment[edge.source] != assignment[edge.target]
        costs = [edge.weight * (weights.sync if mode == "SYNC" and crosses
                                else weights.async_seam if mode == "ASYNC" and not crosses else 0)
                 for mode in possible_modes(architecture, edge)]
        lower += min(costs)
        upper += max(costs)
    return ScoreBounds(lower, upper, unresolved, conditional)


def conservative_order(architecture: Architecture, candidates: tuple[Candidate, ...], weights: Preferences) -> tuple[Candidate, ...]:
    """Minimize the weighted upper bound over all hard-feasible partitions."""
    def key(candidate):
        bounds = score_bounds(architecture, candidate, weights)
        return bounds.upper, bounds.lower, len(candidate.groups), candidate.id

    return tuple(sorted(candidates, key=key))


def review_interaction_cases(architecture: Architecture, source: str, target: str, cases: list[dict], *,
                             actor: str, rationale: str) -> tuple[Architecture, dict]:
    if not actor.strip() or not rationale.strip():
        raise ValueError("Điền người review và căn cứ cho các điều kiện.")
    sources = {item.id: item for item in architecture.requirements}
    normalized = []
    for case in cases:
        requirement = sources.get(case.get("source_id"))
        quote = case.get("source_quote", "")
        if requirement is None or not quote.strip() or quote not in requirement.text:
            raise ValueError("Mỗi điều kiện cần nguồn có thật và đoạn trích nguyên văn.")
        normalized.append({**case, "source_digest": requirement.input_digest()})
    data = architecture.model_dump(mode="json")
    edge = next((item for item in data["interactions"] if (item["source"], item["target"]) == (source, target)), None)
    if edge is None or edge["local_transaction"]:
        raise ValueError("Chọn cạnh hiện có không bắt buộc giao dịch cục bộ. Muốn đổi quy tắc cứng cần review riêng.")
    if len(normalized) < 2:
        raise ValueError("Khai báo ít nhất hai điều kiện, kiểm tra cả trường hợp bình thường và lỗi.")
    edge.update(mode="UNKNOWN", cases=normalized)
    changed = Architecture.model_validate(data)
    return changed, {"action": "INTERACTION_CONDITIONS_REVIEW", "actor": actor.strip(), "rationale": rationale.strip(),
                     "source": source, "target": target, "cases": normalized,
                     "before": architecture.model_dump(mode="json"), "after": changed.model_dump(mode="json")}
