import json
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from eqcr import studio_canvas, studio_llm
from eqcr.ollama import OllamaError
from eqcr.quantum_example import ticket_example


def model_response(**overrides):
    choices = {
        "benefit": "F_AXIS_3", "tradeoff": "F_AXIS_2", "review_question": "F_B_COST_1",
    }
    return {
        "model": "qwen3:4b",
        "done": True,
        "message": {"content": json.dumps(choices | overrides)},
    }


def test_studio_llm_uses_solver_facts_and_requires_fresh_comparison(monkeypatch):
    requests = []
    event = {"token": "analysis", "action": "analyze", "model": ticket_example().model_dump(mode="json")}
    monkeypatch.setattr(studio_canvas, "render_board", lambda **_: event)

    def request(path, *, payload, timeout):
        requests.append(payload)
        assert path == "/api/chat"
        assert timeout == 120
        return model_response()

    monkeypatch.setattr(studio_llm, "_request", request)
    app = AppTest.from_file(Path(__file__).parents[1] / "app.py", default_timeout=30).run()
    assert not app.exception
    assert not requests
    next(button for button in app.button if button.label == "Phân tích trade-off với qwen3:4b").click().run()
    assert not app.exception
    assert app.metric[-1].value == "P011 · 6 điểm"
    grounded_tradeoff = "B (P011) tăng «Tách dữ liệu» từ 0 lên 1 đơn vị."
    assert any(output.value == grounded_tradeoff for output in app.text)
    assert any("Ai giữ quyền ghi chính" in output.value for output in app.text)
    [request_payload] = requests
    assert request_payload["model"] == "qwen3:4b"
    facts = json.loads(request_payload["messages"][1]["content"])["facts"]
    assert facts["F_POLICY"]["ranking"] == "SYNC_FIRST"
    assert facts["F_DELTA"]["weighted_score_difference_B_minus_A"] == 1
    assert facts["F_EDGE_1"]["prefer_async_separation"] is True
    assert facts["F_A"]["weighted_score"] == 5
    assert facts["F_B_COST_1"]["subject"] == "Ticket DB"
    assert facts["F_AXIS_2"] == {"axis": "Tách dữ liệu", "A": 0, "B": 1}
    assert request_payload["format"]["properties"]["tradeoff"]["enum"] == ["F_AXIS_2"]
    assert "F_POLICY" not in request_payload["format"]["properties"]["review_question"]["enum"]
    next(button for button in app.button if button.label == "Ưu tiên giữ dữ liệu").click().run()
    assert not app.exception
    assert not any(output.value == grounded_tradeoff for output in app.text)
    assert any("Chạy lại" in message.value for message in app.info)
    assert len(requests) == 1


@pytest.mark.parametrize("response", [
    model_response(tradeoff="F_NONEXISTENT"),
    model_response(tradeoff="F_AXIS_3"),
    model_response(unverified="Prose outside the schema"),
    {"done": True, "message": {"content": "{}"}},
    {"done": True, "done_reason": "length", "message": {"content": "{}"}},
])
def test_llm_rejects_unknown_references_invalid_schema_and_truncation(monkeypatch, response):
    monkeypatch.setattr(studio_llm, "grounded_choices", lambda facts: {
        "benefit": {"F_AXIS_3": "Improvement"},
        "tradeoff": {"F_AXIS_2": "Cost increase"},
        "review_question": {"F_B_COST_1": "What needs to be reviewed?"},
    })
    monkeypatch.setattr(studio_llm, "comparison_facts", lambda snapshot: {})
    monkeypatch.setattr(studio_llm, "_request", lambda *args, **kwargs: response)
    with pytest.raises(OllamaError):
        studio_llm.analyze_tradeoff({})
