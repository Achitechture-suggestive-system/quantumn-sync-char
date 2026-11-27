"""Authored development examples and technical review fixtures, never independent semantic labels."""

from copy import deepcopy
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from eqcr import ollama, storage, studio_canvas
from eqcr.quantum_example import ticket_example
from eqcr.quantum_tradeoff import Architecture, Preferences, analyze, component_profiles, hard_constraints
from eqcr.studio_evidence import EvidenceReviewRequired, catalog_digest, evidence_blockers, rebind_evidence
from eqcr.studio_extraction import author_clause, decide_proposal, extract_proposals, proposal_issues
from eqcr.studio_oracles import oracle_ticket_cases
from eqcr.studio_semantics import SCHEMA, ClauseFrame, uncovered_text
from eqcr.studio_sessions import invalidate_changed_sources, load_checkpoint, save_checkpoint


def source_model(text, scope=()):
    data = ticket_example().model_dump(mode="json")
    data["requirements"].append({"id": "SEM", "kind": "NFR", "text": text, "component_ids": list(scope)})
    return Architecture.model_validate(data)


def quality(quote, subject, action, owner, *, label="Reliability", modality="phải", condition=None, context=(), statement="OBLIGATION"):
    return {"kind": "QUALITY", "quote": quote, "disposition": "PROPOSED", "characteristic": label, "component_ids": [owner],
            "frame": {"subject": subject, "action": action, "object": None, "condition": condition, "modality": modality,
                      "subject_ids": [owner], "object_ids": [], "context_ids": list(context), "statement_kind": statement, "effect": "QUALITY_OBLIGATION"}}


def proposal(model, payload, number=1):
    source = model.requirements[-1]
    return {"id": f"TEST_ONLY-{number}", "run_id": "TEST_ONLY_RUN", "source_id": source.id, "source_digest": source.input_digest(),
            "catalog_digest": catalog_digest(model), "semantic_schema": SCHEMA, "payload": payload, "status": "REVIEW_REQUIRED", "provenance": "PREPARED_FIXTURE"}


def accept(model, item, **kwargs):
    return decide_proposal(model, item, action=kwargs.pop("action", "APPROVE"), actor="TEST_ONLY", rationale="Authored technical review, no expert labels",
                           semantic_confirmed=True, provenance="PREPARED_FIXTURE", **kwargs)


def test_oc02_exemption_does_not_create_target_and_later_obligation_remains_independent():
    text = oracle_ticket_cases()["OC-02"]["text"]
    model = source_model(text)
    first, second = text.split(". ", 1)
    first += "."
    payload = quality(first, "Operations Reporting", "đáp ứng mốc 150 ms", "REPORT", label="Performance efficiency",
                       modality="không phải", statement="EXEMPTION")
    baseline = analyze(model, Preferences())
    with pytest.raises(ValueError, match="không bắt buộc"):
        accept(model, proposal(model, payload))
    inactive = deepcopy(payload)
    inactive.update(disposition="OUT_OF_SCOPE", characteristic=None, component_ids=[])
    inactive["frame"]["effect"] = "NONE"
    unchanged, event = accept(model, proposal(model, inactive))
    assert analyze(unchanged, Preferences()) == baseline and event["effect_status"] == "NO_ACTIVE_EFFECT"
    active = quality(second, "Operations Reporting", "khôi phục", "REPORT", condition="Sau khi tiến trình xử lý bị dừng")
    changed, _ = accept(unchanged, proposal(unchanged, active, 2))
    assert [row.characteristic for row in changed.requirements[-1].quality_allocations] == ["Reliability"]
    assert analyze(changed, Preferences()) != baseline


def test_omitting_negation_from_modality_does_not_hide_it_in_clause_prefix():
    text = "Operations Reporting không phải đáp ứng mốc 150 ms."
    model = source_model(text)
    payload = quality(text, "Operations Reporting", "đáp ứng", "REPORT", modality="phải", label="Performance efficiency")
    assert any("EXEMPTION" in item for item in proposal_issues(model, "SEM", payload, structured=True))
    with pytest.raises(ValueError):
        accept(model, proposal(model, payload))


def test_prohibition_is_an_active_quality_obligation_instead_of_an_exemption():
    text = "Customer Profile must not disclose personal data to anonymous users."
    model = source_model(text)
    payload = quality(text, "Customer Profile", "disclose personal data", "PROFILE", label="Security", modality="must not", statement="PROHIBITION")
    changed, _ = accept(model, proposal(model, payload))
    allocation = changed.requirements[-1].quality_allocations[0]
    assert allocation.characteristic == "Security" and allocation.component_ids == ["PROFILE"]
    assert allocation.semantic_reviews[0].frame.statement_kind == "PROHIBITION"
    assert allocation.semantic_reviews[0].provenance == "PREPARED_FIXTURE"


