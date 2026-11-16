from eqcr.fixture import get_fixture
from eqcr.ollama import apply_proposals_to_fixture
from eqcr.pipeline import run_pipeline
from eqcr.review import apply_artifact_review
from eqcr.traceability import refresh_traceability_artifact


def test_traceability_records_source_proposal_evidence_constraint_and_partition_edges():
    artifacts = run_pipeline(get_fixture())
    graph = artifacts["traceability"]
    nodes = {item["id"]: item for item in graph["nodes"]}
    edges = {
        (item["from"], item["to"], item["relation"])
        for item in graph["edges"]
    }

    assert graph["status"] == "PASS"
    assert graph["assertions"]["all_feasible_candidates_are_linked"] is True
    assert ("source:REQ-FR-01", "requirement:FR-01", "SOURCE_FOR") in edges
    assert ("requirement:FR-01", "responsibility:R1", "PROPOSES_RESPONSIBILITY_FOR") in edges
    assert ("responsibility:R1", "evidence:EV-R1-01", "HAS_RECORDED_EVIDENCE") in edges
    assert ("constraint:H1", "responsibility:R2", "CONSTRAINS_ENDPOINT") in edges
    assert any(
        source == "constraint:H1" and target.startswith("partition:")
        and relation == "SATISFIED_BY"
        for source, target, relation in edges
    )
    assert nodes["evidence:EV-R1-01"]["review_status"] == "REVIEW_REQUIRED"
    assert {item["constraint_id"] for item in graph["constraints_without_evidence_links"]} == {
        "H1", "H2", "H3"
    }
    assert not any(edge[2] == "EXPLICIT_EVIDENCE_LINK" for edge in edges)
    assert graph["artifact_metadata"]["verification_status"] == "PASS"
    assert "semantic support" in graph["artifact_metadata"]["verification_scope"]


def test_human_evidence_review_updates_traceability_without_claiming_measurement():
    artifacts = run_pipeline(get_fixture())
    reviewed = apply_artifact_review(
        artifacts,
        target_artifact="evidence",
        object_id="EV-R1-01",
        action="APPROVE",
        reason="Reviewed the cited requirement wording.",
        source="TEST-REVIEW",
        actor="reviewer-1",
    )
    graph = reviewed["traceability"]
    evidence_node = next(item for item in graph["nodes"] if item["id"] == "evidence:EV-R1-01")
    assert evidence_node["review_status"] == "APPROVED"
    assert any(
        edge["from"] == "decision:D01"
        and edge["to"] == "evidence:EV-R1-01"
        and edge["relation"] == "REVIEWS_OR_CHANGES"
        for edge in graph["edges"]
    )
    assert reviewed["validation_report"]["status"] == "REVIEW_REQUIRED"
    assert reviewed["quality_profiles"]["profiles"][0]["measurement_status"] == "NOT_MEASURED"


def test_ollama_proposal_lineage_is_visible_and_stays_review_required():
    fixture = get_fixture()
    requirements = fixture["raw_requirements"]["requirements"]
    proposal_data = {
        "model": "synthetic-test-model",
        "provenance": "LOCAL_OLLAMA_UNVERIFIED",
        "prompt_version": "test-prompt",
        "input_sha256": "test-input-hash",
        "context_summary": "Synthetic proposal bundle.",
        "can_apply_to_fixture": True,
        "normalized_requirements": [],
        "proposals": [],
        "evidence_proposals": [],
        "boundary_hypotheses": [],
    }
    for requirement in requirements:
        requirement_id = requirement["id"]
        source_ref = requirement["source_ref"]
        proposal_data["normalized_requirements"].append(
            {
                "id": requirement_id,
                "normalized_text": requirement["text"],
                "source_id": source_ref["source_id"],
                "source_ref": source_ref,
                "source_span_resolved": True,
                "status": "REVIEW_REQUIRED",
            }
        )
        proposal_data["proposals"].append(
            {
                "id": f"MODEL-{requirement_id}",
                "name": f"Model proposal {requirement_id}",
                "activity": "Reviewable activity",
                "operation": f"operation {requirement_id}",
                "requirement_ids": [requirement_id],
                "decomposition_rationale": "Test-only responsibility rationale.",
                "source_id": source_ref["source_id"],
                "source_ref": source_ref,
                "source_span_resolved": True,
                "status": "REVIEW_REQUIRED",
            }
        )
    first_ref = requirements[0]["source_ref"]
    proposal_data["evidence_proposals"].append(
        {
            "id": "MODEL-EVIDENCE-01",
            "subject_requirement_id": "FR-01",
            "predicate": "related_to",
            "object_requirement_id": "FR-02",
            "source_requirement_ids": ["FR-01"],
            "source_refs": [first_ref],
            "review_status": "REVIEW_REQUIRED",
            "validation_note": "Citations resolved; meaning unreviewed.",
        }
    )
    proposal_data["boundary_hypotheses"].append(
        {
            "id": "MODEL-BOUNDARY-01",
            "requirement_ids": ["FR-01", "FR-02"],
            "source_requirement_ids": ["FR-01", "FR-02"],
            "source_refs": [requirements[0]["source_ref"], requirements[1]["source_ref"]],
            "review_status": "REVIEW_REQUIRED",
            "validation_note": "Citations resolved; boundary unreviewed.",
        }
    )

    model_fixture = apply_proposals_to_fixture(fixture, proposal_data)
    artifacts = run_pipeline(model_fixture, execution_mode="OLLAMA_ASSISTED")
    artifacts["ollama_proposals"] = proposal_data
    refresh_traceability_artifact(artifacts)

    graph = artifacts["traceability"]
    nodes = {item["id"]: item for item in graph["nodes"]}
    assert graph["status"] == "PASS"
    assert nodes["llm-responsibility:MODEL-FR-01"]["review_status"] == "REVIEW_REQUIRED"
    assert not any(item.get("provenance") == "MODEL_PROPOSED" for item in graph["nodes"] if item["kind"] == "EVIDENCE_RELATION")
    assert nodes["evidence_proposals:MODEL-EVIDENCE-01"]["review_status"] == "REVIEW_REQUIRED"
    assert nodes["boundary_hypotheses:MODEL-BOUNDARY-01"]["review_status"] == "REVIEW_REQUIRED"
    assert graph["assertions"]["no_unresolved_reference_issues"] is True
