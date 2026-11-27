"""Model proposal review and restorable revisions in the existing Streamlit Studio."""

from __future__ import annotations

import json

import streamlit as st

from . import ollama
from .quantum_tradeoff import Architecture, Preferences, hard_constraints, merge_quality_requirement
from .studio_conflicts import enforce_protected_rules, review_rule_policy
from .studio_evidence import binding_issues, bound_items, rebind_evidence
from .studio_extraction import author_clause, decide_proposal, extract_proposals, proposal_is_current
from .studio_quality import QualityCharacteristic
from .studio_sessions import checkpoints, load_checkpoint, save_checkpoint
from .studio_uncertainty import review_interaction_cases
from .studio_semantic_ui import edit_frame, show_frame, show_source_coverage
from .studio_semantics import SCHEMA


def commit_revision(architecture: Architecture, event: dict, *, proposals: list[dict] | None = None,
                    layout: dict | None = None) -> bool:
    session = st.session_state
    items = session.get("studio_live_proposals", []) if proposals is None else proposals
    try:
        if event.get("action") != "HARD_RULE_POLICY_REVIEW":
            enforce_protected_rules(session.architecture, architecture)
        view = {"preferences": session.studio_weights.model_dump(mode="json"), "ranking": session.studio_ranking,
                "conservative": session.get("studio_conservative", False),
                "time_limit_seconds": session.get("studio_search_seconds", 8),
                "layout": session.studio_layout if layout is None else layout}
        identifier = save_checkpoint(architecture, event=event, parent=session.get("studio_checkpoint"), proposals=items, view=view)
    except (OSError, ValueError) as exc:
        st.error(f"Chưa lưu được phiên. {exc}")
        return False
    session.studio_checkpoint = identifier
    session.studio_live_proposals = items
    return True


