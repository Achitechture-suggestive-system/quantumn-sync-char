"""Versioned, evidence-gated interaction decision support."""

from __future__ import annotations

from typing import Any

from .models import InteractionContract, SourceRef


CONTRACT_SCHEMA_ID = "EQCR-INTERACTION-CONTRACT"
CONTRACT_SCHEMA_VERSION = "1.0.0"
DECISION_TABLE_ID = "EQCR-SYNC-ASYNC-DECISION"
DECISION_TABLE_VERSION = "1.0.0"

INTERACTION_DECISION_TABLE: dict[str, Any] = {
    "id": DECISION_TABLE_ID,
    "version": DECISION_TABLE_VERSION,
    "provenance": "ARCHITECTURAL_POLICY",
    "status": "POLICY_DEFINED_NOT_EMPIRICALLY_VALIDATED",
    "default": "UNDECIDED",
    "rules": [
        {
            "mode": "SYNC",
            "requires": [
                "human-approved source evidence explicitly requires a completed outcome before the initiating request returns",
                "consistency, latency, failure, timeout, retry, and idempotency decisions are reviewed",
            ],
        },
        {
            "mode": "ASYNC",
            "requires": [
                "human-approved source evidence explicitly permits a response before the linked activity completes",
                "completion notification, delivery, failure, retry, and idempotency decisions are reviewed",
            ],
        },
        {
            "mode": "UNDECIDED",
            "applies_when": [
                "mode evidence is missing, ambiguous, contradictory, or not human-approved",
                "business ordering is the only relation available",
            ],
        },
    ],
    "prohibited_inference": "Business ordering, relation adjacency, or scenario association alone cannot select SYNC or ASYNC.",
}


def make_unresolved_contract(
    contract_id: str,
    source_refs: list[dict[str, Any]],
    unresolved_decisions: list[str],
) -> dict[str, Any]:
    contract = InteractionContract(
        contract_id=contract_id,
        source_refs=[SourceRef.model_validate(item) for item in source_refs],
        unresolved_decisions=unresolved_decisions,
    )
    return contract.model_dump(mode="json")


def apply_interaction_contract_overrides(
    interactions: dict[str, Any],
    contract_payloads: list[dict[str, Any]],
    source_texts: dict[str, str],
) -> dict[str, Any]:
    """Apply explicit, schema-valid human interaction decisions to current candidate edges."""
    if not isinstance(contract_payloads, list):
        raise ValueError("Interaction contract overrides must be a list.")
    if not contract_payloads:
        return interactions
    edges_by_id = {edge["id"]: edge for edge in interactions.get("edges", [])}
    contract_ids = [payload.get("contract_id") for payload in contract_payloads if isinstance(payload, dict)]
    if len(contract_ids) != len(contract_payloads) or len(contract_ids) != len(set(contract_ids)):
        raise ValueError("Interaction contract overrides must be JSON objects with unique contract IDs.")
    for payload in contract_payloads:
        contract = InteractionContract.model_validate(payload)
        if contract.selected_mode not in {"SYNC", "ASYNC"}:
            raise ValueError("A contract review must explicitly approve SYNC or ASYNC; leave unresolved contracts unchanged.")
        edge = edges_by_id.get(contract.contract_id)
        if edge is None:
            raise ValueError(f"Interaction contract {contract.contract_id} does not match a current candidate edge.")
        for reference in contract.source_refs:
            text = source_texts.get(reference.source_id)
            if (
                text is None
                or reference.end > len(text)
                or text[reference.start : reference.end] != reference.quote
            ):
                raise ValueError(
                    f"Interaction contract {contract.contract_id} has an unresolved source span: {reference.source_id}."
                )
        contract_data = contract.model_dump(mode="json")
        edge.update(
            contract=contract_data,
            source_refs=[reference.model_dump(mode="json") for reference in contract.source_refs],
            label=contract.selected_mode,
            review_status="APPROVED",
            selection_status="APPROVED",
            consistency=contract.consistency,
            latency_budget=contract.latency_budget,
            failure_handling=contract.failure_handling,
            status="HUMAN_DECISION_RECORDED",
        )
    unresolved_count = sum(
        edge.get("contract", {}).get("selected_mode") == "UNDECIDED"
        for edge in interactions.get("edges", [])
    )
    interactions["status"] = "PARTIALLY_REVIEWED" if unresolved_count else "HUMAN_DECISION_RECORDED"
    interactions["reviewed_contract_ids"] = sorted(contract_ids)
    interactions["unresolved_contract_count"] = unresolved_count
    return interactions
