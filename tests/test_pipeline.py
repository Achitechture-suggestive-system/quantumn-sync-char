from copy import deepcopy
from io import BytesIO
import json
from zipfile import ZipFile

import pytest
from pydantic import ValidationError

from eqcr.fixture import get_fixture
from eqcr.impact import downstream_artifacts, impact_preview
from eqcr.models import LLMProposalBundle, RawRequirements
from eqcr.ollama import apply_proposals_to_fixture
from eqcr.ollama import OllamaError, list_models, propose_responsibilities
from eqcr.pipeline import run_pipeline, validate_project_package
from eqcr.review import (
    apply_artifact_review,
    artifact_diff,
    apply_constraint_edit,
    apply_responsibility_edit,
    replay_artifact_review_decisions,
)
from eqcr.storage import make_export_zip


def test_schema_required_fields():
    raw = get_fixture()["raw_requirements"]
    raw.pop("context_id")
    with pytest.raises(ValidationError):
        RawRequirements.model_validate(raw)

    incomplete_llm_bundle = {
        "context_summary": "",
        "normalized_requirements": [],
        "proposals": [],
        "evidence_proposals": [
            {
                "id": "evidence-1",
                "subject_requirement_id": "FR-01",
                "predicate": "relates_to",
                "object_requirement_id": "FR-02",
                "proposed_status": "UNKNOWN",
                "source_requirement_ids": ["FR-01"],
                "rationale": "Unresolved example.",
            }
        ],
        "boundary_hypotheses": [
            {
                "id": "boundary-1",
                "requirement_ids": ["FR-01", "FR-02"],
                "boundary_rationale": "Hypothesis only.",
                "source_requirement_ids": ["FR-01"],
            }
        ],
    }
    with pytest.raises(ValidationError):
        LLMProposalBundle.model_validate(incomplete_llm_bundle)


def test_no_missing_source_reference():
    fixture = get_fixture()
    req_ids = {item["id"] for item in fixture["raw_requirements"]["requirements"]}
    for responsibility in fixture["responsibilities"]:
        assert responsibility["requirement_ids"]
        assert set(responsibility["requirement_ids"]) <= req_ids
        assert responsibility["source_refs"]
        for ref in responsibility["source_refs"]:
            assert ref["source_id"] in req_ids_as_source_ids(fixture)
            assert ref["quote"]


def req_ids_as_source_ids(fixture):
    return {item["source_ref"]["source_id"] for item in fixture["raw_requirements"]["requirements"]}


def test_unknown_is_not_false():
    artifacts = run_pipeline(get_fixture())
    record = next(item for item in artifacts["evidence"]["items"] if item["status"] == "UNKNOWN")
    assert record["predicate"] == "consistency_contract"
    assert record["status"] != "SCOPED_ABSENT"


def test_evidence_relations_keep_provenance_and_review_state():
    fixture = get_fixture()
    for record in fixture["evidence"]:
        assert record["provenance"] in {"SOURCE_BACKED", "SCOPE_BOUNDARY"}
        assert record["review_status"] == "REVIEW_REQUIRED"
        if record["status"] == "PRESENT":
            assert record["source_refs"] or record["is_assumption"]
    scoped = next(item for item in fixture["evidence"] if item["status"] == "SCOPED_ABSENT")
    assert scoped["provenance"] == "SCOPE_BOUNDARY"


def test_bell6_partition_count_203():
    artifacts = run_pipeline(get_fixture())
    assert artifacts["partitions"]["enumerated_partition_count"] == 203


def test_what_if_10_zero_cost_optima():
    artifacts = run_pipeline(get_fixture())
    partitions = artifacts["partitions"]
    assert partitions["optimal_candidate_count"] == 10
    assert partitions["objective_minimum"] == 0
    assert all(item["objective_cost"] == 0 for item in partitions["optimal_candidates"])