def show_live_review(architecture: Architecture) -> None:
    st.html('<span id="studio-live" class="qs-anchor"></span>')
    with st.expander("Phân tích yêu cầu hiện tại bằng Ollama"):
        if st.session_state.studio_pending:
            st.info("Bấm Phân tích sơ đồ để lưu chỉnh sửa trước khi gọi model hoặc review.")
            return
        task = st.radio("Nội dung cần phân tích", ["QUALITY", "INTERACTION", "SEPARATION"], horizontal=True,
                        format_func=lambda item: {"QUALITY": "ISO và component", "INTERACTION": "Tương tác SYNC/ASYNC",
                                                   "SEPARATION": "Quy tắc bắt buộc tách"}[item])
        available = [item.id for item in architecture.requirements if task != "QUALITY" or item.kind == "NFR"]
        selected = st.multiselect("Nguồn gửi Ollama", available, default=available[:4], max_selections=8)
        model = st.text_input("Model Ollama", value="qwen3:4b", max_chars=100)
        if st.button("Phân tích bằng Ollama", disabled=not selected or not model.strip()):
            try:
                with st.spinner("Ollama đang đọc yêu cầu…"):
                    run = extract_proposals(architecture, selected, task, model.strip())
                existing = st.session_state.get("studio_live_proposals", [])
                if commit_revision(architecture, {"action": "LLM_PROPOSED", "run_id": run["id"],
                                                   "model": run["model"], "model_digest": run["model_digest"],
                                                   "count": len(run["proposals"])}, proposals=[*existing, *run["proposals"]]):
                    st.session_state.studio_last_inference = run
                    st.rerun()
            except (ollama.OllamaError, ValueError, OSError) as exc:
                st.error(str(exc))
        run = st.session_state.get("studio_last_inference")
        if run:
            st.caption(f"{run['model']} · {run['ollama_version']} · {len(run['proposals'])} đề xuất · "
                       f"{run['tokens']} token · {run['recorded_at']}")
        items = st.session_state.get("studio_live_proposals", [])
        with st.expander("Bổ sung mệnh đề reviewer thấy model bỏ sót"):
            st.caption("Mệnh đề bổ sung ghi HUMAN_DECISION, không được tính là model đã trích xuất. Bản nháp giữ nguyên optimizer.")
            if available:
                source_id = st.selectbox("Nguồn bổ sung mệnh đề", available)
                if st.button("Tạo mệnh đề bổ sung để review"):
                    draft = author_clause(architecture, source_id, task)
                    if commit_revision(architecture, {"action": "REVIEWER_CLAUSE_DRAFTED", "actor": "LOCAL_INTERACTIVE_REVIEWER",
                                                       "source_id": source_id, "provenance": "HUMAN_DECISION", "proposal_id": draft["id"]},
                                       proposals=[*items, draft]):
                        st.rerun()
        st.caption("Đề xuất chờ review giữ nguyên đầu vào bộ giải. Đoạn trích khớp cần được kiểm tra cả ý nghĩa và phạm vi.")
        show_source_coverage(architecture, run, items)
        for item in items:
            current = proposal_is_current(architecture, item)
            state = item["status"] if current else "STALE"
            applied = item.get("applied") or item["payload"]
            label = applied.get("characteristic") or applied.get("mode") or applied.get("disposition") or "Quy tắc tách"
            with st.expander(f"{item['source_id']} · {label} · {state}"):
                names = {component.id: component.name for component in architecture.components}
                source = next((r for r in architecture.requirements if r.id == item["source_id"]), None)
                if source:
                    st.write(source.text)
                st.write("Đề xuất gốc từ model" if item.get("provenance", "LLM_PROPOSAL") == "LLM_PROPOSAL" else "Mệnh đề do reviewer bổ sung")
                st.write(item["payload"].get("quote", ""))
                if item.get("issues"):
                    st.warning(" ".join(item["issues"]))
                if item.get("applied"):
                    st.write("Căn cứ đã áp dụng sau review")
                    st.write(item["applied"].get("quote", ""))
                show_frame(applied, names)
                if not current:
                    st.warning("Nguồn hoặc danh mục đã đổi. Phân tích lại để có đề xuất theo phiên bản hiện tại.")
                    continue
                if state not in {"REVIEW_REQUIRED", "DEFERRED"}:
                    continue
                with st.form(f"review_{item['id']}"):
                    payload = dict(item["payload"])
                    names = {component.id: component.name for component in architecture.components}
                    if payload["kind"] == "QUALITY":
                        labels = [None, *list(QualityCharacteristic)]
                        default = next((n for n, label in enumerate(labels) if label == payload.get("characteristic")), 0)
                        payload["characteristic"] = st.selectbox("Characteristic", labels, index=default)
                        payload["component_ids"] = st.multiselect("Component chịu trách nhiệm", list(names),
                                                                  default=[c for c in payload.get("component_ids", []) if c in names],
                                                                  format_func=names.__getitem__)
                    elif payload["kind"] == "INTERACTION":
                        keys = [None, *names]
                        for field, name in [("source", "Component gọi"), ("target", "Component nhận")]:
                            payload[field] = st.selectbox(name, keys, index=keys.index(payload[field]) if payload.get(field) in keys else 0,
                                                          format_func=lambda value: names.get(value, "Chưa xác định"))
                        modes = ["SYNC", "ASYNC", "UNKNOWN"]
                        payload["mode"] = st.selectbox("Mode sau review", modes,
                                                     index=modes.index(payload.get("mode")) if payload.get("mode") in modes else 2)
                        payload["local_transaction"] = st.checkbox("Cùng giao dịch cục bộ", value=bool(payload.get("local_transaction")))
                    else:
                        keys = [None, *names]
                        for field, name in [("left", "Component thứ nhất"), ("right", "Component cần tách")]:
                            payload[field] = st.selectbox(name, keys, index=keys.index(payload[field]) if payload.get(field) in keys else 0,
                                                          format_func=lambda value: names.get(value, "Chưa xác định"))
                    payload["quote"] = st.text_area("Đoạn căn cứ nguyên văn", value=payload.get("quote", ""), max_chars=600)
                    structured = item.get("semantic_schema") == SCHEMA or "frame" in payload
                    if structured:
                        edit_frame(payload, names)
                        st.caption("Ngoài phạm vi/cần làm rõ phải để nhãn, scope và endpoints rỗng, effect NONE. "
                                   "Các mệnh đề cùng ISO trong một NFR hợp nhất scope; mục tiêu độc lập cần tách NFR hoặc scenario riêng.")
                    semantic_confirmed = st.checkbox("Tôi đã review chủ thể, điều kiện, phủ định và tác động của mệnh đề" if structured else
                                                       "Tôi đã review thủ công đề xuất cũ chưa có cấu trúc mệnh đề")
                    provenance = st.selectbox("Nguồn quyết định đề xuất", ["HUMAN_DECISION", "PREPARED_FIXTURE"])
                    actor = st.text_input("Người review", value="LOCAL_INTERACTIVE_REVIEWER", max_chars=100)
                    rationale = st.text_area("Lý do quyết định", max_chars=1000)
                    action = st.selectbox("Quyết định", ["APPROVE", "CORRECT", "REJECT", "DEFER"],
                                          format_func=lambda value: {"APPROVE": "Đồng ý đề xuất gốc", "CORRECT": "Áp dụng phần đã sửa",
                                                                     "REJECT": "Từ chối", "DEFER": "Giữ lại để làm rõ"}[value])
                    submitted = st.form_submit_button("Lưu quyết định và tính lại")
                if submitted:
                    try:
                        if action == "APPROVE" and payload != item["payload"]:
                            raise ValueError("Bạn đã chỉnh đề xuất. Chọn Áp dụng phần đã sửa để lưu các giá trị đang chọn.")
                        if action in {"APPROVE", "CORRECT"} and not semantic_confirmed:
                            raise ValueError("Xác nhận review nghĩa và phạm vi trước khi áp dụng đề xuất.")
                        changed, decision = decide_proposal(architecture, item, action=action, actor=actor,
                                                            rationale=rationale, corrected=payload, semantic_confirmed=semantic_confirmed,
                                                            provenance=provenance)
                        updated = [{**row, "status": {"APPROVE": "APPROVED", "CORRECT": "CORRECTED", "REJECT": "REJECTED",
                                                       "DEFER": "DEFERRED"}[action], "applied": decision["applied"]}
                                   if row["id"] == item["id"] else row for row in items]
                        if commit_revision(changed, decision, proposals=updated):
                            st.session_state.architecture = changed
                            st.session_state.editor_version += 1
                            st.session_state.studio_analyzed = True
                            st.session_state.studio_canvas_commit = st.session_state.get("studio_canvas_commit", 0) + 1
                            st.rerun()
                    except ValueError as exc:
                        st.error(str(exc))


