"""Human edits, audit records, and impact tracking for constraint revisions."""

from __future__ import annotations

import re
from copy import deepcopy
from typing import Any

from .impact import STEP_BY_ARTIFACT, impact_preview
from .traceability import refresh_traceability_artifact


CONSTRAINT_IMPACT = impact_preview("constraints")
IMPACTED_ARTIFACTS = ["constraints", *CONSTRAINT_IMPACT["stale_artifacts"], "decisions", "revisions"]
IMPACTED_STEPS = CONSTRAINT_IMPACT["affected_steps"]
RESPONSIBILITY_IMPACT = impact_preview("responsibilities")

REVIEW_COLLECTIONS = {
    "responsibilities": ("items", "id", "review_decision_status"),
    "evidence": ("items", "id", "review_status"),
    "quanta": ("quanta", "id", "review_status"),
    "interactions": ("edges", "id", "review_status"),
    "quality_profiles": ("profiles", "scenario_id", "review_status"),
}


def apply_artifact_review(
    artifacts: dict[str, Any],
    *,
    target_artifact: str,
    object_id: str,
    action: str,
    reason: str,
    source: str,
    actor: str,
) -> dict[str, Any]:
    """Record a human review outcome without rewriting engineering evidence or validation."""
    action = action.strip().upper()
    if action not in {"APPROVE", "REJECT", "DEFER"}:
        raise ValueError("Artifact review action must be Approve, Reject, or Defer; use the constraint form to revise.")
    if target_artifact not in REVIEW_COLLECTIONS:
        raise ValueError(f"Artifact {target_artifact!r} does not support review outcomes.")
    if not all(value.strip() for value in (object_id, reason, source, actor)):
        raise ValueError("Object ID, reason, source, and reviewer are required.")

    updated = deepcopy(artifacts)
    collection_name, id_field, status_field = REVIEW_COLLECTIONS[target_artifact]
    collection = updated[target_artifact][collection_name]
    item = next((candidate for candidate in collection if candidate.get(id_field) == object_id), None)
    if item is None:
        raise ValueError(f"{target_artifact} item {object_id} was not found.")
    new_status = {"APPROVE": "APPROVED", "REJECT": "REJECTED", "DEFER": "DEFERRED"}[action]
    old_status = item.get(status_field, "REVIEW_REQUIRED")
    if old_status == new_status:
        raise ValueError(f"{object_id} already has review status {new_status}.")
    item[status_field] = new_status

    decision_number = len(updated.get("decisions", {}).get("items", [])) + 1
    revision_number = len(updated.get("revisions", {}).get("items", [])) + 1
    step = STEP_BY_ARTIFACT[target_artifact]
    decision = {
        "decision_id": f"D{decision_number:02d}",
        "decision_type": "ARTIFACT_REVIEW",
        "target_step": step,
        "target_artifact": target_artifact,
        "object_id": object_id,
        "action": action,
        "old_value": old_status,
        "new_value": new_status,
        "reason": reason,
        "source": source,
        "actor": actor,
        "created_at_utc": None,
        "result": "RECORDED_NO_STRUCTURAL_CHANGE",
    }
    revision = {
        "revision_id": f"v{revision_number + 1}",
        "from_revision": f"v{revision_number}",
        "decision_id": decision["decision_id"],
        "target_step": step,
        "target_artifact": target_artifact,
        "object_id": object_id,
        "before": old_status,
        "after": new_status,
        "reason": reason,
        "source": source,
        "actor": actor,
        "affected_steps": [step, "09", "10"],
        "affected_artifacts": [target_artifact, "decisions", "revisions", "validation_report"],
        "unaffected_artifacts": sorted(
            set(STEP_BY_ARTIFACT) - {target_artifact, "decisions", "revisions", "validation_report"}
        ),
        "invalidated_artifacts": [],
        "stale_artifacts_before_revalidation": [],
        "recomputed_artifacts": [],
        "stale_artifacts_after_revalidation": [],
        "revalidation_status": artifacts["validation_report"]["status"],
    }
    updated["decisions"]["items"].append(decision)
    updated["revisions"]["items"].append(revision)
    counts = {name: 0 for name in ("APPROVED", "REJECTED", "DEFERRED")}
    for recorded in updated["decisions"]["items"]:
        if recorded.get("decision_type") == "ARTIFACT_REVIEW":
            value = recorded.get("new_value")
            if value in counts:
                counts[value] += 1
    updated["validation_report"]["review_decision_counts"] = counts
    diff = artifact_diff(artifacts, updated, exclude={"decisions", "revisions"})
    revision["changed_artifacts"] = sorted(set(diff["changed_artifacts"]) | {"decisions", "revisions"})
    revision["artifact_diff"] = diff["changes"]
    refresh_traceability_artifact(updated)
    return updated


