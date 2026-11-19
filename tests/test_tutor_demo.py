"""Exploratory Tutor demo gates; model-shaped data below is test-only unless _request is mocked."""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

import eqcr.ollama as ollama
from eqcr.ollama import OllamaError, propose_responsibilities
from eqcr.p2_experiment import P2ExperimentError, evaluate_p2_structure, validate_p2_proposal_bundle
from eqcr.p2_protocol import source_bundle_sha256
from eqcr.p2_review import apply_tutor_demo_review
from eqcr.pipeline import run_pipeline
from eqcr.storage import make_export_zip, save_run, verify_export_zip
from eqcr import storage
from eqcr.tutor_support import get_tutor_support_fixture


def _model_response(raw):
    return {
        "context_summary": "Test-only response for the mock request path.",
        "normalized_requirements": [
            {"id": item["id"], "normalized_text": item["text"]} for item in raw["requirements"]
        ],
        "proposals": [
            {
                "id": f"proposal-{index}",
                "name": f"Test role {index}",
                "activity": f"Test activity {index}",
                "operation": f"Test operation {index}",
                "requirement_ids": [item["id"]],
                "decomposition_rationale": "Test-only mock output.",
            }
            for index, item in enumerate(raw["requirements"], start=1)
        ],
        "evidence_proposals": [
            {
                "id": "E1",
                "subject_requirement_id": "FR-05",
                "predicate": "SHARES_STATE_OR_INVARIANT",
                "object_requirement_id": "FR-06",
                "proposed_status": "PRESENT",
                "source_requirement_ids": ["FR-05", "FR-06"],
                "rationale": "Test-only mock output.",
            }
        ],
        "boundary_hypotheses": [
            {
                "id": "B1",
                "requirement_ids": ["FR-04", "FR-05"],
                "boundary_rationale": "Test-only mock output.",
                "source_requirement_ids": ["FR-04", "FR-05"],
            }
        ],
    }


def _test_bundle(fixture):
    raw = fixture["raw_requirements"]
    proposal_rows = _model_response(raw)
    by_id = {item["id"]: item for item in raw["requirements"]}
    proposals = []
    for index, row in enumerate(proposal_rows["proposals"], start=1):
        requirement_id = row["requirement_ids"][0]
        proposals.append(
            {
                **row,
                "model_proposal_id": f"mock-{index}",
                "requirement_ids_valid": True,
                "source_ids_valid": True,
                "source_spans_resolved": True,
                "responsibility_id_valid_and_unique": True,
                "source_refs": [by_id[requirement_id]["source_ref"]],
                "source_ref": by_id[requirement_id]["source_ref"],
            }
        )
    source_refs = [by_id[item]["source_ref"] for item in ("FR-05", "FR-06")]
    evidence = {
        **proposal_rows["evidence_proposals"][0],
        "model_proposal_id": "mock-evidence-1",
        "id_valid_and_unique": True,
        "subject_requirement_id_valid": True,
        "object_requirement_id_valid": True,
        "source_refs_valid": True,
        "citation_covers_endpoints": True,
        "predicate_in_registry": True,
        "self_relation": False,
        "source_refs": source_refs,
    }
    boundary = {
        **proposal_rows["boundary_hypotheses"][0],
        "model_proposal_id": "mock-boundary-1",
        "id_valid_and_unique": True,
        "requirement_ids_valid": True,
        "source_refs_valid": True,
        "source_covers_hypothesis": True,
        "source_refs": [by_id[item]["source_ref"] for item in ("FR-04", "FR-05")],
    }
    return {
        "model": "test-only",
        "response_model": "test-only",
        "prompt_version": "test-only",
        "input_sha256": source_bundle_sha256(raw),
        "inference_started_at_utc": "2026-01-01T00:00:01+00:00",
        "inference_completed_at_utc": "2026-01-01T00:00:02+00:00",
        "context_summary": "TEST_ONLY_NOT_MODEL_OUTPUT",
        "normalized_requirements": [],
        "proposals": proposals,
        "evidence_proposals": [evidence],
        "boundary_hypotheses": [boundary],
        "provenance": "TEST_ONLY_NOT_MODEL_OUTPUT",
        "blind_annotation_lock": None,
        "execution_mode": "EXPLORATORY_UNBLINDED_DEMO",
        "research_eligibility": "EXCLUDED_FROM_BLIND_RESEARCH",
        "run_id": "run-test-only-tutor-demo",
    }


