"""P2 coverage for a reviewed, non-PetClinic Tutor Support input path."""

import json
from pathlib import Path
import pytest

from eqcr.pipeline import run_pipeline
from eqcr.review import apply_evidence_relation_edit
from eqcr.ollama import OllamaError, propose_responsibilities
from eqcr.p2_protocol import (
    build_blind_annotation_template,
    lock_blind_annotation,
    source_bundle_sha256,
    verify_blind_annotation_lock,
)
from eqcr.p2_review import apply_tutor_human_review
from eqcr.tutor_support import get_tutor_support_fixture
from streamlit.testing.v1 import AppTest


def _test_blind_lock(raw):
    submission = build_blind_annotation_template(raw)
    submission["reviewer_id"] = "test-reviewer"
    submission["source_only_attested"] = True
    submission["no_prior_model_output_exposure"] = True
    return lock_blind_annotation(raw, submission, locked_at="2026-01-01T00:00:00+00:00")


def _proposal_data(fixture):
    raw = fixture["raw_requirements"]
    proposals = []
    normalized = []
    for index, requirement in enumerate(raw["requirements"], start=1):
        source_ref = requirement["source_ref"]
        proposals.append(
            {
                "id": f"P{index:02d}",
                "model_proposal_id": f"model-{index}",
                "name": f"Proposed responsibility {index}",
                "activity": f"Activity {index}",
                "operation": f"Operation {index}",
                "decomposition_rationale": "TEST-ONLY prepared proposal rationale.",
                "requirement_ids": [requirement["id"]],
                "requirement_ids_valid": True,
                "source_ids_valid": True,
                "source_spans_resolved": True,
                "responsibility_id_valid_and_unique": True,
                "source_refs": [source_ref],
                "source_ref": source_ref,
            }
        )
        normalized.append({"id": requirement["id"], "normalized_text": requirement["text"]})
    evidence = {
        "id": "E01",
        "model_proposal_id": "model-evidence-1",
        "subject_requirement_id": "FR-05",
        "predicate": "SHARES_STATE_OR_INVARIANT",
        "object_requirement_id": "FR-06",
        "proposed_status": "PRESENT",
        "source_requirement_ids": ["FR-05", "FR-06"],
        "rationale": "Test-only proposal input; the reviewer decision is separately supplied below.",
        "id_valid_and_unique": True,
        "subject_requirement_id_valid": True,
        "object_requirement_id_valid": True,
        "source_refs_valid": True,
        "citation_covers_endpoints": True,
        "predicate_in_registry": True,
        "self_relation": False,
        "source_refs": [
            next(item for item in raw["requirements"] if item["id"] == requirement_id)["source_ref"]
            for requirement_id in ("FR-05", "FR-06")
        ],
    }
    return {
        "model": "test-fixture-only",
        "provenance": "TEST_ONLY_NOT_MODEL_OUTPUT",
        "input_sha256": source_bundle_sha256(raw),
        "inference_started_at_utc": "2026-01-01T00:00:01+00:00",
        "inference_completed_at_utc": "2026-01-01T00:00:02+00:00",
        "context_summary": "Test-only model proposal bundle.",
        "normalized_requirements": normalized,
        "proposals": proposals,
        "evidence_proposals": [evidence],
        "boundary_hypotheses": [
            {
                "id": "B01",
                "model_proposal_id": "model-boundary-1",
                "requirement_ids": ["FR-04", "FR-05"],
                "boundary_rationale": "Test-only boundary hypothesis.",
                "source_requirement_ids": ["FR-04", "FR-05"],
                "id_valid_and_unique": True,
                "requirement_ids_valid": True,
                "source_refs_valid": True,
                "source_covers_hypothesis": True,
                "source_refs": [
                    next(item for item in raw["requirements"] if item["id"] == requirement_id)["source_ref"]
                    for requirement_id in ("FR-04", "FR-05")
                ],
            }
        ],
        "blind_annotation_lock": _test_blind_lock(raw),
    }


