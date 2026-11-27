"""Test-only coverage for P2 preflight, structural reporting and export integrity."""

import hashlib
import json
from pathlib import Path

import pytest

from eqcr.ollama import PROMPT_VERSION
from eqcr.p2_experiment import (
    P2ExperimentError,
    P2IndependentAnnotationBlocked,
    evaluate_p2_structure,
    export_p2_proposal_run,
    p2_readiness_status,
    validate_p2_proposal_bundle,
)
from eqcr.p2_protocol import (
    build_blind_annotation_template,
    lock_blind_annotation,
    source_bundle_sha256,
    verify_blind_annotation_lock,
)
from scripts.run_p2_experiment import main
from eqcr.tutor_support import get_tutor_support_fixture


def _locked_annotation(raw):
    submission = build_blind_annotation_template(raw)
    submission.update(
        {
            "reviewer_id": "test-only-reviewer",
            "source_only_attested": True,
            "no_prior_model_output_exposure": True,
            "unresolved_requirement_ids": [item["id"] for item in raw["requirements"]],
        }
    )
    return lock_blind_annotation(raw, submission, locked_at="2026-01-01T00:00:00+00:00")


def _test_bundle(raw, lock):
    return {
        "model": "qwen3:4b",
        "response_model": "qwen3:4b",
        "prompt_version": PROMPT_VERSION,
        "input_sha256": source_bundle_sha256(raw),
        "inference_started_at_utc": "2026-01-01T00:00:01+00:00",
        "inference_completed_at_utc": "2026-01-01T00:00:02+00:00",
        "generation_parameters": {"temperature": 0},
        "raw_response": "TEST_ONLY_NOT_MODEL_OUTPUT",
        "raw_response_sha256": hashlib.sha256(b"TEST_ONLY_NOT_MODEL_OUTPUT").hexdigest(),
        "provenance": "TEST_ONLY_NOT_MODEL_OUTPUT",
        "blind_annotation_lock": lock,
        "proposals": [],
        "evidence_proposals": [],
        "boundary_hypotheses": [],
    }


def test_p2_readiness_records_external_annotation_blocker_without_calling_a_model():
    raw = get_tutor_support_fixture()["raw_requirements"]
    status = p2_readiness_status(raw, None)
    assert status == {
        "status": "P2_BLOCKED_INDEPENDENT_ANNOTATION",
        "reason": "No verified source-only lock is available for this exact case and source hash.",
    }
    with pytest.raises(P2IndependentAnnotationBlocked):
        validate_p2_proposal_bundle(raw, _test_bundle(raw, None), allow_test_only=True)


def test_ready_to_run_command_stops_with_explicit_blocker_before_ollama_without_lock(tmp_path, monkeypatch, capsys):
    lock_path = tmp_path / "unlocked.json"
    lock_path.write_text("{}", encoding="utf-8")

    def unexpected_model_check():
        raise AssertionError("Model availability must not be checked before a verified independent lock.")

    monkeypatch.setattr("eqcr.p2_experiment.list_model_details", unexpected_model_check)
    exit_code = main(["--annotation-lock", str(lock_path)])
    captured = capsys.readouterr()
    assert exit_code == 3
    assert '"status": "P2_BLOCKED_INDEPENDENT_ANNOTATION"' in captured.out


def test_p2_readiness_rejects_a_reviewer_who_does_not_attest_to_no_prior_model_exposure():
    raw = get_tutor_support_fixture()["raw_requirements"]
    submission = build_blind_annotation_template(raw)
    submission.update({"reviewer_id": "exposed-reviewer", "source_only_attested": True})
    with pytest.raises(ValueError, match="have not seen model output"):
        lock_blind_annotation(raw, submission, locked_at="2026-01-01T00:00:00+00:00")


def test_blind_annotation_lock_detects_metadata_tampering():
    raw = get_tutor_support_fixture()["raw_requirements"]
    locked = _locked_annotation(raw)
    assert verify_blind_annotation_lock(raw, locked)

    changed_time = json.loads(json.dumps(locked))
    changed_time["lock"]["locked_at"] = "2026-01-02T00:00:00+00:00"
    assert not verify_blind_annotation_lock(raw, changed_time)

    changed_exposure = json.loads(json.dumps(locked))
    changed_exposure["lock"]["exposure_status"] = "EXPOSED"
    assert not verify_blind_annotation_lock(raw, changed_exposure)


