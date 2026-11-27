from itertools import combinations

from eqcr.studio_conflicts import Repair, conflict_witnesses, minimal_repairs, simulate_repair
from eqcr.studio_oracles import oracle_ticket_cases, replay_architecture
from eqcr.quantum_tradeoff import Architecture, Preferences, analyze, hard_constraints


def test_oc10_repairs_recover_both_outcomes_without_changing_the_original():
    model = replay_architecture(oracle_ticket_cases()["OC-10"], "oracle")
    rules = hard_constraints(model)
    [conflict] = conflict_witnesses(rules)
    assert conflict.separation.components == ("ROUTE", "COMPLETE")
    assert [(a, b, rule.kind) for a, b, rule in conflict.path] == [("ROUTE", "COMPLETE", "LOCAL_TRANSACTION")]

    repairs = minimal_repairs(model, rules)
    assert [(repair.rules[0].kind, repair.feasible) for repair in repairs] == [
        ("KEEP_APART", 10), ("LOCAL_TRANSACTION", 27),
    ]
    weights = Preferences()
    simulations = [simulate_repair(model, repair) for repair in repairs]
    assert simulations[1].interactions[-1].mode == "SYNC"
    for candidate, repair, top, cost in zip(simulations, repairs, ("P031", "P008"), (5, 16), strict=True):
        result = analyze(candidate, weights)
        assert len(result.feasible) == repair.feasible
        assert (result.ranked[0].id, result.ranked[0].score(weights)) == (top, cost)
    assert not analyze(model, weights).feasible


def test_transitive_and_independent_conflicts_return_every_minimal_repair():
    model = Architecture.model_validate({
        "components": [{"id": key, "name": f"Module {key}"} for key in "ABCDE"],
        "stores": [{"id": "DB", "name": "Shared DB", "members": ["A", "B"], "policy": "KEEP_SHARED", "basis": "Same store"}],
        "interactions": [
            {"source": "B", "target": "C", "mode": "SYNC", "local_transaction": True, "basis": "Local transaction one"},
            {"source": "D", "target": "E", "mode": "SYNC", "local_transaction": True, "basis": "Local transaction two"},
        ],
        "keep_apart": [{"left": "A", "right": "C", "basis": "Isolate A/C"},
                       {"left": "D", "right": "E", "basis": "Isolate D/E"}],
    })
    rules = hard_constraints(model)
    first, second = conflict_witnesses(rules)
    assert [(a, b, rule.kind) for a, b, rule in first.path] == [("A", "B", "KEEP_SHARED"), ("B", "C", "LOCAL_TRANSACTION")]
    assert [(a, b) for a, b, _ in second.path] == [("D", "E")]
    repairs = minimal_repairs(model, rules)
    assert len(repairs) == 6
    assert {frozenset(repair.rules) for repair in repairs} == {
        frozenset((left, right)) for left in (rules[0], rules[2], rules[4]) for right in (rules[1], rules[3])
    }
    for repair in repairs:
        repaired = simulate_repair(model, repair)
        result = analyze(repaired, Preferences())
        assert len(result.feasible) == repair.feasible > 0
        assert not conflict_witnesses(hard_constraints(repaired))
        assert not minimal_repairs(repaired, hard_constraints(repaired))
        for subset in combinations(repair.rules, len(repair.rules) - 1):
            assert not analyze(simulate_repair(model, Repair(subset, feasible=0)), Preferences()).feasible
