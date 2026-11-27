"""Blind annotation protocol and integrity checkpoint for the P2 Tutor case."""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from pydantic import Field, ValidationError, model_validator

from .models import StrictModel


BLIND_PROTOCOL_VERSION = "P2-BLIND-ANNOTATION-v3"
MAX_OPTIMIZER_RESPONSIBILITIES = 8
RELATION_PREDICATES = {
    "BUSINESS_PRECEDES": "directed business/workflow ordering only; never an architecture constraint by itself",
    "SHARES_STATE_OR_INVARIANT": "undirected candidate relation requiring direct source evidence of a shared state invariant",
    "REQUIRES_INDEPENDENT_CHANGE": "undirected candidate relation requiring direct source evidence for independent change or deployment",
}
def _canonical_sha256(value: object) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def source_bundle_sha256(raw: dict) -> str:
    """Hash the frozen source-only package used for an annotation session."""
    return _canonical_sha256(raw)


class BlindResponsibilityAnnotation(StrictModel):
    """An independent 0..N responsibility interpretation over one or more FRs."""

    annotation_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    activity: str = Field(min_length=1)
    operation: str = Field(min_length=1)
    requirement_ids: list[str] = Field(min_length=1)
    workflow_ids: list[str] = Field(default_factory=list)
    source_requirement_ids: list[str] = Field(min_length=1)
    source_workflow_ids: list[str] = Field(default_factory=list)
    rationale: str = Field(min_length=1)
    resolved_source_refs: list[dict] = Field(default_factory=list)

    @model_validator(mode="after")
    def unique_citations(self):
        if len(self.requirement_ids) != len(set(self.requirement_ids)):
            raise ValueError("A responsibility annotation cannot repeat requirement IDs.")
        if len(self.workflow_ids) != len(set(self.workflow_ids)):
            raise ValueError("A responsibility annotation cannot repeat workflow IDs.")
        if len(self.source_requirement_ids) != len(set(self.source_requirement_ids)):
            raise ValueError("A responsibility annotation cannot repeat source requirement IDs.")
        if not set(self.workflow_ids) <= set(self.source_workflow_ids):
            raise ValueError("Every mapped workflow activity must also be cited as a source workflow ID.")
        return self


class BlindRelationAnnotation(StrictModel):
    relation_id: str = Field(min_length=1)
    subject_requirement_id: str
    predicate: Literal[
        "BUSINESS_PRECEDES", "SHARES_STATE_OR_INVARIANT", "REQUIRES_INDEPENDENT_CHANGE"
    ]
    object_requirement_id: str
    direction: Literal["DIRECTED", "UNDIRECTED"]
    status: Literal["PRESENT", "UNKNOWN", "SCOPED_ABSENT", "NOT_ANNOTATED"]
    source_requirement_ids: list[str] = Field(default_factory=list)
    source_workflow_ids: list[str] = Field(default_factory=list)
    rationale: str = ""
    reviewer_id: str = ""
    annotated_at: str = ""
    resolved_source_refs: list[dict] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_registry_semantics(self):
        if self.subject_requirement_id == self.object_requirement_id:
            raise ValueError("The relation registry excludes reflexive FR pairs.")
        if self.predicate == "BUSINESS_PRECEDES" and self.direction != "DIRECTED":
            raise ValueError("BUSINESS_PRECEDES is directed.")
        if self.predicate == "SHARES_STATE_OR_INVARIANT":
            if self.direction != "UNDIRECTED":
                raise ValueError("SHARES_STATE_OR_INVARIANT is undirected.")
            if self.subject_requirement_id >= self.object_requirement_id:
                raise ValueError("Undirected relation endpoints must use canonical lexical order.")
        if self.predicate == "REQUIRES_INDEPENDENT_CHANGE":
            if self.direction != "UNDIRECTED":
                raise ValueError("REQUIRES_INDEPENDENT_CHANGE is undirected.")
            if self.subject_requirement_id >= self.object_requirement_id:
                raise ValueError("Undirected relation endpoints must use canonical lexical order.")
        if self.status != "NOT_ANNOTATED" and not self.rationale.strip():
            raise ValueError("Every annotated relation status needs a rationale.")
        if self.status in {"PRESENT", "SCOPED_ABSENT"}:
            if not (self.source_requirement_ids or self.source_workflow_ids) or not self.rationale.strip():
                raise ValueError("PRESENT and SCOPED_ABSENT relations need citations and rationale.")
        if self.status == "PRESENT" and not {
            self.subject_requirement_id, self.object_requirement_id
        } <= set(self.source_requirement_ids):
            raise ValueError("PRESENT source-only relations must cite both FR endpoints.")
        if self.status == "NOT_ANNOTATED" and (
            self.source_requirement_ids
            or self.source_workflow_ids
            or self.rationale.strip()
            or self.reviewer_id
            or self.annotated_at
            or self.resolved_source_refs
        ):
            raise ValueError("NOT_ANNOTATED rows cannot carry reviewer metadata, labels, citations, or rationale.")
        return self


