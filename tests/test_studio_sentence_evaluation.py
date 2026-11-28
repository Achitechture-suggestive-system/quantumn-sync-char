"""Prepared traces/attestations test protocol integrity; never real human annotations."""

from copy import deepcopy
from hashlib import sha256
import json

import pytest

from eqcr import ollama, storage
import eqcr.studio_evaluation as experiment
from eqcr.studio_evaluation import readiness, run_study, score_study
from eqcr.studio_evaluation_protocol import (EvaluationBlocked, PROTOCOL, digest, load_study, prepare_study)
from eqcr.studio_evaluation_trace import artifact_hashes
from eqcr.studio_sentence_extraction import digest as stage_digest
from test_studio_evaluation import DIGEST, FREEZE, simulated_reference, source_fixture


@pytest.fixture
def study(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "ARTIFACT_ROOT", tmp_path / "runs")
    folder = tmp_path / "study"
    prepare_study(source_fixture(), folder, model_digest=DIGEST, code_sha="a" * 40,
                  repetitions=2, prepared_at=FREEZE, method="SENTENCE")
    source, frozen = load_study(folder)
    return folder, source, frozen


def provider(monkeypatch, *, transform_primary=None, fail_at=None, omit_frame_tokens=False):
    monkeypatch.setattr(experiment, "check_revision", lambda frozen: {"sha": "a" * 40, "dirty": False})
    monkeypatch.setattr(ollama, "list_model_details", lambda: [{"name": "qwen3:4b", "digest": DIGEST}])
    monkeypatch.setattr(ollama, "get_ollama_version", lambda: "TEST_ONLY_RUNTIME")
    calls = []

    def reply(endpoint, *, payload, timeout):
        calls.append(payload)
        if len(calls) == fail_at:
            raise ollama.OllamaError("TEST_ONLY_SENTENCE_FRAME_FAILURE")
        content = json.loads(payload["messages"][1]["content"])
        if "units" in content:
            fields = payload["format"]["properties"]["results"]["items"]["properties"]["claims"]["items"]["properties"]
            task = "QUALITY" if "characteristic" in fields else "INTERACTION" if "mode" in fields else "SEPARATION"
            rows = []
            for unit in content["units"]:
                text = unit["text"]
                claims = []
                if task == "QUALITY" and ("return" in text or "recover" in text):
                    claims = [{"characteristic": "Performance efficiency" if "return" in text else "Reliability", "component_ids": ["A"]}]
                elif task == "INTERACTION" and "wait" in text:
                    claims = [{"source": "A", "target": "B", "mode": "SYNC", "local_transaction": True}]
                elif task == "SEPARATION" and "different Quanta" in text:
                    claims = [{"left": "A", "right": "B"}]
                rows.append({"unit_id": unit["unit_id"], "claims": claims})
            if transform_primary:
                transform_primary(task, rows)
            result = {"results": rows}
        else:
            text, task = content["sentence"], content["task"]
            result = {"subject": "Processor", "object": None if task == "QUALITY" else "Archive",
                "action": "recover" if "recover" in text else "return" if task == "QUALITY" else "wait" if task == "INTERACTION" else "remain",
                "condition": "If Archive is stopped" if "recover" in text else None,
                "modality": "shall" if "recover" in text else "must", "statement_kind": "OBLIGATION",
                "effect": "QUALITY_OBLIGATION" if task == "QUALITY" else "LOCAL_ATOMIC_TRANSACTION" if task == "INTERACTION" else "REQUIRE_SEPARATION"}
        response = {"model": "qwen3:4b", "done_reason": "stop", "eval_count": 40,
                    "message": {"content": json.dumps(result)}}
        if omit_frame_tokens and "sentence" in content:
            response.pop("eval_count")
        return response

    monkeypatch.setattr(ollama, "_request", reply)
    return calls


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def write(path, value):
    path.write_text(json.dumps(value), encoding="utf-8")


def reseal(run_folder, call_index, mutate):
    """Reseal ordinary checksums to test recipe/lineage validation beyond file hashes."""
    manifest = read(run_folder / "run.json")
    call = manifest["calls"][call_index]
    root = storage.ARTIFACT_ROOT / "quantum-studio/extractions" / call["extraction_id"]
    extraction = read(root / "manifest.json")
    mutate(root, extraction, call)
    write(root / "manifest.json", extraction)
    call["manifest_sha256"] = sha256((root / "manifest.json").read_bytes()).hexdigest()
    call["artifact_hashes"] = artifact_hashes(root)
    write(run_folder / "run.json", manifest)


