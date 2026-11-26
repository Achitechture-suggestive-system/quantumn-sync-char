"""Authored conflict and revision checks; repair costs are declared test policies."""

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from eqcr import storage, studio_canvas
from eqcr.quantum_tradeoff import Architecture, Preferences, analyze, hard_constraints
from eqcr.studio_conflicts import (Repair, apply_reviewed_repair, conflict_witnesses, enforce_protected_rules,
                                   minimal_repairs, review_rule_policy, simulate_repair)
from eqcr.studio_oracles import oracle_ticket_cases, replay_architecture
from eqcr.studio_sessions import load_checkpoint


def conflict_model():
    return replay_architecture(oracle_ticket_cases()["OC-10"], "oracle")


def set_policy(model, kind, protected=False, cost=1):
    rule = [item for item in hard_constraints(model) if item.kind == kind][-1]
    return review_rule_policy(model, rule, protected=protected, change_cost=cost,
                              actor="TEST_ONLY", rationale="Authored policy check")[0]


def test_weighted_minimal_repairs_respect_protection_and_keep_original_infeasible():
    model = set_policy(conflict_model(), "KEEP_APART", cost=100)
    model = set_policy(model, "LOCAL_TRANSACTION", cost=2)
    repairs = minimal_repairs(model, hard_constraints(model))
    assert [(item.rules[0].kind, item.review_cost) for item in repairs] == [("LOCAL_TRANSACTION", 2), ("KEEP_APART", 100)]
    protected = set_policy(model, "KEEP_APART", protected=True)
    [repair] = minimal_repairs(protected, hard_constraints(protected))
    assert repair.rules[0].kind == "LOCAL_TRANSACTION"
    assert len(analyze(simulate_repair(protected, repair), Preferences()).feasible) == 27
    assert not analyze(protected, Preferences()).feasible
    both = set_policy(protected, "LOCAL_TRANSACTION", protected=True)
    assert conflict_witnesses(hard_constraints(both)) and not minimal_repairs(both, hard_constraints(both))
    rule = next(item for item in hard_constraints(both) if item.kind == "LOCAL_TRANSACTION")
    with pytest.raises(ValueError, match="bảo vệ"):
        simulate_repair(both, Repair((rule,), 27))


def test_protected_edit_and_stale_repair_are_blocked_until_policy_review():
    model = set_policy(conflict_model(), "LOCAL_TRANSACTION", protected=True)
    raw = model.model_dump(mode="json")
    raw["interactions"][-1]["local_transaction"] = False
    with pytest.raises(ValueError, match="bảo vệ"):
        enforce_protected_rules(model, Architecture.model_validate(raw))
    unlocked = set_policy(model, "LOCAL_TRANSACTION", protected=False)
    repair = next(item for item in minimal_repairs(unlocked, hard_constraints(unlocked)) if item.rules[0].kind == "LOCAL_TRANSACTION")
    changed, event = apply_reviewed_repair(unlocked, repair, actor="TEST_ONLY", rationale="Explicit test change")
    assert event["action"] == "HARD_RULE_REPAIR_APPLIED" and event["feasible_after"] == 27
    assert changed.interactions[-1].mode == "SYNC" and not changed.interactions[-1].local_transaction
    assert len(analyze(changed, Preferences()).feasible) == 27 and not analyze(model, Preferences()).feasible
    with pytest.raises(ValueError, match="đã cũ"):
        apply_reviewed_repair(model, repair, actor="TEST_ONLY", rationale="Stale policy test")


def test_positive_policy_cost_and_actor_are_required():
    model = conflict_model()
    rule = hard_constraints(model)[0]
    with pytest.raises(ValueError):
        review_rule_policy(model, rule, protected=True, change_cost=0, actor="TEST_ONLY", rationale="Test")
    with pytest.raises(ValueError, match="người review"):
        review_rule_policy(model, rule, protected=True, change_cost=1, actor="", rationale="Test")
    with pytest.raises(ValueError, match="người review"):
        apply_reviewed_repair(model, minimal_repairs(model, hard_constraints(model))[0], actor="TEST_ONLY", rationale="")