def test_soft_constraint_weight_and_quality_scenario_link_are_used():
    fixture = get_fixture()
    fixture["constraints"].append(
        {
            "id": "S1",
            "relation": "MUST_LINK",
            "left": "R1",
            "right": "R2",
            "hardness": "SOFT",
            "weight": 2.5,
            "quality_scenario_ids": ["SC-OWNER-SEARCH"],
            "origin": "WHAT_IF_POLICY",
            "enabled": True,
            "source_refs": [],
            "rationale": "Illustrative quality-aware coupling preference.",
        }
    )
    artifacts = run_pipeline(fixture)
    partitions = artifacts["partitions"]
    assert partitions["objective_minimum"] == 0
    assert {item["objective_cost"] for item in partitions["feasible_candidates"]} >= {0, 2.5}
    stored = next(item for item in artifacts["constraints"]["items"] if item["id"] == "S1")
    assert stored["weight"] == 2.5
    assert stored["quality_scenario_ids"] == ["SC-OWNER-SEARCH"]

    invalid = get_fixture()
    invalid["constraints"].append({**fixture["constraints"][-1], "id": "S2", "quality_scenario_ids": ["SC-MISSING"]})
    with pytest.raises(ValueError, match="unknown quality scenarios"):
        run_pipeline(invalid)


def test_must_cannot_conflict_detected():
    fixture = get_fixture()
    constraints = deepcopy(fixture["constraints"])
    constraints.append(
        {
            "id": "H4",
            "relation": "MUST_LINK",
            "left": "R4",
            "right": "R6",
            "hardness": "HARD",
            "origin": "HUMAN_OVERRIDE",
            "enabled": True,
            "source_refs": [],
            "rationale": "Demo contradiction.",
        }
    )
    artifacts = run_pipeline(fixture, constraints_override=constraints)
    assert artifacts["validation_report"]["status"] == "INFEASIBLE"
    assert artifacts["partitions"]["feasible_candidate_count"] == 0
    assert artifacts["constraints"]["conflicts"][0]["constraint_ids"] == ["H3", "H4"]


def test_each_responsibility_assigned_once():
    artifacts = run_pipeline(get_fixture())
    assert set(artifacts["quanta"]["membership_counts"].values()) == {1}
    assert all(item["workflow_mapping_status"] == "UNRESOLVED" for item in artifacts["responsibilities"]["items"])


def test_quantum_graph_exposes_unknown_layers_and_evidence():
    artifacts = run_pipeline(get_fixture())
    graph = artifacts["quanta"]["architecture_graph"]
    nodes = {item["id"]: item for item in graph["nodes"]}
    assert nodes["ACTOR-USER"]["status"] == "PRESENT"
    assert nodes["PRESENTATION-UNKNOWN"]["status"] == "UNKNOWN"
    assert nodes["INFRASTRUCTURE-UNKNOWN"]["status"] == "UNKNOWN"
    assert all(item["relevant_evidence_ids"] for item in artifacts["quanta"]["quanta"])
    assert all(item["ownership_status"] == "UNKNOWN" for item in artifacts["quanta"]["quanta"])


def test_contract_unresolved_without_evidence():
    artifacts = run_pipeline(get_fixture())
    edge = artifacts["interactions"]["edges"][0]
    assert edge["label"] == "UNRESOLVED"
    assert edge["consistency"] == "UNKNOWN"
    assert edge["contract"]["request_fields"] == "UNKNOWN"
    assert edge["contract"]["data_dependency"] == "UNKNOWN"
    assert edge["contract"]["retry_policy"] == "UNKNOWN"
    assert edge["contract"]["timeout_policy"] == "UNKNOWN"
    assert edge["contract"]["idempotency_policy"] == "UNKNOWN"


