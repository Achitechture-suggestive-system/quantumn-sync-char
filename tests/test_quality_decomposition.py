import json
from xml.etree import ElementTree

import pytest

from eqcr.fixture import _ref, get_fixture
from eqcr.iso_quality import ARCHITECTURE_DRIVERS, iso_registry, iso_subcharacteristics
from eqcr.pipeline import run_pipeline, validate_project_package
from eqcr.quality_interactions import InteractionAssessment, interaction_profile
from eqcr.quality_worked_example import get_quality_worked_example
from eqcr.requirements_engine import AtomicRequirementReview, RequirementDocument, classify_documents
from eqcr.storage import verify_export_zip
from scripts.run_quality_decomposition import export_quality_run


def _test_only_review():
    return {
        "reviewer_id": "TEST-ONLY",
        "reviewed_at": "2026-01-01T00:00:00Z",
        "rationale": "Synthetic test input for validating the review gate.",
    }


def test_iso_2023_registry_has_stable_taxonomy_and_separate_drivers():
    parents = iso_registry()["characteristics"]
    terms = iso_subcharacteristics()
    assert len(parents) == 9
    assert [len(item["subcharacteristics"]) for item in parents] == [3, 3, 2, 8, 4, 6, 5, 4, 5]
    assert len(terms) == 40
    assert terms["ISO25010-2023-3.2.1"]["name"] == "Time behaviour"
    assert terms["ISO25010-2023-3.5.4"]["name"] == "Recoverability"
    assert terms["ISO25010-2023-3.8.2"]["name"] == "Scalability"
    assert all(item["reference"] and item["verification_methods"] and item["guidance_provenance"] for item in terms.values())
    assert not ARCHITECTURE_DRIVERS.keys() & terms.keys()


@pytest.mark.parametrize(("text", "expected"), [
    ("A borrower can reserve equipment.", "FR"),
    ("The p95 response time must be at most 400 ms.", "NFR"),
    ("The team must use the shared identity service.", "ARCHITECTURAL_CONSTRAINT"),
    ("We decided to use a background queue.", "DESIGN_DECISION"),
    ("The description sounds modern.", "UNKNOWN"),
])
def test_requirement_classification_creates_proposals(text, expected):
    [row] = classify_documents([RequirementDocument(id="SRC", text=text)], [])["documents"]
    [atom] = row["atoms"]
    assert atom["requirement_type"] == expected
    assert atom["source_ref"] == _ref("SRC", text, text)
    assert atom["review_status"] == ("UNKNOWN" if expected == "UNKNOWN" else "PROPOSED")


def test_mixed_requirements_split_and_stale_review_fails():
    text = "A borrower can reserve equipment and p95 response time must be at most 400 ms."
    document = RequirementDocument(id="MIX", text=text)
    [row] = classify_documents([document], [])["documents"]
    assert row["original_text"] == text and row["requirement_type"] == "MIXED"
    fr, nfr = row["atoms"]
    assert [fr["requirement_type"], nfr["requirement_type"]] == ["FR", "NFR"]
    assert [fr["atomic_id"], nfr["atomic_id"]] == ["MIX.A01", "MIX.A02"]
    review = AtomicRequirementReview(**_test_only_review(), atomic_id=nfr["atomic_id"],
                                    source_ref=nfr["source_ref"], requirement_type="NFR", disposition="APPROVED")
    [approved] = classify_documents([document], [review])["documents"]
    assert approved["atoms"][1]["review_status"] == "HUMAN_APPROVED"
    document.text = text.replace("400", "500")
    with pytest.raises(ValueError, match="Unresolved source span"):
        classify_documents([document], [review])


def test_model_declared_nfr_stays_a_proposal_even_with_a_valid_span():
    text = "The p95 response time must be at most 400 ms."
    document = RequirementDocument(id="MODEL", text=text, declared_type="NFR", provenance="LLM_PROPOSAL")
    [row] = classify_documents([document], [])["documents"]
    assert row["atoms"][0]["review_status"] == "PROPOSED"
    review = AtomicRequirementReview(**_test_only_review(), atomic_id="MODEL.A01", source_ref=_ref("MODEL", text, text),
                                    requirement_type="NFR", disposition="APPROVED")
    with pytest.raises(ValueError, match="original source"):
        classify_documents([document], [review])


def _add_hard(project, left, right, relation, predicate=None):
    source = project["raw_requirements"]["requirements"][0]["source_ref"]
    rule_id = f"HARD-{left}-{right}-{relation}"
    evidence_id = f"EV-{rule_id}"
    project["evidence"].append({
        "id": evidence_id, "subject_id": left, "object_id": right,
        "predicate": predicate or ("VERIFIED_ATOMIC_INVARIANT" if relation == "MUST_LINK" else "MANDATORY_SEPARATION"),
        "status": "PRESENT", "review_status": "APPROVED", "provenance": "SOURCE_BACKED",
        "rationale": "Test-only reviewed evidence", "source_refs": [source],
    })
    project["constraints"].append({
        "id": rule_id, "left": left, "right": right, "relation": relation, "origin": "HUMAN_OVERRIDE",
        "evidence_ids": [evidence_id], "source_refs": [source], "rationale": "Test-only hard rule",
    })
    project["quality_decomposition"].setdefault("hard_constraint_reviews", []).append({
        **_test_only_review(), "constraint_id": rule_id, "requirement_atomic_id": source["source_id"] + ".A01",
        "justification": source, "alternative_considered": "Test-only evaluation of an alternative.",
    })


