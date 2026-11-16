"""Local run snapshots and downloadable exports."""

from __future__ import annotations

import io
import hashlib
import importlib.metadata
import json
import os
import platform
import re
import subprocess
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4


ARTIFACT_ROOT = Path(__file__).resolve().parent.parent / "runs"
BUNDLE_MANIFEST_NAME = "reproducibility_manifest.json"
BUNDLE_CHECKSUMS_NAME = "checksums.sha256.json"
BUNDLE_MANIFEST_VERSION = "EQCR-REPRODUCIBILITY-BUNDLE@1.0.0"


def new_run_id() -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"run-{stamp}-{uuid4().hex[:8]}"


def _run_dir(run_id: str, root: Path = ARTIFACT_ROOT) -> Path:
    if not re.fullmatch(r"run-[A-Za-z0-9T_-]+", run_id):
        raise ValueError("Invalid run ID.")
    return root / run_id


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def save_run(run_id: str, artifacts: dict[str, Any], *, root: Path = ARTIFACT_ROOT) -> Path:
    run_dir = _run_dir(run_id, root)
    for name, payload in artifacts.items():
        if not re.fullmatch(r"[a-z][a-z0-9_]*", name):
            raise ValueError(f"Invalid artifact name: {name}")
        _write_json(run_dir / f"{name}.json", payload)
    return run_dir


def save_snapshot(
    run_id: str,
    version: str,
    artifacts: dict[str, Any],
    *,
    root: Path = ARTIFACT_ROOT,
) -> Path:
    if not re.fullmatch(r"v\d+", version):
        raise ValueError("Snapshot version must look like v1.")
    path = _run_dir(run_id, root) / "snapshots" / f"{version}.json"
    _write_json(path, artifacts)
    return path


def list_snapshots(run_id: str, *, root: Path = ARTIFACT_ROOT) -> list[str]:
    snapshot_dir = _run_dir(run_id, root) / "snapshots"
    if not snapshot_dir.exists():
        return []
    return sorted(
        (path.stem for path in snapshot_dir.glob("v*.json") if re.fullmatch(r"v\d+", path.stem)),
        key=lambda version: int(version[1:]),
    )


def load_snapshot(run_id: str, version: str, *, root: Path = ARTIFACT_ROOT) -> dict[str, Any]:
    if not re.fullmatch(r"v\d+", version):
        raise ValueError("Snapshot version must look like v1.")
    path = _run_dir(run_id, root) / "snapshots" / f"{version}.json"
    return json.loads(path.read_text(encoding="utf-8"))


