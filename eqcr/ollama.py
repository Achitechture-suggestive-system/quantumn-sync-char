"""Optional local Ollama proposal client. Output remains untrusted and review-required."""

from __future__ import annotations

import json
import os
import hashlib
from copy import deepcopy
from datetime import datetime, timezone
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .models import LLMProposalBundle
from .p2_protocol import RELATION_PREDICATES, verify_blind_annotation_lock


DEFAULT_HOST = "http://127.0.0.1:11434"
PROMPT_VERSION = "requirements-context-multiresponsibility-relation-boundary-v7"
GENERATION_PARAMETERS = {"temperature": 0}


class OllamaError(RuntimeError):
    pass


def _host() -> str:
    value = os.environ.get("OLLAMA_HOST", DEFAULT_HOST).strip().rstrip("/")
    if not value.startswith(("http://", "https://")):
        value = f"http://{value}"
    return value


def _request(path: str, *, payload: dict[str, Any] | None = None, timeout: int = 12) -> dict[str, Any]:
    url = f"{_host()}{path}"
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    request = Request(url, data=data, headers={"Content-Type": "application/json"})
    try:
        with urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:500]
        raise OllamaError(f"Ollama returned HTTP {exc.code}: {detail}") from exc
    except (URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise OllamaError(f"Could not reach a local Ollama service at {_host()}: {exc}") from exc


def list_models() -> list[str]:
    return sorted(item["name"] for item in list_model_details() if item.get("name"))


def list_model_details() -> list[dict[str, Any]]:
    """Return non-secret local model metadata, including the model digest when supplied."""
    response = _request("/api/tags")
    fields = ("name", "digest", "size", "modified_at", "details")
    return [
        {key: item.get(key) for key in fields if key in item}
        for item in response.get("models", [])
        if item.get("name")
    ]


def get_ollama_version() -> str:
    """Read the local Ollama API version for a reproducibility manifest."""
    response = _request("/api/version")
    version = response.get("version")
    if not isinstance(version, str) or not version.strip():
        raise OllamaError("Local Ollama did not return a version string from /api/version.")
    return version.strip()


def propose_responsibilities(
    raw: dict[str, Any],
    model: str,
    *,
    blind_annotation_lock: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if raw.get("case_id") == "TUTOR-SUPPORT-P2-01":
        if not verify_blind_annotation_lock(raw, blind_annotation_lock):
            raise OllamaError("Tutor Support model proposals stay hidden until a source-only annotation is locked and verified.")
    requirement_source_refs = {
        item["id"]: item["source_ref"] for item in raw["requirements"]
    }
    source_texts = {
        item["source_ref"]["source_id"]: item["text"] for item in raw["requirements"]
    }
    requirement_source_texts = {item["id"]: item["text"] for item in raw["requirements"]}
    additional_context = {
        "context_id": raw["context_id"],
        "context_description": raw["context_description"],
        "workflows": [{"id": item["id"], "text": item["text"]} for item in raw["workflows"]],
        "quality_scenarios": [
            {
                "id": item["id"],
                "name": item["name"],
                "stimulus": item["stimulus"],
                "response_measure": item["response_measure"],
                "target": item["target"],
                "source_quote": item["source_ref"]["quote"],
            }
            for item in raw["scenarios"]
        ],
    }
    output_schema = LLMProposalBundle.model_json_schema()
    prompt = (
        "Analyze this mini-case. Return JSON only with fields: "
        "context_summary (string), normalized_requirements (array of objects with id and normalized_text), "
        "proposals (array of 0..8 objects with id, name, activity, operation, requirement_ids, decomposition_rationale), "
        "evidence_proposals (array of objects with id, subject_requirement_id, predicate, object_requirement_id, "
        "proposed_status, source_requirement_ids, rationale), and boundary_hypotheses (array of objects with id, "
        "requirement_ids, boundary_rationale, source_requirement_ids). "
        "Do not assume one requirement equals one responsibility. Return zero, one, or multiple distinct responsibilities "
        "per requirement when supported; one responsibility may cite multiple FR IDs. The total proposal count is capped at "
        "8 for the exact partition enumerator. An FR with no supported responsibility may have zero proposals. Every proposal "
        "must cite one or more requirement_ids and include a decomposition_rationale explaining its granularity. Give each "
        "proposal a unique proposal label; the application assigns R IDs only after review. Use the additional context to write "
        "a descriptive context summary. Keep normalized requirements and responsibilities grounded in their FR text. "
        "Cite requirements using FR IDs only: "
        "normalized_requirements.id is the cited FR ID, proposals.requirement_ids is the set of cited FR IDs, and evidence or "
        "boundary source_requirement_ids must list cited FR IDs. Do not output source_id fields or workflow/scenario IDs. "
        "The application resolves each FR citation to the exact source ID and input span; do not generate or quote source "
        "text. Use only FR IDs from the REQUIREMENT MAP below for evidence and boundary claims. Propose one or more typed evidence relations using requirement IDs; "
        "proposed_status must be PRESENT only when the cited text supports the relation, SCOPED_ABSENT only when the "
        "provided text explicitly defines a scope where the relation is absent, and UNKNOWN otherwise. Every evidence "
        "proposal must cite one or more source_requirement_ids. Propose one or more tentative responsibility-boundary hypotheses "
        "using requirement IDs; these are hypotheses, not partitions or deployment claims. Cite source_requirement_ids "
        "for every boundary hypothesis. Do not infer runtime topology, ownership, deployment, or business policies. "
        "The relation registry predicates are BUSINESS_PRECEDES (directed), SHARES_STATE_OR_INVARIANT (undirected), and "
        "REQUIRES_INDEPENDENT_CHANGE (undirected). Workflow ordering or triggering is a business relation and never "
        "implies co-location, separation, Sync, or Async. Architectural implications are separate human decisions. "
        "All outputs are untrusted proposals and require human semantic review.\nREQUIRED JSON SCHEMA:\n"
        + json.dumps(output_schema, ensure_ascii=False)
        + "\nREQUIREMENT MAP (FR citation ID => exact input text):\n"
        + json.dumps(requirement_source_texts, ensure_ascii=False)
        + "\nADDITIONAL CONTEXT FOR SUMMARY ONLY (workflow and quality scenarios; these do not provide citation IDs for claims):\n"
        + json.dumps(additional_context, ensure_ascii=False)
    )
    input_sha256 = hashlib.sha256(
        json.dumps(raw, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    inference_started_at_utc = datetime.now(timezone.utc).isoformat()
    response = _request(
        "/api/chat",
        payload={
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "format": output_schema,
            "stream": False,
            "options": GENERATION_PARAMETERS,
        },
        timeout=180,
    )
    content = response.get("message", {}).get("content", "")
    try:
        parsed = LLMProposalBundle.model_validate_json(content)
    except Exception as exc:
        raise OllamaError(f"Model output did not match the proposal schema: {exc}") from exc
    checks = []
    proposal_requirement_counts: dict[str, int] = {}
    for proposal in parsed.proposals:
        for requirement_id in proposal.requirement_ids:
            proposal_requirement_counts[requirement_id] = proposal_requirement_counts.get(requirement_id, 0) + 1
    used_proposal_ids: set[str] = set()
    proposal_shapes = [
        (
            tuple(sorted(proposal.requirement_ids)),
            proposal.name.strip().casefold(),
            proposal.activity.strip().casefold(),
            proposal.operation.strip().casefold(),
        )
        for proposal in parsed.proposals
    ]
    proposal_shape_counts = {shape: proposal_shapes.count(shape) for shape in set(proposal_shapes)}
    for index, proposal in enumerate(parsed.proposals, start=1):
        model_proposal_id = proposal.id
        id_valid = bool(proposal.id.strip()) and proposal.id not in used_proposal_ids
        used_proposal_ids.add(proposal.id)
        proposal_shape = proposal_shapes[index - 1]
        duplicate_proposal = proposal_shape_counts[proposal_shape] > 1
        requirement_ids_valid = bool(proposal.requirement_ids) and set(proposal.requirement_ids) <= set(requirement_source_refs)
        resolved_refs = []
        for requirement_id in proposal.requirement_ids:
            source_ref = requirement_source_refs.get(requirement_id)
            source_id = source_ref["source_id"] if source_ref else None
            exact_source = source_texts.get(source_id) if source_id else None
            if exact_source is not None and source_ref is not None:
                resolved_refs.append({
                    "source_id": source_id,
                    "quote": exact_source,
                    "start": source_ref["start"],
                    "end": source_ref["end"],
                })
        citations_resolved = requirement_ids_valid and len(resolved_refs) == len(proposal.requirement_ids)
        checks.append(
            {
                **proposal.model_dump(mode="json"),
                "id": f"P{index:02d}",
                "model_proposal_id": model_proposal_id,
                "responsibility_id_valid_and_unique": id_valid,
                "duplicate_proposal": duplicate_proposal,
                "overlapping_requirement_coverage": any(proposal_requirement_counts.get(item, 0) > 1 for item in proposal.requirement_ids),
                "requirement_ids_valid": requirement_ids_valid,
                "source_ids_valid": citations_resolved,
                "source_spans_resolved": citations_resolved,
                "semantic_status": "NOT_ASSESSED",
                "source_refs": resolved_refs,
                "status": "REVIEW_REQUIRED",
                "validation_note": "Every cited FR resolved to its exact source span; overlap is not itself a duplicate and semantics remain unassessed."
                if id_valid and citations_resolved
                else "Missing or mismatched source reference; do not use this proposal as evidence.",
            }
        )
    known_requirement_ids = {item["id"] for item in raw["requirements"]}
    normalized = []
    for item in parsed.normalized_requirements:
        source_ref = requirement_source_refs.get(item.id)
        source_id = source_ref["source_id"] if source_ref else None
        exact_source = source_texts.get(source_id) if source_id else None
        resolved_ref = None
        if exact_source is not None and source_ref is not None:
            resolved_ref = {
                "source_id": source_id,
                "quote": exact_source,
                "start": source_ref["start"],
                "end": source_ref["end"],
            }
        normalized.append(
            {
                **item.model_dump(mode="json"),
                "source_id": source_id,
                "requirement_id_valid": item.id in known_requirement_ids,
                "source_id_valid": exact_source is not None,
                "source_span_resolved": resolved_ref is not None,
                "source_ref": resolved_ref,
                "status": "REVIEW_REQUIRED",
                "validation_note": "Source ID resolved to the exact input span; a reviewer must approve normalized meaning."
                if item.id in known_requirement_ids and resolved_ref
                else "Unknown requirement/source ID; do not replace the fixture input.",
            }
        )
    evidence_proposals = []
    evidence_proposal_ids: set[str] = set()
    relation_keys = []
    for item in parsed.evidence_proposals:
        predicate = item.predicate.strip().upper()
        subject, object_id = item.subject_requirement_id, item.object_requirement_id
        if predicate in {"SHARES_STATE_OR_INVARIANT", "REQUIRES_INDEPENDENT_CHANGE"} and subject > object_id:
            subject, object_id = object_id, subject
        relation_keys.append((subject, predicate, object_id))
    relation_counts = {key: relation_keys.count(key) for key in set(relation_keys)}
    relation_statuses = {
        key: {
            item.proposed_status
            for item, item_key in zip(parsed.evidence_proposals, relation_keys)
            if item_key == key
        }
        for key in set(relation_keys)
    }
    for index, item in enumerate(parsed.evidence_proposals, start=1):
        refs = []
        for requirement_id in item.source_requirement_ids:
            source_ref = requirement_source_refs.get(requirement_id)
            exact_source = source_texts.get(source_ref["source_id"]) if source_ref else None
            if source_ref is not None and exact_source is not None:
                refs.append(
                    {
                        "source_id": source_ref["source_id"],
                        "quote": exact_source,
                        "start": source_ref["start"],
                        "end": source_ref["end"],
                    }
                )
        subject_valid = item.subject_requirement_id in known_requirement_ids
        object_valid = item.object_requirement_id in known_requirement_ids
        source_refs_valid = bool(item.source_requirement_ids) and len(refs) == len(item.source_requirement_ids)
        id_valid = bool(item.id.strip()) and item.id not in evidence_proposal_ids
        evidence_proposal_ids.add(item.id)
        relation_key = relation_keys[index - 1]
        duplicate_relation = relation_counts[relation_key] > 1
        conflicting_status = len(relation_statuses[relation_key]) > 1
        reference_valid = id_valid and subject_valid and object_valid and source_refs_valid
        citation_covers_endpoints = {item.subject_requirement_id, item.object_requirement_id} <= set(item.source_requirement_ids)
        evidence_proposals.append(
            {
                **item.model_dump(mode="json"),
                "id": f"E{index:02d}",
                "model_proposal_id": item.id,
                "source_ids": [ref["source_id"] for ref in refs],
                "id_valid_and_unique": id_valid,
                "subject_requirement_id_valid": subject_valid,
                "object_requirement_id_valid": object_valid,
                "source_refs_valid": source_refs_valid,
                "duplicate_relation": duplicate_relation,
                "conflicting_status": conflicting_status,
                "self_relation": item.subject_requirement_id == item.object_requirement_id,
                "citation_covers_endpoints": citation_covers_endpoints,
                "predicate_in_registry": item.predicate.strip().upper() in RELATION_PREDICATES,
                "relation_direction": "DIRECTED" if item.predicate.strip().upper() == "BUSINESS_PRECEDES" else "UNDIRECTED" if item.predicate.strip().upper() in RELATION_PREDICATES else "UNREGISTERED",
                "business_relation_implies_architecture": False,
                "citation_status": "RESOLVED" if reference_valid else "INVALID",
                "semantic_status": "NOT_ASSESSED",
                "source_refs": refs,
                "review_status": "REVIEW_REQUIRED",
                "provenance": "LOCAL_OLLAMA_UNVERIFIED",
                "validation_note": "Requirement and source IDs resolved; relation meaning still needs human review."
                if reference_valid
                else "Unknown or duplicate relation reference; do not treat as evidence.",
            }
        )
    boundary_hypotheses = []
    boundary_hypothesis_ids: set[str] = set()
    boundary_shapes = [tuple(sorted(item.requirement_ids)) for item in parsed.boundary_hypotheses]
    boundary_shape_counts = {shape: boundary_shapes.count(shape) for shape in set(boundary_shapes)}
    for index, item in enumerate(parsed.boundary_hypotheses, start=1):
        refs = []
        for requirement_id in item.source_requirement_ids:
            source_ref = requirement_source_refs.get(requirement_id)
            exact_source = source_texts.get(source_ref["source_id"]) if source_ref else None
            if source_ref is not None and exact_source is not None:
                refs.append(
                    {
                        "source_id": source_ref["source_id"],
                        "quote": exact_source,
                        "start": source_ref["start"],
                        "end": source_ref["end"],
                    }
                )
        unique_requirement_ids = len(item.requirement_ids) == len(set(item.requirement_ids))
        requirement_ids_valid = (
            unique_requirement_ids
            and len(item.requirement_ids) >= 2
            and set(item.requirement_ids) <= known_requirement_ids
        )
        source_refs_valid = bool(item.source_requirement_ids) and len(refs) == len(item.source_requirement_ids)
        id_valid = bool(item.id.strip()) and item.id not in boundary_hypothesis_ids
        boundary_hypothesis_ids.add(item.id)
        reference_valid = id_valid and requirement_ids_valid and source_refs_valid
        source_covers_hypothesis = set(item.requirement_ids) <= set(item.source_requirement_ids)
        boundary_hypotheses.append(
            {
                **item.model_dump(mode="json"),
                "id": f"B{index:02d}",
                "model_proposal_id": item.id,
                "source_ids": [ref["source_id"] for ref in refs],
                "id_valid_and_unique": id_valid,
                "duplicate_hypothesis": boundary_shape_counts[boundary_shapes[index - 1]] > 1,
                "requirement_ids_valid": requirement_ids_valid,
                "source_refs_valid": source_refs_valid,
                "source_covers_hypothesis": source_covers_hypothesis,
                "source_refs": refs,
                "review_status": "REVIEW_REQUIRED",
                "provenance": "LOCAL_OLLAMA_UNVERIFIED",
                "validation_note": "Requirement and source IDs resolved; the proposed boundary still needs human review."
                if reference_valid
                else "Unknown or duplicate boundary reference; do not treat as an architecture decision.",
            }
        )
    proposal_ids = [item["id"] for item in checks]
    normalized_ids = [item["id"] for item in normalized]
    proposal_coverage = {
        requirement_id: proposal_requirement_counts.get(requirement_id, 0)
        for requirement_id in sorted(known_requirement_ids)
    }
    can_apply = (
        len(checks) <= 8
        and len(set(proposal_ids)) == len(proposal_ids)
        and all(
            item["responsibility_id_valid_and_unique"]
            and item["requirement_ids_valid"]
            and item["source_ids_valid"]
            and item["source_spans_resolved"]
            and not item["duplicate_proposal"]
            for item in checks
        )
        and len(normalized) == 6
        and len(set(normalized_ids)) == 6
        and set(normalized_ids) == known_requirement_ids
        and all(
            item["requirement_id_valid"]
            and item["source_id_valid"]
            and item["source_span_resolved"]
            for item in normalized
        )
    )
    return {
        "model": model,
        "response_model": response.get("model", model),
        "prompt_version": PROMPT_VERSION,
        "input_sha256": input_sha256,
        "inference_started_at_utc": inference_started_at_utc,
        "inference_completed_at_utc": datetime.now(timezone.utc).isoformat(),
        "generation_parameters": GENERATION_PARAMETERS,
        "raw_response": content,
        "raw_response_sha256": hashlib.sha256(content.encode("utf-8")).hexdigest(),
        "output_schema": output_schema,
        "prompt": prompt,
        "context_summary": parsed.context_summary,
        "context_status": "REVIEW_REQUIRED",
        "normalized_requirements": normalized,
        "proposals": checks,
        "proposal_coverage_by_requirement": proposal_coverage,
        "uncovered_requirement_ids": [item for item, count in proposal_coverage.items() if count == 0],
        "evidence_proposals": evidence_proposals,
        "evidence_proposals_valid": bool(evidence_proposals)
        and all(
            item["id_valid_and_unique"]
            and item["subject_requirement_id_valid"]
            and item["object_requirement_id_valid"]
            and item["source_refs_valid"]
            for item in evidence_proposals
        ),
        "boundary_hypotheses": boundary_hypotheses,
        "boundary_hypotheses_valid": bool(boundary_hypotheses)
        and all(
            item["id_valid_and_unique"] and not item["duplicate_hypothesis"] and item["requirement_ids_valid"] and item["source_refs_valid"]
            for item in boundary_hypotheses
        ),
        "can_apply_to_fixture": can_apply,
        "blind_annotation_lock": deepcopy(blind_annotation_lock),
        "status": "REVIEW_REQUIRED",
        "provenance": "LOCAL_OLLAMA_UNVERIFIED",
    }


def apply_proposals_to_fixture(fixture: dict[str, Any], proposal_data: dict[str, Any]) -> dict[str, Any]:
    """Prepare a cited LLM proposal set as candidate inputs without approving its semantics."""
    if not proposal_data.get("can_apply_to_fixture"):
        raise OllamaError("Model responsibility proposals must be unique, cite known FRs, resolve exact spans, and fit the optimizer cap.")
    updated = deepcopy(fixture)
    requirements = {
        item["id"]: item for item in updated["raw_requirements"]["requirements"]
    }
    new_responsibilities = []
    for index, proposal in enumerate(proposal_data["proposals"], start=1):
        source_refs = []
        for requirement_id in proposal["requirement_ids"]:
            requirement = requirements.get(requirement_id)
            if requirement is None:
                raise OllamaError(f"Proposal {proposal['id']} references unknown requirement {requirement_id}.")
            source_refs.append(requirement["source_ref"])
        new_responsibilities.append(
            {
                "id": f"R{index}",
                "proposal_id": proposal["id"],
                "name": proposal["name"],
                "activity": proposal["activity"],
                "operation": proposal["operation"],
                "decomposition_rationale": proposal["decomposition_rationale"],
                "requirement_ids": proposal["requirement_ids"],
                "source_refs": source_refs,
                "workflow_activity_ids": [],
                "workflow_mapping_status": "UNRESOLVED",
                "workflow_note": "No workflow mapping is inferred from narrative overlap.",
                "review_decision_status": "REVIEW_REQUIRED",
                "semantic_status": "REVIEW_REQUIRED",
            }
        )
    updated["responsibilities"] = new_responsibilities
    kept_evidence = [
        item for item in updated["evidence"]
        if item["predicate"] == "independent_deployment_evidence"
    ]
    updated["evidence"] = kept_evidence
    updated["relation_annotations"] = []
    updated["responsibility_review_complete"] = False
    updated["responsibility_provenance"] = "LOCAL_OLLAMA_UNVERIFIED"
    updated["context_proposal"] = {
        "context_summary": proposal_data["context_summary"],
        "normalized_requirements": proposal_data["normalized_requirements"],
        "status": "REVIEW_REQUIRED",
        "provenance": "LOCAL_OLLAMA_UNVERIFIED",
        "model": proposal_data["model"],
    }
    updated["fixture_note"] = (
        "Raw requirements are the prepared Tutor Support source package. Responsibility inputs include local Ollama "
        "proposals with variable FR cardinality; exact citations were checked, while semantics remain REVIEW_REQUIRED."
    )
    return updated
