"""Review contracts/ownership and inspect bounded, explicitly prepared execution probes."""

from __future__ import annotations

from datetime import datetime, timezone
import json

import streamlit as st

from .models import InteractionContract, SourceRef
from .studio_boundaries import (CONTRACT_FIELDS, OwnershipDecision, ReviewedContract, boundary_profiles,
                                contract_issues, remove_contract, save_contract, save_ownership, source_digests, store_fingerprint)
from .studio_evidence import catalog_digest, claim_digest
from .studio_probe import probe_is_current, probe_issues, run_boundary_probe
from .studio_protocol import reference_fields
from .studio_review_ui import commit_revision


FIELD_LABELS = {"operation": "Thao tác nghiệp vụ", "data_dependency": "Phụ thuộc dữ liệu",
                "request_fields": "Dữ liệu yêu cầu", "response_fields": "Dữ liệu phản hồi và ý nghĩa ACK",
                "versioning": "Phiên bản và tương thích", "consistency": "Nhất quán cần giữ",
                "latency_budget": "Ngân sách độ trễ", "failure_handling": "Xử lý khi bên nhận lỗi",
                "retry_policy": "Số lần và điều kiện retry", "timeout_policy": "Timeout và kết quả chưa rõ",
                "idempotency_policy": "Khóa và xử lý trùng"}
CHECK_LABELS = {"receiver_unavailable": "Bên nhận chưa chạy", "bounded_failed_attempts": "Giới hạn ba lần thử khi lỗi",
                "producer_restart": "Dữ liệu còn sau khi khởi động lại bên gửi", "ack_lost_after_commit_then_retry": "Mất ACK sau commit, gửi lại không ghi trùng",
                "duplicate_and_conflicting_payload": "Cùng ID: nhận bản lặp, từ chối payload khác", "receiver_restart_keeps_effect": "Bên nhận giữ effect sau khởi động lại",
                "timeout_after_commit_then_retry": "Timeout sau commit, gửi lại không ghi trùng", "unsupported_version_rejected": "Từ chối phiên bản không hỗ trợ",
                "outbox_acknowledged": "Hết outbox chờ sau khi nhận ACK", "sync_returns_after_committed_effect": "SYNC trả thành công sau khi effect đã commit"}


def apply_change(changed, event):
    if commit_revision(changed, event):
        st.session_state.architecture = changed
        st.session_state.studio_analyzed = True
        st.session_state.editor_version += 1
        st.session_state.studio_canvas_commit = st.session_state.get("studio_canvas_commit", 0) + 1
        st.rerun()


def source_review(architecture, saved, prefix):
    sources = {item.id: item for item in architecture.requirements}
    refs = saved.contract.source_refs if isinstance(saved, ReviewedContract) else saved.source_refs if saved else []
    selected = st.multiselect("Requirement làm căn cứ hợp đồng" if prefix.startswith("contract") else "Requirement làm căn cứ ownership",
                               list(sources), default=[ref.source_id for ref in refs if ref.source_id in sources], key=f"{prefix}_sources")
    quotes = {}
    for identifier in selected:
        st.write(sources[identifier].text)
        quotes[identifier] = st.text_area(f"Trích nguồn {identifier}", value=next((ref.quote for ref in refs if ref.source_id == identifier),
                                                                                 sources[identifier].text), max_chars=600,
                                           key=f"{prefix}_{identifier}_quote")
    origin = st.selectbox("Nguồn quyết định hợp đồng" if prefix.startswith("contract") else "Nguồn quyết định ownership",
                          ["HUMAN_DECISION", "PREPARED_FIXTURE"], index=int(saved is not None and saved.provenance == "PREPARED_FIXTURE"),
                          key=f"{prefix}_origin")
    actor = st.text_input("Người review hợp đồng" if prefix.startswith("contract") else "Người review ownership",
                          value=saved.actor if saved else "LOCAL_INTERACTIVE_REVIEWER", max_chars=100, key=f"{prefix}_actor")
    rationale = st.text_area("Lý do review hợp đồng" if prefix.startswith("contract") else "Lý do review ownership",
                             max_chars=1000, key=f"{prefix}_rationale")
    return sources, quotes, {"catalog_digest": catalog_digest(architecture), "actor": actor, "rationale": rationale, "provenance": origin}