def restore_session() -> None:
    try:
        loaded = load_checkpoint(st.session_state.studio_restore_selector)
        enforce_protected_rules(st.session_state.architecture, Architecture.model_validate(loaded["architecture"]))
        if not commit_revision(st.session_state.architecture, {"action": "BEFORE_RESTORE"}):
            return
        saved_view = loaded.get("view", {})
        preferences = Preferences.model_validate(saved_view.get("preferences", {}))
        st.session_state.architecture = Architecture.model_validate(loaded["architecture"])
        st.session_state.studio_live_proposals = loaded["proposals"]
        st.session_state.studio_checkpoint = loaded["id"]
        st.session_state.studio_weights = preferences
        st.session_state.studio_ranking = saved_view.get("ranking", "SYNC_FIRST")
        st.session_state.studio_conservative = saved_view.get("conservative", False)
        limit = saved_view.get("time_limit_seconds", 8)
        st.session_state.studio_search_seconds = limit if type(limit) is int and 1 <= limit <= 30 else 8
        for field, value in preferences.model_dump().items():
            st.session_state[f"studio_weight_{field}"] = value
        st.session_state.studio_layout = saved_view.get("layout", {})
        st.session_state.studio_last_inference = None
        st.session_state.studio_analyzed = True
        st.session_state.editor_version += 1
        st.session_state.studio_canvas_commit = st.session_state.get("studio_canvas_commit", 0) + 1
    except (ValueError, OSError) as exc:
        st.session_state.studio_restore_error = str(exc)


