"""Analytical checks with declared PREPARED_FIXTURE timing assumptions, not measurements."""

from pathlib import Path
import json

import pytest
from streamlit.testing.v1 import AppTest

from eqcr import storage, studio_canvas
from eqcr.models import Scenario, SourceRef
from eqcr.quantum_example import ticket_example
from eqcr.quantum_tradeoff import Architecture, Preferences, analyze, component_profiles
from eqcr.studio_evidence import catalog_digest
from eqcr.studio_scenarios import ReviewedScenario, TimingAssumptions, predict_scenario, review_scenario
from eqcr.studio_sessions import invalidate_changed_sources, load_checkpoint


def latency_case(mode="SYNC", threshold=900):
    text = f"Customer sends a ticket during peak load. Ticket Creation calls Ticket Router and must acknowledge within {threshold} ms."
    data = ticket_example().model_dump(mode="json")
    data["interactions"][0]["mode"] = mode
    data["requirements"].append({"id": "QLAT", "kind": "NFR", "text": text, "component_ids": ["CREATE", "ROUTE"]})
    model = Architecture.model_validate(data)
    record = ReviewedScenario(
        scenario=Scenario(id="SC-LAT", name="Authored latency case", stimulus_source="Customer", stimulus="sends a ticket",
                          environment="during peak load", stimulated_artifact="Ticket Creation", response="must acknowledge",
                          response_measure=f"within {threshold} ms", target=f"{threshold} ms",
                          source_ref=SourceRef(source_id="QLAT", quote=text, start=0, end=len(text))),
        source_digest=model.requirements[-1].input_digest(), catalog_digest=catalog_digest(model),
        characteristic="Performance efficiency", responsible_component_ids=["CREATE", "ROUTE"], component_path=["CREATE", "ROUTE"],
        metric="RESPONSE_LATENCY", target_value=threshold, target_unit="ms",
        assumptions=TimingAssumptions(provenance="PREPARED_FIXTURE", semantics="ASSUMED_UPPER_BOUND_INCLUDING_WAIT",
                                       component_ms={"CREATE": 250, "ROUTE": 350}, sync_round_trip_ms=400,
                                       async_enqueue_ms=10, async_delivery_ms=80, rationale="Authored worst-case bounds including wait; no observations"),
        actor="TEST_ONLY", rationale="Prepared scenario for analytical checks", decision_provenance="PREPARED_FIXTURE",
    )
    return model, record


def candidate(model, identifier):
    return next(item for item in analyze(model, Preferences()).feasible if item.id == identifier)


def test_reviewed_scenario_allocates_iso_and_explains_partition_specific_upper_bounds():
    model, record = latency_case()
    reviewed, event = review_scenario(model, record)
    assert event["action"] == "QUALITY_SCENARIO_REVIEW" and not model.quality_scenarios
    assert component_profiles(reviewed)["CREATE"]["Performance efficiency · QLAT"] == ["QLAT"]
    assert analyze(model, Preferences()) != analyze(reviewed, Preferences())
    together = predict_scenario(reviewed, candidate(reviewed, "P031"), record)
    split = predict_scenario(reviewed, candidate(reviewed, "P011"), record)
    assert (together["predicted_upper_ms"], split["predicted_upper_ms"]) == (600, 1000)
    assert together["target_comparison"] == "UPPER_BOUND_WITHIN_TARGET"
    assert split["target_comparison"] == "UPPER_BOUND_EXCEEDS_TARGET"
    for profile in (together, split):
        assert profile["measurement_status"] == "NOT_MEASURED" and profile["measurement"] is None
        assert profile["prediction_status"] == "PREDICTED_UPPER_BOUND"
        assert sum(item["upper_ms"] for item in profile["drivers"]) == profile["predicted_upper_ms"]
        assert all(item["provenance"] == "PREPARED_FIXTURE" for item in profile["drivers"])


def test_responsibility_scope_is_separate_from_workflow_context():
    model, record = latency_case()
    record = record.model_copy(update={"responsible_component_ids": ["CREATE"]})
    reviewed, _ = review_scenario(model, record)
    profiles = component_profiles(reviewed)
    assert "Performance efficiency · QLAT" in profiles["CREATE"]
    assert "Performance efficiency · QLAT" not in profiles["ROUTE"]
    profile = predict_scenario(reviewed, candidate(reviewed, "P011"), record)
    assert profile["scope"] == ["CREATE"] and profile["component_path"] == ["CREATE", "ROUTE"]