def _human_review(fixture, proposal_data, *, evidence_action="APPROVE"):
    responsibilities = [
        {
            "proposal_id": item["id"],
            "action": "APPROVE",
            "reason": "Unit test exercises the explicit approval gate.",
            "source": "TEST-ONLY-REVIEW",
            "actor": "test-reviewer",
        }
        for item in proposal_data["proposals"]
    ]
    evidence = [
        {
            "proposal_id": proposal_data["evidence_proposals"][0]["id"],
            "action": evidence_action,
            "reason": "Unit test exercises the evidence review gate.",
            "source": "TEST-ONLY-REVIEW",
            "actor": "test-reviewer",
            "architecture_implication": "COLOCATE_CANDIDATE",
            "architecture_rationale": "Test-only architectural rationale, not a Tutor Support finding.",
            "responsibility_pairs": [["R5", "R6"]],
        }
    ]
    boundaries = [
        {
            "proposal_id": proposal["id"],
            "action": "REJECT",
            "reason": "Unit test keeps boundary hypotheses out of optimizer input.",
            "source": "TEST-ONLY-REVIEW",
            "actor": "test-reviewer",
        }
        for proposal in proposal_data.get("boundary_hypotheses", [])
    ]
    if evidence_action == "CORRECT":
        evidence[0]["correction"] = {
            "subject_requirement_id": "FR-04",
            "predicate": "SHARES_STATE_OR_INVARIANT",
            "object_requirement_id": "FR-05",
            "status": "PRESENT",
            "source_requirement_ids": ["FR-04", "FR-05"],
            "rationale": "Unit test correction; not a domain label.",
            "architecture_implication": "COLOCATE_CANDIDATE",
            "architecture_rationale": "Test-only architecture rationale.",
            "responsibility_pairs": [["R4", "R5"]],
        }
    return {"responsibilities": responsibilities, "evidence": evidence, "boundaries": boundaries}


def _assert_hard_constraints_hold(artifacts):
    hard = [
        item
        for item in artifacts["constraints"]["items"]
        if item["enabled"] and item["hardness"] == "HARD"
    ]
    for candidate in artifacts["partitions"]["feasible_candidates"]:
        for constraint in hard:
            together = any(
                constraint["left"] in group and constraint["right"] in group
                for group in candidate["groups"]
            )
            assert (constraint["relation"] == "MUST_LINK") == together


def test_tutor_case_has_original_requirements_workflows_scenarios_and_exact_source_spans():
    fixture = get_tutor_support_fixture()
    raw = fixture["raw_requirements"]
    assert raw["case_id"] == "TUTOR-SUPPORT-P2-01"
    assert len(raw["requirements"]) == 6
    assert len(raw["workflows"]) == 4
    assert len(raw["scenarios"]) == 2
    assert all(
        item["text"][item["source_ref"]["start"] : item["source_ref"]["end"]]
        == item["source_ref"]["quote"]
        for item in raw["requirements"]
    )
    assert all(
        item["source_ref"]["quote"]
        == f"{item['name']}. Stimulus: {item['stimulus']} Measure: {item['response_measure']}. Target: {item['target']}."
        for item in raw["scenarios"]
    )
    assert "PetClinic" not in raw["context_description"]
    assert fixture["constraints"] == []


def test_app_can_load_the_tutor_support_case_without_streamlit_exceptions():
    app = AppTest.from_file(Path(__file__).parents[1] / "app.py", default_timeout=30).run()
    next(button for button in app.button if button.label == "Load Tutor Support P2 case").click().run()
    assert not app.exception
    assert app.session_state["fixture"]["raw_requirements"]["case_id"] == "TUTOR-SUPPORT-P2-01"
    app.session_state["ollama_models"] = ["qwen3:4b"]
    app.run()
    proposal_button = next(button for button in app.button if button.label == "Run local Ollama proposals")
    assert proposal_button.disabled is True
    assert app.session_state["p2_blind_annotation_lock"] is None