def show_session_history() -> None:
    with st.expander("Lịch sử và tải lại phiên Studio"):
        if st.session_state.studio_pending:
            st.caption("Lưu chỉnh sửa bằng Phân tích sơ đồ trước khi tải phiên.")
            return
        try:
            saved = checkpoints()
            if not saved:
                st.caption("Phiên được lưu khi phân tích thay đổi hoặc đưa ra quyết định review.")
                return
            rows = {item["id"]: item for item in saved}
            selected = st.selectbox("Phiên đã lưu", list(rows),
                                    format_func=lambda key: f"{rows[key]['recorded_at']} · {rows[key]['action']} · {key[-8:]}",
                                    key="studio_restore_selector")
            loaded = load_checkpoint(selected)
            st.caption(f"Nguồn quyết định · {loaded['event'].get('actor', loaded['event'].get('model', 'LOCAL_INPUT'))}")
            if loaded["event"].get("rationale"):
                st.write(loaded["event"]["rationale"])
            st.download_button("Tải hồ sơ phiên", json.dumps(loaded, ensure_ascii=False, indent=2),
                               file_name=f"{selected}.json", mime="application/json")
            st.button("Tải lại phiên đã chọn", on_click=restore_session)
            if error := st.session_state.pop("studio_restore_error", None):
                st.error(error)
        except (ValueError, OSError) as exc:
            st.error(f"Chưa đọc được lịch sử phiên. {exc}")


def show_duplicate_review(architecture: Architecture) -> None:
    sources = {item.id: item for item in architecture.requirements if item.kind == "NFR"}
    if len(sources) < 2:
        return
    with st.expander("Review yêu cầu cùng mục tiêu"):
        if st.session_state.studio_pending:
            st.caption("Bấm Phân tích sơ đồ để lưu nguồn trước khi hợp nhất.")
            return
        alias_id = st.selectbox("Nguồn cần đối chiếu", list(sources))
        alias = sources[alias_id]
        st.write(alias.text)
        choices = [None, *[item.id for item in sources.values() if item.id != alias_id and not item.duplicate_of and item.quality_allocations]]
        saved = alias.duplicate_of if alias.duplicate_of in choices else None
        target_id = st.selectbox("Mục tiêu chất lượng gốc", choices, index=choices.index(saved),
                                 format_func=lambda value: value or "Giữ thành mục tiêu riêng", key=f"merge_{alias_id}")
        if target_id:
            target = sources[target_id]
            st.write(target.text)
            st.caption("Kiểm tra điều kiện tải, ngưỡng, actor và phạm vi component. Sau hợp nhất, ánh xạ của bản gốc "
                       "quyết định chi phí, cả hai mã nguồn vẫn truy vết về cùng mục tiêu.")
        actor = st.text_input("Người xác nhận mục tiêu", value="LOCAL_INTERACTIVE_REVIEWER", max_chars=100)
        rationale = st.text_area("Căn cứ hợp nhất hoặc tách mục tiêu", max_chars=1000)
        if st.button("Lưu quan hệ mục tiêu", disabled=target_id == alias.duplicate_of):
            try:
                if not actor.strip() or not rationale.strip():
                    raise ValueError("Điền người review và lý do quyết định.")
                changed = merge_quality_requirement(architecture, alias_id, target_id)
                if commit_revision(changed, {"action": "QUALITY_TARGET_MERGE" if target_id else "QUALITY_TARGET_UNLINK",
                                             "actor": actor, "source_id": alias_id, "target_id": target_id, "rationale": rationale,
                                             "before": architecture.model_dump(mode="json"), "after": changed.model_dump(mode="json")}):
                    st.session_state.architecture = changed
                    st.session_state.studio_analyzed = True
                    st.session_state.editor_version += 1
                    st.session_state.studio_canvas_commit = st.session_state.get("studio_canvas_commit", 0) + 1
                    st.rerun()
            except ValueError as exc:
                st.error(str(exc))


