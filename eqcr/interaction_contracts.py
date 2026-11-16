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
