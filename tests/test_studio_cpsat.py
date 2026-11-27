"""Exact arithmetic oracles for a bounded solver; synthesized inputs are PREPARED_FIXTURE."""

import pytest
from ortools.sat.python import cp_model

from eqcr.pipeline import _partitions
from eqcr.quantum_example import ticket_example
from eqcr.quantum_tradeoff import Architecture, Preferences, _evaluate, analyze, component_profiles, group_index, hard_constraints, ranking_key
from eqcr.studio_cpsat import analyze_cpsat, compile_partition, hard_blocks, lexicographic
from eqcr.studio_uncertainty import conservative_order, score_bounds
from eqcr.studio_conflicts import minimal_repairs, simulate_repair


def synthetic_model(size):
    return Architecture.model_validate({
        "components": [{"id": f"C{index:02d}", "name": f"Prepared component {index}", "characteristics": [f"Trait {index // 3}"]}
                       for index in range(size)],
        "interactions": [{"source": f"C{index:02d}", "target": f"C{index+1:02d}", "mode": "SYNC" if index % 3 != 2 else "ASYNC", "weight": 1 + index % 2}
                         for index in range(size - 1)],
        "stores": [{"id": f"D{index:02d}", "name": f"Prepared store {index}", "members": [f"C{index:02d}", f"C{index+1:02d}"],
                    "policy": "SPLITTABLE", "basis": "Prepared benchmark policy"} for index in range(0, size - 1, 3)],
        "keep_apart": [{"left": "C00", "right": f"C{size-1:02d}", "basis": "Prepared isolation policy"}] if size > 1 else [],
    })


@pytest.mark.parametrize("variant", ["ticket", "unknown", "no_labels", "must_link"])
def test_every_small_cp_partition_has_exact_python_vector_and_uncertainty_bounds(variant):
    data = ticket_example().model_dump(mode="json")
    if variant == "unknown":
        for edge in data["interactions"]:
            edge["mode"] = "UNKNOWN"
    elif variant == "no_labels":
        for item in data["components"]:
            item["characteristics"] = []
            item["characteristic_requirements"] = {}
    elif variant == "must_link":
        data["interactions"][1]["local_transaction"] = True
    model = Architecture.model_validate(data)
    weights = Preferences(sync=7, data=0, async_seam=4, characteristics=3)
    compiled = compile_partition(model, weights)
    expected = {frozenset(frozenset(group) for group in item.groups): item for item in analyze(model, weights).feasible}
    seen = set()

    class Collector(cp_model.CpSolverSolutionCallback):
        def on_solution_callback(self):
            groups = compiled.partition(self.value)
            signature = frozenset(frozenset(group) for group in groups)
            assert signature not in seen
            seen.add(signature)
            reference = expected[signature]
            assert tuple(self.value(axis) for axis in compiled.axes) == reference.vector
            bounds = score_bounds(model, reference, weights)
            assert (self.value(compiled.lower), self.value(compiled.upper)) == (bounds.lower, bounds.upper)

    solver = cp_model.CpSolver()
    solver.parameters.enumerate_all_solutions = True
    solver.parameters.num_search_workers = 1
    assert solver.solve(compiled.model, Collector()) == cp_model.OPTIMAL
    assert seen == set(expected)


@pytest.mark.parametrize("ranking", ["WEIGHTED", "SYNC_FIRST", "CHARACTERISTIC_FIRST"])
@pytest.mark.parametrize("weights", [Preferences(), Preferences(sync=0, data=0, async_seam=0, characteristics=0)])
def test_requested_primary_objective_matches_exhaustive_costs_including_zero_weights(ranking, weights):
    model = ticket_example()
    reference = analyze(model, weights, ranking=ranking)
    result = analyze_cpsat(model, weights, ranking=ranking, time_limit_seconds=2)
    expected = min(ranking_key(item, weights, ranking)[:-2] for item in reference.frontier)
    actual = min(ranking_key(item, weights, ranking)[:-2] for item in result.feasible)
    assert expected == actual and result.search["optimality_proven"]
    assert result.enumerated is None and not result.search["complete_feasible_set"]
    assert result.search["frontier_scope"] == "FOUND_POOL"


def test_robust_objective_is_global_upper_bound_cost_and_not_nominal_frontier_only():
    data = ticket_example().model_dump(mode="json")
    for edge in data["interactions"]:
        edge["mode"] = "UNKNOWN"
    model = Architecture.model_validate(data)
    weights = Preferences()
    expected = conservative_order(model, analyze(model, weights).feasible, weights)[0]
    result = analyze_cpsat(model, weights, conservative=True, time_limit_seconds=2)
    actual = conservative_order(model, result.feasible, weights)[0]
    assert score_bounds(model, actual, weights).upper == score_bounds(model, expected, weights).upper
    assert result.search["optimality_proven"] and result.search["conservative"]


