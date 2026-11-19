"""Interactive Quantum trade-off workbench."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import streamlit as st
from pydantic import ValidationError

from eqcr.quantum_example import ticket_example
from eqcr.quantum_tradeoff import Architecture, Candidate, Preferences, analyze, characteristic_index, explain_candidate, group_index
from eqcr.storage import save_quantum_review
from eqcr.studio_canvas import read_layout, render_board


st.set_page_config(page_title="Quantum Studio", layout="wide")
st.html(Path(__file__).with_name("eqcr") / "quantum_studio.css")

AXES = ("SYNC qua ranh giới", "Tách dữ liệu", "ASYNC giữ chung", "Characteristic rải nhiều nhóm", "Quantum trộn đặc tính")
AXIS_EFFECTS = (
    "Phụ thuộc qua Quantum làm tăng nhu cầu quản lý timeout, độ trễ và lỗi lan truyền.",
    "Cần quyết định quyền ghi, độ trễ đồng bộ và cách đối soát dữ liệu.",
    "Chưa dùng cơ hội cô lập hai component tại ranh giới ASYNC này.",
    "Một đặc tính cần phối hợp giữa nhiều Quantum.",
    "Một Quantum chịu trách nhiệm cho nhiều đặc tính.",
)
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
        if edge.mode == "ASYNC" and assignment[edge.source] != assignment[edge.target]:
            st.write(f"**{edge.source} → {edge.target}** tách qua ASYNC. Cần thiết kế giao nhận, retry và xử lý trùng.")


def candidate_costs(architecture: Architecture, candidate: Candidate, preferences: Preferences) -> list[dict]:
    return [
        {
            "axis": AXES[item.axis],
            "subject": item.subject,
            "components": list(item.components),
            "quanta": [f"Q{group}" for group in item.quanta],
            "units": item.units,
            "weight": preferences.vector[item.axis],
            "weighted_cost": item.units * preferences.vector[item.axis],
            "reason": AXIS_EFFECTS[item.axis],
        }
        for item in explain_candidate(architecture, candidate)
    ]


def plan_graph(architecture: Architecture, candidate: Candidate) -> dict:
    assignment = group_index(candidate.groups)
    _, labels = characteristic_index(architecture, assignment)
    return {
        "id": candidate.id,
        "label": f"{candidate.id} · {len(candidate.groups)} Quantum",
        "assignment": {item: f"Q{group}" for item, group in assignment.items()},
        "groups": [
            {"id": f"Q{index}", "components": list(group), "characteristics": sorted(labels.get(index, set()))}
            for index, group in enumerate(candidate.groups, 1)
        ],
    }


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


def show_comparison(architecture: Architecture) -> tuple[list[dict], bool]:
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
        return [], True
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
        return f"{candidate.id} · {len(candidate.groups)} Quantum"

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

    axis_weights = preferences.vector
    st.table([
        {"Chi phí mô hình": label, "Hệ số": weight, left.id + " · A": a, right.id + " · B": b,
         "B − A (đã nhân hệ số)": (b - a) * weight}
        for label, weight, a, b in zip(AXES, axis_weights, left.vector, right.vector, strict=True)
    ])
    score_delta = right.score(preferences) - left.score(preferences)
    improvements = [label for label, a, b in zip(AXES, left.vector, right.vector, strict=True) if b < a]
    drawbacks = [label for label, a, b in zip(AXES, left.vector, right.vector, strict=True) if b > a]
    if left.id != right.id:
        st.write(
            f"**{right.id} so với {left.id}** · giảm {', '.join(improvements) or '0 tiêu chí'} · "
            f"tăng {', '.join(drawbacks) or '0 tiêu chí'} · chênh {score_delta:+d} điểm."
        )
    st.caption("Điểm dùng để so sánh mô hình thiết kế. Độ trễ và độ tin cậy cần được đo riêng.")
    details = {item.id: candidate_costs(architecture, item, preferences) for item in (left, right)}
    for column, candidate in ((left_col, left), (right_col, right)):
        with column.container(border=True):
            st.subheader(f"{option(candidate)} · {candidate.score(preferences)} điểm")
            for index, group in enumerate(candidate.groups, 1):
                st.write(f"**Q{index}** · {', '.join(names[item] for item in group)}")
            describe_partition(architecture, candidate)
            st.markdown("**Điểm phát sinh từ đâu**")
            if not details[candidate.id]:
                st.caption("Không có đóng góp chi phí theo các tiêu chí đã khai báo.")
            for detail in details[candidate.id]:
                st.write(f"**{detail['subject']}** · {detail['axis']} · {' / '.join(detail['quanta'])} · "
                         f"{detail['units']} × {detail['weight']} = {detail['weighted_cost']} điểm.")
                st.caption(detail["reason"])

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
                        "costs": dict(zip(AXES, item.vector, strict=True)), "cost_drivers": details[item.id],
                        "assignment": plan_graph(architecture, item)["assignment"]}
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
    return [plan_graph(architecture, item) for item in {row.id: row for row in (best, left, right)}.values()], False


example = ticket_example()
st.session_state.setdefault("architecture", example)
st.session_state.setdefault("editor_version", 0)
st.session_state.setdefault("studio_layout", {})
st.session_state.setdefault("studio_analyzed", False)
st.session_state.setdefault("studio_pending", False)
st.session_state.setdefault("studio_weights", Preferences())
architecture = st.session_state.architecture

st.html("""
<section class="studio-header">
    <p>EQCR / QAME</p>
    <h1>Quantum Studio</h1>
    <div>Chỉnh component trên sơ đồ, suy ra các Quantum và so sánh trade-off.</div>