def _review_payload(bundle, *, actor="test-demo-actor"):
    return {
        "demo_unblinded_acknowledged": True,
        "demo_actor": actor,
        "responsibilities": [
            {
                "proposal_id": item["id"],
                "action": "APPROVE",
                "reason": "TEST_ONLY: explicit fixture decision exercises the gate.",
                "source": "TEST_ONLY",
                "actor": actor,
            }
            for item in bundle["proposals"]
        ],
        "evidence": [
            {
                "proposal_id": "E1",
                "action": "APPROVE",
                "reason": "TEST_ONLY: explicit fixture decision exercises the gate.",
                "source": "TEST_ONLY",
                "actor": actor,
                "architecture_implication": "COLOCATE_CANDIDATE",
                "architecture_rationale": "TEST_ONLY: explicit reversible policy input.",
                "responsibility_pairs": [["R5", "R6"]],
            }
        ],
        "boundaries": [
            {
                "proposal_id": "B1",
                "action": "REJECT",
                "reason": "TEST_ONLY: boundary proposal is deliberately excluded.",
                "source": "TEST_ONLY",
                "actor": actor,
            }
        ],
    }


def test_tutor_inference_stays_lock_first_by_default_and_demo_requires_ack(monkeypatch):
    raw = get_tutor_support_fixture()["raw_requirements"]
    called = []

    def unexpected_request(*args, **kwargs):
        called.append((args, kwargs))
        raise AssertionError("The blind gate must fail before an Ollama request.")

    monkeypatch.setattr(ollama, "_request", unexpected_request)
    with pytest.raises(OllamaError, match="source-only annotation"):
        propose_responsibilities(raw, "qwen3:4b")
    with pytest.raises(OllamaError, match="explicit acknowledgement"):
        propose_responsibilities(raw, "qwen3:4b", demo_unblinded=True)
    assert called == []


def test_demo_calls_ollama_request_and_records_explicit_demo_provenance(monkeypatch):
    raw = get_tutor_support_fixture()["raw_requirements"]
    response_content = json.dumps(_model_response(raw))
    calls = []

    def fake_request(path, *, payload=None, timeout=12):
        calls.append((path, payload, timeout))
        if path == "/api/chat":
            return {"model": "qwen3:4b", "message": {"content": response_content}}
        if path == "/api/tags":
            return {"models": [{"name": "qwen3:4b", "digest": "test-digest", "size": 42}]}
        if path == "/api/version":
            return {"version": "test-version"}
        raise AssertionError(path)

    monkeypatch.setattr(ollama, "_request", fake_request)
    result = propose_responsibilities(
        raw,
        "qwen3:4b",
        demo_unblinded=True,
        demo_acknowledged=True,
    )
    assert [call[0] for call in calls] == ["/api/chat", "/api/tags", "/api/version"]
    assert calls[0][1]["model"] == "qwen3:4b"
    assert calls[0][2] == 180
    assert result["execution_mode"] == "EXPLORATORY_UNBLINDED_DEMO"
    assert result["research_eligibility"] == "EXCLUDED_FROM_BLIND_RESEARCH"
    assert result["blind_annotation_lock"] is None
    assert result["ollama_version"] == "test-version"
    assert result["model_digest"] == "test-digest"
    assert result["prompt_version"] == ollama.PROMPT_VERSION
    assert result["provenance"] == "LOCAL_OLLAMA_UNVERIFIED"
    assert all(
        item["status"] == "REVIEW_REQUIRED" and item["semantic_status"] == "NOT_ASSESSED"
        for item in result["proposals"]
    )


def test_blind_evaluator_rejects_any_unblinded_demo_bundle():
    raw = get_tutor_support_fixture()["raw_requirements"]
    bundle = _test_bundle(get_tutor_support_fixture())
    with pytest.raises(P2ExperimentError, match="permanently excluded"):
        validate_p2_proposal_bundle(raw, bundle, allow_test_only=True)
    with pytest.raises(P2ExperimentError, match="cannot be evaluated as blind"):
        evaluate_p2_structure(raw, bundle)


def test_demo_review_requires_real_acknowledgement_and_an_actor():
    fixture = get_tutor_support_fixture()
    bundle = _test_bundle(fixture)
    payload = _review_payload(bundle)
    payload["demo_unblinded_acknowledged"] = False
    with pytest.raises(ValueError, match="explicit acknowledgement"):
        apply_tutor_demo_review(fixture, bundle, payload)
    payload["demo_unblinded_acknowledged"] = True
    payload["demo_actor"] = " "
    with pytest.raises(ValueError, match="actual demo stakeholder identifier"):
        apply_tutor_demo_review(fixture, bundle, payload)


