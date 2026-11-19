"""P2-specific review semantics for variable-cardinality responsibilities and relations."""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from typing import Any

from .models import EvidenceRecord, RelationAnnotation
from .p2_protocol import (
    MAX_OPTIMIZER_RESPONSIBILITIES,
    RELATION_PREDICATES,
    source_bundle_sha256,
    verify_blind_annotation_lock,
)


RESPONSIBILITY_ACTIONS = {"APPROVE", "CORRECT", "REJECT", "DEFER"}
RELATION_ACTIONS = {"APPROVE", "CORRECT", "REJECT", "DEFER"}


def _required_fields(item: dict[str, Any], decision_type: str) -> None:
    if not isinstance(item, dict) or not all(
        isinstance(item.get(key), str) and item[key].strip()
        for key in ("action", "reason", "source", "actor")
    ):
        raise ValueError(f"{decision_type} decisions require action, reason, source, and actor.")


def _apply_tutor_review(
    fixture: dict[str, Any],
    proposal_data: dict[str, Any],
    review: dict[str, Any],
    *,
    mode: str,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Record human dispositions after the mode-specific research/demo gate."""
    updated = deepcopy(fixture)
    if not isinstance(review, dict):
        raise ValueError("Human review input must be a JSON object.")
    raw = updated["raw_requirements"]
    if raw["case_id"] != "TUTOR-SUPPORT-P2-01":
        raise ValueError("Tutor review can only be applied to TUTOR-SUPPORT-P2-01.")
    blind_bundle = proposal_data.get("blind_annotation_lock")
    demo_actor = ""
    if mode == "EXPLORATORY_UNBLINDED_DEMO":
        if (
            proposal_data.get("execution_mode") != mode
            or proposal_data.get("research_eligibility") != "EXCLUDED_FROM_BLIND_RESEARCH"
            or blind_bundle is not None
        ):
            raise ValueError("Unblinded demo review requires an explicitly unblinded proposal bundle without a research lock.")
        if review.get("demo_unblinded_acknowledged") is not True:
            raise ValueError("Demo review requires an explicit acknowledgement that outputs are unblinded and not gold labels.")
        demo_actor = review.get("demo_actor", "")
        if not isinstance(demo_actor, str) or not demo_actor.strip():
            raise ValueError("Demo review requires the actual demo stakeholder identifier.")
    elif mode == "P2_BLIND_RESEARCH":
        if not verify_blind_annotation_lock(raw, blind_bundle):
            raise ValueError("The source-only annotation lock is missing, changed, or bound to different sources.")
    else:
        raise ValueError("Unknown Tutor review mode.")
    if proposal_data.get("input_sha256") != source_bundle_sha256(raw):
        raise ValueError("The model proposal bundle is not bound to this exact frozen source package.")
    try:
        inference_started = datetime.fromisoformat(proposal_data["inference_started_at_utc"].replace("Z", "+00:00"))
        inference_completed = datetime.fromisoformat(proposal_data["inference_completed_at_utc"].replace("Z", "+00:00"))
    except (KeyError, TypeError, ValueError, AttributeError) as exc:
        raise ValueError("Proposal bundle must record a valid timezone-aware local inference interval.") from exc
    if any(value.tzinfo is None for value in (inference_started, inference_completed)):
        raise ValueError("Inference timestamps must include a timezone.")
    if inference_started > inference_completed:
        raise ValueError("The local inference interval is invalid.")
    if mode == "P2_BLIND_RESEARCH":
        try:
            locked_at = datetime.fromisoformat(blind_bundle["lock"]["locked_at"].replace("Z", "+00:00"))
        except (KeyError, TypeError, ValueError, AttributeError) as exc:
            raise ValueError("Proposal bundle must record a valid blind-lock timestamp.") from exc
        if locked_at.tzinfo is None:
            raise ValueError("Blind-lock timestamp must include a timezone.")
        if locked_at > inference_started:
            raise ValueError("The source-only annotation must be locked before local inference starts.")

    requirements = {item["id"]: item for item in raw["requirements"]}
    workflows = {item["id"]: item for item in raw["workflows"]}
    requirement_ids = set(requirements)
    workflow_ids = set(workflows)
    test_only_proposals = proposal_data.get("provenance") == "TEST_ONLY_NOT_MODEL_OUTPUT"
    proposals = proposal_data.get("proposals", [])
    proposal_by_id = {item["id"]: item for item in proposals}
    if len(proposal_by_id) != len(proposals):
        raise ValueError("Model responsibility proposal IDs must be unique before review.")
    model_proposal_ids = [item.get("model_proposal_id") for item in proposals]
    if any(not isinstance(item, str) or not item.strip() for item in model_proposal_ids) or len(model_proposal_ids) != len(set(model_proposal_ids)):
        raise ValueError("Model responsibility proposal labels must be present and unique.")
    proposal_shapes = [
        (
            tuple(sorted(item.get("requirement_ids", []))),
            str(item.get("name", "")).strip().casefold(),
            str(item.get("activity", "")).strip().casefold(),
            str(item.get("operation", "")).strip().casefold(),
        )
        for item in proposals
    ]
    proposal_shape_counts = {shape: proposal_shapes.count(shape) for shape in set(proposal_shapes)}

    def exact_fr_source_refs(requirement_ids: list[str], refs: Any) -> bool:
        if not isinstance(requirement_ids, list) or not requirement_ids or len(requirement_ids) != len(set(requirement_ids)):
            return False
        if not set(requirement_ids) <= set(requirements):
            return False
        return refs == [requirements[item]["source_ref"] for item in requirement_ids]

    if mode == "EXPLORATORY_UNBLINDED_DEMO":
        decisions: list[dict[str, Any]] = [
            {
                "decision_id": "D00",
                "decision_type": "UNBLINDED_DEMO_ACKNOWLEDGEMENT",
                "target_step": "09",
                "target_artifact": "demo_research_eligibility",
                "object_id": proposal_data.get("run_id", proposal_data["input_sha256"]),
                "action": "ACKNOWLEDGED",
                "old_value": None,
                "new_value": {
                    "execution_mode": mode,
                    "research_eligibility": "EXCLUDED_FROM_BLIND_RESEARCH",
                    "input_sha256": proposal_data["input_sha256"],
                },
                "reason": "Demo stakeholder acknowledged that this exposure is unblinded and cannot create gold labels.",
                "source": "EXPLORATORY_DEMO_UI_ACKNOWLEDGEMENT",
                "actor": demo_actor.strip(),
                "actor_role": "DEMO_STAKEHOLDER",
                "created_at_utc": datetime.now(timezone.utc).isoformat(),
                "research_eligibility": "EXCLUDED_FROM_BLIND_RESEARCH",
                "result": "ACKNOWLEDGED_NOT_A_SEMANTIC_LABEL",
            }
        ]
    else:
        decisions = [
            {
            "decision_id": "D00",
            "decision_type": "BLIND_ANNOTATION_CHECKPOINT",
            "target_step": "02",
            "target_artifact": "independent_annotation",
            "object_id": blind_bundle["lock"]["annotation_sha256"],
            "action": "LOCKED",
            "old_value": None,
            "new_value": {
                "source_bundle_sha256": blind_bundle["lock"]["source_bundle_sha256"],
                "annotation_sha256": blind_bundle["lock"]["annotation_sha256"],
                "locked_at": blind_bundle["lock"]["locked_at"],
                "reviewer_id": blind_bundle["lock"]["reviewer_id"],
                "identity_status": blind_bundle["lock"]["identity_status"],
            },
            "reason": "Source-only annotation was hash-locked before this model proposal review.",
            "source": "P2-BLIND-ANNOTATION",
            "actor": blind_bundle["lock"]["reviewer_id"],
            "result": "CHECKPOINT_RECORDED_NOT_IDENTITY_VERIFIED",
            }
        ]

    responsibility_decisions = {item["proposal_id"]: item for item in review.get("responsibilities", [])}
    if len(responsibility_decisions) != len(review.get("responsibilities", [])):
        raise ValueError("Responsibility decisions cannot repeat proposal IDs.")
    if set(responsibility_decisions) != set(proposal_by_id):
        raise ValueError("Provide one explicit APPROVE/CORRECT/REJECT/DEFER disposition per model responsibility proposal.")

    reviewed_responsibilities: list[dict[str, Any]] = []

    def add_responsibility(
        values: dict[str, Any],
        *,
        provenance: str,
        proposal_id: str | None,
    ) -> dict[str, Any]:
        required = ("name", "activity", "operation")
        if not all(isinstance(values.get(key), str) and values[key].strip() for key in required):
            raise ValueError("Each accepted or corrected responsibility needs name, activity, and operation.")
        cited_requirement_ids = values.get("requirement_ids", [])
        if (
            not isinstance(cited_requirement_ids, list)
            or not cited_requirement_ids
            or len(cited_requirement_ids) != len(set(cited_requirement_ids))
            or not set(cited_requirement_ids) <= requirement_ids
        ):
            raise ValueError("Each responsibility must cite one or more known FR IDs exactly once.")
        activity_ids = values.get("workflow_activity_ids", [])
        if not isinstance(activity_ids, list) or not set(activity_ids) <= workflow_ids:
            raise ValueError("Responsibility workflow mapping contains an unknown workflow ID.")
        refs = [requirements[item]["source_ref"] for item in cited_requirement_ids]
        role = {
            "id": f"R{len(reviewed_responsibilities) + 1}",
            "proposal_id": proposal_id,
            "provenance": provenance,
            "name": values["name"].strip(),
            "activity": values["activity"].strip(),
            "operation": values["operation"].strip(),
            "decomposition_rationale": values.get("decomposition_rationale", "") or "Recorded from a reviewer decision; no model rationale is assumed.",
            "requirement_ids": cited_requirement_ids,
            "source_refs": refs,
            "workflow_activity_ids": activity_ids,
            "workflow_mapping_status": "MAPPED" if activity_ids else "UNRESOLVED",
            "workflow_note": "Workflow mapping was explicitly recorded by the reviewer." if activity_ids else "No workflow mapping was supplied.",
            "review_decision_status": "APPROVED",
            "semantic_status": "REVIEW_REQUIRED",
        }
        reviewed_responsibilities.append(role)
        return role

    for proposal_index, proposal in enumerate(proposals):
        decision = responsibility_decisions[proposal["id"]]
        _required_fields(decision, "Responsibility")
        action = decision["action"].upper()
        if action not in RESPONSIBILITY_ACTIONS:
            raise ValueError("Responsibility decisions must be APPROVE, CORRECT, REJECT, or DEFER.")
        produced = []
        if action == "APPROVE":
            exact_citations = exact_fr_source_refs(
                proposal.get("requirement_ids", []), proposal.get("source_refs")
            )
            if not exact_citations or proposal_shape_counts[proposal_shapes[proposal_index]] > 1:
                raise ValueError(f"Cannot approve unresolved, duplicate, or citation-invalid proposal {proposal['id']}.")
            produced.append(
                add_responsibility(
                    proposal,
                    provenance=(
                        "P2_TEST_ONLY"
                        if test_only_proposals
                        else "LOCAL_OLLAMA_PROPOSAL_UNBLINDED"
                        if mode == "EXPLORATORY_UNBLINDED_DEMO"
                        else "LOCAL_OLLAMA_PROPOSAL"
                    ),
                    proposal_id=proposal["id"],
                )
            )
        elif action == "CORRECT":
            corrections = decision.get("correction", {}).get("responsibilities", [])
            if not isinstance(corrections, list) or not corrections:
                raise ValueError("CORRECT needs one or more corrected responsibility objects; use REJECT or DEFER for zero.")
            for correction in corrections:
                correction = {**correction, "decomposition_rationale": correction.get("decomposition_rationale") or decision["reason"]}
                produced.append(
                    add_responsibility(
                        correction,
                        provenance="HUMAN_CORRECTION",
                        proposal_id=None,
                    )
                )
        decisions.append(
            {
                "decision_id": f"D{len(decisions):02d}",
                "decision_type": "HUMAN_RESPONSIBILITY_REVIEW",
                "target_step": "02",
                "target_artifact": "responsibilities",
                "object_id": proposal["id"],
                "action": action,
                "old_value": proposal,
                "new_value": produced if action in {"APPROVE", "CORRECT"} else None,
                "reason": decision["reason"],
                "source": decision["source"],
                "actor": decision["actor"],
                "result": "RECORDED_HUMAN_DECISION",
            }
        )

    for addition in review.get("additional_responsibilities", []):
        _required_fields(addition, "Additional responsibility")
        if addition["action"].upper() != "ADD":
            raise ValueError("Additional responsibility rows must use action ADD.")
        addition = {**addition, "decomposition_rationale": addition.get("decomposition_rationale") or addition["reason"]}
        produced = add_responsibility(
            addition,
            provenance="HUMAN_ADDITION",
            proposal_id=None,
        )
        decisions.append(
            {
                "decision_id": f"D{len(decisions):02d}",
                "decision_type": "HUMAN_RESPONSIBILITY_ADDITION",
                "target_step": "02",
                "target_artifact": "responsibilities",
                "object_id": produced["id"],
                "action": "ADD",
                "old_value": None,
                "new_value": produced,
                "reason": addition["reason"],
                "source": addition["source"],
                "actor": addition["actor"],
                "result": "RECORDED_HUMAN_DECISION",
            }
        )
    if len(reviewed_responsibilities) > MAX_OPTIMIZER_RESPONSIBILITIES:
        raise ValueError(
            f"Reviewed result has {len(reviewed_responsibilities)} responsibilities; the exact partitioner supports at most {MAX_OPTIMIZER_RESPONSIBILITIES}."
        )

    relation_decisions = {item["proposal_id"]: item for item in review.get("evidence", [])}
    evidence_proposals = proposal_data.get("evidence_proposals", [])
    evidence_by_id = {item["id"]: item for item in evidence_proposals}
    if len(relation_decisions) != len(review.get("evidence", [])) or set(relation_decisions) != set(evidence_by_id):
        raise ValueError("Provide one APPROVE/CORRECT/REJECT/DEFER disposition per model relation proposal.")
    relation_model_ids = [item.get("model_proposal_id") for item in evidence_proposals]
    if any(not isinstance(item, str) or not item.strip() for item in relation_model_ids) or len(relation_model_ids) != len(set(relation_model_ids)):
        raise ValueError("Model relation proposal labels must be present and unique.")
    relation_keys = []
    for proposal in evidence_proposals:
        predicate = str(proposal.get("predicate", "")).strip().upper()
        subject_fr = proposal.get("subject_requirement_id")
        object_fr = proposal.get("object_requirement_id")
        if predicate in {"SHARES_STATE_OR_INVARIANT", "REQUIRES_INDEPENDENT_CHANGE"} and subject_fr and object_fr and subject_fr > object_fr:
            subject_fr, object_fr = object_fr, subject_fr
        relation_keys.append((subject_fr, predicate, object_fr))
    relation_counts = {key: relation_keys.count(key) for key in set(relation_keys)}
    relation_statuses = {
        key: {
            item.get("proposed_status")
            for item, item_key in zip(evidence_proposals, relation_keys)
            if item_key == key
        }
        for key in set(relation_keys)
    }
    responsibility_by_id = {item["id"]: item for item in reviewed_responsibilities}
    relation_annotations: list[dict[str, Any]] = []
    derived_evidence: list[dict[str, Any]] = []

    def relation_refs(source_fr_ids: list[str], source_wf_ids: list[str]) -> list[dict[str, Any]]:
        if (
            not isinstance(source_fr_ids, list)
            or not isinstance(source_wf_ids, list)
            or len(source_fr_ids) != len(set(source_fr_ids))
            or len(source_wf_ids) != len(set(source_wf_ids))
        ):
            raise ValueError("Relation citations must be unique source ID lists.")
        if not set(source_fr_ids) <= requirement_ids or not set(source_wf_ids) <= workflow_ids:
            raise ValueError("Relation citation references an unknown FR or workflow ID.")
        return [requirements[item]["source_ref"] for item in source_fr_ids] + [workflows[item]["source_ref"] for item in source_wf_ids]

    for proposal_index, proposal in enumerate(evidence_proposals):
        decision = relation_decisions[proposal["id"]]
        _required_fields(decision, "Relation")
        action = decision["action"].upper()
        if action not in RELATION_ACTIONS:
            raise ValueError("Relation decisions must be APPROVE, CORRECT, REJECT, or DEFER.")
        relation_value = None
        if action in {"APPROVE", "CORRECT"}:
            if action == "APPROVE":
                source_fr_ids = proposal.get("source_requirement_ids", [])
                try:
                    exact_relation_refs = relation_refs(source_fr_ids, proposal.get("source_workflow_ids", []))
                except (TypeError, ValueError, KeyError):
                    exact_relation_refs = None
                if (
                    proposal.get("subject_requirement_id") not in requirement_ids
                    or proposal.get("object_requirement_id") not in requirement_ids
                    or exact_relation_refs is None
                    or proposal.get("source_refs") != exact_relation_refs
                ):
                    raise ValueError(f"Cannot approve citation-invalid relation {proposal['id']}.")
                relation_key = relation_keys[proposal_index]
                if relation_counts[relation_key] > 1 or len(relation_statuses[relation_key]) > 1:
                    raise ValueError(f"Cannot approve duplicate or status-conflicting relation {proposal['id']} without correction.")
                if proposal.get("proposed_status") == "PRESENT" and not {
                    proposal.get("subject_requirement_id"), proposal.get("object_requirement_id")
                } <= set(proposal.get("source_requirement_ids", [])):
                    raise ValueError(f"PRESENT relation {proposal['id']} must cite both FR endpoints.")
                correction = {
                    "subject_requirement_id": proposal["subject_requirement_id"],
                    "predicate": proposal["predicate"],
                    "object_requirement_id": proposal["object_requirement_id"],
                    "status": proposal["proposed_status"],
                    "source_requirement_ids": proposal["source_requirement_ids"],
                    "source_workflow_ids": [],
                    "rationale": proposal["rationale"],
                }
                provenance = (
                    "P2_TEST_ONLY"
                    if test_only_proposals
                    else "LOCAL_OLLAMA_UNBLINDED_DEMO"
                    if mode == "EXPLORATORY_UNBLINDED_DEMO"
                    else "LOCAL_OLLAMA_REVIEWED"
                )
            else:
                correction = decision.get("correction", {})
                provenance = "HUMAN_OVERRIDE"
            subject_fr = correction.get("subject_requirement_id")
            object_fr = correction.get("object_requirement_id")
            predicate = correction.get("predicate")
            status = correction.get("status")
            source_fr_ids = correction.get("source_requirement_ids", [])
            source_wf_ids = correction.get("source_workflow_ids", [])
            rationale = correction.get("rationale", "")
            if subject_fr not in requirement_ids or object_fr not in requirement_ids or subject_fr == object_fr:
                raise ValueError(f"Relation {proposal['id']} needs two distinct, known requirement endpoints.")
            if predicate not in RELATION_PREDICATES:
                raise ValueError(f"Relation {proposal['id']} uses a predicate outside the P2 registry; correct, reject, or defer it.")
            if status not in {"PRESENT", "UNKNOWN", "SCOPED_ABSENT"}:
                raise ValueError(f"Relation {proposal['id']} has an invalid typed status.")
            if not isinstance(rationale, str) or not rationale.strip():
                raise ValueError(f"Relation {proposal['id']} needs a semantic rationale for every status.")
            if status == "PRESENT" and not {subject_fr, object_fr} <= set(source_fr_ids):
                raise ValueError(f"PRESENT relation {proposal['id']} must cite both endpoint requirements.")
            refs = relation_refs(source_fr_ids, source_wf_ids)
            if status in {"PRESENT", "SCOPED_ABSENT"} and (not refs or not rationale.strip()):
                raise ValueError(f"{status} relation {proposal['id']} needs source citations and rationale.")
            direction = "DIRECTED" if predicate == "BUSINESS_PRECEDES" else "UNDIRECTED"
            swapped_endpoints = False
            if direction == "UNDIRECTED" and subject_fr > object_fr:
                subject_fr, object_fr = object_fr, subject_fr
                swapped_endpoints = True
            implication = decision.get(
                "architecture_implication",
                correction.get("architecture_implication", "UNRESOLVED"),
            )
            architecture_rationale = decision.get(
                "architecture_rationale",
                correction.get("architecture_rationale", ""),
            )
            pair_values = decision.get("responsibility_pairs", correction.get("responsibility_pairs", []))
            pairs = []
            for pair in pair_values:
                if isinstance(pair, dict):
                    left, right = pair.get("left_responsibility_id"), pair.get("right_responsibility_id")
                elif isinstance(pair, (list, tuple)) and len(pair) == 2:
                    left, right = pair
                else:
                    raise ValueError("Responsibility pairs must be [left_R_id, right_R_id] entries.")
                if swapped_endpoints:
                    left, right = right, left
                if left not in responsibility_by_id or right not in responsibility_by_id or left == right:
                    raise ValueError("Architecture candidate pairs must reference two distinct reviewed responsibilities.")
                if subject_fr not in responsibility_by_id[left]["requirement_ids"] or object_fr not in responsibility_by_id[right]["requirement_ids"]:
                    raise ValueError("Named responsibility pairs must correspond to the relation's FR endpoints.")
                pairs.append((left, right))
            if len(pairs) != len(set(pairs)):
                raise ValueError("Architecture candidate responsibility pairs cannot be duplicated.")
            relation_value = RelationAnnotation.model_validate(
                {
                    "id": f"REL-{proposal['id']}",
                    "subject_requirement_id": subject_fr,
                    "predicate": predicate,
                    "object_requirement_id": object_fr,
                    "direction": direction,
                    "status": status,
                    "review_status": "APPROVED",
                    "provenance": provenance,
                    "source_requirement_ids": source_fr_ids,
                    "source_workflow_ids": source_wf_ids,
                    "source_refs": refs,
                    "rationale": rationale,
                    "architecture_implication": implication,
                    "architecture_rationale": architecture_rationale,
                    "responsibility_pairs": pairs,
                    "proposal_id": proposal["id"],
                }
            ).model_dump(mode="json")
            relation_annotations.append(relation_value)
            relation_key = (
                relation_value["subject_requirement_id"],
                relation_value["predicate"],
                relation_value["object_requirement_id"],
            )
            if relation_value["direction"] == "UNDIRECTED" and relation_key[0] > relation_key[2]:
                relation_key = (relation_key[2], relation_key[1], relation_key[0])
            if sum(
                1
                for existing in relation_annotations[:-1]
                if (
                    existing["subject_requirement_id"],
                    existing["predicate"],
                    existing["object_requirement_id"],
                ) == relation_key
            ):
                raise ValueError("Human-reviewed relation annotations cannot duplicate the same predicate and endpoint pair.")
            if implication in {"COLOCATE_CANDIDATE", "SEPARATE_CANDIDATE"}:
                for pair_index, (left, right) in enumerate(pairs, start=1):
                    derived_evidence.append(
                        EvidenceRecord(
                            id=f"EV-{proposal['id']}-PAIR-{pair_index:02d}",
                            subject_id=left,
                            predicate=predicate,
                            object_id=right,
                            status="PRESENT",
                            provenance=(
                                "P2_TEST_ONLY"
                                if provenance == "P2_TEST_ONLY"
                                else "MODEL_PROPOSED_UNBLINDED_DEMO"
                                if provenance == "LOCAL_OLLAMA_UNBLINDED_DEMO"
                                else "MODEL_PROPOSED"
                                if provenance == "LOCAL_OLLAMA_REVIEWED"
                                else "HUMAN_OVERRIDE"
                            ),
                            review_status="APPROVED",
                            source_refs=refs,
                            is_assumption=False,
                            rationale=f"{rationale} Architecture candidate: {architecture_rationale}",
                            relation_annotation_id=relation_value["id"],
                            subject_requirement_id=subject_fr,
                            object_requirement_id=object_fr,
                            architecture_implication=implication,
                        ).model_dump(mode="json")
                    )

        decisions.append(
            {
                "decision_id": f"D{len(decisions):02d}",
                "decision_type": "HUMAN_RELATION_REVIEW",
                "target_step": "03",
                "target_artifact": "relation_registry",
                "object_id": f"REL-{proposal['id']}",
                "action": action,
                "old_value": proposal,
                "new_value": relation_value,
                "reason": decision["reason"],
                "source": decision["source"],
                "actor": decision["actor"],
                "result": "RECORDED_HUMAN_RELATION_DECISION",
            }
        )

    boundary_decisions = {item["proposal_id"]: item for item in review.get("boundaries", [])}
    boundary_proposals = proposal_data.get("boundary_hypotheses", [])
    boundary_by_id = {item["id"]: item for item in boundary_proposals}
    boundary_shapes = [tuple(sorted(item.get("requirement_ids", []))) for item in boundary_proposals]
    boundary_shape_counts = {shape: boundary_shapes.count(shape) for shape in set(boundary_shapes)}
    duplicate_boundary_shapes = {shape for shape, count in boundary_shape_counts.items() if count > 1}
    if len(boundary_decisions) != len(review.get("boundaries", [])) or set(boundary_decisions) != set(boundary_by_id):
        raise ValueError("Provide one APPROVE/CORRECT/REJECT/DEFER disposition per boundary hypothesis.")
    for boundary_index, proposal in enumerate(boundary_proposals):
        decision = boundary_decisions[proposal["id"]]
        _required_fields(decision, "Boundary")
        action = decision["action"].upper()
        if action not in RELATION_ACTIONS:
            raise ValueError("Boundary decisions must be APPROVE, CORRECT, REJECT, or DEFER.")
        if action == "APPROVE":
            cited = proposal.get("requirement_ids", [])
            sources = proposal.get("source_requirement_ids", [])
            exact_refs = exact_fr_source_refs(sources, proposal.get("source_refs")) if sources else False
            if (
                len(cited) < 2
                or len(cited) != len(set(cited))
                or not set(cited) <= requirement_ids
                or len(sources) != len(set(sources))
                or not set(cited) <= set(sources)
                or not exact_refs
                or boundary_shapes[boundary_index] in duplicate_boundary_shapes
            ):
                raise ValueError(f"Cannot approve duplicate, citation-invalid, or source-incomplete boundary hypothesis {proposal['id']}.")
        new_value = None
        if action == "CORRECT":
            new_value = decision.get("correction", {})
            cited = new_value.get("requirement_ids", [])
            sources = new_value.get("source_requirement_ids", [])
            if (
                len(cited) < 2
                or not set(cited) <= requirement_ids
                or not set(sources) <= requirement_ids
                or not set(cited) <= set(sources)
                or not str(new_value.get("boundary_rationale", "")).strip()
            ):
                raise ValueError(f"Boundary correction {proposal['id']} needs multiple known FRs and a cited rationale.")
        decisions.append(
            {
                "decision_id": f"D{len(decisions):02d}",
                "decision_type": "HUMAN_HYPOTHESIS_REVIEW",
                "target_step": "06",
                "target_artifact": "boundary_hypotheses",
                "object_id": proposal["id"],
                "action": action,
                "old_value": proposal,
                "new_value": new_value if action == "CORRECT" else proposal if action == "APPROVE" else None,
                "reason": decision["reason"],
                "source": decision["source"],
                "actor": decision["actor"],
                "result": "RECORDED_HYPOTHESIS_REVIEW_ONLY",
            }
        )

    updated["responsibilities"] = reviewed_responsibilities
    updated["evidence"] = [
        item for item in updated["evidence"] if item.get("predicate") == "independent_deployment_evidence"
    ] + derived_evidence
    updated["relation_annotations"] = relation_annotations
    updated["unresolved_requirement_ids"] = sorted(
        requirement_ids - {fr for item in reviewed_responsibilities for fr in item["requirement_ids"]}
    )
    updated["responsibility_review_complete"] = True
    updated["independent_annotation_lock"] = deepcopy(blind_bundle) if mode == "P2_BLIND_RESEARCH" else None
    updated["research_eligibility"] = (
        "EXCLUDED_FROM_BLIND_RESEARCH"
        if mode == "EXPLORATORY_UNBLINDED_DEMO"
        else "P2_BLIND_RESEARCH_PENDING_ADJUDICATED_REFERENCE"
    )
    updated["responsibility_provenance"] = (
        "P2_TEST_ONLY"
        if test_only_proposals
        else "LOCAL_OLLAMA_PROPOSAL_UNBLINDED"
        if mode == "EXPLORATORY_UNBLINDED_DEMO"
        else "LOCAL_OLLAMA_HUMAN_REVIEWED"
    )
    if mode == "EXPLORATORY_UNBLINDED_DEMO":
        for decision in decisions:
            decision.setdefault("actor_role", "DEMO_STAKEHOLDER")
            decision.setdefault("created_at_utc", datetime.now(timezone.utc).isoformat())
            decision["research_eligibility"] = "EXCLUDED_FROM_BLIND_RESEARCH"
            decision["demo_run_id"] = proposal_data.get("run_id")
        updated["fixture_note"] = (
            "Exploratory unblinded Tutor demo. Local model outputs and stakeholder decisions are excluded from blind "
            "research labels; only reviewed roles/evidence enter this deterministic candidate pipeline."
        )
    else:
        updated["fixture_note"] = (
            "Tutor Support source package was frozen; a source-only annotation was hash-locked before model review. "
            "Responsibility cardinality is variable, and only explicitly accepted/corrected roles enter optimization. "
            "Business ordering is recorded separately from architectural candidate constraints."
        )
    return updated, decisions


def apply_tutor_human_review(
    fixture: dict[str, Any], proposal_data: dict[str, Any], review: dict[str, Any]
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Review the Tutor blind-research proposal path; a valid lock remains mandatory."""
    return _apply_tutor_review(fixture, proposal_data, review, mode="P2_BLIND_RESEARCH")


def apply_tutor_demo_review(
    fixture: dict[str, Any], proposal_data: dict[str, Any], review: dict[str, Any]
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Review an explicitly unblinded demo; it can never be research-eligible."""
    return _apply_tutor_review(fixture, proposal_data, review, mode="EXPLORATORY_UNBLINDED_DEMO")
