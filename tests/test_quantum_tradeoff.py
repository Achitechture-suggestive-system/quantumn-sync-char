import json
from pathlib import Path

import pytest
from pydantic import ValidationError
from streamlit.testing.v1 import AppTest

from eqcr import storage, studio_canvas
from eqcr.quantum_example import ticket_example
from eqcr.quantum_tradeoff import Architecture, Preferences, analyze, explain_candidate, group_index


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
    next(button for button in app.button if button.label == "Ưu tiên giữ dữ liệu").click().run()
    assert not app.exception
    assert app.metric[-1].value == "P031 · 5 điểm"
    assert not list(tmp_path.rglob("*.json"))
    next(button for button in app.button if button.label == "Ưu tiên tập trung đặc tính").click().run()
    assert not app.exception
    assert app.metric[-1].value == "P011 · 6 điểm"
    assert not list(tmp_path.rglob("*.json"))
    app.text_input[0].set_value("AppTest-only decision")
    next(button for button in app.button if button.label == "Chọn B · P011").click().run()
    assert not app.exception
    [path] = list(tmp_path.rglob("review-*.json"))
    review = json.loads(path.read_text(encoding="utf-8"))
    assert review["selected_candidate"] == "P011"
    assert review["ranking"] == "WEIGHTED"
    assert review["recommended_candidate"] == "P011"
    assert review["baseline_under_default_weights"] == "P031"
    assert review["preferences"]["characteristics"] == 4
    assert review["note"] == "AppTest-only decision"
    assert [item["score"] for item in review["comparison"]] == [9, 6]
    assert review["comparison"][1]["cost_drivers"][0]["subject"] == "Ticket DB"
    assert review["comparison"][1]["interaction_routing"] == plan["interactions"]
    assert review["architecture"]["requirements"][1]["id"] == "REQ-02"
    assert review["recommended_plan"]["groups"][1]["characteristic_requirements"] == ticket_trace
    assert review["comparison"][1]["quantum_profiles"][1]["characteristic_requirements"] == ticket_trace


def test_canvas_edits_recompute_generic_groups_and_keep_layout_separate(monkeypatch):
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