def test_sync_and_async_options_are_cited_hypotheses_without_selection():
    fixture = get_fixture()
    artifacts = run_pipeline(fixture)
    edge = artifacts["interactions"]["edges"][0]
    options = {option["mode"]: option for option in edge["options"]}
    assert set(options) == {"SYNC", "ASYNC"}
    assert edge["label"] == "UNRESOLVED"
    assert edge["selection_status"] == "UNRESOLVED"
    for option in options.values():
        assert option["status"] == "PROPOSED_NOT_VERIFIED"
        assert option["review_status"] == "REVIEW_REQUIRED"
        assert option["provenance"] == "DETERMINISTIC_PATTERN_HYPOTHESIS"
        assert {ref["source_id"] for ref in option["source_refs"]} == {"SC-PET-VISIT", "REQ-FR-06"}
        assert option["unresolved_decisions"]
    assert artifacts["validation_report"]["assertions"]["interaction_option_sources_well_formed"] is True


def test_quality_target_not_measured():
    artifacts = run_pipeline(get_fixture())
    profile = artifacts["quality_profiles"]["profiles"][0]
    assert profile["target"] == "p95 <= 250 ms @ 300 requests/s"
    assert profile["measurement_status"] == "NOT_MEASURED"
    assert profile["measurement"] is None
    assert profile["proposed_metric"] == "p95 response latency at 300 requests/s"
    assert profile["measurement_plan_status"] == "PROPOSED"
    assert profile["evidence"][0]["kind"] == "TARGET_SOURCE"
    assert [item["scenario_id"] for item in artifacts["quality_profiles"]["profiles"]] == [
        "SC-OWNER-SEARCH",
        "SC-PET-VISIT",
    ]
    interaction_profile = artifacts["quality_profiles"]["profiles"][1]
    assert interaction_profile["target"] is None
    assert interaction_profile["iso_characteristic"] == "UNKNOWN"
    assert interaction_profile["measurement_status"] == "INSUFFICIENT_EVIDENCE"
    assert interaction_profile["measurement"] is None
    assert interaction_profile["affected_interaction_edges"] == ["EDGE-PET-VISIT"]
    assert interaction_profile["responsibility_ids"] == ["R4", "R6"]
    assert artifacts["validation_report"]["assertions"]["quality_scenarios_allocated_without_fake_pass"] is True
    assert artifacts["validation_report"]["assertions"]["quality_profile_sources_well_formed"] is True


@pytest.mark.parametrize(
    ("action", "expected_status"),
    [("APPROVE", "APPROVED"), ("REJECT", "REJECTED"), ("DEFER", "DEFERRED")],
)
def test_human_quality_review_does_not_fake_a_measurement_or_pass(action, expected_status):
    fixture = get_fixture()
    before = run_pipeline(fixture)
    reviewed = apply_artifact_review(
        before,
        target_artifact="quality_profiles",
        object_id="SC-OWNER-SEARCH",
        action=action,
        reason="Approve the proposed metric for later measurement planning.",
        source="REVIEW-SESSION-01",
        actor="reviewer-1",
    )
    profile = reviewed["quality_profiles"]["profiles"][0]
    assert profile["review_status"] == expected_status
    assert profile["measurement_status"] == "NOT_MEASURED"
    assert profile["measurement"] is None
    assert reviewed["validation_report"]["status"] == "REVIEW_REQUIRED"
    assert reviewed["decisions"]["items"][-1]["result"] == "RECORDED_NO_STRUCTURAL_CHANGE"
    rerun = run_pipeline(
        fixture,
        decisions=reviewed["decisions"]["items"],
        revisions=reviewed["revisions"]["items"],
    )
    replayed = replay_artifact_review_decisions(rerun)
    assert replayed["quality_profiles"]["profiles"][0]["review_status"] == expected_status
    assert replayed["quality_profiles"]["profiles"][0]["measurement_status"] == "NOT_MEASURED"


