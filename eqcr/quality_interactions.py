"""Evidence-gated interaction assessments used by quality-aware candidates."""

from __future__ import annotations

from typing import Literal

from pydantic import Field

from .models import SourceRef, StrictModel
from .requirements_engine import ReviewRecord, require_span

InteractionMode = Literal["LOCAL", "SYNC_REQUEST_RESPONSE", "ASYNC_EVENT", "ASYNC_COMMAND", "UNRESOLVED"]
POLICY_VERSION = "1.0.0"


class InteractionReview(ReviewRecord):
    mode: InteractionMode
    optimizer_weight: float | None = Field(default=None, gt=0, allow_inf_nan=False)


class InteractionAssessment(StrictModel):
    id: str = Field(min_length=1)
    caller: str
    callee: str
    purpose: str
    source_refs: list[SourceRef] = Field(default_factory=list)
    basis_refs: dict[Literal["timing", "consistency", "atomicity", "freshness"], SourceRef] = Field(default_factory=dict)
    evidence_ids: list[str] = Field(default_factory=list)
    request: str | None = None
    response: str | None = None
    timing: Literal["IMMEDIATE", "DEFERRED", "UNKNOWN"] = "UNKNOWN"
    consistency: Literal["STRONG", "EVENTUAL", "UNKNOWN"] = "UNKNOWN"
    freshness: str | None = None
    atomicity: Literal["REQUIRED", "NOT_REQUIRED", "UNKNOWN"] = "UNKNOWN"
    deadline: SourceRef | None = None
    consistency_protocol: str | None = None
    distributed_proof: SourceRef | None = None
    message_intent: Literal["EVENT", "COMMAND", "UNKNOWN"] = "UNKNOWN"
    delivery: str | None = None
    retries: str | None = None
    idempotency: str | None = None
    ordering: str | None = None
    failure: str | None = None
    timeout: str | None = None
    independent_availability: bool | None = None
    operational_overhead: str | None = None
    review: InteractionReview | None = None


def _specified(value: str | None) -> bool:
    return bool(value and value.strip() and value.strip().upper() not in {"UNKNOWN", "UNRESOLVED"})


def propose_mode(item: InteractionAssessment) -> tuple[InteractionMode, list[str]]:
    gaps = [
        key for key in ("purpose", "request", "response", "freshness", "failure", "timeout")
        if not _specified(getattr(item, key))
    ]
    gaps.extend(key for key in ("timing", "consistency", "atomicity") if getattr(item, key) == "UNKNOWN")
    if not item.deadline:
        gaps.append("deadline")
    if not item.source_refs:
        gaps.append("source evidence")
    gaps.extend(f"{key} citation" for key in ("timing", "consistency", "atomicity", "freshness")
                if key not in item.basis_refs)
    if gaps:
        return "UNRESOLVED", gaps
    if item.atomicity == "REQUIRED":
        if item.consistency != "STRONG":
            return "UNRESOLVED", ["consistency conflicts with atomicity"]
        if not (_specified(item.consistency_protocol) and item.distributed_proof and item.review
                and item.review.mode == "SYNC_REQUEST_RESPONSE" and item.timing == "IMMEDIATE"):
            return "LOCAL", []
    if item.timing == "IMMEDIATE":
        return "SYNC_REQUEST_RESPONSE", []
    if item.consistency != "EVENTUAL" or item.atomicity != "NOT_REQUIRED":
        return "UNRESOLVED", ["deferred completion requires explicit eventual consistency and no atomic invariant"]
    gaps = [
        key for key in ("delivery", "idempotency", "retries", "ordering")
        if not _specified(getattr(item, key))
    ]
    if item.message_intent == "UNKNOWN":
        gaps.append("event or command")
    if gaps:
        return "UNRESOLVED", gaps
    return ("ASYNC_EVENT" if item.message_intent == "EVENT" else "ASYNC_COMMAND"), []


def validate_interaction(item: InteractionAssessment, texts: dict[str, str], role_ids: set[str]) -> None:
    if item.caller == item.callee or not {item.caller, item.callee} <= role_ids:
        raise ValueError(f"{item.id} has invalid responsibility endpoints.")
    for reference in [*item.source_refs, *item.basis_refs.values(), item.deadline, item.distributed_proof]:
        if reference is not None:
            require_span(reference, texts)
    if item.review:
        mode, gaps = propose_mode(item)
        if item.review.mode != mode or mode == "UNRESOLVED":
            raise ValueError(f"{item.id} has an unsupported reviewed mode: {'; '.join(gaps) or mode}.")
        if item.review.optimizer_weight and mode.startswith("ASYNC") and item.independent_availability is not True:
            raise ValueError(f"{item.id} requires explicit independent availability for an async separation preference.")


def interaction_profile(item: InteractionAssessment, assignment: dict[str, str]) -> dict:
    mode, gaps = propose_mode(item)
    caller_group, callee_group = assignment[item.caller], assignment[item.callee]
    original_mode = mode
    if mode == "LOCAL" and caller_group != callee_group:
        mode, gaps = "UNRESOLVED", ["Atomic local operation crosses the proposed boundary."]
    benefits = {
        "LOCAL": "Keeps required state changes in one proposed boundary.",
        "SYNC_REQUEST_RESPONSE": "Returns the completed outcome before the caller continues.",
        "ASYNC_EVENT": "Allows observers to process a fact after the initiating activity completes.",
        "ASYNC_COMMAND": "Lets completion occur after the initiating request returns.",
        "UNRESOLVED": "The selected evidence leaves the mode open.",
    }
    risks = {
        "LOCAL": "Co-location still needs verification of a shared transaction.",
        "SYNC_REQUEST_RESPONSE": "Caller depends on completion and may inherit latency or failure.",
        "ASYNC_EVENT": "Delayed visibility and replay require delivery and ordering checks.",
        "ASYNC_COMMAND": "Acceptance and completion can diverge; retries can duplicate effects.",
        "UNRESOLVED": "Contract and source gaps prevent assessing latency or failure behavior.",
    }
    return {
        "id": item.id, "caller": item.caller, "callee": item.callee,
        "from_quantum": caller_group, "to_quantum": callee_group,
        "mode": mode, "reviewed_mode": item.review.mode if item.review else None,
        "alternative_mode": ("LOCAL" if mode == "SYNC_REQUEST_RESPONSE" else "SYNC_REQUEST_RESPONSE")
        if mode != "UNRESOLVED" else original_mode if original_mode != "UNRESOLVED" else None,
        "alternative_status": "CONDITIONAL_REVIEW_REQUIRED",
        "status": "UNRESOLVED" if mode == "UNRESOLVED" else "HUMAN_APPROVED" if item.review else "PROPOSED",
        "provenance": "HUMAN_DECISION" if item.review and mode != "UNRESOLVED" else "DETERMINISTIC_RULE_INFERENCE",
        "benefit": benefits[mode], "risk": risks[mode], "missing_evidence": gaps,
        "review_trigger": "Review any change to wait, freshness, atomicity, deadline, or the cited contract.",
        "contract": item.model_dump(mode="json"), "verification_status": "NOT_MEASURED",
    }
