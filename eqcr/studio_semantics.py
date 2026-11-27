"""Clause structure and revision-bound decisions; structural checks are not entailment proofs."""

from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
import json
import re
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, ValidationError, field_validator

from .models import SourceRef
from .studio_quality import component_mentions


SCHEMA = "STUDIO-CLAUSE@1"
KINDS = ("OBLIGATION", "PROHIBITION", "PERMISSION", "EXEMPTION", "DESCRIPTION", "UNKNOWN")
DISPOSITIONS = ("PROPOSED", "OUT_OF_SCOPE", "AMBIGUOUS")
EFFECTS = ("QUALITY_OBLIGATION", "WAIT_COMPLETION", "RETURN_BEFORE_COMPLETION", "WORKFLOW_ONLY", "LOCAL_ATOMIC_TRANSACTION", "REQUIRE_SEPARATION", "NONE")
PARTS = ("subject", "action", "object", "condition", "modality")
HUMAN_FIELDS = (*PARTS, "subject_ids", "object_ids", "context_ids", "statement_kind", "effect")
Text = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=600)]
Digest = Annotated[str, StringConstraints(pattern=r"^[a-f0-9]{64}$")]


class ClauseFrame(BaseModel):
    model_config = ConfigDict(extra="forbid")
    subject: Text | None = None
    action: Text | None = None
    object: Text | None = None
    condition: Text | None = None
    modality: Text | None = None
    subject_ids: list[str] = Field(default_factory=list, max_length=50)
    object_ids: list[str] = Field(default_factory=list, max_length=50)
    context_ids: list[str] = Field(default_factory=list, max_length=50)
    statement_kind: Literal["OBLIGATION", "PROHIBITION", "PERMISSION", "EXEMPTION", "DESCRIPTION", "UNKNOWN"] = "UNKNOWN"
    effect: Literal["QUALITY_OBLIGATION", "WAIT_COMPLETION", "RETURN_BEFORE_COMPLETION", "WORKFLOW_ONLY", "LOCAL_ATOMIC_TRANSACTION", "REQUIRE_SEPARATION", "NONE"] = "NONE"
    human_fields: list[Literal["subject", "action", "object", "condition", "modality", "subject_ids", "object_ids", "context_ids", "statement_kind", "effect"]] = Field(default_factory=list, max_length=10)


class ClauseReview(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schema_id: Literal["STUDIO-CLAUSE@1"] = SCHEMA
    frame: ClauseFrame
    source_ref: SourceRef
    source_digest: Digest
    catalog_digest: Digest
    claim: dict
    proposal_id: Annotated[str, StringConstraints(min_length=1, max_length=200)]
    run_id: Annotated[str, StringConstraints(min_length=1, max_length=100)]
    actor: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]
    rationale: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=1000)]
    provenance: Literal["HUMAN_DECISION", "PREPARED_FIXTURE"]
    proposal_provenance: Literal["LLM_PROPOSAL", "HUMAN_DECISION", "PREPARED_FIXTURE"]
    claim_provenance: Literal["LLM_PROPOSAL", "HUMAN_DECISION", "PREPARED_FIXTURE"]
    recorded_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @field_validator("recorded_at")
    @classmethod
    def timezone_required(cls, value):
        if value.tzinfo is None:
            raise ValueError("Thời điểm quyết định cần múi giờ.")
        return value


def frame_schema(catalog: list[str]) -> dict:
    fields = {part: {"type": ["string", "null"], "maxLength": 600} for part in PARTS}
    fields.update({key: {"type": "array", "maxItems": 50, "items": {"enum": catalog}}
                   for key in ("subject_ids", "object_ids", "context_ids")})
    fields.update(statement_kind={"enum": list(KINDS)}, effect={"enum": list(EFFECTS)})
    return {"type": "object", "properties": fields, "required": list(fields), "additionalProperties": False}


