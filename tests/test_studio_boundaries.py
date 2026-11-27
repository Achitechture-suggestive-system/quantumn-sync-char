"""Prepared contracts/labels test code paths; they are not stakeholder or independent semantic labels."""

from datetime import datetime, timezone
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from eqcr import storage, studio_canvas
from eqcr.models import InteractionContract, SourceRef
from eqcr.quantum_example import ticket_example
from eqcr.quantum_tradeoff import Architecture, Preferences, analyze, hard_constraints
from eqcr.studio_boundaries import (OwnershipDecision, ReviewedContract, boundary_profiles, contract_issues, ownership_issues,
                                    remove_contract, save_contract, save_ownership, source_digests, store_fingerprint)
from eqcr.studio_evidence import EvidenceReviewRequired, catalog_digest, claim_digest, evidence_blockers, rebind_evidence
from eqcr.studio_probe import probe_binding, probe_is_current, probe_issues, run_boundary_probe
from eqcr.studio_protocol import reference_fields
from eqcr.studio_sessions import load_checkpoint


def prepared_contract(mode="ASYNC", *, model=None, draft=False):
    model = model or ticket_example()
    refs = [SourceRef(source_id=source.id, quote=source.text, start=0, end=len(source.text)) for source in model.requirements[:2]]
    contract = InteractionContract(contract_id="CT-TEST", selected_mode="UNDECIDED" if draft else mode,
        selection_status="UNDECIDED" if draft else "APPROVED", decision_basis_status="INSUFFICIENT_EVIDENCE" if draft else "HUMAN_DECISION",
        provenance="DETERMINISTIC_TRANSFORMATION" if draft else "HUMAN_DECISION", reviewer_id=None if draft else "TEST_ONLY",
        reviewed_at=None if draft else datetime.now(timezone.utc), source_refs=refs, decision_rationale="Prepared technical contract, no business validation",
        request_must_wait_for_completion=mode == "SYNC", request_may_return_before_completion=mode == "ASYNC", **reference_fields(mode))
    prospective = model.interactions[0].model_dump(mode="json")
    if not draft:
        prospective["mode"] = mode
    record = ReviewedContract(source="CREATE", target="ROUTE", contract=contract, claim_digest=claim_digest("interactions", prospective),
        data_scope="NONE", source_digests=source_digests(model, refs), catalog_digest=catalog_digest(model), actor="TEST_ONLY",
        rationale="Prepared technical review, not real human acceptance", provenance="PREPARED_FIXTURE", reference_protocol="OUTBOX_INBOX_V1")
    return model, record


def candidate(model):
    return next(item for item in analyze(model, Preferences()).feasible if item.id == "P011")


def test_draft_has_no_optimizer_effect_and_complete_review_changes_mode_causally():
    model, draft = prepared_contract("SYNC", draft=True)
    saved, event = save_contract(model, draft)
    assert event["action"] == "CONTRACT_DRAFT_SAVED" and saved.interactions[0].mode == "ASYNC"
    assert analyze(saved, Preferences()) == analyze(model, Preferences())
    _, record = prepared_contract("SYNC", model=saved)
    reviewed, event = save_contract(saved, record)
    assert reviewed.interactions[0].mode == "SYNC" and not contract_issues(reviewed, record)
    assert analyze(reviewed, Preferences()) != analyze(model, Preferences())
    assert hard_constraints(reviewed) == hard_constraints(model)
    assert reviewed.interactions[0].evidence.review_provenance == "PREPARED_FIXTURE"
    assert event["before"] == saved.model_dump(mode="json") and event["provenance"] == "PREPARED_FIXTURE"
    with pytest.raises(ValueError, match="nháp"):
        save_contract(reviewed, draft)


def test_approval_needs_complete_fields_mode_signal_and_current_span():
    model, record = prepared_contract()
    data = record.model_dump(mode="json")
    data["contract"]["idempotency_policy"] = "unknown"
    with pytest.raises(ValueError, match="chưa được xác định"):
        save_contract(model, ReviewedContract.model_validate(data))
    for invalid in ("signal", "actor", "span"):
        data = record.model_dump(mode="json")
        if invalid == "signal":
            data["contract"]["request_may_return_before_completion"] = False
        elif invalid == "actor":
            data["actor"] = "SOMEONE_ELSE"
        else:
            data["contract"]["source_refs"][0]["end"] += 100
        with pytest.raises(ValueError):
            save_contract(model, ReviewedContract.model_validate(data))