def show_interaction_review(architecture: Architecture) -> None:
    sources = {item.id: item for item in architecture.requirements}
    eligible = [edge for edge in architecture.interactions if not edge.local_transaction]
    if not sources or not eligible:
        return
    with st.expander("Review tương tác theo điều kiện"):
        if st.session_state.studio_pending:
            st.caption("Lưu sơ đồ trước khi khai báo điều kiện.")
            return
        edges = {f"{edge.source} → {edge.target}": edge for edge in eligible}
        edge = edges[st.selectbox("Cạnh cần đối chiếu điều kiện", list(edges))]
        st.caption("Khai báo các chế độ vận hành, ví dụ bình thường và mất kết nối. Reviewer xác định tập điều kiện "
                   "được bao phủ. Khoảng chi phí xét mọi mode đã khai báo, chưa có xác suất xảy ra.")
        prefix = f"conditions_{edge.source}_{edge.target}_{st.session_state.editor_version}"
        count = st.selectbox("Số điều kiện", [2, 3, 4], index=max(0, len(edge.cases) - 2), key=f"{prefix}_count")
        cases = []
        for index in range(count):
            saved = edge.cases[index] if index < len(edge.cases) else None
            with st.container(border=True):
                st.markdown(f"**Điều kiện {index + 1}**")
                condition = st.text_input(f"Tên điều kiện {index + 1}", value=saved.condition if saved else "", key=f"{prefix}_{index}_name", max_chars=100)
                source_id = st.selectbox(f"Nguồn điều kiện {index + 1}", list(sources),
                                         index=list(sources).index(saved.source_id) if saved and saved.source_id in sources else 0,
                                         key=f"{prefix}_{index}_source")
                st.write(sources[source_id].text)
                mode = st.selectbox(f"Mode điều kiện {index + 1}", ["SYNC", "ASYNC"],
                                    index=int(saved is not None and saved.mode == "ASYNC"), key=f"{prefix}_{index}_mode")
                quote = st.text_area(f"Căn cứ điều kiện {index + 1}", value=saved.source_quote if saved else "",
                                     max_chars=600, key=f"{prefix}_{index}_quote")
                cases.append({"condition": condition, "mode": mode, "source_id": source_id, "source_quote": quote})
        actor = st.text_input("Người review điều kiện", value="LOCAL_INTERACTIVE_REVIEWER", max_chars=100)
        rationale = st.text_area("Căn cứ và phạm vi bao phủ điều kiện", max_chars=1000)
        if st.button("Lưu các điều kiện và tính lại"):
            try:
                changed, event = review_interaction_cases(architecture, edge.source, edge.target, cases, actor=actor, rationale=rationale)
                if commit_revision(changed, event):
                    st.session_state.architecture = changed
                    st.session_state.studio_analyzed = True
                    st.session_state.editor_version += 1
                    st.session_state.studio_canvas_commit = st.session_state.get("studio_canvas_commit", 0) + 1
                    st.rerun()
            except ValueError as exc:
                st.error(str(exc))


def show_rule_policy_review(architecture: Architecture) -> None:
    rules = hard_constraints(architecture)
    if not rules:
        return
    with st.expander("Review chính sách ràng buộc"):
        if st.session_state.studio_pending:
            st.caption("Lưu sơ đồ trước khi review chính sách. Chỉnh sửa làm mất quy tắc được bảo vệ sẽ bị chặn.")
            if blocked := st.session_state.get("studio_blocked_edit"):
                st.download_button("Tải chỉnh sửa đang bị chặn", json.dumps(blocked, ensure_ascii=False, indent=2),
                                   file_name="studio-blocked-edit.json", mime="application/json")
                if st.button("Lưu bản nháp bị chặn và quay lại review chính sách"):
                    if commit_revision(architecture, {"action": "PROTECTED_EDIT_RETAINED", "actor": "LOCAL_INPUT",
                                                       "attempted_input": blocked}):
                        st.session_state.studio_pending = False
                        st.session_state.studio_canvas_error = ""
                        st.session_state.pop("studio_blocked_edit", None)
                        st.session_state.studio_canvas_commit = st.session_state.get("studio_canvas_commit", 0) + 1
                        st.rerun()
            return
        index = st.selectbox("Quy tắc cần review", range(len(rules)),
                             format_func=lambda value: f"{rules[value].kind} · {' / '.join(rules[value].components)}")
        rule = rules[index]
        st.write(rule.basis)
        st.caption("Quy tắc được bảo vệ không xuất hiện trong tập sửa được phép. Chi phí sửa là mức ưu tiên "
                   "do reviewer đặt, tách riêng với điểm chi phí kiến trúc.")
        prefix = f"policy_{index}_{st.session_state.editor_version}"
        protected = st.checkbox("Bảo vệ quy tắc này", value=rule.protected, key=f"{prefix}_protected")
        cost = st.number_input("Chi phí sửa quy tắc", min_value=1, max_value=1000, value=rule.change_cost, key=f"{prefix}_cost")
        actor = st.text_input("Người review chính sách", value="LOCAL_INTERACTIVE_REVIEWER", max_chars=100)
        rationale = st.text_area("Căn cứ bảo vệ hoặc cho phép sửa", max_chars=1000)
        if st.button("Lưu chính sách ràng buộc", disabled=(protected, cost) == (rule.protected, rule.change_cost)):
            try:
                changed, event = review_rule_policy(architecture, rule, protected=protected, change_cost=cost,
                                                     actor=actor, rationale=rationale)
                if commit_revision(changed, event):
                    st.session_state.architecture = changed
                    st.session_state.editor_version += 1
                    st.session_state.studio_canvas_commit = st.session_state.get("studio_canvas_commit", 0) + 1
                    st.rerun()
            except ValueError as exc:
                st.error(str(exc))


