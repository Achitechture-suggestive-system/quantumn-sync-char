"""Verify all raw stages before scoring sentence drafts; integrity is not entailment."""

from collections import Counter
from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from .models import SourceRef
from .studio_evaluation_protocol import EvaluationBlocked, timestamp
from .studio_evidence import catalog_digest
from .studio_extraction import proposal_issues
from .studio_semantics import SCHEMA, proposal_signature
from .studio_sentence_extraction import (MAX_CLAIMS, build_claim_request, build_frame_request, check_processing,
                                         digest, normalize)


@dataclass(frozen=True)
class VerifiedProposal:
    raw: Any
    source_ref: SourceRef | None = None
    duplicate: bool = False


def token_metadata(extraction) -> dict:
    values = ([stage.get("tokens") for stage in extraction.get("stages", [])]
              if extraction.get("method") == "SENTENCE" else [extraction.get("tokens")])
    observed = [value for value in values if type(value) is int and value >= 0]
    complete = bool(values) and len(observed) == len(values)
    return {"tokens": sum(observed) if complete else None, "tokens_observed": sum(observed) if observed else None,
            "token_reporting": "COMPLETE" if complete else "PARTIAL" if observed else "UNAVAILABLE"}


def artifact_hashes(root: Path) -> dict:
    files = sorted(root.glob("*.json"))
    if any(path.is_symlink() or not path.is_file() for path in files):
        raise EvaluationBlocked("Raw trace có symlink hoặc file không hợp lệ.")
    return {path.name: sha256(path.read_bytes()).hexdigest() for path in files}


def _read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def _require(condition, message):
    if not condition:
        raise EvaluationBlocked(message)


def verify_sentence_trace(root, architecture, query, extraction, call, frozen):
    """Regenerate requests from frozen code + raw claims, never from reference labels."""
    try:
        return _verify_sentence(root, architecture, query, extraction, call, frozen)
    except (ValueError, TypeError, KeyError, AttributeError, IndexError) as exc:
        raise EvaluationBlocked(f"Sentence trace không nhất quán: {exc}") from exc


