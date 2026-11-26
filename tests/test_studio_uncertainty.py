"""Test-authored uncertainty hypotheses, without semantic accuracy claims."""

from itertools import product
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from eqcr import storage, studio_canvas
from eqcr.quantum_tradeoff import Architecture, Preferences, analyze, hard_constraints, group_index
from eqcr.studio_sessions import invalidate_changed_sources, load_checkpoint
from eqcr.studio_uncertainty import cases_are_current, conservative_order, review_interaction_cases, score_bounds


def conditional_input():
    return Architecture.model_validate({
        "components": [{"id": key, "name": key, "characteristics": ["Shared goal"]} for key in "ABC"],
        "requirements": [{"id": "CASE", "kind": "FR",
                          "text": "When online A waits for B. When offline A queues work for B."}],
        "interactions": [{"source": "A", "target": "B", "mode": "UNKNOWN", "weight": 2},
                         {"source": "B", "target": "C", "mode": "UNKNOWN", "weight": 1}],
        "keep_apart": [{"left": "A", "right": "C", "basis": "TEST_ONLY isolation"}],
    })


def case_rows():
    return [{"condition": "online", "mode": "SYNC", "source_id": "CASE", "source_quote": "When online A waits for B."},
            {"condition": "offline", "mode": "ASYNC", "source_id": "CASE", "source_quote": "When offline A queues work for B."}]


def test_interval_endpoints_equal_explicit_mode_enumeration_and_preserve_hard_rules():
    model = conditional_input()
    weights = Preferences(sync=4, async_seam=3)
    original = analyze(model, weights)
    observed = {candidate.id: [] for candidate in original.feasible}
    for modes in product(("SYNC", "ASYNC"), repeat=2):
        raw = model.model_dump(mode="json")
        for edge, mode in zip(raw["interactions"], modes, strict=True):
            edge["mode"] = mode
        resolved = Architecture.model_validate(raw)
        result = analyze(resolved, weights)
        assert {item.id for item in result.feasible} == set(observed)
        for item in result.feasible:
            observed[item.id].append(item.score(weights))
            assert not any(rule.violated_by(group_index(item.groups)) for rule in hard_constraints(model))
    for candidate in original.feasible:
        bounds = score_bounds(model, candidate, weights)
        assert (bounds.lower, bounds.upper) == (min(observed[candidate.id]), max(observed[candidate.id]))
        assert bounds.unresolved_edges == 2 and bounds.conditional_edges == 0


def test_upper_bound_optimizer_includes_nominally_dominated_partition():
    model = Architecture.model_validate({
        "components": [{"id": key, "name": key, "characteristics": ["Shared"]} for key in "AB"],
        "interactions": [{"source": "A", "target": "B", "mode": "UNKNOWN"}],
    })
    weights = Preferences(sync=0, data=0, async_seam=10, characteristics=1)
    analysis = analyze(model, weights)
    assert len(analysis.frontier) == 1 and len(analysis.ranked[0].groups) == 1
    best = conservative_order(model, analysis.feasible, weights)[0]
    assert len(best.groups) == 2 and best not in analysis.frontier
    assert score_bounds(model, best, weights).upper == 1
    assert score_bounds(model, analysis.ranked[0], weights).upper == 10


def test_reviewed_conditions_keep_modes_quotes_and_invalidate_on_source_revision():
    model = conditional_input()
    changed, event = review_interaction_cases(model, "A", "B", case_rows(), actor="TEST_ONLY", rationale="Test branches")
    assert event["action"] == "INTERACTION_CONDITIONS_REVIEW" and event["before"] != event["after"]
    assert changed.interactions[0].mode == "UNKNOWN" and cases_are_current(changed, changed.interactions[0])
    assert not model.interactions[0].cases
    candidate = analyze(changed, Preferences()).ranked[0]
    bounds = score_bounds(changed, candidate, Preferences())
    assert (bounds.conditional_edges, bounds.unresolved_edges) == (1, 1)
    raw = changed.model_dump(mode="json")
    raw["requirements"][0]["text"] += " Updated scope."
    edited = Architecture.model_validate(raw)
    assert not cases_are_current(edited, edited.interactions[0])
    invalidated = invalidate_changed_sources(changed, edited)
    assert not invalidated.interactions[0].cases
    assert invalidated.interactions[0].mode == "UNKNOWN"


