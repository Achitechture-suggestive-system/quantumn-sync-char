"""Interactive Quantum trade-off workbench."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import pandas as pd
import streamlit as st
from graphviz import Digraph, escape
from pydantic import ValidationError

from eqcr.quantum_example import ticket_example
from eqcr.quantum_tradeoff import Architecture, Candidate, Preferences, analyze, characteristic_index, group_index
from eqcr.storage import save_quantum_review


st.set_page_config(page_title="Quantum Studio", layout="wide")
st.html(Path(__file__).with_name("eqcr") / "quantum_studio.css")

INPUT = "Sơ đồ ban đầu"
EDIT = "Chỉnh đầu vào"
RESULTS = "So sánh phương án"
PALETTE = ("#007a67", "#385b9b", "#8e5d25", "#785c91", "#496e3c", "#9d4960", "#356b82", "#74644f")
MODE_COLOR = {"SYNC": "#ad493a", "ASYNC": "#007a67", "UNKNOWN": "#6e7980"}
AXES = ("SYNC qua ranh giới", "Tách dữ liệu", "ASYNC giữ chung", "Characteristic rải nhiều nhóm", "Quantum trộn đặc tính")
REVIEW_PRESETS = {
    "Ưu tiên giữ dữ liệu": Preferences(),
    "Ưu tiên tập trung đặc tính": Preferences(characteristics=4),
    "Ưu tiên giữ SYNC trong nhóm": Preferences(sync=8),
}
WEIGHT_FIELDS = (
    ("sync", "SYNC qua ranh giới"),
    ("data", "Tách dữ liệu"),
    ("async_seam", "Cơ hội tách ASYNC"),
    ("characteristics", "Tập trung đặc tính"),
)


def topology(architecture: Architecture, candidate: Candidate | None = None) -> Digraph:
    graph = Digraph(graph_attr={"rankdir": "LR", "bgcolor": "#f7f7ef", "pad": ".22", "nodesep": ".35",
                                "ranksep": ".65", "fontname": "Segoe UI"})
    graph.attr("node", shape="box", style="filled", fillcolor="#ffffff", color="#778981",
               fontcolor="#193331", fontname="Segoe UI", fontsize="11", margin=".15,.10")
    graph.attr("edge", fontname="Segoe UI", fontsize="10", arrowsize=".65")
    components = {item.id: item for item in architecture.components}
    assignment = group_index(candidate.groups) if candidate else {}
    _, labels = characteristic_index(architecture, assignment) if candidate else ({}, {})

    if candidate:
        for index, group in enumerate(candidate.groups, 1):
            accent = PALETTE[index - 1]
            with graph.subgraph(name=f"cluster_{index}") as region:
                label = ", ".join(sorted(labels.get(index, []))) or "Chưa gắn đặc tính"
                region.attr(label=escape(f"Q{index} | {label}"), color=accent, penwidth="1.5",
                            fontcolor=accent, fontsize="12", style="dashed", margin="14")
                for component_id in group:
                    region.node(f"c_{component_id}", label=escape(components[component_id].name))
    else:
        for component in architecture.components:
            graph.node(f"c_{component.id}", label=escape(component.name))

    for edge in architecture.interactions:
        color = MODE_COLOR[edge.mode]
        graph.edge(f"c_{edge.source}", f"c_{edge.target}", label=edge.mode, color=color, fontcolor=color,
                   style={"SYNC": "solid", "ASYNC": "dashed", "UNKNOWN": "dotted"}[edge.mode])

    for store in architecture.stores:
        owners = sorted({assignment.get(member, 0) for member in store.members})
        if len(owners) == 1:
            graph.node(f"d_{store.id}", label=escape(store.name), shape="cylinder", fillcolor="#e5eee5")
            for member in store.members:
                graph.edge(f"c_{member}", f"d_{store.id}", color="#8d9991", arrowhead="none")
            continue
        for owner in owners:
            store_node = f"d_{store.id}_{owner}"
            graph.node(store_node, label=escape(f"{store.name} · Q{owner}"), shape="cylinder", fillcolor="#f5e8d1")
            for member in store.members:
                if assignment[member] == owner:
                    graph.edge(f"c_{member}", store_node, color="#8d9991", arrowhead="none")
        for left, right in zip(owners, owners[1:]):
            graph.edge(f"d_{store.id}_{left}", f"d_{store.id}_{right}", label="Cần thiết kế đồng bộ",
                       color="#9a682f", fontcolor="#795326", dir="none", style="dotted", constraint="false")
    return graph


def go_to(page: str) -> None:
    st.session_state.studio_page = page


def load_example() -> None:
    st.session_state.architecture = ticket_example()
    st.session_state.editor_version += 1


def set_review_priority(preferences: Preferences) -> None:
    st.session_state.studio_weights = preferences
    for name, value in preferences.model_dump().items():
        st.session_state[f"studio_weight_{name}"] = value


def save_slider_weights() -> None:
    st.session_state.studio_weights = Preferences(
        **{name: st.session_state[f"studio_weight_{name}"] for name, _ in WEIGHT_FIELDS}
    )


def heading(title: str, detail: str) -> None:
    st.header(title)
    st.caption(detail)


def parse_list(value: str | None) -> list[str]:
    return [item.strip() for item in (value or "").split(";") if item.strip()]


def editor_frame(items, fields):
    return pd.DataFrame([item.model_dump() for item in items], columns=list(fields)).astype(fields)


def editor_records(frame):
    return [
        {key: value for key, value in row.items() if value is not None}
        for row in frame.astype(object).where(frame.notna(), None).to_dict("records")
    ]


def show_editor(architecture: Architecture) -> None:
    heading("Mô hình đầu vào", "Dùng ID để nối các bảng. Phân cách nhiều đặc tính hoặc nhiều ID bằng dấu chấm phẩy (;).")
    st.button("Nạp lại ví dụ Ticket Support", on_click=load_example)
    version = st.session_state.editor_version
    with st.form("architecture_editor"):
        st.markdown("#### Component và characteristics")
        component_rows = st.data_editor(
            [{**item.model_dump(), "characteristics": "; ".join(item.characteristics)} for item in architecture.components],
            num_rows="dynamic", hide_index=True, width="stretch", key=f"components_{version}",
            column_config={"id": "ID", "name": "Tên", "characteristics": "Đặc tính"},
        )
        st.markdown("#### Quan hệ giữa component")
        st.caption("SYNC tính thêm chi phí khi cắt qua Quantum. Giao dịch cục bộ là ràng buộc cứng và cần ghi căn cứ.")
        edge_rows = st.data_editor(
            editor_frame(architecture.interactions, {"source": "string", "target": "string", "mode": "string",
                                                       "weight": "Int64", "local_transaction": "boolean", "basis": "string"}),
            num_rows="dynamic", hide_index=True, width="stretch", key=f"edges_{version}",
            column_config={
                "source": "Từ ID", "target": "Đến ID",
                "mode": st.column_config.SelectboxColumn("Kiểu", options=["SYNC", "ASYNC", "UNKNOWN"], default="UNKNOWN"),
                "weight": st.column_config.NumberColumn("Mức ảnh hưởng", min_value=0, max_value=10, step=1, default=1),
                "local_transaction": st.column_config.CheckboxColumn("Giao dịch cục bộ", default=False),
                "basis": "Nguồn hoặc giả định",
            },
        )
        st.markdown("#### Kho dữ liệu")
        st.caption("KEEP_SHARED giữ các component cùng nhóm. SPLITTABLE cho phép tách và tính chi phí đồng bộ dữ liệu.")
        store_frame = editor_frame(architecture.stores, {"id": "string", "name": "string", "members": "object",
                                                         "policy": "string", "weight": "Int64", "basis": "string"})
        store_frame["members"] = store_frame["members"].map("; ".join).astype("string")
        store_rows = st.data_editor(
            store_frame,
            num_rows="dynamic", hide_index=True, width="stretch", key=f"stores_{version}",
            column_config={
                "id": "ID", "name": "Tên", "members": "Component IDs",
                "policy": st.column_config.SelectboxColumn("Chính sách", options=["KEEP_SHARED", "SPLITTABLE"], default="KEEP_SHARED"),
                "weight": st.column_config.NumberColumn("Mức ảnh hưởng", min_value=0, max_value=10, step=1, default=1),
                "basis": "Nguồn hoặc giả định",
            },
        )
        st.markdown("#### Cặp component bắt buộc tách")
        separate_rows = st.data_editor(
            editor_frame(architecture.keep_apart, {"left": "string", "right": "string", "basis": "string"}),
            num_rows="dynamic", hide_index=True, width="stretch", key=f"separate_{version}",
            column_config={"left": "ID thứ nhất", "right": "ID thứ hai", "basis": "Căn cứ"},
        )
        submitted = st.form_submit_button("Lưu mô hình", type="primary")
    if submitted:
        try:
            st.session_state.architecture = Architecture.model_validate({
                "components": [{**row, "characteristics": parse_list(row.get("characteristics"))} for row in component_rows],
                "interactions": [{"mode": "UNKNOWN", **row} for row in editor_records(edge_rows)],
                "stores": [{"policy": "KEEP_SHARED", **row, "members": parse_list(row.get("members"))}
                           for row in editor_records(store_rows)],
                "keep_apart": editor_records(separate_rows),
            })
        except (ValidationError, TypeError, AttributeError) as exc:
            st.error(f"Kiểm tra lại đầu vào. {exc}")
        else:
            st.session_state.editor_version += 1
            st.session_state.studio_page_saved = True
            st.rerun()
    if st.session_state.pop("studio_page_saved", False):
        st.success("Đã lưu mô hình. Bấm Phân tích Quantum để tính lại phương án.")
    st.button("Phân tích Quantum", type="primary", on_click=go_to, args=(RESULTS,), key="analyze_edit")


def describe_partition(architecture: Architecture, candidate: Candidate) -> None:
    assignment = group_index(candidate.groups)
    locations, labels = characteristic_index(architecture, assignment)
    one_to_one = (
        bool(locations)
        and len(labels) == len(candidate.groups)
        and all(len(items) == 1 for items in locations.values())
        and all(len(items) == 1 for items in labels.values())
    )
    st.caption("Ánh xạ đặc tính ↔ Quantum đạt 1:1." if one_to_one else "Ánh xạ đặc tính ↔ Quantum chưa đạt 1:1.")
    for characteristic, groups in sorted(locations.items()):
        st.write(f"**{characteristic}** · {', '.join(f'Q{group}' for group in sorted(groups))}")
    for edge in architecture.interactions:
        if assignment[edge.source] == assignment[edge.target]:
            if edge.mode == "ASYNC" and edge.weight:
                st.write(f"• {edge.source} → {edge.target} giữ chung. Có thể cân nhắc tách ở điểm ASYNC này.")
            continue
        message = {
            "SYNC": "SYNC qua ranh giới. Xem độ trễ, timeout và lỗi lan truyền.",
            "ASYNC": "ASYNC qua ranh giới. Chốt giao nhận, retry và xử lý trùng.",
            "UNKNOWN": "Chưa rõ Sync/Async. Cần xác nhận hợp đồng tương tác.",
        }[edge.mode]
        st.write(f"• {edge.source} → {edge.target} · {message}")
    for store in architecture.stores:
        if len({assignment[member] for member in store.members}) > 1:
            st.write(f"• **{store.name}** bị tách. Chốt quyền ghi, độ trễ dữ liệu và cách đối soát.")


@st.cache_data(show_spinner=False)
def calculate(architecture: Architecture, preferences: Preferences):
    return analyze(architecture, preferences)


def show_review(comparison: dict, left: Candidate, right: Candidate) -> None:
    st.subheader("Human Review")
    with st.form("quick_review"):
        note = st.text_input("Ghi chú review", placeholder="Ví dụ: chấp nhận đồng bộ Ticket DB để giữ một đặc tính cho mỗi nhóm",
                             max_chars=400)
        a, b, revise = st.columns(3)
        approve_a = a.form_submit_button(f"Chọn A · {left.id}", type="primary", width="stretch")
        approve_b = b.form_submit_button(f"Chọn B · {right.id}", width="stretch")
        request_changes = revise.form_submit_button("Yêu cầu chỉnh", width="stretch")
    if approve_a or approve_b or request_changes:
        if request_changes and not note.strip():
            st.error("Ghi điều cần chỉnh để lưu yêu cầu.")
            return
        review = {
            "id": f"review-{uuid4().hex}",
            "recorded_at": datetime.now(timezone.utc).isoformat(),
            "actor": "LOCAL_INTERACTIVE_REVIEWER",
            "decision": "REQUEST_CHANGES" if request_changes else "PREFERRED_CANDIDATE",
            "selected_candidate": left.id if approve_a else right.id if approve_b else None,
            "note": note.strip(),
            **comparison,
        }
        try:
            save_quantum_review(review)
        except OSError as exc:
            st.error(f"Không lưu được review. {exc}")
        else:
            st.session_state.studio_last_review = review
    recorded = st.session_state.get("studio_last_review")
    if recorded and recorded["architecture"] == comparison["architecture"]:
        selection = recorded["selected_candidate"]
        st.success(f"Đã lưu lựa chọn {selection}." if selection else "Đã lưu yêu cầu chỉnh.")
        if recorded["note"]:
            st.write(recorded["note"])
        st.download_button(
            "Tải quyết định review", json.dumps(recorded, ensure_ascii=False, indent=2),
            file_name=f"{recorded['id']}.json", mime="application/json",
        )


def show_comparison(architecture: Architecture) -> None:
    heading("So sánh phương án", "Chỉnh trọng số để xem khi nào việc giữ dữ liệu chung quan trọng hơn việc cô lập đặc tính.")
    for column, (label, preset) in zip(st.columns(3), REVIEW_PRESETS.items(), strict=True):
        column.button(label, on_click=set_review_priority, args=(preset,), width="stretch")
    with st.expander("Tùy chỉnh trọng số"):
        for column, (name, label) in zip(st.columns(4), WEIGHT_FIELDS, strict=True):
            key = f"studio_weight_{name}"
            st.session_state.setdefault(key, getattr(st.session_state.studio_weights, name))
            column.slider(label, 0, 10, key=key, on_change=save_slider_weights)
    preferences = st.session_state.studio_weights
    result = calculate(architecture, preferences)
    if not result.ranked:
        st.error(f"INFEASIBLE · Đã xét {result.enumerated} cách chia. Không có phương án thỏa mọi ràng buộc cứng.")
        st.caption("Kiểm tra xung đột giữa cặp bắt buộc tách, giao dịch cục bộ và kho phải giữ chung.")
        st.button("Sửa mô hình đầu vào", on_click=go_to, args=(EDIT,))
        return
    best = result.ranked[0]
    summaries = st.columns(4)
    for column, (label, value) in zip(summaries, (
        ("Đã xét", result.enumerated), ("Khả thi", len(result.feasible)),
        ("Trên biên Pareto", len(result.frontier)), ("Xếp đầu theo trọng số", f"{best.id} · {best.score(preferences)} điểm"),
    ), strict=True):
        column.metric(label, value)
    st.caption("Điểm càng thấp càng tốt. Trên biên Pareto, cải thiện một tiêu chí sẽ đánh đổi ít nhất một tiêu chí khác, nếu có phương án với bộ chi phí khác.")
    if any(edge.mode == "UNKNOWN" for edge in architecture.interactions):
        st.warning("Quan hệ UNKNOWN chưa góp vào điểm. Kiểm tra các quan hệ này trước khi chọn phương án.")
    names = {item.id: item.name for item in architecture.components}

    def option(candidate: Candidate) -> str:
        exemplar = {
            frozenset(map(frozenset, (("LOGIN", "PROFILE"), ("CREATE", "ROUTE", "COMPLETE"), ("REPORT",)))): " · Hình 2",
            frozenset(map(frozenset, (("LOGIN", "PROFILE", "CREATE"), ("ROUTE", "COMPLETE"), ("REPORT",)))): " · Hình 3",
        }.get(frozenset(map(frozenset, candidate.groups)), "") if architecture == ticket_example() else ""
        return f"{candidate.id}{exemplar} · {len(candidate.groups)} Quantum"

    show_all = st.checkbox("Bao gồm các phương án khả thi ngoài biên Pareto")
    options = sorted(result.feasible, key=lambda item: (item.score(preferences), len(item.groups), item.id)) if show_all else list(result.ranked)
    choices = {item.id: item for item in options}
    left_col, right_col = st.columns(2)
    # Keep the same pair visible as weights move. The ranking above updates independently.
    ids = sorted(choices)
    default_order = sorted(result.frontier, key=lambda item: (item.score(Preferences()), len(item.groups), item.id))
    initial_left = default_order[0].id
    initial_right = next((item.id for item in default_order if item.id != initial_left), initial_left)
    if best.id != initial_left:
        st.info(f"Ưu tiên hiện tại đổi phương án xếp đầu từ {initial_left} sang {best.id} · {choices[initial_left].score(preferences)} → {best.score(preferences)} điểm với cùng bộ trọng số.")
    generation = st.session_state.editor_version
    left_id = left_col.selectbox("Phương án A", ids, index=ids.index(initial_left), format_func=lambda key: option(choices[key]),
                                key=f"compare_a_{generation}_{show_all}")
    right_id = right_col.selectbox("Phương án B", ids, index=ids.index(initial_right), format_func=lambda key: option(choices[key]),
                                  key=f"compare_b_{generation}_{show_all}")
    left, right = choices[left_id], choices[right_id]

    axis_weights = (preferences.sync, preferences.data, preferences.async_seam, preferences.characteristics, preferences.characteristics)
    st.table([
        {"Chi phí mô hình": label, "Hệ số": weight, left.id + " · A": a, right.id + " · B": b,
         "B − A (đã nhân hệ số)": (b - a) * weight}
        for label, weight, a, b in zip(AXES, axis_weights, left.vector, right.vector, strict=True)
    ])
    st.caption("Điểm dùng để so sánh mô hình thiết kế. Độ trễ và độ tin cậy cần được đo riêng.")
    for column, candidate in ((left_col, left), (right_col, right)):
        with column.container(border=True):
            st.subheader(f"{option(candidate)} · {candidate.score(preferences)} điểm")
            st.graphviz_chart(topology(architecture, candidate), width="stretch")
            for index, group in enumerate(candidate.groups, 1):
                st.write(f"**Q{index}** · {', '.join(names[item] for item in group)}")
            describe_partition(architecture, candidate)

    comparison = {
        "status": "PROPOSED_NOT_VERIFIED",
        "input_provenance": "PREPARED_DEMO_ASSUMPTIONS" if architecture == ticket_example() else "USER_SUPPLIED",
        "architecture": architecture.model_dump(mode="json"),
        "preferences": preferences.model_dump(mode="json"),
        "enumerated": result.enumerated,
        "feasible": len(result.feasible),
        "pareto": len(result.frontier),
        "baseline_under_default_weights": initial_left,
        "recommended_under_weights": best.id,
        "comparison": [{"id": item.id, "groups": item.groups, "score": item.score(preferences),
                        "costs": dict(zip(AXES, item.vector, strict=True))}
                       for item in (left, right)],
    }
    show_review(comparison, left, right)

    with st.expander("Danh sách phương án Pareto"):
        st.dataframe(
            [{"Phương án": option(item), "Điểm": item.score(preferences),
              "Nhóm": " | ".join(", ".join(group) for group in item.groups),
              **dict(zip(AXES, item.vector, strict=True))}
             for item in result.ranked],
            hide_index=True, width="stretch",
        )
    st.download_button(
        "Tải bản so sánh JSON", json.dumps(comparison, ensure_ascii=False, indent=2),
        file_name="quantum-comparison.json", mime="application/json",
    )


st.session_state.setdefault("architecture", ticket_example())
st.session_state.setdefault("editor_version", 0)
st.session_state.setdefault("studio_page", INPUT)
st.session_state.setdefault("studio_weights", Preferences())
architecture = st.session_state.architecture

st.html("""
<section class="studio-header">
    <p>EQCR / QAME</p>
    <h1>Quantum Studio</h1>
    <div>Khám phá ranh giới kiến trúc từ component, luồng tương tác và đặc tính chất lượng.</div>