def claim_fields(payload: dict) -> dict:
    keys = {"QUALITY": ("characteristic", "component_ids"), "INTERACTION": ("source", "target", "mode", "local_transaction"),
            "SEPARATION": ("left", "right")}.get(payload.get("kind"), ())
    return {"kind": payload.get("kind"), **{key: payload.get(key) for key in keys}}


def proposal_signature(source_id, payload: dict) -> str:
    return sha256(json.dumps([source_id, payload], ensure_ascii=False, sort_keys=True).encode()).hexdigest()


def clause_issues(architecture, source, payload, *, allow_human=False) -> list[str]:
    try:
        frame = ClauseFrame.model_validate(payload.get("frame"))
    except ValidationError:
        return ["Cấu trúc mệnh đề thiếu hoặc chưa hợp lệ; cần review chủ thể, hành vi, điều kiện và phạm vi phủ định."]
    issues = []
    quote = payload.get("quote") if isinstance(payload.get("quote"), str) else ""
    disposition = payload.get("disposition")
    if disposition not in DISPOSITIONS:
        issues.append("Chọn PROPOSED, OUT_OF_SCOPE hoặc AMBIGUOUS cho mệnh đề.")
    if frame.human_fields and not allow_human:
        issues.append("Model không được tự gán HUMAN_DECISION. Chọn CORRECT và review rõ phần bổ sung.")
    for part in PARTS:
        value = getattr(frame, part)
        if value is not None and (not isinstance(quote, str) or value not in quote) and part not in frame.human_fields:
            issues.append(f"Phần {part} cần nguyên văn trong đoạn căn cứ, hoặc đánh dấu là bổ sung của reviewer.")
    if frame.action and frame.action in quote:
        action_start = quote.find(frame.action)
        action_end = action_start + len(frame.action)
        boundaries = list(re.finditer(r"[.!?;](?=\s|$)|\n", quote))
        left = max([0, *(item.end() for item in boundaries if item.end() <= action_start)])
        right = min([len(quote), *(item.start() for item in boundaries if item.start() >= action_end)])
        active_clause = quote[left:right]
        for part in ("subject", "object", "modality"):
            value = getattr(frame, part)
            if value and value not in active_clause and part not in frame.human_fields:
                issues.append(f"Phần {part} đang lấy từ mệnh đề khác với action; tách hoặc review rõ quan hệ giữa các câu.")
    catalog = {item.id: item.name for item in architecture.components}
    for key in ("subject_ids", "object_ids", "context_ids"):
        values = getattr(frame, key)
        if len(values) != len(set(values)) or not set(values) <= set(catalog):
            issues.append(f"{key} có ID trùng hoặc ngoài danh mục.")
    for part, key in (("subject", "subject_ids"), ("object", "object_ids")):
        named = set(component_mentions(getattr(frame, part) or "", catalog))
        actual = set(getattr(frame, key))
        if named and named != actual and key not in frame.human_fields:
            issues.append(f"ID của {part} không khớp component được gọi tên trong chính phần đó.")
        elif actual and not named and not actual <= set(source.component_ids) and key not in frame.human_fields:
            issues.append(f"Danh tính {part} chưa được nguồn hoặc scope khai báo xác định; cần làm rõ biệt danh.")
    if isinstance(quote, str) and quote and source.text.count(quote) > 1:
        issues.append("Đoạn trích xuất hiện nhiều lần; mở rộng ngữ cảnh để xác định đúng mệnh đề.")
    if disposition != "PROPOSED":
        if payload.get("kind") == "QUALITY":
            populated = bool(payload.get("component_ids")) or payload.get("characteristic") is not None
        elif payload.get("kind") == "INTERACTION":
            populated = bool(payload.get("source") or payload.get("target") or payload.get("local_transaction") or payload.get("mode", "UNKNOWN") != "UNKNOWN")
        else:
            populated = bool(payload.get("left") or payload.get("right"))
        if populated or frame.effect != "NONE":
            issues.append("Mệnh đề OUT_OF_SCOPE/AMBIGUOUS phải giữ ánh xạ và tác động kiến trúc rỗng.")
        if disposition == "OUT_OF_SCOPE" and frame.statement_kind == "UNKNOWN":
            issues.append("Chưa biết nghĩa mệnh đề cần giữ AMBIGUOUS, không tự kết luận OUT_OF_SCOPE.")
        return issues
    if not frame.subject or not frame.action or not frame.subject_ids:
        issues.append("Mệnh đề áp dụng cần chủ thể, hành vi và component chịu trách nhiệm rõ ràng.")
    if frame.statement_kind in {"OBLIGATION", "PROHIBITION", "PERMISSION", "EXEMPTION"} and not frame.modality:
        issues.append("Cần giữ cả từ chỉ nghĩa vụ/cho phép/phủ định trong phần modality.")
    action_start = quote.find(frame.action) if isinstance(quote, str) and frame.action else -1
    context = re.split(r"[.!?;]\s+|\n", quote[:action_start + len(frame.action)] if action_start >= 0 else quote or "")[-1]
    modality = (frame.modality or "") + " " + context
    if (re.search(r"\b(not required|not need|does not require|need not|không phải|không cần|không yêu cầu|không bắt buộc)\b", modality, re.I)
            and frame.statement_kind != "EXEMPTION" and "statement_kind" not in frame.human_fields):
        issues.append("Modality nêu điều không bắt buộc; cần review EXEMPTION, không biến thành nghĩa vụ tự động.")
    if (re.search(r"\b(must not|shall not|không được|bị cấm)\b", modality, re.I)
            and frame.statement_kind != "PROHIBITION" and "statement_kind" not in frame.human_fields):
        issues.append("Đoạn nghĩa vụ có điều cấm; giữ đúng phạm vi phủ định và review PROHIBITION.")
    if frame.statement_kind in {"EXEMPTION", "UNKNOWN"}:
        issues.append("Điều không bắt buộc hoặc chưa rõ không tạo ràng buộc/target chủ động; giữ ngoài phạm vi hoặc làm rõ.")
    if payload.get("kind") == "QUALITY":
        if frame.statement_kind not in {"OBLIGATION", "PROHIBITION"} or frame.effect != "QUALITY_OBLIGATION":
            issues.append("Quality target cần nghĩa vụ hoặc điều cấm được review, với effect QUALITY_OBLIGATION.")
        if set(payload.get("component_ids", [])) != set(frame.subject_ids):
            issues.append("Scope chất lượng phải khớp component chịu trách nhiệm, không lấy component bối cảnh gây lỗi.")
    elif payload.get("kind") == "INTERACTION":
        effects = {"WAIT_COMPLETION": "SYNC", "RETURN_BEFORE_COMPLETION": "ASYNC", "WORKFLOW_ONLY": "UNKNOWN", "LOCAL_ATOMIC_TRANSACTION": "SYNC"}
        if effects.get(frame.effect) != payload.get("mode") or bool(payload.get("local_transaction")) != (frame.effect == "LOCAL_ATOMIC_TRANSACTION"):
            issues.append("Mode/giao dịch không khớp tác động kiến trúc đã khai báo trong mệnh đề.")
        if payload.get("source") not in frame.subject_ids or payload.get("target") not in frame.object_ids:
            issues.append("Hai đầu tương tác phải khớp vai trò chủ thể gọi và đối tượng nhận, không suy từ điều kiện lỗi.")
        if frame.effect == "LOCAL_ATOMIC_TRANSACTION" and frame.statement_kind != "OBLIGATION":
            issues.append("Giao dịch cục bộ bắt buộc cần một nghĩa vụ được xác nhận.")
        if frame.statement_kind == "DESCRIPTION" and frame.effect != "WORKFLOW_ONLY":
            issues.append("Mô tả thứ tự công việc không tự xác định SYNC/ASYNC.")
        if frame.condition and payload.get("mode") != "UNKNOWN" and "effect" not in frame.human_fields:
            issues.append("Mode có điều kiện chưa áp dụng vô điều kiện: review các nhánh tại Review tương tác theo điều kiện, hoặc CORRECT effect như policy của ngữ cảnh đã chọn và ghi rationale.")
    elif payload.get("kind") == "SEPARATION":
        if frame.effect != "REQUIRE_SEPARATION" or frame.statement_kind not in {"OBLIGATION", "PROHIBITION"}:
            issues.append("Hard separation cần nghĩa vụ/điều cấm và tác động REQUIRE_SEPARATION được review.")
        if {payload.get("left"), payload.get("right")} != set(frame.subject_ids + frame.object_ids):
            issues.append("Hai component cần tách phải nằm trong vai trò chủ thể/đối tượng của mệnh đề.")
        if re.search(r"must not (?:be )?(?:separat|split)|shall not (?:be )?(?:separat|split)|không được (?:tách|chia)", quote, re.I) and "effect" not in frame.human_fields:
            issues.append("Câu đang cấm tách, không tự tạo REQUIRE_SEPARATION. Cần làm rõ hoặc khai báo quyết định kiến trúc bổ sung.")
        if frame.condition and "effect" not in frame.human_fields:
            issues.append("Policy tách có điều kiện cần quyết định rõ về ngữ cảnh trước khi trở thành hard rule hiện hành; CORRECT effect và ghi rationale.")
    return list(dict.fromkeys(issues))