def test_unreviewed_proposals_do_not_create_optimizer_constraints():
    fixture = get_tutor_support_fixture()
    proposal_data = _proposal_data(fixture)
    reviewed_fixture, decisions = apply_tutor_human_review(
        fixture,
        proposal_data,
        _human_review(fixture, proposal_data, evidence_action="REJECT"),
    )
    artifacts = run_pipeline(
        reviewed_fixture,
        decisions=decisions,
        execution_mode="P2_LOCAL_LLM",
    )
    assert artifacts["constraints"]["items"] == []
    assert artifacts["partitions"]["enumerated_partition_count"] == 203
    assert artifacts["partitions"]["optimal_candidate_count"] == 203


def test_approved_evidence_and_responsibilities_drive_tutor_optimizer_and_all_stages():
    fixture = get_tutor_support_fixture()
    proposal_data = _proposal_data(fixture)
    reviewed_fixture, decisions = apply_tutor_human_review(
        fixture,
        proposal_data,
        _human_review(fixture, proposal_data),
    )
    artifacts = run_pipeline(
        reviewed_fixture,
        decisions=decisions,
        execution_mode="P2_LOCAL_LLM",
    )
    derived = [item for item in artifacts["constraints"]["items"] if item["origin"] == "ARCHITECTURAL_POLICY"]
    assert len(derived) == 1
    assert derived[0]["evidence_ids"] == ["EV-E01-PAIR-01"]
    assert derived[0]["relation"] == "MUST_LINK"
    assert derived[0]["hardness"] == "SOFT"
    assert derived[0]["left"] == "R5"
    assert derived[0]["right"] == "R6"
    assert artifacts["partitions"]["enumerated_partition_count"] == 203
    assert artifacts["partitions"]["objective_minimum"] == 0
    assert artifacts["partitions"]["optimal_candidate_count"] < 203
    assert any(set(group) == {"R5", "R6"} for group in artifacts["partitions"]["selected_groups"])
    assert reviewed_fixture["responsibility_provenance"] == "P2_TEST_ONLY"
    assert next(item for item in reviewed_fixture["evidence"] if item["id"] == "EV-E01-PAIR-01")["provenance"] == "P2_TEST_ONLY"
    assert [step["step"] for step in artifacts["validation_report"]["steps"]] == [
        f"{index:02d}" for index in range(1, 11)
    ]
    assert {profile["scenario_id"] for profile in artifacts["quality_profiles"]["profiles"]} == {
        "SC-REQUEST-ACK",
        "SC-DECISION-NOTICE",
    }
    assert {edge["responsibility_ids"][0] for edge in artifacts["interactions"]["edges"]} == {"R4", "R5"}
    assert all(edge["selection_status"] == "UNRESOLVED" for edge in artifacts["interactions"]["edges"])
    assert all(profile["measurement"] is None for profile in artifacts["quality_profiles"]["profiles"])
    _assert_hard_constraints_hold(artifacts)


