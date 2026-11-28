"""Prepared two-stage responses test integrity, not model semantics or human labels."""

from copy import deepcopy
import json
from pathlib import Path

import pytest

from eqcr import ollama, storage
from eqcr.models import SourceRef
from eqcr.quantum_example import ticket_example
from eqcr.quantum_tradeoff import Architecture, Preferences, analyze
from eqcr.studio_evidence import EvidenceReviewRequired, binding_issues
from eqcr.studio_extraction import decide_proposal, extract_proposals, proposal_issues
from eqcr.studio_semantics import ClauseFrame, review_issues
from eqcr.studio_sentence_extraction import (MAX_CLAIMS, build_claim_request, build_frame_request, check_processing,
                                            source_units)
from eqcr.studio_sessions import save_checkpoint, load_checkpoint


def model(text="Customer Profile must encrypt personal data. Operations Reporting must recover within 90 seconds.", kind="NFR"):
    data = ticket_example().model_dump(mode="json")
    data["requirements"].append({"id": "SENTENCE_TEST", "text": text, "kind": kind})
    return Architecture.model_validate(data)


def provider(monkeypatch, tmp_path, *, primary=None, frames=None, fail_frame=False):
    monkeypatch.setattr(storage, "ARTIFACT_ROOT", tmp_path)
    monkeypatch.setattr(ollama, "list_model_details", lambda: [{"name": "qwen3:4b", "digest": "a" * 64}])
    monkeypatch.setattr(ollama, "get_ollama_version", lambda: "TEST_ONLY_RUNTIME")
    calls = []
    frame_number = 0

    def respond(endpoint, *, payload, timeout):
        nonlocal frame_number
        calls.append(payload)
        if "results" in payload["format"]["properties"]:
            body = primary if primary is not None else {"results": [
                {"unit_id": "U001", "claims": [{"characteristic": "Security", "component_ids": ["PROFILE"]}]},
                {"unit_id": "U002", "claims": [{"characteristic": "Reliability", "component_ids": ["REPORT"]}]}]}
        else:
            if fail_frame:
                raise ollama.OllamaError("TEST_ONLY_FRAME_FAILURE")
            defaults = [{"subject": "Customer Profile", "action": "encrypt", "object": None, "condition": None,
                         "modality": "must", "statement_kind": "OBLIGATION", "effect": "QUALITY_OBLIGATION"},
                        {"subject": "Operations Reporting", "action": "recover", "object": None, "condition": None,
                         "modality": "must", "statement_kind": "OBLIGATION", "effect": "QUALITY_OBLIGATION"}]
            body = (frames or defaults)[min(frame_number, len(frames or defaults) - 1)]
            frame_number += 1
        return {"model": "qwen3:4b", "done_reason": "stop", "eval_count": 15, "message": {"content": json.dumps(body)}}

    monkeypatch.setattr(ollama, "_request", respond)
    return calls


def accept(m, p, **kwargs):
    return decide_proposal(m, p, action=kwargs.pop("action", "APPROVE"), actor="TEST_ONLY_NOT_HUMAN_LABEL",
        rationale="Prepared technical decision, not independent semantic annotation", semantic_confirmed=True,
        provenance="PREPARED_FIXTURE", **kwargs)


def test_sentence_offsets_keep_decimal_semicolon_and_unicode_and_do_not_become_atomic_truths():
    m = model("Customer Profile handles a p95 of 1.2 seconds; no measurement exists.\n Operations Reporting then recovers.")
    units = source_units(m, ["SENTENCE_TEST"])
    assert len(units) == 2 and "1.2 seconds;" in units[0]["text"]
    for u in units:
        assert m.requirements[-1].text[u["start"]:u["end"]] == u["text"]
    with pytest.raises(ValueError, match="24"):
        source_units(model("A. " * 25), ["SENTENCE_TEST"])


