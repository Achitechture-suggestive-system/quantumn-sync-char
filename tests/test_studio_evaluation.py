"""Synthetic protocol/scorer tests only; simulated attestations are not human reference labels."""

from copy import deepcopy
import json
from pathlib import Path

import pytest

from eqcr import ollama, storage
from eqcr.studio_evaluation import readiness, run_study, score_study
import eqcr.studio_evaluation as experiment
from eqcr.studio_evaluation_protocol import (PROTOCOL, EvaluationBlocked, adjudicate, annotation_template,
    claim_links, digest, load_study, lock_annotation, prepare_study, source_units, validate_claim, validate_source, verify_reference)
from eqcr.studio_extraction import build_request
from eqcr.studio_oracles import oracle_ticket_cases
from scripts.studio_evaluation import main


DIGEST = "1" * 64
FREEZE = "2026-01-01T00:00:00+00:00"
ANNOTATED = "2026-01-02T00:00:00+00:00"
LOCKED = "2026-01-03T00:00:00+00:00"
ADJUDICATED = "2026-01-04T00:00:00+00:00"


def source_fixture():
    return {"id": "TEST-STUDY", "curation_rationale": "Synthetic unit-test case; no actual independent annotation.",
        "no_known_paraphrase_leakage_attested": True, "cases": [{"id": "TEST-CASE", "document_group": "TEST-DOC",
            "split": "HELD_OUT", "provenance": "PREPARED_FIXTURE", "authorship": "TEST_ONLY_NOT_RESEARCH_DATA",
            "components": [{"id": "A", "name": "Processor"}, {"id": "B", "name": "Archive"}],
            "requirements": [
                {"id": "Q1", "kind": "NFR", "text": "Processor must return a receipt within 450 ms. Processor and Archive must remain in different Quanta."},
                {"id": "Q2", "kind": "NFR", "text": "If Archive is stopped, Processor shall recover within ten seconds."},
                {"id": "W1", "kind": "FR", "text": "Processor must wait for Archive to commit in a single local atomic transaction."}]}],
        "queries": [{"id": "QUERY-Q", "case_id": "TEST-CASE", "task": "QUALITY", "source_ids": ["Q1", "Q2"]},
                    {"id": "QUERY-I", "case_id": "TEST-CASE", "task": "INTERACTION", "source_ids": ["W1"]},
                    {"id": "QUERY-S", "case_id": "TEST-CASE", "task": "SEPARATION", "source_ids": ["Q1"]}]}


def reference_claims():
    return {
        "TEST-CASE/QUALITY/Q1": [{"kind": "QUALITY", "quote": "Processor must return a receipt within 450 ms.", "condition": None,
                                 "characteristic": "Performance efficiency", "component_ids": ["A"]}],
        "TEST-CASE/QUALITY/Q2": [{"kind": "QUALITY", "quote": "If Archive is stopped, Processor shall recover within ten seconds.",
                                 "condition": "If Archive is stopped", "characteristic": "Reliability", "component_ids": ["A"]}],
        "TEST-CASE/INTERACTION/W1": [{"kind": "INTERACTION", "quote": "Processor must wait for Archive to commit in a single local atomic transaction.",
                                     "condition": None, "source": "A", "target": "B", "mode": "SYNC", "local_transaction": True}],
        "TEST-CASE/SEPARATION/Q1": [{"kind": "SEPARATION", "quote": "Processor and Archive must remain in different Quanta.",
                                   "condition": None, "left": "A", "right": "B"}]}


def simulated_reference(source, frozen):
    locks = []
    for actor in ("TEST_ANNOTATOR_A", "TEST_ANNOTATOR_B"):
        submission = annotation_template(source, frozen["source_digest"])
        submission.update(annotator_id=actor, provenance="HUMAN_SOURCE_ONLY", source_only_attested=True,
            no_prior_model_output_exposure=True, independent_of_other_annotators=True, completed_at=ANNOTATED)
        for row in submission["rows"]:
            row.update(status="COMPLETE", claims=reference_claims()[row["unit"]], rationale="SIMULATED_TEST_LABEL_NOT_HUMAN_RESEARCH")
        locks.append(lock_annotation(source, frozen, submission, locked_at=LOCKED))
    submission = {"protocol": PROTOCOL, "package_digest": frozen["source_digest"], "adjudicator_id": "TEST_ADJUDICATOR",
        "provenance": "HUMAN_SOURCE_ONLY", "no_model_output_exposure": True, "completed_at": ADJUDICATED, "rows": deepcopy(locks[0]["submission"]["rows"])}
    return adjudicate(source, frozen, locks, submission, locked_at=ADJUDICATED)


