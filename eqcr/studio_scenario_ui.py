"""Scenario review forms and comparable conditional timing profiles."""

from __future__ import annotations

import streamlit as st

from .models import Scenario, SourceRef
from .quantum_tradeoff import Architecture
from .studio_evidence import catalog_digest
from .studio_quality import QualityCharacteristic, quality_suggestions
from .studio_review_ui import commit_revision
from .studio_scenarios import PARTS, ReviewedScenario, TimingAssumptions


PART_LABELS = {"stimulus_source": "Nguồn kích thích", "stimulus": "Kích thích",
               "environment": "Môi trường và tải", "stimulated_artifact": "Đối tượng bị tác động",
               "response": "Phản hồi cần đạt", "response_measure": "Thước đo phản hồi"}


def optional_number(value: str) -> float | None:
    try:
        return float(value.strip().replace(",", ".")) if value.strip() else None
    except ValueError as exc:
        raise ValueError("Nhập số thập phân hoặc để trống khi chưa biết giá trị.") from exc


def show_scenario_review(architecture: Architecture) -> None:
    sources = {item.id: item for item in architecture.requirements if item.kind == "NFR" and not item.duplicate_of}
    if not sources:
        return
    st.html('<span id="studio-scenarios" class="qs-anchor"></span>')
    with st.expander("Quality scenario và dự đoán"):
        if st.session_state.studio_pending:
            st.caption("Lưu sơ đồ trước khi review scenario.")
            return
        source_id = st.selectbox("NFR cho quality scenario", list(sources))
        source = sources[source_id]
        st.write(source.text)
        records = {item.scenario.id: item for item in architecture.quality_scenarios if item.scenario.source_ref.source_id == source_id}
        picker_key = f"scenario_picker_{source_id}"
        pending_selection = st.session_state.get("studio_scenario_select_next")
        if pending_selection and pending_selection[0] == source_id:
            st.session_state[picker_key] = pending_selection[1]
            st.session_state.pop("studio_scenario_select_next")
        selected = st.selectbox("Scenario đã lưu", [None, *records], format_func=lambda value: value or "Tạo scenario mới",
                                key=picker_key)
        saved = records.get(selected)
        prefix = f"scenario_{source_id}_{selected}_{st.session_state.editor_version}"
        identifier = st.text_input("Mã scenario", value=selected or f"QS-{len(architecture.quality_scenarios) + 1:02d}",
                                   max_chars=32, key=f"{prefix}_id")
        name = st.text_input("Tên scenario", value=saved.scenario.name if saved else f"Kịch bản {source_id}",
                             max_chars=100, key=f"{prefix}_name")
        quote = st.text_area("Đoạn nguồn của scenario", value=saved.scenario.source_ref.quote if saved else source.text,
                             max_chars=600, key=f"{prefix}_quote")
        parts = {}
        st.caption("Điền sáu phần từ đoạn nguồn. Phần bổ sung ngoài đoạn nguồn được ghi là quyết định reviewer. "
                   "Để trống giữ UNKNOWN và chưa tạo dự đoán.")
        for field in PARTS:
            parts[field] = st.text_input(PART_LABELS[field], value=(getattr(saved.scenario, field) or "") if saved else "",
                                         max_chars=600, key=f"{prefix}_{field}")
        default = saved.characteristic if saved else next(iter(source.quality_allocations), None)
        default = default.characteristic if default and not isinstance(default, str) else default
        default = default or next(iter(quality_suggestions(source.text)), None)
        labels = list(QualityCharacteristic)
        label = st.selectbox("Characteristic của scenario", labels, index=labels.index(default) if default in labels else None,
                             key=f"{prefix}_iso")
        names = {item.id: item.name for item in architecture.components}
        responsible = st.multiselect("Component chịu trách nhiệm scenario", list(names),
                                      default=saved.responsible_component_ids if saved else source.component_ids,
                                      format_func=names.__getitem__, key=f"{prefix}_responsible")
        path = st.multiselect("Đường đi tuần tự hoặc component cần khôi phục", list(names),
                               default=saved.component_path if saved else source.component_ids,
                               format_func=names.__getitem__, key=f"{prefix}_path")
        st.caption("Đường đi giữ thứ tự chọn. Scope chịu trách nhiệm dùng để gán ISO; component bối cảnh trên đường đi "
                   "có thể khác scope. Với khôi phục, chọn đúng một component làm đầu mối.")
        metrics = ["UNSUPPORTED", "RESPONSE_LATENCY", "RECOVERY_TIME"]
        metric = st.selectbox("Adapter dự đoán", metrics, index=metrics.index(saved.metric) if saved else 0,
                              format_func=lambda value: {"UNSUPPORTED": "Chưa có adapter", "RESPONSE_LATENCY": "Giới hạn thời gian phản hồi tuần tự",
                                                         "RECOVERY_TIME": "Khôi phục tuần tự toàn Quantum"}[value], key=f"{prefix}_metric")
        threshold = st.text_input("Ngưỡng mục tiêu", value=str(saved.target_value) if saved and saved.target_value is not None else "",
                                  key=f"{prefix}_threshold")
        units = [None, "ms", "s", "min"]
        unit = st.selectbox("Đơn vị mục tiêu", units, index=units.index(saved.target_unit) if saved else 0,
                            format_func=lambda value: value or "Chưa biết", key=f"{prefix}_unit")
        target_quote = st.text_input("Đoạn nguồn chứa ngưỡng", value=saved.scenario.target or "" if saved else "",
                                     max_chars=600, key=f"{prefix}_target_quote")
        completion = st.selectbox("Mốc kết thúc phép đo", ["BUSINESS_COMPLETION", "CALLER_RESPONSE"],
                                  index=int(saved is not None and saved.completion == "CALLER_RESPONSE"),
                                  format_func=lambda value: "Hoàn tất nghiệp vụ" if value == "BUSINESS_COMPLETION" else "Trả phản hồi cho bên gọi",
                                  key=f"{prefix}_completion")
        st.markdown("**Giả định thời gian, đơn vị ms**")
        st.caption("Các số dưới đây là giới hạn trên giả định, phải gồm cả thời gian chờ tại môi trường/tải đã nêu. "
                   "Không cộng các số p95 thành p95 của toàn luồng. Ô trống giữ giá trị chưa biết. Chưa có phép đo vận hành.")
        if metric == "RECOVERY_TIME":
            st.caption("Adapter giả định toàn bộ Quantum khởi động lại tuần tự. Bound từng component phải gồm phục hồi "
                       "trạng thái và phụ thuộc cần thiết; mô hình này chưa chứng minh khả năng triển khai độc lập.")
        bounds = {}
        components = list(names) if metric == "RECOVERY_TIME" else path
        for component in components:
            value = saved.assumptions.component_ms.get(component) if saved else None
            bounds[component] = st.text_input(f"Giới hạn {names[component]} (ms)", value=str(value) if value is not None else "",
                                              key=f"{prefix}_bound_{component}")
        fields = ["detection_ms"] if metric == "RECOVERY_TIME" else ["sync_round_trip_ms", "async_enqueue_ms", "async_delivery_ms"]
        field_labels = {"detection_ms": "Giới hạn phát hiện lỗi (ms)", "sync_round_trip_ms": "Giới hạn RTT SYNC qua Quantum (ms)",
                        "async_enqueue_ms": "Giới hạn ghi nhận hàng đợi (ms)", "async_delivery_ms": "Giới hạn chờ và giao nhận ASYNC (ms)"}
        parameters = {}
        for field in fields:
            value = getattr(saved.assumptions, field) if saved else None
            parameters[field] = st.text_input(field_labels[field], value=str(value) if value is not None else "", key=f"{prefix}_{field}")
        assumption_note = st.text_area("Căn cứ và giới hạn của giả định thời gian", value=saved.assumptions.rationale if saved else "",
                                       max_chars=1000, key=f"{prefix}_assumptions")
        origins = ["HUMAN_DECISION", "PREPARED_FIXTURE"]
        format_origin = lambda value: "Khai báo của reviewer" if value == "HUMAN_DECISION" else "Dữ liệu chuẩn bị cho demo/kiểm thử"
        assumption_origin = st.selectbox("Nguồn giả định thời gian", origins,
                                          index=origins.index(saved.assumptions.provenance) if saved else 0,
                                          format_func=format_origin, key=f"{prefix}_assumption_origin")
        acknowledged = st.checkbox("Tôi khai báo các giá trị đã điền là giới hạn trên giả định, đã gồm thời gian chờ",
                                     value=saved is not None, key=f"{prefix}_ack")
        actor = st.text_input("Người review scenario", value="LOCAL_INTERACTIVE_REVIEWER", max_chars=100)
        decision_origin = st.selectbox("Nguồn quyết định scenario", origins, index=origins.index(saved.decision_provenance) if saved else 0,
                                       format_func=format_origin, key=f"{prefix}_decision_origin")
        rationale = st.text_area("Lý do xác nhận scenario và phạm vi component", max_chars=1000)
        allocate = st.checkbox("Đưa characteristic và scope chịu trách nhiệm vào phân nhóm", value=True)
        st.caption("Khi bật, xác nhận sẽ thay ánh xạ cùng characteristic của NFR này bằng scope đang chọn.")
        if st.button("Xác nhận scenario và tính lại", disabled=not acknowledged or label is None or not path or not responsible):
            try:
                from .studio_scenarios import review_scenario

                start = source.text.find(quote)
                if not quote.strip() or start < 0:
                    raise ValueError("Đoạn nguồn scenario cần khớp nguyên văn NFR.")
                record = ReviewedScenario(
                    scenario=Scenario(id=identifier, name=name, **{key: value or None for key, value in parts.items() if key not in {"stimulus", "response_measure"}},
                                      stimulus=parts["stimulus"], response_measure=parts["response_measure"], target=target_quote or None,
                                      quality_characteristic=label.value,
                                      source_ref=SourceRef(source_id=source_id, quote=quote, start=start, end=start + len(quote))),
                    source_digest=source.input_digest(), catalog_digest=catalog_digest(architecture), characteristic=label,
                    component_path=path, responsible_component_ids=responsible, metric=metric,
                    target_value=optional_number(threshold), target_unit=unit, completion=completion,
                    assumptions=TimingAssumptions(provenance=assumption_origin, semantics="ASSUMED_UPPER_BOUND_INCLUDING_WAIT",
                                                   component_ms={key: optional_number(value) for key, value in bounds.items()},
                                                   **{key: optional_number(value) for key, value in parameters.items()}, rationale=assumption_note),
                    actor=actor, rationale=rationale, decision_provenance=decision_origin,
                )
                changed, event = review_scenario(architecture, record, allocate=allocate)
                if commit_revision(changed, event):
                    st.session_state.architecture = changed
                    st.session_state.studio_scenario_select_next = (source_id, identifier)
                    st.session_state.studio_analyzed = True
                    st.session_state.editor_version += 1
                    st.session_state.studio_canvas_commit = st.session_state.get("studio_canvas_commit", 0) + 1
                    st.rerun()
            except ValueError as exc:
                st.error(str(exc))
        if saved:
            st.caption("Gỡ scenario chỉ bỏ profile dự đoán. Ánh xạ ISO đã review được giữ; muốn gỡ ánh xạ, dùng phần Ánh xạ NFR.")
            if st.button("Gỡ scenario đã chọn"):
                if not actor.strip() or not rationale.strip():
                    st.error("Điền người review và lý do gỡ scenario.")
                else:
                    data = architecture.model_dump(mode="json")
                    data["quality_scenarios"] = [item for item in data["quality_scenarios"] if item["scenario"]["id"] != selected]
                    changed = Architecture.model_validate(data)
                    if commit_revision(changed, {"action": "QUALITY_SCENARIO_REMOVED", "scenario_id": selected,
                                                 "actor": actor, "rationale": rationale, "provenance": decision_origin,
                                                 "before": architecture.model_dump(mode="json"),
                                                 "after": changed.model_dump(mode="json")}):
                        st.session_state.architecture = changed
                        st.session_state.studio_scenario_select_next = (source_id, None)
                        st.session_state.editor_version += 1
                        st.session_state.studio_canvas_commit = st.session_state.get("studio_canvas_commit", 0) + 1
                        st.rerun()