def test_human_responsibility_edit_invalidates_downstream_and_resets_review():
    fixture = get_fixture()
    before = run_pipeline(fixture)
    approved = apply_artifact_review(
        before,
        target_artifact="responsibilities",
        object_id="R1",
        action="APPROVE",
        reason="Reviewed the initial responsibility proposal.",
        source="REVIEW-SESSION-01",
        actor="reviewer-1",
    )
    revised_fixture, decision, revision = apply_responsibility_edit(
        fixture,
        approved,
        object_id="R1",
        name="Search Owner",
        activity="Owner search",
        operation="search owner by name",
        reason="Clarify the operation wording against FR-01.",
        source="HUMAN-REVISION-01",
        actor="reviewer-1",
    )
    after = run_pipeline(
        revised_fixture,
        decisions=approved["decisions"]["items"] + [decision],
        revisions=approved["revisions"]["items"] + [revision],
    )
    after = replay_artifact_review_decisions(after)
    responsibility = after["responsibilities"]["items"][0]
    assert responsibility["name"] == "Search Owner"
    assert responsibility["review_decision_status"] == "REVIEW_REQUIRED"
    assert responsibility["semantic_status"] == "REVIEW_REQUIRED"
    assert "constraints" in revision["invalidated_artifacts"]
    assert "quality_profiles" in revision["invalidated_artifacts"]
    assert after["validation_report"]["assertions"]["responsibility_sources_well_formed"] is True
    assert after["raw_requirements"] == before["raw_requirements"]


def test_human_revision_audit_and_impact():
    fixture = get_fixture()
    before = run_pipeline(fixture)
    constraints, decision, revision = apply_constraint_edit(
        before,
        target_step="04",
        object_id="H4",
        old_value="ABSENT",
        new_value="ADD MUST_LINK(R4,R6)",
        reason="Exercise contradiction detection.",
        source="TEST-REVIEW",
        actor="reviewer-1",
    )
    after = run_pipeline(
        fixture,
        constraints_override=constraints,
        decisions=[decision],
        revisions=[revision],
    )
    assert decision["old_value"] == "ABSENT"
    assert decision["submitted_old_value"] == "ABSENT"
    assert decision["actor"] == "reviewer-1"
    assert revision["affected_steps"] == ["04", "05", "06", "07", "08", "10"]
    assert revision["stale_artifacts_before_revalidation"] == [
        "interactions", "partitions", "quality_profiles", "quanta", "traceability", "validation_report"
    ]
    assert revision["recomputed_artifacts"] == []
    assert after["validation_report"]["status"] == "INFEASIBLE"


def test_dependency_graph_computes_transitive_impact_preview():
    impact = impact_preview("constraints")
    assert impact["stale_artifacts"] == [
        "interactions", "partitions", "quality_profiles", "quanta", "traceability", "validation_report"
    ]
    assert impact["affected_steps"] == ["04", "05", "06", "07", "08", "10"]
    assert "evidence" in impact["unaffected_artifacts"]
    assert downstream_artifacts("interactions") == ["quality_profiles", "traceability", "validation_report"]


def test_human_correction_resolves_conflict_and_captures_actual_before_value():
    fixture = get_fixture()
    baseline = run_pipeline(fixture)
    conflict_constraints, decision, revision = apply_constraint_edit(
        baseline,
        target_step="04",
        object_id="H4",
        old_value="ABSENT",
        new_value="ADD MUST_LINK(R4,R6)",
        reason="Check H3 against an opposing must-link.",
        source="DEMO-REVIEW",
        actor="reviewer",
    )
    conflict = run_pipeline(fixture, constraints_override=conflict_constraints, decisions=[decision], revisions=[revision])
    fixed_constraints, correction, fixed_revision = apply_constraint_edit(
        conflict,
        target_step="04",
        object_id="H3",
        old_value="stale form text",
        new_value="DISABLE H3",
        reason="The team withdraws the what-if cannot-link for this experiment.",
        source="DEMO-REVIEW",
        actor="reviewer",
    )
    fixed = run_pipeline(
        fixture,
        constraints_override=fixed_constraints,
        decisions=[decision, correction],
        revisions=[revision, fixed_revision],
    )
    assert conflict["validation_report"]["status"] == "INFEASIBLE"
    assert fixed["validation_report"]["status"] == "REVIEW_REQUIRED"
    assert fixed["validation_report"]["assertions"]["fixture_has_10_zero_cost_optima"] is None
    assert fixed["validation_report"]["assertion_applicability"]["fixture_has_10_zero_cost_optima"] == (
        "NOT_APPLICABLE_AFTER_REVIEW_OR_INPUT_EDIT"
    )
    assert correction["old_value"]["id"] == "H3"
    assert correction["old_value"]["enabled"] is True


