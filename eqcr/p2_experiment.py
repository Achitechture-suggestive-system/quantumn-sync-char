"""Preflight, structural evaluation, and reproducibility export for real P2 runs."""

from __future__ import annotations

import hashlib
import importlib.metadata
import json
import platform
import subprocess
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from .ollama import (
    PROMPT_VERSION,
    get_ollama_version,
    list_model_details,
    propose_responsibilities,
)
from .p2_protocol import source_bundle_sha256, verify_blind_annotation_lock
from .p2_reviewer_package import SourceOnlyPackageError, validate_source_only_reviewer_package
from .tutor_support import get_tutor_support_fixture


EXPERIMENT_PROTOCOL_VERSION = "P2-EXPERIMENT-RUN-v1"
EXPECTED_MODEL = "qwen3:4b"


class P2ExperimentError(RuntimeError):
    pass


class P2IndependentAnnotationBlocked(P2ExperimentError):
    status = "P2_BLOCKED_INDEPENDENT_ANNOTATION"


def _canonical_json_bytes(payload: Any) -> bytes:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _sha256(payload: Any) -> str:
    return hashlib.sha256(_canonical_json_bytes(payload)).hexdigest()


def _parse_time(value: Any, name: str) -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise P2ExperimentError(f"Proposal bundle is missing {name}.")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise P2ExperimentError(f"Proposal bundle has invalid {name}.") from exc
    if parsed.tzinfo is None:
        raise P2ExperimentError(f"Proposal bundle {name} must include a timezone.")
    return parsed


def p2_readiness_status(
    raw: dict[str, Any],
    lock_bundle: dict[str, Any] | None,
    *,
    source_package_root: Path | None = None,
) -> dict[str, str]:
    """Return an explicit blocker unless an unexposed source-only annotation is hash-locked."""
    if not verify_blind_annotation_lock(raw, lock_bundle, source_package_root=source_package_root):
        return {
            "status": P2IndependentAnnotationBlocked.status,
            "reason": "No verified source-only lock is available for this exact case and source hash.",
        }
    annotation = lock_bundle["annotation"]
    if not annotation.get("no_prior_model_output_exposure"):
        return {
            "status": P2IndependentAnnotationBlocked.status,
            "reason": "The reviewer did not attest to having no prior model-output exposure for this case.",
        }
    return {
        "status": "P2_READY_FOR_LOCAL_MODEL_PROPOSAL",
        "reason": "A source-only annotation lock is bound to this case and precedes model inference.",
    }


def validate_p2_proposal_bundle(
    raw: dict[str, Any],
    proposal_bundle: dict[str, Any],
    *,
    allow_test_only: bool = False,
    source_package_root: Path | None = None,
) -> None:
    if raw.get("case_id") != "TUTOR-SUPPORT-P2-01":
        raise P2ExperimentError("P2 experiment validation is restricted to the prepared Tutor Support case.")
    lock_bundle = proposal_bundle.get("blind_annotation_lock")
    readiness = p2_readiness_status(raw, lock_bundle, source_package_root=source_package_root)
    if readiness["status"] != "P2_READY_FOR_LOCAL_MODEL_PROPOSAL":
        raise P2IndependentAnnotationBlocked(readiness["reason"])
    if proposal_bundle.get("input_sha256") != source_bundle_sha256(raw):
        raise P2ExperimentError("Proposal bundle is not bound to the exact frozen Tutor source package.")
    if proposal_bundle.get("prompt_version") != PROMPT_VERSION:
        raise P2ExperimentError(f"Expected prompt/schema version {PROMPT_VERSION}.")
    provenance = proposal_bundle.get("provenance")
    if provenance != "LOCAL_OLLAMA_UNVERIFIED" and not (allow_test_only and provenance == "TEST_ONLY_NOT_MODEL_OUTPUT"):
        raise P2ExperimentError("Proposal bundle provenance is not an actual local Ollama proposal.")
    model = proposal_bundle.get("model")
    if not isinstance(model, str) or not model.strip():
        raise P2ExperimentError("Proposal bundle has no model tag.")
    if model != EXPECTED_MODEL:
        raise P2ExperimentError(f"P2 experiment results must use exact model tag {EXPECTED_MODEL}.")
    if proposal_bundle.get("raw_response") is not None:
        actual_response_hash = hashlib.sha256(str(proposal_bundle["raw_response"]).encode("utf-8")).hexdigest()
        if proposal_bundle.get("raw_response_sha256") != actual_response_hash:
            raise P2ExperimentError("Raw model response hash does not match the stored response text.")
    locked_at = _parse_time(lock_bundle["lock"].get("locked_at"), "blind-lock timestamp")
    inference_started = _parse_time(proposal_bundle.get("inference_started_at_utc"), "inference start timestamp")
    inference_completed = _parse_time(proposal_bundle.get("inference_completed_at_utc"), "inference completion timestamp")
    if not locked_at <= inference_started <= inference_completed:
        raise P2ExperimentError("Blind annotation must be locked before the recorded inference interval.")


