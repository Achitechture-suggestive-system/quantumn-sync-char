import json
from pathlib import Path

import pytest
from pydantic import ValidationError
from streamlit.testing.v1 import AppTest

from eqcr import storage, studio_canvas
from eqcr.quantum_example import ticket_example
from eqcr.quantum_tradeoff import Architecture, Preferences, analyze, component_profiles, explain_candidate, group_index
from eqcr.studio_quality import QualityCharacteristic, component_mentions, quality_suggestions
from eqcr.studio_views import requirement_cards, review_receipt


def test_ticket_example_reproduces_both_tradeoffs_and_reverses_ranking():
    architecture = ticket_example()
    result = analyze(architecture, Preferences())
    assert (result.enumerated, len(result.feasible), len(result.frontier)) == (203, 37, 2)
    keep_data, separate = result.ranked
    assert keep_data.groups == (("LOGIN", "PROFILE"), ("CREATE", "ROUTE", "COMPLETE"), ("REPORT",))
    assert keep_data.vector == (0, 0, 1, 1, 1)
    assert separate.groups == (("LOGIN", "PROFILE", "CREATE"), ("ROUTE", "COMPLETE"), ("REPORT",))
    assert separate.vector == (0, 1, 0, 0, 0)
    assert (keep_data.score(Preferences()), separate.score(Preferences())) == (5, 6)
    assert analyze(architecture, Preferences(characteristics=4)).ranked == (separate, keep_data)
    assert analyze(architecture, Preferences(), ranking="SYNC_FIRST").ranked == (separate, keep_data)
    assert analyze(architecture, Preferences(), ranking="CHARACTERISTIC_FIRST").ranked == (separate, keep_data)
    for item in result.feasible:
        assignment = group_index(item.groups)
        assert assignment["LOGIN"] == assignment["PROFILE"]
        assert assignment["LOGIN"] != assignment["ROUTE"]
        assert set(assignment) == {component.id for component in architecture.components}
    for candidate in result.frontier:
        drivers = explain_candidate(architecture, candidate)
        assert tuple(sum(item.units for item in drivers if item.axis == axis) for axis in range(5)) == candidate.vector
    assert [(item.subject, item.components, item.quanta) for item in explain_candidate(architecture, separate)] == [
        ("Ticket DB", ("CREATE", "ROUTE", "COMPLETE"), (1, 2))
    ]


def test_cross_group_sync_soft_cost_unknown_edge_and_hard_conflict():
    raw = {
        "components": [{"id": "A", "name": "Alpha"}, {"id": "B", "name": "Beta"}],
        "interactions": [{"source": "A", "target": "B", "mode": "SYNC", "weight": 3}],
        "keep_apart": [{"left": "A", "right": "B", "basis": "Test independent boundary."}],
    }
    result = analyze(Architecture.model_validate(raw), Preferences())
    assert len(result.feasible) == 1
    assert result.ranked[0].sync == 3
    raw["interactions"][0]["mode"] = "UNKNOWN"
    assert analyze(Architecture.model_validate(raw), Preferences()).ranked[0].sync == 0
    raw["interactions"][0].update(mode="SYNC", local_transaction=True, basis="Test local transaction.")
    assert analyze(Architecture.model_validate(raw), Preferences()).ranked == ()
    raw["interactions"][0]["target"] = "UNKNOWN"
    with pytest.raises(ValidationError, match="component chưa khai báo"):
        Architecture.model_validate(raw)


def test_sync_first_retains_stronger_sync_under_hard_separation():
    architecture = Architecture.model_validate({
        "components": [
            {"id": "A", "name": "Alpha", "characteristics": ["Security"]},
            {"id": "B", "name": "Beta", "characteristics": ["Security"]},
            {"id": "C", "name": "Gamma", "characteristics": ["Latency"]},
        ],
        "interactions": [
            {"source": "A", "target": "B", "mode": "SYNC", "weight": 2},
            {"source": "B", "target": "C", "mode": "SYNC", "weight": 5},
        ],
        "keep_apart": [{"left": "A", "right": "C", "basis": "Test independent boundary."}],
    })
    weights = Preferences(sync=1, characteristics=4)
    balanced = analyze(architecture, weights).ranked[0]
    sync_first = analyze(architecture, weights, ranking="SYNC_FIRST").ranked[0]
    assert balanced.groups == (("A", "B"), ("C",))
    assert sync_first.groups == (("A",), ("B", "C"))
    assert sync_first.sync == 2
    assert sync_first.score(weights) > balanced.score(weights)
    sync_weights = Preferences(characteristics=0)
    assert analyze(architecture, sync_weights).ranked[0].groups == sync_first.groups
    by_characteristic = analyze(architecture, sync_weights, ranking="CHARACTERISTIC_FIRST").ranked[0]
    assert by_characteristic.groups == (("A", "B"), ("C",))
    assert (by_characteristic.characteristic_spread, by_characteristic.characteristic_mix) == (0, 0)
    assert by_characteristic.sync == 5

    model = architecture.model_dump(mode="json")
    model["interactions"][1].update(local_transaction=True, basis="Beta and Gamma share an atomic write.")
    constrained = analyze(Architecture.model_validate(model), sync_weights, ranking="CHARACTERISTIC_FIRST").ranked
    assert [item.groups for item in constrained] == [(("A",), ("B", "C"))]