def test_all_citations_are_revision_bound_and_first_citation_rebind_cannot_bypass_contract():
    model, record = prepared_contract()
    reviewed, _ = save_contract(model, record)
    data = reviewed.model_dump(mode="json")
    data["requirements"][1]["text"] += " Revised scope."
    stale = Architecture.model_validate(data)
    assert any(item["collection"] == "interaction_contracts" for item in evidence_blockers(stale))
    with pytest.raises(EvidenceReviewRequired):
        analyze(stale, Preferences())
    first = stale.requirements[0]
    rebound, _ = rebind_evidence(stale, "interactions", 0, source_id=first.id, quote=first.text, actor="TEST_ONLY", rationale="Only first citation checked")
    with pytest.raises(EvidenceReviewRequired):
        analyze(rebound, Preferences())
    removed, event = remove_contract(stale, "CREATE", "ROUTE", actor="TEST_ONLY", rationale="Return explicitly to a design assumption", provenance="PREPARED_FIXTURE")
    assert not evidence_blockers(removed) and removed.interactions[0].mode == "ASYNC"
    assert hard_constraints(removed) == hard_constraints(stale) and event["provenance"] == "PREPARED_FIXTURE"


def test_contract_cannot_remove_local_transaction_and_store_changes_expire_review():
    data = ticket_example().model_dump(mode="json")
    data["interactions"][0].update(mode="SYNC", local_transaction=True, basis="Prepared local atomicity rule")
    model, record = prepared_contract(model=Architecture.model_validate(data))
    with pytest.raises(ValueError, match="Giao dịch cục bộ"):
        save_contract(model, record)
    model, record = prepared_contract()
    record = record.model_copy(update={"data_scope": "STORES", "store_ids": ["TICKET_DB"],
                                      "store_digests": {"TICKET_DB": store_fingerprint(model.stores[1])}})
    reviewed, _ = save_contract(model, record)
    data = reviewed.model_dump(mode="json")
    data["stores"][1]["policy"] = "KEEP_SHARED"
    assert contract_issues(Architecture.model_validate(data), record)
    with pytest.raises(EvidenceReviewRequired):
        analyze(Architecture.model_validate(data), Preferences())


def test_ownership_is_source_bound_separate_from_hard_policy_and_runtime_proof():
    model, contract = prepared_contract()
    ownership = OwnershipDecision(store_id="TICKET_DB", store_digest=store_fingerprint(model.stores[1]), review_status="REVIEWED",
        strategy="SINGLE_WRITER", writers=["ROUTE"], invariant="One accepted route per ticket", consistency="Readers may lag",
        source_refs=contract.contract.source_refs, source_digests=contract.source_digests, catalog_digest=contract.catalog_digest,
        actor="TEST_ONLY", rationale="Prepared ownership hypothesis", provenance="PREPARED_FIXTURE")
    reviewed, event = save_ownership(model, ownership)
    assert hard_constraints(reviewed) == hard_constraints(model) and not ownership_issues(reviewed, ownership)
    profile = boundary_profiles(reviewed, candidate(reviewed))
    store = next(row for row in profile["stores"] if row["store_id"] == "TICKET_DB")
    assert store["ownership_status"] == "REVIEWED_INVARIANT_NOT_PROVEN"
    assert store["writer_quanta"] and store["replication_lag_measurement_status"] == "NOT_MEASURED"
    assert profile["deployability_status"] == "NOT_VERIFIED" and event["provenance"] == "PREPARED_FIXTURE"
    for edit in ({"writers": ["ROUTE", "CREATE"]}, {"writers": ["LOGIN"]}, {"invariant": "UNKNOWN"}):
        with pytest.raises(ValueError):
            save_ownership(model, ownership.model_copy(update=edit))
    data = reviewed.model_dump(mode="json")
    data["requirements"][1]["text"] += " Changed invariant."
    assert ownership_issues(Architecture.model_validate(data), ownership)


def test_arbitrary_contract_and_invalid_candidate_cannot_reuse_reference_probe():
    model, record = prepared_contract()
    model, _ = save_contract(model, record)
    assert not probe_issues(model, candidate(model), record)
    custom = record.model_copy(update={"contract": record.contract.model_copy(update={"retry_policy": "Retry forever"})})
    assert any("harness" in issue for issue in probe_issues(model, candidate(model), custom))
    from dataclasses import replace

    bad = replace(candidate(model), groups=(("CREATE", "ROUTE"),))
    assert probe_issues(model, bad, record)
    assert probe_binding(model, candidate(model), record) != probe_binding(model, replace(candidate(model), groups=tuple(reversed(candidate(model).groups))), record)


