"""P2 coverage for a reviewed, non-PetClinic Tutor Support input path."""

import json
from pathlib import Path

from eqcr.pipeline import run_pipeline
from eqcr.review import apply_evidence_relation_edit
from eqcr.ollama import propose_responsibilities
from eqcr.tutor_support import apply_tutor_human_review, get_tutor_support_fixture
from streamlit.testing.v1 import AppTest


def _proposal_data(fixture):
    raw = fixture["raw_requirements"]
    proposals = []
    normalized = []
    for index, requirement in enumerate(raw["requirements"], start=1):
        source_ref = requirement["source_ref"]
        proposals.append(
            {
                "id": f"test-proposal-{index}",
                "name": f"Proposed responsibility {index}",
                "activity": f"Activity {index}",
                "operation": f"Operation {index}",
                "requirement_id": requirement["id"],
                "requirement_id_valid": True,
                "source_id": source_ref["source_id"],
                "source_id_valid": True,
                "source_span_resolved": True,
                "responsibility_id_valid_and_unique": True,
                "source_ref": source_ref,
            }
        )
        normalized.append({"id": requirement["id"], "normalized_text": requirement["text"]})
    evidence = {
        "id": "test-evidence-1",
        "subject_requirement_id": "FR-05",
        "predicate": "same_workflow_lifecycle",
        "object_requirement_id": "FR-06",
        "proposed_status": "PRESENT",
        "source_requirement_ids": ["FR-05", "FR-06"],
        "rationale": "Test-only proposal input; the reviewer decision is separately supplied below.",
        "id_valid_and_unique": True,
        "subject_requirement_id_valid": True,
        "object_requirement_id_valid": True,
        "source_refs_valid": True,
        "source_refs": [
            next(item for item in raw["requirements"] if item["id"] == requirement_id)["source_ref"]
            for requirement_id in ("FR-05", "FR-06")
        ],
    }
    return {
        "model": "test-fixture-only",
        "context_summary": "Test-only model proposal bundle.",
        "normalized_requirements": normalized,
        "proposals": proposals,
        "evidence_proposals": [evidence],
        "boundary_hypotheses": [
            {
                "id": "test-boundary-1",
                "requirement_ids": ["FR-04", "FR-05"],
                "boundary_rationale": "Test-only boundary hypothesis.",
                "source_requirement_ids": ["FR-04", "FR-05"],
                "id_valid_and_unique": True,
                "requirement_ids_valid": True,
                "source_refs_valid": True,
                "source_covers_hypothesis": True,
            }
        ],
    }


def _human_review(fixture, proposal_data, *, evidence_action="APPROVE"):
    responsibilities = [
        {
            "requirement_id": item["requirement_id"],
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
            "predicate": "same_workflow_lifecycle",
            "object_requirement_id": "FR-05",
            "status": "PRESENT",
            "source_requirement_ids": ["FR-04", "FR-05"],
            "rationale": "Unit test correction; not a domain label.",
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
    assert derived[0]["evidence_ids"] == ["EV-LLM-P01"]
    assert derived[0]["relation"] == "MUST_LINK"
    assert derived[0]["hardness"] == "SOFT"
    assert derived[0]["left"] == "R5"
    assert derived[0]["right"] == "R6"
    assert artifacts["partitions"]["enumerated_partition_count"] == 203
    assert artifacts["partitions"]["objective_minimum"] == 0
    assert artifacts["partitions"]["optimal_candidate_count"] < 203
    assert any(set(group) == {"R5", "R6"} for group in artifacts["partitions"]["selected_groups"])
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
        object_id="EV-LLM-P01",
        subject_requirement_id="FR-04",
        predicate="same_workflow_lifecycle",
        object_requirement_id="FR-05",
        source_requirement_ids=["FR-04", "FR-05"],
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
    review = _human_review(fixture, proposal_data)
    review["responsibilities"][0] = {
        "requirement_id": "FR-01",
        "action": "CORRECT",
        "correction": {
            "name": "Search tutors",
            "activity": "Find tutors by subject and time",
            "operation": "Filter the tutor directory by subject and availability",
        },
        "reason": "Clarify wording against the cited requirement.",
        "source": "P2-HUMAN-REVIEW",
        "actor": "reviewer",
        "workflow_activity_ids": ["WF-01"],
    }
    updated, decisions = apply_tutor_human_review(fixture, proposal_data, review)
    assert updated["responsibilities"][0]["name"] == "Search tutors"
    assert updated["responsibilities"][0]["review_decision_status"] == "APPROVED"
    assert updated["responsibilities"][0]["workflow_mapping_status"] == "MAPPED"
    assert decisions[0]["action"] == "CORRECT"


def test_human_can_replace_a_missing_model_responsibility_proposal():
    fixture = get_tutor_support_fixture()
    proposal_data = _proposal_data(fixture)
    proposal_data["proposals"] = [
        item for item in proposal_data["proposals"] if item["requirement_id"] != "FR-01"
    ]
    review = _human_review(fixture, _proposal_data(fixture))
    review["responsibilities"][0] = {
        "requirement_id": "FR-01",
        "action": "CORRECT",
        "correction": {
            "name": "Tutor search",
            "activity": "Search tutors by subject and availability",
            "operation": "Filter the tutor directory",
        },
        "reason": "Replace the missing model row using the cited requirement.",
        "source": "P2-HUMAN-REVIEW",
        "actor": "reviewer",
    }
    updated, _ = apply_tutor_human_review(fixture, proposal_data, review)
    assert updated["responsibilities"][0]["name"] == "Tutor search"
    assert updated["responsibilities"][0]["proposal_id"] is None


def test_invalid_source_span_cannot_create_evidence_derived_optimizer_constraint():
    fixture = get_tutor_support_fixture()
    proposal_data = _proposal_data(fixture)
    reviewed_fixture, _ = apply_tutor_human_review(
        fixture,
        proposal_data,
        _human_review(fixture, proposal_data),
    )
    evidence = next(item for item in reviewed_fixture["evidence"] if item["id"] == "EV-LLM-P01")
    evidence["source_refs"][0]["quote"] = "X" * len(evidence["source_refs"][0]["quote"])
    artifacts = run_pipeline(reviewed_fixture, execution_mode="P2_LOCAL_LLM")
    assert not any(item["origin"] == "ARCHITECTURAL_POLICY" for item in artifacts["constraints"]["items"])
    assert artifacts["validation_report"]["assertions"]["evidence_sources_well_formed"] is False


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
        _human_review(fixture, proposal_data),
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
                "requirement_id": item["id"],
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
    result = propose_responsibilities(raw, "test-model")
    first, second = result["evidence_proposals"]
    assert first["citation_status"] == "RESOLVED"
    assert first["citation_covers_endpoints"] is False
    assert second["duplicate_relation"] is True
    assert first["conflicting_status"] is True
    assert second["conflicting_status"] is True
    assert result["boundary_hypotheses"][0]["source_covers_hypothesis"] is False
