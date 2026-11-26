"""Authored metamorphic checks, not independent semantic reference labels."""

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from eqcr import storage, studio_canvas
from eqcr.quantum_example import ticket_example
from eqcr.quantum_tradeoff import Architecture, Preferences, analyze, component_profiles, merge_quality_requirement
from eqcr.studio_sessions import invalidate_changed_sources, load_checkpoint


def paired_targets():
    raw = ticket_example().model_dump(mode="json")
    raw["requirements"][-1]["quality_allocations"] = [
        {"characteristic": "Security", "component_ids": ["PROFILE"], "source_quote": "mã hóa"}]
    one = Architecture.model_validate(raw)
    raw["requirements"].append({"id": "DUP", "kind": "NFR", "text": "Customer Profile phải mã hóa dữ liệu.",
                                "quality_allocations": [{"characteristic": "Security", "component_ids": ["PROFILE"],
                                                         "source_quote": "mã hóa"}]})
    return one, Architecture.model_validate(raw)


def test_reviewed_paraphrase_is_cost_invariant_and_keeps_both_sources():
    one, two = paired_targets()
    weights = Preferences()
    assert analyze(two, weights).ranked[0].score(weights) > analyze(one, weights).ranked[0].score(weights)
    merged = merge_quality_requirement(two, "DUP", "NFR-03")
    assert analyze(merged, weights) == analyze(one, weights)
    assert component_profiles(merged)["PROFILE"]["Security · NFR-03"] == ["NFR-03", "DUP"]
    assert two.requirements[-1].quality_allocations  # Input object remains intact.
    separated = merge_quality_requirement(merged, "DUP", None)
    assert not separated.requirements[-1].duplicate_of and not separated.requirements[-1].quality_allocations


def test_different_scope_stays_independent_until_review_and_invalid_links_fail():
    _, two = paired_targets()
    raw = two.model_dump(mode="json")
    raw["requirements"][-1]["quality_allocations"][0]["component_ids"] = ["REPORT"]
    independent = Architecture.model_validate(raw)
    profiles = component_profiles(independent)
    assert "Security · DUP" in profiles["REPORT"] and "Security · NFR-03" in profiles["PROFILE"]
    for alias, target in [("MISSING", "NFR-03"), ("DUP", "MISSING"), ("DUP", "DUP"), ("REQ-01", "NFR-03")]:
        with pytest.raises(ValueError):
            merge_quality_requirement(two, alias, target)
    raw["requirements"][-1]["duplicate_of"] = "NFR-03"
    with pytest.raises(ValueError, match="Tách mục tiêu"):
        Architecture.model_validate(raw)
    raw["requirements"][-1]["quality_allocations"] = []
    raw["requirements"][-2]["duplicate_of"] = "DUP"
    with pytest.raises(ValueError):
        Architecture.model_validate(raw)


@pytest.mark.parametrize("changed_id", ["NFR-03", "DUP"])
def test_source_edits_invalidate_reviewed_merge(changed_id):
    _, two = paired_targets()
    merged = merge_quality_requirement(two, "DUP", "NFR-03")
    raw = merged.model_dump(mode="json")
    source = next(item for item in raw["requirements"] if item["id"] == changed_id)
    source["text"] += " Điều kiện mới."
    after = invalidate_changed_sources(merged, Architecture.model_validate(raw))
    assert not after.requirements[-1].duplicate_of
    assert not next(item for item in after.requirements if item.id == changed_id).quality_allocations


def test_remerging_a_root_keeps_direct_references_and_all_provenance():
    _, two = paired_targets()
    merged = merge_quality_requirement(two, "DUP", "NFR-03")
    raw = two.model_dump(mode="json")["requirements"][-1]
    raw["id"] = "ROOT"
    data = merged.model_dump(mode="json")
    data["requirements"].append(raw)
    new = merge_quality_requirement(Architecture.model_validate(data), "NFR-03", "ROOT")
    assert new.requirements[-2].duplicate_of == "ROOT"
    assert set(component_profiles(new)["PROFILE"]["Security · ROOT"]) == {"NFR-03", "DUP", "ROOT"}


def test_ui_merge_persists_review_and_restores_cost_invariance(tmp_path, monkeypatch):
    import eqcr.quantum_example as example

    one, two = paired_targets()
    monkeypatch.setattr(storage, "ARTIFACT_ROOT", tmp_path)
    monkeypatch.setattr(example, "ticket_example", lambda: two)
    monkeypatch.setattr(studio_canvas, "render_board", lambda **kwargs: None)
    view = AppTest.from_file(Path(__file__).parents[1] / "app.py", default_timeout=30).run()

    def widget(kind, label):
        return next(item for item in getattr(view, kind) if item.label == label)

    widget("selectbox", "Nguồn cần đối chiếu").select("DUP").run()
    widget("selectbox", "Mục tiêu chất lượng gốc").select("NFR-03").run()
    widget("text_area", "Căn cứ hợp nhất hoặc tách mục tiêu").set_value("TEST ONLY paraphrase, same scope and target.")
    widget("button", "Lưu quan hệ mục tiêu").click().run()
    assert not view.exception
    saved = load_checkpoint(view.session_state.studio_checkpoint)
    assert saved["event"]["action"] == "QUALITY_TARGET_MERGE"
    assert saved["event"]["before"] != saved["event"]["after"]
    assert analyze(Architecture.model_validate(saved["architecture"]), Preferences()) == analyze(one, Preferences())
    widget("selectbox", "NFR nguồn").select("DUP").run()
    assert any("dùng mục tiêu" in item.value for item in view.info)