@pytest.fixture
def study(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "ARTIFACT_ROOT", tmp_path / "runs")
    folder = tmp_path / "study"
    prepare_study(source_fixture(), folder, model_digest=DIGEST, code_sha="a" * 40, repetitions=2, prepared_at=FREEZE)
    source, frozen = load_study(folder)
    return folder, source, frozen


def fake_provider(monkeypatch, transform=None):
    monkeypatch.setattr(experiment, "check_revision", lambda frozen: {"sha": "a" * 40, "dirty": False})
    monkeypatch.setattr(ollama, "list_model_details", lambda: [{"name": "qwen3:4b", "digest": DIGEST}])
    monkeypatch.setattr(ollama, "get_ollama_version", lambda: "TEST_ONLY_OLLAMA_VERSION")
    calls = []

    def reply(endpoint, *, payload, timeout):
        calls.append(payload)
        fields = payload["format"]["properties"]["proposals"]["items"]["properties"]
        task = "QUALITY" if "characteristic" in fields else "INTERACTION" if "mode" in fields else "SEPARATION"
        proposals = []
        for source in json.loads(payload["messages"][-1]["content"]):
            claim = reference_claims()[f"TEST-CASE/{task}/{source['id']}"][0]
            raw = {key: value for key, value in claim.items() if key not in {"kind", "condition"}}
            raw.update(source_id=source["id"], disposition="PROPOSED", frame={
                "subject": "Processor", "action": "return" if source["id"] == "Q1" and task == "QUALITY" else "recover" if source["id"] == "Q2" else "wait" if task == "INTERACTION" else "remain",
                "object": "Archive" if task in {"INTERACTION", "SEPARATION"} else None,
                "condition": claim["condition"], "modality": "shall" if source["id"] == "Q2" else "must",
                "subject_ids": ["A"], "object_ids": ["B"] if task in {"INTERACTION", "SEPARATION"} else [],
                "context_ids": ["B"] if source["id"] == "Q2" else [], "statement_kind": "OBLIGATION",
                "effect": "QUALITY_OBLIGATION" if task == "QUALITY" else "LOCAL_ATOMIC_TRANSACTION" if task == "INTERACTION" else "REQUIRE_SEPARATION"})
            proposals.append(raw)
        if transform:
            transform(task, proposals)
        return {"model": "qwen3:4b", "done_reason": "stop", "eval_count": 50, "message": {"content": json.dumps({"proposals": proposals})}}

    monkeypatch.setattr(ollama, "_request", reply)
    return calls


def test_source_only_package_is_blank_and_cannot_be_inferred_as_reference(study):
    folder, source, frozen = study
    template = json.loads((folder / "source_only/ANNOTATION_TEMPLATE.json").read_text())
    assert all(row["status"] == "NOT_ANNOTATED" and row["claims"] == [] for row in template["rows"])
    assert set(p.name for p in (folder / "source_only").iterdir()) == {"SOURCE.json", "ANNOTATION_TEMPLATE.json", "README.md", "MANIFEST.json"}
    assert readiness(folder)["status"] == "BLOCKED_INDEPENDENT_REFERENCE"
    with pytest.raises(EvaluationBlocked):
        lock_annotation(source, frozen, template)