def test_regression_unchanged_unaffected_artifacts():
    fixture = get_fixture()
    before = run_pipeline(fixture)
    constraints, decision, revision = apply_constraint_edit(
        before,
        target_step="04",
        object_id="H4",
        old_value="ABSENT",
        new_value="ADD MUST_LINK(R4,R6)",
        reason="Create a temporary conflict.",
        source="TEST-REVIEW",
        actor="reviewer-1",
    )
    after = run_pipeline(fixture, constraints_override=constraints, decisions=[decision], revisions=[revision])
    for key in ("raw_requirements", "context", "responsibilities", "evidence"):
        assert before[key] == after[key]


def test_reproducible_rerun_with_frozen_fixture():
    fixture = get_fixture()
    assert run_pipeline(fixture) == run_pipeline(fixture)


def test_artifacts_include_provenance_and_scoped_verification_status():
    artifacts = run_pipeline(get_fixture())
    json_artifacts = {key: value for key, value in artifacts.items() if isinstance(value, dict)}
    for payload in json_artifacts.values():
        metadata = payload["artifact_metadata"]
        assert metadata["provenance"]["kind"]
        assert metadata["provenance"]["execution_mode"] == "OFFLINE_FIXTURE"
        assert "verification_status" in metadata
        assert metadata["verification_scope"]
    assert artifacts["validation_report"]["assertions"][
        "all_artifacts_have_provenance_and_verification_status"
    ] is True
    assert artifacts["quanta"]["artifact_metadata"]["verification_status"] == "PROPOSED_NOT_VERIFIED"


def test_structured_project_package_validates_source_spans():
    fixture = get_fixture()
    fixture["fixture_label"] = "USER_SUPPLIED"
    artifacts = validate_project_package(fixture)
    assert artifacts["validation_report"]["execution_mode"] == "STRUCTURED_INPUT"
    assert artifacts["validation_report"]["assertions"]["all_raw_source_spans_valid"] is True

    invalid = get_fixture()
    text = invalid["raw_requirements"]["requirements"][0]["text"]
    invalid["raw_requirements"]["requirements"][0]["source_ref"]["quote"] = "X" * len(text)
    invalid["raw_requirements"]["requirements"][0]["source_ref"]["end"] = len(text)
    with pytest.raises(ValueError, match="all_raw_source_spans_valid"):
        validate_project_package(invalid)

    invalid_evidence = get_fixture()
    invalid_evidence["evidence"][0]["source_refs"][0]["quote"] = "Unsupported evidence quote"
    with pytest.raises(ValueError, match="evidence_sources_well_formed"):
        validate_project_package(invalid_evidence)