@pytest.mark.parametrize("locked_at", ["2026-01-01T00:00:00", "not-a-timestamp"])
def test_blind_annotation_lock_rejects_invalid_or_timezone_naive_timestamp(locked_at):
    raw = get_tutor_support_fixture()["raw_requirements"]
    submission = build_blind_annotation_template(raw)
    submission.update(
        {
            "reviewer_id": "test-only-reviewer",
            "source_only_attested": True,
            "no_prior_model_output_exposure": True,
            "unresolved_requirement_ids": [item["id"] for item in raw["requirements"]],
        }
    )
    with pytest.raises(ValueError, match="timezone"):
        lock_blind_annotation(raw, submission, locked_at=locked_at)


def test_proposal_bundle_version_hash_and_timestamp_are_checked():
    raw = get_tutor_support_fixture()["raw_requirements"]
    lock = _locked_annotation(raw)
    bundle = _test_bundle(raw, lock)
    validate_p2_proposal_bundle(raw, bundle, allow_test_only=True)
    bundle["prompt_version"] = "old-prompt"
    with pytest.raises(P2ExperimentError, match="Expected prompt/schema version"):
        validate_p2_proposal_bundle(raw, bundle, allow_test_only=True)

    bundle = _test_bundle(raw, lock)
    bundle["inference_started_at_utc"] = "2025-12-31T23:59:59+00:00"
    with pytest.raises(P2ExperimentError, match="must be locked before"):
        validate_p2_proposal_bundle(raw, bundle, allow_test_only=True)


def test_structural_evaluation_reports_exact_spans_and_errors_without_semantic_metrics():
    raw = get_tutor_support_fixture()["raw_requirements"]
    lock = _locked_annotation(raw)
    bundle = _test_bundle(raw, lock)
    source = {item["id"]: item["source_ref"] for item in raw["requirements"]}
    bundle["proposals"] = [
        {
            "id": "P01", "model_proposal_id": "m1", "name": "Search", "activity": "Search", "operation": "Filter",
            "requirement_ids": ["FR-01"], "source_refs": [source["FR-01"]],
        },
        {
            "id": "P02", "model_proposal_id": "m2", "name": "Search", "activity": "Search", "operation": "Filter",
            "requirement_ids": ["FR-01"], "source_refs": [source["FR-01"]],
        },
    ]
    bundle["normalized_requirements"] = [
        {"id": "FR-01", "source_ref": source["FR-01"]},
        {"id": "FR-99", "source_ref": None},
    ]
    bundle["evidence_proposals"] = [
        {
            "id": "E01", "subject_requirement_id": "FR-02", "object_requirement_id": "FR-03",
            "predicate": "SHARES_STATE_OR_INVARIANT", "proposed_status": "PRESENT",
            "source_requirement_ids": ["FR-02", "FR-03"],
            "source_refs": [source["FR-02"], source["FR-03"]],
        },
        {
            "id": "E02", "subject_requirement_id": "FR-03", "object_requirement_id": "FR-02",
            "predicate": "SHARES_STATE_OR_INVARIANT", "proposed_status": "UNKNOWN",
            "source_requirement_ids": ["FR-03", "FR-02"],
            "source_refs": [source["FR-03"], source["FR-02"]],
        },
        {
            "id": "E03", "subject_requirement_id": "FR-04", "object_requirement_id": "FR-04",
            "predicate": "UNREGISTERED", "proposed_status": "PRESENT",
            "source_requirement_ids": ["FR-04"], "source_refs": [source["FR-04"]],
        },
    ]
    report = evaluate_p2_structure(raw, bundle)
    assert report["provenance"] == "DETERMINISTIC_TRANSFORMATION"
    assert report["citation_audit"]["requirement_citations_resolved_to_exact_source_ref"] == 8
    assert report["citation_audit"]["requirement_citation_count"] == 9
    assert report["error_counts_by_type"]["RESPONSIBILITY_DUPLICATE_SHAPE"] == 2
    assert report["error_counts_by_type"]["NORMALIZED_REQUIREMENT_CITATION_INVALID"] == 1
    assert report["responsibility_mapping"]["proposal_uncovered_requirement_ids"] == [
        "FR-02", "FR-03", "FR-04", "FR-05", "FR-06"
    ]
    assert report["error_counts_by_type"]["RELATION_DUPLICATE_OR_STATUS_CONFLICT"] == 2
    assert report["error_counts_by_type"]["RELATION_REFLEXIVE"] == 1
    assert report["error_counts_by_type"]["RELATION_PREDICATE_UNREGISTERED"] == 1
    assert report["semantic_evaluation"]["status"] == "NOT_MEASURED_NO_ADJUDICATED_REFERENCE"
    assert report["semantic_evaluation"]["metrics"] is None


