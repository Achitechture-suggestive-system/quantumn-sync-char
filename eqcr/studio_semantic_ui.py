"""Readable clause roles, reviewer corrections and uncovered source text in the existing review panel."""

import streamlit as st
from pydantic import ValidationError

from .studio_semantics import DISPOSITIONS, EFFECTS, HUMAN_FIELDS, KINDS, PARTS, ClauseFrame, uncovered_text


PART_LABELS = {"subject": "Chủ thể chịu trách nhiệm", "action": "Hành vi cần thực hiện", "object": "Đối tượng của hành vi",
               "condition": "Điều kiện và tác nhân bối cảnh", "modality": "Từ chỉ nghĩa vụ hoặc phủ định"}
KIND_LABELS = {"OBLIGATION": "Nghĩa vụ phải thực hiện", "PROHIBITION": "Điều cấm phải ngăn chặn", "PERMISSION": "Điều được phép",
               "EXEMPTION": "Điều không bắt buộc", "DESCRIPTION": "Mô tả, chưa xác lập nghĩa vụ", "UNKNOWN": "Chưa xác định"}
DISPOSITION_LABELS = {"PROPOSED": "Đề xuất tác động kiến trúc", "OUT_OF_SCOPE": "Ngoài phạm vi tác vụ này", "AMBIGUOUS": "Cần làm rõ"}
EFFECT_LABELS = {"QUALITY_OBLIGATION": "Target chất lượng", "WAIT_COMPLETION": "Bên gọi chờ hoàn tất · SYNC",
                 "RETURN_BEFORE_COMPLETION": "Bên gọi trả trước hoàn tất · ASYNC", "WORKFLOW_ONLY": "Chỉ biết thứ tự · UNKNOWN",
                 "LOCAL_ATOMIC_TRANSACTION": "Bắt buộc giao dịch cục bộ", "REQUIRE_SEPARATION": "Bắt buộc khác Quantum", "NONE": "Chưa tạo tác động"}
ROLE_LABELS = {"subject_ids": "Component thực hiện phản hồi", "object_ids": "Component nhận tương tác", "context_ids": "Component chỉ làm bối cảnh"}


def show_frame(payload, names):
    frame = payload.get("frame")
    if not isinstance(frame, dict):
        st.caption("LEGACY_UNSTRUCTURED · Đề xuất cũ chưa có cấu trúc mệnh đề, cần review thủ công đầy đủ.")
        return
    try:
        ClauseFrame.model_validate(frame)
    except ValidationError:
        st.warning("Frame gốc chưa hợp lệ. Giữ nguyên phản hồi để đối chiếu và sửa rõ từng trường, hoặc từ chối.")
        return
    human = frame.get("human_fields", [])
    st.caption(f"{DISPOSITION_LABELS.get(payload.get('disposition'), 'Chưa có trạng thái mệnh đề')} · "
               f"{KIND_LABELS.get(frame.get('statement_kind'), 'Chưa rõ loại nghĩa')} · "
               f"{EFFECT_LABELS.get(frame.get('effect'), 'Chưa rõ tác động')}")
    st.dataframe([{"Phần mệnh đề": label, "Nội dung": frame.get(part) or "UNKNOWN",
                   "Căn cứ": "HUMAN_DECISION" if part in human else "Đoạn trích cần kiểm nghĩa" if frame.get(part) else "UNKNOWN"}
                  for part, label in PART_LABELS.items()], hide_index=True, width="stretch")
    for key, label in ROLE_LABELS.items():
        values = frame.get(key) if isinstance(frame.get(key), list) else []
        st.write(f"{label} · {', '.join(str(names.get(item, item)) for item in values if isinstance(item, str)) or 'UNKNOWN'}")


def show_confirmed_clauses(allocation, names, plans):
    if not allocation.semantic_reviews:
        return
    st.markdown("**Mệnh đề đã dùng cho ánh xạ này**")
    for record in allocation.semantic_reviews:
        owners = record.claim.get("component_ids", [])
        rows = [{"Component chịu trách nhiệm": names.get(owner, owner),
                 **{plan["label"]: plan["assignment"].get(owner, "Chưa phân nhóm") for plan in plans}} for owner in owners]
        st.write(record.source_ref.quote)
        if rows:
            st.dataframe(rows, hide_index=True, width="stretch")
        st.caption(f"{KIND_LABELS[record.frame.statement_kind]} · gốc {record.proposal_provenance} → claim {record.claim_provenance} "
                   f"→ review {record.provenance} · {record.actor} · {record.proposal_id}")
        if record.frame.human_fields:
            st.caption("Phần bổ sung ngoài nguồn: " + ", ".join(record.frame.human_fields))