def test_shared_table_or_nfr_label_cannot_justify_hard_link():
    project = get_quality_worked_example()
    _add_hard(project, "R1", "R2", "MUST_LINK", predicate="SHARED_TABLE")
    with pytest.raises(ValueError, match="Unsupported hard constraint"):
        run_pipeline(project)
    project["evidence"][-1]["predicate"] = "VERIFIED_ATOMIC_INVARIANT"
    project["quality_decomposition"]["hard_constraint_reviews"][-1]["requirement_atomic_id"] = "NFR-RESERVATION.A01"
    with pytest.raises(ValueError, match="Unsupported hard constraint"):
        run_pipeline(project)


def test_existing_closure_preserves_hard_constraint_conflicts():
    project = get_quality_worked_example()
    _add_hard(project, "R1", "R2", "MUST_LINK")
    _add_hard(project, "R2", "R3", "MUST_LINK")
    _add_hard(project, "R1", "R3", "CANNOT_LINK")
    artifacts = run_pipeline(project)
    assert artifacts["partitions"]["result_status"] == "INFEASIBLE"
    assert not artifacts["quality_decomposition"]["candidates"]
    assert len(artifacts["quality_decomposition"]["core_conflicts"][0]["constraint_ids"]) == 3


def test_atomic_interaction_abstains_across_quantum_boundaries():
    connection = get_quality_worked_example()["quality_decomposition"]["interactions"][0]
    connection["atomicity"] = "REQUIRED"
    assessment = InteractionAssessment.model_validate(connection)
    assert interaction_profile(assessment, {"R1": "Q1", "R2": "Q1"})["mode"] == "LOCAL"
    cross = interaction_profile(assessment, {"R1": "Q1", "R2": "Q2"})
    assert cross["mode"] == "UNRESOLVED"
    assert "crosses" in cross["missing_evidence"][0]


@pytest.mark.parametrize("missing", ["delivery", "retries", "idempotency", "ordering", "timing"])
def test_async_review_requires_cited_consent_and_complete_delivery_contract(missing):
    project = get_quality_worked_example()
    connection = project["quality_decomposition"]["interactions"][1]
    connection["review"] = {**_test_only_review(), "mode": "ASYNC_EVENT"}
    if missing == "timing":
        del connection["basis_refs"]["timing"]
    else:
        del connection[missing]
    with pytest.raises(ValueError, match="unsupported reviewed mode"):
        run_pipeline(project)


def test_approved_async_separation_enters_existing_optimizer():
    project = get_quality_worked_example()
    project["constraints"].append({
        "id": "KEEP-REPORT-LEGACY", "left": "R4", "right": "R5", "relation": "MUST_LINK",
        "hardness": "SOFT", "weight": 1, "origin": "WHAT_IF_POLICY", "rationale": "Test prior policy.",
    })
    before = run_pipeline(project)
    project["quality_decomposition"]["interactions"][1]["review"] = {
        **_test_only_review(), "mode": "ASYNC_EVENT", "optimizer_weight": 4,
    }
    after = run_pipeline(project)
    assert before["quanta"]["primary_assignment"]["R4"] == before["quanta"]["primary_assignment"]["R5"]
    assert after["quanta"]["primary_assignment"]["R4"] != after["quanta"]["primary_assignment"]["R5"]
    assert after["quality_decomposition"]["constraint_origins"][0]["constraint_id"] == "INTERACTION-I-REPORT"


def test_quality_priority_weights_change_the_partition_and_cannot_be_implicit():
    project = get_quality_worked_example()
    project["constraints"].append({
        "id": "CAPACITY-WHAT-IF", "left": "R1", "right": "R2", "relation": "CANNOT_LINK",
        "hardness": "SOFT", "weight": 3, "origin": "WHAT_IF_POLICY", "rationale": "Test competing capacity preference.",
    })
    scenario = project["quality_decomposition"]["scenarios"][0]
    scenario["preferences"] = [{"left": "R1", "right": "R2", "relation": "MUST_LINK", "weight": 2}]
    with pytest.raises(ValueError, match="requires explicit review"):
        run_pipeline(project)
    scenario["review"] = _test_only_review()
    low = run_pipeline(project)["quanta"]["primary_assignment"]
    scenario["preferences"][0]["weight"] = 4
    high = run_pipeline(project)["quanta"]["primary_assignment"]
    assert low["R1"] != low["R2"] and high["R1"] == high["R2"]


