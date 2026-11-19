import json
from pathlib import Path

import pytest
from pydantic import ValidationError
from streamlit.testing.v1 import AppTest

from eqcr import storage
from eqcr.quantum_example import ticket_example
from eqcr.quantum_tradeoff import Architecture, Preferences, analyze, group_index


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
    for item in result.feasible:
        assignment = group_index(item.groups)
        assert assignment["LOGIN"] == assignment["PROFILE"]
        assert assignment["LOGIN"] != assignment["ROUTE"]
        assert set(assignment) == {component.id for component in architecture.components}


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


def test_studio_review_records_explicit_choice_and_tradeoff_after_reweighting(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "ARTIFACT_ROOT", tmp_path)
    app = AppTest.from_file(Path(__file__).parents[1] / "app.py", default_timeout=30).run()
    next(button for button in app.button if button.label == "Phân tích Quantum").click().run()
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
    assert review["baseline_under_default_weights"] == "P031"
    assert review["preferences"]["characteristics"] == 4
    assert review["note"] == "AppTest-only decision"
    assert [item["score"] for item in review["comparison"]] == [9, 6]