@pytest.mark.parametrize(("links", "message"), [
    ({"Unassigned characteristic": ["REQ-01"]}, "chưa được gán characteristic"),
    ({"Freshness": ["REQ-99"]}, "requirement chưa khai báo"),
    ({"Freshness": ["REQ-01", "REQ-01"]}, "requirement trùng"),
])
def test_invalid_requirement_links_are_rejected(links, message):
    with pytest.raises(ValidationError, match=message):
        Architecture.model_validate({
            "requirements": [{"id": "REQ-01", "text": "Index new content."}],
            "components": [{"id": "INDEXER", "name": "Indexer", "characteristics": ["Freshness"],
                            "characteristic_requirements": links}],
        })


def test_nfr_suggestions_are_multi_label_and_return_verbatim_evidence():
    text = "Ticket Router phải đạt p95 200 ms, xác thực yêu cầu và khôi phục sau lỗi."
    assert quality_suggestions(text) == {
        QualityCharacteristic.PERFORMANCE_EFFICIENCY: "p95",
        QualityCharacteristic.RELIABILITY: "khôi phục",
        QualityCharacteristic.SECURITY: "xác thực",
    }
    assert component_mentions(text, {"ROUTE": "Ticket Router", "ROUTER": "Router Worker", "PORT": "Port"}) == {
        "ROUTE": "Ticket Router",
    }
    assert not quality_suggestions("The solution should feel modern.")


def test_nfr_confirmation_scopes_the_optimizer_inputs_and_rejects_stale_evidence():
    original = ticket_example()
    raw = original.model_dump(mode="json")
    source = next(item for item in raw["requirements"] if item["id"] == "NFR-01")
    assignment = {"characteristic": "Performance efficiency", "component_ids": ["CREATE", "ROUTE"],
                  "source_quote": "thời gian phản hồi"}
    source["quality_allocations"] = [assignment]
    confirmed = Architecture.model_validate(raw)
    profiles = component_profiles(confirmed)
    label = "Performance efficiency · NFR-01"
    assert profiles["CREATE"][label] == profiles["ROUTE"][label] == ["NFR-01"]
    assert label not in profiles["COMPLETE"]
    assert analyze(original, Preferences(), ranking="CHARACTERISTIC_FIRST").ranked[0].id == "P011"
    assert analyze(confirmed, Preferences(), ranking="CHARACTERISTIC_FIRST").ranked[0].id == "P031"
    assignment["source_quote"] = "mốc không có trong NFR"
    with pytest.raises(ValidationError, match="đoạn trích ISO không khớp"):
        Architecture.model_validate(raw)
    assignment.update(source_quote="", component_ids=["IMAGINED"])
    with pytest.raises(ValidationError, match="component ISO trùng hoặc chưa khai báo"):
        Architecture.model_validate(raw)