def test_human_evidence_correction_changes_optimizer_and_downstream_assignments():
    fixture = get_tutor_support_fixture()
    proposal_data = _proposal_data(fixture)
    reviewed_fixture, decisions = apply_tutor_human_review(
        fixture,
        proposal_data,
        _human_review(fixture, proposal_data),
    )
    before = run_pipeline(reviewed_fixture, decisions=decisions, execution_mode="P2_LOCAL_LLM")
    before_assignment = before["quanta"]["primary_assignment"]
    revised_fixture, decision, revision = apply_evidence_relation_edit(
        reviewed_fixture,
        before,
        object_id="EV-E01-PAIR-01",
        subject_requirement_id="FR-04",
        predicate="SHARES_STATE_OR_INVARIANT",
        object_requirement_id="FR-05",
        source_requirement_ids=["FR-04", "FR-05"],
        subject_responsibility_id="R4",
        object_responsibility_id="R5",
        architecture_implication="COLOCATE_CANDIDATE",
        architecture_rationale="TEST-ONLY before/after rationale, not a case-study label.",
        reason="The reviewer changes the accepted relation to follow the request-to-decision workflow pair.",
        source="P2-HUMAN-REVIEW",
        actor="reviewer",
    )
    after = run_pipeline(
        revised_fixture,
        decisions=[*decisions, decision],
        revisions=[revision],
        execution_mode="P2_LOCAL_LLM",
    )
    after_assignment = after["quanta"]["primary_assignment"]
    assert any(set(group) == {"R5", "R6"} for group in before["partitions"]["selected_groups"])
    assert any(set(group) == {"R4", "R5"} for group in after["partitions"]["selected_groups"])
    assert before_assignment != after_assignment
    before_edges = {item["id"]: item for item in before["interactions"]["edges"]}
    after_edges = {item["id"]: item for item in after["interactions"]["edges"]}
    assert before_edges["EDGE-SC-DECISION-NOTICE-R5-R6"]["same_quantum"] is True
    assert after_edges["EDGE-SC-DECISION-NOTICE-R5-R6"]["same_quantum"] is False
    assert before_edges["EDGE-SC-REQUEST-ACK-R4-R5"]["same_quantum"] is False
    assert after_edges["EDGE-SC-REQUEST-ACK-R4-R5"]["same_quantum"] is True
    assert "partitions" in revision["invalidated_artifacts"]
    assert "quality_profiles" in revision["invalidated_artifacts"]
    assert after["validation_report"]["assertions"]["all_raw_source_spans_valid"] is True
    _assert_hard_constraints_hold(after)


def test_human_correction_of_responsibility_is_source_checked():
    fixture = get_tutor_support_fixture()
    proposal_data = _proposal_data(fixture)
    review = _human_review(fixture, proposal_data, evidence_action="REJECT")
    review["responsibilities"][0] = {
        "proposal_id": "P01",
        "action": "CORRECT",
        "correction": {
            "responsibilities": [
                {
                    "name": "Search tutors",
                    "activity": "Find tutors by subject and time",
                    "operation": "Filter the tutor directory by subject and availability",
                    "requirement_ids": ["FR-01"],
                    "workflow_activity_ids": ["WF-01"],
                },
                {
                    "name": "Filter tutor availability",
                    "activity": "Filter the directory",
                    "operation": "Narrow results to available times",
                    "requirement_ids": ["FR-01"],
                }
            ]
        },
        "reason": "Clarify wording against the cited requirement.",
        "source": "P2-HUMAN-REVIEW",
        "actor": "reviewer",
    }
    updated, decisions = apply_tutor_human_review(fixture, proposal_data, review)
    assert updated["responsibilities"][0]["name"] == "Search tutors"
    assert updated["responsibilities"][0]["review_decision_status"] == "APPROVED"
    assert updated["responsibilities"][0]["workflow_mapping_status"] == "MAPPED"
    assert sum("FR-01" in item["requirement_ids"] for item in updated["responsibilities"]) == 2
    assert next(item for item in decisions if item["decision_type"] == "HUMAN_RESPONSIBILITY_REVIEW")["action"] == "CORRECT"


def test_human_can_replace_a_missing_model_responsibility_proposal():
    fixture = get_tutor_support_fixture()
    proposal_data = _proposal_data(fixture)
    proposal_data["proposals"] = [
        item for item in proposal_data["proposals"] if item["requirement_ids"] != ["FR-01"]
    ]
    review = _human_review(fixture, proposal_data)
    review["responsibilities"] = [row for row in review["responsibilities"] if row["proposal_id"] != "P01"]
    review["evidence"][0]["responsibility_pairs"] = [["R4", "R5"]]
    review["additional_responsibilities"] = [
        {
            "action": "ADD",
            "name": "Tutor search",
            "activity": "Search tutors by subject and availability",
            "operation": "Filter the tutor directory",
            "requirement_ids": ["FR-01", "FR-02"],
            "reason": "Replace the missing model row using the cited requirement.",
            "source": "P2-HUMAN-REVIEW",
            "actor": "test-reviewer",
        }
    ]
    updated, _ = apply_tutor_human_review(fixture, proposal_data, review)
    added_role = next(item for item in updated["responsibilities"] if item["name"] == "Tutor search")
    assert added_role["proposal_id"] is None
    assert added_role["provenance"] == "HUMAN_ADDITION"
    assert added_role["requirement_ids"] == ["FR-01", "FR-02"]