def _expected_fr_refs(raw: dict[str, Any], ids: Any) -> list[dict[str, Any]] | None:
    if not isinstance(ids, list) or any(not isinstance(value, str) for value in ids):
        return None
    by_id = {item["id"]: item["source_ref"] for item in raw["requirements"]}
    if not ids or len(ids) != len(set(ids)) or not set(ids) <= set(by_id):
        return None
    return [by_id[value] for value in ids]


def evaluate_p2_structure(raw: dict[str, Any], proposal_bundle: dict[str, Any]) -> dict[str, Any]:
    """Measure deterministic ID/span properties; never infer semantic correctness."""
    if not isinstance(raw, dict) or not isinstance(raw.get("requirements"), list):
        raise P2ExperimentError("Frozen raw requirements must be a JSON object with a requirements array.")
    if any(
        not isinstance(item, dict) or not isinstance(item.get("id"), str)
        for item in raw["requirements"]
    ):
        raise P2ExperimentError("Every raw requirement must be a JSON object with a string ID.")
    if not isinstance(proposal_bundle, dict):
        raise P2ExperimentError("Proposal bundle must be a JSON object.")
    requirements = {item["id"]: item for item in raw["requirements"]}
    proposals = proposal_bundle.get("proposals", [])
    evidence = proposal_bundle.get("evidence_proposals", [])
    boundaries = proposal_bundle.get("boundary_hypotheses", [])
    normalized = proposal_bundle.get("normalized_requirements", [])
    if not all(isinstance(rows, list) for rows in (proposals, evidence, boundaries, normalized)):
        raise P2ExperimentError("Proposal, relation, and boundary outputs must be JSON arrays.")
    if any(
        not isinstance(item, dict)
        for rows in (proposals, evidence, boundaries, normalized)
        for item in rows
    ):
        raise P2ExperimentError("Every proposal, relation, boundary, and normalized requirement row must be a JSON object.")

    def string_values(values: Any) -> tuple[str, ...]:
        if not isinstance(values, list):
            return ()
        return tuple(sorted(value for value in values if isinstance(value, str)))

    errors: list[dict[str, Any]] = []
    citation_total = 0
    citation_resolved = 0
    coverage: dict[str, int] = {requirement_id: 0 for requirement_id in requirements}
    responsibility_shapes = [
        (
            string_values(item.get("requirement_ids", [])),
            str(item.get("name", "")).strip().casefold(),
            str(item.get("activity", "")).strip().casefold(),
            str(item.get("operation", "")).strip().casefold(),
        )
        for item in proposals
    ]
    shape_counts = {shape: responsibility_shapes.count(shape) for shape in set(responsibility_shapes)}
    model_ids = [item.get("model_proposal_id") for item in proposals]
    duplicate_model_ids = {value for value in model_ids if isinstance(value, str) and model_ids.count(value) > 1}

    for proposal_index, proposal in enumerate(proposals):
        proposal_id = str(proposal.get("id", ""))
        ids = proposal.get("requirement_ids", [])
        refs = proposal.get("source_refs", [])
        expected_refs = _expected_fr_refs(raw, ids)
        citation_total += len(ids) if isinstance(ids, list) else 0
        if isinstance(ids, list):
            valid_requirement_ids = {
                value for value in ids if isinstance(value, str) and value in requirements
            }
            for requirement_id in valid_requirement_ids:
                coverage[requirement_id] += 1
        if expected_refs is not None and refs == expected_refs:
            citation_resolved += len(ids)
        else:
            errors.append({"type": "RESPONSIBILITY_CITATION_INVALID", "proposal_id": proposal_id})
        if not isinstance(ids, list) or not ids:
            errors.append({"type": "RESPONSIBILITY_REQUIREMENT_SET_INVALID", "proposal_id": proposal_id})
        elif any(not isinstance(value, str) for value in ids):
            errors.append({"type": "RESPONSIBILITY_REQUIREMENT_ID_INVALID_TYPE", "proposal_id": proposal_id})
        duplicate_requirement_ids = isinstance(ids, list) and all(isinstance(value, str) for value in ids) and len(ids) != len(set(ids))
        if duplicate_requirement_ids:
            errors.append({"type": "RESPONSIBILITY_DUPLICATE_REQUIREMENT_ID", "proposal_id": proposal_id})
        if any(requirement_id not in requirements for requirement_id in ids if isinstance(requirement_id, str)):
            errors.append({"type": "RESPONSIBILITY_UNKNOWN_REQUIREMENT_ID", "proposal_id": proposal_id})
        if shape_counts[responsibility_shapes[proposal_index]] > 1:
            errors.append({"type": "RESPONSIBILITY_DUPLICATE_SHAPE", "proposal_id": proposal_id})
        model_id = proposal.get("model_proposal_id")
        if not isinstance(model_id, str) or not model_id.strip():
            errors.append({"type": "MODEL_PROPOSAL_ID_MISSING", "proposal_id": proposal_id})
        elif model_id in duplicate_model_ids:
            errors.append({"type": "MODEL_PROPOSAL_ID_DUPLICATE", "proposal_id": proposal_id})

    for item in normalized:
        source_ref = item.get("source_ref")
        citation_total += 1
        requirement_id = item.get("id")
        requirement = requirements.get(requirement_id) if isinstance(requirement_id, str) else None
        if requirement is not None and source_ref == requirement["source_ref"]:
            citation_resolved += 1
        else:
            errors.append({"type": "NORMALIZED_REQUIREMENT_CITATION_INVALID", "proposal_id": str(item.get("id", ""))})

    relation_shapes: dict[tuple[str, str, str], list[dict[str, Any]]] = {}
    relation_model_ids = [item.get("model_proposal_id") for item in evidence]
    duplicate_relation_model_ids = {
        value for value in relation_model_ids if isinstance(value, str) and relation_model_ids.count(value) > 1
    }
    allowed_predicates = {"BUSINESS_PRECEDES", "SHARES_STATE_OR_INVARIANT", "REQUIRES_INDEPENDENT_CHANGE"}
    for relation in evidence:
        proposal_id = str(relation.get("id", ""))
        subject = relation.get("subject_requirement_id")
        predicate = str(relation.get("predicate", "")).upper()
        object_id = relation.get("object_requirement_id")
        source_ids = relation.get("source_requirement_ids", [])
        refs = relation.get("source_refs", [])
        expected_refs = _expected_fr_refs(raw, source_ids)
        citation_total += len(source_ids) if isinstance(source_ids, list) else 0
        if expected_refs is not None and refs == expected_refs:
            citation_resolved += len(source_ids)
        else:
            errors.append({"type": "RELATION_CITATION_INVALID", "proposal_id": proposal_id})
        if predicate not in allowed_predicates:
            errors.append({"type": "RELATION_PREDICATE_UNREGISTERED", "proposal_id": proposal_id})
        model_id = relation.get("model_proposal_id")
        if not isinstance(model_id, str) or not model_id.strip():
            errors.append({"type": "RELATION_MODEL_PROPOSAL_ID_MISSING", "proposal_id": proposal_id})
        elif model_id in duplicate_relation_model_ids:
            errors.append({"type": "RELATION_MODEL_PROPOSAL_ID_DUPLICATE", "proposal_id": proposal_id})
        subject_is_known = isinstance(subject, str) and subject in requirements
        object_is_known = isinstance(object_id, str) and object_id in requirements
        if not subject_is_known or not object_is_known:
            errors.append({"type": "RELATION_ENDPOINT_UNKNOWN", "proposal_id": proposal_id})
        if subject == object_id:
            errors.append({"type": "RELATION_REFLEXIVE", "proposal_id": proposal_id})
        source_requirement_ids = {
            value for value in source_ids if isinstance(value, str)
        } if isinstance(source_ids, list) else set()
        if isinstance(source_ids, list) and any(not isinstance(value, str) for value in source_ids):
            errors.append({"type": "RELATION_SOURCE_ID_INVALID_TYPE", "proposal_id": proposal_id})
        if (
            relation.get("proposed_status") == "PRESENT"
            and subject_is_known
            and object_is_known
            and not {subject, object_id} <= source_requirement_ids
        ):
            errors.append({"type": "RELATION_PRESENT_ENDPOINT_NOT_CITED", "proposal_id": proposal_id})
        canonical_subject, canonical_object = subject, object_id
        if predicate != "BUSINESS_PRECEDES" and isinstance(subject, str) and isinstance(object_id, str):
            canonical_subject, canonical_object = sorted((subject, object_id))
        relation_shapes.setdefault((str(canonical_subject), predicate, str(canonical_object)), []).append(relation)
    for rows in relation_shapes.values():
        if len(rows) > 1:
            errors.extend({"type": "RELATION_DUPLICATE_OR_STATUS_CONFLICT", "proposal_id": str(item.get("id", ""))} for item in rows)

    boundary_shapes = [
        string_values(item.get("requirement_ids", []))
        for item in boundaries
    ]
    boundary_shape_counts = {shape: boundary_shapes.count(shape) for shape in set(boundary_shapes)}
    boundary_model_ids = [item.get("model_proposal_id") for item in boundaries]
    duplicate_boundary_model_ids = {
        value for value in boundary_model_ids if isinstance(value, str) and boundary_model_ids.count(value) > 1
    }
    for boundary_index, boundary in enumerate(boundaries):
        proposal_id = str(boundary.get("id", ""))
        ids = boundary.get("requirement_ids", [])
        source_ids = boundary.get("source_requirement_ids", [])
        refs = boundary.get("source_refs", [])
        expected_refs = _expected_fr_refs(raw, source_ids)
        citation_total += len(source_ids) if isinstance(source_ids, list) else 0
        if expected_refs is not None and refs == expected_refs:
            citation_resolved += len(source_ids)
        else:
            errors.append({"type": "BOUNDARY_CITATION_INVALID", "proposal_id": proposal_id})
        valid_ids = isinstance(ids, list) and all(
            isinstance(value, str) and value in requirements for value in ids
        )
        if not isinstance(ids, list) or len(ids) < 2 or not valid_ids:
            errors.append({"type": "BOUNDARY_REQUIREMENT_SET_INVALID", "proposal_id": proposal_id})
        source_requirement_ids = {
            value for value in source_ids if isinstance(value, str)
        } if isinstance(source_ids, list) else set()
        if isinstance(source_ids, list) and any(not isinstance(value, str) for value in source_ids):
            errors.append({"type": "BOUNDARY_SOURCE_ID_INVALID_TYPE", "proposal_id": proposal_id})
        if valid_ids and not set(ids) <= source_requirement_ids:
            errors.append({"type": "BOUNDARY_SOURCE_COVERAGE_MISSING", "proposal_id": proposal_id})
        if boundary_shape_counts[boundary_shapes[boundary_index]] > 1:
            errors.append({"type": "BOUNDARY_DUPLICATE_HYPOTHESIS", "proposal_id": proposal_id})
        model_id = boundary.get("model_proposal_id")
        if not isinstance(model_id, str) or not model_id.strip():
            errors.append({"type": "BOUNDARY_MODEL_PROPOSAL_ID_MISSING", "proposal_id": proposal_id})
        elif model_id in duplicate_boundary_model_ids:
            errors.append({"type": "BOUNDARY_MODEL_PROPOSAL_ID_DUPLICATE", "proposal_id": proposal_id})

    uncovered = sorted(requirement_id for requirement_id, count in coverage.items() if count == 0)
    lock_bundle = proposal_bundle.get("blind_annotation_lock")
    annotation = lock_bundle.get("annotation") if isinstance(lock_bundle, dict) else None
    unresolved_ids = annotation.get("unresolved_requirement_ids", []) if isinstance(annotation, dict) else []
    source_only_unresolved = sorted(
        value for value in unresolved_ids if isinstance(value, str)
    ) if isinstance(unresolved_ids, list) else []
    error_counts: dict[str, int] = {}
    for error in errors:
        error_counts[error["type"]] = error_counts.get(error["type"], 0) + 1
    return {
        "provenance": "DETERMINISTIC_TRANSFORMATION",
        "verification_status": "STRUCTURAL_ONLY_NOT_SEMANTIC",
        "case_id": raw["case_id"],
        "source_bundle_sha256": source_bundle_sha256(raw),
        "responsibility_mapping": {
            "proposal_count": len(proposals),
            "coverage_by_requirement": coverage,
            "proposal_uncovered_requirement_ids": uncovered,
            "source_only_unresolved_requirement_ids": source_only_unresolved,
            "interpretation": (
                "Counts structurally valid FR IDs in responsibility proposals independently of citation validity; "
                "this is not a semantic correctness measure."
            ),
        },
        "citation_audit": {
            "requirement_citations_resolved_to_exact_source_ref": citation_resolved,
            "requirement_citation_count": citation_total,
            "exact_source_ref_resolution_rate": citation_resolved / citation_total if citation_total else None,
            "interpretation": "Exact ID/span resolution only; it does not establish entailment or semantic correctness.",
        },
        "relation_audit": {
            "proposal_count": len(evidence),
            "proposed_status_counts": {
                status: sum(item.get("proposed_status") == status for item in evidence)
                for status in ("PRESENT", "UNKNOWN", "SCOPED_ABSENT")
            },
        },
        "normalized_requirement_count": len(normalized),
        "boundary_hypothesis_count": len(boundaries),
        "error_count": len(errors),
        "error_counts_by_type": error_counts,
        "errors": errors,
        "semantic_evaluation": {
            "status": "NOT_MEASURED_NO_ADJUDICATED_REFERENCE",
            "metrics": None,
            "reason": "No independently adjudicated reference set and matching decisions were supplied.",
        },
    }


