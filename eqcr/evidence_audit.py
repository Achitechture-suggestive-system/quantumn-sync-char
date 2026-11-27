"""Deterministic structural audit for duplicate and incompatible evidence rows."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from .models import EvidenceRecord, RelationAnnotation


def audit_evidence_records(
    evidence: list[EvidenceRecord],
    relations: list[RelationAnnotation],
) -> dict[str, Any]:
    """Find exact duplicate citations and incompatible states for the same claim.

    The audit uses exact typed identifiers and relation direction. It does not
    infer predicate equivalence, entailment, temporal scope, or source meaning.
    """
    relation_by_id = {item.id: item for item in relations}
    claim_groups: dict[tuple[str, ...], list[EvidenceRecord]] = defaultdict(list)
    duplicate_groups: dict[tuple[Any, ...], list[EvidenceRecord]] = defaultdict(list)

    def claim_key(item: EvidenceRecord) -> tuple[str, ...]:
        endpoints = (item.subject_id, item.object_id)
        requirement_endpoints = (
            item.subject_requirement_id or "",
            item.object_requirement_id or "",
        )
        relation = relation_by_id.get(item.relation_annotation_id or "")
        if relation is not None and relation.direction == "UNDIRECTED":
            endpoints = tuple(sorted(endpoints))
            requirement_endpoints = tuple(sorted(requirement_endpoints))
        return (*endpoints, item.predicate, *requirement_endpoints)

    def source_signature(item: EvidenceRecord) -> tuple[tuple[Any, ...], ...]:
        return tuple(sorted(
            (ref.source_id, ref.start, ref.end, ref.quote)
            for ref in item.source_refs
        ))

    for item in evidence:
        key = claim_key(item)
        claim_groups[key].append(item)
        duplicate_groups[(key, item.status, source_signature(item))].append(item)

    duplicates = [
        {
            "evidence_ids": sorted(item.id for item in rows),
            "claim": {
                "subject_id": key[0],
                "object_id": key[1],
                "predicate": key[2],
                "subject_requirement_id": key[3] or None,
                "object_requirement_id": key[4] or None,
            },
            "status": status,
            "source_spans": [
                {"source_id": ref[0], "start": ref[1], "end": ref[2], "quote": ref[3]}
                for ref in source_spans
            ],
            "classification": "EXACT_DUPLICATE_CLAIM_AND_CITATION",
        }
        for (key, status, source_spans), rows in duplicate_groups.items()
        if len(rows) > 1
    ]

    ambiguous_claims = []
    for key, rows in claim_groups.items():
        statuses = {item.status for item in rows}
        if "PRESENT" in statuses and "SCOPED_ABSENT" in statuses:
            classification = "CONTRADICTORY_PRESENT_AND_SCOPED_ABSENT"
        elif "UNKNOWN" in statuses and statuses & {"PRESENT", "SCOPED_ABSENT"}:
            classification = "MIXED_WITH_UNKNOWN"
        else:
            continue
        ambiguous_claims.append(
            {
                "evidence_ids": sorted(item.id for item in rows),
                "claim": {
                    "subject_id": key[0],
                    "object_id": key[1],
                    "predicate": key[2],
                    "subject_requirement_id": key[3] or None,
                    "object_requirement_id": key[4] or None,
                },
                "statuses": sorted(statuses),
                "classification": classification,
            }
        )

    blocked_ids = {
        evidence_id
        for group in duplicates
        for evidence_id in group["evidence_ids"]
    }
    blocked_ids.update(
        evidence_id
        for group in ambiguous_claims
        for evidence_id in group["evidence_ids"]
    )
    return {
        "schema_id": "EQCR-EVIDENCE-CLAIM-AUDIT",
        "schema_version": "1.0.0",
        "provenance": "DETERMINISTIC_TRANSFORMATION",
        "status": "REVIEW_REQUIRED" if duplicates or ambiguous_claims else "NO_FINDINGS",
        "duplicate_groups": sorted(duplicates, key=lambda item: item["evidence_ids"]),
        "ambiguous_claims": sorted(ambiguous_claims, key=lambda item: item["evidence_ids"]),
        "blocked_evidence_ids": sorted(blocked_ids),
        "normalization_policy": (
            "Exact subject/object identifiers, predicate, optional FR endpoints, and declared relation direction; "
            "duplicate detection additionally requires identical status and exact source spans."
        ),
        "limitations": [
            "This is a structural consistency check, not semantic validation or source entailment.",
            "Different source spans remain separate observations and may still describe different contexts or times.",
            "Predicates are not treated as equivalent and inverse relations are not inferred.",
            "UNKNOWN is not converted to SCOPED_ABSENT or to a negative label.",
        ],
    }