def test_invalid_source_span_cannot_create_evidence_derived_optimizer_constraint():
    fixture = get_tutor_support_fixture()
    proposal_data = _proposal_data(fixture)
    reviewed_fixture, _ = apply_tutor_human_review(
        fixture,
        proposal_data,
        _human_review(fixture, proposal_data),
    )
    evidence = next(item for item in reviewed_fixture["evidence"] if item["id"] == "EV-E01-PAIR-01")
    evidence["source_refs"][0]["quote"] = "X" * len(evidence["source_refs"][0]["quote"])
    artifacts = run_pipeline(reviewed_fixture, execution_mode="P2_LOCAL_LLM")
    assert not any(item["origin"] == "ARCHITECTURAL_POLICY" for item in artifacts["constraints"]["items"])
    assert artifacts["validation_report"]["assertions"]["evidence_sources_well_formed"] is False


def test_evidence_materialization_must_match_the_reviewed_relation_annotation():
    fixture = get_tutor_support_fixture()
    proposals = _proposal_data(fixture)
    reviewed_fixture, _ = apply_tutor_human_review(
        fixture, proposals, _human_review(fixture, proposals)
    )
    evidence = next(item for item in reviewed_fixture["evidence"] if item["id"] == "EV-E01-PAIR-01")
    evidence["predicate"] = "BUSINESS_PRECEDES"
    with pytest.raises(ValueError, match="does not preserve the approved relation status and semantics"):
        run_pipeline(reviewed_fixture, execution_mode="P2_TEST_ONLY")


def test_self_relation_is_not_used_as_a_partition_constraint():
    fixture = get_tutor_support_fixture()
    proposal_data = _proposal_data(fixture)
    evidence_proposal = proposal_data["evidence_proposals"][0]
    evidence_proposal.update(
        {
            "subject_requirement_id": "FR-06",
            "object_requirement_id": "FR-06",
            "source_requirement_ids": ["FR-06"],
            "source_refs": [fixture["raw_requirements"]["requirements"][5]["source_ref"]],
        }
    )
    reviewed_fixture, decisions = apply_tutor_human_review(
        fixture,
        proposal_data,
        _human_review(fixture, proposal_data, evidence_action="REJECT"),
    )
    artifacts = run_pipeline(reviewed_fixture, decisions=decisions, execution_mode="P2_LOCAL_LLM")
    assert not any(item["origin"] == "ARCHITECTURAL_POLICY" for item in artifacts["constraints"]["items"])


def test_extraction_audit_flags_duplicate_relations_and_missing_endpoint_citations(monkeypatch):
    fixture = get_tutor_support_fixture()
    raw = fixture["raw_requirements"]
    requirements = raw["requirements"]
    bundle = {
        "context_summary": "Test-only response.",
        "normalized_requirements": [
            {"id": item["id"], "normalized_text": item["text"]} for item in requirements
        ],
        "proposals": [
            {
                "id": f"P{index}",
                "name": f"Responsibility {index}",
                "activity": "Activity",
                "operation": "Operation",
                "requirement_ids": [item["id"]],
                "decomposition_rationale": "TEST-ONLY proposal.",
            }
            for index, item in enumerate(requirements, start=1)
        ],
        "evidence_proposals": [
            {
                "id": "E1",
                "subject_requirement_id": "FR-04",
                "predicate": "leads to",
                "object_requirement_id": "FR-05",
                "proposed_status": "PRESENT",
                "source_requirement_ids": ["FR-03"],
                "rationale": "Unsupported test relation.",
            },
            {
                "id": "E2",
                "subject_requirement_id": "FR-04",
                "predicate": "LEADS TO",
                "object_requirement_id": "FR-05",
                "proposed_status": "UNKNOWN",
                "source_requirement_ids": ["FR-03"],
                "rationale": "Conflicting test relation.",
            },
        ],
        "boundary_hypotheses": [
            {
                "id": "B1",
                "requirement_ids": ["FR-04", "FR-05"],
                "boundary_rationale": "Test boundary.",
                "source_requirement_ids": ["FR-03"],
            }
        ],
    }

    def fake_request(*args, **kwargs):
        return {"model": "test-model", "message": {"content": json.dumps(bundle)}}

    monkeypatch.setattr("eqcr.ollama._request", fake_request)
    result = propose_responsibilities(raw, "test-model", blind_annotation_lock=_test_blind_lock(raw))
    first, second = result["evidence_proposals"]
    assert first["citation_status"] == "RESOLVED"
    assert first["citation_covers_endpoints"] is False
    assert first["duplicate_relation"] is True
    assert second["duplicate_relation"] is True
    assert first["conflicting_status"] is True
    assert second["conflicting_status"] is True
    assert result["boundary_hypotheses"][0]["source_covers_hypothesis"] is False


