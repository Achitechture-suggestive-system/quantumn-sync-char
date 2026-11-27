"""Interactive Quantum trade-off workbench."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import streamlit as st
from pydantic import ValidationError

from eqcr.quantum_example import ticket_example
from eqcr.quantum_tradeoff import (
    Architecture, Candidate, Preferences, Ranking, analyze, characteristic_index,
    component_profiles, explain_candidate, group_index, hard_constraints, ranking_key,
)
from eqcr.storage import save_quantum_review
from eqcr.studio_canvas import read_layout, render_board
from eqcr.studio_cases import new_case_requirements, ticket_requirement_cases
from eqcr.studio_conflicts import apply_reviewed_repair, conflict_witnesses, enforce_protected_rules, minimal_repairs, simulate_repair
from eqcr.studio_evidence import evidence_blockers
from eqcr.studio_oracles import REPLAY_MODES, matches_oracle, oracle_ticket_cases, replay_architecture, replay_outcome
from eqcr.studio_quality import ISO_EDITION, QualityCharacteristic, component_mentions, quality_suggestions
from eqcr.studio_review_ui import commit_revision, show_duplicate_review, show_evidence_review, show_interaction_review, show_live_review, show_rule_policy_review, show_session_history
from eqcr.studio_sessions import invalidate_changed_sources
from eqcr.studio_scenario_ui import show_prediction_comparison, show_scenario_review
from eqcr.studio_scenarios import predict_scenario
from eqcr.studio_boundaries import boundary_profiles
from eqcr.studio_boundary_ui import show_boundary_outputs, show_boundary_review
from eqcr.studio_semantic_ui import show_confirmed_clauses
from eqcr.studio_semantics import clause_reviews
from eqcr.studio_uncertainty import cases_are_current, conservative_order, score_bounds
from eqcr.studio_views import (
    candidate_card, conflict_evidence, constraint_cards, constraint_subject, cost_matrix, diagram_header, interaction_cards,
    iso_evidence, iso_route_preview, quantum_cards, requirement_cards, review_receipt,
)


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
    "Chia theo SYNC": (Preferences(), "SYNC_FIRST"),
    "Chia theo characteristics": (Preferences(), "CHARACTERISTIC_FIRST"),
    "Ưu tiên giữ dữ liệu": (Preferences(), "WEIGHTED"),
    "Ưu tiên tập trung đặc tính": (Preferences(characteristics=4), "WEIGHTED"),
}
WEIGHT_FIELDS = (
    ("sync", "SYNC qua ranh giới"),
    ("data", "Tách dữ liệu"),
    ("async_seam", "Cơ hội tách ASYNC"),
    ("characteristics", "Tập trung đặc tính"),
)


def set_review_priority(preferences: Preferences, ranking: Ranking) -> None:
    st.session_state.studio_weights = preferences
    st.session_state.studio_ranking = ranking
    for name, value in preferences.model_dump().items():
        st.session_state[f"studio_weight_{name}"] = value


def save_slider_weights() -> None:
    st.session_state.studio_weights = Preferences(
        **{name: st.session_state[f"studio_weight_{name}"] for name, _ in WEIGHT_FIELDS}
    )


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
    indexes = group_index(candidate.groups)
    assignment = {item: f"Q{group}" for item, group in indexes.items()}
    profiles = component_profiles(architecture)
    _, labels = characteristic_index(profiles, indexes)
    groups = []
    for index, group in enumerate(candidate.groups, 1):
        characteristic_sources = {
            label: [component for component in group if label in profiles[component]]
            for label in sorted(labels.get(index, set()))
        }
        groups.append({
            "id": f"Q{index}", "components": list(group), "characteristics": list(characteristic_sources),
            "characteristic_sources": characteristic_sources,
            "characteristic_requirements": {
                label: {owner: profiles[owner][label] for owner in owners}
                for label, owners in characteristic_sources.items()
            },
        })
    return {
        "id": candidate.id,
        "label": f"{candidate.id} · {len(candidate.groups)} Quantum",
        "assignment": assignment,
        "groups": groups,
        "quality_profiles": [predict_scenario(architecture, candidate, scenario) for scenario in architecture.quality_scenarios],
        "boundary_profiles": boundary_profiles(architecture, candidate),
        "interactions": [
            {
                **edge.model_dump(mode="json"),
                "case_review_status": "CURRENT" if cases_are_current(architecture, edge) else "STALE" if edge.cases else "NONE",
                "from_quantum": assignment[edge.source], "to_quantum": assignment[edge.target],
                "placement": "INTERNAL" if assignment[edge.source] == assignment[edge.target] else "CROSS_QUANTUM",
            }
            for edge in architecture.interactions
        ],
    }


@st.cache_data(show_spinner=False)
def calculate(architecture: Architecture, preferences: Preferences, ranking: Ranking, conservative=False, time_limit_seconds=8.0):
    return analyze(architecture, preferences, ranking=ranking, conservative=conservative, time_limit_seconds=time_limit_seconds)


@st.cache_data(show_spinner=False)
def diagnose_conflicts(architecture: Architecture):
    rules = hard_constraints(architecture)
    return conflict_witnesses(rules), minimal_repairs(architecture, rules)


def show_conflict_repairs(architecture: Architecture, weights: Preferences, ranking: Ranking, *, can_apply: bool = True) -> None:
    st.header("Vì sao không có nghiệm?", anchor="studio-conflicts")
    names = {item.id: item.name for item in architecture.components}
    conflicts, repairs = diagnose_conflicts(architecture)
    if not conflicts:
        st.warning("Chưa tìm được chuỗi ràng buộc để giải thích. Hãy kiểm tra các quy tắc cứng của sơ đồ.")
        return
    for index, conflict in enumerate(conflicts, 1):
        subject = constraint_subject(conflict.separation, architecture, names)
        with st.expander(f"Xung đột {index} · {subject}", expanded=index == 1):
            st.html(conflict_evidence(conflict, architecture, names))

    st.subheader("Mô phỏng các cách gỡ xung đột")
    st.caption("Mỗi hàng nêu các quy tắc cần sửa cùng nhau để có nghiệm trở lại. Kết quả dùng bản sao mô phỏng, "
               "mô hình gốc vẫn ở trạng thái INFEASIBLE.")
    if len(architecture.components) > 8:
        st.caption("CP-SAT tìm tối đa ba tập sửa trong thời hạn. Mỗi tập đã kiểm tối thiểu theo bao hàm bằng closure; "
                   "chưa liệt kê mọi MCS hoặc đếm toàn bộ phân hoạch sau sửa. OPTIMAL nói về chi phí sửa của lần tìm tương ứng.")
    actions = {"KEEP_APART": "Bỏ yêu cầu tách", "LOCAL_TRANSACTION": "Bỏ yêu cầu giao dịch cục bộ, giữ SYNC",
               "KEEP_SHARED": "Cho phép tách kho"}
    labels = [" + ".join(f"{actions[rule.kind]} · {constraint_subject(rule, architecture, names)}"
                         for rule in repair.rules) for repair in repairs]
    st.dataframe([{"Phương án": f"M{index}", "Thay đổi giả định": label,
                   "Chi phí sửa": repair.review_cost, "Số quy tắc": len(repair.rules), "Nghiệm khả thi": repair.feasible,
                   "Bộ giải": repair.solver_status, "Chi phí sửa đã chứng minh": repair.cost_optimality_proven}
                  for index, (repair, label) in enumerate(zip(repairs, labels, strict=True), 1)],
                 hide_index=True, width="stretch", column_config={"Thay đổi giả định": st.column_config.TextColumn(width="large")})
    if not repairs:
        st.warning("Không có cách gỡ tuân thủ chính sách bảo vệ hiện hành. Review chính sách hoặc bổ sung yêu cầu làm rõ.")
        return
    selected = st.selectbox("Xem chi tiết mô phỏng", range(len(repairs)), format_func=lambda index: f"M{index + 1} · {labels[index]}")
    repair = repairs[selected]
    alternative = simulate_repair(architecture, repair)
    result = calculate(alternative, weights, ranking)
    best = result.ranked[0]
    qualifier = "ít nhất " if result.search else ""
    st.markdown(f"**M{selected + 1} · {qualifier}{len(result.feasible)} nghiệm khả thi · {best.id} xếp đầu · {best.score(weights)} điểm**")
    plan = plan_graph(alternative, best)
    st.html(quantum_cards(plan, names))
    if can_apply:
        st.caption("Các quy tắc thay đổi đã liệt kê phía trên. Áp dụng sẽ tạo revision mới từ bản sao đã xem.")
        actor = st.text_input("Người duyệt cách sửa", value="LOCAL_INTERACTIVE_REVIEWER", max_chars=100)
        rationale = st.text_area("Lý do áp dụng cách sửa", max_chars=1000)
        if st.button("Áp dụng cách sửa đã review"):
            try:
                changed, event = apply_reviewed_repair(architecture, repair, actor=actor, rationale=rationale)
                if commit_revision(changed, event):
                    st.session_state.architecture = changed
                    st.session_state.editor_version += 1
                    st.session_state.studio_analyzed = True
                    st.session_state.studio_canvas_commit = st.session_state.get("studio_canvas_commit", 0) + 1
                    st.rerun()
            except ValueError as exc:
                st.error(str(exc))


def open_oracle_case(case: dict, mode: str) -> None:
    session = st.session_state
    if session.studio_pending:
        return
    fixture = replay_architecture(case, mode)
    if "studio_case_return" not in session:
        session.studio_case_return = {
            name: session.get(name) for name in ("architecture", "studio_layout", "studio_analyzed",
                                                  "studio_weights", "studio_ranking", "studio_output_slot", "studio_conservative")
        }
    session.studio_replay = (case["id"], mode)
    session.architecture = fixture
    session.studio_layout = {}
    session.studio_analyzed = True
    session.studio_conservative = False
    session.studio_canvas_error = ""
    session.editor_version += 1
    session.studio_canvas_commit = session.get("studio_canvas_commit", 0) + 1
    session.pop("studio_output_slot", None)
    set_review_priority(Preferences(), "WEIGHTED")


def close_oracle_case() -> None:
    session = st.session_state
    if session.studio_pending:
        return
    original = session.pop("studio_case_return")
    session.pop("studio_replay")
    set_review_priority(original.pop("studio_weights"), original.pop("studio_ranking"))
    slot = original.pop("studio_output_slot")
    session.pop("studio_output_slot", None)
    if slot is not None:
        session.studio_output_slot = slot
    session.update(original)
    session.editor_version += 1
    session.studio_canvas_commit = session.get("studio_canvas_commit", 0) + 1


def show_oracle_cases(architecture: Architecture, active: tuple[str, str] | None) -> None:
    st.html('<span id="studio-oracles" class="qs-anchor"></span>')
    with st.expander("Ca khó và oracle", expanded=active is not None):
        cases = oracle_ticket_cases()
        case = cases[st.selectbox("Ca kiểm thử", list(cases), key="studio_oracle_picker",
                                  format_func=lambda key: f"{key} · {cases[key]['title']}")]
        st.write(case["text"])
        for reference in case["context"]:
            st.caption(f"{reference['id']} · {reference['text']}")
        st.caption(f"Oracle · {case['status']}" + (f" · Trùng {case['duplicate_of']}" if case.get("duplicate_of") else ""))
        options = ["draft", "oracle"]
        if "saved_model" in case:
            options.append("saved_model")
            st.caption(f"Phát lại {case['saved_model']['model']} từ phản hồi đã lưu. "
                       "Phản hồi có giao dịch cục bộ và thiếu chính sách bắt buộc tách.")
        mode = st.radio("Chế độ nạp", options, format_func=REPLAY_MODES.__getitem__, horizontal=True,
                        key=f"studio_oracle_mode_{case['id']}")
        baseline = calculate(ticket_example(), Preferences(), "WEIGHTED")
        rows = []
        for method in options:
            result = calculate(replay_architecture(case, method), Preferences(), "WEIGHTED")
            outcome = replay_outcome(result)
            if method == "draft":
                verdict = "Giữ nguyên mẫu" if result == baseline else "Lệch mẫu"
            elif method == "oracle":
                verdict = "Khớp oracle" if matches_oracle(result, case["expected"]) else "Lệch oracle"
            else:
                verdict = "Tái hiện sai lệch so với oracle" if matches_oracle(result, case["saved_model"]["expected"]) else "Lệch kết quả đã lưu"
            rows.append({"Chế độ": REPLAY_MODES[method], "Khả thi": outcome["feasible"],
                         "Xếp đầu": outcome["leader"] or "INFEASIBLE",
                         "Điểm": str(outcome["score"]) if outcome["score"] is not None else "—", "Đối chiếu": verdict})
        st.dataframe(rows, hide_index=True, width="stretch")
        st.caption("Bảng dùng trọng số mặc định. Nạp ca để xem sơ đồ, trade-off và truy vết trong phiên mô phỏng riêng.")
        if active:
            loaded_case, loaded_mode = active
            note = f"Đang mở {loaded_case} · {REPLAY_MODES[loaded_mode]}"
            if architecture != replay_architecture(cases[loaded_case], loaded_mode):
                note += " · Có chỉnh sửa trong phiên thử"
            st.info(note)
        pending = st.session_state.studio_pending
        if pending:
            st.caption("Bấm Phân tích sơ đồ để lưu chỉnh sửa đang làm trước khi đổi phiên.")
        load, leave, suite = st.columns(3)
        load.button("Nạp ca vào sơ đồ", on_click=open_oracle_case, args=(case, mode), disabled=pending,
                    width="stretch", type="primary")
        if active:
            leave.button("Quay lại sơ đồ của tôi", on_click=close_oracle_case, disabled=pending, width="stretch")
        if suite.button("Chạy cả 12 ca", width="stretch"):
            st.session_state.studio_oracle_suite = True
        if st.session_state.get("studio_oracle_suite"):
            suite_rows = []
            passed = 0
            for item in cases.values():
                draft = calculate(replay_architecture(item, "draft"), Preferences(), "WEIGHTED")
                outcome = calculate(replay_architecture(item, "oracle"), Preferences(), "WEIGHTED")
                agrees = draft == baseline and matches_oracle(outcome, item["expected"])
                passed += agrees
                suite_rows.append({"Ca": item["id"], "Nháp khả thi": len(draft.feasible),
                                   "Theo oracle khả thi": len(outcome.feasible),
                                   "Xếp đầu theo oracle": replay_outcome(outcome)["leader"] or "INFEASIBLE",
                                   "Đối chiếu": "Khớp" if agrees else "Lệch"})
            st.write(f"{passed}/{len(cases)} ca khớp oracle của bộ giải.")
            st.dataframe(suite_rows, hide_index=True, width="stretch")


def show_traceability(architecture: Architecture, plan: dict, names: dict[str, str]) -> None:
    st.header("Hồ sơ và truy vết", anchor="studio-trace")
    st.caption(f"Theo sơ đồ đang hiển thị · {plan['label']}")
    groups, edges, stores, requirements = st.tabs(["Quantum", "Tương tác", "Kho và ràng buộc", "Requirements"])
    with groups:
        st.html(quantum_cards(plan, names))
    with edges:
        st.html(interaction_cards(plan, names))
    with stores:
        st.html(constraint_cards(architecture, plan, names))
    with requirements:
        st.html(requirement_cards(architecture, plan, names))


def show_nfr_review(architecture: Architecture, plans: list[dict], replay: tuple[str, str] | None = None) -> None:
    nfrs = {item.id: item for item in architecture.requirements if item.kind == "NFR"}
    if not nfrs:
        return
    st.html('<span id="studio-iso" class="qs-anchor"></span>')
    with st.expander(f"Ánh xạ NFR vào {ISO_EDITION}", expanded=True):
        ids = list(nfrs)
        initial = ids.index(replay[0]) if replay and replay[0] in nfrs else 0
        key = f"studio_replay_nfr_{st.session_state.editor_version}" if replay else None
        requirement = nfrs[st.selectbox("NFR nguồn", ids, index=initial, key=key)]
        if requirement.duplicate_of:
            st.info(f"{requirement.id} dùng mục tiêu và ánh xạ của {requirement.duplicate_of}. "
                    "Chọn bản gốc để sửa ánh xạ, hoặc tách tại Review yêu cầu cùng mục tiêu.")
            st.write(requirement.text)
            return
        suggested = quality_suggestions(requirement.text)
        model_suggestion = requirement.model_suggestion
        names = {item.id: item.name for item in architecture.components}
        mentions = component_mentions(requirement.text, names)
        confirmed = {item.characteristic: item for item in requirement.quality_allocations}
        st.html(iso_evidence(requirement, suggested, mentions, confirmed, names, simulation=replay is not None))
        linked = [
            item.id for item in architecture.components
            if any(requirement.id in references for references in item.characteristic_requirements.values())
        ]
        if requirement.component_ids:
            components, origin = requirement.component_ids, "Theo phạm vi khai báo trong requirement"
        elif linked:
            components, origin = linked, "Theo các liên kết characteristic đã gắn requirement"
        elif mentions:
            components, origin = list(mentions), "Theo tên hoặc mã component xuất hiện trong nguồn"
        else:
            components, origin = [], "Chưa xác định được component từ dữ liệu nguồn"
        default = next(iter(confirmed), model_suggestion[0] if model_suggestion else next(iter(suggested), None))
        labels = list(QualityCharacteristic)
        generation = st.session_state.editor_version
        label = st.selectbox("Characteristic ISO", labels, index=labels.index(default) if default else None,
                             key=f"quality_label_{requirement.id}_{generation}")
        if label is None:
            st.html(iso_route_preview(components, names, plans, origin=origin, applied=False))
            return
        saved = confirmed.get(label)
        if saved:
            show_confirmed_clauses(saved, names, plans)
        selected = st.multiselect("Component ứng viên", list(names),
                                  default=saved.component_ids if saved else components,
                                  format_func=names.__getitem__, key=f"quality_components_{requirement.id}_{labels.index(label)}_{generation}")
        applied = saved is not None and set(selected) == set(saved.component_ids)
        if applied:
            origin = "Theo component trong phiên mô phỏng" if replay else "Theo danh sách component đã xác nhận"
        elif set(selected) != set(components):
            origin = "Theo danh sách component bạn đang chọn"
        st.html(iso_route_preview(selected, names, plans, origin=origin, applied=applied, simulation=replay is not None))
        initial_quote = (saved.source_quote if saved else model_suggestion[1]
                         if model_suggestion and model_suggestion[0] == label else suggested.get(label, ""))
        quote = st.text_area("Căn cứ cho ánh xạ ISO", value=initial_quote, max_chars=600,
                             key=f"quality_quote_{requirement.id}_{labels.index(label)}_{generation}")
        rationale = st.text_input("Lý do bổ sung của reviewer", max_chars=1000,
                                  key=f"quality_rationale_{requirement.id}_{labels.index(label)}_{generation}")
        apply, remove = st.columns(2)
        confirmed_now = apply.button("Xác nhận gán ISO", disabled=not selected)
        removed_now = remove.button("Gỡ ánh xạ ISO", disabled=label not in confirmed)
        if confirmed_now or removed_now:
            if confirmed_now and ((quote and quote not in requirement.text) or (not quote.strip() and not rationale.strip())):
                st.error("Chọn đoạn nguyên văn trong requirement, hoặc ghi căn cứ bổ sung khi nguồn chưa diễn đạt đủ.")
                return
            model = architecture.model_dump(mode="json")
            target = next(item for item in model["requirements"] if item["id"] == requirement.id)
            target["quality_allocations"] = [item for item in target["quality_allocations"] if item["characteristic"] != label]
            if confirmed_now:
                target["quality_allocations"].append({
                    "characteristic": label, "component_ids": selected, "source_quote": quote,
                })
            changed = Architecture.model_validate(model)
            if replay is None and not commit_revision(changed, {
                "action": "MANUAL_ISO_CONFIRM" if confirmed_now else "MANUAL_ISO_REMOVE",
                "actor": "LOCAL_INTERACTIVE_REVIEWER", "source_id": requirement.id,
                "source_digest": requirement.input_digest(), "characteristic": label,
                "source_quote": quote, "rationale": rationale,
                "before": architecture.model_dump(mode="json"), "after": changed.model_dump(mode="json"),
            }):
                return
            st.session_state.architecture = changed
            st.session_state.editor_version += 1
            st.session_state.studio_canvas_commit = st.session_state.get("studio_canvas_commit", 0) + 1
            st.rerun()


def show_requirement_cases(architecture: Architecture) -> None:
    with st.expander("Thêm requirement từ Ollama"):
        if st.session_state.studio_pending:
            st.info("Bấm Phân tích sơ đồ để lưu chỉnh sửa đang làm rồi nạp requirement LLM.")
            return
        cases = ticket_requirement_cases()
        case = cases[st.selectbox("Kịch bản Ticket Support", list(cases), format_func=lambda key: cases[key]["title"])]
        available = {item.id: item for item in new_case_requirements(architecture, case)}
        st.caption(f"Ollama {case['ollama_version']} · {case['model']} · {case['created_at'][:10]} UTC · "
                   f"{case['generated_tokens']} token đầu ra · SHA-256 {case['response_sha256'][:16]}…")
        st.write(case["brief"])
        if not available:
            st.info("Các requirement của gói đã được nạp hoặc sơ đồ thiếu component tương ứng trong mẫu Ticket Support.")
            return
        remaining = 40 - len(architecture.requirements)
        if remaining == 0:
            st.info("Sơ đồ đã đủ 40 requirement. Gỡ bớt requirement trước khi nạp thêm.")
            return
        st.dataframe([
            {"Mã": item.id, "Loại": item.kind, "Yêu cầu giả lập": item.text,
             "Component": ", ".join(item.component_ids),
             "Nhãn LLM có đoạn trích": item.model_suggestion[0].value if item.model_suggestion else "—"}
            for item in available.values()
        ], hide_index=True, width="stretch")
        selected = st.multiselect("Requirement để nạp vào sơ đồ", list(available),
                                  default=list(available)[:remaining], max_selections=remaining,
                                  key=f"studio_pack_{case['id']}_{st.session_state.editor_version}")
        st.caption("Bản nháp tổng hợp. NFR chỉ góp vào điểm phân nhóm sau khi bạn xác nhận ánh xạ ISO.")
        if st.button("Nạp requirement đã chọn", disabled=not selected):
            data = architecture.model_dump(mode="json")
            data["requirements"].extend(available[item].model_dump(mode="json") for item in selected)
            st.session_state.architecture = Architecture.model_validate(data)
            st.session_state.studio_analyzed = True
            st.session_state.editor_version += 1
            st.session_state.studio_canvas_commit = st.session_state.get("studio_canvas_commit", 0) + 1
            st.rerun()


def show_review(comparison: dict, candidates: list[Candidate]) -> None:
    st.header("Human Review", anchor="studio-review")
    st.caption("Lưu phương án bạn ưu tiên cùng mô hình, trọng số và ghi chú tại thời điểm review.")
    with st.form("quick_review"):
        note = st.text_input("Ghi chú review", placeholder="Ví dụ: chấp nhận đồng bộ Ticket DB để giữ một đặc tính cho mỗi nhóm",
                             max_chars=400)
        *columns, revise = st.columns(len(candidates) + 1)
        approvals = [
            item.id for label, item, column in zip("ABC"[:len(candidates)], candidates, columns, strict=True)
            if column.form_submit_button(f"Chọn {label} · {item.id}", width="stretch")
        ]
        request_changes = revise.form_submit_button("Yêu cầu chỉnh", width="stretch")
    if approvals or request_changes:
        if request_changes and not note.strip():
            st.error("Ghi điều cần chỉnh để lưu yêu cầu.")
            return
        review = {
            "id": f"review-{uuid4().hex}",
            "recorded_at": datetime.now(timezone.utc).isoformat(),
            "actor": "LOCAL_INTERACTIVE_REVIEWER",
            "decision": "REQUEST_CHANGES" if request_changes else "PREFERRED_CANDIDATE",
            "selected_candidate": next(iter(approvals), None),
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
        st.html(review_receipt(recorded))
        st.download_button(
            "Tải quyết định review", json.dumps(recorded, ensure_ascii=False, indent=2),
            file_name=f"{recorded['id']}.json", mime="application/json",
        )


def show_comparison(architecture: Architecture, details_panel, evidence_panel,
                    replay: tuple[str, str] | None = None) -> tuple[list[dict], bool, str | None]:
    st.header("So sánh phương án", anchor="studio-tradeoffs")
    if blockers := evidence_blockers(architecture):
        st.warning("Cần review lại căn cứ nguồn trước khi phân nhóm. Các ràng buộc cứng hiện hành vẫn được giữ.")
        for blocker in blockers:
            details_panel.write(f"{blocker['source_id']} · {' '.join(blocker['issues'])}")
        st.markdown("[Review căn cứ nguồn](#studio-source-review)")
        st.markdown("[Review hợp đồng tương tác](#studio-boundaries)")
        return [], False, None
    preferences = st.session_state.studio_weights
    ranking = st.session_state.studio_ranking
    with st.expander("Ưu tiên phân nhóm và trọng số"):
        for column, (label, preset) in zip(st.columns(len(REVIEW_PRESETS)), REVIEW_PRESETS.items(), strict=True):
            active = preset == (preferences, ranking)
            column.button(label, on_click=set_review_priority, args=preset, type="primary" if active else "secondary", width="stretch")
        for column, (name, label) in zip(st.columns(4), WEIGHT_FIELDS, strict=True):
            key = f"studio_weight_{name}"
            st.session_state.setdefault(key, getattr(st.session_state.studio_weights, name))
            column.slider(label, 0, 10, key=key, on_change=save_slider_weights)
    uncertain = any(edge.mode == "UNKNOWN" for edge in architecture.interactions)
    conservative = uncertain and st.checkbox("Ưu tiên chi phí biên trên khi còn bất định", key="studio_conservative")
    large = len(architecture.components) > 8
    if large:
        st.session_state.setdefault("studio_search_seconds", 8)
        limit = st.slider("Thời hạn tìm phương án (giây)", 1, 30, key="studio_search_seconds")
    else:
        limit = 8
    with st.spinner("Đang tìm phương án theo ràng buộc và năm trục chi phí…", show_time=large):
        result = calculate(architecture, preferences, ranking, conservative, limit)
    if not result.ranked:
        if large:
            st.error("INFEASIBLE · Closure của các quy tắc cùng Quantum xung đột với một yêu cầu khác Quantum.")
        else:
            st.error(f"INFEASIBLE · Đã xét {result.enumerated} cách chia. Không có phương án thỏa mọi ràng buộc cứng.")
        st.markdown("[Xem xung đột và các cách gỡ](#studio-conflicts)")
        with details_panel:
            show_conflict_repairs(architecture, preferences, ranking, can_apply=replay is None)
        return [], True, None
    if large:
        details_panel.caption(f"CP-SAT {result.search['solver_version']} · mục tiêu chính {result.search['primary_status']} · "
                              f"{result.search['elapsed_seconds']:.2f} giây. Chi phí được tính lại bằng Python và hard constraints được kiểm cho từng phương án.")
        details_panel.caption("Tập ứng viên gồm nghiệm từ các mục tiêu tìm kiếm và seed hợp lệ. Chưa liệt kê mọi nghiệm hoặc Pareto toàn cục. "
                              "Chứng minh tối ưu chỉ áp dụng chi phí chính khi OPTIMAL; tie theo số nhóm/ID và so Pareto được giới hạn trong tập đã tìm.")
    robust = conservative_order(architecture, result.feasible, preferences) if conservative else ()
    best = robust[0] if conservative else result.ranked[0]
    if conservative:
        details_panel.caption(("Đang chọn biên trên thấp nhất trong tập đã tìm; trạng thái chứng minh của mục tiêu chính ghi phía trên. " if large else
                               "Đang giảm chi phí biên trên theo trọng số trên toàn bộ phương án thỏa ràng buộc cứng. ") +
                              "Nhãn Pareto và ma trận năm trục bên dưới dựa trên các cạnh đã xác định mode.")
    elif ranking == "SYNC_FIRST":
        details_panel.caption("Đang chia theo SYNC. Bộ giải giảm tổng mức ảnh hưởng của các cạnh SYNC bị cắt trước, "
                              "sau đó giảm ASYNC giữ chung, rồi mới so điểm trọng số.")
        if best.sync:
            details_panel.info(f"Chi phí SYNC {'của phương án đang xếp đầu' if large else 'thấp nhất qua ranh giới'} là {best.sync} với các ràng buộc đang bật.")
    elif ranking == "CHARACTERISTIC_FIRST":
        details_panel.caption("Đang chia theo characteristics. Bộ giải giảm đặc tính rải nhiều Quantum trước, "
                              "sau đó giảm trộn đặc tính trong một Quantum, rồi mới so điểm trọng số.")
        if best.sync:
            details_panel.info(f"Phương án này có chi phí SYNC qua ranh giới là {best.sync}. Xem các luồng trong phần truy vết.")
    else:
        details_panel.caption("Đang xếp theo điểm trọng số. Cạnh SYNC qua ranh giới góp vào tổng điểm.")
    summaries = details_panel.columns(4)
    best_bounds = score_bounds(architecture, best, preferences)
    best_cost = f"{best_bounds.lower}–{best_bounds.upper}" if uncertain else str(best.score(preferences))
    for column, (label, value) in zip(summaries, (
        ("Bộ giải" if large else "Đã xét", "CP-SAT" if large else result.enumerated),
        ("Khả thi đã tìm" if large else "Khả thi", len(result.feasible)),
        ("Không trội trong tập đã tìm" if large else "Trên biên Pareto", len(result.frontier)), ("Xếp đầu", f"{best.id} · {best_cost} điểm"),
    ), strict=True):
        column.metric(label, value)
    if uncertain:
        bounds = score_bounds(architecture, best, preferences)
        details_panel.warning(f"Cạnh chưa xác định mode góp vào khoảng chi phí, không được coi là miễn phí. "
                              f"{bounds.unresolved_edges} cạnh chưa rõ · {bounds.conditional_edges} cạnh có điều kiện được review. "
                              f"{best.id} có khoảng {bounds.lower}–{bounds.upper} điểm theo tập giả thuyết hiện tại.")
        total = len(architecture.interactions)
        covered = total - bounds.unresolved_edges
        details_panel.caption(f"Độ phủ khai báo mode/điều kiện còn hiệu lực · {covered}/{total} cạnh. "
                              "Con số này không đo độ đúng ngữ nghĩa của quyết định.")
    names = {item.id: item.name for item in architecture.components}
    best_plan = plan_graph(architecture, best)

    frontier_ids = {item.id for item in result.frontier}

    def option(candidate: Candidate) -> str:
        status = ("Không trội trong tập tìm" if candidate.id in frontier_ids else "Đã có phương án trội") if large else "Pareto" if candidate.id in frontier_ids else "Ngoài Pareto"
        return f"{candidate.id} · {len(candidate.groups)} Quantum · {status}"

    show_all = st.checkbox("Cho chọn từ toàn bộ tập khả thi đã tìm" if large else "Cho chọn từ toàn bộ phương án khả thi")
    default_order = sorted(result.frontier, key=lambda item: ranking_key(item, Preferences(), "WEIGHTED"))
    initial_left = default_order[0]
    defaults = list(dict.fromkeys([initial_left, best, *default_order]))[:3]
    other_feasible = list(robust) if conservative else sorted(result.feasible, key=lambda item: ranking_key(item, preferences, ranking))
    if len(defaults) < 3:
        defaults = list(dict.fromkeys([*defaults, *other_feasible]))[:3]
    options = other_feasible if show_all else list(dict.fromkeys([*result.ranked, *defaults]))
    choices = {item.id: item for item in options}
    if len(defaults) < 3:
        details_panel.info(f"{'Đang có' if large else 'Chỉ có'} {len(defaults)} phương án khả thi {'trong tập đã tìm' if large else 'theo ràng buộc hiện tại'}.")
    elif any(item.id not in frontier_ids for item in defaults):
        details_panel.caption(("Biên không trội trong tập đã tìm" if large else "Biên Pareto") + " có ít hơn ba phương án. Studio bổ sung phương án khả thi ngoài biên để so sánh.")
    if not conservative and ranking == "WEIGHTED" and best.id != initial_left.id:
        details_panel.info(f"Ưu tiên hiện tại đổi phương án xếp đầu từ {initial_left.id} sang {best.id} · {initial_left.score(preferences)} → {best.score(preferences)} điểm với cùng bộ trọng số.")
    generation = st.session_state.editor_version
    columns = st.columns(len(defaults))
    slots = "ABC"[:len(defaults)]
    candidates = []
    selected_ids = []
    for slot, column, default in zip(slots, columns, defaults, strict=True):
        available = sorted(set(choices) - set(selected_ids))
        selected = column.selectbox(
            f"Phương án {slot}", available, index=available.index(default.id) if default.id in available else 0,
            format_func=lambda key: option(choices[key]), key=f"compare_{slot}_{generation}_{show_all}_{conservative}_{'_'.join(selected_ids)}",
        )
        selected_ids.append(selected)
        candidates.append(choices[selected])
    plans = {best.id: best_plan, **{item.id: plan_graph(architecture, item) for item in candidates if item.id != best.id}}
    for slot, item in zip(slots, candidates, strict=True):
        plans[item.id]["label"] = f"{slot} · {option(item)}"
    initial_slot = slots[candidates.index(best)] if best in candidates else slots[0]
    active_slot = st.radio("Phương án hiển thị trên sơ đồ", list(slots), index=slots.index(initial_slot),
                           horizontal=True, key="studio_output_slot")
    active_id = candidates[slots.index(active_slot)].id

    axis_weights = preferences.vector
    baseline = candidates[0]
    details_panel.html(cost_matrix(AXES, axis_weights, candidates, slots))
    intervals = {item.id: score_bounds(architecture, item, preferences) for item in candidates}
    if uncertain:
        details_panel.dataframe([
            {"Phương án": f"{slot} · {item.id}", "Điểm cạnh đã xác định": item.score(preferences),
             "Biên dưới": intervals[item.id].lower, "Biên trên": intervals[item.id].upper}
            for slot, item in zip(slots, candidates, strict=True)
        ], hide_index=True, width="stretch")
        details_panel.caption("Khoảng điểm xét độc lập SYNC/ASYNC cho cạnh UNKNOWN, hoặc các mode trong điều kiện đã review. "
                              "Chưa có xác suất hay tương quan giữa các cạnh. Ràng buộc cứng được giữ trong mọi giả thuyết.")
    deltas = {
        item.id: {label: b - a for label, a, b in zip(AXES, baseline.vector, item.vector, strict=True)}
        for item in candidates
    }
    details = {item.id: candidate_costs(architecture, item, preferences) for item in candidates}
    dominated_by = {
        item.id: next((other.id for other in result.ranked if other.vector != item.vector and
                       all(a <= b for a, b in zip(other.vector, item.vector, strict=True))), None)
        for item in candidates if item.id not in frontier_ids
    }
    scale = max(1, *(item.score(preferences) for item in candidates))
    cards = "".join(
        candidate_card(slot, item, baseline=baseline, axes=AXES, weights=axis_weights, points=details[item.id],
                       plan=plans[item.id], names=names, ranked=item.id == best.id, frontier=item.id in frontier_ids,
                       displayed=item.id == active_id, dominator=dominated_by.get(item.id), scale=scale,
                       interval=intervals[item.id] if uncertain else None, frontier_scope="FOUND_POOL" if large else "GLOBAL")
        for slot, item in zip(slots, candidates, strict=True)
    )
    details_panel.html(f'<div class="qs-candidate-grid">{cards}</div>')
    details_panel.caption("Điểm so sánh là chi phí thiết kế. Độ trễ và độ tin cậy cần được đo riêng.")
    with details_panel:
        show_prediction_comparison(candidates, plans)
        show_boundary_outputs(architecture, next(item for item in candidates if item.id == active_id), replay=bool(replay))

    comparison = {
        "status": "PROPOSED_NOT_VERIFIED",
        "quality_standard": ISO_EDITION,
        "quality_measurement_status": "NOT_MEASURED",
        "input_provenance": ("SYNTHETIC_REPLAY" if replay else
                             "MIXED_WITH_PREPARED_SCENARIO_DATA" if any(item.decision_provenance == "PREPARED_FIXTURE" or
                                                                         item.assumptions.provenance == "PREPARED_FIXTURE"
                                                                         for item in architecture.quality_scenarios) else
                             "MIXED_WITH_PREPARED_BOUNDARY_DATA" if any(item.provenance == "PREPARED_FIXTURE" or item.reference_protocol
                                                                       for item in architecture.interaction_contracts) or
                                                                       any(item.provenance == "PREPARED_FIXTURE" for item in architecture.ownership_decisions) else
                             "MIXED_WITH_PREPARED_CLAUSE_REVIEW" if any(item.provenance == "PREPARED_FIXTURE" or item.claim_provenance == "PREPARED_FIXTURE"
                                                                       for item in clause_reviews(architecture)) else
                             "MIXED_WITH_SYNTHETIC_OLLAMA_REQUIREMENTS" if any(item.generation for item in architecture.requirements)
                             else "PREPARED_DEMO_ASSUMPTIONS" if architecture == ticket_example()
                             else "CONTAINS_PREPARED_FIXTURE_INPUT" if architecture.input_origin == "PREPARED_FIXTURE" else architecture.input_origin),
        "architecture": architecture.model_dump(mode="json"),
        "preferences": preferences.model_dump(mode="json"),
        "ranking": ranking,
        "uncertainty_policy": "MINIMIZE_WEIGHTED_UPPER_BOUND" if conservative else "KNOWN_MODE_COSTS",
        "enumerated": result.enumerated,
        "feasible": None if large else len(result.feasible),
        "feasible_found": len(result.feasible),
        "pareto": None if large else len(result.frontier),
        "pareto_in_found_pool": len(result.frontier) if large else None,
        "search": result.search or {"backend": "EXHAUSTIVE", "complete_feasible_set": True, "frontier_scope": "GLOBAL",
                                    "status": "OPTIMAL", "optimality_proven": True},
        "baseline_under_default_weights": initial_left.id,
        "recommended_under_weights": min(result.frontier, key=lambda item: ranking_key(item, preferences, "WEIGHTED")).id,
        "recommended_candidate": best.id,
        "recommended_plan": best_plan,
        "displayed_candidate": active_id,
        "comparison": [{"id": item.id, "slot": slot, "groups": item.groups, "score": item.score(preferences),
                        "score_interval": {"lower": intervals[item.id].lower, "upper": intervals[item.id].upper,
                                           "unresolved_edges": intervals[item.id].unresolved_edges,
                                           "conditional_edges": intervals[item.id].conditional_edges},
                        "pareto": None if large else item.id in frontier_ids,
                        "pareto_in_found_pool": item.id in frontier_ids if large else None,
                        "pareto_scope": "FOUND_POOL" if large else "GLOBAL", "dominated_by": dominated_by.get(item.id),
                        "cost_delta_vs_a": deltas[item.id],
                        "costs": dict(zip(AXES, item.vector, strict=True)), "cost_drivers": details[item.id],
                        "assignment": plans[item.id]["assignment"], "quantum_profiles": plans[item.id]["groups"],
                        "interaction_routing": plans[item.id]["interactions"],
                        "quality_profiles": plans[item.id]["quality_profiles"],
                        "boundary_profiles": plans[item.id]["boundary_profiles"]}
                       for slot, item in zip(slots, candidates, strict=True)],
    }
    if replay:
        case_id, mode = replay
        case = oracle_ticket_cases()[case_id]
        comparison["replay"] = {"case_id": case_id, "mode": mode,
                                "input_edited": architecture != replay_architecture(case, mode)}
        if mode == "saved_model":
            comparison["replay"]["response_sha256"] = case["saved_model"]["response_sha256"]
    with details_panel.expander("Các phương án không trội trong tập đã tìm" if large else "Danh sách phương án Pareto"):
        st.dataframe(
            [{"Phương án": option(item), "Điểm": item.score(preferences),
              "Nhóm": " | ".join(", ".join(group) for group in item.groups),
              **dict(zip(AXES, item.vector, strict=True))}
             for item in result.ranked],
            hide_index=True, width="stretch",
        )
    with evidence_panel:
        show_traceability(architecture, plans[active_id], names)
        if replay:
            st.caption("Kết quả mô phỏng. Phiên này không ghi vào lịch sử Human Review.")
        else:
            show_review(comparison, candidates)
        st.download_button(
            "Tải bản so sánh JSON", json.dumps(comparison, ensure_ascii=False, indent=2),
            file_name="quantum-comparison.json", mime="application/json",
        )
    return list(plans.values()), False, active_id


example = ticket_example()
st.session_state.setdefault("architecture", example)
st.session_state.setdefault("editor_version", 0)
st.session_state.setdefault("studio_layout", {})
st.session_state.setdefault("studio_analyzed", False)
st.session_state.setdefault("studio_pending", False)
st.session_state.setdefault("studio_weights", Preferences())
st.session_state.setdefault("studio_ranking", "SYNC_FIRST")
st.session_state.setdefault("studio_conservative", False)
if type(st.session_state.architecture) is not Architecture:
    st.session_state.architecture = Architecture.model_validate(st.session_state.architecture.model_dump(mode="json"))
architecture = st.session_state.architecture
replay = st.session_state.get("studio_replay")

header = st.empty()
show_oracle_cases(architecture, replay)
workspace = st.container(key="studio_workspace", border=st.session_state.studio_analyzed and not st.session_state.studio_pending)
comparison_panel = workspace.container()
board = workspace.container()
details_panel = workspace.container()
samples_panel = st.container()
nfr_panel = st.container()
evidence_panel = st.container()
plans, no_solution, active_plan = [], False, None
if st.session_state.studio_analyzed and not st.session_state.studio_pending:
    with comparison_panel:
        plans, no_solution, active_plan = show_comparison(architecture, details_panel, evidence_panel, replay)
    with nfr_panel:
        show_nfr_review(architecture, sorted(plans, key=lambda plan: plan['id'] != active_plan), replay)
elif st.session_state.studio_pending:
    comparison_panel.info("Bấm Phân tích sơ đồ để cập nhật trade-off và truy vết.")

if replay is None:
    with samples_panel:
        show_live_review(architecture)
        show_session_history()
        show_duplicate_review(architecture)
        show_interaction_review(architecture)
        show_rule_policy_review(architecture)
        show_evidence_review(architecture)
        show_scenario_review(architecture)
        show_boundary_review(architecture)
        st.html('<span id="studio-ollama" class="qs-anchor"></span>')
        show_requirement_cases(architecture)

header.html(diagram_header(
    architecture, example=architecture == example, analyzed=st.session_state.studio_analyzed,
    pending=st.session_state.studio_pending, feasible=bool(plans), replay=replay[0] if replay else None,
    review_required=bool(evidence_blockers(architecture)),
))

with board:
    st.html('<span id="studio-diagrams" class="qs-anchor"></span>')
    if architecture == example:
        st.caption("Mẫu Ticket Support · Nhãn Sync/Async, đặc tính và chính sách dữ liệu là giả định minh họa có thể chỉnh.")
    reset_model = replay_architecture(oracle_ticket_cases()[replay[0]], replay[1]) if replay else example
    event = render_board(
        model=architecture.model_dump(mode="json"), example=reset_model.model_dump(mode="json"),
        layout=st.session_state.studio_layout, revision=st.session_state.get("studio_canvas_commit", 0),
        plans=plans, no_solution=no_solution, active_plan=active_plan,
        error=st.session_state.get("studio_canvas_error", ""), pending=st.session_state.studio_pending,
        review_required=bool(evidence_blockers(architecture)),
    )
if isinstance(event, dict) and event.get("token") != st.session_state.get("studio_submission"):
    st.session_state.studio_submission = event.get("token")
    if event.get("action") == "layout":
        st.session_state.studio_layout = read_layout(architecture, event.get("layout"))
    if event.get("action") == "dirty" and not st.session_state.studio_pending:
        st.session_state.studio_pending = True
        st.session_state.studio_canvas_error = ""
        st.rerun()
    if event.get("action") == "analyze":
        try:
            submitted = invalidate_changed_sources(architecture, Architecture.model_validate(event.get("model")))
            enforce_protected_rules(architecture, submitted)
        except (ValidationError, ValueError) as exc:
            if not isinstance(exc, ValidationError):
                st.session_state.studio_canvas_error = str(exc)
                st.session_state.studio_blocked_edit = event.get("model")
                st.session_state.studio_pending = True
                st.rerun()
            issue = exc.errors(include_url=False)[0]
            field = " / ".join(str(part + 1) if isinstance(part, int) else part for part in issue["loc"])
            st.session_state.studio_canvas_error = f"{field} · {issue['msg']}" if field else issue["msg"]
            st.session_state.studio_pending = True
        else:
            submitted_layout = read_layout(submitted, event.get("layout"))
            if submitted != architecture and replay is None and not commit_revision(submitted, {
                "action": "INPUT_CHANGED", "actor": "LOCAL_INTERACTIVE_REVIEWER",
                "before": architecture.model_dump(mode="json"), "after": submitted.model_dump(mode="json"),
            }, layout=submitted_layout):
                st.stop()
            if submitted != architecture:
                st.session_state.editor_version += 1
            st.session_state.architecture = submitted
            st.session_state.studio_layout = submitted_layout
            st.session_state.studio_analyzed = True
            st.session_state.studio_pending = False
            st.session_state.studio_canvas_error = ""
            st.session_state.studio_canvas_commit = st.session_state.get("studio_canvas_commit", 0) + 1
        st.rerun()
