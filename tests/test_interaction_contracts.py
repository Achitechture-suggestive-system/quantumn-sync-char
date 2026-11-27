"""Versioned interaction-contract defaults and human-decision guards."""

from copy import deepcopy

import pytest

from eqcr.pipeline import run_pipeline
from eqcr.review import apply_interaction_contract_edit
from eqcr.interaction_contracts import make_unresolved_contract
from eqcr.models import InteractionContract
from eqcr.storage import make_export_zip, verify_export_zip
from eqcr.tutor_support import get_tutor_support_fixture


def _source_ref():
    return {"source_id": "REQ-1", "quote": "Explicit timing requirement.", "start": 0, "end": 28}


def test_unresolved_contract_is_versioned_and_preserves_unknowns():
    contract = make_unresolved_contract("IC-1", [_source_ref()], ["latency", "failure", "retry"])
    assert contract["schema_id"] == "EQCR-INTERACTION-CONTRACT"
    assert contract["schema_version"] == "1.0.0"
    assert contract["decision_table_version"] == "1.0.0"
    assert contract["selected_mode"] == "UNDECIDED"
    assert contract["decision_basis_status"] == "INSUFFICIENT_EVIDENCE"
    assert contract["request_fields"] == contract["response_fields"] == "UNKNOWN"
    assert contract["source_refs"][0]["source_id"] == "REQ-1"


def test_selected_sync_mode_requires_cited_explicit_complete_human_decision():
    contract = InteractionContract(
        contract_id="IC-SYNC",
        selected_mode="SYNC",
        selection_status="APPROVED",
        decision_basis_status="HUMAN_DECISION",
        provenance="HUMAN_DECISION",
        reviewer_id="reviewer-1",
        reviewed_at="2026-11-16T08:00:00Z",
        source_refs=[_source_ref()],
        decision_rationale="The source explicitly requires completion before returning.",
        request_must_wait_for_completion=True,
        request_may_return_before_completion=False,
        operation="submit request and await result",
        data_dependency="request status record",
        request_fields="learner, tutor, slot",
        response_fields="accepted or rejected result",
        versioning="v1 request/response contract",
        consistency="read-your-writes for the returned request status",
        latency_budget="within the source-backed request target",
        failure_handling="return a visible failure status",
        retry_policy="retry only after a terminal failure response",
        timeout_policy="bounded request timeout",
        idempotency_policy="deduplicate by request id",
    )
    assert contract.selected_mode == "SYNC"


def test_mode_cannot_be_selected_from_unreviewed_or_contradictory_signals():
    base = {
        "contract_id": "IC-INVALID",
        "selected_mode": "SYNC",
        "selection_status": "APPROVED",
        "decision_basis_status": "HUMAN_DECISION",
        "provenance": "HUMAN_DECISION",
        "reviewer_id": "reviewer-1",
        "reviewed_at": "2026-11-16T08:00:00Z",
        "source_refs": [_source_ref()],
        "decision_rationale": "Reviewed explicit source requirement.",
        "request_must_wait_for_completion": True,
        "request_may_return_before_completion": True,
        "operation": "request",
        "data_dependency": "request record",
        "request_fields": "request fields",
        "response_fields": "response fields",
        "versioning": "v1",
        "consistency": "read-your-writes",
        "latency_budget": "source target",
        "failure_handling": "explicit failure response",
        "retry_policy": "bounded retries",
        "timeout_policy": "bounded timeout",
        "idempotency_policy": "request ID",
    }
    with pytest.raises(ValueError, match="complete, cited, non-contradictory"):
        InteractionContract.model_validate(base)

    base["request_may_return_before_completion"] = False
    base["decision_basis_status"] = "INSUFFICIENT_EVIDENCE"
    with pytest.raises(ValueError, match="complete, cited, non-contradictory"):
        InteractionContract.model_validate(base)


def test_approved_interaction_mode_requires_timezone_aware_review_timestamp():
    with pytest.raises(ValueError, match="complete, cited, non-contradictory"):
        InteractionContract(
            contract_id="IC-NO-TZ",
            selected_mode="SYNC",
            selection_status="APPROVED",
            decision_basis_status="HUMAN_DECISION",
            provenance="HUMAN_DECISION",
            reviewer_id="reviewer-1",
            reviewed_at="2026-11-16T08:00:00",
            source_refs=[_source_ref()],
            decision_rationale="Reviewed source requirement.",
            request_must_wait_for_completion=True,
            operation="request",
            data_dependency="request record",
            request_fields="request fields",
            response_fields="response fields",
            versioning="v1",
            consistency="read-your-writes",
            latency_budget="source target",
            failure_handling="explicit failure response",
            retry_policy="bounded retries",
            timeout_policy="bounded timeout",
            idempotency_policy="request ID",
        )