def test_freezes_secondary_recipe_separately_from_blank_source_only_package(study):
    folder, _, frozen = study
    plan = read(folder / "execution.json")
    assert frozen["protocol"] == PROTOCOL == "STUDIO-EVALUATION@2"
    assert plan["prompt_version"] == "STUDIO-EXTRACT@3" and plan["maximum_provider_calls_per_query"] == 25
    template = plan["secondary_requests"]["QUERY-Q"]["frame_templates"]["U001"]
    assert json.loads(template["messages"][1]["content"])["unverified_focus"] == {"participant_names": [], "quality_hint": None}
    assert set(path.name for path in (folder / "source_only").iterdir()) == {"SOURCE.json", "README.md", "ANNOTATION_TEMPLATE.json", "MANIFEST.json"}
    assert readiness(folder)["method"] == "SENTENCE" and readiness(folder)["link_metrics"] is None


def test_no_reference_cannot_contact_provider_in_sentence_mode(study, monkeypatch):
    folder, _, _ = study
    touched = []
    monkeypatch.setattr(ollama, "list_model_details", lambda: touched.append(True))
    with pytest.raises(EvaluationBlocked):
        run_study(folder, None)
    assert not touched and not (storage.ARTIFACT_ROOT / "quantum-studio/evaluations").exists()


@pytest.mark.parametrize("change", ["template", "method", "prompt", "unit"])
def test_recipe_drift_fails_even_if_outer_frozen_digest_is_recomputed(study, change):
    folder, _, frozen = study
    plan = read(folder / "execution.json")
    if change == "method":
        frozen["method"] = "DIRECT"
    elif change == "prompt":
        frozen["prompt_version"] = "STUDIO-EXTRACT@2"
    elif change == "unit":
        plan["secondary_requests"]["QUERY-Q"]["units"][0]["start"] += 1
    else:
        plan["secondary_requests"]["QUERY-Q"]["frame_templates"]["U001"]["options"]["seed"] = 99
    write(folder / "execution.json", plan)
    frozen["execution_plan_digest"] = digest(plan)
    frozen["study_digest"] = digest({k: v for k, v in frozen.items() if k != "study_digest"})
    write(folder / "frozen.json", frozen)
    with pytest.raises(EvaluationBlocked):
        load_study(folder)


def test_sentence_flow_scores_both_stages_and_keeps_measured_costs_and_origins_separate(study, monkeypatch):
    folder, source, frozen = study
    calls = provider(monkeypatch)
    ref = simulated_reference(source, frozen)
    run = run_study(folder, ref)
    report = score_study(folder, run, ref)
    assert report["method"] == "SENTENCE" and len(calls) == 14
    assert report["semantic_accuracy"] is None and report["architecture_quality"] == "NOT_MEASURED"
    assert report["structural_totals"]["provider_calls"] == 14
    assert sum(item["provider_calls"] for item in report["query_costs"]) == 14
    assert sum(item["tokens"] for item in report["query_costs"]) == 560
    assert report["provenance"]["quote"] == "SOURCE_REQUIREMENT_VIA_DETERMINISTIC_SPAN_LOOKUP"
    for repeat in report["repetitions"]:
        assert repeat["raw_projectable_fields"]["tp"] == repeat["gate_eligible_fields"]["tp"] == 4
        assert repeat["structural"]["sentence_unit_rows"] == 6
        assert repeat["structural"]["empty_sentence_unit_rows"] == 2
    assert all(not r.quality_allocations for r in source.cases[0].architecture().requirements)


@pytest.mark.parametrize("change", ["request", "focus", "frame", "lineage", "claim", "drop", "time", "model", "provenance"])
def test_resealed_stage_cannot_change_recipe_raw_lineage_or_omit_drafts(study, monkeypatch, change):
    folder, source, frozen = study
    provider(monkeypatch)
    ref = simulated_reference(source, frozen)
    run = run_study(folder, ref)

    def alter(root, extraction, call):
        if change in {"request", "focus"}:
            path = root / "frame-001-request.json"
            value = read(path)
            if change == "request":
                value["options"]["seed"] += 1
            else:
                data = json.loads(value["messages"][1]["content"])
                data["unverified_focus"]["participant_names"] = ["Archive"]
                value["messages"][1]["content"] = json.dumps(data)
            write(path, value)
            extraction["stages"][1]["request_sha256"] = stage_digest(value)
        elif change in {"frame", "model"}:
            path = root / "frame-001-response.json"
            value = read(path)
            if change == "model":
                value["model"] = "DIFFERENT_TEST_MODEL"
            else:
                data = json.loads(value["message"]["content"])
                data["action"] = "remain"
                value["message"]["content"] = json.dumps(data)
            write(path, value)
            extraction["stages"][1]["response_sha256"] = sha256(value["message"]["content"].encode()).hexdigest()
        elif change == "lineage":
            extraction["proposals"][0]["processing"]["unit"]["start"] += 1
        elif change == "claim":
            extraction["proposals"][0]["payload"]["component_ids"] = ["B"]
        elif change == "drop":
            extraction["proposals"].pop()
            extraction["stages"].pop()
            call["provider_calls"] -= 1
        elif change == "time":
            extraction["stages"][1]["recorded_at"] = FREEZE
        else:
            processing = extraction["proposals"][0]["processing"]
            processing["field_origins"]["quote_and_source_ref"] = "LLM_PROPOSAL"
            processing["digest"] = stage_digest({k: v for k, v in processing.items() if k != "digest"})

    reseal(run, 0, alter)
    with pytest.raises(EvaluationBlocked):
        score_study(folder, run, ref)