class BlindAnnotationSubmission(StrictModel):
    protocol_version: Literal["P2-BLIND-ANNOTATION-v3"]
    case_id: str
    source_bundle_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    source_package_manifest_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    reviewer_id: str
    source_only_attested: bool
    no_prior_model_output_exposure: bool
    responsibility_annotations: list[BlindResponsibilityAnnotation] = Field(default_factory=list)
    unresolved_requirement_ids: list[str] = Field(default_factory=list)
    relation_registry: list[BlindRelationAnnotation]

    @model_validator(mode="after")
    def unique_registry_keys(self):
        relation_ids = [item.relation_id for item in self.relation_registry]
        if len(relation_ids) != len(set(relation_ids)):
            raise ValueError("Relation registry IDs must be unique.")
        annotation_ids = [item.annotation_id for item in self.responsibility_annotations]
        if len(annotation_ids) != len(set(annotation_ids)):
            raise ValueError("Responsibility annotation IDs must be unique.")
        if len(self.unresolved_requirement_ids) != len(set(self.unresolved_requirement_ids)):
            raise ValueError("Unresolved requirement IDs cannot be duplicated.")
        return self


def build_relation_registry(raw: dict) -> list[dict]:
    requirement_ids = sorted(item["id"] for item in raw["requirements"])
    relations = []
    for subject in requirement_ids:
        for object_id in requirement_ids:
            if subject != object_id:
                relations.append(
                    {
                        "relation_id": f"BUS-{subject}-{object_id}",
                        "subject_requirement_id": subject,
                        "predicate": "BUSINESS_PRECEDES",
                        "object_requirement_id": object_id,
                        "direction": "DIRECTED",
                        "status": "NOT_ANNOTATED",
                        "source_requirement_ids": [],
                        "source_workflow_ids": [],
                        "rationale": "",
                        "reviewer_id": "",
                        "annotated_at": "",
                        "resolved_source_refs": [],
                    }
                )
    for predicate in ("SHARES_STATE_OR_INVARIANT", "REQUIRES_INDEPENDENT_CHANGE"):
        for index, subject in enumerate(requirement_ids):
            for object_id in requirement_ids[index + 1 :]:
                relations.append(
                    {
                        "relation_id": f"{predicate[:4]}-{subject}-{object_id}",
                        "subject_requirement_id": subject,
                        "predicate": predicate,
                        "object_requirement_id": object_id,
                        "direction": "UNDIRECTED",
                        "status": "NOT_ANNOTATED",
                        "source_requirement_ids": [],
                        "source_workflow_ids": [],
                        "rationale": "",
                        "reviewer_id": "",
                        "annotated_at": "",
                        "resolved_source_refs": [],
                    }
                )
    return relations


def build_blind_annotation_template(raw: dict, source_package_root: Path | None = None) -> dict:
    from .p2_reviewer_package import validate_source_only_reviewer_package

    package_info = validate_source_only_reviewer_package(raw, source_package_root)
    return {
        "protocol_version": BLIND_PROTOCOL_VERSION,
        "case_id": raw["case_id"],
        "source_bundle_sha256": source_bundle_sha256(raw),
        "source_package_manifest_sha256": package_info["manifest_sha256"],
        "reviewer_id": "",
        "source_only_attested": False,
        "no_prior_model_output_exposure": False,
        "responsibility_annotations": [],
        "unresolved_requirement_ids": [],
        "relation_registry": build_relation_registry(raw),
    }


def _resolved_refs(raw: dict, requirement_ids: list[str], workflow_ids: list[str]) -> list[dict]:
    sources = [item["source_ref"] for item in raw["requirements"] if item["id"] in requirement_ids]
    sources.extend(item["source_ref"] for item in raw["workflows"] if item["id"] in workflow_ids)
    return deepcopy(sources)