def show_evidence_review(architecture: Architecture) -> None:
    items = list(bound_items(architecture))
    if not items:
        return
    st.html('<span id="studio-source-review" class="qs-anchor"></span>')
    with st.expander("Căn cứ nguồn của tương tác và quy tắc"):
        if st.session_state.studio_pending:
            st.caption("Lưu sơ đồ trước khi xác nhận lại căn cứ.")
            return
        names = {component.id: component.name for component in architecture.components}

        def option(value):
            collection, _, item = items[value]
            endpoints = (item.source, item.target) if collection == "interactions" else (item.left, item.right)
            return ("Tương tác" if collection == "interactions" else "Bắt buộc tách") + " · " + " → ".join(
                names[endpoint] for endpoint in endpoints) + f" · {item.evidence.source_id}"

        selected = st.selectbox("Quan hệ có căn cứ đã review", range(len(items)), format_func=option)
        collection, index, item = items[selected]
        evidence = item.evidence
        issues = binding_issues(architecture, evidence, collection=collection, item=item)
        st.write(f"Nguồn {evidence.source_id}")
        st.write(evidence.source_quote)
        st.caption(f"Đoạn nguồn · {evidence.citation_provenance} · quyết định {evidence.review_provenance} · {evidence.review_actor}")
        with st.expander("Dấu vết lần đề xuất"):
            st.write(f"Proposal · {evidence.proposal_id}")
            st.write(f"Run · {evidence.run_id}")
        if issues:
            for issue in issues:
                st.warning(issue)
        else:
            st.caption("Căn cứ khớp revision đã review. Ý nghĩa vẫn thuộc trách nhiệm reviewer.")
        sources = {source.id: source for source in architecture.requirements}
        if not sources:
            st.info("Thêm requirement hiện hành để review lại căn cứ.")
            return
        prefix = f"source_rebind_{collection}_{index}_{st.session_state.editor_version}"
        source_id = st.selectbox("Requirement làm căn cứ mới", list(sources),
                                 index=list(sources).index(evidence.source_id) if evidence.source_id in sources else 0,
                                 key=f"{prefix}_source")
        st.write(sources[source_id].text)
        quote = st.text_area("Đoạn nguồn xác nhận lại", max_chars=600,
                             value=evidence.source_quote if evidence.source_quote in sources[source_id].text else "",
                             key=f"{prefix}_{source_id}_quote")
        actor = st.text_input("Người review lại căn cứ", value="LOCAL_INTERACTIVE_REVIEWER", max_chars=100)
        rationale = st.text_area("Lý do giữ quan hệ theo nguồn hiện hành", max_chars=1000)
        st.caption("Xác nhận lại chỉ cập nhật căn cứ. Mode và các ràng buộc cứng giữ nguyên. "
                   "Muốn đổi quan hệ, sửa sơ đồ hoặc review proposal mới, rồi kiểm lại policy bảo vệ.")
        if st.button("Xác nhận lại căn cứ nguồn"):
            try:
                changed, event = rebind_evidence(architecture, collection, index, source_id=source_id, quote=quote,
                                                  actor=actor, rationale=rationale)
                if commit_revision(changed, event):
                    st.session_state.architecture = changed
                    st.session_state.editor_version += 1
                    st.session_state.studio_canvas_commit = st.session_state.get("studio_canvas_commit", 0) + 1
                    st.rerun()
            except ValueError as exc:
                st.error(str(exc))