@pytest.mark.parametrize("mutation", ["extra", "source", "guide", "request", "frozen", "prefill"])
def test_study_rejects_source_only_leaks_or_changed_frozen_artifacts(study, mutation):
    folder, _, _ = study
    if mutation == "extra":
        (folder / "source_only/model-output.json").write_text("{}")
    else:
        name = {"source": "source_only/SOURCE.json", "guide": "source_only/README.md", "request": "requests.json",
                "frozen": "frozen.json", "prefill": "source_only/ANNOTATION_TEMPLATE.json"}[mutation]
        path = folder / name
        path.write_text(path.read_text(encoding="utf8") + " ", encoding="utf8")
        if mutation in {"request", "frozen"}:
            content = json.loads(path.read_text())
            if mutation == "request":
                content["QUERY-Q"]["options"]["temperature"] = 1
            else:
                content["repetitions"] = 1
            path.write_text(json.dumps(content))
    with pytest.raises(EvaluationBlocked):
        load_study(folder)


def test_rejects_same_document_or_text_across_splits_and_known_development_source():
    original = source_fixture()
    extra = deepcopy(original["cases"][0])
    extra.update(id="DEV", split="DEVELOPMENT")
    original["cases"].append(extra)
    with pytest.raises(EvaluationBlocked, match="document_group"):
        validate_source(original)
    extra["document_group"] = "OTHER"
    with pytest.raises(EvaluationBlocked, match="Nguồn trùng"):
        validate_source(original)
    original = source_fixture()
    original["cases"][0]["requirements"][0]["text"] = oracle_ticket_cases()["OC-02"]["text"]
    with pytest.raises(EvaluationBlocked, match="phát triển"):
        validate_source(original)


def test_previously_sent_source_cannot_become_new_held_out(study):
    folder, _, _ = study
    architecture = validate_source(source_fixture()).cases[0].architecture()
    path = storage.ARTIFACT_ROOT / "quantum-studio/extractions/history/request.json"
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(build_request(architecture, ["Q1"], "QUALITY")))
    with pytest.raises(EvaluationBlocked, match="extraction local"):
        prepare_study(source_fixture(), folder.parent / "second", model_digest=DIGEST, code_sha="a" * 40)


@pytest.mark.parametrize("field,value", [("provenance", "PREPARED_FIXTURE"), ("source_only_attested", False),
    ("no_prior_model_output_exposure", False), ("independent_of_other_annotators", False), ("completed_at", FREEZE.replace("2026", "2025"))])
def test_fixture_exposure_or_bad_order_cannot_lock_annotations(study, field, value):
    _, source, frozen = study
    submission = simulated_reference(source, frozen)["annotation_locks"][0]["submission"]
    submission[field] = value
    with pytest.raises(EvaluationBlocked):
        lock_annotation(source, frozen, submission)


def test_unresolved_is_not_absence_and_annotation_or_reference_tampering_fails(study):
    _, source, frozen = study
    ref = simulated_reference(source, frozen)
    wrong = deepcopy(ref)
    wrong["submission"]["rows"][0]["claims"] = []
    with pytest.raises(EvaluationBlocked):
        verify_reference(source, frozen, wrong)
    wrong = deepcopy(ref)
    wrong["annotation_locks"][0]["submission"]["rows"][0]["status"] = "UNRESOLVED"
    with pytest.raises(EvaluationBlocked):
        verify_reference(source, frozen, wrong)
    with pytest.raises(EvaluationBlocked, match="trước inference"):
        verify_reference(source, frozen, ref, before=ANNOTATED)
    with pytest.raises(EvaluationBlocked, match="khác nhau"):
        adjudicate(source, frozen, [ref["annotation_locks"][0]] * 2, ref["submission"])


def test_blank_or_missing_reference_blocks_before_any_provider_contact(study, monkeypatch):
    folder, _, _ = study
    touched = []
    monkeypatch.setattr(ollama, "list_model_details", lambda: touched.append(True))
    with pytest.raises(EvaluationBlocked):
        run_study(folder, None)
    assert touched == []
    assert not (storage.ARTIFACT_ROOT / "quantum-studio/evaluations").exists()