def review_issues(architecture, record: ClauseReview) -> list[str]:
    from .studio_evidence import catalog_digest

    source = next((item for item in architecture.requirements if item.id == record.source_ref.source_id), None)
    issues = []
    if source is None or source.input_digest() != record.source_digest:
        return ["Nguồn của mệnh đề đã đổi sau review."]
    ref = record.source_ref
    if not 0 <= ref.start < ref.end <= len(source.text) or source.text[ref.start:ref.end] != ref.quote:
        issues.append("Span của mệnh đề không còn khớp nguồn.")
    if catalog_digest(architecture) != record.catalog_digest:
        issues.append("Danh mục component đã đổi sau review mệnh đề.")
    issues += clause_issues(architecture, source, {**record.claim, "quote": ref.quote, "frame": record.frame.model_dump(), "disposition": "PROPOSED"}, allow_human=True)
    return issues


def quality_review_blockers(architecture) -> list[dict]:
    blockers = []
    for source in architecture.requirements:
        for allocation in source.quality_allocations:
            for record in allocation.semantic_reviews:
                issues = review_issues(architecture, record)
                if (record.claim.get("kind") != "QUALITY" or record.claim.get("characteristic") != allocation.characteristic
                        or record.source_ref.source_id != source.id or not set(record.claim.get("component_ids", [])) <= set(allocation.component_ids)):
                    issues.append("Ánh xạ hiện hành không khớp claim đã review; xác nhận lại scope đầy đủ.")
                if issues:
                    blockers.append({"collection": "quality_allocations", "source_id": source.id, "issues": issues})
    return blockers


def clause_reviews(architecture):
    for source in architecture.requirements:
        for allocation in source.quality_allocations:
            yield from allocation.semantic_reviews
    for item in [*architecture.interactions, *architecture.keep_apart]:
        if item.evidence and item.evidence.semantic_review:
            yield item.evidence.semantic_review


def uncovered_text(source, proposals) -> list[str]:
    """Text outside all quoted spans, not semantic recall or completeness of obligations."""
    covered = [False] * len(source.text)
    for item in proposals:
        if item.get("source_id") != source.id:
            continue
        quote = (item.get("applied") or item.get("payload", {})).get("quote")
        if not isinstance(quote, str) or not quote:
            continue
        start = source.text.find(quote)
        if start >= 0:
            covered[start:start + len(quote)] = [True] * len(quote)
    spans, current = [], ""
    for char, present in zip(source.text, covered, strict=True):
        if present:
            if re.search(r"\w", current):
                spans.append(current.strip())
            current = ""
        else:
            current += char
    if re.search(r"\w", current):
        spans.append(current.strip())
    return spans