def test_later_frame_failure_preserves_raw_primary_and_stops_without_report(study, monkeypatch):
    folder, source, frozen = study
    calls = provider(monkeypatch, fail_at=2)
    with pytest.raises(ollama.OllamaError, match="FRAME_FAILURE"):
        run_study(folder, simulated_reference(source, frozen))
    run_file = next((storage.ARTIFACT_ROOT / "quantum-studio/evaluations").glob("*/run.json"))
    manifest = read(run_file)
    call = manifest["calls"][0]
    root = storage.ARTIFACT_ROOT / "quantum-studio/extractions" / call["extraction_id"]
    assert len(calls) == 2 and manifest["status"] == call["status"] == "FAILED"
    assert (root / "claims-response.json").is_file() and (root / "frame-001-request.json").is_file()
    assert read(root / "manifest.json")["stages"][-1]["status"] == "FAILED"
    assert not (run_file.parent / "report.json").exists()


def test_primary_missing_unknown_units_remain_reported_not_disguised_as_processed_negatives(study, monkeypatch):
    folder, source, frozen = study
    def replace(task, rows):
        if task == "QUALITY":
            rows[0]["unit_id"] = "UNKNOWN_TEST_UNIT"
    provider(monkeypatch, transform_primary=replace)
    report = read(run_study(folder, simulated_reference(source, frozen)) / "report.json")
    for repeat in report["repetitions"]:
        assert repeat["structural"]["missing_sentence_units"] == repeat["structural"]["invalid_sentence_unit_rows"] == 1
        assert repeat["structural"]["unmapped_claims_in_invalid_units"] == 1
        assert repeat["raw_projectable_fields"]["fn"] == 1


def test_empty_claim_arrays_have_no_fabricated_frames_and_keep_false_negatives(study, monkeypatch):
    folder, source, frozen = study
    def abstain(task, rows):
        for row in rows:
            row["claims"] = []
    calls = provider(monkeypatch, transform_primary=abstain)
    report = read(run_study(folder, simulated_reference(source, frozen)) / "report.json")
    assert len(calls) == 6
    for repeat in report["repetitions"]:
        assert repeat["raw_projectable_fields"]["fn"] == 4
        assert repeat["raw_projectable_fields"]["precision"] is None and repeat["raw_projectable_fields"]["recall"] == 0


def test_repeated_quote_uses_exact_source_offset_and_reports_duplicate_links(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "ARTIFACT_ROOT", tmp_path / "runs")
    raw = source_fixture()
    requirement = raw["cases"][0]["requirements"][0]
    requirement["text"] = "Processor must return a receipt within 450 ms. " + requirement["text"]
    folder = tmp_path / "repeated"
    prepare_study(raw, folder, model_digest=DIGEST, code_sha="a" * 40, repetitions=1, prepared_at=FREEZE, method="SENTENCE")
    source, frozen = load_study(folder)
    provider(monkeypatch)
    report = read(run_study(folder, simulated_reference(source, frozen)) / "report.json")
    assert report["repetitions"][0]["gate_eligible_fields"]["tp"] == 4
    assert report["structural_totals"]["duplicate_projected_links"] == 1
    assert report["structural_totals"].get("rows_with_gate_issues", 0) == 0


def test_source_format_one_remains_readable_without_reusing_old_execution_locks(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "ARTIFACT_ROOT", tmp_path / "runs")
    raw = source_fixture()
    raw["schema_id"] = "STUDIO-EVALUATION@1"
    frozen = prepare_study(raw, tmp_path / "study", model_digest=DIGEST, code_sha="a" * 40, method="SENTENCE")
    source, loaded = load_study(tmp_path / "study")
    assert source.schema_id == "STUDIO-EVALUATION@1" and loaded["protocol"] == PROTOCOL
    assert frozen["source_digest"] == digest(source.model_dump(mode="json"))