def replay_artifact_review_decisions(artifacts: dict[str, Any]) -> dict[str, Any]:
    """Restore review-only statuses after a structural constraint recomputation."""
    updated = deepcopy(artifacts)
    counts = {name: 0 for name in ("APPROVED", "REJECTED", "DEFERRED")}
    for decision in updated.get("decisions", {}).get("items", []):
        if decision.get("decision_type") == "STRUCTURAL_REVISION" and decision.get("target_artifact") == "responsibilities":
            target = decision.get("object_id")
            item = next(
                (candidate for candidate in updated["responsibilities"]["items"] if candidate.get("id") == target),
                None,
            )
            if item is not None:
                item["review_decision_status"] = "REVIEW_REQUIRED"
            continue
        if decision.get("decision_type") != "ARTIFACT_REVIEW":
            continue
        target = decision.get("target_artifact")
        if target not in REVIEW_COLLECTIONS:
            continue
        collection_name, id_field, status_field = REVIEW_COLLECTIONS[target]
        item = next(
            (candidate for candidate in updated[target][collection_name] if candidate.get(id_field) == decision.get("object_id")),
            None,
        )
        if item is not None:
            item[status_field] = decision["new_value"]
        value = decision.get("new_value")
        if value in counts:
            counts[value] += 1
    updated["validation_report"]["review_decision_counts"] = counts
    refresh_traceability_artifact(updated)
    return updated


def _find_constraint(constraints: list[dict[str, Any]], constraint_id: str) -> dict[str, Any]:
    for item in constraints:
        if item["id"] == constraint_id:
            return item
    raise ValueError(f"Constraint {constraint_id} was not found.")