def edit_frame(payload, names):
    original = payload.get("frame") if isinstance(payload.get("frame"), dict) else {}
    frame = {}
    disposition = payload.get("disposition", "AMBIGUOUS")
    payload["disposition"] = st.selectbox("Kết luận phạm vi mệnh đề", list(DISPOSITIONS), index=list(DISPOSITIONS).index(disposition) if disposition in DISPOSITIONS else 2,
                                         format_func=DISPOSITION_LABELS.__getitem__)
    for part in PARTS:
        frame[part] = st.text_input(PART_LABELS[part], value=original.get(part) if isinstance(original.get(part), str) else "", max_chars=600) or None
    kind = original.get("statement_kind", "UNKNOWN")
    frame["statement_kind"] = st.selectbox("Loại nghĩa của mệnh đề", list(KINDS), index=list(KINDS).index(kind) if kind in KINDS else len(KINDS) - 1,
                                            format_func=KIND_LABELS.__getitem__)
    for key, label in ROLE_LABELS.items():
        values = original.get(key) if isinstance(original.get(key), list) else []
        frame[key] = st.multiselect(label, list(names), default=[item for item in values if isinstance(item, str) and item in names], format_func=names.__getitem__)
    effect = original.get("effect", "NONE")
    frame["effect"] = st.selectbox("Tác động kiến trúc từ mệnh đề", list(EFFECTS), index=list(EFFECTS).index(effect) if effect in EFFECTS else len(EFFECTS) - 1,
                                   format_func=EFFECT_LABELS.__getitem__)
    field_labels = {**PART_LABELS, **ROLE_LABELS, "statement_kind": "Loại nghĩa", "effect": "Tác động kiến trúc"}
    initial_human = original.get("human_fields") if isinstance(original.get("human_fields"), list) else []
    human = st.multiselect("Phần bổ sung hoặc diễn giải ngoài nguồn của reviewer", list(HUMAN_FIELDS),
                            default=[item for item in initial_human if item in HUMAN_FIELDS], format_func=field_labels.__getitem__)
    if human or "human_fields" in original:
        frame["human_fields"] = human
    st.caption("Nội dung ngoài đoạn trích phải đánh dấu ở trên, ghi rationale và chọn Áp dụng phần đã sửa. "
               "ID/label và tác động vẫn là diễn giải cần review; khớp chuỗi không xác nhận ngữ nghĩa.")
    payload["frame"] = frame


def show_source_coverage(architecture, run, proposals):
    if not run:
        return
    current = [item for item in proposals if item.get("run_id") == run["id"]]
    sources = {item.id: item for item in architecture.requirements}
    with st.expander("Đối chiếu đoạn nguồn và mệnh đề của lượt phân tích"):
        st.caption("Chỉ đối chiếu vùng văn bản đã được trích. Một quote phủ cả câu vẫn có thể bỏ sót nghĩa vụ bên trong. "
                   "Đây không phải semantic recall hoặc xác nhận đủ mọi mệnh đề.")
        for identifier in run.get("source_digests", {}):
            source = sources.get(identifier)
            if source is None:
                st.write(f"{identifier} · nguồn đã bị xóa")
                continue
            count = sum(item["source_id"] == identifier for item in current)
            st.write(f"{identifier} · {count} đề xuất từ model")
            if source.input_digest() != run["source_digests"][identifier]:
                st.warning("Nguồn đã đổi; đối chiếu lượt cũ không đại diện đầu vào hiện tại.")
                continue
            remaining = uncovered_text(source, current)
            if remaining:
                st.write("Phần văn bản chưa có trong quote của lượt này")
                for fragment in remaining:
                    st.write(fragment)
            else:
                st.caption("Quote phủ văn bản nguồn; reviewer vẫn cần kiểm tra các mệnh đề và vai trò.")