def test_blind_annotation_protocol_is_source_only_and_supports_zero_to_many_labels_per_fr():
    raw = get_tutor_support_fixture()["raw_requirements"]
    submission = build_blind_annotation_template(raw)
    assert set(submission) == {
        "protocol_version", "case_id", "source_bundle_sha256", "reviewer_id",
        "source_only_attested", "no_prior_model_output_exposure", "responsibility_annotations", "unresolved_requirement_ids",
        "relation_registry",
    }
    assert len(submission["relation_registry"]) == 60
    assert sum(item["predicate"] == "BUSINESS_PRECEDES" for item in submission["relation_registry"]) == 30
    assert sum(item["predicate"] == "SHARES_STATE_OR_INVARIANT" for item in submission["relation_registry"]) == 15
    assert sum(item["predicate"] == "REQUIRES_INDEPENDENT_CHANGE" for item in submission["relation_registry"]) == 15
    assert {item["status"] for item in submission["relation_registry"]} == {"NOT_ANNOTATED"}
    assert all("architecture_implication" not in item for item in submission["relation_registry"])

    submission.update(
        {
            "reviewer_id": "independent-test-annotator",
            "source_only_attested": True,
            "no_prior_model_output_exposure": True,
        }
    )
    submission["responsibility_annotations"] = [
        {
            "annotation_id": "A-FR-01", "name": "Search tutors", "activity": "Search",
            "operation": "Filter directory", "requirement_ids": ["FR-01"],
            "source_requirement_ids": ["FR-01"], "rationale": "TEST-ONLY annotation.",
        },
        {
            "annotation_id": "A-FR-02", "name": "View tutor", "activity": "Inspect profile",
            "operation": "Display details", "requirement_ids": ["FR-02"],
            "source_requirement_ids": ["FR-02"], "rationale": "TEST-ONLY annotation.",
        },
        {
            "annotation_id": "A-FR-03", "name": "Publish availability", "activity": "Update slots",
            "operation": "Save weekly availability", "requirement_ids": ["FR-03"],
            "source_requirement_ids": ["FR-03"], "rationale": "TEST-ONLY annotation.",
        },
        {
            "annotation_id": "A-FR-04A", "name": "Request session", "activity": "Select slot",
            "operation": "Submit request", "requirement_ids": ["FR-04"],
            "source_requirement_ids": ["FR-04"], "rationale": "TEST-ONLY annotation A.",
        },
        {
            "annotation_id": "A-FR-04B", "name": "Validate open slot", "activity": "Check slot",
            "operation": "Confirm availability", "requirement_ids": ["FR-04"],
            "source_requirement_ids": ["FR-04"], "rationale": "TEST-ONLY annotation B.",
        },
        {
            "annotation_id": "A-FR-05", "name": "Decide request", "activity": "Review request",
            "operation": "Accept or decline", "requirement_ids": ["FR-05"],
            "source_requirement_ids": ["FR-05"], "rationale": "TEST-ONLY annotation.",
        },
    ]
    submission["unresolved_requirement_ids"] = ["FR-06"]
    business_row = next(
        item for item in submission["relation_registry"]
        if item["predicate"] == "BUSINESS_PRECEDES"
        and item["subject_requirement_id"] == "FR-04"
        and item["object_requirement_id"] == "FR-05"
    )
    business_row.update(
        {
            "status": "PRESENT", "source_requirement_ids": ["FR-04", "FR-05"],
            "rationale": "TEST-ONLY relation annotation.",
        }
    )
    locked = lock_blind_annotation(raw, submission, locked_at="2026-01-01T00:00:00+00:00")
    assert verify_blind_annotation_lock(raw, locked)
    assert locked["annotation"]["unresolved_requirement_ids"] == ["FR-06"]
    assert sum("FR-04" in item["requirement_ids"] for item in locked["annotation"]["responsibility_annotations"]) == 2
    changed = json.loads(json.dumps(locked))
    changed["annotation"]["responsibility_annotations"][0]["name"] = "Tampered after lock"
    assert not verify_blind_annotation_lock(raw, changed)

    source_only_candidate = build_blind_annotation_template(raw)
    source_only_candidate.update(
        {
            "reviewer_id": "annotator",
            "source_only_attested": True,
            "no_prior_model_output_exposure": True,
        }
    )
    architecture_row = next(
        item for item in source_only_candidate["relation_registry"]
        if item["predicate"] == "SHARES_STATE_OR_INVARIANT"
    )
    architecture_row.update(
        {
            "status": "PRESENT",
            "source_requirement_ids": [architecture_row["subject_requirement_id"], architecture_row["object_requirement_id"]],
            "rationale": "TEST-ONLY source annotation.",
            "architecture_implication": "COLOCATE_CANDIDATE",
        }
    )
    with pytest.raises(ValueError):
        lock_blind_annotation(raw, source_only_candidate, locked_at="2026-01-01T00:00:00+00:00")


