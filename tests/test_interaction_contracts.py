"""Versioned interaction-contract defaults and human-decision guards."""

import pytest

from eqcr.interaction_contracts import make_unresolved_contract
from eqcr.models import InteractionContract


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