def _json_bytes(payload: Any) -> bytes:
    return (json.dumps(payload, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def _canonical_sha256(payload: Any) -> str:
    canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _runtime_versions() -> dict[str, str | None]:
    versions: dict[str, str | None] = {"python": sys.version, "platform": platform.platform()}
    for package in ("pydantic", "networkx", "ortools", "streamlit"):
        try:
            versions[package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            versions[package] = None
    return versions


def _git_snapshot() -> dict[str, Any]:
    repo_root = Path(__file__).resolve().parents[1]
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


def _provenance_summary(artifacts: dict[str, Any]) -> dict[str, Any]:
    def counts(rows: Any, field: str) -> dict[str, int]:
        if not isinstance(rows, list):
            return {}
        values = [str(item.get(field) or "UNSPECIFIED") for item in rows if isinstance(item, dict)]
        return {value: values.count(value) for value in sorted(set(values))}

    raw = artifacts.get("raw_requirements", {})
    raw_provenance = "SOURCE_REQUIREMENTS" if raw else "MISSING"
    return {
        "raw_requirements": raw_provenance,
        "context": artifacts.get("context", {}).get("provenance", "DETERMINISTIC_TRANSFORMATION"),
        "responsibilities": counts(artifacts.get("responsibilities", {}).get("items"), "provenance"),
        "relations": counts(artifacts.get("relation_registry", {}).get("items"), "provenance"),
        "evidence": counts(artifacts.get("evidence", {}).get("items"), "provenance"),
        "constraints": counts(artifacts.get("constraints", {}).get("items"), "origin"),
        "partitions": "DETERMINISTIC_TRANSFORMATION",
        "quanta": "DETERMINISTIC_TRANSFORMATION",
        "interactions": "DETERMINISTIC_TRANSFORMATION_AND_ARCHITECTURAL_POLICY",
        "quality_profiles": "DETERMINISTIC_TRANSFORMATION_WITH_FIELD_LEVEL_PROVENANCE",
        "decisions": counts(artifacts.get("decisions", {}).get("items"), "decision_type"),
        "revisions": counts(artifacts.get("revisions", {}).get("items"), "decision_type"),
        "fixture_label": artifacts.get("metadata", {}).get("fixture_label"),
    }


def _build_bundle_manifest(artifacts: dict[str, Any], member_hashes: dict[str, str]) -> dict[str, Any]:
    raw = artifacts.get("raw_requirements", {})
    source_refs = [
        item.get("source_ref")
        for group in ("requirements", "workflows", "scenarios")
        for item in raw.get(group, [])
        if isinstance(item, dict) and isinstance(item.get("source_ref"), dict)
    ]
    proposal = artifacts.get("ollama_proposals", {})
    lock = proposal.get("blind_annotation_lock", {}) if isinstance(proposal, dict) else {}
    lock_metadata = lock.get("lock", {}) if isinstance(lock, dict) else {}
    partition = artifacts.get("partitions", {})
    solver_keys = (
        "solver_backend",
        "solver_version",
        "random_seed",
        "num_search_workers",
        "time_limit_seconds",
        "max_optimal_candidates",
        "objective_definition",
        "objective_minimum",
        "optimal_candidate_set_complete",
        "selection_policy",
    )
    optimizer = {key: partition[key] for key in solver_keys if key in partition}
    optimizer.setdefault(
        "solver_backend",
        artifacts.get("metadata", {}).get("optimizer_backend", "EXHAUSTIVE_ENUMERATOR"),
    )
    dependency_file = Path(__file__).resolve().parents[1] / "requirements.txt"
    dependency_sha256 = _sha256_bytes(dependency_file.read_bytes()) if dependency_file.is_file() else None
    return {
        "manifest_version": BUNDLE_MANIFEST_VERSION,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "case_id": raw.get("case_id"),
        "run_id": artifacts.get("metadata", {}).get("run_id"),
        "execution_mode": artifacts.get("metadata", {}).get("execution_mode"),
        "input_hashes": {
            "raw_requirements_sha256": _canonical_sha256(raw) if raw else None,
            "source_refs_sha256": _canonical_sha256(source_refs) if source_refs else None,
            "blind_annotation_sha256": lock_metadata.get("annotation_sha256"),
            "human_decisions_sha256": _canonical_sha256(artifacts.get("decisions", {}).get("items", [])),
            "human_revisions_sha256": _canonical_sha256(artifacts.get("revisions", {}).get("items", [])),
        },
        "source_package": {
            "version": raw.get("source_package_version"),
            "license_status": raw.get("source_license_status", "NOT_RECORDED"),
            "provenance_status": raw.get("source_provenance_status", "NOT_RECORDED"),
        },
        "dependency_manifest": {
            "file": "requirements.txt" if dependency_sha256 else None,
            "sha256": dependency_sha256,
        },
        "code": _git_snapshot(),
        "runtime": _runtime_versions(),
        "optimizer": optimizer,
        "model": {
            "provenance": proposal.get("provenance") if isinstance(proposal, dict) else None,
            "requested_tag": proposal.get("model") if isinstance(proposal, dict) else None,
            "response_model": proposal.get("response_model") if isinstance(proposal, dict) else None,
            "prompt_version": proposal.get("prompt_version") if isinstance(proposal, dict) else None,
            "raw_response_sha256": proposal.get("raw_response_sha256") if isinstance(proposal, dict) else None,
        },
        "provenance_summary": _provenance_summary(artifacts),
        "bundle_member_sha256": member_hashes,
        "ci_run_id": os.environ.get("GITHUB_RUN_ID"),
        "ci_run_attempt": os.environ.get("GITHUB_RUN_ATTEMPT"),
        "ci_status": "NOT_RECORDED" if not os.environ.get("GITHUB_RUN_ID") else "EXTERNAL_STATUS_NOT_QUERIED",
        "limitations": [
            "Hashes establish byte integrity, not semantic correctness or reviewer identity.",
            "Absent source-version, license, model, or CI metadata remains null or not recorded.",
            "Prepared fixture provenance remains distinct from local model proposals and human decisions.",
        ],
    }


def make_export_zip(artifacts: dict[str, Any], extra: dict[str, Any] | None = None) -> bytes:
    """Export run JSON with a versioned manifest and verifiable member checksums."""
    members: dict[str, bytes] = {}
    for name, payload in artifacts.items():
        if not re.fullmatch(r"[a-z][a-z0-9_]*", name):
            raise ValueError(f"Invalid artifact name: {name}")
        members[f"{name}.json"] = _json_bytes(payload)
    for name, payload in (extra or {}).items():
        parts = name.replace("\\", "/").split("/")
        safe_name = (
            "/".join(parts)
            if all(part not in {"", ".", ".."} and re.fullmatch(r"[a-zA-Z0-9_.-]+", part) for part in parts)
            else re.sub(r"[^a-zA-Z0-9_.-]", "_", name)
        )
        if safe_name in members or safe_name in {BUNDLE_MANIFEST_NAME, BUNDLE_CHECKSUMS_NAME}:
            raise ValueError(f"Duplicate or reserved export member name: {safe_name}")
        members[safe_name] = _json_bytes(payload)

    member_hashes = {name: _sha256_bytes(payload) for name, payload in sorted(members.items())}
    manifest = _build_bundle_manifest(artifacts, member_hashes)
    manifest_bytes = _json_bytes(manifest)
    members[BUNDLE_MANIFEST_NAME] = manifest_bytes
    checksum_map = {
        name: _sha256_bytes(payload)
        for name, payload in sorted(members.items())
    }
    checksum_bytes = _json_bytes(checksum_map)

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, payload in sorted(members.items()):
            archive.writestr(name, payload)
        archive.writestr(BUNDLE_CHECKSUMS_NAME, checksum_bytes)
    return buffer.getvalue()


def verify_export_zip(payload: bytes) -> dict[str, Any]:
    """Validate that an exported bundle's manifest and checksums cover every member."""
    try:
        with zipfile.ZipFile(io.BytesIO(payload), "r") as archive:
            names = archive.namelist()
            if len(names) != len(set(names)):
                raise ValueError("Artifact bundle contains duplicate member names.")
            if any(name.startswith(("/", "\\")) or ".." in name.replace("\\", "/").split("/") for name in names):
                raise ValueError("Artifact bundle contains an unsafe member path.")
            if BUNDLE_MANIFEST_NAME not in names or BUNDLE_CHECKSUMS_NAME not in names:
                raise ValueError("Artifact bundle is missing its manifest or checksum map.")
            manifest = json.loads(archive.read(BUNDLE_MANIFEST_NAME))
            checksum_map = json.loads(archive.read(BUNDLE_CHECKSUMS_NAME))
            if not isinstance(manifest, dict) or not isinstance(checksum_map, dict):
                raise ValueError("Artifact bundle manifest and checksum map must be JSON objects.")
            if manifest.get("manifest_version") != BUNDLE_MANIFEST_VERSION:
                raise ValueError("Artifact bundle manifest version is unsupported.")
            actual_names = set(names) - {BUNDLE_CHECKSUMS_NAME}
            if set(checksum_map) != actual_names:
                raise ValueError("Artifact bundle checksum map does not cover exactly its payload members.")
            actual_hashes = {
                name: _sha256_bytes(archive.read(name))
                for name in sorted(actual_names)
            }
            if actual_hashes != checksum_map:
                raise ValueError("Artifact bundle checksum verification failed.")
            payload_names = set(names) - {BUNDLE_MANIFEST_NAME, BUNDLE_CHECKSUMS_NAME}
            for name in payload_names:
                if not name.lower().endswith(".json"):
                    raise ValueError(f"Artifact bundle member is not JSON: {name}")
                try:
                    json.loads(archive.read(name))
                except json.JSONDecodeError as exc:
                    raise ValueError(f"Artifact bundle member is invalid JSON: {name}") from exc
            manifest_hashes = manifest.get("bundle_member_sha256")
            if not isinstance(manifest_hashes, dict) or set(manifest_hashes) != payload_names:
                raise ValueError("Artifact bundle manifest does not cover exactly its run artifacts.")
            if manifest_hashes != {
                name: actual_hashes[name] for name in sorted(payload_names)
            }:
                raise ValueError("Artifact bundle manifest hashes do not match its run artifacts.")
    except (OSError, zipfile.BadZipFile, json.JSONDecodeError, KeyError, TypeError, AttributeError) as exc:
        raise ValueError(f"Invalid artifact bundle: {exc}") from exc
    return {
        "status": "PASS",
        "manifest_version": manifest["manifest_version"],
        "case_id": manifest.get("case_id"),
        "run_id": manifest.get("run_id"),
        "verified_member_count": len(names),
        "manifest": manifest,
    }
