"""Frozen Studio extraction experiments and exact declared-link evaluation.

No reference is inferred from quotes, fixtures, model self-judgment or optimization scores.
"""

from __future__ import annotations

from collections import Counter
from hashlib import sha256
from importlib.metadata import version
import json
from pathlib import Path
import platform
import subprocess
import sys
import time
from uuid import uuid4

from . import ollama, storage
from .studio_extraction import extract_proposals, proposal_issues
from .studio_quality import component_mentions, quality_suggestions
from .studio_evaluation_trace import VerifiedProposal, artifact_hashes, token_metadata, verify_sentence_trace
from .studio_evaluation_protocol import (ROOT, MATCHING, PROTOCOL, EvaluationBlocked, _write_new, claim_links,
    check_unplanned_exposure, digest, load_study, now, source_units, timestamp, unit_key, validate_claim, verify_reference)


def git_state() -> dict:
    def git(*args):
        return subprocess.check_output(["git", *args], cwd=ROOT, text=True, encoding="utf-8").strip()
    return {"sha": git("rev-parse", "HEAD"), "dirty": bool(git("status", "--porcelain"))}


def check_revision(frozen):
    state = git_state()
    if state["dirty"]:
        raise EvaluationBlocked("Checkout cần sạch trước inference nghiên cứu.")
    changed = subprocess.check_output(["git", "diff", "--name-only", frozen["code_sha"], "HEAD", "--", "eqcr", "scripts",
        "app.py", "research_app.py", "requirements.txt", "pyproject.toml"], cwd=ROOT, text=True, encoding="utf-8").strip()
    if changed:
        raise EvaluationBlocked("Mã thực thi đã đổi từ commit freeze. Chốt protocol mới thay vì chấm output bằng mã đã tune.")
    return state


def _read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def readiness(folder: Path, reference: dict | None = None) -> dict:
    source, frozen = load_study(folder)
    result = {"study_digest": frozen["study_digest"], "protocol": PROTOCOL, "units": len(source_units(source)),
              "method": frozen["method"], "prompt_version": frozen["prompt_version"],
              "queries": len(source.queries), "model_inference": False, "semantic_accuracy": None,
              "link_metrics": None, "review_identity": "SELF_REPORTED_NOT_AUTHENTICATED"}
    try:
        verify_reference(source, frozen, reference, before=now())
    except (ValueError, TypeError, KeyError) as exc:
        return {**result, "status": "BLOCKED_INDEPENDENT_REFERENCE", "reason": str(exc)}
    return {**result, "status": "REFERENCE_LOCK_VALIDATED", "reason": "Vẫn cần kiểm code/model/runtime trước inference."}