def test_model_review_cannot_weaken_a_protected_transaction():
    from eqcr.studio_extraction import catalog_digest, decide_proposal

    model = set_policy(conflict_model(), "LOCAL_TRANSACTION", protected=True)
    source = next(item for item in model.requirements if item.id == "OC-10")
    proposal = {"id": "TEST_ONLY", "status": "REVIEW_REQUIRED", "source_id": source.id,
                "source_digest": source.input_digest(), "catalog_digest": catalog_digest(model), "run_id": "TEST_ONLY",
                "payload": {"kind": "INTERACTION", "source": "ROUTE", "target": "COMPLETE", "mode": "SYNC",
                            "local_transaction": False, "quote": source.text[:100]}}
    with pytest.raises(ValueError, match="bảo vệ"):
        decide_proposal(model, proposal, action="APPROVE", actor="TEST_ONLY", rationale="Test guard")


def app_view(tmp_path, monkeypatch, model, events=None):
    monkeypatch.setattr(storage, "ARTIFACT_ROOT", tmp_path)
    pending = list(events or [])
    monkeypatch.setattr(studio_canvas, "render_board", lambda **kwargs: pending.pop(0) if pending else None)
    view = AppTest.from_file(Path(__file__).parents[1] / "app.py", default_timeout=30)
    view.session_state.architecture = model
    view.session_state.studio_analyzed = True
    return view.run()


def widget(view, kind, label):
    return next(item for item in getattr(view, kind) if item.label == label)


def test_ui_repair_requires_rationale_then_records_applied_diff(tmp_path, monkeypatch):
    model = set_policy(conflict_model(), "LOCAL_TRANSACTION", protected=True)
    view = app_view(tmp_path, monkeypatch, model)
    assert not view.exception
    widget(view, "button", "Áp dụng cách sửa đã review").click().run()
    assert any("lý do" in item.value for item in view.error)
    assert view.session_state.architecture == model
    widget(view, "text_area", "Lý do áp dụng cách sửa").set_value("TEST_ONLY reviewed removal of separation, local transaction remains")
    widget(view, "button", "Áp dụng cách sửa đã review").click().run()
    assert not view.exception
    saved = load_checkpoint(view.session_state.studio_checkpoint)
    assert saved["event"]["action"] == "HARD_RULE_REPAIR_APPLIED"
    assert saved["event"]["changes"][0]["kind"] == "KEEP_APART"
    after = Architecture.model_validate(saved["architecture"])
    assert len(analyze(after, Preferences()).feasible) == 10
    assert next(item for item in hard_constraints(after) if item.kind == "LOCAL_TRANSACTION").protected


def test_ui_blocked_edit_is_retained_before_return_to_policy_review(tmp_path, monkeypatch):
    model = set_policy(conflict_model(), "LOCAL_TRANSACTION", protected=True)
    raw = model.model_dump(mode="json")
    raw["interactions"][-1]["local_transaction"] = False
    view = app_view(tmp_path, monkeypatch, model, [{"token": "TEST_ONLY_PROTECTED_EDIT", "action": "analyze", "model": raw, "layout": {}}])
    assert not view.exception and view.session_state.studio_pending
    assert view.session_state.architecture == model
    widget(view, "button", "Lưu bản nháp bị chặn và quay lại review chính sách").click().run()
    assert not view.exception and not view.session_state.studio_pending
    saved = load_checkpoint(view.session_state.studio_checkpoint)
    assert saved["event"]["action"] == "PROTECTED_EDIT_RETAINED"
    assert saved["event"]["attempted_input"] == raw
    assert view.session_state.architecture == model


def test_ui_policy_decision_has_its_own_revision(tmp_path, monkeypatch):
    view = app_view(tmp_path, monkeypatch, conflict_model())
    widget(view, "selectbox", "Quy tắc cần review").select(1).run()
    widget(view, "checkbox", "Bảo vệ quy tắc này").check().run()
    widget(view, "text_area", "Căn cứ bảo vệ hoặc cho phép sửa").set_value("TEST_ONLY do not relax isolation")
    widget(view, "button", "Lưu chính sách ràng buộc").click().run()
    assert not view.exception
    saved = load_checkpoint(view.session_state.studio_checkpoint)
    assert saved["event"]["action"] == "HARD_RULE_POLICY_REVIEW"
    model = Architecture.model_validate(saved["architecture"])
    assert hard_constraints(model)[1].protected
    assert [item.rules[0].kind for item in minimal_repairs(model, hard_constraints(model))] == ["LOCAL_TRANSACTION"]