def test_nine_components_use_studio_backend_and_match_bell9_reference_objective():
    model = synthetic_model(9)
    weights = Preferences()
    rules, profiles = hard_constraints(model), component_profiles(model)
    references = [item for index, groups in enumerate(_partitions([item.id for item in model.components]))
                  if (item := _evaluate(model, profiles, rules, groups, index)) is not None]
    result = analyze(model, weights, time_limit_seconds=3)
    assert result.search["backend"] == "CP-SAT"
    assert min(item.score(weights) for item in result.feasible) == min(item.score(weights) for item in references)
    assert result.search["optimality_proven"]
    assert all(not any(rule.violated_by(group_index(item.groups)) for rule in rules) for item in result.feasible)
    assert len(result.feasible) >= 3


def test_50_component_limit_has_feasible_candidates_even_when_no_search_time_remains():
    model = synthetic_model(50)
    result = analyze(model, Preferences(), time_limit_seconds=1e-9)
    assert len(result.feasible) >= 3 and result.enumerated is None
    assert result.search["status"] == "FEASIBLE" and result.search["primary_status"] == "NOT_RUN"
    assert not result.search["optimality_proven"]
    for item in result.feasible:
        assert set(group_index(item.groups)) == {component.id for component in model.components}
        assert all(not rule.violated_by(group_index(item.groups)) for rule in hard_constraints(model))
    data = model.model_dump(mode="json")
    data["components"].append({"id": "OVER_LIMIT", "name": "Over limit"})
    with pytest.raises(ValueError):
        Architecture.model_validate(data)


def test_large_infeasibility_is_proved_by_hard_closure_and_preserves_protected_policies():
    data = synthetic_model(12).model_dump(mode="json")
    data["interactions"][0].update(mode="SYNC", local_transaction=True, basis="Prepared atomic policy", review_policy={"protected": True})
    data["keep_apart"].append({"left": "C00", "right": "C01", "basis": "Prepared contradictory isolation"})
    model = Architecture.model_validate(data)
    result = analyze(model, Preferences())
    assert result.search["status"] == "INFEASIBLE" and not result.feasible
    assert result.search["infeasibility_proof"] == "MUST_LINK_CLOSURE_CONFLICTS_WITH_KEEP_APART"
    assert model.interactions[0].review_policy.protected and model.interactions[0].local_transaction


def test_lexicographic_encoding_rejects_unsafe_coefficients_without_rounding():
    with pytest.raises(ValueError, match="integer"):
        lexicographic([(1, 2**60), (2, 2**60)])


@pytest.mark.parametrize("mode", ["SYNC", "ASYNC"])
def test_restricted_reviewed_mode_sets_match_python_bounds(mode):
    data = ticket_example().model_dump(mode="json")
    source = data["requirements"][0]
    source_model = Architecture.model_validate(data).requirements[0]
    data["interactions"][0].update(mode="UNKNOWN", cases=[{"condition": name, "mode": mode, "source_id": source["id"],
                                                         "source_digest": source_model.input_digest(), "source_quote": source["text"]}
                                                        for name in ("Prepared normal", "Prepared exceptional")])
    model = Architecture.model_validate(data)
    result = analyze_cpsat(model, Preferences(), conservative=True, time_limit_seconds=1)
    assert result.search["optimality_proven"]
    for item in result.feasible:
        assert score_bounds(model, item, Preferences()).lower == score_bounds(model, item, Preferences()).upper


def test_large_repairs_respect_protection_cost_and_subset_minimality_without_count_claims():
    data = synthetic_model(12).model_dump(mode="json")
    data["interactions"][0].update(mode="SYNC", local_transaction=True, basis="Prepared atomic rule",
                                     review_policy={"protected": True, "change_cost": 1})
    data["keep_apart"].append({"left": "C00", "right": "C01", "basis": "Prepared separate rule", "review_policy": {"change_cost": 7}})
    model = Architecture.model_validate(data)
    rules = hard_constraints(model)
    repairs = minimal_repairs(model, rules)
    assert repairs and all(not rule.protected for repair in repairs for rule in repair.rules)
    assert repairs[0].review_cost == 7 and repairs[0].cost_optimality_proven
    assert all(repair.feasible is None for repair in repairs)
    for repair in repairs:
        assert analyze(simulate_repair(model, repair), Preferences(), time_limit_seconds=.1).feasible
        for rule in repair.rules:
            kept = [item for item in rules if item not in repair.rules or item == rule]
            assert hard_blocks([item.id for item in model.components], kept)[1]
    data["keep_apart"][-1]["review_policy"]["protected"] = True
    protected_conflict = Architecture.model_validate(data)
    assert minimal_repairs(protected_conflict, hard_constraints(protected_conflict)) == ()


