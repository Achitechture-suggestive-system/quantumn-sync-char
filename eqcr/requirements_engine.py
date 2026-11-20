"""Exact-span requirement classification proposals and explicit review records."""

from __future__ import annotations

import re
from typing import Literal

from pydantic import AwareDatetime, Field, field_validator

from .models import SourceRef, StrictModel
from .studio_quality import quality_suggestions

RequirementType = Literal["FR", "NFR", "MIXED", "ARCHITECTURAL_CONSTRAINT", "DESIGN_DECISION", "UNKNOWN"]

_BOUNDARY = re.compile(r";|\r?\n|(?<=[.!?])\s+")
_CONNECTOR = re.compile(r"\s+(?:and|và)\s+", re.IGNORECASE)
_DECISION = re.compile(r"\b(?:design decision|we decided|we chose|the design uses|quyết định thiết kế|đã chọn)\b", re.IGNORECASE)
_CONSTRAINT = re.compile(r"\b(?:must use|must comply with|shall be deployed on|bắt buộc dùng|phải tuân thủ|phải triển khai trên)\b", re.IGNORECASE)
_FUNCTION = re.compile(r"\b(?:can|must be able to|shall allow|shall provide|có thể|cho phép)\b", re.IGNORECASE)


class ReviewRecord(StrictModel):
    reviewer_id: str = Field(min_length=1)
    reviewed_at: AwareDatetime
    rationale: str = Field(min_length=1)

    @field_validator("reviewer_id", "rationale")
    @classmethod
    def nonblank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("A review requires an actor and rationale.")
        return value


class RequirementDocument(StrictModel):
    id: str = Field(min_length=1)
    text: str = Field(min_length=1)
    declared_type: RequirementType | None = None
    provenance: Literal["SOURCE_REQUIREMENT", "PREPARED_FIXTURE", "LLM_PROPOSAL", "SUPPLIED_OBSERVATION"] = "SOURCE_REQUIREMENT"

    @field_validator("text")
    @classmethod
    def nonblank_document(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("A source document must contain text.")
        return value


class AtomicRequirementReview(ReviewRecord):
    atomic_id: str
    source_ref: SourceRef
    requirement_type: RequirementType
    disposition: Literal["APPROVED", "REJECTED"]


def require_span(ref: SourceRef, texts: dict[str, str]) -> None:
    text = texts.get(ref.source_id)
    if text is None or not (ref.start < ref.end <= len(text)) or text[ref.start:ref.end] != ref.quote:
        raise ValueError(f"Unresolved source span in {ref.source_id!r} at {ref.start}:{ref.end}.")


def _propose_kind(text: str) -> tuple[RequirementType, str]:
    if _DECISION.search(text):
        return "DESIGN_DECISION", "Explicit design-choice marker"
    if _CONSTRAINT.search(text):
        return "ARCHITECTURAL_CONSTRAINT", "Explicit mandate marker"
    quality = quality_suggestions(text)
    functional = _FUNCTION.search(text)
    if quality and functional:
        return "MIXED", "Functional marker and quality signals occur together"
    if quality:
        return "NFR", "Quality signal: " + ", ".join(quality.values())
    if functional:
        return "FR", "Externally observable capability marker: " + functional.group()
    return "UNKNOWN", "No specific requirement signal found"


def _atomic_spans(text: str, declared: RequirementType | None) -> list[tuple[int, int]]:
    if declared and declared != "MIXED":
        return [(0, len(text))]
    starts = [0]
    ends = []
    for match in _BOUNDARY.finditer(text):
        ends.append(match.start())
        starts.append(match.end())
    ends.append(len(text))
    spans = []
    for start, end in zip(starts, ends, strict=True):
        segment = text[start:end]
        kind, _ = _propose_kind(segment)
        split = None
        if kind == "MIXED":
            split = next((match for match in _CONNECTOR.finditer(segment)
                          if {_propose_kind(segment[:match.start()])[0], _propose_kind(segment[match.end():])[0]}
                          == {"FR", "NFR"}), None)
        parts = [(start, end)] if split is None else [(start, start + split.start()), (start + split.end(), end)]
        spans.extend((a + len(text[a:b]) - len(text[a:b].lstrip()), a + len(text[a:b].rstrip()))
                     for a, b in parts if text[a:b].strip())
    return spans


def classify_documents(
    documents: list[RequirementDocument], reviews: list[AtomicRequirementReview],
) -> dict:
    text_by_id = {document.id: document.text for document in documents}
    if len(text_by_id) != len(documents):
        raise ValueError("Requirement source IDs must be unique.")
    review_by_id = {item.atomic_id: item for item in reviews}
    if len(review_by_id) != len(reviews):
        raise ValueError("Provide at most one current classification review per atomic ID.")
    report = []
    for document in documents:
        atoms = []
        for index, (start, end) in enumerate(_atomic_spans(document.text, document.declared_type), 1):
            atom_id = f"{document.id}.A{index:02d}"
            source = SourceRef(source_id=document.id, start=start, end=end, quote=document.text[start:end])
            declared = document.declared_type not in (None, "MIXED")
            kind, rationale = _propose_kind(source.quote)
            if declared:
                kind, rationale = document.declared_type, "Requirement type declared in the input source record"
            evidence = (
                "UNKNOWN" if kind == "UNKNOWN" else "SOURCE_CONFIRMED"
                if declared and document.provenance in {"SOURCE_REQUIREMENT", "PREPARED_FIXTURE"} else "PROPOSED"
            )
            review = review_by_id.pop(atom_id, None)
            if review:
                require_span(review.source_ref, text_by_id)
                if review.source_ref != source or review.disposition == "APPROVED" and review.requirement_type == "MIXED":
                    raise ValueError(f"Review for {atom_id} has changed spans or an unsplit MIXED requirement.")
                if review.disposition == "APPROVED" and document.provenance == "LLM_PROPOSAL":
                    raise ValueError(f"Review the original source instead of approving model output {atom_id} as evidence.")
                kind, rationale = review.requirement_type, review.rationale
            status = ("HUMAN_APPROVED" if review.disposition == "APPROVED" else "REJECTED") if review else evidence
            atoms.append({
                "atomic_id": atom_id, "requirement_type": kind, "source_ref": source.model_dump(mode="json"),
                "interpretation": source.quote, "rationale": rationale, "evidence_status": evidence,
                "review_status": status,
                "source_provenance": document.provenance,
                "provenance": "HUMAN_DECISION" if review else "SOURCE_DECLARATION" if declared else "DETERMINISTIC_RULE_INFERENCE",
                "review": review.model_dump(mode="json") if review else None,
            })
        kinds = {item["requirement_type"] for item in atoms}
        kind = document.declared_type or ("MIXED" if len(kinds) > 1 else next(iter(kinds), "UNKNOWN"))
        report.append({"source_id": document.id, "original_text": document.text, "requirement_type": kind,
                       "source_provenance": document.provenance, "atoms": atoms})
    if review_by_id:
        raise ValueError(f"Reviews refer to unknown atomic IDs: {sorted(review_by_id)}.")
    return {"schema_version": "1.0.0", "documents": report}