def test_studio_review_records_explicit_choice_and_tradeoff_after_reweighting(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "ARTIFACT_ROOT", tmp_path)
    event = {"token": "test-1", "action": "analyze", "model": ticket_example().model_dump(mode="json")}
    views = []

    def board(**kwargs):
        views.append(kwargs)
        return event

    monkeypatch.setattr(studio_canvas, "render_board", board)
    app = AppTest.from_file(Path(__file__).parents[1] / "app.py", default_timeout=30).run()
    assert not app.exception
    assert app.metric[-1].value == "P011 · 6 điểm"
    plan = views[-1]["plans"][0]
    assert plan["groups"][1]["characteristic_sources"] == {"Nhất quán luồng ticket": ["ROUTE", "COMPLETE"]}
    ticket_trace = {"Nhất quán luồng ticket": {"ROUTE": ["REQ-02"], "COMPLETE": ["REQ-02"]}}
    assert plan["groups"][1]["characteristic_requirements"] == ticket_trace
    assert [(edge["mode"], edge["from_quantum"], edge["to_quantum"], edge["placement"]) for edge in plan["interactions"]] == [
        ("ASYNC", "Q1", "Q2", "CROSS_QUANTUM"),
        ("SYNC", "Q2", "Q2", "INTERNAL"),
    ]
    output_selector = next(widget for widget in app.radio if widget.label == "Phương án hiển thị trên sơ đồ")
    output_selector.set_value("A").run()
    shown = next(item for item in views[-1]["plans"] if item["id"] == views[-1]["active_plan"])
    assert shown["label"].startswith("A · P031")
    assert any(item.value == f"Theo sơ đồ đang hiển thị · {shown['label']}" for item in app.caption)
    next(button for button in app.button if button.label == "Ưu tiên giữ dữ liệu").click().run()
    assert not app.exception
    assert app.metric[-1].value == "P031 · 5 điểm"
    assert not list(tmp_path.rglob("*.json"))
    next(button for button in app.button if button.label == "Ưu tiên tập trung đặc tính").click().run()
    assert not app.exception
    assert app.metric[-1].value == "P011 · 6 điểm"
    assert not list(tmp_path.rglob("*.json"))
    next(widget for widget in app.text_input if widget.label == "Ghi chú review").set_value("AppTest-only decision")
    next(button for button in app.button if button.label == "Chọn B · P011").click().run()
    assert not app.exception
    [path] = list(tmp_path.rglob("review-*.json"))
    review = json.loads(path.read_text(encoding="utf-8"))
    assert review["selected_candidate"] == "P011"
    assert review["ranking"] == "WEIGHTED"
    assert review["recommended_candidate"] == "P011"
    assert review["displayed_candidate"] == "P031"
    assert review["baseline_under_default_weights"] == "P031"
    assert review["preferences"]["characteristics"] == 4
    assert review["note"] == "AppTest-only decision"
    assert [item["score"] for item in review["comparison"][:2]] == [9, 6]
    assert len({item["id"] for item in review["comparison"]}) == 3
    third = review["comparison"][2]
    assert third["slot"] == "C" and not third["pareto"] and third["dominated_by"]
    assert review["comparison"][1]["cost_drivers"][0]["subject"] == "Ticket DB"
    assert review["comparison"][1]["interaction_routing"] == plan["interactions"]
    assert review["architecture"]["requirements"][1]["id"] == "REQ-02"
    assert review["recommended_plan"]["groups"][1]["characteristic_requirements"] == ticket_trace
    assert review["comparison"][1]["quantum_profiles"][1]["characteristic_requirements"] == ticket_trace
    next(button for button in app.button if button.label == f"Chọn C · {third['id']}").click().run()
    assert not app.exception
    saved = [json.loads(item.read_text(encoding="utf-8")) for item in tmp_path.rglob("review-*.json")]
    assert {item["selected_candidate"] for item in saved} == {"P011", third["id"]}


def test_studio_visual_report_keeps_user_text_literal():
    raw = '<custom-note title="draft">Nội dung</custom-note>'
    architecture = Architecture.model_validate({
        "components": [{"id": "A", "name": "Component A"}],
        "requirements": [{"id": "REQ-01", "text": raw}],
    })
    trace = requirement_cards(architecture, {"groups": []}, {})
    receipt = review_receipt({
        "selected_candidate": None, "comparison": [], "note": raw, "recorded_at": "2026-01-01T08:00:00+00:00",
    })
    for html in (trace, receipt):
        assert raw not in html
        assert "&lt;custom-note" in html and "&gt;" in html


@pytest.mark.parametrize("scope", [["MISSING"], ["PROFILE", "PROFILE"]])
def test_requirement_rejects_invalid_component_scope(scope):
    data = ticket_example().model_dump(mode="json")
    data["requirements"][-1]["component_ids"] = scope
    with pytest.raises(ValidationError, match="component phụ trách trùng hoặc chưa khai báo"):
        Architecture.model_validate(data)


def test_declared_requirement_scope_feeds_iso_review_and_quantum_trace(monkeypatch, tmp_path):
    monkeypatch.setattr(storage, "ARTIFACT_ROOT", tmp_path)
    architecture = ticket_example()
    event = {"token": "scope-fixture", "action": "analyze", "model": architecture.model_dump(mode="json")}
    views = []

    def board(**kwargs):
        views.append(kwargs)
        return event

    monkeypatch.setattr(studio_canvas, "render_board", board)
    app = AppTest.from_file(Path(__file__).parents[1] / "app.py").run()
    next(widget for widget in app.selectbox if widget.label == "NFR nguồn").select("NFR-03").run()
    assert not app.exception
    assert next(widget for widget in app.multiselect if widget.label == "Component ứng viên").value == ["PROFILE"]
    assert not any("Security · NFR-03" in group["characteristic_requirements"]
                   for plan in views[-1]["plans"] for group in plan["groups"])

    next(widget for widget in app.button if widget.label == "Xác nhận gán ISO").click().run()
    assert not app.exception
    for plan in views[-1]["plans"]:
        group_id = plan["assignment"]["PROFILE"]
        group = next(item for item in plan["groups"] if item["id"] == group_id)
        assert group["characteristic_requirements"]["Security · NFR-03"] == {"PROFILE": ["NFR-03"]}


