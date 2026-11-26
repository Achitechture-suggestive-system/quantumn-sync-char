"""Authored revision checks; proposals below are TEST_ONLY and never model inference evidence."""

from hashlib import sha256
import json
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from eqcr import storage, studio_canvas
from eqcr.quantum_example import ticket_example
from eqcr.quantum_tradeoff import Architecture, Preferences, analyze, hard_constraints
from eqcr.studio_conflicts import review_rule_policy
from eqcr.studio_evidence import EvidenceReviewRequired, catalog_digest, evidence_blockers, rebind_evidence
from eqcr.studio_extraction import decide_proposal
from eqcr.studio_sessions import invalidate_changed_sources, load_checkpoint, save_checkpoint


def reviewed_relationship(kind="INTERACTION", local=True):
    data = ticket_example().model_dump(mode="json")
    text = ("Ticket Router and Ticket Completion use the same local transaction." if local else
            "Ticket Router waits for Ticket Completion before replying.") if kind == "INTERACTION" else (
            "Ticket Router and Ticket Completion must be placed in separate Quanta.")
    data["requirements"].append({"id": "SRC", "kind": "FR", "text": text})
    source_model = Architecture.model_validate(data)
    source = source_model.requirements[-1]
    payload = {"kind": kind, "quote": text}
    payload.update({"source": "ROUTE", "target": "COMPLETE", "mode": "SYNC", "local_transaction": local}
                   if kind == "INTERACTION" else {"left": "ROUTE", "right": "COMPLETE"})
    proposal = {"id": "TEST_ONLY_PROPOSAL", "run_id": "TEST_ONLY_RUN", "status": "REVIEW_REQUIRED",
                "source_id": "SRC", "source_digest": source.input_digest(), "catalog_digest": catalog_digest(source_model),
                "payload": payload}
    model, event = decide_proposal(source_model, proposal, action="APPROVE", actor="TEST_ONLY", rationale="Authored structural test")
    return model, proposal, event


@pytest.mark.parametrize("kind", ["INTERACTION", "SEPARATION"])
def test_changed_source_blocks_optimizer_without_relaxing_declared_hard_rules(kind):
    before, _, _ = reviewed_relationship(kind)
    baseline = analyze(before, Preferences())
    data = before.model_dump(mode="json")
    data["requirements"][-1]["text"] += " Changed operating scope."
    changed = invalidate_changed_sources(before, Architecture.model_validate(data))
    assert hard_constraints(changed) == hard_constraints(before)
    assert evidence_blockers(changed)[0]["source_id"] == "SRC"
    with pytest.raises(EvidenceReviewRequired, match="review lại"):
        analyze(changed, Preferences())
    collection = "interactions" if kind == "INTERACTION" else "keep_apart"
    index = len(getattr(changed, collection)) - 1
    rebound, event = rebind_evidence(changed, collection, index, source_id="SRC", quote=before.requirements[-1].text,
                                      actor="TEST_ONLY", rationale="Test rechecked the unchanged claim under updated scope")
    assert not evidence_blockers(rebound)
    assert analyze(rebound, Preferences()) == baseline
    assert event["action"] == "SOURCE_EVIDENCE_RECONFIRMED"
    binding = getattr(rebound, collection)[index].evidence
    assert binding.citation_provenance == "HUMAN_DECISION" and binding.proposal_id == "TEST_ONLY_PROPOSAL"


def test_removed_source_catalog_and_claim_edits_are_each_detected():
    before, _, _ = reviewed_relationship(local=False)
    for edit in ("delete", "catalog", "claim"):
        data = before.model_dump(mode="json")
        if edit == "delete":
            data["requirements"].pop()
        elif edit == "catalog":
            data["components"][-1]["name"] += " renamed"
        else:
            data["interactions"][-1]["mode"] = "ASYNC"
        changed = Architecture.model_validate(data)
        assert evidence_blockers(changed)
        with pytest.raises(EvidenceReviewRequired):
            analyze(changed, Preferences())


