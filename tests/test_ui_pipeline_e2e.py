"""UI-level regression of the deterministic offline case flow."""

from pathlib import Path

from streamlit.testing.v1 import AppTest

from eqcr import storage


def test_streamlit_petclinic_offline_run_reaches_all_ten_stages(monkeypatch):
    # Keep this UI regression from writing generated files into the preserved runs/ tree.
    monkeypatch.setattr(
        storage,
        "save_run",
        lambda run_id, artifacts, **kwargs: Path("isolated-ui-test-run"),
    )
    monkeypatch.setattr(
        storage,
        "save_snapshot",
        lambda run_id, version, artifacts, **kwargs: Path("isolated-ui-test-snapshot"),
    )
    app_path = Path(__file__).parents[1] / "research_app.py"
    app = AppTest.from_file(app_path, default_timeout=30).run()

    next(button for button in app.button if button.label == "Load PetClinic demo data").click().run()
    assert not app.exception
    assert app.session_state["fixture"]["raw_requirements"]["case_id"] == "PETCLINIC-MINI-WHAT-IF"

    next(button for button in app.button if button.label == "Run offline fixture").click().run()
    assert not app.exception
    artifacts = app.session_state["artifacts"]

    assert artifacts["metadata"]["execution_mode"] == "OFFLINE_FIXTURE"
    assert artifacts["metadata"]["fixture_label"] == "PRECOMPUTED"
    assert [step["step"] for step in artifacts["validation_report"]["steps"]] == [
        f"{index:02d}" for index in range(1, 11)
    ]
    assert artifacts["partitions"]["enumerated_partition_count"] == 203
    assert artifacts["partitions"]["feasible_candidate_count"] == 10
    assert artifacts["partitions"]["optimal_candidate_count"] == 10
    assert artifacts["traceability"]["assertions"]["qame_trace_chain_resolves"] is True
    assert artifacts["traceability"]["assertions"]["qame_allocations_resolve"] is True
    assert {profile["measurement_status"] for profile in artifacts["quality_profiles"]["profiles"]} == {
        "NOT_MEASURED",
        "INSUFFICIENT_EVIDENCE",
    }