def test_reviewed_test_only_evidence_enters_generic_optimizer_with_excluded_status():
    fixture = get_tutor_support_fixture()
    bundle = _test_bundle(fixture)
    reviewed_fixture, decisions = apply_tutor_demo_review(
        fixture,
        bundle,
        _review_payload(bundle),
    )
    artifacts = run_pipeline(
        reviewed_fixture,
        decisions=decisions,
        execution_mode="EXPLORATORY_UNBLINDED_DEMO",
    )
    assert reviewed_fixture["independent_annotation_lock"] is None
    assert reviewed_fixture["research_eligibility"] == "EXCLUDED_FROM_BLIND_RESEARCH"
    assert all(item["provenance"] == "P2_TEST_ONLY" for item in reviewed_fixture["responsibilities"])
    assert artifacts["metadata"]["execution_mode"] == "EXPLORATORY_UNBLINDED_DEMO"
    assert artifacts["metadata"]["research_eligibility"] == "EXCLUDED_FROM_BLIND_RESEARCH"
    policy_constraint = next(
        item for item in artifacts["constraints"]["items"] if item["origin"] == "ARCHITECTURAL_POLICY"
    )
    assert policy_constraint["evidence_ids"] == ["EV-E1-PAIR-01"]
    assert {policy_constraint["left"], policy_constraint["right"]} == {"R5", "R6"}
    assert policy_constraint["hardness"] == "SOFT"
    assert artifacts["partitions"]["enumerated_partition_count"] == 203
    assert artifacts["partitions"]["feasible_candidate_count"] == 203
    assert artifacts["validation_report"]["assertions"]["traceability_workflow_mappings_explicit"] is True
    assert {item["measurement_status"] for item in artifacts["quality_profiles"]["profiles"]} <= {
        "NOT_MEASURED",
        "INSUFFICIENT_EVIDENCE",
    }


def test_unknown_assertion_is_not_a_failure_when_case_has_no_unknown_evidence():
    artifacts = run_pipeline(
        get_tutor_support_fixture(),
        execution_mode="EXPLORATORY_UNBLINDED_DEMO",
    )

    assert artifacts["validation_report"]["assertions"]["unknown_is_not_false"] is None
    assert (
        artifacts["validation_report"]["assertion_applicability"]["unknown_is_not_false"]
        == "NOT_APPLICABLE_NO_UNKNOWN_EVIDENCE"
    )


def test_demo_run_storage_root_and_export_manifest_are_isolated(tmp_path):
    artifacts = run_pipeline(
        get_tutor_support_fixture(),
        execution_mode="EXPLORATORY_UNBLINDED_DEMO",
    )
    artifacts["metadata"]["run_id"] = "run-test-only-isolated"
    artifacts["metadata"]["research_eligibility"] = "EXCLUDED_FROM_BLIND_RESEARCH"
    demo_root = tmp_path / "demo-unblinded"
    path = save_run("run-test-only-isolated", artifacts, root=demo_root)
    assert path == demo_root / "run-test-only-isolated"
    assert (path / "metadata.json").exists()

    manifest = verify_export_zip(make_export_zip(artifacts))["manifest"]
    assert manifest["execution_mode"] == "EXPLORATORY_UNBLINDED_DEMO"
    assert manifest["research_eligibility"] == "EXCLUDED_FROM_BLIND_RESEARCH"


def test_tutor_ui_disables_model_until_unblinded_demo_acknowledgement():
    app = AppTest.from_file(Path(__file__).parents[1] / "app.py", default_timeout=30).run()
    next(button for button in app.button if button.label == "Load Tutor Support P2 case").click().run()
    app.session_state["ollama_models"] = ["qwen3:4b"]
    app.run()

    mode = next(radio for radio in app.radio if radio.label == "Tutor mode")
    mode.set_value("EXPLORATORY_UNBLINDED_DEMO").run()
    proposal_button = next(button for button in app.button if button.label == "Run local Ollama proposals")
    assert proposal_button.disabled is True
    acknowledgement = next(
        checkbox for checkbox in app.checkbox if checkbox.label.startswith("I acknowledge this Tutor run is unblinded")
    )
    acknowledgement.check().run()
    assert not app.exception
    proposal_button = next(button for button in app.button if button.label == "Run local Ollama proposals")
    assert proposal_button.disabled is False
    assert app.session_state["p2_blind_annotation_lock"] is None
    assert "EXPLORATORY_UNBLINDED_DEMO | NO_GOLD_LABELS | SEMANTIC_EVALUATION_NOT_PERFORMED" in [
        item.value for item in app.error
    ]


