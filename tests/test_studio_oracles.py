from pathlib import Path

from streamlit.testing.v1 import AppTest

from eqcr import storage, studio_canvas
from eqcr.quantum_example import ticket_example
from eqcr.quantum_tradeoff import Architecture, Preferences, analyze, group_index
from eqcr.studio_oracles import matches_oracle, oracle_ticket_cases, replay_architecture


def test_all_replays_validate_against_outcomes_and_preserve_baseline_until_applied():
    cases = oracle_ticket_cases()
    base = analyze(ticket_example(), Preferences())
    assert list(cases) == [f"OC-{number:02d}" for number in range(1, 13)]
    for case in cases.values():
        draft = replay_architecture(case, "draft")
        assert draft.requirements[-1].text == case["text"]
        assert draft.requirements[-1].quality_allocations == []
        assert analyze(draft, Preferences()) == base
        result = analyze(replay_architecture(case, "oracle"), Preferences())
        assert matches_oracle(result, case["expected"])

    conflict = cases["OC-10"]
    saved_model = replay_architecture(conflict, "saved_model")
    actual = analyze(saved_model, Preferences())
    assert matches_oracle(actual, conflict["saved_model"]["expected"])
    assert len(actual.feasible) == 10
    assert all(group_index(c.groups)["ROUTE"] == group_index(c.groups)["COMPLETE"] for c in actual.feasible)


def test_studio_replays_use_the_real_canvas_and_restore_previous_workspace(monkeypatch, tmp_path):
    monkeypatch.setattr(storage, "ARTIFACT_ROOT", tmp_path)
    example = ticket_example().model_dump(mode="json")
    example["requirements"].append({"id": "MY-FR", "kind": "FR", "text": "Local Studio draft."})
    event = {"token": "start", "action": "analyze", "model": example}
    captures = []

    def canvas(**data):
        captures.append(data)
        return event

    def widget(view, kind, label):
        return next(item for item in getattr(view, kind) if item.label == label)

    monkeypatch.setattr(studio_canvas, "render_board", canvas)
    view = AppTest.from_file(Path(__file__).parents[1] / "app.py", default_timeout=30).run()
    layout = {"component:LOGIN": [0.37, 0.28]}
    event.update(token="move", action="layout", layout=layout)
    view.run()
    widget(view, "button", "Chia theo characteristics").click().run()
    widget(view, "button", "Chạy cả 12 ca").click().run()
    assert any(item.value == "12/12 ca khớp oracle của bộ giải." for item in view.markdown)

    widget(view, "selectbox", "Ca kiểm thử").select("OC-01").run()
    widget(view, "button", "Nạp ca vào sơ đồ").click().run()
    draft = Architecture.model_validate(captures[-1]["model"])
    assert draft.requirements[-1].id == "OC-01" and not draft.requirements[-1].quality_allocations
    assert view.metric[-1].value == "P031 · 5 điểm"

    widget(view, "radio", "Chế độ nạp").set_value("oracle").run()
    widget(view, "button", "Nạp ca vào sơ đồ").click().run()
    assert view.metric[-1].value == "P011 · 8 điểm"
    shown = next(plan for plan in captures[-1]["plans"] if plan["id"] == captures[-1]["active_plan"])
    assert shown["assignment"]["LOGIN"] == shown["assignment"]["CREATE"]
    assert not any(heading.value == "Human Review" for heading in view.header)

    widget(view, "selectbox", "Ca kiểm thử").select("OC-10").run()
    for mode, feasible in [("oracle", False), ("saved_model", True)]:
        widget(view, "radio", "Chế độ nạp").set_value(mode).run()
        widget(view, "button", "Nạp ca vào sơ đồ").click().run()
        assert bool(captures[-1]["plans"]) == feasible
        assert captures[-1]["no_solution"] != feasible
        if not feasible:
            for index, message in enumerate(("10 nghiệm khả thi · P031 xếp đầu · 5 điểm", "27 nghiệm khả thi · P008 xếp đầu · 16 điểm")):
                widget(view, "selectbox", "Xem chi tiết mô phỏng").select(index).run()
                assert any(message in row.value for row in view.markdown)
                assert captures[-1]["no_solution"]
                assert captures[-1]["model"] == replay_architecture(oracle_ticket_cases()["OC-10"], "oracle").model_dump(mode="json")
    assert view.metric[1].value == "10"

    widget(view, "button", "Quay lại sơ đồ của tôi").click().run()
    assert not view.exception
    assert Architecture.model_validate(captures[-1]["model"]) == Architecture.model_validate(example)
    assert captures[-1]["layout"] == layout
    assert view.session_state.studio_ranking == "CHARACTERISTIC_FIRST"
    assert any(heading.value == "Human Review" for heading in view.header)