</section>
""")
page = st.radio("Bước phân tích", [INPUT, EDIT, RESULTS], horizontal=True, label_visibility="collapsed", key="studio_page")

if page == INPUT:
    main, guide = st.columns([2.25, 1], gap="large")
    with main:
        heading("Sơ đồ ban đầu", f"{len(architecture.components)} component · {len(architecture.interactions)} quan hệ · {len(architecture.stores)} kho dữ liệu")
        if architecture == ticket_example():
            st.caption("Ticket Support · component và kho lấy từ hình tham chiếu. Nhãn SYNC/ASYNC và đặc tính là giả định minh họa có thể chỉnh.")
        st.graphviz_chart(topology(architecture), width="stretch")
        with st.expander("Xem căn cứ quan hệ và kho dữ liệu"):
            for edge in architecture.interactions:
                st.write(f"**{edge.source} → {edge.target} · {edge.mode}** · {edge.basis or 'Chưa ghi căn cứ'}")
            for store in architecture.stores:
                st.write(f"**{store.name} · {store.policy}** · {store.basis or 'Chưa ghi căn cứ'}")
            for rule in architecture.keep_apart:
                st.write(f"**{rule.left} ↔ {rule.right} · Bắt buộc tách** · {rule.basis}")
    with guide:
        with st.container(border=True, key="studio_guide"):
            st.subheader("Cách chia Quantum")
            st.markdown(
                "1. **Nhập component.** Gắn đặc tính, quan hệ và kho dữ liệu.\n"
                "2. **Kiểm tra ràng buộc.** Giữ chung giao dịch cục bộ và kho bắt buộc.\n"
                "3. **So sánh phương án.** Cân bằng tách ASYNC, chi phí SYNC, dữ liệu và đặc tính."
            )
            st.button("Phân tích Quantum", type="primary", on_click=go_to, args=(RESULTS,), width="stretch")
            st.button("Chỉnh đầu vào", on_click=go_to, args=(EDIT,), width="stretch")
    st.dataframe([{"ID": item.id, "Component": item.name, "Characteristics": " · ".join(item.characteristics) or "Chưa gắn"}
                  for item in architecture.components], hide_index=True, width="stretch")
elif page == EDIT:
    show_editor(architecture)
else:
    show_comparison(architecture)