def apply_constraint_edit(
    artifacts: dict[str, Any],
    *,
    target_step: str,
    object_id: str,
    old_value: str,
    new_value: str,
    reason: str,
    source: str,
    actor: str,
) -> tuple[list[dict[str, Any]], dict[str, Any], dict[str, Any]]:
    """Apply a supported constraint edit and return constraints plus audit records."""
    if target_step not in {"04", "Constraint & Quality Reasoning", "constraints"}:
        raise ValueError("The P0 review form currently supports edits to step 04 constraints.")
    if not all(value.strip() for value in (object_id, new_value, reason, source, actor)):
        raise ValueError("Object ID, new value, reason, source, and reviewer are required.")

    constraints = deepcopy(artifacts["constraints"]["items"])
    before_list = deepcopy(constraints)
    normalized = new_value.strip().upper()
    if normalized.startswith("ADD "):
        match = re.fullmatch(r"ADD\s+(MUST_LINK|CANNOT_LINK)\(\s*(R[1-6])\s*,\s*(R[1-6])\s*\)", normalized)
        if not match:
            raise ValueError("Use ADD MUST_LINK(R4,R6) or ADD CANNOT_LINK(R4,R6).")
        relation, left, right = match.groups()
        if left == right:
            raise ValueError("A relation must connect two different responsibilities.")
        if any(c["id"] == object_id for c in constraints):
            raise ValueError(f"Constraint ID {object_id} already exists.")
        constraints.append(
            {
                "id": object_id,
                "relation": relation,
                "left": left,
                "right": right,
                "hardness": "HARD",
                "origin": "HUMAN_OVERRIDE",
                "enabled": True,
                "source_refs": [{"source_id": source, "quote": reason, "start": 0, "end": len(reason)}],
                "rationale": reason,
            }
        )
    elif normalized.startswith("DISABLE "):
        constraint_id = normalized.split(maxsplit=1)[1]
        constraint = _find_constraint(constraints, constraint_id)
        if object_id not in {constraint_id, "constraints"}:
            raise ValueError(f"Object ID {object_id} does not match {constraint_id}.")
        constraint["enabled"] = False
        constraint["origin"] = "HUMAN_OVERRIDE"
        constraint["rationale"] = reason
        constraint["source_refs"] = [{"source_id": source, "quote": reason, "start": 0, "end": len(reason)}]
    elif normalized.startswith("ENABLE "):
        constraint_id = normalized.split(maxsplit=1)[1]
        constraint = _find_constraint(constraints, constraint_id)
        if object_id not in {constraint_id, "constraints"}:
            raise ValueError(f"Object ID {object_id} does not match {constraint_id}.")
        constraint["enabled"] = True
        constraint["origin"] = "HUMAN_OVERRIDE"
        constraint["rationale"] = reason
        constraint["source_refs"] = [{"source_id": source, "quote": reason, "start": 0, "end": len(reason)}]
    elif normalized.startswith("REMOVE "):
        constraint_id = normalized.split(maxsplit=1)[1]
        if object_id != constraint_id:
            raise ValueError(f"Object ID {object_id} does not match {constraint_id}.")
        if not any(c["id"] == constraint_id for c in constraints):
            raise ValueError(f"Constraint {constraint_id} was not found.")
        constraints = [c for c in constraints if c["id"] != constraint_id]
    else:
        match = re.fullmatch(r"SET\s+(H[1-9]\d*)\s+(MUST_LINK|CANNOT_LINK)\(\s*(R[1-6])\s*,\s*(R[1-6])\s*\)", normalized)
        if not match:
            raise ValueError("Supported edits: ADD MUST_LINK(...), ADD CANNOT_LINK(...), SET H3 CANNOT_LINK(...), DISABLE H3, ENABLE H3, REMOVE H4.")
        constraint_id, relation, left, right = match.groups()
        if object_id != constraint_id:
            raise ValueError(f"Object ID {object_id} does not match {constraint_id}.")
        if left == right:
            raise ValueError("A relation must connect two different responsibilities.")
        constraint = _find_constraint(constraints, constraint_id)
        constraint.update(
            {
                "relation": relation,
                "left": left,
                "right": right,
                "origin": "HUMAN_OVERRIDE",
                "rationale": reason,
                "source_refs": [{"source_id": source, "quote": reason, "start": 0, "end": len(reason)}],
            }
        )

    changed = next((item for item in constraints if item["id"] == object_id), None)
    previous = next((item for item in before_list if item["id"] == object_id), None)
    old_recorded = "ABSENT" if previous is None else deepcopy(previous)
    new_recorded = new_value.strip()
    if previous is not None and changed is not None and previous == changed:
        raise ValueError(f"The requested change leaves {object_id} unchanged.")

    decision_number = len(artifacts.get("decisions", {}).get("items", [])) + 1
    revision_number = len(artifacts.get("revisions", {}).get("items", [])) + 1
    decision = {
        "decision_id": f"D{decision_number:02d}",
        "target_step": target_step,
        "object_id": object_id,
        "old_value": old_recorded,
        "submitted_old_value": old_value.strip(),
        "new_value": new_recorded,
        "reason": reason,
        "source": source,
        "actor": actor,
        "created_at_utc": None,
        "result": "APPLIED_PENDING_REVALIDATION",
    }
    revision = {
        "revision_id": f"v{revision_number + 1}",
        "from_revision": f"v{revision_number}",
        "decision_id": decision["decision_id"],
        "target_step": target_step,
        "object_id": object_id,
        "before": previous,
        "after": changed or {"removed": object_id},
        "reason": reason,
        "source": source,
        "actor": actor,
        "affected_steps": IMPACTED_STEPS,
        "affected_artifacts": IMPACTED_ARTIFACTS,
        "unaffected_artifacts": CONSTRAINT_IMPACT["unaffected_artifacts"],
        "invalidated_artifacts": CONSTRAINT_IMPACT["stale_artifacts"],
        "stale_artifacts_before_revalidation": CONSTRAINT_IMPACT["stale_artifacts"],
        "recomputed_artifacts": [],
        "stale_artifacts_after_revalidation": CONSTRAINT_IMPACT["stale_artifacts"],
    }
    return constraints, decision, revision


