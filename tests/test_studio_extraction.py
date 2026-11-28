from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from eqcr import ollama, storage, studio_canvas
from eqcr.quantum_example import ticket_example
from eqcr.quantum_tradeoff import Architecture, Preferences, analyze
from eqcr.studio_extraction import decide_proposal, extract_proposals, proposal_is_current
from eqcr.studio_sessions import checkpoints, invalidate_changed_sources, load_checkpoint, save_checkpoint


def fake_inference(monkeypatch):
    import json

    monkeypatch.setattr(ollama, "list_model_details", lambda: [{"name": "qwen3:4b", "digest": "TEST_ONLY_DIGEST"}])
    monkeypatch.setattr(ollama, "get_ollama_version", lambda: "TEST_ONLY")

    def request(path, *, payload, timeout):
        assert path == "/api/chat"
        assert "NFR-03" in payload["messages"][1]["content"]
        text = next(item["text"] for item in json.loads(payload["messages"][1]["content"]) if item["id"] == "NFR-03")
        # Prepared response tests the new schema; no local inference is performed here.
        return {"model": "qwen3:4b", "done_reason": "stop", "eval_count": 10, "message": {"content": json.dumps({"proposals": [
            {"source_id": "NFR-03", "characteristic": "Security", "component_ids": ["PROFILE"], "quote": text,
             "disposition": "PROPOSED", "frame": {"subject": "Dữ liệu hồ sơ cá nhân", "action": "mã hóa", "object": None,
                "condition": "khi gửi và nhận qua mạng", "modality": "phải", "subject_ids": ["PROFILE"], "object_ids": [], "context_ids": [],
                "statement_kind": "OBLIGATION", "effect": "QUALITY_OBLIGATION"}},
            {"source_id": "NFR-03", "characteristic": "Security", "component_ids": ["UNKNOWN_ID"], "quote": "unsupported"},
        ]})}}

    monkeypatch.setattr(ollama, "_request", request)


def test_proposals_are_inert_and_review_is_revision_bound_with_restorable_decisions(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "ARTIFACT_ROOT", tmp_path)
    fake_inference(monkeypatch)
    original = ticket_example()
    baseline = analyze(original, Preferences())
    run = extract_proposals(original, ["NFR-03"], "QUALITY")
    assert analyze(original, Preferences()) == baseline
    valid, invalid = run["proposals"]
    assert not valid["issues"] and invalid["issues"]
    for action in ("REJECT", "DEFER"):
        unchanged, event = decide_proposal(original, valid, action=action, actor="TEST_REVIEWER", rationale="Test only")
        assert unchanged == original and event["applied"] is None
    with pytest.raises(ValueError):
        decide_proposal(original, invalid, action="APPROVE", actor="TEST_REVIEWER", rationale="Test only")
    changed, event = decide_proposal(original, valid, action="APPROVE", actor="TEST_REVIEWER", rationale="Exact clause reviewed", semantic_confirmed=True, provenance="PREPARED_FIXTURE")
    assert event["before"] != event["after"]
    assert event["source_digest"] == original.requirements[-1].input_digest()
    assert analyze(changed, Preferences()) != baseline
    first = save_checkpoint(original, event={"action": "TEST_INPUT"}, proposals=run["proposals"])
    second = save_checkpoint(changed, event=event, parent=first, proposals=[{**valid, "status": "APPROVED"}, invalid])
    restored = load_checkpoint(second)
    assert restored["parent"] == first and restored["event"]["actor"] == "TEST_REVIEWER"
    assert analyze(Architecture.model_validate(restored["architecture"]), Preferences()) == analyze(changed, Preferences())
    assert len(checkpoints()) == 2
    modified = original.model_dump(mode="json")
    modified["requirements"][-1]["text"] = "New requirement after review."
    newer = Architecture.model_validate(modified)
    assert not proposal_is_current(newer, valid)
    with pytest.raises(ValueError, match="đã đổi"):
        decide_proposal(newer, valid, action="APPROVE", actor="TEST_REVIEWER", rationale="Test only")


def test_live_ui_review_then_restore_reproduces_diagram_inputs(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "ARTIFACT_ROOT", tmp_path)
    fake_inference(monkeypatch)
    captures = []
    monkeypatch.setattr(studio_canvas, "render_board", lambda **kwargs: captures.append(kwargs))

    def widget(view, kind, label):
        return next(item for item in getattr(view, kind) if item.label == label)

    view = AppTest.from_file(Path(__file__).parents[1] / "app.py", default_timeout=30).run()
    widget(view, "selectbox", "Cách trích xuất").select("DIRECT").run()
    widget(view, "multiselect", "Nguồn gửi Ollama").set_value(["NFR-03"]).run()
    widget(view, "button", "Phân tích bằng Ollama").click().run()
    assert not view.exception
    assert not Architecture.model_validate(captures[-1]["model"]).requirements[-1].quality_allocations
    original_checkpoint = view.session_state.studio_checkpoint
    widget(view, "text_area", "Lý do quyết định").set_value("TEST ONLY: source clause checked")
    widget(view, "checkbox", "Tôi đã review chủ thể, điều kiện, phủ định và tác động của mệnh đề").check()
    widget(view, "selectbox", "Nguồn quyết định đề xuất").select("PREPARED_FIXTURE")
    widget(view, "button", "Lưu quyết định và tính lại").click().run()
    assert not view.exception
    assert view.session_state.studio_checkpoint != original_checkpoint
    assert Architecture.model_validate(captures[-1]["model"]).requirements[-1].quality_allocations[0].characteristic == "Security"
    widget(view, "selectbox", "Phiên đã lưu").select(original_checkpoint).run()
    widget(view, "button", "Tải lại phiên đã chọn").click().run()
    assert not view.exception
    assert captures[-1]["model"] == ticket_example().model_dump(mode="json")


def test_source_revision_requires_reconfirmation_even_if_old_quote_still_matches():
    data = ticket_example().model_dump(mode="json")
    data["requirements"][-1]["quality_allocations"] = [
        {"characteristic": "Security", "component_ids": ["PROFILE"], "source_quote": "mã hóa"}]
    before = Architecture.model_validate(data)
    data["requirements"][-1]["text"] += " Điều kiện đo đã được cập nhật."
    changed = invalidate_changed_sources(before, Architecture.model_validate(data))
    assert not changed.requirements[-1].quality_allocations
    assert before.requirements[-1].quality_allocations


def test_provider_failure_is_recorded_and_never_creates_applied_evidence(tmp_path, monkeypatch):
    import json

    monkeypatch.setattr(storage, "ARTIFACT_ROOT", tmp_path)
    fake_inference(monkeypatch)

    def failed(path, **kwargs):
        raise ollama.OllamaError("TEST_ONLY provider unavailable")

    monkeypatch.setattr(ollama, "_request", failed)
    original = ticket_example()
    with pytest.raises(ollama.OllamaError):
        extract_proposals(original, ["NFR-03"], "QUALITY")
    [record] = list(tmp_path.rglob("manifest.json"))
    data = json.loads(record.read_text(encoding="utf-8"))
    assert data["status"] == "FAILED" and not data["proposals"]
    assert data["source_digests"]["NFR-03"] == original.requirements[-1].input_digest()
    assert not original.requirements[-1].quality_allocations
