"""Independent, deliberately small oracle for the six-responsibility fixture."""

from copy import deepcopy
from itertools import product

from eqcr.fixture import get_fixture
from eqcr.pipeline import run_pipeline


def _canonical_partition(labels, items):
    groups = {}
    for item, label in zip(items, labels, strict=True):
        groups.setdefault(label, []).append(item)
    return tuple(sorted(tuple(sorted(group)) for group in groups.values()))


def _all_partitions_independently(items):
    # Enumerate every label assignment and collapse equivalent block labels.
    # This intentionally does not call the production restricted-growth generator.
    return {
        _canonical_partition(labels, items)
        for labels in product(range(len(items)), repeat=len(items))
    }


def _oracle_candidates(items, constraints):
    candidates = []
    for partition in _all_partitions_independently(items):
        cost = 0.0
        feasible = True
        for constraint in constraints:
            if not constraint.get("enabled", True):
                continue
            left, right = constraint["left"], constraint["right"]
            together = any(left in group and right in group for group in partition)
            violated = (
                constraint["relation"] == "MUST_LINK" and not together
            ) or (
                constraint["relation"] == "CANNOT_LINK" and together
            )
            if constraint["hardness"] == "HARD" and violated:
                feasible = False
                break
            if constraint["hardness"] == "SOFT" and violated:
                cost += constraint.get("weight", 1.0)
        if feasible:
            candidates.append((partition, cost))
    return candidates


def _signature(groups):
    return tuple(sorted(tuple(sorted(group)) for group in groups))


def test_independent_oracle_matches_baseline_conflict_and_correction():
    fixture = get_fixture()
    responsibility_ids = [item["id"] for item in fixture["responsibilities"]]

    baseline = run_pipeline(fixture)
    baseline_oracle = _oracle_candidates(responsibility_ids, fixture["constraints"])
    assert len(_all_partitions_independently(responsibility_ids)) == 203
    assert len(baseline_oracle) == baseline["partitions"]["feasible_candidate_count"]
    minimum = min(cost for _, cost in baseline_oracle)
    oracle_optima = {groups for groups, cost in baseline_oracle if cost == minimum}
    production_optima = {
        _signature(item["groups"]) for item in baseline["partitions"]["optimal_candidates"]
    }
    assert minimum == 0
    assert len(oracle_optima) == 10
    assert production_optima == oracle_optima

    contradictory_constraints = deepcopy(fixture["constraints"])
    contradictory_constraints.append(
        {
            "id": "H4",
            "relation": "MUST_LINK",
            "left": "R4",
            "right": "R6",
            "hardness": "HARD",
            "origin": "HUMAN_OVERRIDE",
            "enabled": True,
            "source_refs": [],
            "rationale": "Independent oracle conflict case.",
        }
    )
    assert _oracle_candidates(responsibility_ids, contradictory_constraints) == []
    conflict = run_pipeline(fixture, constraints_override=contradictory_constraints)
    assert conflict["validation_report"]["status"] == "INFEASIBLE"
    assert conflict["partitions"]["feasible_candidate_count"] == 0

    corrected_constraints = deepcopy(contradictory_constraints)
    next(item for item in corrected_constraints if item["id"] == "H3")["enabled"] = False
    corrected_oracle = _oracle_candidates(responsibility_ids, corrected_constraints)
    corrected = run_pipeline(fixture, constraints_override=corrected_constraints)
    assert len(corrected_oracle) == 5
    assert len(corrected_oracle) == corrected["partitions"]["feasible_candidate_count"]
    assert corrected["partitions"]["optimal_candidate_count"] == 5
    assert corrected["validation_report"]["status"] == "REVIEW_REQUIRED"
