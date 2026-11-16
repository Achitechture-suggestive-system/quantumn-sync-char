"""CP-SAT correctness checks against an independent small partition oracle."""

from copy import deepcopy
from decimal import Decimal
from itertools import product
import math
import random

import pytest

from eqcr.cpsat_optimizer import analyze_weight_sensitivity, optimize_with_cpsat
from eqcr.fixture import get_fixture
from eqcr.models import Constraint
from eqcr.pipeline import _optimize, run_pipeline


def _canonical_partition(labels, responsibility_ids):
    groups = {}
    for responsibility_id, label in zip(responsibility_ids, labels, strict=True):
        groups.setdefault(label, []).append(responsibility_id)
    return tuple(sorted(tuple(sorted(group)) for group in groups.values()))


def _independent_oracle(responsibility_ids, constraints):
    partitions = {
        _canonical_partition(labels, responsibility_ids)
        for labels in product(range(len(responsibility_ids)), repeat=len(responsibility_ids))
    }
    feasible = []
    for groups in partitions:
        owner = {item: index for index, group in enumerate(groups) for item in group}
        cost = Decimal(0)
        valid = True
        for item in constraints:
            if not item.enabled:
                continue
            together = item.left == item.right or owner[item.left] == owner[item.right]
            violated = (item.relation == "MUST_LINK" and not together) or (
                item.relation == "CANNOT_LINK" and together
            )
            if item.hardness == "HARD" and violated:
                valid = False
                break
            if item.hardness == "SOFT" and violated:
                cost += Decimal(str(item.weight))
        if valid:
            feasible.append((groups, cost))
    if not feasible:
        return None, set()
    minimum = min(cost for _, cost in feasible)
    return minimum, {groups for groups, cost in feasible if cost == minimum}


def _constraint(identifier, relation, left, right, *, hardness="SOFT", weight=1.0):
    return Constraint.model_validate(
        {
            "id": identifier,
            "relation": relation,
            "left": left,
            "right": right,
            "hardness": hardness,
            "weight": weight,
            "origin": "WHAT_IF_POLICY",
            "rationale": "TEST_ONLY algorithm fixture.",
        }
    )


def _signature(groups):
    return tuple(sorted(tuple(sorted(group)) for group in groups))


def test_cpsat_matches_independent_oracle_for_seeded_small_instances():
    rng = random.Random(20261116)
    responsibility_ids = ["R1", "R2", "R3", "R4"]
    pairs = [(left, right) for index, left in enumerate(responsibility_ids) for right in responsibility_ids[index + 1 :]]

    for case_index in range(12):
        constraints = []
        for row_index in range(rng.randint(1, 8)):
            left, right = rng.choice(pairs)
            constraints.append(
                _constraint(
                    f"C{case_index}-{row_index}",
                    rng.choice(["MUST_LINK", "CANNOT_LINK"]),
                    left,
                    right,
                    hardness=rng.choice(["HARD", "SOFT", "SOFT"]),
                    weight=rng.choice([0.1, 0.2, 0.3, 1.0, 2.5]),
                )
            )
        expected_cost, expected_optima = _independent_oracle(responsibility_ids, constraints)
        result = optimize_with_cpsat(
            responsibility_ids,
            constraints,
            time_limit_seconds=5,
            max_optimal_candidates=100,
        )
        if expected_cost is None:
            assert result["result_status"] == "INFEASIBLE"
            assert result["feasible_candidate_count"] == 0
            assert all(item["constraint_ids"] for item in result["conflicts"])
        else:
            assert result["solver_status"] == "OPTIMAL"
            assert Decimal(str(result["objective_minimum"])) == expected_cost
            assert result["optimal_candidate_set_complete"] is True
            actual_optima = {_signature(item["groups"]) for item in result["optimal_candidates"]}
            assert actual_optima == expected_optima


def test_cpsat_preserves_decimal_weight_sum_without_binary_float_rounding():
    ids = ["R1", "R2", "R3"]
    constraints = [
        _constraint("H1", "CANNOT_LINK", "R1", "R2", hardness="HARD"),
        _constraint("H2", "CANNOT_LINK", "R1", "R3", hardness="HARD"),
        _constraint("H3", "CANNOT_LINK", "R2", "R3", hardness="HARD"),
        _constraint("S1", "MUST_LINK", "R1", "R2", weight=0.1),
        _constraint("S2", "MUST_LINK", "R1", "R3", weight=0.2),
    ]
    result = optimize_with_cpsat(ids, constraints)
    assert result["objective_minimum"] == 0.3
    assert result["solver_parameters"]["objective_weight_scale"] == 10


def test_cpsat_reports_transitive_hard_conflict_explanation():
    constraints = [
        _constraint("ML-12", "MUST_LINK", "R1", "R2", hardness="HARD"),
        _constraint("ML-23", "MUST_LINK", "R2", "R3", hardness="HARD"),
        _constraint("CL-13", "CANNOT_LINK", "R1", "R3", hardness="HARD"),
    ]
    result = optimize_with_cpsat(["R1", "R2", "R3"], constraints)
    assert result["result_status"] == "INFEASIBLE"
    assert result["conflicts"] == [
        {
            "pair": ["R1", "R3"],
            "constraint_ids": ["ML-12", "ML-23", "CL-13"],
            "relations": ["CANNOT_LINK", "MUST_LINK"],
            "status": "INFEASIBLE",
            "reason": "Cannot-link endpoints are connected by the must-link transitive closure.",
            "explanation_scope": "INCLUSION_MINIMAL_MUST_LINK_PATH_PLUS_CANNOT_LINK",
        }
    ]