def _git_metadata(repo_root: Path) -> dict[str, Any]:
    try:
        revision = subprocess.run(
            ["git", "-C", str(repo_root), "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
        status = subprocess.run(
            ["git", "-C", str(repo_root), "status", "--porcelain"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout
    except (OSError, subprocess.CalledProcessError):
        return {"revision": None, "working_tree_clean": None}
    return {"revision": revision, "working_tree_clean": not bool(status.strip())}


def _package_versions() -> dict[str, str | None]:
    result = {}
    for package in ("pydantic", "networkx", "streamlit", "pytest"):
        try:
            result[package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            result[package] = None
    return result


def _write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def export_p2_proposal_run(
    raw: dict[str, Any],
    lock_bundle: dict[str, Any],
    proposal_bundle: dict[str, Any],
    structural_evaluation: dict[str, Any],
    *,
    output_root: Path,
    repo_root: Path,
    ollama_version: str,
    model_metadata: dict[str, Any],
    allow_test_only: bool = False,
    source_package_root: Path | None = None,
) -> Path:
    validate_p2_proposal_bundle(
        raw,
        proposal_bundle,
        allow_test_only=allow_test_only,
        source_package_root=source_package_root,
    )
    if not verify_blind_annotation_lock(raw, lock_bundle, source_package_root=source_package_root):
        raise P2IndependentAnnotationBlocked("A verified source-only lock is required for a P2 result export.")
    package_validation = validate_source_only_reviewer_package(raw, source_package_root)
    proposal_lock = proposal_bundle.get("blind_annotation_lock", {})
    if proposal_lock.get("lock", {}).get("lock_sha256") != lock_bundle.get("lock", {}).get("lock_sha256"):
        raise P2ExperimentError("Export annotation lock differs from the checkpoint attached to model proposals.")
    if structural_evaluation.get("source_bundle_sha256") != source_bundle_sha256(raw):
        raise P2ExperimentError("Structural evaluation is bound to a different source package.")
    now = datetime.now(timezone.utc)
    run_id = f"p2-{now.strftime('%Y%m%dT%H%M%S%fZ')}-{uuid4().hex[:8]}"
    run_dir = output_root / run_id
    run_dir.mkdir(parents=True, exist_ok=False)
    payloads = {
        "raw_requirements.json": raw,
        "blind_annotation_lock.json": lock_bundle,
        "ollama_proposals.json": proposal_bundle,
        "structural_evaluation.json": structural_evaluation,
    }
    for filename, payload in payloads.items():
        _write_json(run_dir / filename, payload)
    hashes = {
        filename: hashlib.sha256((run_dir / filename).read_bytes()).hexdigest()
        for filename in payloads
    }
    git_info = _git_metadata(repo_root)
    manifest = {
        "manifest_version": EXPERIMENT_PROTOCOL_VERSION,
        "run_id": run_id,
        "case_id": raw["case_id"],
        "experiment_status": "P2_MODEL_PROPOSAL_COMPLETE_PENDING_HUMAN_REVIEW",
        "created_at_utc": now.isoformat(),
        "source_bundle_sha256": source_bundle_sha256(raw),
        "source_package_manifest_sha256": package_validation["manifest_sha256"],
        "source_package_file_sha256": package_validation["file_sha256"],
        "annotation_sha256": lock_bundle["lock"]["annotation_sha256"],
        "model_tag_requested": proposal_bundle["model"],
        "response_model": proposal_bundle.get("response_model"),
        "local_model_metadata": model_metadata,
        "ollama_version": ollama_version,
        "prompt_version": proposal_bundle["prompt_version"],
        "output_schema_sha256": _sha256(proposal_bundle.get("output_schema", {})),
        "generation_parameters": proposal_bundle["generation_parameters"],
        "raw_response_sha256": proposal_bundle.get("raw_response_sha256"),
        "inference_started_at_utc": proposal_bundle["inference_started_at_utc"],
        "inference_completed_at_utc": proposal_bundle["inference_completed_at_utc"],
        "python_version": sys.version,
        "platform": platform.platform(),
        "package_versions": _package_versions(),
        "git": git_info,
        "artifact_sha256": hashes,
        "semantic_evaluation_status": structural_evaluation["semantic_evaluation"]["status"],
        "provenance_note": "LLM proposals remain untrusted; structural evaluation is deterministic and is not a semantic score.",
    }
    _write_json(run_dir / "manifest.json", manifest)
    checksum_map = {
        path.name: hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(run_dir.glob("*.json"))
        if path.name != "checksums.sha256.json"
    }
    _write_json(run_dir / "checksums.sha256.json", checksum_map)
    zip_path = run_dir / f"{run_id}-reproducibility.zip"
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(run_dir.glob("*.json")):
            archive.write(path, arcname=path.name)
    return run_dir


def run_local_tutor_proposal_experiment(
    lock_bundle: dict[str, Any],
    *,
    model: str = EXPECTED_MODEL,
    output_root: Path,
    repo_root: Path,
    source_package_root: Path | None = None,
) -> Path:
    fixture = get_tutor_support_fixture()
    raw = fixture["raw_requirements"]
    readiness = p2_readiness_status(raw, lock_bundle, source_package_root=source_package_root)
    if readiness["status"] != "P2_READY_FOR_LOCAL_MODEL_PROPOSAL":
        raise P2IndependentAnnotationBlocked(readiness["reason"])
    try:
        validate_source_only_reviewer_package(raw, source_package_root)
    except SourceOnlyPackageError as exc:
        raise P2ExperimentError(f"Source-only reviewer package validation failed: {exc}") from exc
    if model != EXPECTED_MODEL:
        raise P2ExperimentError(f"P2 comparison is registered for exact local model tag {EXPECTED_MODEL}.")
    git_info = _git_metadata(repo_root)
    if git_info["working_tree_clean"] is not True:
        raise P2ExperimentError("Commit the experiment code and use a clean checkout before a reproducible model run.")
    models = list_model_details()
    model_metadata = next((item for item in models if item.get("name") == model), None)
    if model_metadata is None:
        raise P2ExperimentError(f"Exact local model tag {model} is not installed; no inference was started.")
    ollama_version = get_ollama_version()
    proposal_bundle = propose_responsibilities(
        raw,
        model,
        blind_annotation_lock=lock_bundle,
        source_package_root=source_package_root,
    )
    validate_p2_proposal_bundle(raw, proposal_bundle, source_package_root=source_package_root)
    evaluation = evaluate_p2_structure(raw, proposal_bundle)
    return export_p2_proposal_run(
        raw,
        lock_bundle,
        proposal_bundle,
        evaluation,
        output_root=output_root,
        repo_root=repo_root,
        ollama_version=ollama_version,
        model_metadata=model_metadata,
        source_package_root=source_package_root,
    )