def _verify_sentence(root, architecture, query, extraction, call, frozen):
    primary_request, units = build_claim_request(architecture, query.source_ids, query.task, frozen["model"])
    _require(extraction.get("method") == "SENTENCE" and extraction.get("semantic_schema") == SCHEMA
             and extraction.get("units") == units, "Method/schema/unit registry khác freeze.")
    _require(extraction.get("catalog_digest") == catalog_digest(architecture)
             and extraction.get("source_digests") == {r.id: r.input_digest() for r in architecture.requirements if r.id in query.source_ids},
             "Source/catalog hash của sentence trace khác input đã freeze.")
    _require(extraction.get("validation_code_sha256") == {name: frozen["code_hashes"][name] for name in
              ("studio_sentence_extraction.py", "studio_extraction.py", "studio_semantics.py")}, "Validation code hash khác freeze.")
    stages = extraction.get("stages")
    _require(isinstance(stages, list) and stages, "Thiếu stage claims/frame.")
    previous = timestamp(extraction["recorded_at"])
    token_count = 0

    def stage(index, name, expected_request):
        nonlocal previous, token_count
        record = stages[index]
        request, response = _read(root / f"{name}-request.json"), _read(root / f"{name}-response.json")
        content = response.get("message", {}).get("content")
        _require(record.get("name") == name and record.get("status") == "RESPONSE_RECEIVED", "Stage thiếu/trùng/đảo thứ tự.")
        _require(request == expected_request and record.get("request_sha256") == digest(request), "Request stage khác frozen recipe.")
        _require(isinstance(content, str) and record.get("response_sha256") == sha256(content.encode()).hexdigest(), "Raw frame/claim content hash khác trace.")
        _require(response.get("model") == frozen["model"] and response.get("done_reason") == "stop", "Stage model chưa hoàn tất hoặc khác model.")
        started, ended = timestamp(record["recorded_at"]), timestamp(record["completed_at"])
        _require(previous <= started <= ended <= timestamp(call["completed_at"]), "Thời điểm stage không tuần tự hoặc ngoài query.")
        previous = ended
        _require(record.get("tokens") == response.get("eval_count"), "Stage token count không khớp response.")
        token_count += response.get("eval_count", 0) or 0
        return json.loads(content), response

    primary, response = stage(0, "claims", primary_request)
    _require(_read(root / "request.json") == primary_request and _read(root / "response.json") == response,
             "Primary compatibility files khác claims request/response.")
    _require(isinstance(primary, dict) and isinstance(primary.get("results"), list), "Raw primary thiếu results.")
    registry = {unit["unit_id"]: unit for unit in units}
    returned, candidates = [], []
    counts = Counter(sentence_unit_rows=len(primary["results"]), provider_calls=len(stages))
    for row in primary["results"]:
        if not isinstance(row, dict) or row.get("unit_id") not in registry or not isinstance(row.get("claims"), list):
            counts["invalid_sentence_unit_rows"] += 1
            counts["unmapped_claims_in_invalid_units"] += len(row["claims"]) if isinstance(row, dict) and isinstance(row.get("claims"), list) else 0
            continue
        returned.append(row["unit_id"])
        counts["empty_sentence_unit_rows"] += not row["claims"]
        for index, claim in enumerate(row["claims"]):
            candidates.append((registry[row["unit_id"]], index, claim))
    missing = sorted(set(registry) - set(returned))
    duplicates = sorted({key for key in returned if returned.count(key) > 1})
    _require(extraction.get("missing_unit_ids") == missing and extraction.get("duplicate_unit_ids") == duplicates,
             "Unit coverage metadata khác raw primary.")
    counts.update(missing_sentence_units=len(missing), duplicate_sentence_unit_ids=len(duplicates))
    proposals = extraction.get("proposals")
    _require(len(candidates) <= MAX_CLAIMS and isinstance(proposals, list) and len(proposals) == len(candidates)
             and len(stages) == 1 + len(candidates), "Thiếu/thừa frame hoặc proposal; không được chọn lọc draft.")
    signatures, verified = {}, []
    for number, ((unit, claim_index, claim), proposal) in enumerate(zip(candidates, proposals), 1):
        name = f"frame-{number:03d}"
        frame, _ = stage(number, name, build_frame_request(architecture, unit, query.task, claim, frozen["model"]))
        payload = normalize(architecture, query.task, unit, claim, frame)
        processing = proposal["processing"]
        _require(processing.get("task") == query.task and processing.get("unit") == unit and processing.get("claim_index") == claim_index
                 and processing.get("frame_stage") == name and processing.get("raw_claim") == claim and processing.get("raw_frame") == frame,
                 "Lineage không khớp raw claim/frame hoặc unit đã freeze.")
        check_processing(architecture, processing, payload)
        _require(processing.get("field_origins") == {
            "claim_fields": "LLM_PROPOSAL_STAGE_1", "frame_text_and_effect": "LLM_PROPOSAL_STAGE_2",
            "quote_and_source_ref": "SOURCE_REQUIREMENT_VIA_DETERMINISTIC_SPAN_LOOKUP",
            "role_ids_and_disposition": "DETERMINISTIC_TRANSFORMATION"}, "Provenance của normalized fields đã đổi.")
        signature = digest([unit, claim])
        duplicate = signatures.get(signature)
        identifier = f"{extraction['id']}-{number}"
        _require(proposal.get("id") == identifier and proposal.get("run_id") == extraction["id"]
                 and proposal.get("source_id") == unit["source_id"] and proposal.get("payload") == payload
                 and proposal.get("status") == "REVIEW_REQUIRED" and proposal.get("provenance") == "LLM_PROPOSAL"
                 and proposal.get("model") == frozen["model"] and proposal.get("prompt_version") == frozen["prompt_version"]
                 and proposal.get("semantic_schema") == SCHEMA and proposal.get("catalog_digest") == extraction["catalog_digest"]
                 and proposal.get("source_digest") == extraction["source_digests"][unit["source_id"]]
                 and proposal.get("proposal_signature") == proposal_signature(unit["source_id"], payload)
                 and proposal.get("duplicate_of_proposal_id") == duplicate, "Draft đã đổi hoặc thiếu/trùng so với raw stages.")
        ref = SourceRef(source_id=unit["source_id"], quote=unit["text"], start=unit["start"], end=unit["end"])
        issues = proposal_issues(architecture, unit["source_id"], payload, structured=True, source_ref=ref)
        if duplicate:
            issues.append(f"Claim trùng trong cùng unit với {duplicate}; giữ để REJECT/DEFER hoặc CORRECT.")
        _require(proposal.get("issues") == issues, "Gate issues khác frozen validator.")
        verified.append(VerifiedProposal({**payload, "source_id": unit["source_id"]}, ref, bool(duplicate)))
        signatures.setdefault(signature, identifier)
    _require(extraction.get("tokens") == token_count, "Tổng token không khớp các stage.")
    _require(previous <= timestamp(extraction["completed_at"]) <= timestamp(call["completed_at"]), "Extraction completion ngoài query.")
    return verified, counts