def test_changed_target_requires_review_and_changes_profile_comparison_without_faking_a_measurement():
    model, record = latency_case()
    reviewed, _ = review_scenario(model, record)
    newer_model, newer_record = latency_case(threshold=9000)
    raw = reviewed.model_dump(mode="json")
    raw["requirements"][-1] = newer_model.requirements[-1].model_dump(mode="json")
    revised = invalidate_changed_sources(reviewed, Architecture.model_validate(raw))
    stale = predict_scenario(revised, candidate(revised, "P011"), record)
    assert stale["prediction_status"] == "INSUFFICIENT_EVIDENCE" and stale["target_ms"] is None
    confirmed, _ = review_scenario(revised, newer_record)
    profile = predict_scenario(confirmed, candidate(confirmed, "P011"), newer_record)
    assert profile["predicted_upper_ms"] == 1000 and profile["target_ms"] == 9000
    assert profile["target_comparison"] == "UPPER_BOUND_WITHIN_TARGET" and profile["measurement_status"] == "NOT_MEASURED"


@pytest.mark.parametrize("missing", ["scenario_part", "whitespace_part", "timing", "mode", "target", "adapter"])
def test_unknown_inputs_never_produce_a_prediction(missing):
    model, record = latency_case()
    raw = record.model_dump(mode="json")
    if missing == "scenario_part":
        raw["scenario"]["environment"] = None
    elif missing == "whitespace_part":
        raw["scenario"]["environment"] = "   "
    elif missing == "timing":
        raw["assumptions"]["component_ms"]["ROUTE"] = None
    elif missing == "target":
        raw["target_value"] = 9  # Source says 900 ms; a substring token is insufficient.
    elif missing == "adapter":
        raw["metric"] = "UNSUPPORTED"
    else:
        changed = model.model_dump(mode="json")
        changed["interactions"][0]["mode"] = "UNKNOWN"
        model = Architecture.model_validate(changed)
    profile = predict_scenario(model, candidate(model, "P011"), ReviewedScenario.model_validate(raw))
    assert profile["issues"] and profile["predicted_upper_ms"] is None
    assert profile["prediction_status"] == "INSUFFICIENT_EVIDENCE" and profile["target_comparison"] == "UNKNOWN"


@pytest.mark.parametrize("value", [float("nan"), float("inf"), -1, True])
def test_invalid_numerical_assumptions_are_rejected(value):
    _, record = latency_case()
    raw = record.model_dump(mode="json")
    raw["assumptions"]["component_ms"]["CREATE"] = value
    with pytest.raises(ValueError):
        ReviewedScenario.model_validate(raw)


def test_overflowing_aggregate_bound_abstains_and_remains_json_serializable():
    model, record = latency_case()
    raw = record.model_dump(mode="json")
    raw["assumptions"]["component_ms"] = {"CREATE": 1e308, "ROUTE": 1e308}
    profile = predict_scenario(model, candidate(model, "P031"), ReviewedScenario.model_validate(raw))
    assert profile["predicted_upper_ms"] is None and profile["prediction_status"] == "INSUFFICIENT_EVIDENCE"
    json.dumps(profile, allow_nan=False)


def test_async_acknowledgement_and_business_completion_have_distinct_scopes():
    model, record = latency_case(mode="ASYNC")
    chosen = candidate(model, "P011")
    business = predict_scenario(model, chosen, record)
    ack = predict_scenario(model, chosen, record.model_copy(update={"completion": "CALLER_RESPONSE"}))
    assert business["predicted_upper_ms"] == 680
    assert ack["predicted_upper_ms"] == 260
    assert not any(item["subject"] == "ROUTE" for item in ack["drivers"])


def test_recovery_budget_covers_all_components_in_the_affected_quantum():
    data = ticket_example().model_dump(mode="json")
    text = "Monitor notices a stopped reporting process under normal reporting load. Operations Reporting must restore service within 10 min."
    data["requirements"].append({"id": "QREC", "kind": "NFR", "text": text})
    model = Architecture.model_validate(data)
    record = ReviewedScenario(
        scenario=Scenario(id="SC-REC", name="Authored recovery", stimulus_source="Monitor", stimulus="a stopped reporting process",
                          environment="under normal reporting load", stimulated_artifact="Operations Reporting", response="restore service",
                          response_measure="within 10 min", target="10 min",
                          source_ref=SourceRef(source_id="QREC", quote=text, start=0, end=len(text))),
        source_digest=model.requirements[-1].input_digest(), catalog_digest=catalog_digest(model),
        characteristic="Reliability", responsible_component_ids=["REPORT"], component_path=["REPORT"], metric="RECOVERY_TIME",
        target_value=10, target_unit="min",
        assumptions=TimingAssumptions(provenance="PREPARED_FIXTURE", semantics="ASSUMED_UPPER_BOUND_INCLUDING_WAIT",
                                       component_ms={"REPORT": 100000, "LOGIN": 300000, "PROFILE": 300000}, detection_ms=5000,
                                       rationale="Entire Quantum restarts sequentially; authored component bounds include state restoration"),
        actor="TEST_ONLY", rationale="Authored recovery scenario", decision_provenance="PREPARED_FIXTURE",
    )
    isolated = predict_scenario(model, candidate(model, "P031"), record)
    combined = predict_scenario(model, candidate(model, "P029"), record)
    assert (isolated["predicted_upper_ms"], combined["predicted_upper_ms"]) == (105000, 705000)
    assert isolated["target_ms"] == combined["target_ms"] == 600000
    assert combined["target_comparison"] == "UPPER_BOUND_EXCEEDS_TARGET"


