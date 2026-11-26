"""Explain hard-constraint conflicts and enumerate exact what-if repairs in Studio."""

from __future__ import annotations

from collections import Counter, deque
from dataclasses import dataclass
from itertools import combinations

from .pipeline import _partitions
from .quantum_tradeoff import Architecture, HardConstraint, group_index, hard_constraints


@dataclass(frozen=True)
class Conflict:
    separation: HardConstraint
    path: tuple[tuple[str, str, HardConstraint], ...]


@dataclass(frozen=True)
class Repair:
    rules: tuple[HardConstraint, ...]
    feasible: int

    @property
    def review_cost(self) -> int:
        return sum(rule.change_cost for rule in self.rules)


def conflict_witnesses(rules: tuple[HardConstraint, ...]) -> tuple[Conflict, ...]:
    """Find a shortest chain of mandatory co-location for each conflicting separation."""
    links: dict[str, list[tuple[str, HardConstraint]]] = {}
    for rule in rules:
        if rule.kind != "KEEP_APART":
            for a, b in combinations(rule.components, 2):
                links.setdefault(a, []).append((b, rule))
                links.setdefault(b, []).append((a, rule))

    conflicts = []
    for separation in rules:
        if separation.kind != "KEEP_APART":
            continue
        start, end = separation.components
        seen = {start}
        queue = deque([(start, ())])
        while queue:
            node, path = queue.popleft()
            if node == end:
                conflicts.append(Conflict(separation, path))
                break
            for neighbor, rule in links.get(node, []):
                if neighbor not in seen:
                    seen.add(neighbor)
                    queue.append((neighbor, (*path, (node, neighbor, rule))))
    return tuple(conflicts)


def minimal_repairs(architecture: Architecture, rules: tuple[HardConstraint, ...]) -> tuple[Repair, ...]:
    """A partition becomes feasible by relaxing every hard rule it violates."""
    counts = Counter()
    for groups in _partitions([component.id for component in architecture.components]):
        assignment = group_index(groups)
        violated = frozenset(index for index, rule in enumerate(rules) if rule.violated_by(assignment))
        if not violated:
            return ()
        if any(rules[index].protected for index in violated):
            continue
        counts[violated] += 1

    minimal: list[frozenset[int]] = []
    for violations in sorted(counts, key=lambda items: (len(items), sorted(items))):
        if not any(smaller <= violations for smaller in minimal):
            minimal.append(violations)

    # A feasible partition after a subset-minimal repair must violate exactly that repair's rules.
    repairs = [Repair(tuple(rules[index] for index in sorted(items)), counts[items]) for items in minimal]
    return tuple(sorted(repairs, key=lambda repair: (repair.review_cost, len(repair.rules),
                                                    tuple((rule.kind, rule.index) for rule in repair.rules))))


def simulate_repair(architecture: Architecture, repair: Repair) -> Architecture:
    """Return an isolated what-if model for the existing analyzer."""
    data = architecture.model_dump(mode="json")
    current = hard_constraints(architecture)
    if any(rule not in current or rule.protected for rule in repair.rules):
        raise ValueError("Cách sửa đã cũ hoặc tác động quy tắc được bảo vệ. Review chính sách trước khi sửa.")
    removed = set()
    for rule in repair.rules:
        if rule.kind == "LOCAL_TRANSACTION":
            data["interactions"][rule.index]["local_transaction"] = False
            data["interactions"][rule.index]["evidence"] = None
        elif rule.kind == "KEEP_SHARED":
            data["stores"][rule.index]["policy"] = "SPLITTABLE"
        else:
            removed.add(rule.index)
    data["keep_apart"] = [rule for index, rule in enumerate(data["keep_apart"]) if index not in removed]
    return Architecture.model_validate(data)


def enforce_protected_rules(before: Architecture, after: Architecture) -> None:
    """Guard all input/edit routes; removing protection requires its own reviewed policy revision."""
    def signature(rule):
        return rule.kind, frozenset(rule.components), rule.basis, rule.protected, rule.change_cost

    resulting = {signature(rule) for rule in hard_constraints(after)}
    if any(rule.protected and signature(rule) not in resulting for rule in hard_constraints(before)):
        raise ValueError("Thay đổi tác động quy tắc được bảo vệ. Mở Review chính sách ràng buộc và ghi quyết định trước.")


def review_rule_policy(architecture: Architecture, rule: HardConstraint, *, protected: bool, change_cost: int,
                       actor: str, rationale: str) -> tuple[Architecture, dict]:
    if not actor.strip() or not rationale.strip():
        raise ValueError("Điền người review và lý do thay đổi chính sách.")
    if rule not in hard_constraints(architecture):
        raise ValueError("Quy tắc đã đổi. Chọn lại quy tắc hiện hành.")
    data = architecture.model_dump(mode="json")
    collection = {"KEEP_APART": "keep_apart", "LOCAL_TRANSACTION": "interactions", "KEEP_SHARED": "stores"}[rule.kind]
    data[collection][rule.index]["review_policy"] = {"protected": protected, "change_cost": change_cost}
    changed = Architecture.model_validate(data)
    return changed, {"action": "HARD_RULE_POLICY_REVIEW", "actor": actor.strip(), "rationale": rationale.strip(),
                     "rule_kind": rule.kind, "rule_index": rule.index,
                     "before": architecture.model_dump(mode="json"), "after": changed.model_dump(mode="json")}


def apply_reviewed_repair(architecture: Architecture, repair: Repair, *, actor: str, rationale: str) -> tuple[Architecture, dict]:
    if not actor.strip() or not rationale.strip():
        raise ValueError("Điền người review và lý do áp dụng cách sửa.")
    if repair not in minimal_repairs(architecture, hard_constraints(architecture)):
        raise ValueError("Cách sửa đã cũ hoặc không thuộc tập sửa được phép. Phân tích lại xung đột.")
    changed = simulate_repair(architecture, repair)
    enforce_protected_rules(architecture, changed)
    return changed, {"action": "HARD_RULE_REPAIR_APPLIED", "actor": actor.strip(), "rationale": rationale.strip(),
                     "changes": [{"kind": rule.kind, "index": rule.index, "components": list(rule.components),
                                  "basis": rule.basis, "change_cost": rule.change_cost} for rule in repair.rules],
                     "review_cost": repair.review_cost, "feasible_after": repair.feasible,
                     "before": architecture.model_dump(mode="json"), "after": changed.model_dump(mode="json")}
