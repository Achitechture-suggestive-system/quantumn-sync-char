from eqcr.evidence_audit import audit_evidence_records
from eqcr.models import EvidenceRecord, RelationAnnotation, SourceRef


def _evidence(evidence_id, status, *, subject="R1", object_="R2", source_id="SRC-1"):
    return EvidenceRecord(
        id=evidence_id,
        subject_id=subject,
        predicate="SHARES_STATE_OR_INVARIANT",
        object_id=object_,
        status=status,
        provenance="P2_TEST_ONLY",
        review_status="APPROVED",
        source_refs=[SourceRef(source_id=source_id, quote="x", start=0, end=1)],
        rationale="Test-only evidence row.",
    )


def test_evidence_audit_reports_duplicates_contradictions_and_unknown_mixture():
    evidence = [
        _evidence("E1", "PRESENT"),
        _evidence("E2", "PRESENT"),
        _evidence("E3", "SCOPED_ABSENT", source_id="SRC-2"),
        _evidence("E4", "PRESENT", subject="R3", object_="R4"),
        _evidence("E5", "UNKNOWN", subject="R3", object_="R4"),
    ]

    audit = audit_evidence_records(evidence, [])

    assert audit["status"] == "REVIEW_REQUIRED"
    assert audit["duplicate_groups"][0]["evidence_ids"] == ["E1", "E2"]
    classes = {item["classification"]: set(item["evidence_ids"]) for item in audit["ambiguous_claims"]}
    assert classes["CONTRADICTORY_PRESENT_AND_SCOPED_ABSENT"] == {"E1", "E2", "E3"}
    assert classes["MIXED_WITH_UNKNOWN"] == {"E4", "E5"}
    assert audit["blocked_evidence_ids"] == ["E1", "E2", "E3", "E4", "E5"]


def test_evidence_audit_canonicalizes_only_declared_undirected_relations():
    relation = RelationAnnotation(
        id="REL-1",
        subject_requirement_id="FR-01",
        predicate="SHARES_STATE_OR_INVARIANT",
        object_requirement_id="FR-02",
        direction="UNDIRECTED",
        status="PRESENT",
        review_status="APPROVED",
        provenance="P2_TEST_ONLY",
        source_requirement_ids=["FR-01", "FR-02"],
        rationale="Test-only relation annotation.",
    )
    left_to_right = _evidence("E1", "PRESENT")
    left_to_right.relation_annotation_id = "REL-1"
    right_to_left = _evidence("E2", "SCOPED_ABSENT", subject="R2", object_="R1", source_id="SRC-2")
    right_to_left.relation_annotation_id = "REL-1"

    audit = audit_evidence_records([left_to_right, right_to_left], [relation])

    assert audit["ambiguous_claims"][0]["classification"] == "CONTRADICTORY_PRESENT_AND_SCOPED_ABSENT"