@pytest.mark.parametrize("location,shape", [("extractions/old/frame-001-request.json", "sentence"),
    ("development-probes/probe/request.json", "sentence"), ("development-probes/probe/request.json", "units"),
    ("extractions/old/request.json", "sources")])
def test_prior_sentence_or_probe_exposure_cannot_become_held_out(tmp_path, monkeypatch, location, shape):
    monkeypatch.setattr(storage, "ARTIFACT_ROOT", tmp_path / "runs")
    text = "Processor must return a receipt within 450 ms."  # Only part of Q1, not its full text.
    body = {"sentence": text} if shape == "sentence" else {shape: [{"text": text}]}
    path = storage.ARTIFACT_ROOT / "quantum-studio" / location
    path.parent.mkdir(parents=True)
    write(path, {"messages": [{"role": "user", "content": json.dumps(body)}]})
    with pytest.raises(EvaluationBlocked, match="extraction local"):
        prepare_study(source_fixture(), tmp_path / "study", model_digest=DIGEST, code_sha="a" * 40, method="SENTENCE")


def test_unplanned_exposure_after_freeze_blocks_before_any_provider_contact(study, monkeypatch):
    folder, source, frozen = study
    path = storage.ARTIFACT_ROOT / "quantum-studio/development-probes/late/request.json"
    path.parent.mkdir(parents=True)
    write(path, {"messages": [{"role": "user", "content": json.dumps({"sentence": "Processor must return a receipt within 450 ms."})}]})
    touched = []
    monkeypatch.setattr(ollama, "list_model_details", lambda: touched.append(True))
    with pytest.raises(EvaluationBlocked, match="exposure"):
        run_study(folder, simulated_reference(source, frozen))
    assert not touched


def test_history_drift_is_not_silently_removed_from_exposure_ledger(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "ARTIFACT_ROOT", tmp_path / "runs")
    path = storage.ARTIFACT_ROOT / "quantum-studio/development-probes/history/request.json"
    path.parent.mkdir(parents=True)
    write(path, {"messages": [{"role": "user", "content": json.dumps({"sentence": "An unrelated source sentence."})}]})
    folder = tmp_path / "study"
    prepare_study(source_fixture(), folder, model_digest=DIGEST, code_sha="a" * 40, method="SENTENCE", prepared_at=FREEZE)
    source, frozen = load_study(folder)
    path.unlink()  # Temp fixture only; no actual run/history is deleted.
    with pytest.raises(EvaluationBlocked, match="lịch sử"):
        run_study(folder, simulated_reference(source, frozen))


def test_completed_study_cannot_be_rerun_selectively_as_an_unexposed_new_run(study, monkeypatch):
    folder, source, frozen = study
    calls = provider(monkeypatch)
    reference = simulated_reference(source, frozen)
    run_study(folder, reference)
    size = len(calls)
    with pytest.raises(EvaluationBlocked, match="exposure"):
        run_study(folder, reference)
    assert len(calls) == size


def test_duplicate_unit_rows_and_claims_are_counted_and_never_promoted_by_scoring(study, monkeypatch):
    folder, source, frozen = study
    def duplicate(task, rows):
        if task == "QUALITY":
            rows.append(deepcopy(rows[0]))
    provider(monkeypatch, transform_primary=duplicate)
    report = read(run_study(folder, simulated_reference(source, frozen)) / "report.json")
    for repeat in report["repetitions"]:
        assert repeat["structural"]["duplicate_sentence_unit_ids"] == 1
        assert repeat["structural"]["duplicate_projected_links"] == 1
        assert repeat["structural"]["rows_with_gate_issues"] == 1
        assert repeat["gate_eligible_fields"]["tp"] == 4


def test_unrecognized_prior_request_blocks_instead_of_being_ignored(study, monkeypatch):
    folder, source, frozen = study
    path = storage.ARTIFACT_ROOT / "quantum-studio/development-probes/unknown/request.json"
    path.parent.mkdir(parents=True)
    write(path, {"messages": [{"role": "user", "content": "Unrecognized free-form development prompt"}]})
    touched = []
    monkeypatch.setattr(ollama, "list_model_details", lambda: touched.append(True))
    with pytest.raises(EvaluationBlocked, match="exposure request"):
        run_study(folder, simulated_reference(source, frozen))
    assert not touched


def test_missing_token_metadata_is_partial_and_never_reported_as_complete_zero_cost(study, monkeypatch):
    folder, source, frozen = study
    provider(monkeypatch, omit_frame_tokens=True)
    report = read(run_study(folder, simulated_reference(source, frozen)) / "report.json")
    assert all(cost["tokens"] is None and cost["tokens_observed"] == 40 and cost["token_reporting"] == "PARTIAL"
               for cost in report["query_costs"])
    assert report["semantic_accuracy"] is None