def test_primary_request_exposes_schema_to_model_and_keeps_claim_fields_small():
    request, units = build_claim_request(model(), ["SENTENCE_TEST"], "QUALITY")
    assert json.loads(request["messages"][1]["content"])["units"] == units
    assert '"results"' in request["messages"][0]["content"]
    fields = request["format"]["properties"]["results"]["items"]["properties"]["claims"]["items"]["properties"]
    assert set(fields) == {"characteristic", "component_ids"}
    assert request["options"]["temperature"] == 0
    with pytest.raises(ValueError):
        build_claim_request(model(kind="FR"), ["SENTENCE_TEST"], "QUALITY")


def test_frame_uses_actual_source_names_and_does_not_receive_proposed_mode_or_locality():
    m = model("Ticket Router must wait for Ticket Completion.", "FR")
    unit = source_units(m, ["SENTENCE_TEST"])[0]
    request = build_frame_request(m, unit, "INTERACTION", {"source": "ROUTE", "target": "COMPLETE", "mode": "ASYNC", "local_transaction": True})
    body = json.loads(request["messages"][1]["content"])
    assert "mode" not in body["unverified_focus"] and "local_transaction" not in body["unverified_focus"]
    assert request["format"]["properties"]["subject"]["enum"] == ["Ticket Router", "Ticket Completion", None]
    assert "supports_claim" not in request["format"]["properties"]


def test_both_raw_stages_preserved_and_drafts_never_mutate_optimizer(tmp_path, monkeypatch):
    calls = provider(monkeypatch, tmp_path)
    m = model()
    before = analyze(m, Preferences())
    updates = []
    result = extract_proposals(m, ["SENTENCE_TEST"], "QUALITY", method="SENTENCE", progress=updates.append)
    assert len(calls) == 3 and len(updates) == 3
    assert result["prompt_version"] == "STUDIO-EXTRACT@3" and result["tokens"] == 45
    assert all(p["status"] == "REVIEW_REQUIRED" and not p["issues"] for p in result["proposals"])
    assert analyze(m, Preferences()) == before
    root = tmp_path / "quantum-studio/extractions" / result["id"]
    assert json.loads((root / "response.json").read_text())["message"]["content"] == json.loads((root / "claims-response.json").read_text())["message"]["content"]
    for index, p in enumerate(result["proposals"], 1):
        assert (root / f"frame-{index:03d}-request.json").exists()
        assert (root / f"frame-{index:03d}-response.json").exists()
        assert check_processing(m, p["processing"], p["payload"]) == p["payload"]


def test_review_preserves_separate_claim_citation_and_review_origins_and_reloads(tmp_path, monkeypatch):
    provider(monkeypatch, tmp_path)
    m = model()
    run = extract_proposals(m, ["SENTENCE_TEST"], "QUALITY", method="SENTENCE")
    proposal = run["proposals"][0]
    changed, event = accept(m, proposal)
    assert analyze(changed, Preferences()) != analyze(m, Preferences())
    record = changed.requirements[-1].quality_allocations[0].semantic_reviews[0]
    assert record.proposal_provenance == record.claim_provenance == "LLM_PROPOSAL"
    assert record.provenance == "PREPARED_FIXTURE" and record.processing == proposal["processing"]
    assert record.source_ref.quote == proposal["processing"]["unit"]["text"]
    assert not review_issues(changed, record) and event["processing"] == record.processing
    checkpoint = save_checkpoint(changed, event=event, proposals=run["proposals"])
    assert Architecture.model_validate(load_checkpoint(checkpoint)["architecture"]) == changed
    tampered = changed.model_dump(mode="json")
    tampered["requirements"][-1]["quality_allocations"][0]["semantic_reviews"][0]["processing"]["raw_claim"]["component_ids"] = ["LOGIN"]
    with pytest.raises(EvidenceReviewRequired):
        analyze(Architecture.model_validate(tampered), Preferences())


