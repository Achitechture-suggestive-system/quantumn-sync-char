"""Original, requirements-only Tutor Support case prepared for P2 validation."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from .models import RawRequirements


def _source_ref(source_id: str, quote: str, text: str) -> dict[str, Any]:
    start = text.find(quote)
    if start < 0:
        raise ValueError(f"Source quote is not present in {source_id}")
    return {"source_id": source_id, "quote": quote, "start": start, "end": start + len(quote)}


def get_tutor_support_fixture() -> dict[str, Any]:
    """Return a fresh prepared case template; no responsibility is attributed to an LLM here."""
    requirement_texts = [
        ("FR-01", "A learner can search the tutor directory by subject and available time."),
        ("FR-02", "A learner can view a tutor profile, subjects, and listed availability."),
        ("FR-03", "A tutor can publish and update weekly availability slots."),
        ("FR-04", "A learner can request a tutoring session in an available slot."),
        ("FR-05", "A tutor can accept or decline a pending tutoring session request."),
        ("FR-06", "The learner receives a notice when the tutor accepts or declines the request."),
    ]
    workflow_texts = [
        ("WF-01", "A learner searches the tutor directory by subject and a time window."),
        ("WF-02", "The learner reviews a tutor profile and selects an open availability slot."),
        ("WF-03", "The learner requests the slot; the tutor accepts or declines the pending request."),
        ("WF-04", "The learner receives a notice of the tutor's decision."),
    ]
    scenario_texts = [
        (
            "SC-REQUEST-ACK",
            "Session request acknowledgement",
            "During a peak period of 50 request submissions per minute, a learner requests an available tutoring slot.",
            "p95 request acknowledgement time at 50 submissions per minute",
            "p95 <= 2 seconds at 50 submissions/minute",
            ["FR-04", "FR-05"],
            "performance efficiency / time behaviour",
            "p95 request acknowledgement latency at 50 submissions/minute",
            "Submit representative session requests at the stated rate and record p95 acknowledgement latency and test environment.",
        ),
        (
            "SC-DECISION-NOTICE",
            "Tutor decision notification",
            "A tutor accepts or declines a pending session request.",
            "percentage of decision notices delivered within 30 seconds",
            "at least 99% of notices delivered within 30 seconds over a rolling 24-hour window",
            ["FR-05", "FR-06"],
            "reliability / timeliness",
            "delivery ratio within 30 seconds over a rolling 24-hour window",
            "Record accepted and declined requests and measure the share of corresponding notices delivered within 30 seconds.",
        ),
    ]
    context_text = (
        "An original, small Tutor Support requirements case. The package contains requirements and workflows only; "
        "it supplies no source code, runtime topology, deployment evidence, or confirmed architecture policy."
    )
    raw = {
        "case_id": "TUTOR-SUPPORT-P2-01",
        "context_id": "C0",
        "context_description": context_text,
        "requirements": [
            {
                "id": requirement_id,
                "text": text,
                "source_ref": _source_ref(f"TUTOR-REQ-{requirement_id}", text, text),
            }
            for requirement_id, text in requirement_texts
        ],
        "workflows": [
            {
                "id": workflow_id,
                "text": text,
                "source_ref": _source_ref(f"TUTOR-{workflow_id}", text, text),
            }
            for workflow_id, text in workflow_texts
        ],
        "scenarios": [
            {
                "id": scenario_id,
                "name": name,
                "stimulus": stimulus,
                "response_measure": response_measure,
                "target": target,
                "related_requirement_ids": related_requirement_ids,
                "interaction_source_requirement_ids": related_requirement_ids,
                "quality_characteristic": quality_characteristic,
                "proposed_metric": proposed_metric,
                "measurement_method": measurement_method,
                "status": "NOT_MEASURED",
                "source_ref": _source_ref(
                    scenario_id,
                    f"{name}. Stimulus: {stimulus} Measure: {response_measure}. Target: {target}.",
                    f"{name}. Stimulus: {stimulus} Measure: {response_measure}. Target: {target}.",
                ),
            }
            for (
                scenario_id,
                name,
                stimulus,
                response_measure,
                target,
                related_requirement_ids,
                quality_characteristic,
                proposed_metric,
                measurement_method,
            ) in scenario_texts
        ],
    }
    validated = RawRequirements.model_validate(raw).model_dump(mode="json")
    requirements_by_id = {item["id"]: item for item in validated["requirements"]}
    responsibilities = [
        {
            "id": f"R{index}",
            "name": f"Prepared placeholder for {requirement_id}",
            "activity": "Responsibility pending local model proposal and human review",
            "operation": "UNRESOLVED",
            "requirement_ids": [requirement_id],
            "source_refs": [requirements_by_id[requirement_id]["source_ref"]],
            "workflow_activity_ids": [],
            "workflow_mapping_status": "UNRESOLVED",
            "workflow_note": "Workflow links are not inferred from narrative overlap.",
            "provenance": "PREPARED_FIXTURE",
            "review_decision_status": "REVIEW_REQUIRED",
            "semantic_status": "REVIEW_REQUIRED",
        }
        for index, (requirement_id, _) in enumerate(requirement_texts, start=1)
    ]
    evidence = [
        {
            "id": f"EV-R{index}-SOURCE",
            "subject_id": f"R{index}",
            "predicate": "responsibility_cites_requirement",
            "object_id": requirement_id,
            "status": "PRESENT",
            "provenance": "SOURCE_BACKED",
            "review_status": "REVIEW_REQUIRED",
            "source_refs": [requirements_by_id[requirement_id]["source_ref"]],
            "is_assumption": False,
            "rationale": "The source link is exact; it does not validate the responsibility interpretation.",
        }
        for index, (requirement_id, _) in enumerate(requirement_texts, start=1)
    ]
    evidence.append(
        {
            "id": "EV-TUTOR-RUNTIME-SCOPE",
            "subject_id": "C0",
            "predicate": "independent_deployment_evidence",
            "object_id": "runtime_topology",
            "status": "SCOPED_ABSENT",
            "provenance": "SCOPE_BOUNDARY",
            "review_status": "REVIEW_REQUIRED",
            "source_refs": [],
            "is_assumption": False,
            "rationale": "Runtime topology is explicitly outside this requirements-only package.",
        }
    )
    return deepcopy(
        {
            "raw_requirements": validated,
            "responsibilities": responsibilities,
            "evidence": evidence,
            "constraints": [],
            "constraint_policy_catalog": {
                "catalog_id": "EQCR-P2-TUTOR-EXPERIMENTAL-POLICIES",
                "version": "1.0.0",
                "status": "EXPERIMENTAL_CASE_POLICY_CATALOG",
                "review_status": "NOT_INDEPENDENTLY_VALIDATED",
                "entries": [
                    {
                        "id": "P2-SOFT-SHARED-INVARIANT-COLOCATION",
                        "version": "1.0.0",
                        "evidence_predicate": "SHARES_STATE_OR_INVARIANT",
                        "required_architecture_implication": "COLOCATE_CANDIDATE",
                        "relation": "MUST_LINK",
                        "hardness": "SOFT",
                        "weight": 1.0,
                        "quality_driver": "Candidate cohesion for responsibilities explicitly judged to share state or an invariant.",
                        "source_basis_status": "INTERNAL_EXPERIMENTAL_CASE_POLICY",
                        "assumptions": [
                            "A human reviewer has separately approved the evidence and named the responsibility pair.",
                            "The soft preference is reversible and does not establish a production boundary.",
                        ],
                        "abstention_conditions": [
                            "Evidence is UNKNOWN, SCOPED_ABSENT, unapproved, uncited, or has an unresolved implication.",
                            "The reviewer did not name distinct approved responsibility endpoints.",
                        ],
                        "rationale": (
                            "Experimental case rule: an explicitly reviewed shared-state/invariant architectural candidate "
                            "with named responsibility pairs creates a reversible soft co-location preference; business order alone never does."
                        ),
                    },
                    {
                        "id": "P2-SOFT-INDEPENDENT-CHANGE-SEPARATION",
                        "version": "1.0.0",
                        "evidence_predicate": "REQUIRES_INDEPENDENT_CHANGE",
                        "required_architecture_implication": "SEPARATE_CANDIDATE",
                        "relation": "CANNOT_LINK",
                        "hardness": "SOFT",
                        "weight": 1.0,
                        "quality_driver": "Candidate changeability for responsibility pairs explicitly judged to change independently.",
                        "source_basis_status": "INTERNAL_EXPERIMENTAL_CASE_POLICY",
                        "assumptions": [
                            "A human reviewer has separately approved the evidence and named the responsibility pair.",
                            "The soft preference is reversible and does not establish separate deployment.",
                        ],
                        "abstention_conditions": [
                            "Evidence is UNKNOWN, SCOPED_ABSENT, unapproved, uncited, or has an unresolved implication.",
                            "The reviewer did not name distinct approved responsibility endpoints.",
                        ],
                        "rationale": (
                            "Experimental case rule: an explicitly reviewed independent-change architectural candidate "
                            "with named responsibility pairs creates a reversible soft separation preference; workflow ordering alone never does."
                        ),
                    },
                ],
            },
            "relation_annotations": [],
            "responsibility_review_complete": False,
            "candidate_selection_policy": "MAXIMUM_GROUPS",
            "responsibility_provenance": "PREPARED_CASE_STUDY_TEMPLATE",
            "fixture_label": "PREPARED_CASE_STUDY",
            "fixture_note": (
                "Original Tutor Support requirements and source spans prepared for P2. Placeholder responsibilities "
                "are not model outputs and must be replaced by reviewed proposals before substantive interpretation."
            ),
        }
    )