def test_reconfirmation_of_protected_rule_updates_proof_and_preserves_rule():
    before, _, _ = reviewed_relationship()
    rule = next(item for item in hard_constraints(before) if item.kind == "LOCAL_TRANSACTION")
    before, _ = review_rule_policy(before, rule, protected=True, change_cost=5, actor="TEST_ONLY", rationale="Protected fixture")
    data = before.model_dump(mode="json")
    data["requirements"][-1]["text"] = "New source explicitly retains a local transaction for Router and Completion."
    changed = Architecture.model_validate(data)
    with pytest.raises(ValueError, match="nguyên văn"):
        rebind_evidence(changed, "interactions", 1, source_id="SRC", quote="invented", actor="TEST_ONLY", rationale="Test")
    rebound, _ = rebind_evidence(changed, "interactions", 1, source_id="SRC", quote=changed.requirements[-1].text,
                                 actor="TEST_ONLY", rationale="Test only rechecks declared transaction")
    assert hard_constraints(rebound) == hard_constraints(before)
    assert rebound.interactions[-1].evidence.review_actor == "TEST_ONLY"
    assert analyze(rebound, Preferences()) == analyze(before, Preferences())


@pytest.mark.parametrize("stale", [False, True])
def test_legacy_checkpoint_rebuilds_only_recorded_applied_links_without_rewriting_file(tmp_path, monkeypatch, stale):
    monkeypatch.setattr(storage, "ARTIFACT_ROOT", tmp_path)
    model, proposal, event = reviewed_relationship()
    data = model.model_dump(mode="json")
    data["interactions"][-1]["evidence"] = None
    if stale:
        data["requirements"][-1]["text"] += " Updated after review."
    identifier = save_checkpoint(Architecture.model_validate(data), event=event,
                                  proposals=[{**proposal, "status": "APPROVED"}])
    path = tmp_path / "quantum-studio" / "checkpoints" / f"{identifier}.json"
    legacy_data = json.loads(path.read_text(encoding="utf-8"))
    legacy_data["schema"] = "STUDIO-CHECKPOINT@1"
    path.write_text(json.dumps(legacy_data, ensure_ascii=False), encoding="utf-8")
    original_hash = sha256(path.read_bytes()).hexdigest()
    loaded = load_checkpoint(identifier)
    restored = Architecture.model_validate(loaded["architecture"])
    assert restored.interactions[-1].evidence.proposal_id == proposal["id"]
    assert bool(evidence_blockers(restored)) is stale
    assert sha256(path.read_bytes()).hexdigest() == original_hash
    # A legacy manual/fixture relationship without an applied record stays unbound.
    fixture = save_checkpoint(ticket_example(), event={"action": "TEST_ONLY_FIXTURE"})
    assert all(edge["evidence"] is None for edge in load_checkpoint(fixture)["architecture"]["interactions"])


def test_current_checkpoint_does_not_reapply_superseded_legacy_proposal(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "ARTIFACT_ROOT", tmp_path)
    model, proposal, event = reviewed_relationship(local=False)
    raw = model.model_dump(mode="json")
    raw["interactions"][-1]["evidence"] = None
    identifier = save_checkpoint(Architecture.model_validate(raw), event={"action": "TEST_ONLY_MANUAL_REPLACEMENT"},
                                  proposals=[{**proposal, "status": "APPROVED", "applied": event["applied"]}])
    assert load_checkpoint(identifier)["schema"] == "STUDIO-CHECKPOINT@2"
    assert load_checkpoint(identifier)["architecture"]["interactions"][-1]["evidence"] is None


def test_ui_clears_outputs_until_source_review_then_records_reconfirmation(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "ARTIFACT_ROOT", tmp_path)
    model, _, _ = reviewed_relationship()
    data = model.model_dump(mode="json")
    data["requirements"][-1]["text"] += " Updated scope."
    stale = Architecture.model_validate(data)
    captures = []
    monkeypatch.setattr(studio_canvas, "render_board", lambda **kwargs: captures.append(kwargs))
    view = AppTest.from_file(Path(__file__).parents[1] / "app.py", default_timeout=30)
    view.session_state.architecture = stale
    view.session_state.studio_analyzed = True
    view.run()
    assert not view.exception
    assert captures[-1]["review_required"] and not captures[-1]["plans"] and not captures[-1]["no_solution"]
    assert any("Cần review lại căn cứ" in item.value for item in view.warning)
    next(item for item in view.text_input if item.label == "Người review lại căn cứ").set_value("TEST_ONLY")
    next(item for item in view.text_area if item.label == "Lý do giữ quan hệ theo nguồn hiện hành").set_value("Authored UI confirmation test")
    next(item for item in view.button if item.label == "Xác nhận lại căn cứ nguồn").click().run()
    assert not view.exception and captures[-1]["plans"] and not captures[-1]["review_required"]
    saved = load_checkpoint(view.session_state.studio_checkpoint)
    assert saved["event"]["action"] == "SOURCE_EVIDENCE_RECONFIRMED"
    assert saved["event"]["before"] != saved["event"]["after"]