def test_loading_llm_case_keeps_inputs_draft_until_explicit_iso_review(monkeypatch, tmp_path):
    monkeypatch.setattr(storage, "ARTIFACT_ROOT", tmp_path)
    from eqcr.studio_cases import case_requirements, ticket_requirement_cases

    cases = ticket_requirement_cases()
    selected_case, source = next((case, item) for case in cases.values() for item in case_requirements(case)
                                 if item.model_suggestion)
    captured = []

    def board(**kwargs):
        captured.append(kwargs)

    monkeypatch.setattr(studio_canvas, "render_board", board)
    app = AppTest.from_file(Path(__file__).parents[1] / "app.py").run()
    next(widget for widget in app.selectbox if widget.label == "Kịch bản Ticket Support").select(selected_case["id"]).run()
    next(widget for widget in app.multiselect if widget.label == "Requirement để nạp vào sơ đồ").set_value([source.id]).run()
    next(widget for widget in app.button if widget.label == "Nạp requirement đã chọn").click().run()
    assert not app.exception
    architecture = Architecture.model_validate(captured[-1]["model"])
    assert architecture.requirements[-1] == source
    assert source.matches_generated_input
    assert component_profiles(architecture) == component_profiles(ticket_example())

    next(widget for widget in app.selectbox if widget.label == "NFR nguồn").select(source.id).run()
    label, quote = source.model_suggestion
    assert next(widget for widget in app.selectbox if widget.label == "Characteristic ISO").value == label
    next(widget for widget in app.button if widget.label == "Xác nhận gán ISO").click().run()
    assert not app.exception
    accepted = Architecture.model_validate(captured[-1]["model"]).requirements[-1]
    assert accepted.quality_allocations[0].source_quote == quote
    assert accepted.matches_generated_input
    assert accepted.model_copy(update={"text": "Đã sửa tại Studio."}).model_suggestion is None
    shown = next(plan for plan in captured[-1]["plans"] if plan["id"] == captured[-1]["active_plan"])
    assert any(f"{label} · {source.id}" in group["characteristic_requirements"] for group in shown["groups"])


def test_canvas_edits_recompute_generic_groups_and_keep_layout_separate(monkeypatch, tmp_path):
    monkeypatch.setattr(storage, "ARTIFACT_ROOT", tmp_path)
    model = {
        "requirements": [{"id": "REQ-01", "text": "Index and serve new content promptly."}],
        "components": [
            {"id": "INDEXER", "name": "Indexer", "characteristics": ["Freshness"],
             "characteristic_requirements": {"Freshness": ["REQ-01"]}},
            {"id": "QUERY", "name": "Query", "characteristics": ["Latency"]},
        ]
    }
    event = {"token": "generic-1", "action": "analyze", "model": model,
             "layout": {"component:INDEXER": [0.4, 0.25], "component:DELETED": [0.1, 0.1]}}
    views = []

    def board(**kwargs):
        views.append(kwargs)
        return event

    monkeypatch.setattr(studio_canvas, "render_board", board)
    app = AppTest.from_file(Path(__file__).parents[1] / "app.py", default_timeout=30).run()
    assert not app.exception
    assert views[-1]["plans"][0]["assignment"] == {"INDEXER": "Q1", "QUERY": "Q2"}
    assert views[-1]["layout"] == {"component:INDEXER": [0.4, 0.25]}
    next(button for button in app.button if button.label == "Chia theo characteristics").click().run()
    assert app.session_state.studio_ranking == "CHARACTERISTIC_FIRST"

    event.update(token="generic-2", action="dirty")
    app.run()
    assert views[-1]["pending"] is True
    assert not app.metric
    model["components"][1]["characteristics"] = ["Freshness"]
    model["components"][1]["characteristic_requirements"] = {"Freshness": ["REQ-01"]}
    event.update(token="generic-3", action="analyze")
    app.run()
    assert not app.exception
    assert views[-1]["pending"] is False
    assert views[-1]["plans"][0]["assignment"] == {"INDEXER": "Q1", "QUERY": "Q1"}
    assert views[-1]["plans"][0]["groups"][0]["characteristic_requirements"] == {
        "Freshness": {"INDEXER": ["REQ-01"], "QUERY": ["REQ-01"]},
    }