def show_prediction_comparison(candidates, plans) -> None:
    rows = [(slot, profile) for slot, candidate in zip("ABC", candidates)
            for profile in plans[candidate.id].get("quality_profiles", [])]
    if not rows:
        return
    labels = {"UNKNOWN": "Chưa đủ căn cứ", "UPPER_BOUND_WITHIN_TARGET": "Giới hạn giả định nằm trong ngưỡng",
              "UPPER_BOUND_EXCEEDS_TARGET": "Giới hạn giả định vượt ngưỡng"}
    with st.expander("Quality Profiles theo phương án", expanded=True):
        st.caption("Dự đoán có điều kiện theo các giả định đã review. Chưa có measurement và không gán quality PASS. "
                   "Biên trên vượt ngưỡng chưa chứng minh độ trễ thực tế sẽ vượt ngưỡng.")
        st.caption("Thứ hạng và Pareto phía trên dùng năm tiêu chí điểm thiết kế. Profile là thông tin bổ sung để review lựa chọn.")
        st.dataframe([{"Phương án": f"{slot} · {profile['candidate_id']}", "Scenario": profile["scenario_id"],
                       "NFR": profile["source_id"], "Characteristic": profile["characteristic"],
                       "Quantum chịu trách nhiệm": ", ".join(profile["quanta"]),
                       "Giới hạn dự đoán (ms)": profile["predicted_upper_ms"], "Mục tiêu (ms)": profile["target_ms"],
                       "Đối chiếu": labels[profile["target_comparison"]], "Đo thực tế": "NOT_MEASURED"}
                      for slot, profile in rows], hide_index=True, width="stretch")
        options = {f"{slot} · {profile['candidate_id']} · {profile['scenario_id']}": profile for slot, profile in rows}
        profile = options[st.selectbox("Giải thích một Quality Profile", list(options))]
        st.write(f"Scope · {', '.join(profile['scope'])} → {', '.join(profile['quanta'])}")
        st.write(profile["source_ref"]["quote"])
        st.dataframe([{"Phần scenario": PART_LABELS[field], "Giá trị": part["value"], "Nguồn": part["provenance"]}
                      for field, part in profile["scenario_parts"].items()], hide_index=True, width="stretch")
        if profile["drivers"]:
            st.dataframe([{"Đóng góp": driver["subject"], "Giới hạn (ms)": driver["upper_ms"], "Nguồn": driver["provenance"]}
                          for driver in profile["drivers"]], hide_index=True, width="stretch")
        st.caption(profile["assumption_rationale"])
        st.caption(f"Nguồn scenario · {profile['review_provenance']} · giả định thời gian · {profile['assumption_provenance']}")
        for issue in profile["issues"]:
            st.warning(issue)