def test_relation_citation_is_a_deterministic_source_lookup_not_a_generated_quote(tmp_path, monkeypatch):
    text = "Ticket Router must wait for Ticket Completion."
    primary = {"results": [{"unit_id": "U001", "claims": [{"source": "ROUTE", "target": "COMPLETE", "mode": "SYNC", "local_transaction": False}]}]}
    frames = [{"subject": "Ticket Router", "action": "wait", "object": "Ticket Completion", "condition": None,
               "modality": "must", "statement_kind": "OBLIGATION", "effect": "WAIT_COMPLETION"}]
    provider(monkeypatch, tmp_path, primary=primary, frames=frames)
    m = model(text, "FR")
    run = extract_proposals(m, ["SENTENCE_TEST"], "INTERACTION", method="SENTENCE")
    changed, _ = accept(m, run["proposals"][0])
    binding = changed.interactions[1].evidence
    assert binding.citation_provenance == "DETERMINISTIC_TRANSFORMATION"
    assert binding.semantic_review.claim_provenance == "LLM_PROPOSAL" and binding.review_provenance == "PREPARED_FIXTURE"
    assert not binding_issues(changed, binding, collection="interactions", item=changed.interactions[1])


def test_exemption_or_background_frame_cannot_silently_delete_or_validate_first_claim(tmp_path, monkeypatch):
    text = "Operations Reporting is not required to recover."
    primary = {"results": [{"unit_id": "U001", "claims": [{"characteristic": "Reliability", "component_ids": ["REPORT"]}]}]}
    frames = [{"subject": "Operations Reporting", "action": "recover", "object": None, "condition": None,
               "modality": "not required", "statement_kind": "EXEMPTION", "effect": "NONE"}]
    provider(monkeypatch, tmp_path, primary=primary, frames=frames)
    m = model(text)
    p = extract_proposals(m, ["SENTENCE_TEST"], "QUALITY", method="SENTENCE")["proposals"][0]
    assert p["payload"]["characteristic"] == "Reliability" and p["payload"]["disposition"] == "AMBIGUOUS" and p["issues"]
    with pytest.raises(ValueError):
        accept(m, p)
    exclusion = deepcopy(p["payload"])
    exclusion.update(disposition="OUT_OF_SCOPE", characteristic=None, component_ids=[])
    unchanged, event = accept(m, p, action="CORRECT", corrected=exclusion)
    assert unchanged == m and event["effect_status"] == "NO_ACTIVE_EFFECT"


def test_local_transaction_frame_cannot_support_separation_even_with_matching_endpoints(tmp_path, monkeypatch):
    text = "Ticket Router and Ticket Completion must share a local atomic transaction."
    primary = {"results": [{"unit_id": "U001", "claims": [{"left": "ROUTE", "right": "COMPLETE"}]}]}
    frames = [{"subject": "Ticket Router", "action": "share", "object": "Ticket Completion", "condition": None,
               "modality": "must", "statement_kind": "OBLIGATION", "effect": "LOCAL_ATOMIC_TRANSACTION"}]
    provider(monkeypatch, tmp_path, primary=primary, frames=frames)
    m = model(text)
    p = extract_proposals(m, ["SENTENCE_TEST"], "SEPARATION", method="SENTENCE")["proposals"][0]
    with pytest.raises(ValueError, match="Hard separation"):
        accept(m, p)


@pytest.mark.parametrize("target", ["raw_claim", "raw_frame", "payload", "unit"])
def test_modified_raw_or_normalized_origin_requires_reextract_or_reviewed_correction(tmp_path, monkeypatch, target):
    provider(monkeypatch, tmp_path)
    m = model()
    p = extract_proposals(m, ["SENTENCE_TEST"], "QUALITY", method="SENTENCE")["proposals"][0]
    if target == "raw_claim":
        p["processing"]["raw_claim"]["component_ids"] = ["LOGIN"]
    elif target == "raw_frame":
        p["processing"]["raw_frame"]["action"] = "wrong"
    elif target == "unit":
        p["processing"]["unit"]["start"] += 1
    else:
        p["payload"]["component_ids"] = ["LOGIN"]
    with pytest.raises(ValueError):
        accept(m, p)