def test_oc03_two_clauses_keep_both_labels_and_only_their_responsible_components():
    text = oracle_ticket_cases()["OC-03"]["text"]
    model = source_model(text)
    first, second = text.split(". ", 1)
    security = quality(first + ".", "Customer Profile", "mã hóa trường định danh", "PROFILE", label="Security", condition="trước khi truyền")
    recovery = quality(second, "Operations Reporting", "khôi phục", "REPORT", condition="Khi worker báo cáo bị dừng")
    changed, _ = accept(model, proposal(model, security))
    changed, _ = accept(changed, proposal(changed, recovery, 2))
    assert {row.characteristic: row.component_ids for row in changed.requirements[-1].quality_allocations} == {"Security": ["PROFILE"], "Reliability": ["REPORT"]}
    assert len(changed.interactions) == len(model.interactions) and hard_constraints(changed) == hard_constraints(model)
    assert "Security · SEM" in component_profiles(changed)["PROFILE"]
    assert "Reliability · SEM" in component_profiles(changed)["REPORT"]


@pytest.mark.parametrize("case_id,owner,context,action,label", [
    ("OC-07", "REPORT", "CREATE", "đọc được cả hai phiên bản hợp đồng v1 và v2", "Compatibility"),
    ("OC-12", "COMPLETE", "REPORT", "duy trì tỷ lệ hoàn tất thành công ít nhất 99,5%", "Reliability"),
])
def test_context_components_are_not_promoted_to_owners(case_id, owner, context, action, label):
    text = oracle_ticket_cases()[case_id]["text"]
    model = source_model(text)
    names = {item.id: item.name for item in model.components}
    correct = quality(text, names[owner], action, owner, label=label, context=[context])
    wrong = deepcopy(correct)
    wrong["component_ids"] = [context]
    with pytest.raises(ValueError, match="Scope"):
        accept(model, proposal(model, wrong))
    changed, event = accept(model, proposal(model, wrong), action="CORRECT", corrected=correct)
    assert changed.requirements[-1].quality_allocations[0].component_ids == [owner]
    assert event["before"] != event["after"] and hard_constraints(model) == hard_constraints(changed)
    wrong["frame"]["subject_ids"] = [context]
    assert any("không khớp component" in item for item in proposal_issues(model, "SEM", wrong, structured=True))


def test_alias_requires_scope_or_an_explicit_reviewer_mapping():
    text = "Thành phần cầu nối phải khôi phục trong 3 phút."
    model = source_model(text)
    payload = quality(text, "Thành phần cầu nối", "khôi phục", "REPORT")
    with pytest.raises(ValueError, match="biệt danh"):
        accept(model, proposal(model, payload))
    corrected = deepcopy(payload)
    corrected["frame"]["human_fields"] = ["subject_ids"]
    with pytest.raises(ValueError, match="HUMAN_DECISION"):
        accept(model, proposal(model, corrected))
    changed, _ = accept(model, proposal(model, payload), action="CORRECT", corrected=corrected)
    record = changed.requirements[-1].quality_allocations[0].semantic_reviews[0]
    assert record.frame.human_fields == ["subject_ids"] and record.proposal_provenance == "PREPARED_FIXTURE"
    # Explicitly declared source scope supplies the otherwise absent identity; no synonym is invented.
    declared = source_model(text, scope=["REPORT"])
    assert not proposal_issues(declared, "SEM", payload, structured=True)


def test_inactive_mapping_and_unknown_disposition_cannot_be_marked_applied():
    text = "Customer Profile must encrypt personal data."
    model = source_model(text)
    payload = quality(text, "Customer Profile", "encrypt personal data", "PROFILE", label="Security", modality="must")
    for disposition in ("OUT_OF_SCOPE", "AMBIGUOUS"):
        bad = deepcopy(payload)
        bad["disposition"] = disposition
        with pytest.raises(ValueError, match="rỗng"):
            accept(model, proposal(model, bad))
    payload["disposition"] = "AMBIGUOUS"
    payload.update(characteristic=None, component_ids=[])
    payload["frame"]["effect"] = "NONE"
    with pytest.raises(ValueError, match="AMBIGUOUS"):
        accept(model, proposal(model, payload))