def test_source_checked_llm_proposals_can_feed_candidate_pipeline():
    fixture = get_fixture()
    requirements = fixture["raw_requirements"]["requirements"]
    responsibility_by_fr = {
        item["requirement_ids"][0]: item for item in fixture["responsibilities"]
    }
    proposals = []
    normalized = []
    for requirement in requirements:
        original = responsibility_by_fr[requirement["id"]]
        source_id = requirement["source_ref"]["source_id"]
        proposals.append(
            {
                "id": original["id"],
                "name": f"Proposed {original['name']}",
                "activity": original["activity"],
                "operation": original["operation"],
                "requirement_ids": [requirement["id"]],
                "decomposition_rationale": "Test proposal grounded in the cited FR.",
                "source_id": source_id,
            }
        )
        normalized.append(
            {
                "id": requirement["id"],
                "normalized_text": requirement["text"],
                "source_id": source_id,
                "requirement_id_valid": True,
                "source_matches_requirement": True,
                "source_id_valid": True,
                "source_span_resolved": True,
                "source_ref": requirement["source_ref"],
                "status": "REVIEW_REQUIRED",
                "validation_note": "Fixture proposal for testing.",
            }
        )
    proposal_data = {
        "model": "fixture-model",
        "context_summary": "Cited proposal summary.",
        "normalized_requirements": normalized,
        "proposals": proposals,
        "can_apply_to_fixture": True,
    }
    model_fixture = apply_proposals_to_fixture(fixture, proposal_data)
    artifacts = run_pipeline(model_fixture, execution_mode="OLLAMA_ASSISTED")
    assert artifacts["responsibilities"]["provenance"] == "LOCAL_OLLAMA_UNVERIFIED"
    assert artifacts["context"]["llm_normalization_proposal"]["status"] == "REVIEW_REQUIRED"
    assert artifacts["partitions"]["optimal_candidate_count"] == 10


def test_revision_diff_is_serializable_without_self_reference():
    fixture = get_fixture()
    before = run_pipeline(fixture)
    constraints, decision, revision = apply_constraint_edit(
        before,
        target_step="04",
        object_id="H4",
        old_value="ABSENT",
        new_value="ADD MUST_LINK(R4,R6)",
        reason="Detect the H3/H4 conflict.",
        source="TEST-REVIEW",
        actor="reviewer-1",
    )
    after = run_pipeline(fixture, constraints_override=constraints, decisions=[decision], revisions=[revision])
    diff = artifact_diff(before, after, exclude={"decisions", "revisions"})
    after["revisions"]["items"][-1]["changed_artifacts"] = sorted(
        set(diff["changed_artifacts"]) | {"decisions", "revisions"}
    )
    after["revisions"]["items"][-1]["artifact_diff"] = diff["changes"]
    json.dumps(after)


def _make_llm_bundle(fixture):
    raw = fixture["raw_requirements"]
    by_fr = {item["requirement_ids"][0]: item for item in fixture["responsibilities"]}
    normalized = []
    proposals = []
    for requirement in raw["requirements"]:
        source_id = requirement["source_ref"]["source_id"]
        original = by_fr[requirement["id"]]
        normalized.append(
            {
                "id": requirement["id"],
                "normalized_text": requirement["text"],
            }
        )
        proposals.append(
            {
                "id": f"proposal-{requirement['id']}",
                "name": original["name"],
                "activity": original["activity"],
                "operation": original["operation"],
                "requirement_ids": [requirement["id"]],
                "decomposition_rationale": "Test proposal grounded in the cited FR.",
            }
        )
    return {
        "context_summary": "Grounded summary.",
        "normalized_requirements": normalized,
        "proposals": proposals,
        "evidence_proposals": [
            {
                "id": "evidence-proposal-1",
                "subject_requirement_id": "FR-01",
                "predicate": "may_depend_on",
                "object_requirement_id": "FR-06",
                "proposed_status": "UNKNOWN",
                "source_requirement_ids": ["FR-01"],
                "rationale": "The available requirement does not establish runtime interaction details.",
            }
        ],
        "boundary_hypotheses": [
            {
                "id": "boundary-hypothesis-1",
                "requirement_ids": ["FR-01", "FR-02"],
                "boundary_rationale": "These responsibilities may share a boundary; this remains a hypothesis.",
                "source_requirement_ids": ["FR-01", "FR-02"],
            }
        ],
    }