def test_large_ui_renders_partial_counts_three_choices_and_records_solver_scope(tmp_path, monkeypatch):
    from pathlib import Path
    from streamlit.testing.v1 import AppTest
    from eqcr import storage, studio_canvas
    from eqcr.studio_scale_cases import scale_case

    monkeypatch.setattr(storage, "ARTIFACT_ROOT", tmp_path)
    captured = []
    monkeypatch.setattr(studio_canvas, "render_board", lambda **kwargs: captured.append(kwargs))
    view = AppTest.from_file(Path(__file__).parents[1] / "app.py", default_timeout=30)
    view.session_state.architecture = scale_case(12)
    view.session_state.studio_analyzed = True
    view.run()
    assert not view.exception
    assert any(item.label == "Khả thi đã tìm" for item in view.metric)
    assert not any(item.label == "Đã xét" for item in view.metric)
    assert len(captured[-1]["plans"]) >= 3
    next(item for item in view.button if item.label.startswith("Chọn A")).click().run()
    assert not view.exception
    record = view.session_state.studio_last_review
    assert record["enumerated"] is None and record["search"]["frontier_scope"] == "FOUND_POOL"
    assert record["feasible"] is None and record["pareto"] is None and record["feasible_found"] >= 3
    assert not record["search"]["complete_feasible_set"] and record["input_provenance"] == "CONTAINS_PREPARED_FIXTURE_INPUT"
    assert all(item["pareto_scope"] == "FOUND_POOL" for item in record["comparison"])
    assert all(item["pareto"] is None for item in record["comparison"])


def test_large_infeasible_ui_finishes_with_bounded_policy_repairs(tmp_path, monkeypatch):
    from pathlib import Path
    from streamlit.testing.v1 import AppTest
    from eqcr import storage, studio_canvas

    monkeypatch.setattr(storage, "ARTIFACT_ROOT", tmp_path)
    monkeypatch.setattr(studio_canvas, "render_board", lambda **kwargs: None)
    data = synthetic_model(12).model_dump(mode="json")
    data["interactions"][0].update(local_transaction=True, basis="Prepared atomic rule")
    data["keep_apart"].append({"left": "C00", "right": "C01", "basis": "Prepared isolation rule"})
    view = AppTest.from_file(Path(__file__).parents[1] / "app.py", default_timeout=30)
    view.session_state.architecture = Architecture.model_validate(data)
    view.session_state.studio_analyzed = True
    view.run()
    assert not view.exception
    assert any("INFEASIBLE" in item.value for item in view.error)
    assert any("ít nhất" in item.value for item in view.markdown)


@pytest.mark.parametrize("protected", [False, True])
def test_bounded_repair_minimum_cost_matches_exhaustive_small_reference(protected):
    from eqcr.studio_cpsat_repair import bounded_repairs

    data = ticket_example().model_dump(mode="json")
    data["interactions"][0].update(mode="SYNC", local_transaction=True, basis="Prepared atomic rule",
                                     review_policy={"protected": protected, "change_cost": 7})
    data["keep_apart"].append({"left": "CREATE", "right": "ROUTE", "basis": "Prepared isolation", "review_policy": {"change_cost": 2}})
    model = Architecture.model_validate(data)
    rules = hard_constraints(model)
    reference = minimal_repairs(model, rules)
    actual = bounded_repairs(model, rules, time_limit_seconds=1)
    assert actual[0].review_cost == reference[0].review_cost and actual[0].cost_optimality_proven
    expected_sets = {frozenset(item.rules) for item in reference}
    assert all(frozenset(item.rules) in expected_sets for item in actual)


def test_solver_unknown_retains_validated_seeds_without_claiming_infeasibility_or_optimality(monkeypatch):
    original = cp_model.CpSolver

    class TimedOutSolver(original):
        def solve(self, model, *args):
            self.parameters.max_time_in_seconds = 1e-9
            return super().solve(model, *args)

    monkeypatch.setattr(cp_model, "CpSolver", TimedOutSolver)
    model = synthetic_model(12)
    result = analyze_cpsat(model, Preferences(), time_limit_seconds=1)
    assert result.search["primary_status"] == "UNKNOWN" and result.search["status"] == "FEASIBLE"
    assert result.feasible and not result.search["optimality_proven"]
    assert all(not rule.violated_by(group_index(item.groups)) for item in result.feasible for rule in hard_constraints(model))