def test_tutor_demo_review_ui_recomputes_only_from_explicit_test_fixture_decisions(monkeypatch):
    fixture = get_tutor_support_fixture()
    pending = deepcopy(fixture)
    pending["responsibilities"] = []
    pending["evidence"] = [
        item for item in pending["evidence"] if item.get("predicate") == "independent_deployment_evidence"
    ]
    pending["relation_annotations"] = []
    pending["constraints"] = []
    pending["responsibility_review_complete"] = False
    bundle = _test_bundle(fixture)
    bundle["run_id"] = "run-test-only-ui-review"
    monkeypatch.setattr(storage, "save_run", lambda *args, **kwargs: Path("isolated-ui-test-run"))
    monkeypatch.setattr(storage, "save_snapshot", lambda *args, **kwargs: Path("isolated-ui-test-snapshot"))

    app = AppTest.from_file(Path(__file__).parents[1] / "app.py", default_timeout=30)
    app.session_state["fixture"] = pending
    app.session_state["run_fixture"] = pending
    app.session_state["artifacts"] = run_pipeline(
        pending,
        execution_mode="EXPLORATORY_UNBLINDED_DEMO",
    )
    app.session_state["run_id"] = "run-test-only-ui-review"
    app.session_state["snapshot_version"] = 1
    app.session_state["ollama_proposals"] = bundle
    app.session_state["tutor_mode"] = "EXPLORATORY_UNBLINDED_DEMO"
    app.session_state["tutor_demo_exposed"] = True
    app.run()
    assert not app.exception
    assert app.session_state["artifacts"]["partitions"]["feasible_candidate_count"] == 0

    review_key = f"tutor_review_json_{bundle['input_sha256'][:12]}"
    review_box = next(item for item in app.text_area if item.key == review_key)
    review_box.set_value(json.dumps(_review_payload(bundle))).run()
    actor = next(item for item in app.text_input if item.key == "tutor_demo_review_actor")
    actor.set_value("test-demo-actor").run()
    acknowledgement = next(
        item for item in app.checkbox if item.key == "tutor_demo_review_acknowledged"
    )
    acknowledgement.check().run()
    next(button for button in app.button if button.label == "Apply demo stakeholder review & recompute all stages").click().run()

    assert not app.exception
    artifacts = app.session_state["artifacts"]
    assert artifacts["metadata"]["demo_status"] == "DEMO_REVIEW_RECORDED"
    assert len(artifacts["responsibilities"]["items"]) == 6
    assert artifacts["partitions"]["feasible_candidate_count"] == 203
    assert any(item["origin"] == "ARCHITECTURAL_POLICY" for item in artifacts["constraints"]["items"])
    assert artifacts["metadata"]["research_eligibility"] == "EXCLUDED_FROM_BLIND_RESEARCH"

    before_groups = deepcopy(artifacts["partitions"]["selected_groups"])
    next(item for item in app.selectbox if item.label == "Subject responsibility").set_value("R4")
    next(item for item in app.selectbox if item.label == "Subject requirement").set_value("FR-04")
    next(item for item in app.selectbox if item.label == "Object responsibility").set_value("R5")
    next(item for item in app.selectbox if item.label == "Object requirement").set_value("FR-05")
    next(item for item in app.text_area if item.label == "Architectural candidate rationale").set_value(
        "TEST_ONLY UI revision rationale for the FR-04/FR-05 pair."
    )
    next(item for item in app.text_area if item.label == "Correction reason").set_value(
        "TEST_ONLY UI correction changes the reviewed endpoint pair."
    )
    revision_button = next(
        button
        for button in app.form_submit_button
        if button.label == "Record demo correction & recompute all stages"
    )
    revision_button.click().run()

    assert not app.exception
    revised = app.session_state["artifacts"]
    assert "demo_revision_audit" in revised, [item.value for item in app.error]
    revised_evidence = next(item for item in revised["evidence"]["items"] if item["id"] == "EV-E1-PAIR-01")
    assert revised_evidence["subject_id"] == "R4", revised_evidence
    assert revised_evidence["object_id"] == "R5"
    assert revised_evidence["subject_requirement_id"] == "FR-04"
    assert revised_evidence["object_requirement_id"] == "FR-05"
    assert revised["partitions"]["selected_groups"] != before_groups
    audit = revised["demo_revision_audit"]
    assert audit["actor_role"] == "DEMO_STAKEHOLDER"
    assert audit["source_requirement_ids"] == ["FR-04", "FR-05"]
    assert len(audit["before_artifacts_sha256"]) == 64
    assert len(audit["after_artifacts_sha256"]) == 64
    assert audit["recompute_scope"] == "FULL_PIPELINE_01_TO_10"
    assert revised["metadata"]["research_eligibility"] == "EXCLUDED_FROM_BLIND_RESEARCH"