def _save_progress(path, manifest):
    # Updates only this newly allocated run's status; raw extraction directories remain immutable.
    (path / "run.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def run_study(folder: Path, reference: dict | None, *, progress=None) -> Path:
    source, frozen = load_study(folder)
    started = now()
    verify_reference(source, frozen, reference, before=started)  # Before any provider or model call.
    check_unplanned_exposure(source, frozen)
    state = check_revision(frozen)
    details = next((item for item in ollama.list_model_details() if item["name"] == frozen["model"]), None)
    if details is None or details.get("digest") != frozen["model_digest"]:
        raise EvaluationBlocked("Exact qwen3:4b model digest khác freeze hoặc chưa có model.")
    ollama_version = ollama.get_ollama_version()
    identifier = f"study-run-{uuid4().hex}"
    path = storage.ARTIFACT_ROOT / "quantum-studio" / "evaluations" / identifier
    path.mkdir(parents=True, exist_ok=False)
    manifest = {"protocol": PROTOCOL, "id": identifier, "study_digest": frozen["study_digest"],
        "method": frozen["method"], "prompt_version": frozen["prompt_version"],
        "reference_digest": reference["reference_digest"], "inference_started_at": started,
        "git": state, "python": sys.version, "platform": platform.platform(), "pydantic": version("pydantic"),
        "ollama_version": ollama_version, "model": frozen["model"], "model_digest": frozen["model_digest"],
        "repetitions": frozen["repetitions"], "status": "RUNNING", "calls": [], "semantic_accuracy": None}
    _write_new(path / "reference.json", reference)
    _save_progress(path, manifest)
    cases = {case.id: case for case in source.cases}
    try:
        for repetition in range(frozen["repetitions"]):
            for query in source.queries:
                call_started, clock_started = now(), time.monotonic()
                record = {"query_id": query.id, "repetition": repetition, "started_at": call_started, "status": "REQUESTED"}
                manifest["calls"].append(record)
                _save_progress(path, manifest)
                if progress:
                    progress({"id": identifier, **record})

                def allocated(extraction_id):
                    record["extraction_id"] = extraction_id
                    _save_progress(path, manifest)

                run = extract_proposals(cases[query.case_id].architecture(), query.source_ids, query.task, frozen["model"],
                                        method=frozen["method"], on_run_allocated=allocated)
                run_folder = storage.ARTIFACT_ROOT / "quantum-studio" / "extractions" / run["id"]
                record.update(extraction_id=run["id"], completed_at=now(), elapsed_seconds=time.monotonic() - clock_started,
                              status="RESPONSE_RECEIVED", manifest_sha256=sha256((run_folder / "manifest.json").read_bytes()).hexdigest(),
                              artifact_hashes=artifact_hashes(run_folder), provider_calls=len(run.get("stages", [])) or 1,
                              **token_metadata(run))
                if run.get("model_digest") != frozen["model_digest"] or run.get("ollama_version") != ollama_version:
                    raise EvaluationBlocked("Model/runtime thay đổi giữa study; giữ run lỗi, không chấm như cùng cấu hình.")
                _save_progress(path, manifest)
                if progress:
                    progress({"id": identifier, **record})
        manifest.update(status="COMPLETE", inference_completed_at=now())
        _save_progress(path, manifest)
        report = score_study(folder, path, reference)
        _write_new(path / "report.json", report)
    except Exception as exc:
        if manifest["calls"] and manifest["calls"][-1]["status"] == "REQUESTED":
            failed = manifest["calls"][-1]
            failed.update(status="FAILED", completed_at=now(), error=str(exc))
            if failed.get("extraction_id"):
                raw = storage.ARTIFACT_ROOT / "quantum-studio" / "extractions" / failed["extraction_id"] / "manifest.json"
                if raw.is_file():
                    failed["manifest_sha256"] = sha256(raw.read_bytes()).hexdigest()
        manifest.update(status="FAILED", error=str(exc), failed_at=now())
        _save_progress(path, manifest)
        raise
    return path


def _verify_response(source, frozen, query, call, manifest):
    identifier = call.get("extraction_id", "")
    if not isinstance(identifier, str) or not identifier.startswith("studio-extraction-") or len(identifier) != 50 or any(ch not in "0123456789abcdef" for ch in identifier[18:]):
        raise EvaluationBlocked("Extraction ID không hợp lệ.")
    root = storage.ARTIFACT_ROOT / "quantum-studio" / "extractions" / identifier
    raw_manifest = (root / "manifest.json").read_bytes()
    if sha256(raw_manifest).hexdigest() != call.get("manifest_sha256"):
        raise EvaluationBlocked("Extraction manifest đã đổi.")
    extraction = json.loads(raw_manifest)
    request, response = _read(root / "request.json"), _read(root / "response.json")
    canonical_request_hash = sha256(json.dumps(request, ensure_ascii=False, sort_keys=True).encode()).hexdigest()
    content = response.get("message", {}).get("content")
    if not isinstance(content, str) or digest(request) != frozen["request_digests"][query.id] or canonical_request_hash != extraction.get("request_sha256") or sha256(content.encode()).hexdigest() != extraction.get("response_sha256"):
        raise EvaluationBlocked("Request/response không khớp freeze hoặc raw hash.")
    if extraction.get("id") != identifier or extraction.get("model") != frozen["model"] or extraction.get("model_digest") != frozen["model_digest"] or response.get("model") != frozen["model"] or response.get("done_reason") != "stop" or extraction.get("status") != "REVIEW_REQUIRED" or extraction.get("task") != query.task or extraction.get("prompt_version") != frozen["prompt_version"]:
        raise EvaluationBlocked("Extraction chưa hoàn tất hoặc provenance/model/prompt/task không khớp.")
    if not timestamp(manifest["inference_started_at"]) <= timestamp(call["started_at"]) <= timestamp(extraction["recorded_at"]) <= timestamp(call["completed_at"]) <= timestamp(manifest["inference_completed_at"]):
        raise EvaluationBlocked("Khoảng inference/response không nhất quán.")
    if call.get("artifact_hashes") != artifact_hashes(root):
        raise EvaluationBlocked("Raw stage artifact đã đổi so với query trace.")
    if extraction.get("ollama_version") != manifest.get("ollama_version"):
        raise EvaluationBlocked("Runtime extraction khác study.")
    if frozen["method"] == "SENTENCE":
        architecture = next(case for case in source.cases if case.id == query.case_id).architecture()
        verified, counts = verify_sentence_trace(root, architecture, query, extraction, call, frozen)
        if call.get("provider_calls") != counts["provider_calls"] or any(call.get(k) != v for k, v in token_metadata(extraction).items()):
            raise EvaluationBlocked("Query cost metadata khác raw stages.")
        return verified, counts
    payloads = json.loads(content).get("proposals")
    if not isinstance(payloads, list):
        raise EvaluationBlocked("Raw output thiếu proposals array.")
    stored = []
    for proposal in extraction.get("proposals", []):
        payload = dict(proposal["payload"])
        payload.pop("kind", None)
        stored.append({**payload, "source_id": proposal["source_id"]})
    if stored != payloads:
        raise EvaluationBlocked("Proposal payload đã được sửa so với raw output.")
    if call.get("provider_calls") != 1 or any(call.get(k) != v for k, v in token_metadata(extraction).items()):
        raise EvaluationBlocked("Query cost metadata khác raw response.")
    return [VerifiedProposal(raw) for raw in payloads], Counter(provider_calls=1)


def _metrics(predicted, expected):
    tp, fp, fn = len(predicted & expected), len(predicted - expected), len(expected - predicted)
    return {"tp": tp, "fp": fp, "fn": fn, "predicted_links": len(predicted), "reference_links": len(expected),
            "precision": tp / (tp + fp) if tp + fp else None,
            "recall": tp / (tp + fn) if tp + fn else None,
            "f1": 2 * tp / (2 * tp + fp + fn) if 2 * tp + fp + fn else None}


def score_study(folder: Path, run_folder: Path, reference: dict | None) -> dict:
    source, frozen = load_study(folder)
    manifest = _read(run_folder / "run.json")
    verify_reference(source, frozen, reference, before=manifest.get("inference_started_at"))
    if manifest.get("protocol") != PROTOCOL or manifest.get("study_digest") != frozen["study_digest"] or manifest.get("reference_digest") != reference["reference_digest"] or manifest.get("status") != "COMPLETE" or manifest.get("model") != frozen["model"] or manifest.get("model_digest") != frozen["model_digest"] or manifest.get("method") != frozen["method"] or manifest.get("prompt_version") != frozen["prompt_version"]:
        raise EvaluationBlocked("Run không hoàn tất hoặc không gắn đúng source/reference/model.")
    if _read(run_folder / "reference.json") != reference:
        raise EvaluationBlocked("Reference của run đã bị thay thế.")
    calls = manifest.get("calls", [])
    expected_calls = {(repeat, q.id) for repeat in range(frozen["repetitions"]) for q in source.queries}
    if not isinstance(calls, list) or len(calls) != len(expected_calls) or {(c.get("repetition"), c.get("query_id")) for c in calls} != expected_calls:
        raise EvaluationBlocked("Thiếu/thừa repetition/query; không chọn riêng những response tốt để chấm.")
    if len({c.get("extraction_id") for c in calls}) != len(calls):
        raise EvaluationBlocked("Không dùng một response làm nhiều repetition.")
    cases, queries, units = {c.id: c for c in source.cases}, {q.id: q for q in source.queries}, source_units(source)
    rows = {row["unit"]: row for row in reference["submission"]["rows"]}
    eligible = {key for key, row in rows.items() if row["status"] == "COMPLETE" and units[key][0].split == "HELD_OUT"}
    expected = set().union(*(claim_links(key, claim) for key in eligible for claim in rows[key]["claims"]))
    per_repeat = []
    structural = Counter()
    for repeat in range(frozen["repetitions"]):
        raw_links, gated_links = set(), set()
        count = Counter()
        for call in calls:
            if call["repetition"] != repeat:
                continue
            query = queries[call["query_id"]]
            case = cases[query.case_id]
            architecture = case.architecture()
            payloads, trace_counts = _verify_response(source, frozen, query, call, manifest)
            count.update(trace_counts)
            for verified in payloads:
                raw = verified.raw
                count["returned_rows"] += 1
                if not isinstance(raw, dict) or raw.get("source_id") not in query.source_ids:
                    count["invalid_source_or_row"] += 1
                    continue
                key = unit_key(case.id, query.task, raw["source_id"])
                if key not in eligible:
                    count["excluded_unresolved_or_development_rows"] += 1
                    continue
                payload = {**{k: v for k, v in raw.items() if k != "source_id"}, "kind": query.task}
                source_requirement = units[key][2]
                quote = raw.get("quote")
                count["exact_quote_rows"] += bool(isinstance(quote, str) and quote.strip() and quote in source_requirement.text)
                count[f"disposition_{raw.get('disposition', 'MISSING')}"] += 1
                issues = proposal_issues(architecture, raw["source_id"], payload, structured=True, source_ref=verified.source_ref)
                if verified.duplicate:
                    issues.append("Duplicate raw claim in same sentence unit.")
                count["rows_with_gate_issues"] += bool(issues)
                active = (bool(raw.get("characteristic") is not None or raw.get("component_ids")) if query.task == "QUALITY" else
                          bool(raw.get("source") or raw.get("target") or raw.get("local_transaction") or raw.get("mode", "UNKNOWN") != "UNKNOWN") if query.task == "INTERACTION" else
                          bool(raw.get("left") or raw.get("right")))
                if not active and raw.get("disposition") in {"OUT_OF_SCOPE", "AMBIGUOUS"}:
                    count["inactive_empty_rows"] += 1
                    continue
                fields = {"QUALITY": ("characteristic", "component_ids"), "INTERACTION": ("source", "target", "mode", "local_transaction"), "SEPARATION": ("left", "right")}[query.task]
                frame = raw.get("frame")
                claim = {"kind": query.task, "quote": quote, "condition": frame.get("condition") if isinstance(frame, dict) else None,
                         **{field: raw.get(field) for field in fields}}
                try:
                    validate_claim(case, query.task, source_requirement, claim)
                except (ValueError, TypeError, KeyError):
                    count["unprojectable_rows"] += 1
                    continue
                links = claim_links(key, claim)
                count["duplicate_projected_links"] += len(raw_links & links)
                raw_links.update(links)
                if not issues and raw.get("disposition") == "PROPOSED":
                    gated_links.update(links)
        structural.update(count)
        task_metrics = {}
        for task in ("QUALITY", "INTERACTION", "SEPARATION"):
            prefix = f"/{task}/"
            truth = {link for link in expected if prefix in link[0]}
            task_metrics[task] = {"raw_projectable_fields": _metrics({x for x in raw_links if prefix in x[0]}, truth),
                                  "gate_eligible_fields": _metrics({x for x in gated_links if prefix in x[0]}, truth)}
        case_metrics = {}
        for case in source.cases:
            prefix = case.id + "/"
            truth = {link for link in expected if link[0].startswith(prefix)}
            case_metrics[case.id] = {"document_group": case.document_group, "split": case.split,
                "eligible_units": sum(key.startswith(prefix) for key in eligible),
                "raw_projectable_fields": _metrics({x for x in raw_links if x[0].startswith(prefix)}, truth),
                "gate_eligible_fields": _metrics({x for x in gated_links if x[0].startswith(prefix)}, truth)}
        per_repeat.append({"repetition": repeat, "raw_projectable_fields": _metrics(raw_links, expected),
            "gate_eligible_fields": _metrics(gated_links, expected), "by_task": task_metrics, "by_case": case_metrics, "structural": dict(count),
            "false_hard_policy_fields_relative_to_reference": {name: sum("/SEPARATION/" in item[0] or "/INTERACTION/" in item[0] and item[-1] is True for item in links - expected)
                                                               for name, links in (("raw_projectable", raw_links), ("gate_eligible", gated_links))}})
    # Deterministic lexical baseline applies only to QUALITY; other tasks are not silently scored as empty predictions.
    regex_links, regex_truth = set(), {link for link in expected if "/QUALITY/" in link[0]}
    for key in eligible:
        case, task, requirement = units[key]
        if task == "QUALITY":
            mentions = component_mentions(requirement.text, {c.id: c.name for c in case.components})
            for characteristic in quality_suggestions(requirement.text):
                regex_links.update((key, None, str(characteristic), owner) for owner in mentions)
    comparable, equal = 0, 0
    first, second = [{row["unit"]: row for row in lock["submission"]["rows"]} for lock in reference["annotation_locks"]]
    for key in eligible:
        if first[key]["status"] == second[key]["status"] == "COMPLETE":
            comparable += 1
            one = set().union(*(claim_links(key, c) for c in first[key]["claims"]))
            two = set().union(*(claim_links(key, c) for c in second[key]["claims"]))
            equal += one == two
    return {"protocol": PROTOCOL, "matching": MATCHING, "study_digest": frozen["study_digest"],
        "method": frozen["method"], "prompt_version": frozen["prompt_version"],
        "reference_digest": reference["reference_digest"], "run_id": manifest["id"], "status": "EXACT_LINK_FIELDS_EVALUATED",
        "semantic_accuracy": None, "architecture_quality": "NOT_MEASURED", "reference_provenance": "HUMAN_SOURCE_ONLY_SELF_ATTESTED",
        "reference_identity": "SELF_REPORTED_NOT_AUTHENTICATED", "matching_scope": "PROJECTABLE_FIELDS_WITH_EXACT_CONDITION; NOT_FULL_ENTAILMENT",
        "eligible_held_out_units": len(eligible), "total_units": len(units), "excluded_units": sorted(set(units) - eligible),
        "independent_annotation_agreement": {"comparable_complete_units": comparable, "exact_link_set_agreements": equal},
        "repetitions": per_repeat, "structural_totals": dict(structural),
        "regex_quality_baseline": {"policy": "LEXICAL_LABELS_X_ALL_EXPLICIT_COMPONENT_MENTIONS; CONDITION_NULL", **_metrics(regex_links, regex_truth)},
        "unsupported_baselines": ["REGEX_INTERACTION", "REGEX_SEPARATION"],
        "query_costs": [{"repetition": c["repetition"], "query_id": c["query_id"], "provider_calls": c["provider_calls"],
                         "tokens": c["tokens"], "tokens_observed": c["tokens_observed"], "token_reporting": c["token_reporting"],
                         "elapsed_seconds": c["elapsed_seconds"]} for c in calls],
        "provenance": {"claim_and_frame_fields": "LLM_PROPOSAL", "reference": "HUMAN_DECISION_SELF_ATTESTED",
                       "quote": "LLM_PROPOSAL" if frozen["method"] == "DIRECT" else "SOURCE_REQUIREMENT_VIA_DETERMINISTIC_SPAN_LOOKUP",
                       "metrics_and_regex": "DETERMINISTIC_TRANSFORMATION", "matching_and_gate": "ARCHITECTURAL_POLICY"},
        "limitations": ["Quote/condition validity is structural, not entailment.", "Unprojectable/invalid rows are counted separately, never reported as true links.",
            "Raw projectable fields include populated claims even if disposition contradicts them; gate eligibility is separate.",
            "Empty denominators produce null, never a perfect score.", "Repetitions share reference cases; they are not independent new case samples.",
            "No human-reviewed metric or downstream architectural agreement is inferred from raw extraction.",
            "SENTENCE quote exactness is deterministic source lookup, not a model citation score.",
            "Two calls to the same model are not independent judges; condition/frame can still be semantically wrong."]}