@pytest.mark.parametrize("mode", ["SYNC", "ASYNC"])
def test_real_two_process_reference_fault_schedule_has_persisted_observations_and_cleanup(tmp_path, mode):
    model, record = prepared_contract(mode)
    model, _ = save_contract(model, record)
    report = run_boundary_probe(model, candidate(model), record, root=tmp_path)
    assert report["status"] == "PROTOTYPE_CONTRACT_CHECK_PASSED", report
    assert len(report["checks"]) == 9 and all(row["passed"] for row in report["checks"])
    assert report["workers_stopped"] and len(report["worker_pids"]) == 4
    assert report["deployability_status"] == "NOT_VERIFIED" and report["quality_measurement_status"] == "NOT_MEASURED"
    assert report["protocol_input_provenance"] == report["review_provenance"] == "PREPARED_FIXTURE"
    assert {"input.json", "observations.json", "producer.sqlite", "receiver.sqlite"} == set(report["artifact_hashes"])
    folder = tmp_path / report["id"]
    assert (folder / "report.json").exists()
    assert probe_is_current(model, candidate(model), record, report)
    assert not probe_is_current(model, candidate(model), record, {**report, "harness_sha256": {}})
    assert all(path.read_text() == "" for path in folder.glob("*.stderr.txt"))


def test_ui_contract_and_ownership_review_checkpoint_and_output_profiles(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "ARTIFACT_ROOT", tmp_path)
    captures = []
    monkeypatch.setattr(studio_canvas, "render_board", lambda **kwargs: captures.append(kwargs))
    view = AppTest.from_file(Path(__file__).parents[1] / "app.py", default_timeout=30).run()

    def widget(kind, label):
        return next(item for item in getattr(view, kind) if item.label == label)

    widget("checkbox", "Dùng giao thức mẫu để kiểm thử cục bộ").check().run()
    widget("multiselect", "Requirement làm căn cứ hợp đồng").set_value(["REQ-01", "REQ-02"])
    widget("selectbox", "Nguồn quyết định hợp đồng").select("PREPARED_FIXTURE")
    widget("text_input", "Người review hợp đồng").set_value("TEST_ONLY")
    widget("text_area", "Lý do review hợp đồng").set_value("Prepared UI reference protocol, not a domain label")
    widget("checkbox", "Tôi xác nhận bên gọi được trả trước khi hoàn tất").check()
    widget("checkbox", "Duyệt hợp đồng và đưa mode vào phân nhóm").check().run()
    widget("button", "Lưu review hợp đồng").click().run()
    assert not view.exception, view.exception
    assert view.session_state.architecture.interaction_contracts[0].provenance == "PREPARED_FIXTURE"
    assert load_checkpoint(view.session_state.studio_checkpoint)["event"]["action"] == "INTERACTION_CONTRACT_REVIEWED"
    assert all("boundary_profiles" in row for row in captures[-1]["plans"])
    widget("selectbox", "Kho cần review ownership").select("TICKET_DB").run()
    widget("selectbox", "Chiến lược ghi").select("SINGLE_WRITER")
    widget("multiselect", "Component được ghi dữ liệu").set_value(["ROUTE"])
    widget("text_input", "Bất biến phải giữ").set_value("Prepared one route per ticket")
    widget("text_input", "Mô hình nhất quán dữ liệu").set_value("Prepared single-writer, replicas may lag")
    widget("multiselect", "Requirement làm căn cứ ownership").set_value(["REQ-02"])
    widget("selectbox", "Nguồn quyết định ownership").select("PREPARED_FIXTURE")
    widget("text_area", "Lý do review ownership").set_value("Prepared UI metadata test; invariant not proven")
    widget("checkbox", "Xác nhận ownership để đưa vào hồ sơ boundary").check().run()
    widget("button", "Lưu review ownership").click().run()
    assert not view.exception
    assert load_checkpoint(view.session_state.studio_checkpoint)["event"]["action"] == "DATA_OWNERSHIP_REVIEW"
    assert view.session_state.architecture.ownership_decisions[0].writers == ["ROUTE"]


def test_failed_probe_records_failure_and_stops_workers(tmp_path, monkeypatch):
    from eqcr import studio_probe

    model, record = prepared_contract()
    model, _ = save_contract(model, record)
    monkeypatch.setattr(studio_probe.Worker, "state", lambda self: (_ for _ in ()).throw(RuntimeError("Prepared forced observation failure")))
    report = run_boundary_probe(model, candidate(model), record, root=tmp_path)
    assert report["status"] == "PROTOTYPE_CONTRACT_CHECK_FAILED"
    assert report["workers_stopped"] and "forced observation failure" in report["error"]
    assert (tmp_path / report["id"] / "report.json").exists()