def test_responsibility_mapping_coverage_is_independent_of_citation_validity():
    raw = get_tutor_support_fixture()["raw_requirements"]
    bundle = _test_bundle(raw, _locked_annotation(raw))
    bundle["proposals"] = [
        {
            "id": "P-FR04",
            "model_proposal_id": "test-proposal-04",
            "name": "Test responsibility",
            "activity": "Test activity",
            "operation": "Test operation",
            "requirement_ids": ["FR-04"],
            "source_refs": [],
        }
    ]

    report = evaluate_p2_structure(raw, bundle)

    assert report["responsibility_mapping"]["coverage_by_requirement"]["FR-04"] == 1
    assert "FR-04" not in report["responsibility_mapping"]["proposal_uncovered_requirement_ids"]
    assert "independently of citation validity" in report["responsibility_mapping"]["interpretation"]
    assert report["error_counts_by_type"]["RESPONSIBILITY_CITATION_INVALID"] == 1


def test_structural_evaluator_reports_malformed_id_types_without_raw_type_errors():
    raw = get_tutor_support_fixture()["raw_requirements"]
    bundle = _test_bundle(raw, _locked_annotation(raw))
    bundle["proposals"] = [
        {
            "id": "P-MALFORMED",
            "model_proposal_id": "test-malformed-proposal",
            "name": "Malformed test role",
            "activity": "Test activity",
            "operation": "Test operation",
            "requirement_ids": [["FR-01"], "FR-04"],
            "source_refs": [],
        }
    ]
    bundle["normalized_requirements"] = [{"id": [], "source_ref": None}]
    bundle["evidence_proposals"] = [
        {
            "id": "E-MALFORMED",
            "model_proposal_id": "test-malformed-evidence",
            "subject_requirement_id": [],
            "object_requirement_id": "FR-04",
            "predicate": "SHARES_STATE_OR_INVARIANT",
            "proposed_status": "PRESENT",
            "source_requirement_ids": [["FR-04"]],
            "source_refs": [],
        }
    ]
    bundle["boundary_hypotheses"] = [
        {
            "id": "B-MALFORMED",
            "model_proposal_id": "test-malformed-boundary",
            "requirement_ids": [["FR-01"], "FR-02"],
            "source_requirement_ids": [["FR-01"], "FR-02"],
            "source_refs": [],
        }
    ]

    report = evaluate_p2_structure(raw, bundle)

    expected_errors = {
        "RESPONSIBILITY_REQUIREMENT_ID_INVALID_TYPE",
        "NORMALIZED_REQUIREMENT_CITATION_INVALID",
        "RELATION_ENDPOINT_UNKNOWN",
        "RELATION_SOURCE_ID_INVALID_TYPE",
        "BOUNDARY_REQUIREMENT_SET_INVALID",
        "BOUNDARY_SOURCE_ID_INVALID_TYPE",
    }
    assert expected_errors <= set(report["error_counts_by_type"])
    assert report["responsibility_mapping"]["coverage_by_requirement"]["FR-04"] == 1


def test_structural_evaluator_rejects_non_object_rows_with_domain_error():
    raw = get_tutor_support_fixture()["raw_requirements"]
    bundle = _test_bundle(raw, _locked_annotation(raw))
    bundle["proposals"] = [None]

    with pytest.raises(P2ExperimentError, match="must be a JSON object"):
        evaluate_p2_structure(raw, bundle)


def test_reproducibility_export_contains_hash_manifest_and_test_only_provenance(tmp_path):
    raw = get_tutor_support_fixture()["raw_requirements"]
    lock = _locked_annotation(raw)
    bundle = _test_bundle(raw, lock)
    evaluation = evaluate_p2_structure(raw, bundle)
    run_dir = export_p2_proposal_run(
        raw,
        lock,
        bundle,
        evaluation,
        output_root=tmp_path / "runs",
        repo_root=Path(__file__).resolve().parents[1],
        ollama_version="TEST_ONLY",
        model_metadata={"name": "qwen3:4b", "digest": "TEST_ONLY"},
        allow_test_only=True,
    )
    manifest = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
    checksum_map = json.loads((run_dir / "checksums.sha256.json").read_text(encoding="utf-8"))
    assert manifest["experiment_status"] == "P2_MODEL_PROPOSAL_COMPLETE_PENDING_HUMAN_REVIEW"
    assert manifest["semantic_evaluation_status"] == "NOT_MEASURED_NO_ADJUDICATED_REFERENCE"
    assert manifest["source_bundle_sha256"] == source_bundle_sha256(raw)
    assert checksum_map["manifest.json"] == hashlib.sha256((run_dir / "manifest.json").read_bytes()).hexdigest()
    assert (run_dir / f"{manifest['run_id']}-reproducibility.zip").exists()