</section>
""")
board = st.container()
if st.session_state.studio_analyzed and not st.session_state.studio_pending:
    st.session_state.studio_plans, st.session_state.studio_no_solution = show_comparison(architecture)
elif st.session_state.studio_pending:
    st.info("Bấm Phân tích sơ đồ để cập nhật trade-off và tiếp tục Human Review.")

with board:
    if architecture == example:
        st.caption("Mẫu Ticket Support · Nhãn Sync/Async, đặc tính và chính sách dữ liệu là giả định minh họa có thể chỉnh.")
    event = render_board(
        model=architecture.model_dump(mode="json"), example=example.model_dump(mode="json"),
        layout=st.session_state.studio_layout, revision=st.session_state.get("studio_canvas_commit", 0),
        plans=st.session_state.get("studio_plans", []), no_solution=st.session_state.get("studio_no_solution", False),
        error=st.session_state.get("studio_canvas_error", ""), pending=st.session_state.studio_pending,
    )
if isinstance(event, dict) and event.get("token") != st.session_state.get("studio_submission"):
    st.session_state.studio_submission = event.get("token")
    if event.get("action") == "dirty" and not st.session_state.studio_pending:
        st.session_state.studio_pending = True
        st.session_state.studio_canvas_error = ""
        st.rerun()
    if event.get("action") == "analyze":
        try:
            submitted = Architecture.model_validate(event.get("model"))
        except ValidationError as exc:
            issue = exc.errors(include_url=False)[0]
            field = " / ".join(str(part + 1) if isinstance(part, int) else part for part in issue["loc"])
            st.session_state.studio_canvas_error = f"{field} · {issue['msg']}" if field else issue["msg"]
            st.session_state.studio_pending = True
        else:
            if submitted != architecture:
                st.session_state.editor_version += 1
            st.session_state.architecture = submitted
            st.session_state.studio_layout = read_layout(submitted, event.get("layout"))
            st.session_state.studio_analyzed = True
            st.session_state.studio_pending = False
            st.session_state.studio_canvas_error = ""
            st.session_state.studio_canvas_commit = st.session_state.get("studio_canvas_commit", 0) + 1
        st.rerun()