def test_structured_review_confirmation_is_required_and_frame_cannot_be_removed_by_correction():
    text = "Customer Profile must encrypt personal data."
    model = source_model(text)
    payload = quality(text, "Customer Profile", "encrypt personal data", "PROFILE", label="Security", modality="must")
    item = proposal(model, payload)
    with pytest.raises(ValueError, match="Xác nhận"):
        decide_proposal(model, item, action="APPROVE", actor="TEST_ONLY", rationale="Missing confirmation")
    stripped = {key: value for key, value in payload.items() if key not in {"frame", "disposition"}}
    with pytest.raises(ValueError, match="mệnh đề"):
        accept(model, item, action="CORRECT", corrected=stripped)
    for action in ("DEFER", "REJECT"):
        unchanged, _ = decide_proposal(model, item, action=action, actor="TEST_ONLY", rationale="Technical abstention")
        assert unchanged == model


def test_same_iso_in_two_clauses_preserves_union_scope_and_both_proofs():
    first = "Customer Profile must encrypt personal data."
    second = "Operations Reporting must encrypt report exports."
    model = source_model(first + " " + second)
    for number, args in enumerate([(first, "Customer Profile", "encrypt personal data", "PROFILE"),
                                   (second, "Operations Reporting", "encrypt report exports", "REPORT")], 1):
        payload = quality(*args, label="Security", modality="must")
        model, _ = accept(model, proposal(model, payload, number))
    assert len(model.requirements[-1].quality_allocations) == 1
    allocation = model.requirements[-1].quality_allocations[0]
    assert allocation.component_ids == ["PROFILE", "REPORT"] and len(allocation.semantic_reviews) == 2
    assert not evidence_blockers(model)
    assert all("Security · SEM" in component_profiles(model)[owner] for owner in ("PROFILE", "REPORT"))


@pytest.mark.parametrize("edit", ["source", "catalog", "scope"])
def test_quality_proofs_block_solver_when_revision_or_scope_is_not_current(edit):
    text = "Customer Profile must encrypt personal data."
    model = source_model(text)
    payload = quality(text, "Customer Profile", "encrypt personal data", "PROFILE", label="Security", modality="must")
    reviewed, _ = accept(model, proposal(model, payload))
    data = reviewed.model_dump(mode="json")
    if edit == "source":
        data["requirements"][-1]["text"] += " Changed operating condition."
    elif edit == "catalog":
        data["components"][0]["name"] += " renamed"
    else:
        data["requirements"][-1]["quality_allocations"][0]["component_ids"] = ["REPORT"]
    stale = Architecture.model_validate(data)
    assert evidence_blockers(stale)
    with pytest.raises(EvidenceReviewRequired):
        analyze(stale, Preferences())
    if edit == "source":
        cleared = invalidate_changed_sources(reviewed, stale)
        assert not cleared.requirements[-1].quality_allocations and not evidence_blockers(cleared)


def test_interaction_requires_actor_receiver_roles_and_matching_mode_effect():
    text = "Ticket Creation must wait for Ticket Router before replying."
    model = source_model(text)
    payload = {"kind": "INTERACTION", "quote": text, "disposition": "PROPOSED", "source": "CREATE", "target": "ROUTE", "mode": "SYNC", "local_transaction": False,
               "frame": ClauseFrame(subject="Ticket Creation", action="wait", object="Ticket Router", modality="must", subject_ids=["CREATE"], object_ids=["ROUTE"],
                                    statement_kind="OBLIGATION", effect="WAIT_COMPLETION").model_dump(exclude={"human_fields"})}
    reviewed, _ = accept(model, proposal(model, payload))
    assert reviewed.interactions[0].mode == "SYNC" and reviewed.interactions[0].evidence.semantic_review
    assert analyze(reviewed, Preferences()) != analyze(model, Preferences())
    wrong = deepcopy(payload)
    wrong["mode"] = "ASYNC"
    with pytest.raises(ValueError, match="Mode"):
        accept(model, proposal(model, wrong))
    with pytest.raises(ValueError, match="mệnh đề đầy đủ"):
        rebind_evidence(reviewed, "interactions", 0, source_id="SEM", quote=text, actor="TEST_ONLY", rationale="Cannot bypass full frame")


def test_forbidden_separation_is_not_a_separation_policy():
    text = "Ticket Router must not be separated from Ticket Completion."
    model = source_model(text)
    payload = {"kind": "SEPARATION", "quote": text, "disposition": "PROPOSED", "left": "ROUTE", "right": "COMPLETE",
               "frame": ClauseFrame(subject="Ticket Router", action="separated", object="Ticket Completion", modality="must not", subject_ids=["ROUTE"], object_ids=["COMPLETE"],
                                    statement_kind="PROHIBITION", effect="REQUIRE_SEPARATION").model_dump(exclude={"human_fields"})}
    with pytest.raises(ValueError, match="cấm tách"):
        accept(model, proposal(model, payload))