def test_invalid_llm_source_reference_stays_review_required(monkeypatch):
    fixture = get_fixture()
    bundle = _make_llm_bundle(fixture)
    bundle["proposals"][0]["requirement_ids"] = ["FR-99"]
    request_capture = {}

    def fake_request(*args, **kwargs):
        request_capture.update(kwargs["payload"])
        return {
            "model": "test-model",
            "message": {"content": json.dumps(bundle)},
        }

    monkeypatch.setattr("eqcr.ollama._request", fake_request)
    result = propose_responsibilities(fixture["raw_requirements"], "test-model")
    assert result["status"] == "REVIEW_REQUIRED"
    assert result["can_apply_to_fixture"] is False
    assert result["proposals"][0]["requirement_ids_valid"] is False
    assert result["proposals"][0]["source_ids_valid"] is False
    assert isinstance(request_capture["format"], dict)
    assert result["prompt_version"] == "requirements-context-multiresponsibility-relation-boundary-v7"
    assert len(result["input_sha256"]) == 64
    prompt = request_capture["messages"][0]["content"]
    assert "ADDITIONAL CONTEXT FOR SUMMARY ONLY" in prompt
    assert fixture["raw_requirements"]["workflows"][0]["text"] in prompt
    assert fixture["raw_requirements"]["scenarios"][0]["source_ref"]["quote"] in prompt


def test_llm_evidence_and_boundary_proposals_resolve_sources_but_remain_review_required(monkeypatch):
    fixture = get_fixture()
    bundle = _make_llm_bundle(fixture)

    def fake_request(*args, **kwargs):
        return {
            "model": "test-model",
            "message": {"content": json.dumps(bundle)},
        }

    monkeypatch.setattr("eqcr.ollama._request", fake_request)
    result = propose_responsibilities(fixture["raw_requirements"], "test-model")
    evidence = result["evidence_proposals"][0]
    boundary = result["boundary_hypotheses"][0]
    assert result["evidence_proposals_valid"] is True
    assert result["boundary_hypotheses_valid"] is True
    assert evidence["source_refs"][0]["quote"] == fixture["raw_requirements"]["requirements"][0]["text"]
    assert evidence["review_status"] == "REVIEW_REQUIRED"
    assert evidence["provenance"] == "LOCAL_OLLAMA_UNVERIFIED"
    assert boundary["source_refs_valid"] is True
    assert boundary["review_status"] == "REVIEW_REQUIRED"

    bundle["evidence_proposals"][0]["source_requirement_ids"] = ["FR-99"]
    bundle["boundary_hypotheses"][0]["source_requirement_ids"] = ["FR-01", "FR-99"]
    invalid = propose_responsibilities(fixture["raw_requirements"], "test-model")
    assert invalid["evidence_proposals_valid"] is False
    assert invalid["boundary_hypotheses_valid"] is False
    assert invalid["evidence_proposals"][0]["review_status"] == "REVIEW_REQUIRED"


def test_ollama_unavailable_does_not_block_deterministic_mode(monkeypatch):
    def unavailable(*args, **kwargs):
        raise OllamaError("Ollama unavailable for test")

    monkeypatch.setattr("eqcr.ollama._request", unavailable)
    with pytest.raises(OllamaError, match="unavailable"):
        list_models()
    artifacts = run_pipeline(get_fixture(), execution_mode="OFFLINE_FIXTURE")
    assert artifacts["partitions"]["optimal_candidate_count"] == 10


def test_zip_export_contains_artifacts_and_versioned_snapshots():
    artifacts = run_pipeline(get_fixture())
    payload = make_export_zip(
        {"validation_report": artifacts["validation_report"]},
        {"snapshots/v1.json": artifacts, "snapshots/v2.json": {"status": "INFEASIBLE"}},
    )
    with ZipFile(BytesIO(payload)) as archive:
        assert set(archive.namelist()) == {
            "validation_report.json",
            "snapshots/v1.json",
            "snapshots/v2.json",
        }
        assert json.loads(archive.read("snapshots/v2.json")) == {"status": "INFEASIBLE"}