def make_refs(sources, quotes):
    refs = []
    for identifier, quote in quotes.items():
        start = sources[identifier].text.find(quote)
        if not quote.strip() or start < 0:
            raise ValueError(f"Đoạn trích {identifier} cần khớp nguyên văn requirement.")
        refs.append(SourceRef(source_id=identifier, quote=quote, start=start, end=start + len(quote)))
    if not refs:
        raise ValueError("Chọn ít nhất một requirement làm căn cứ review.")
    return refs


def show_boundary_review(architecture):
    st.html('<span id="studio-boundaries" class="qs-anchor"></span>')
    with st.expander("Hợp đồng tương tác và quyền ghi dữ liệu"):
        st.caption("Review mode, giao thức lỗi và quyền ghi theo nguồn hiện hành. Hợp đồng được duyệt vẫn chưa chứng minh triển khai độc lập.")
        if st.session_state.studio_pending:
            st.info("Lưu sơ đồ trước khi review hợp đồng và ownership.")
            return
        names = {item.id: item.name for item in architecture.components}
        pairs = list(dict.fromkeys([(item.source, item.target) for item in architecture.interactions]
                                   + [(item.source, item.target) for item in architecture.interaction_contracts]))
        if pairs:
            pair = st.selectbox("Tương tác cần hợp đồng", pairs, format_func=lambda value: " → ".join(names.get(item, item) for item in value))
            saved = next((item for item in architecture.interaction_contracts if (item.source, item.target) == pair), None)
            edge = next((item for item in architecture.interactions if (item.source, item.target) == pair), None)
            prefix = f"contract_{'_'.join(pair)}_{st.session_state.editor_version}"
            if saved:
                issues = contract_issues(architecture, saved)
                st.caption(" · ".join(issues) if issues else "Đã review · chưa có chứng cứ runtime của nghiệp vụ thật.")
            sources, quotes, context = source_review(architecture, saved, prefix)
            if edge:
                mode = st.selectbox("Mode hợp đồng", ["SYNC", "ASYNC"], index=int((saved.contract.selected_mode if saved and saved.contract.selected_mode != "UNDECIDED" else edge.mode) == "ASYNC"), key=f"{prefix}_mode")
                reference = st.checkbox("Dùng giao thức mẫu để kiểm thử cục bộ", value=bool(saved and saved.reference_protocol), key=f"{prefix}_reference")
                if reference:
                    st.info("PREPARED_FIXTURE · APPLY_EVENT ghi một effect tổng hợp. Đây là mã mẫu để kiểm giao thức, chưa thực thi nghiệp vụ component hay bất biến của kho trong sơ đồ.")
                defaults = reference_fields(mode) if reference else {field: getattr(saved.contract, field) if saved else "UNKNOWN" for field in CONTRACT_FIELDS}
                fields = {field: st.text_area(label, value=defaults[field], max_chars=1000, disabled=reference,
                                              key=f"{prefix}_{mode}_{reference}_{field}") for field, label in FIELD_LABELS.items()}
                scope = st.selectbox("Phạm vi kho dữ liệu của hợp đồng", ["UNKNOWN", "NONE", "STORES"],
                                      index=1 if reference else ["UNKNOWN", "NONE", "STORES"].index(saved.data_scope) if saved else 0,
                                      disabled=reference, key=f"{prefix}_{reference}_scope")
                stores = {item.id: item for item in architecture.stores}
                store_ids = st.multiselect("Kho nghiệp vụ liên quan hợp đồng", list(stores), default=[item for item in saved.store_ids if item in stores] if saved and not reference else [],
                                            disabled=reference or scope != "STORES", key=f"{prefix}_{reference}_stores") if scope == "STORES" else []
                confirmed = st.checkbox("Tôi xác nhận bên gọi phải chờ hoàn tất" if mode == "SYNC" else "Tôi xác nhận bên gọi được trả trước khi hoàn tất",
                                         key=f"{prefix}_{mode}_signal")
                approve = st.checkbox("Duyệt hợp đồng và đưa mode vào phân nhóm", key=f"{prefix}_approve")
                st.caption("Lưu nháp giữ nguyên mode. Duyệt thay mode và tập điều kiện cũ, giữ mọi hard rule hiện hành. Chọn ASYNC không tự bỏ giao dịch cục bộ.")
                if st.button("Lưu review hợp đồng", disabled=approve and not confirmed):
                    try:
                        refs = make_refs(sources, quotes)
                        contract = InteractionContract(contract_id=saved.contract.contract_id if saved else f"CT-{pair[0]}-{pair[1]}",
                            selected_mode=mode if approve else "UNDECIDED", selection_status="APPROVED" if approve else "UNDECIDED",
                            decision_basis_status="HUMAN_DECISION" if approve else "INSUFFICIENT_EVIDENCE",
                            provenance="HUMAN_DECISION" if approve else "DETERMINISTIC_TRANSFORMATION", reviewer_id=context["actor"] if approve else None,
                            reviewed_at=datetime.now(timezone.utc) if approve else None, source_refs=refs, decision_rationale=context["rationale"],
                            request_must_wait_for_completion=confirmed if mode == "SYNC" else False,
                            request_may_return_before_completion=confirmed if mode == "ASYNC" else False, **fields)
                        prospective = edge.model_dump(mode="json")
                        if approve:
                            prospective["mode"] = mode
                        record = ReviewedContract(source=pair[0], target=pair[1], contract=contract, claim_digest=claim_digest("interactions", prospective),
                            data_scope=scope, store_ids=store_ids, store_digests={key: store_fingerprint(stores[key]) for key in store_ids},
                            source_digests=source_digests(architecture, refs), reference_protocol="OUTBOX_INBOX_V1" if reference else None, **context)
                        apply_change(*save_contract(architecture, record))
                    except ValueError as exc:
                        st.error(str(exc))
            if saved and st.button("Gỡ hợp đồng, giữ giả định mode hiện hành"):
                try:
                    apply_change(*remove_contract(architecture, *pair, actor=context["actor"], rationale=context["rationale"], provenance=context["provenance"]))
                except ValueError as exc:
                    st.error(str(exc))
        if architecture.stores:
            st.markdown("**Quyền ghi và bất biến dữ liệu**")
            stores = {item.id: item for item in architecture.stores}
            store_id = st.selectbox("Kho cần review ownership", list(stores), format_func=lambda value: stores[value].name)
            store = stores[store_id]
            saved = next((item for item in architecture.ownership_decisions if item.store_id == store_id), None)
            prefix = f"ownership_{store_id}_{st.session_state.editor_version}"
            strategies = ["UNKNOWN", "SINGLE_WRITER", "PARTITIONED_WRITERS"]
            strategy = st.selectbox("Chiến lược ghi", strategies, index=strategies.index(saved.strategy) if saved else 0, key=f"{prefix}_strategy")
            writers = st.multiselect("Component được ghi dữ liệu", store.members, default=[item for item in saved.writers if item in store.members] if saved else [],
                                     format_func=names.__getitem__, key=f"{prefix}_writers")
            texts = {field: st.text_input(label, value=getattr(saved, field) if saved else "UNKNOWN", max_chars=1000, key=f"{prefix}_{field}")
                     for field, label in [("partition_key", "Khóa phân vùng writer"), ("invariant", "Bất biến phải giữ"), ("consistency", "Mô hình nhất quán dữ liệu")]}
            lag = st.text_input("Giới hạn replication lag khai báo (ms, trống nếu chưa biết)", value=str(saved.replication_lag_ms) if saved and saved.replication_lag_ms is not None else "", key=f"{prefix}_lag")
            sources, quotes, context = source_review(architecture, saved, prefix)
            approved = st.checkbox("Xác nhận ownership để đưa vào hồ sơ boundary", key=f"{prefix}_approved")
            st.caption("Quyết định này không tự đổi KEEP_SHARED/SPLITTABLE và không chứng minh bất biến nghiệp vụ. Replication lag là khai báo, chưa đo.")
            if st.button("Lưu review ownership"):
                try:
                    refs = make_refs(sources, quotes)
                    record = OwnershipDecision(store_id=store_id, store_digest=store_fingerprint(store), strategy=strategy, writers=writers,
                        review_status="REVIEWED" if approved else "DRAFT", replication_lag_ms=float(lag) if lag.strip() else None,
                        source_refs=refs, source_digests=source_digests(architecture, refs), **texts, **context)
                    apply_change(*save_ownership(architecture, record))
                except ValueError as exc:
                    st.error(str(exc))