def test_worked_example_keeps_unknown_evidence_and_measurable_targets_separate():
    project = get_quality_worked_example()
    run = validate_project_package(project)
    report = run["quality_decomposition"]
    assert report == run_pipeline(project, execution_mode="STRUCTURED_INPUT")["quality_decomposition"]
    assert {item["status"] for item in report["coupling"]["dimensions"]["domain_invariant"]} == {"SCOPED_ABSENT"}
    assert report["coupling"]["dimensions"]["independent_deployability"][0]["status"] == "UNKNOWN"
    assert not report["coupling"]["dimensions"]["scalability_independence"]
    assert report["coupling"]["unrecorded_scope"] == "UNKNOWN"
    scenario, recovery = report["quality_scenario_matrix"]
    assert len(scenario["parts"]) == 6 and all(item["source_ref"] for item in scenario["parts"].values())
    assert scenario["iso_mappings"][0]["mapping_status"] == "SOURCE_CONFIRMED"
    assert scenario["target_status"] == "TARGET_SPECIFIED" and scenario["measurement"] is None
    assert scenario["latency_budget"]["declared_allocation_ms"] == 160
    assert recovery["target_status"] == "MEASURE_MISSING" and recovery["parts"]["environment"]["status"] == "UNKNOWN"
    assert all(profile["measurement_status"] == "NOT_MEASURED"
               for candidate in report["candidates"] for profile in candidate["quality_profiles"])
    assert report["candidate_count"] == 3
    assert run["traceability"]["assertions"]["all_edge_endpoints_resolve"]


def test_unmeasured_quality_cannot_be_overwritten_by_a_target_or_unsafe_budget():
    project = get_quality_worked_example()
    scenario = project["quality_decomposition"]["scenarios"][0]
    scenario["latency_observation"] = {
        "run_id": "NONEXISTENT", "metric": "p95", "milliseconds": 400,
        "source_ref": scenario["target"], "review": _test_only_review(),
    }
    with pytest.raises(ValueError, match="observation requires a reviewed"):
        run_pipeline(project)
    del scenario["latency_observation"]
    scenario["latency_allocations"][0]["milliseconds"] = 410
    with pytest.raises(ValueError, match="unsupported, duplicate"):
        run_pipeline(project)


def test_every_accepted_nfr_has_at_least_an_unresolved_scenario():
    project = get_quality_worked_example()
    project["quality_decomposition"]["scenarios"] = []
    scenarios = run_pipeline(project)["quality_decomposition"]["quality_scenario_matrix"]
    assert {item["nfr_id"] for item in scenarios} == {"NFR-RESERVATION.A01", "NFR-REPORT.A01"}
    for item in scenarios:
        assert item["target_status"] == "MEASURE_MISSING"
        assert all(part["status"] == "UNKNOWN" for part in item["parts"].values())


@pytest.mark.parametrize(("millis", "status"), [(350, "MEASURED_PASS"), (450, "MEASURED_FAIL")])
def test_supplied_system_observation_requires_linked_metric_and_stays_system_level(millis, status):
    project = get_quality_worked_example()
    config = project["quality_decomposition"]
    text = f"TEST-RUN-1 busy-hour load p95 result was {millis} ms."
    config["source_documents"].append({"id": "SUPPLIED-TEST", "text": text, "provenance": "SUPPLIED_OBSERVATION"})
    config["scenarios"][0].update(review=_test_only_review(), latency_observation={
        "run_id": "TEST-RUN-1", "metric": "p95", "milliseconds": millis,
        "source_ref": _ref("SUPPLIED-TEST", text, text), "review": _test_only_review(),
    })
    report = run_pipeline(project)["quality_decomposition"]
    assert report["quality_scenario_matrix"][0]["measurement_status"] == status
    assert all(item["measurement_status"] == "NOT_MEASURED" for item in report["candidates"][0]["quality_profiles"])


def test_export_preserves_before_after_unknown_and_editable_graph(tmp_path):
    before = get_quality_worked_example(explicit_wait_evidence=False)
    out = tmp_path / "quality"
    export_quality_run(get_quality_worked_example(), out, before=before)
    replay = json.loads((out / "before-after.json").read_text(encoding="utf-8"))
    assert replay["before"]["candidates"][0]["modes"]["I-RESERVE"] == "UNRESOLVED"
    assert replay["after"]["candidates"][0]["modes"]["I-RESERVE"] == "SYNC_REQUEST_RESPONSE"
    assert replay["before"]["objective_minimum"] == replay["after"]["objective_minimum"]
    assert len(list(out.glob("*.drawio"))) == 3
    for path in out.glob("*.drawio"):
        assert ElementTree.parse(path).getroot().tag == "mxfile"
    verify_export_zip((out / "artifacts.zip").read_bytes())


def test_legacy_fixture_remains_on_precomputed_scope():
    artifacts = run_pipeline(get_fixture())
    assert "quality_decomposition" not in artifacts
    assert artifacts["partitions"]["enumerated_partition_count"] == 203
    assert artifacts["quality_profiles"]["profiles"][0]["quality_characteristic_mapping"]["status"] == "UNMAPPED"