def test_same_mode_conditions_collapse_bounds_but_stale_proof_expands_them():
    model = conditional_input()
    rows = case_rows()
    rows[1]["mode"] = "SYNC"  # Authored structural check, not a semantic decision.
    changed, _ = review_interaction_cases(model, "A", "B", rows, actor="TEST_ONLY", rationale="Test only")
    raw = changed.model_dump(mode="json")
    raw["interactions"] = [raw["interactions"][0]]
    changed = Architecture.model_validate(raw)
    cross = next(item for item in analyze(changed, Preferences()).feasible if group_index(item.groups)["A"] != group_index(item.groups)["B"])
    bounds = score_bounds(changed, cross, Preferences())
    assert bounds.lower == bounds.upper == cross.score(Preferences()) + 6
    raw["requirements"][0]["text"] += " Updated."
    bounds = score_bounds(Architecture.model_validate(raw), cross, Preferences())
    assert bounds.lower == cross.score(Preferences()) and bounds.upper == cross.score(Preferences()) + 6


def test_conditional_review_cannot_erase_local_transaction_or_use_invalid_quotes():
    model = conditional_input()
    bad = case_rows()
    bad[0]["source_quote"] = "TEST_ONLY invented quote"
    with pytest.raises(ValueError, match="nguyên văn"):
        review_interaction_cases(model, "A", "B", bad, actor="TEST_ONLY", rationale="Test")
    raw = model.model_dump(mode="json")
    raw["interactions"][0].update(mode="SYNC", local_transaction=True, basis="TEST_ONLY atomic")
    with pytest.raises(ValueError, match="quy tắc cứng"):
        review_interaction_cases(Architecture.model_validate(raw), "A", "B", case_rows(), actor="TEST_ONLY", rationale="Test")


def test_ui_conditions_and_conservative_review_are_persisted(tmp_path, monkeypatch):
    import eqcr.quantum_example as example
    from eqcr import studio_cases, studio_oracles

    monkeypatch.setattr(storage, "ARTIFACT_ROOT", tmp_path)
    monkeypatch.setattr(studio_oracles, "ticket_example", example.ticket_example)
    monkeypatch.setattr(studio_cases, "ticket_example", example.ticket_example)
    monkeypatch.setattr(example, "ticket_example", conditional_input)
    monkeypatch.setattr(studio_canvas, "render_board", lambda **kwargs: None)
    view = AppTest.from_file(Path(__file__).parents[1] / "app.py", default_timeout=30).run()

    def widget(kind, label):
        return next(item for item in getattr(view, kind) if item.label == label)

    for index, row in enumerate(case_rows(), 1):
        widget("text_input", f"Tên điều kiện {index}").set_value(row["condition"])
        widget("selectbox", f"Mode điều kiện {index}").select(row["mode"])
        widget("text_area", f"Căn cứ điều kiện {index}").set_value(row["source_quote"])
    widget("text_area", "Căn cứ và phạm vi bao phủ điều kiện").set_value("TEST_ONLY two branches, no measured probabilities")
    widget("button", "Lưu các điều kiện và tính lại").click().run()
    assert not view.exception
    saved = load_checkpoint(view.session_state.studio_checkpoint)
    assert saved["event"]["action"] == "INTERACTION_CONDITIONS_REVIEW"
    assert len(saved["architecture"]["interactions"][0]["cases"]) == 2
    widget("checkbox", "Ưu tiên chi phí biên trên khi còn bất định").check().run()
    next(item for item in view.button if item.label.startswith("Chọn A")).click().run()
    assert not view.exception
    review = view.session_state.studio_last_review
    assert review["uncertainty_policy"] == "MINIMIZE_WEIGHTED_UPPER_BOUND"
    assert all(item["score_interval"]["upper"] >= item["score_interval"]["lower"] for item in review["comparison"])
