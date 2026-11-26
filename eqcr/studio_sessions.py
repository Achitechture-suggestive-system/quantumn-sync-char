"""Immutable Studio checkpoints for model revisions and evidence decisions."""

from __future__ import annotations

from datetime import datetime, timezone
import json
from uuid import UUID, uuid4

from . import storage
from .quantum_tradeoff import Architecture


def save_checkpoint(architecture: Architecture, *, event: dict, parent: str | None = None,
                    proposals: list[dict] | None = None, view: dict | None = None) -> str:
    identifier = f"checkpoint-{uuid4().hex}"
    storage._write_json(storage.ARTIFACT_ROOT / "quantum-studio" / "checkpoints" / f"{identifier}.json", {
        "schema": "STUDIO-CHECKPOINT@1", "id": identifier, "parent": parent,
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "architecture": architecture.model_dump(mode="json"), "event": event, "proposals": proposals or [], "view": view or {},
    })
    return identifier


def checkpoints() -> list[dict]:
    directory = storage.ARTIFACT_ROOT / "quantum-studio" / "checkpoints"
    result = []
    for path in sorted(directory.glob("checkpoint-*.json"), key=lambda path: path.stat().st_mtime, reverse=True):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if data.get("schema") == "STUDIO-CHECKPOINT@1":
                result.append({"id": path.stem, "recorded_at": data["recorded_at"], "action": data["event"].get("action", "SAVE")})
        except (OSError, ValueError, KeyError, TypeError):
            continue
    return result


def load_checkpoint(identifier: str) -> dict:
    if not identifier.startswith("checkpoint-") or len(identifier) != 43:
        raise ValueError("Checkpoint ID không hợp lệ.")
    try:
        checkpoint_uuid = UUID(identifier[11:])
    except ValueError as exc:
        raise ValueError("Checkpoint ID không hợp lệ.") from exc
    if checkpoint_uuid.hex != identifier[11:]:
        raise ValueError("Checkpoint ID không hợp lệ.")
    data = json.loads((storage.ARTIFACT_ROOT / "quantum-studio" / "checkpoints" / f"{identifier}.json").read_text(encoding="utf-8"))
    if data.get("schema") != "STUDIO-CHECKPOINT@1" or data.get("id") != identifier:
        raise ValueError("Checkpoint schema hoặc ID không khớp.")
    Architecture.model_validate(data["architecture"])
    decision = data.get("event", {})
    if decision.get("applied"):
        for proposal in data.get("proposals", []):
            if proposal["id"] == decision.get("proposal_id") and "applied" not in proposal:
                proposal["applied"] = decision["applied"]
    return data


def invalidate_changed_sources(before: Architecture, after: Architecture) -> Architecture:
    previous = {item.id: item.input_digest() for item in before.requirements}
    data = after.model_dump(mode="json")
    for item, raw in zip(after.requirements, data["requirements"], strict=True):
        if item.id in previous and previous[item.id] != item.input_digest():
            raw["quality_allocations"] = []
    return Architecture.model_validate(data)
