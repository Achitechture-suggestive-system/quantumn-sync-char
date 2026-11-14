"""Optional local Ollama proposal client. Output remains untrusted and review-required."""

from __future__ import annotations

import json
import os
import hashlib
from copy import deepcopy
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .models import LLMProposalBundle


DEFAULT_HOST = "http://127.0.0.1:11434"
PROMPT_VERSION = "petclinic-context-responsibility-evidence-boundary-v5"
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
    response = _request("/api/tags")
    return sorted(item["name"] for item in response.get("models", []) if item.get("name"))


def propose_responsibilities(raw: dict[str, Any], model: str) -> dict[str, Any]:
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
        "proposals (array of objects with id, name, activity, operation, requirement_id), "
        "evidence_proposals (array of objects with id, subject_requirement_id, predicate, object_requirement_id, "
        "proposed_status, source_requirement_ids, rationale), and boundary_hypotheses (array of objects with id, "
        "requirement_ids, boundary_rationale, source_requirement_ids). "
        "Return six proposals covering FR-01 through FR-06 exactly once. Give each proposal a unique proposal label; "
        "the application assigns stable R1-R6 IDs from the cited requirement ID. Use the additional context to write "
        "a descriptive context summary. Keep normalized requirements and responsibilities grounded in their FR text. "
        "Cite requirements using FR IDs only: "
        "normalized_requirements.id is the cited FR ID, proposals.requirement_id is the cited FR ID, and evidence or "
        "boundary source_requirement_ids must list cited FR IDs. Do not output source_id fields or workflow/scenario IDs. "
        "The application resolves each FR citation to the exact source ID and input span; do not generate or quote source "
        "text. Use only FR IDs from the REQUIREMENT MAP below for evidence and boundary claims. Propose one or more typed evidence relations using requirement IDs; "
        "proposed_status must be PRESENT only when the cited text supports the relation, SCOPED_ABSENT only when the "
        "provided text explicitly defines a scope where the relation is absent, and UNKNOWN otherwise. Every evidence "
        "proposal must cite one or more source_requirement_ids. Propose one or more tentative responsibility-boundary hypotheses "
        "using requirement IDs; these are hypotheses, not partitions or deployment claims. Cite source_requirement_ids "
        "for every boundary hypothesis. Do not infer runtime topology, ownership, deployment, or business policies. "
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
    used_proposal_ids: set[str] = set()
    for proposal in parsed.proposals:
        source_ref = requirement_source_refs.get(proposal.requirement_id)
        source_id = source_ref["source_id"] if source_ref else None
        exact_source = source_texts.get(source_id) if source_id else None
        id_valid = bool(proposal.id.strip()) and proposal.id not in used_proposal_ids
        used_proposal_ids.add(proposal.id)
        requirement_valid = proposal.requirement_id in {item["id"] for item in raw["requirements"]}
        resolved_ref = None
        if exact_source is not None and source_ref is not None:
            resolved_ref = {
                "source_id": source_id,
                "quote": exact_source,
                "start": source_ref["start"],
                "end": source_ref["end"],
            }
        checks.append(
            {
                **proposal.model_dump(mode="json"),
                "source_id": source_id,
                "responsibility_id_valid_and_unique": id_valid,
                "requirement_id_valid": requirement_valid,
                "source_id_valid": exact_source is not None,
                "source_span_resolved": resolved_ref is not None,
                "source_ref": resolved_ref,
                "status": "REVIEW_REQUIRED",
                "validation_note": "Source ID resolved to the exact input span; a human must still approve the semantic proposal."
                if id_valid and requirement_valid and resolved_ref
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
    for item in parsed.evidence_proposals:
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
        reference_valid = id_valid and subject_valid and object_valid and source_refs_valid
        evidence_proposals.append(
            {
                **item.model_dump(mode="json"),
                "source_ids": [ref["source_id"] for ref in refs],
                "id_valid_and_unique": id_valid,
                "subject_requirement_id_valid": subject_valid,
                "object_requirement_id_valid": object_valid,
                "source_refs_valid": source_refs_valid,
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
    for item in parsed.boundary_hypotheses:
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
        boundary_hypotheses.append(
            {
                **item.model_dump(mode="json"),
                "source_ids": [ref["source_id"] for ref in refs],
                "id_valid_and_unique": id_valid,
                "requirement_ids_valid": requirement_ids_valid,
                "source_refs_valid": source_refs_valid,
                "source_refs": refs,
                "review_status": "REVIEW_REQUIRED",
                "provenance": "LOCAL_OLLAMA_UNVERIFIED",
                "validation_note": "Requirement and source IDs resolved; the proposed boundary still needs human review."
                if reference_valid
                else "Unknown or duplicate boundary reference; do not treat as an architecture decision.",
            }
        )
    proposal_ids = [item["id"] for item in checks]
    requirement_ids = [item["requirement_id"] for item in checks]
    normalized_ids = [item["id"] for item in normalized]
    can_apply = (
        len(checks) == 6
        and len(set(proposal_ids)) == 6
        and len(set(requirement_ids)) == 6
        and set(requirement_ids) == known_requirement_ids
        and all(
            item["responsibility_id_valid_and_unique"]
            and item["requirement_id_valid"]
            and item["source_id_valid"]
            and item["source_span_resolved"]
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
        "generation_parameters": GENERATION_PARAMETERS,
        "output_schema": output_schema,
        "prompt": prompt,
        "context_summary": parsed.context_summary,
        "context_status": "REVIEW_REQUIRED",
        "normalized_requirements": normalized,
        "proposals": checks,
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
            item["id_valid_and_unique"] and item["requirement_ids_valid"] and item["source_refs_valid"]
            for item in boundary_hypotheses
        ),
        "can_apply_to_fixture": can_apply,
        "status": "REVIEW_REQUIRED",
        "provenance": "LOCAL_OLLAMA_UNVERIFIED",
    }


def apply_proposals_to_fixture(fixture: dict[str, Any], proposal_data: dict[str, Any]) -> dict[str, Any]:
    """Prepare a cited LLM proposal set as candidate inputs without approving its semantics."""
    if not proposal_data.get("can_apply_to_fixture"):
        raise OllamaError("The model output does not have complete, source-checked coverage for FR-01 through FR-06.")
    updated = deepcopy(fixture)
    requirements = {
        item["id"]: item for item in updated["raw_requirements"]["requirements"]
    }
    canonical_ids = {
        requirement_id: item["id"]
        for item in fixture["responsibilities"]
        for requirement_id in item["requirement_ids"]
    }
    proposals = {item["requirement_id"]: item for item in proposal_data["proposals"]}
    new_responsibilities = []
    for requirement_id in sorted(requirements):
        proposal = proposals[requirement_id]
        requirement = requirements[requirement_id]
        if proposal["source_id"] != requirement["source_ref"]["source_id"]:
            raise OllamaError(f"The source ID for {requirement_id} no longer matches the frozen input.")
        quote = requirement["text"]
        ref = {
            "source_id": requirement["source_ref"]["source_id"],
            "quote": quote,
            "start": 0,
            "end": len(quote),
        }
        new_responsibilities.append(
            {
                "id": canonical_ids[requirement_id],
                "proposal_id": proposal["id"],
                "name": proposal["name"],
                "activity": proposal["activity"],
                "operation": proposal["operation"],
                "requirement_ids": [requirement_id],
                "source_refs": [ref],
                "workflow_activity_ids": [],
                "workflow_mapping_status": "UNRESOLVED",
                "workflow_note": "WF-01 is narrative text without stable task IDs; no task-level mapping is inferred.",
                "semantic_status": "REVIEW_REQUIRED",
            }
        )
    updated["responsibilities"] = new_responsibilities
    kept_evidence = [
        item for item in updated["evidence"]
        if item["predicate"] != "responsibility_named_by_requirement"
    ]
    for responsibility in new_responsibilities:
        kept_evidence.append(
            {
                "id": f"EV-{responsibility['id']}-LLM",
                "subject_id": responsibility["id"],
                "predicate": "responsibility_proposal_cites_requirement",
                "object_id": responsibility["requirement_ids"][0],
                "status": "PRESENT",
                "provenance": "MODEL_PROPOSED",
                "review_status": "REVIEW_REQUIRED",
                "source_refs": responsibility["source_refs"],
                "is_assumption": False,
                "rationale": "The system resolved the cited requirement ID to its exact source span; the LLM interpretation remains review-required.",
            }
        )
    updated["evidence"] = kept_evidence
    updated["responsibility_provenance"] = "LOCAL_OLLAMA_UNVERIFIED"
    updated["context_proposal"] = {
        "context_summary": proposal_data["context_summary"],
        "normalized_requirements": proposal_data["normalized_requirements"],
        "status": "REVIEW_REQUIRED",
        "provenance": "LOCAL_OLLAMA_UNVERIFIED",
        "model": proposal_data["model"],
    }
    updated["fixture_note"] = (
        "Raw requirements are from the PRECOMPUTED fixture. Context and responsibility inputs include local Ollama "
        "proposals; exact citations were checked, while semantics remain REVIEW_REQUIRED."
    )
    return updated