def show_boundary_outputs(architecture, candidate, *, replay=False):
    with st.expander("Boundary: hợp đồng, ownership và chạy thử"):
        profile = boundary_profiles(architecture, candidate)
        if profile["interactions"]:
            st.dataframe([{"Tương tác": f"{row['source']} → {row['target']}", "Quantum": f"{row['from_quantum']} → {row['to_quantum']}",
                           "Mode": row["mode"], "Hợp đồng": row["contract_status"], "Cần bổ sung": " · ".join(row["issues"])}
                          for row in profile["interactions"]], hide_index=True, width="stretch")
        if profile["stores"]:
            st.dataframe([{"Kho dữ liệu": row["store_id"], "Quantum": ", ".join(row["quanta"]), "Ownership": row["ownership_status"],
                           "Cần bổ sung": " · ".join(row["issues"])} for row in profile["stores"]], hide_index=True, width="stretch")
        st.caption("Khả năng triển khai độc lập: NOT_VERIFIED. Hợp đồng/ownership được review và phép thử mẫu có phạm vi bằng chứng riêng.")
        st.markdown("[Review hợp đồng và quyền ghi](#studio-boundaries)")
        options = {(item.source, item.target): item for item in architecture.interaction_contracts
                   if any((row["source"], row["target"]) == (item.source, item.target) for row in profile["interactions"])}
        if not options or replay:
            st.caption("Chọn một hợp đồng qua hai Quantum đã review để kiểm giao thức mẫu. Phiên oracle không ghi hoặc chạy probe.")
            return
        key = st.selectbox("Boundary cần chạy probe", list(options), format_func=lambda value: " → ".join(value))
        record = options[key]
        issues = probe_issues(architecture, candidate, record)
        for issue in issues:
            st.caption(issue)
        st.caption("Probe dùng hai tiến trình HTTP loopback và hai file SQLite riêng. Chỉ thực thi APPLY_EVENT của PREPARED_FIXTURE; không chạy mã nghiệp vụ hay benchmark chất lượng production.")
        if st.button("Chạy thử lỗi và xử lý trùng cục bộ", disabled=bool(issues)):
            try:
                with st.spinner("Đang chạy hai tiến trình và các tình huống lỗi…"):
                    st.session_state.studio_boundary_probe = run_boundary_probe(architecture, candidate, record)
            except (OSError, ValueError) as exc:
                st.error(str(exc))
        report = st.session_state.get("studio_boundary_probe")
        if report:
            current = probe_is_current(architecture, candidate, record, report)
            st.caption(f"{report['id']} · {report['status']} · {'khớp input và harness hiện tại' if current else 'STALE: input, hợp đồng, phương án hoặc harness đã đổi'}")
            st.dataframe([{"Tình huống": CHECK_LABELS.get(item["name"], item["name"]), "Đạt phép kiểm": item["passed"]}
                          for item in report["checks"]], hide_index=True, width="stretch")
            st.caption("Chỉ kiểm effect tổng hợp của mã mẫu, chưa kiểm nghiệp vụ và bất biến của kho trong sơ đồ. "
                       "Chưa kiểm TLS, broker, tải lớn, mất điện hoặc mọi thứ tự lỗi. Retry hữu hạn và dispatch thủ công chưa bảo đảm eventual delivery. "
                       "Báo cáo tải xuống giữ observation và phạm vi đầy đủ.")
            if report.get("error"):
                st.error(report["error"])
            st.download_button("Tải bằng chứng probe", json.dumps(report, ensure_ascii=False, indent=2), file_name=f"{report['id']}.json", mime="application/json")