def test_partial_scenario_can_be_saved_but_retains_unknown_target_and_no_prediction():
    model, record = latency_case()
    data = record.model_dump(mode="json")
    data.update(target_value=None, target_unit=None)
    data["scenario"]["target"] = None
    data["scenario"]["stimulus_source"] = None
    partial = ReviewedScenario.model_validate(data)
    reviewed, _ = review_scenario(model, partial)
    profile = predict_scenario(reviewed, candidate(reviewed, "P031"), partial)
    assert profile["scenario_parts"]["stimulus_source"]["provenance"] == "UNKNOWN"
    assert profile["target_ms"] is None and profile["predicted_upper_ms"] is None


def test_ui_review_persists_scenario_allocation_and_prediction_trace(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "ARTIFACT_ROOT", tmp_path)
    captures = []
    monkeypatch.setattr(studio_canvas, "render_board", lambda **kwargs: captures.append(kwargs))
    model, record = latency_case()
    view = AppTest.from_file(Path(__file__).parents[1] / "app.py", default_timeout=30)
    view.session_state.architecture = model
    view.run()

    def widget(kind, label):
        return next(item for item in getattr(view, kind) if item.label == label)

    widget("selectbox", "NFR cho quality scenario").select("QLAT").run()
    widget("selectbox", "Adapter dự đoán").select("RESPONSE_LATENCY").run()
    from eqcr.studio_scenario_ui import PART_LABELS

    for field, label in PART_LABELS.items():
        widget("text_input", label).set_value(getattr(record.scenario, field))
    widget("text_input", "Ngưỡng mục tiêu").set_value("900")
    widget("selectbox", "Đơn vị mục tiêu").select("ms")
    widget("text_input", "Đoạn nguồn chứa ngưỡng").set_value("900 ms")
    widget("text_input", "Giới hạn Ticket Creation (ms)").set_value("250")
    widget("text_input", "Giới hạn Ticket Router (ms)").set_value("350")
    widget("text_input", "Giới hạn RTT SYNC qua Quantum (ms)").set_value("400")
    widget("text_area", "Căn cứ và giới hạn của giả định thời gian").set_value("TEST ONLY assumed worst-case bounds, no observations")
    widget("selectbox", "Nguồn giả định thời gian").select("PREPARED_FIXTURE")
    widget("selectbox", "Nguồn quyết định scenario").select("PREPARED_FIXTURE")
    widget("text_area", "Lý do xác nhận scenario và phạm vi component").set_value("TEST ONLY scenario mapping")
    widget("checkbox", "Tôi khai báo các giá trị đã điền là giới hạn trên giả định, đã gồm thời gian chờ").check().run()
    widget("button", "Xác nhận scenario và tính lại").click().run()
    assert not view.exception
    saved = load_checkpoint(view.session_state.studio_checkpoint)
    assert saved["event"]["action"] == "QUALITY_SCENARIO_REVIEW"
    assert saved["architecture"]["quality_scenarios"]
    assert any(plan["quality_profiles"] for plan in captures[-1]["plans"])
    next(item for item in view.button if item.label.startswith("Chọn A")).click().run()
    assert not view.exception
    assert all(item["quality_profiles"] for item in view.session_state.studio_last_review["comparison"])
    assert view.session_state.studio_last_review["input_provenance"] == "MIXED_WITH_PREPARED_SCENARIO_DATA"
    assert widget("selectbox", "Scenario đã lưu").value == "QS-01"
    widget("text_area", "Lý do xác nhận scenario và phạm vi component").set_value("TEST ONLY remove profile, retain reviewed ISO allocation")
    widget("button", "Gỡ scenario đã chọn").click().run()
    assert not view.exception and not view.session_state.architecture.quality_scenarios
    assert view.session_state.architecture.requirements[-1].quality_allocations
    assert load_checkpoint(view.session_state.studio_checkpoint)["event"]["action"] == "QUALITY_SCENARIO_REMOVED"