def test_local_model_cannot_run_before_a_verified_source_only_lock(monkeypatch):
    raw = get_tutor_support_fixture()["raw_requirements"]
    request_called = False

    def unexpected_request(*args, **kwargs):
        nonlocal request_called
        request_called = True
        raise AssertionError("The model request should not run without the blind checkpoint.")

    monkeypatch.setattr("eqcr.ollama._request", unexpected_request)
    try:
        propose_responsibilities(raw, "qwen3:4b")
    except OllamaError as exc:
        assert "source-only annotation is locked" in str(exc)
    else:
        raise AssertionError("Tutor proposals must require a verified blind lock.")
    assert not request_called


def test_review_rejects_proposals_from_a_different_source_or_before_the_lock():
    fixture = get_tutor_support_fixture()
    proposals = _proposal_data(fixture)
    proposals["input_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="not bound to this exact frozen source package"):
        apply_tutor_human_review(fixture, proposals, _human_review(fixture, proposals))

    proposals = _proposal_data(fixture)
    proposals["inference_started_at_utc"] = "2025-12-31T23:59:59+00:00"
    with pytest.raises(ValueError, match="must be locked before local inference starts"):
        apply_tutor_human_review(fixture, proposals, _human_review(fixture, proposals))


def test_unknown_relation_disposition_still_needs_a_semantic_rationale():
    fixture = get_tutor_support_fixture()
    proposals = _proposal_data(fixture)
    relation = proposals["evidence_proposals"][0]
    relation.update(
        {
            "proposed_status": "UNKNOWN",
            "source_requirement_ids": [],
            "source_refs": [],
            "rationale": "",
        }
    )
    review = _human_review(fixture, proposals)
    review["evidence"][0].update(
        {"architecture_implication": "UNRESOLVED", "responsibility_pairs": [], "architecture_rationale": ""}
    )
    with pytest.raises(ValueError, match="needs a semantic rationale for every status"):
        apply_tutor_human_review(fixture, proposals, review)


def test_all_rejected_or_deferred_responsibilities_are_explicit_and_leave_no_partition_candidates():
    fixture = get_tutor_support_fixture()
    proposals = _proposal_data(fixture)
    review = _human_review(fixture, proposals, evidence_action="DEFER")
    for decision in review["responsibilities"]:
        decision["action"] = "REJECT"
    for decision in review["boundaries"]:
        decision["action"] = "DEFER"
    reviewed, decisions = apply_tutor_human_review(fixture, proposals, review)
    artifacts = run_pipeline(reviewed, decisions=decisions, execution_mode="P2_TEST_ONLY")
    assert reviewed["responsibilities"] == []
    assert reviewed["unresolved_requirement_ids"] == [f"FR-0{index}" for index in range(1, 7)]
    assert artifacts["partitions"]["feasible_candidates"] == []
    assert artifacts["quanta"]["status"] == "INSUFFICIENT_EVIDENCE"


def test_business_order_is_recorded_but_cannot_become_an_optimizer_constraint():
    fixture = get_tutor_support_fixture()
    proposals = _proposal_data(fixture)
    relation = proposals["evidence_proposals"][0]
    relation.update(
        {
            "subject_requirement_id": "FR-04", "predicate": "BUSINESS_PRECEDES",
            "object_requirement_id": "FR-05", "source_requirement_ids": ["FR-04", "FR-05"],
            "source_refs": [fixture["raw_requirements"]["requirements"][3]["source_ref"], fixture["raw_requirements"]["requirements"][4]["source_ref"]],
        }
    )
    review = _human_review(fixture, proposals)
    review["evidence"][0].update(
        {"architecture_implication": "UNRESOLVED", "responsibility_pairs": [], "architecture_rationale": ""}
    )
    reviewed, _ = apply_tutor_human_review(fixture, proposals, review)
    artifacts = run_pipeline(reviewed, execution_mode="P2_TEST_ONLY")
    assert reviewed["relation_annotations"][0]["predicate"] == "BUSINESS_PRECEDES"
    assert not any(item["origin"] == "ARCHITECTURAL_POLICY" for item in artifacts["constraints"]["items"])


def test_business_order_cannot_be_given_a_direct_architecture_implication():
    fixture = get_tutor_support_fixture()
    proposals = _proposal_data(fixture)
    proposals["evidence_proposals"][0].update(
        {
            "subject_requirement_id": "FR-04", "predicate": "BUSINESS_PRECEDES",
            "object_requirement_id": "FR-05", "source_requirement_ids": ["FR-04", "FR-05"],
            "source_refs": [fixture["raw_requirements"]["requirements"][3]["source_ref"], fixture["raw_requirements"]["requirements"][4]["source_ref"]],
        }
    )
    review = _human_review(fixture, proposals)
    review["evidence"][0]["responsibility_pairs"] = [["R4", "R5"]]
    import pytest
    with pytest.raises(ValueError, match="Business ordering alone"):
        apply_tutor_human_review(fixture, proposals, review)


def test_duplicate_relation_proposal_cannot_be_approved_without_correction():
    fixture = get_tutor_support_fixture()
    proposals = _proposal_data(fixture)
    duplicate = dict(proposals["evidence_proposals"][0])
    duplicate["id"] = "E02"
    duplicate["model_proposal_id"] = "model-evidence-2"
    duplicate["model_proposal_id"] = "duplicate-model-relation"
    duplicate["duplicate_relation"] = True
    proposals["evidence_proposals"].append(duplicate)
    review = _human_review(fixture, proposals)
    review["evidence"].append(
        {
            "proposal_id": "E02", "action": "APPROVE",
            "reason": "TEST-ONLY duplicate relation check.",
            "source": "TEST-ONLY-REVIEW", "actor": "test-reviewer",
            "architecture_implication": "COLOCATE_CANDIDATE",
            "architecture_rationale": "TEST-ONLY rationale.",
            "responsibility_pairs": [["R5", "R6"]],
        }
    )
    import pytest
    with pytest.raises(ValueError, match="duplicate or status-conflicting"):
        apply_tutor_human_review(fixture, proposals, review)