def lock_blind_annotation(
    raw: dict,
    submission: dict,
    *,
    locked_at: str | None = None,
    source_package_root: Path | None = None,
) -> dict:
    """Validate and hash source-only annotations before the UI reveals model proposals."""
    from .p2_reviewer_package import validate_source_only_reviewer_package

    parsed = BlindAnnotationSubmission.model_validate(submission)
    package_info = validate_source_only_reviewer_package(raw, source_package_root)
    requirement_by_id = {item["id"]: item for item in raw["requirements"]}
    workflow_by_id = {item["id"]: item for item in raw["workflows"]}
    expected_source_hash = source_bundle_sha256(raw)
    if parsed.case_id != raw["case_id"] or parsed.source_bundle_sha256 != expected_source_hash:
        raise ValueError("Blind annotation is bound to a different or changed source package.")
    if parsed.source_package_manifest_sha256 != package_info["manifest_sha256"]:
        raise ValueError("Blind annotation is bound to a different or changed source-only reviewer package.")
    if not parsed.source_only_attested:
        raise ValueError("Reviewer must attest that this annotation was completed from source-only materials.")
    if not parsed.no_prior_model_output_exposure:
        raise ValueError(
            "Reviewer must attest that they have not seen model output for this case; otherwise use a different annotator."
        )
    if not parsed.reviewer_id.strip():
        raise ValueError("Reviewer ID is required before an annotation can be locked.")

    covered_requirement_ids: set[str] = set()
    normalized = parsed.model_dump(mode="json")
    for index, annotation in enumerate(parsed.responsibility_annotations):
        unknown = (set(annotation.requirement_ids) | set(annotation.source_requirement_ids)) - set(requirement_by_id)
        if unknown:
            raise ValueError(f"Responsibility annotation references unknown FR IDs: {sorted(unknown)}.")
        unknown_workflows = (set(annotation.workflow_ids) | set(annotation.source_workflow_ids)) - set(workflow_by_id)
        if unknown_workflows:
            raise ValueError(f"Responsibility annotation references unknown workflow IDs: {sorted(unknown_workflows)}.")
        if not set(annotation.requirement_ids) <= set(annotation.source_requirement_ids):
            raise ValueError("Each responsibility must cite every requirement it interprets.")
        covered_requirement_ids.update(annotation.requirement_ids)
        normalized["responsibility_annotations"][index]["resolved_source_refs"] = _resolved_refs(
            raw,
            annotation.source_requirement_ids,
            annotation.source_workflow_ids,
        )

    requirement_ids = set(requirement_by_id)
    unresolved = set(parsed.unresolved_requirement_ids)
    if unresolved - requirement_ids or unresolved != requirement_ids - covered_requirement_ids:
        raise ValueError(
            "List each FR with zero responsibility annotations as unresolved; FRs with one or more annotations must not be unresolved."
        )

    expected_registry = build_relation_registry(raw)
    expected_by_id = {item["relation_id"]: item for item in expected_registry}
    provided_by_id = {item.relation_id: item for item in parsed.relation_registry}
    if set(provided_by_id) != set(expected_by_id):
        raise ValueError("The relation registry must explicitly contain every directed and undirected pair row.")
    workflow_ids = set(workflow_by_id)
    raw_lock_time = locked_at or datetime.now(timezone.utc).isoformat()
    try:
        parsed_lock_time = datetime.fromisoformat(raw_lock_time.replace("Z", "+00:00"))
    except (TypeError, ValueError) as exc:
        raise ValueError("Blind annotation lock time must be a valid timezone-aware ISO-8601 timestamp.") from exc
    if parsed_lock_time.tzinfo is None:
        raise ValueError("Blind annotation lock time must include a timezone.")
    if parsed_lock_time.astimezone(timezone.utc) > datetime.now(timezone.utc):
        raise ValueError("Blind annotation lock time cannot be in the future.")
    now = parsed_lock_time.astimezone(timezone.utc).isoformat()
    for index, relation in enumerate(parsed.relation_registry):
        expected = expected_by_id[relation.relation_id]
        for key in ("subject_requirement_id", "predicate", "object_requirement_id", "direction"):
            if getattr(relation, key) != expected[key]:
                raise ValueError(f"Relation registry row {relation.relation_id} changes its frozen predicate or pair universe.")
        if (set(relation.source_requirement_ids) - requirement_ids) or (set(relation.source_workflow_ids) - workflow_ids):
            raise ValueError(f"Relation {relation.relation_id} cites an unknown source ID.")
        if relation.status in {"PRESENT", "SCOPED_ABSENT"}:
            if not set(relation.source_requirement_ids) <= requirement_ids or not set(relation.source_workflow_ids) <= workflow_ids:
                raise ValueError(f"Relation {relation.relation_id} has unresolved source citations.")
        if relation.status != "NOT_ANNOTATED":
            normalized["relation_registry"][index]["reviewer_id"] = parsed.reviewer_id
            normalized["relation_registry"][index]["annotated_at"] = now
            normalized["relation_registry"][index]["resolved_source_refs"] = _resolved_refs(
                raw, relation.source_requirement_ids, relation.source_workflow_ids
            )

    annotation_hash = _canonical_sha256(normalized)
    lock = {
        "protocol_version": BLIND_PROTOCOL_VERSION,
        "case_id": raw["case_id"],
        "source_bundle_sha256": expected_source_hash,
        "source_package_manifest_sha256": package_info["manifest_sha256"],
        "annotation_sha256": annotation_hash,
        "reviewer_id": parsed.reviewer_id,
        "locked_at": now,
        "integrity_status": "LOCKED_HASH_VERIFIED",
        "identity_status": "REVIEWER_ID_SELF_REPORTED",
        "exposure_status": "NO_PRIOR_MODEL_OUTPUT_EXPOSURE_SELF_REPORTED",
    }
    lock["lock_sha256"] = _canonical_sha256(lock)
    return {"annotation": normalized, "lock": lock}


def verify_blind_annotation_lock(
    raw: dict,
    locked_bundle: dict | None,
    *,
    source_package_root: Path | None = None,
) -> bool:
    if not isinstance(locked_bundle, dict):
        return False
    annotation = locked_bundle.get("annotation")
    lock = locked_bundle.get("lock")
    if not isinstance(annotation, dict) or not isinstance(lock, dict):
        return False
    try:
        recomputed = lock_blind_annotation(
            raw,
            annotation,
            locked_at=lock.get("locked_at"),
            source_package_root=source_package_root,
        )
    except (TypeError, ValueError, ValidationError, OSError):
        return False
    return recomputed == locked_bundle