def test_cpsat_is_deterministic_under_fixed_seed_and_single_worker():
    constraints = [
        _constraint("S1", "MUST_LINK", "R1", "R2", weight=1.0),
        _constraint("S2", "CANNOT_LINK", "R2", "R3", weight=1.0),
    ]
    first = optimize_with_cpsat(["R1", "R2", "R3", "R4"], constraints, random_seed=23)
    second = optimize_with_cpsat(["R1", "R2", "R3", "R4"], constraints, random_seed=23)
    assert first["selected_groups"] == second["selected_groups"]
    assert [_signature(item["groups"]) for item in first["optimal_candidates"]] == [
        _signature(item["groups"]) for item in second["optimal_candidates"]
    ]


def test_weight_sensitivity_records_explicit_policy_weight_changes():
    constraints = [
        _constraint("PREFER_TOGETHER", "MUST_LINK", "R1", "R2", weight=1.0),
        _constraint("PREFER_APART", "CANNOT_LINK", "R1", "R2", weight=2.0),
    ]
    analysis = analyze_weight_sensitivity(
        ["R1", "R2"],
        constraints,
        {
            "declared_weights": {},
            "reversed_preference": {"PREFER_TOGETHER": 2.0, "PREFER_APART": 1.0},
        },
    )
    declared, reversed_case = analysis["scenarios"]
    assert declared["optimal_candidates"][0]["groups"] == [["R1"], ["R2"]]
    assert reversed_case["optimal_candidates"][0]["groups"] == [["R1", "R2"]]
    assert analysis["analysis_status"] == "SCENARIO_COMPARISON_ONLY"


def test_weight_sensitivity_rejects_unknown_or_hard_constraint_updates():
    constraints = [_constraint("H1", "MUST_LINK", "R1", "R2", hardness="HARD")]
    try:
        analyze_weight_sensitivity(["R1", "R2"], constraints, {"bad": {"H1": 2.0}})
    except ValueError as exc:
        assert "unknown/non-soft constraints" in str(exc)
    else:
        raise AssertionError("Sensitivity analysis must reject edits to hard or unknown constraints.")


def test_cpsat_large_case_reports_multiple_optima_and_incomplete_enumeration_explicitly():
    result = optimize_with_cpsat(
        [f"R{index:02d}" for index in range(9)],
        [],
        time_limit_seconds=5,
        max_optimal_candidates=20,
    )
    assert result["solver_backend"] == "CP_SAT"
    assert result["solver_status"] == "OPTIMAL"
    assert result["bell_number_expected"] == 21147
    assert result["optimal_candidate_count"] == 20
    assert result["optimal_candidate_set_complete"] is False
    assert result["candidate_reporting_scope"] == "OPTIMAL_CANDIDATES_ONLY"
    assert result["feasible_candidate_count"] is None
    assert result["feasible_candidates"] == []


def test_pipeline_uses_cpsat_above_exhaustive_cap_and_traces_reported_optima():
    fixture = get_fixture()
    for index in range(7, 10):
        added = deepcopy(fixture["responsibilities"][index - 7])
        added.update({"id": f"R{index}", "name": f"Test responsibility {index}"})
        fixture["responsibilities"].append(added)

    artifacts = run_pipeline(
        fixture,
        constraints_override=[],
        execution_mode="P2_TEST_ONLY",
    )
    assert artifacts["metadata"]["optimizer_backend"] == "CP_SAT"
    assert artifacts["partitions"]["feasible_candidate_count"] is None
    assert len(artifacts["partitions"]["reported_candidates"]) == 200
    assert artifacts["partitions"]["optimal_candidate_set_complete"] is False
    assert artifacts["traceability"]["assertions"]["all_feasible_candidates_are_linked"] is None
    assert artifacts["traceability"]["assertions"]["all_reported_partition_candidates_are_linked"] is True
    assert artifacts["validation_report"]["assertions"]["traceability_graph_well_formed"] is True
    assert artifacts["validation_report"]["assertions"]["bell_6_count_is_203"] is None


def test_exhaustive_and_cpsat_agree_on_small_instance_without_changing_default_backend():
    ids = ["R1", "R2", "R3", "R4"]
    constraints = [
        _constraint("M1", "MUST_LINK", "R1", "R2", weight=2.5),
        _constraint("C1", "CANNOT_LINK", "R2", "R3", weight=0.3),
        _constraint("M2", "MUST_LINK", "R3", "R4", hardness="HARD"),
    ]
    exhaustive = _optimize(ids, constraints)
    cpsat = optimize_with_cpsat(ids, constraints)
    assert exhaustive.get("solver_backend", "EXHAUSTIVE_ENUMERATOR") == "EXHAUSTIVE_ENUMERATOR"
    assert Decimal(str(exhaustive["objective_minimum"])) == Decimal(str(cpsat["objective_minimum"]))
    assert {
        _signature(item["groups"]) for item in exhaustive["optimal_candidates"]
    } == {_signature(item["groups"]) for item in cpsat["optimal_candidates"]}


@pytest.mark.parametrize("time_limit", [math.nan, math.inf, -math.inf, 0, -1])
def test_cpsat_rejects_non_finite_or_non_positive_time_limits(time_limit):
    with pytest.raises(ValueError, match="finite positive"):
        optimize_with_cpsat(["R1"], [], time_limit_seconds=time_limit)


@pytest.mark.parametrize(
    ("candidate_limit", "seed"),
    [(0, 0), (True, 0), (1, -1), (1, 2**31), (1, True)],
)
def test_cpsat_rejects_invalid_enumeration_limits_and_seeds(candidate_limit, seed):
    with pytest.raises(ValueError):
        optimize_with_cpsat(["R1"], [], max_optimal_candidates=candidate_limit, random_seed=seed)