def apply_responsibility_edit(
    fixture: dict[str, Any],
    artifacts: dict[str, Any],
    *,
    object_id: str,
    name: str,
    activity: str,
    operation: str,
    reason: str,
    source: str,
    actor: str,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    """Prepare a human responsibility revision and its downstream impact record."""
    if not all(value.strip() for value in (object_id, name, activity, operation, reason, source, actor)):
        raise ValueError("Responsibility ID, name, activity, operation, reason, source, and reviewer are required.")
    updated_fixture = deepcopy(fixture)
    target = next((item for item in updated_fixture["responsibilities"] if item["id"] == object_id), None)
    current = next(
        (item for item in artifacts["responsibilities"]["items"] if item["id"] == object_id),
        None,
    )
    if target is None or current is None:
        raise ValueError(f"Responsibility {object_id} was not found.")
    before = {key: current[key] for key in ("name", "activity", "operation")}
    after = {"name": name.strip(), "activity": activity.strip(), "operation": operation.strip()}
    if before == after:
        raise ValueError(f"The requested edit leaves {object_id} unchanged.")
    target.update(after)
    target["review_decision_status"] = "REVIEW_REQUIRED"
    target["semantic_status"] = "REVIEW_REQUIRED"
    updated_fixture["responsibility_provenance"] = "HUMAN_REVISED_REVIEW_REQUIRED"

    decision_number = len(artifacts.get("decisions", {}).get("items", [])) + 1
    revision_number = len(artifacts.get("revisions", {}).get("items", [])) + 1
    stale = RESPONSIBILITY_IMPACT["stale_artifacts"]
    decision = {
        "decision_id": f"D{decision_number:02d}",
        "decision_type": "STRUCTURAL_REVISION",
        "target_step": "02",
        "target_artifact": "responsibilities",
        "object_id": object_id,
        "action": "REVISE",
        "old_value": before,
        "new_value": after,
        "reason": reason,
        "source": source,
        "actor": actor,
        "created_at_utc": None,
        "result": "APPLIED_PENDING_REVALIDATION",
    }
    revision = {
        "revision_id": f"v{revision_number + 1}",
        "from_revision": f"v{revision_number}",
        "decision_id": decision["decision_id"],
        "target_step": "02",
        "target_artifact": "responsibilities",
        "object_id": object_id,
        "before": before,
        "after": after,
        "reason": reason,
        "source": source,
        "actor": actor,
        "affected_steps": sorted(set(RESPONSIBILITY_IMPACT["affected_steps"]) | {"09"}),
        "affected_artifacts": ["responsibilities", *stale, "decisions", "revisions"],
        "unaffected_artifacts": RESPONSIBILITY_IMPACT["unaffected_artifacts"],
        "invalidated_artifacts": stale,
        "stale_artifacts_before_revalidation": stale,
        "recomputed_artifacts": [],
        "stale_artifacts_after_revalidation": stale,
    }
    return updated_fixture, decision, revision


def artifact_diff(
    before: dict[str, Any],
    after: dict[str, Any],
    *,
    exclude: set[str] | None = None,
) -> dict[str, Any]:
    """Return changed artifact names and a compact before/after record."""
    changed = {}
    excluded = exclude or set()
    for key in sorted(set(before) | set(after)):
        if key in excluded:
            continue
        if before.get(key) != after.get(key):
            changed[key] = {"before": before.get(key), "after": after.get(key)}
    return {"changed_artifacts": list(changed), "changes": changed}
