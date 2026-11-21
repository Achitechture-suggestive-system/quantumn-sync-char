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
        counts[violated] += 1

    minimal: list[frozenset[int]] = []
    for violations in sorted(counts, key=lambda items: (len(items), sorted(items))):
        if not any(smaller <= violations for smaller in minimal):
            minimal.append(violations)

    # A feasible partition after a subset-minimal repair must violate exactly that repair's rules.
    return tuple(Repair(tuple(rules[index] for index in sorted(items)), counts[items]) for items in minimal)


def simulate_repair(architecture: Architecture, repair: Repair) -> Architecture:
    """Return an isolated what-if model for the existing analyzer."""
    data = architecture.model_dump(mode="json")
    removed = set()
    for rule in repair.rules:
        if rule.kind == "LOCAL_TRANSACTION":
            data["interactions"][rule.index]["local_transaction"] = False
        elif rule.kind == "KEEP_SHARED":
            data["stores"][rule.index]["policy"] = "SPLITTABLE"
        else:
            removed.add(rule.index)
    data["keep_apart"] = [rule for index, rule in enumerate(data["keep_apart"]) if index not in removed]
    return Architecture.model_validate(data)
