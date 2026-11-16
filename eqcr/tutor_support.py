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
            "constraint_policies": [
                {
                    "id": "P2-SOFT-LIFECYCLE-COHESION",
                    "evidence_predicate": "same_workflow_lifecycle",
                    "relation": "MUST_LINK",
                    "hardness": "SOFT",
                    "weight": 1.0,
                    "rationale": (
                        "For candidate generation only, a reviewer-approved lifecycle relation creates a reversible "
                        "soft co-location preference; this is not a production boundary claim."
                    ),
                }
            ],
            "candidate_selection_policy": "MAXIMUM_GROUPS",
            "responsibility_provenance": "PREPARED_CASE_STUDY_TEMPLATE",
            "fixture_label": "PREPARED_CASE_STUDY",
            "fixture_note": (
                "Original Tutor Support requirements and source spans prepared for P2. Placeholder responsibilities "
                "are not model outputs and must be replaced by reviewed proposals before substantive interpretation."
            ),
        }
    )


def apply_tutor_human_review(
    fixture: dict[str, Any],
    proposal_data: dict[str, Any],
    review: dict[str, Any],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Promote only explicitly approved/corrected, source-resolved Tutor proposals."""
    updated = deepcopy(fixture)
    if not isinstance(review, dict):
        raise ValueError("Human review input must be a JSON object.")
    raw = updated["raw_requirements"]
    if raw["case_id"] != "TUTOR-SUPPORT-P2-01":
        raise ValueError("Tutor P2 review can only be applied to TUTOR-SUPPORT-P2-01.")
    requirements = {item["id"]: item for item in raw["requirements"]}
    workflow_ids = {item["id"] for item in raw["workflows"]}
    if any(item.get("review_decision_status") == "APPROVED" for item in updated["responsibilities"]):
        raise ValueError("This Tutor case already contains human-approved responsibilities; start from its unreviewed run to avoid duplicate decisions.")
    responsibility_by_requirement = {
        item["requirement_ids"][0]: item for item in updated["responsibilities"]
    }
    proposal_by_id = {item["id"]: item for item in proposal_data.get("proposals", [])}
    responsibility_decisions = {
        item["requirement_id"]: item for item in review.get("responsibilities", [])
    }
    expected_requirement_ids = set(requirements)
    if len(review.get("responsibilities", [])) != len(responsibility_decisions) or set(responsibility_decisions) != expected_requirement_ids:
        raise ValueError("Provide exactly one human decision for every Tutor functional requirement.")
    if len(proposal_by_id) != len(proposal_data.get("proposals", [])):
        raise ValueError("Model responsibility proposal IDs are not unique; correct or reject duplicates explicitly first.")

    def _required_fields(item: dict[str, Any], decision_type: str) -> None:
        if not isinstance(item, dict) or not all(
            isinstance(item.get(key), str) and item[key].strip()
            for key in ("action", "reason", "source", "actor")
        ):
            raise ValueError(f"{decision_type} decisions require action, reason, source, and actor.")

    decisions = []
    for requirement_id in sorted(requirements):
        decision = responsibility_decisions[requirement_id]
        _required_fields(decision, "Responsibility")
        action = decision["action"].upper()
        if action not in {"APPROVE", "CORRECT"}:
            raise ValueError("Each requirement must be APPROVE or CORRECT before the optimizer can use its responsibility.")
        target = responsibility_by_requirement[requirement_id]
        selected_proposal = None
        if action == "APPROVE":
            selected_proposal = proposal_by_id.get(decision.get("proposal_id"))
            if (
                selected_proposal is None
                or selected_proposal.get("requirement_id") != requirement_id
                or not selected_proposal.get("requirement_id_valid")
                or not selected_proposal.get("source_span_resolved")
                or not selected_proposal.get("responsibility_id_valid_and_unique")
            ):
                raise ValueError(f"Cannot approve an unresolved or ambiguous proposal for {requirement_id}.")
            if selected_proposal.get("source_ref") != requirements[requirement_id]["source_ref"]:
                raise ValueError(f"Proposal citation for {requirement_id} no longer matches the prepared source span.")
            values = {key: selected_proposal[key] for key in ("name", "activity", "operation")}
            target["proposal_id"] = selected_proposal["id"]
        else:
            correction = decision.get("correction", {})
            if not all(str(correction.get(key, "")).strip() for key in ("name", "activity", "operation")):
                raise ValueError(f"A correction for {requirement_id} must supply name, activity, and operation.")
            values = {key: str(correction[key]).strip() for key in ("name", "activity", "operation")}
            target["proposal_id"] = None
        target.update(values)
        target["review_decision_status"] = "APPROVED"
        target["semantic_status"] = "REVIEW_REQUIRED"
        target["source_refs"] = [requirements[requirement_id]["source_ref"]]
        target["requirement_ids"] = [requirement_id]
        workflow_activity_ids = decision.get("workflow_activity_ids", [])
        if not isinstance(workflow_activity_ids, list) or not set(workflow_activity_ids) <= workflow_ids:
            raise ValueError(f"Human workflow mapping for {requirement_id} references an unknown workflow ID.")
        target["workflow_activity_ids"] = workflow_activity_ids
        target["workflow_mapping_status"] = "MAPPED" if workflow_activity_ids else "UNRESOLVED"
        target["workflow_note"] = "Mapped by reviewer." if workflow_activity_ids else "No reviewer workflow mapping supplied."
        decisions.append(
            {
                "decision_id": f"D{len(decisions) + 1:02d}",
                "decision_type": "HUMAN_SEMANTIC_REVIEW",
                "target_step": "02",
                "target_artifact": "responsibilities",
                "object_id": target["id"],
                "action": action,
                "old_value": selected_proposal or "LLM proposal not accepted",
                "new_value": values,
                "reason": decision["reason"],
                "source": decision["source"],
                "actor": decision["actor"],
                "result": "RECORDED_HUMAN_DECISION",
            }
        )

    evidence_proposals = proposal_data.get("evidence_proposals", [])
    evidence_decisions = {item["proposal_id"]: item for item in review.get("evidence", [])}
    expected_evidence_ids = {item["id"] for item in evidence_proposals}
    if len(review.get("evidence", [])) != len(evidence_decisions) or set(evidence_decisions) != expected_evidence_ids:
        raise ValueError("Provide one human decision for every proposed evidence relation.")
    requirement_to_responsibility = {
        requirement_id: item["id"]
        for item in updated["responsibilities"]
        for requirement_id in item["requirement_ids"]
    }
    for index, proposal in enumerate(evidence_proposals, start=1):
        decision = evidence_decisions[proposal["id"]]
        _required_fields(decision, "Evidence")
        action = decision["action"].upper()
        if action not in {"APPROVE", "CORRECT", "REJECT"}:
            raise ValueError("Evidence decisions must be APPROVE, CORRECT, or REJECT.")
        evidence_id = f"EV-LLM-P{index:02d}"
        evidence_value = None
        if action != "REJECT":
            if action == "APPROVE":
                evidence_value = proposal
                if not all(
                    proposal.get(key)
                    for key in (
                        "id_valid_and_unique",
                        "subject_requirement_id_valid",
                        "object_requirement_id_valid",
                        "source_refs_valid",
                    )
                ):
                    raise ValueError(f"Cannot approve a citation-invalid relation: {proposal['id']}.")
                subject_fr = proposal["subject_requirement_id"]
                object_fr = proposal["object_requirement_id"]
                predicate = proposal["predicate"]
                status = proposal["proposed_status"]
                source_requirement_ids = proposal["source_requirement_ids"]
                rationale = proposal["rationale"]
                provenance = "MODEL_PROPOSED"
            else:
                evidence_value = decision.get("correction", {})
                subject_fr = evidence_value.get("subject_requirement_id")
                object_fr = evidence_value.get("object_requirement_id")
                predicate = evidence_value.get("predicate")
                status = evidence_value.get("status")
                source_requirement_ids = evidence_value.get("source_requirement_ids", [])
                rationale = evidence_value.get("rationale")
                provenance = "HUMAN_OVERRIDE"
                if status not in {"PRESENT", "SCOPED_ABSENT", "UNKNOWN"}:
                    raise ValueError(f"Evidence correction {proposal['id']} has an invalid typed status.")
                if not all((subject_fr, object_fr, predicate, rationale)):
                    raise ValueError(f"Evidence correction {proposal['id']} is incomplete.")
                if not source_requirement_ids:
                    raise ValueError(f"Evidence correction {proposal['id']} must cite at least one requirement.")
            if subject_fr not in requirements or object_fr not in requirements:
                raise ValueError(f"Evidence relation {proposal['id']} references an unknown requirement.")
            if not set(source_requirement_ids) <= expected_requirement_ids:
                raise ValueError(f"Evidence relation {proposal['id']} has an unknown source requirement citation.")
            expected_refs = [requirements[item]["source_ref"] for item in source_requirement_ids]
            if action == "APPROVE" and proposal.get("source_refs") != expected_refs:
                raise ValueError(f"Evidence citation for {proposal['id']} does not match the prepared source spans.")
            if status == "PRESENT" and not source_requirement_ids:
                raise ValueError(f"PRESENT evidence {proposal['id']} must have a source citation.")
            if status == "PRESENT" and not {subject_fr, object_fr} <= set(source_requirement_ids):
                raise ValueError(f"PRESENT evidence {proposal['id']} must cite both relationship endpoints.")
            source_refs = [requirements[item]["source_ref"] for item in source_requirement_ids]
            evidence_value = {
                "id": evidence_id,
                "subject_id": requirement_to_responsibility[subject_fr],
                "predicate": predicate,
                "object_id": requirement_to_responsibility[object_fr],
                "status": status,
                "provenance": provenance,
                "review_status": "APPROVED",
                "source_refs": source_refs,
                "is_assumption": False,
                "rationale": rationale,
            }
            updated["evidence"].append(evidence_value)
        decisions.append(
            {
                "decision_id": f"D{len(decisions) + 1:02d}",
                "decision_type": "HUMAN_SEMANTIC_REVIEW",
                "target_step": "03",
                "target_artifact": "evidence",
                "object_id": evidence_id,
                "action": action,
                "old_value": proposal,
                "new_value": evidence_value,
                "reason": decision["reason"],
                "source": decision["source"],
                "actor": decision["actor"],
                "result": "RECORDED_HUMAN_DECISION",
            }
        )
    boundary_hypotheses = proposal_data.get("boundary_hypotheses", [])
    boundary_decisions = {item["proposal_id"]: item for item in review.get("boundaries", [])}
    expected_boundary_ids = {item["id"] for item in boundary_hypotheses}
    if len(review.get("boundaries", [])) != len(boundary_decisions) or set(boundary_decisions) != expected_boundary_ids:
        raise ValueError("Provide one human decision for every proposed boundary hypothesis.")
    for proposal in boundary_hypotheses:
        decision = boundary_decisions[proposal["id"]]
        _required_fields(decision, "Boundary")
        action = decision["action"].upper()
        if action not in {"APPROVE", "CORRECT", "REJECT"}:
            raise ValueError("Boundary decisions must be APPROVE, CORRECT, or REJECT.")
        if action == "APPROVE" and not all(
            proposal.get(key)
            for key in ("id_valid_and_unique", "requirement_ids_valid", "source_refs_valid")
        ):
            raise ValueError(f"Cannot approve a citation-invalid boundary hypothesis: {proposal['id']}.")
        new_value: Any = proposal
        if action == "CORRECT":
            new_value = decision.get("correction", {})
            requirement_ids = new_value.get("requirement_ids", [])
            source_requirement_ids = new_value.get("source_requirement_ids", [])
            if (
                len(requirement_ids) < 2
                or not set(requirement_ids) <= expected_requirement_ids
                or not source_requirement_ids
                or not set(source_requirement_ids) <= expected_requirement_ids
                or not str(new_value.get("boundary_rationale", "")).strip()
            ):
                raise ValueError(f"Boundary correction {proposal['id']} is incomplete or has unknown FR citations.")
        decisions.append(
            {
                "decision_id": f"D{len(decisions) + 1:02d}",
                "decision_type": "HUMAN_HYPOTHESIS_REVIEW",
                "target_step": "06",
                "target_artifact": "boundary_hypotheses",
                "object_id": proposal["id"],
                "action": action,
                "old_value": proposal,
                "new_value": new_value if action != "REJECT" else None,
                "reason": decision["reason"],
                "source": decision["source"],
                "actor": decision["actor"],
                "result": "RECORDED_HYPOTHESIS_REVIEW_ONLY",
            }
        )
    updated["responsibility_provenance"] = "LOCAL_OLLAMA_HUMAN_REVIEWED"
    updated["fixture_note"] = (
        "Tutor requirements are prepared source input; responsibility/evidence proposals came from local Ollama and "
        "were individually approved, corrected, or rejected by a recorded human reviewer."
    )
    return updated, decisions
