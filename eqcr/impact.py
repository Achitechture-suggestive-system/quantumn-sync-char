"""Artifact dependency map used to preview review impact."""

from __future__ import annotations

from collections import deque


# Keys are persisted artifact names; values are the artifacts that consume them.
DEPENDENTS: dict[str, tuple[str, ...]] = {
    "raw_requirements": ("context", "responsibilities", "relation_registry", "interactions", "quality_profiles", "traceability"),
    "context": ("responsibilities", "traceability"),
    "responsibilities": ("evidence", "relation_registry", "partitions", "quanta", "validation_report", "traceability"),
    "relation_registry": ("evidence",),
    "evidence": ("constraints", "quanta", "interactions", "validation_report", "traceability"),
    "constraints": ("partitions", "validation_report", "traceability"),
    "partitions": ("quanta", "validation_report", "traceability"),
    "quanta": ("interactions", "quality_profiles", "validation_report", "traceability"),
    "interactions": ("quality_profiles", "validation_report", "traceability"),
    "quality_profiles": ("validation_report", "traceability"),
    "decisions": ("traceability",),
    "revisions": ("traceability",),
    "traceability": ("validation_report",),
}

STEP_BY_ARTIFACT = {
    "raw_requirements": "01",
    "context": "01",
    "responsibilities": "02",
    "relation_registry": "03",
    "evidence": "03",
    "constraints": "04",
    "partitions": "05",
    "quanta": "06",
    "interactions": "07",
    "quality_profiles": "08",
    "decisions": "09",
    "revisions": "09",
    "validation_report": "10",
    "traceability": "10",
}


def downstream_artifacts(source_artifact: str) -> list[str]:
    """Return a stable, transitive list of outputs invalidated by a source edit."""
    if source_artifact not in DEPENDENTS:
        raise ValueError(f"No dependency mapping exists for {source_artifact!r}.")
    visited: set[str] = set()
    pending = deque([source_artifact])
    while pending:
        artifact = pending.popleft()
        for child in DEPENDENTS.get(artifact, ()):
            if child not in visited:
                visited.add(child)
                pending.append(child)
    return sorted(visited)


def impact_preview(source_artifact: str) -> dict[str, list[str]]:
    """Describe the preview state before recomputation and the unaffected source artifacts."""
    stale = downstream_artifacts(source_artifact)
    return {
        "stale_artifacts": stale,
        "affected_steps": sorted(
            {STEP_BY_ARTIFACT[name] for name in [source_artifact, *stale] if name in STEP_BY_ARTIFACT}
        ),
        "unaffected_artifacts": sorted(
            set(STEP_BY_ARTIFACT) - set(stale) - {source_artifact, "decisions", "revisions"}
        ),
    }