def test_complete_synthetic_flow_keeps_repetitions_citations_and_policy_fields_separate(study, monkeypatch):
    folder, source, frozen = study
    calls = fake_provider(monkeypatch)
    ref = simulated_reference(source, frozen)
    progress = []
    run = run_study(folder, ref, progress=progress.append)
    report = score_study(folder, run, ref)
    assert len(calls) == 6 and len(report["repetitions"]) == 2
    assert len(progress) == 12 and all(progress[i]["status"] == "REQUESTED" and progress[i + 1]["status"] == "RESPONSE_RECEIVED" for i in range(0, 12, 2))
    assert report["semantic_accuracy"] is None and report["architecture_quality"] == "NOT_MEASURED"
    assert report["eligible_held_out_units"] == 4
    for repeat in report["repetitions"]:
        assert repeat["raw_projectable_fields"]["tp"] == 4
        assert repeat["gate_eligible_fields"]["tp"] == 4
        assert repeat["by_case"]["TEST-CASE"]["eligible_units"] == 4
    assert report["independent_annotation_agreement"] == {"comparable_complete_units": 4, "exact_link_set_agreements": 4}
    assert report["regex_quality_baseline"]["reference_links"] == 2
    assert all(not r.quality_allocations for r in source.cases[0].architecture().requirements)


def test_model_digest_mismatch_blocks_before_inference(study, monkeypatch):
    folder, source, frozen = study
    calls = fake_provider(monkeypatch)
    monkeypatch.setattr(ollama, "list_model_details", lambda: [{"name": "qwen3:4b", "digest": "2" * 64}])
    with pytest.raises(EvaluationBlocked, match="digest"):
        run_study(folder, simulated_reference(source, frozen))
    assert calls == []


def test_provider_failure_keeps_extraction_id_and_failed_call_in_trace(study, monkeypatch):
    folder, source, frozen = study
    fake_provider(monkeypatch)

    def unavailable(*args, **kwargs):
        raise ollama.OllamaError("TEST_ONLY_PROVIDER_UNAVAILABLE")

    monkeypatch.setattr(ollama, "_request", unavailable)
    with pytest.raises(ollama.OllamaError):
        run_study(folder, simulated_reference(source, frozen))
    runs = list((storage.ARTIFACT_ROOT / "quantum-studio/evaluations").glob("*/run.json"))
    assert len(runs) == 1
    manifest = json.loads(runs[0].read_text())
    call = manifest["calls"][0]
    assert manifest["status"] == call["status"] == "FAILED" and call["extraction_id"] and call["manifest_sha256"]
    raw = storage.ARTIFACT_ROOT / "quantum-studio/extractions" / call["extraction_id"] / "manifest.json"
    assert json.loads(raw.read_text())["status"] == "FAILED"
    assert not (runs[0].parent / "report.json").exists()


def test_raw_fields_do_not_equal_gate_eligibility_and_bad_rows_remain_counted(study, monkeypatch):
    folder, source, frozen = study

    def change(task, rows):
        if task == "QUALITY":
            rows[0]["disposition"] = "OUT_OF_SCOPE"  # Still has fields: raw projection stays, gate rejects.
            rows[1]["component_ids"] = ["NOT_IN_CATALOG"]

    fake_provider(monkeypatch, change)
    run = run_study(folder, simulated_reference(source, frozen))
    report = json.loads((run / "report.json").read_text())
    for repeat in report["repetitions"]:
        assert repeat["raw_projectable_fields"]["tp"] == 3
        assert repeat["gate_eligible_fields"]["tp"] == 2
        assert repeat["structural"]["unprojectable_rows"] == 1
        assert repeat["structural"]["rows_with_gate_issues"] == 2


def test_response_edit_missing_call_or_reused_response_is_not_a_valid_experiment(study, monkeypatch):
    folder, source, frozen = study
    fake_provider(monkeypatch)
    ref = simulated_reference(source, frozen)
    run = run_study(folder, ref)
    manifest_path = run / "run.json"
    original = json.loads(manifest_path.read_text())
    for edit in ("missing", "reuse"):
        data = deepcopy(original)
        if edit == "missing":
            data["calls"].pop()
        else:
            data["calls"][1]["extraction_id"] = data["calls"][0]["extraction_id"]
        manifest_path.write_text(json.dumps(data))
        with pytest.raises(EvaluationBlocked):
            score_study(folder, run, ref)
    manifest_path.write_text(json.dumps(original))
    response = storage.ARTIFACT_ROOT / "quantum-studio/extractions" / original["calls"][0]["extraction_id"] / "response.json"
    data = json.loads(response.read_text())
    data["message"]["content"] = '{"proposals": []}'
    response.write_text(json.dumps(data))
    with pytest.raises(EvaluationBlocked, match="raw hash"):
        score_study(folder, run, ref)


