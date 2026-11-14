"""Frozen, source-backed demo inputs. These are illustrative requirements, not PetClinic claims."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from .models import RawRequirements


def _ref(source_id: str, quote: str, text: str) -> dict[str, Any]:
    start = text.find(quote)
    if start < 0:
        raise ValueError(f"Fixture quote is not present in {source_id}")
    return {"source_id": source_id, "quote": quote, "start": start, "end": start + len(quote)}


def get_fixture() -> dict[str, Any]:
    """Return a fresh copy of the precomputed mini-case and its traceability map."""
    requirements = [
        ("FR-01", "A user can find an owner by entering an owner name."),
        ("FR-02", "A user can create an owner profile with contact details."),
        ("FR-03", "A user can edit an existing owner's profile and contact details."),
        ("FR-04", "A user can add a pet to an owner."),
        ("FR-05", "A user can edit an existing pet's details."),
        ("FR-06", "A user can schedule a visit for a pet."),
    ]
    workflow_text = (
        "Find or create an owner, maintain owner details, add or edit a pet, "
        "then schedule a visit for that pet."
    )
    scenario_text = "Owner Search: p95 response time target is at most 250 ms at 300 requests per second."
    interaction_scenario = "Pet and Visit interaction: consistency, latency, failure handling, and contract are unspecified."
    raw = {
        "case_id": "PETCLINIC-MINI-WHAT-IF",
        "context_id": "C0",
        "context_description": (
            "A deliberately small requirements-only PetClinic-style case. No source code, runtime topology, "
            "deployment evidence, or confirmed business policies are included."
        ),
        "requirements": [
            {
                "id": rid,
                "text": text,
                "source_ref": _ref(f"REQ-{rid}", text, text),
            }
            for rid, text in requirements
        ],
        "workflows": [
            {
                "id": "WF-01",
                "text": workflow_text,
                "source_ref": _ref("WF-01", workflow_text, workflow_text),
            }
        ],
        "scenarios": [
            {
                "id": "SC-OWNER-SEARCH",
                "name": "Owner Search",
                "stimulus": "A search request for an owner is submitted under load.",
                "response_measure": "p95 response time at the stated request rate",
                "target": "p95 <= 250 ms @ 300 requests/s",
                "status": "NOT_MEASURED",
                "source_ref": _ref("SC-OWNER-SEARCH", scenario_text, scenario_text),
            },
            {
                "id": "SC-PET-VISIT",
                "name": "Pet and Visit interaction",
                "stimulus": "A visit is scheduled for a pet.",
                "response_measure": "consistency, latency, failure handling, and contract",
                "target": None,
                "status": "INSUFFICIENT_EVIDENCE",
                "source_ref": _ref("SC-PET-VISIT", interaction_scenario, interaction_scenario),
            },
        ],
    }
    validated = RawRequirements.model_validate(raw).model_dump(mode="json")

    # The offline proposals are frozen fixture data and remain review-required.
    responsibility_specs = [
        ("R1", "Find Owner", "Owner search", "find owner", "FR-01"),
        ("R2", "Create Owner", "Owner maintenance", "create owner", "FR-02"),
        ("R3", "Edit Owner", "Owner maintenance", "edit owner", "FR-03"),
        ("R4", "Add Pet", "Pet maintenance", "add pet", "FR-04"),
        ("R5", "Edit Pet", "Pet maintenance", "edit pet", "FR-05"),
        ("R6", "Schedule Visit", "Visit scheduling", "schedule visit", "FR-06"),
    ]
    responsibilities = []
    by_id = {item["id"]: item for item in validated["requirements"]}
    for rid, name, activity, operation, fr_id in responsibility_specs:
        requirement = by_id[fr_id]
        responsibilities.append(
            {
                "id": rid,
                "name": name,
                "activity": activity,
                "operation": operation,
                "requirement_ids": [fr_id],
                "source_refs": [requirement["source_ref"]],
                "workflow_activity_ids": [],
                "workflow_mapping_status": "UNRESOLVED",
                "workflow_note": "WF-01 is narrative text without stable task IDs; no task-level mapping is inferred.",
                "semantic_status": "REVIEW_REQUIRED",
            }
        )

    policy_quote = "H1/H2/H3 are what-if policies for this demo, not confirmed business or architecture facts."
    policy_ref = {
        "source_id": "DEMO-POLICY-NOTE",
        "quote": policy_quote,
        "start": 0,
        "end": len(policy_quote),
    }
    constraints = [
        {
            "id": "H1", "relation": "MUST_LINK", "left": "R2", "right": "R3",
            "hardness": "HARD", "origin": "WHAT_IF_POLICY", "enabled": True,
            "source_refs": [policy_ref], "rationale": "Demo what-if policy: keep Create Owner and Edit Owner together.",
        },
        {
            "id": "H2", "relation": "MUST_LINK", "left": "R4", "right": "R5",
            "hardness": "HARD", "origin": "WHAT_IF_POLICY", "enabled": True,
            "source_refs": [policy_ref], "rationale": "Demo what-if policy: keep Add Pet and Edit Pet together.",
        },
        {
            "id": "H3", "relation": "CANNOT_LINK", "left": "R4", "right": "R6",
            "hardness": "HARD", "origin": "WHAT_IF_POLICY", "enabled": True,
            "source_refs": [policy_ref], "rationale": "Demo what-if policy: separate Pet maintenance and Visit scheduling.",
        },
    ]
    evidence = [
        {
            "id": f"EV-{responsibility['id']}-01", "subject_id": responsibility["id"],
            "predicate": "responsibility_named_by_requirement", "object_id": responsibility["requirement_ids"][0],
            "status": "PRESENT", "source_refs": responsibility["source_refs"], "is_assumption": False,
            "provenance": "SOURCE_BACKED", "review_status": "REVIEW_REQUIRED",
            "rationale": "The cited requirement text names this capability; semantic grouping still needs human review.",
        }
        for responsibility in responsibilities
    ]
    evidence.append(
        {
            "id": "EV-PET-VISIT-CONSISTENCY", "subject_id": "R6", "predicate": "consistency_contract",
            "object_id": "R4", "status": "UNKNOWN", "source_refs": [validated["scenarios"][1]["source_ref"]],
            "is_assumption": False, "provenance": "SOURCE_BACKED", "review_status": "REVIEW_REQUIRED",
            "rationale": "The mini-case explicitly leaves consistency unspecified; UNKNOWN is not treated as false.",
        }
    )
    evidence.append(
        {
            "id": "EV-RUNTIME-TOPOLOGY", "subject_id": "C0", "predicate": "independent_deployment_evidence",
            "object_id": "deployment_topology", "status": "SCOPED_ABSENT", "source_refs": [], "is_assumption": False,
            "provenance": "SCOPE_BOUNDARY", "review_status": "REVIEW_REQUIRED",
            "rationale": "Runtime and deployment evidence are outside this requirements-only mini-case.",
        }
    )
    return deepcopy(
        {
            "raw_requirements": validated,
            "responsibilities": responsibilities,
            "evidence": evidence,
            "constraints": constraints,
            "fixture_label": "PRECOMPUTED",
            "fixture_note": "Frozen requirements and responsibility proposals; every proposal remains review-required.",
        }
    )