def _approved_contract(edge, mode="ASYNC"):
    contract = deepcopy(edge["contract"])
    contract.update(
        selected_mode=mode,
        selection_status="APPROVED",
        decision_basis_status="HUMAN_DECISION",
        provenance="HUMAN_DECISION",
        reviewer_id="human-reviewer-test",
        reviewed_at="2026-11-16T08:00:00Z",
        decision_rationale="Test-only human decision; the exact cited spans are preserved for structural validation.",
        request_must_wait_for_completion=mode == "SYNC",
        request_may_return_before_completion=mode == "ASYNC",
        operation="submit a tutoring request and deliver its later decision",
        data_dependency="session request decision state",
        request_fields="learner, tutor, and session slot identifiers",
        response_fields="request accepted for review or a final decision notice",
        versioning="versioned session request contract v1",
        consistency="decision status is read after the reviewer transition",
        latency_budget="reviewed timing budget for request acceptance",
        failure_handling="record delivery failure and retain request state",
        retry_policy="bounded retry after transient notification failure",
        timeout_policy="expire a delivery attempt and record its result",
        idempotency_policy="deduplicate by session request identifier",
        unresolved_decisions=[],
    )
    return contract


def test_human_contract_decision_recomputes_interactions_without_changing_constraints():
    fixture = get_tutor_support_fixture()
    before = run_pipeline(fixture, execution_mode="P2_TEST_ONLY")
    edge = before["interactions"]["edges"][0]
    contract = _approved_contract(edge)
    revised_fixture, decision, revision = apply_interaction_contract_edit(fixture, before, contract)

    after = run_pipeline(
        revised_fixture,
        decisions=[decision],
        revisions=[revision],
        execution_mode="P2_TEST_ONLY",
    )
    revised_edge = next(item for item in after["interactions"]["edges"] if item["id"] == edge["id"])

    assert revised_edge["label"] == "ASYNC"
    assert revised_edge["review_status"] == "APPROVED"
    assert revised_edge["contract"]["provenance"] == "HUMAN_DECISION"
    assert after["partitions"] == before["partitions"]
    assert after["quality_profiles"] == before["quality_profiles"]
    assert after["traceability"] != before["traceability"]
    assert after["decisions"]["items"][-1]["decision_type"] == "HUMAN_INTERACTION_CONTRACT_DECISION"
    assert after["validation_report"]["assertions"]["interaction_decisions_match_contract_state"] is True
    assert revision["target_step"] == "07"
    assert "quality_profiles" in revision["invalidated_artifacts"]
    manifest = verify_export_zip(make_export_zip(after))["manifest"]
    assert manifest["provenance_summary"]["interactions"]["contract_provenance"]["HUMAN_DECISION"] == 1


def test_interaction_contract_review_rejects_unresolved_or_wrong_edge_contract():
    fixture = get_tutor_support_fixture()
    artifacts = run_pipeline(fixture, execution_mode="P2_TEST_ONLY")
    edge = artifacts["interactions"]["edges"][0]
    unresolved = deepcopy(edge["contract"])
    with pytest.raises(ValueError, match="must select SYNC or ASYNC"):
        apply_interaction_contract_edit(fixture, artifacts, unresolved)

    wrong_id = _approved_contract(edge)
    wrong_id["contract_id"] = "EDGE-UNKNOWN"
    with pytest.raises(ValueError, match="was not found"):
        apply_interaction_contract_edit(fixture, artifacts, wrong_id)


def test_interaction_contract_recompute_rejects_nonmatching_source_span():
    fixture = get_tutor_support_fixture()
    before = run_pipeline(fixture, execution_mode="P2_TEST_ONLY")
    edge = before["interactions"]["edges"][0]
    contract = _approved_contract(edge)
    contract["source_refs"][0]["quote"] = "fabricated source quote"
    contract["source_refs"][0]["end"] = contract["source_refs"][0]["start"] + len("fabricated source quote")
    revised_fixture, decision, revision = apply_interaction_contract_edit(fixture, before, contract)

    with pytest.raises(ValueError, match="unresolved source span"):
        run_pipeline(
            revised_fixture,
            decisions=[decision],
            revisions=[revision],
            execution_mode="P2_TEST_ONLY",
        )