def test_conditional_mode_cannot_silently_become_unconditional_without_explicit_context_policy():
    text = "When a ticket is urgent, Ticket Creation must wait for Ticket Router."
    model = source_model(text)
    payload = {"kind": "INTERACTION", "quote": text, "disposition": "PROPOSED", "source": "CREATE", "target": "ROUTE", "mode": "SYNC", "local_transaction": False,
               "frame": ClauseFrame(subject="Ticket Creation", action="wait", object="Ticket Router", modality="must", condition="When a ticket is urgent",
                                    subject_ids=["CREATE"], object_ids=["ROUTE"], statement_kind="OBLIGATION", effect="WAIT_COMPLETION").model_dump(exclude={"human_fields"})}
    with pytest.raises(ValueError, match="có điều kiện"):
        accept(model, proposal(model, payload))
    corrected = deepcopy(payload)
    corrected["frame"]["human_fields"] = ["effect"]
    changed, _ = accept(model, proposal(model, payload), action="CORRECT", corrected=corrected)
    assert changed.interactions[0].evidence.semantic_review.frame.human_fields == ["effect"]


def test_text_coverage_shows_omission_without_claiming_semantic_recall():
    text = oracle_ticket_cases()["OC-03"]["text"]
    model = source_model(text)
    quote = text.split(". ")[0] + "."
    item = proposal(model, quality(quote, "Customer Profile", "mã hóa", "PROFILE", label="Security"))
    assert "Operations Reporting" in " ".join(uncovered_text(model.requirements[-1], [item]))
    full = deepcopy(item)
    full["payload"]["quote"] = text
    assert uncovered_text(model.requirements[-1], [full]) == []  # This text coverage still proves no semantic completeness.


def test_exact_duplicate_model_payload_stays_unapplied_and_raw_outputs_are_preserved(tmp_path, monkeypatch):
    import json

    text = "Customer Profile must encrypt personal data."
    model = source_model(text)
    payload = quality(text, "Customer Profile", "encrypt personal data", "PROFILE", label="Security", modality="must")
    raw = {key: value for key, value in payload.items() if key != "kind"}
    raw["source_id"] = "SEM"
    monkeypatch.setattr(storage, "ARTIFACT_ROOT", tmp_path)
    monkeypatch.setattr(ollama, "list_model_details", lambda: [{"name": "qwen3:4b", "digest": "TEST_ONLY"}])
    monkeypatch.setattr(ollama, "get_ollama_version", lambda: "TEST_ONLY")
    monkeypatch.setattr(ollama, "_request", lambda *args, **kwargs: {"model": "qwen3:4b", "done_reason": "stop", "message": {"content": json.dumps({"proposals": [raw, raw]})}})
    run = extract_proposals(model, ["SEM"], "QUALITY")
    first, duplicate = run["proposals"]
    assert duplicate["duplicate_of_proposal_id"] == first["id"] and run["semantic_schema"] == SCHEMA
    assert not model.requirements[-1].quality_allocations and list(tmp_path.rglob("response.json"))
    with pytest.raises(ValueError, match="trùng"):
        accept(model, duplicate)


def test_repeated_quote_needs_unambiguous_context():
    quote = "Customer Profile must encrypt personal data."
    model = source_model(quote + " " + quote)
    payload = quality(quote, "Customer Profile", "encrypt personal data", "PROFILE", label="Security", modality="must")
    assert any("nhiều lần" in issue for issue in proposal_issues(model, "SEM", payload, structured=True))


def test_parts_from_another_sentence_are_not_treated_as_one_atomic_clause():
    first = "Customer Profile must encrypt personal data."
    second = "Operations Reporting should recover after a failure."
    model = source_model(first + " " + second)
    payload = quality(model.requirements[-1].text, "Customer Profile", "encrypt personal data", "PROFILE", label="Security", modality="should recover")
    assert any("mệnh đề khác" in issue for issue in proposal_issues(model, "SEM", payload, structured=True))


def test_reviewer_can_add_a_missed_clause_without_calling_it_model_generated():
    text = "Operations Reporting must recover within 3 minutes."
    model = source_model(text)
    draft = author_clause(model, "SEM", "QUALITY")
    assert draft["provenance"] == "HUMAN_DECISION" and draft["payload"]["disposition"] == "AMBIGUOUS"
    assert not model.requirements[-1].quality_allocations
    corrected = quality(text, "Operations Reporting", "recover within 3 minutes", "REPORT", modality="must")
    changed, _ = accept(model, draft, action="CORRECT", corrected=corrected)
    record = changed.requirements[-1].quality_allocations[0].semantic_reviews[0]
    assert record.proposal_provenance == "HUMAN_DECISION" and record.claim_provenance == "PREPARED_FIXTURE"