def test_atomic_links_keep_direction_transaction_and_condition_without_false_perfect_empty_scores():
    from eqcr.studio_evaluation import _metrics
    claims = reference_claims()
    key = "TEST-CASE/INTERACTION/W1"
    original = claims[key][0]
    swapped = {**original, "source": "B", "target": "A"}
    assert not claim_links(key, original) & claim_links(key, swapped)
    assert not claim_links(key, original) & claim_links(key, {**original, "local_transaction": False})
    quality = claims["TEST-CASE/QUALITY/Q2"][0]
    assert not claim_links("q", quality) & claim_links("q", {**quality, "condition": None})
    assert _metrics(set(), set())["f1"] is None
    assert _metrics(set(), {("missed",)})["recall"] == 0


def test_empty_exclusion_is_an_abstention_not_a_malformed_active_mapping(study, monkeypatch):
    folder, source, frozen = study

    def exclude(task, rows):
        if task == "QUALITY":
            for row in rows:
                row.update(disposition="OUT_OF_SCOPE", characteristic=None, component_ids=[])
                row["frame"].update(effect="NONE")

    fake_provider(monkeypatch, exclude)
    report = json.loads((run_study(folder, simulated_reference(source, frozen)) / "report.json").read_text())
    for repeat in report["repetitions"]:
        assert repeat["structural"]["inactive_empty_rows"] == 2
        assert repeat["structural"].get("unprojectable_rows", 0) == 0
        assert repeat["by_task"]["QUALITY"]["raw_projectable_fields"]["recall"] == 0


def test_unknown_reference_units_are_excluded_with_denominator_and_not_treated_as_negative(study, monkeypatch):
    folder, source, frozen = study
    fake_provider(monkeypatch)
    ref = simulated_reference(source, frozen)
    submission = deepcopy(ref["submission"])
    row = next(row for row in submission["rows"] if row["unit"].endswith("QUALITY/Q2"))
    row.update(status="UNRESOLVED", claims=[], rationale="SIMULATED_UNRESOLVED_TEST_ONLY")
    ref = adjudicate(source, frozen, ref["annotation_locks"], submission, locked_at=ADJUDICATED)
    report = json.loads((run_study(folder, ref) / "report.json").read_text())
    assert report["eligible_held_out_units"] == 3 and report["excluded_units"] == ["TEST-CASE/QUALITY/Q2"]
    assert report["repetitions"][0]["raw_projectable_fields"]["fp"] == 0
    assert report["repetitions"][0]["structural"]["excluded_unresolved_or_development_rows"] == 1


def test_cannot_run_when_every_held_out_reference_is_unresolved(study):
    _, source, frozen = study
    ref = simulated_reference(source, frozen)
    submission = deepcopy(ref["submission"])
    for row in submission["rows"]:
        row.update(status="UNRESOLVED", claims=[])
    reference = adjudicate(source, frozen, ref["annotation_locks"], submission, locked_at=ADJUDICATED)
    with pytest.raises(EvaluationBlocked, match="held-out COMPLETE"):
        verify_reference(source, frozen, reference)


def test_cli_status_reports_null_metrics_and_cannot_write_inside_source_only(study, capsys):
    folder, _, _ = study
    assert main(["status", "--folder", str(folder)]) == 0
    status = json.loads(capsys.readouterr().out)
    assert status["link_metrics"] is None and status["status"] == "BLOCKED_INDEPENDENT_REFERENCE"
    assert main(["lock", "--folder", str(folder), "--submission", str(folder / "source_only/ANNOTATION_TEMPLATE.json"),
                 "--output", str(folder / "source_only/extra.json")]) == 2
    assert not (folder / "source_only/extra.json").exists()
