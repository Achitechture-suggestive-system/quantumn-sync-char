"""Local run snapshots and downloadable exports."""

from __future__ import annotations

import io
import json
import os
import re
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4


ARTIFACT_ROOT = Path(__file__).resolve().parent.parent / "runs"


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


def make_export_zip(artifacts: dict[str, Any], extra: dict[str, Any] | None = None) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, payload in artifacts.items():
            archive.writestr(
                f"{name}.json",
                json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            )
        for name, payload in (extra or {}).items():
            parts = name.replace("\\", "/").split("/")
            safe_name = (
                "/".join(parts)
                if all(part not in {"", ".", ".."} and re.fullmatch(r"[a-zA-Z0-9_.-]+", part) for part in parts)
                else re.sub(r"[^a-zA-Z0-9_.-]", "_", name)
            )
            archive.writestr(safe_name, json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    return buffer.getvalue()