def test_identical_quotes_have_unambiguous_recorded_offsets_not_first_string_match(tmp_path, monkeypatch):
    text = "Customer Profile must encrypt personal data. Customer Profile must encrypt personal data."
    primary = {"results": [{"unit_id": u, "claims": [{"characteristic": "Security", "component_ids": ["PROFILE"]}]} for u in ["U001", "U002"]]}
    frame = {"subject": "Customer Profile", "action": "encrypt", "object": None, "condition": None,
             "modality": "must", "statement_kind": "OBLIGATION", "effect": "QUALITY_OBLIGATION"}
    provider(monkeypatch, tmp_path, primary=primary, frames=[frame, frame])
    m = model(text)
    run = extract_proposals(m, ["SENTENCE_TEST"], "QUALITY", method="SENTENCE")
    p = run["proposals"][1]
    assert not p["issues"]
    changed, _ = accept(m, p)
    record = changed.requirements[-1].quality_allocations[0].semantic_reviews[0]
    assert record.source_ref.start > text.find(p["payload"]["quote"])
    assert proposal_issues(m, "SENTENCE_TEST", p["payload"], structured=True)  # Legacy unanchored quote still ambiguous.
    assert not review_issues(changed, record)


def test_duplicate_claims_remain_explicit_and_cannot_be_applied_twice(tmp_path, monkeypatch):
    claim = {"characteristic": "Security", "component_ids": ["PROFILE"]}
    primary = {"results": [{"unit_id": "U001", "claims": [claim, claim]}, {"unit_id": "U002", "claims": []}]}
    frame = {"subject": "Customer Profile", "action": "encrypt", "object": None, "condition": None,
             "modality": "must", "statement_kind": "OBLIGATION", "effect": "QUALITY_OBLIGATION"}
    provider(monkeypatch, tmp_path, primary=primary, frames=[frame, frame])
    m = model()
    first, duplicate = extract_proposals(m, ["SENTENCE_TEST"], "QUALITY", method="SENTENCE")["proposals"]
    assert duplicate["duplicate_of_proposal_id"] == first["id"]
    with pytest.raises(ValueError, match="trùng"):
        accept(m, duplicate)


def test_missing_unknown_unit_rows_are_reported_and_do_not_acquire_citations(tmp_path, monkeypatch):
    primary = {"results": [{"unit_id": "NOT_REAL", "claims": [{"characteristic": "Security", "component_ids": ["PROFILE"]}]}]}
    provider(monkeypatch, tmp_path, primary=primary)
    run = extract_proposals(model(), ["SENTENCE_TEST"], "QUALITY", method="SENTENCE")
    assert not run["proposals"] and run["missing_unit_ids"] == ["U001", "U002"] and run["run_issues"]


def test_frame_failure_keeps_primary_response_and_failed_stage_with_no_evidence(tmp_path, monkeypatch):
    provider(monkeypatch, tmp_path, fail_frame=True)
    allocated = []
    with pytest.raises(ollama.OllamaError, match="FRAME_FAILURE"):
        extract_proposals(model(), ["SENTENCE_TEST"], "QUALITY", method="SENTENCE", on_run_allocated=allocated.append)
    manifest = json.loads((tmp_path / "quantum-studio/extractions" / allocated[0] / "manifest.json").read_text())
    assert manifest["status"] == "FAILED" and manifest["stages"][-1]["status"] == "FAILED" and not manifest["proposals"]
    assert (tmp_path / "quantum-studio/extractions" / allocated[0] / "response.json").exists()


def test_ui_exposes_both_methods_and_renders_sentence_lineage_without_raw_json(tmp_path, monkeypatch):
    from streamlit.testing.v1 import AppTest
    from eqcr import studio_canvas

    m = model("Customer Profile must encrypt personal data.")
    primary = {"results": [{"unit_id": "U001", "claims": [{"characteristic": "Security", "component_ids": ["PROFILE"]}]}]}
    provider(monkeypatch, tmp_path, primary=primary)
    monkeypatch.setattr(studio_canvas, "render_board", lambda **kwargs: None)
    view = AppTest.from_file(Path(__file__).parents[1] / "app.py", default_timeout=30)
    view.session_state.architecture = m
    view.run()
    next(w for w in view.multiselect if w.label == "Nguồn gửi Ollama").set_value(["SENTENCE_TEST"]).run()
    next(w for w in view.button if w.label == "Phân tích bằng Ollama").click().run()
    assert not view.exception and view.session_state.studio_last_inference["method"] == "SENTENCE"
    assert any("quote tra từ nguồn" in w.value for w in view.caption)
    assert not view.session_state.architecture.requirements[-1].quality_allocations