def test_invalid_model_frame_is_visible_and_rejectable_in_ui(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "ARTIFACT_ROOT", tmp_path)
    monkeypatch.setattr(studio_canvas, "render_board", lambda **kwargs: None)
    model = source_model("Customer Profile must encrypt personal data.")
    payload = quality(model.requirements[-1].text, "Customer Profile", "encrypt personal data", "PROFILE", label="Security", modality="must")
    payload["frame"].update(statement_kind={"invalid": True}, subject_ids=None)
    item = proposal(model, payload)
    view = AppTest.from_file(Path(__file__).parents[1] / "app.py", default_timeout=30)
    view.session_state.architecture = model
    view.session_state.studio_live_proposals = [item]
    view.run()
    assert not view.exception and any("Frame gốc chưa hợp lệ" in row.value for row in view.warning)
    next(row for row in view.selectbox if row.label == "Quyết định").select("REJECT")
    next(row for row in view.text_area if row.label == "Lý do quyết định").set_value("Prepared invalid provider frame, reject without applying")
    next(row for row in view.button if row.label == "Lưu quyết định và tính lại").click().run()
    assert not view.exception and view.session_state.studio_live_proposals[0]["status"] == "REJECTED"
    assert view.session_state.architecture == model


def test_ui_corrects_context_scope_then_persists_clause_proof_and_restores_it(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "ARTIFACT_ROOT", tmp_path)
    captures = []
    monkeypatch.setattr(studio_canvas, "render_board", lambda **kwargs: captures.append(kwargs))
    text = "When Operations Reporting stops, Ticket Completion must maintain successful completion."
    model = source_model(text)
    correct = quality(text, "Ticket Completion", "maintain successful completion", "COMPLETE", modality="must", context=["REPORT"], condition="When Operations Reporting stops")
    wrong = deepcopy(correct)
    wrong["component_ids"] = ["REPORT"]
    item = proposal(model, wrong)
    view = AppTest.from_file(Path(__file__).parents[1] / "app.py", default_timeout=30)
    view.session_state.architecture = model
    view.session_state.studio_live_proposals = [item]
    view.run()

    def widget(kind, label):
        return next(row for row in getattr(view, kind) if row.label == label)

    widget("multiselect", "Component chịu trách nhiệm").set_value(["COMPLETE"])
    widget("selectbox", "Quyết định").select("CORRECT")
    widget("selectbox", "Nguồn quyết định đề xuất").select("PREPARED_FIXTURE")
    widget("text_input", "Người review").set_value("TEST_ONLY")
    widget("text_area", "Lý do quyết định").set_value("Prepared technical correction: failure context is not owner")
    widget("checkbox", "Tôi đã review chủ thể, điều kiện, phủ định và tác động của mệnh đề").check()
    widget("button", "Lưu quyết định và tính lại").click().run()
    assert not view.exception
    checkpoint = load_checkpoint(view.session_state.studio_checkpoint)
    assert checkpoint["event"]["semantic_confirmed"] and checkpoint["event"]["provenance"] == "PREPARED_FIXTURE"
    restored = Architecture.model_validate(checkpoint["architecture"])
    assert restored.requirements[-1].quality_allocations[0].component_ids == ["COMPLETE"]
    assert restored.requirements[-1].quality_allocations[0].semantic_reviews[0].proposal_id == "TEST_ONLY-1"
    assert all(plan["assignment"].get("COMPLETE") for plan in captures[-1]["plans"])
    assert analyze(restored, Preferences()) != analyze(model, Preferences())
    saved = save_checkpoint(restored, event=checkpoint["event"], proposals=checkpoint["proposals"])
    assert Architecture.model_validate(load_checkpoint(saved)["architecture"]) == restored
    widget("selectbox", "Nguồn bổ sung mệnh đề").select("SEM").run()
    widget("button", "Tạo mệnh đề bổ sung để review").click().run()
    assert not view.exception and view.session_state.architecture == restored
    assert view.session_state.studio_live_proposals[-1]["provenance"] == "HUMAN_DECISION"
    assert load_checkpoint(view.session_state.studio_checkpoint)["event"]["action"] == "REVIEWER_CLAUSE_DRAFTED"
