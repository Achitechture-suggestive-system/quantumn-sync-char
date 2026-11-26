"""Revision-bound source citations for reviewed model relationships."""

from __future__ import annotations

from hashlib import sha256
import json

from .quantum_tradeoff import Architecture, EvidenceBinding


class EvidenceReviewRequired(ValueError):
    """Input is structurally valid, but its reviewed citations have become stale."""


def catalog_digest(architecture: Architecture) -> str:
    catalog = sorted((item.id, item.name) for item in architecture.components)
    return sha256(json.dumps(catalog, ensure_ascii=False).encode("utf-8")).hexdigest()


def bound_items(architecture: Architecture):
    for collection in ("interactions", "keep_apart"):
        for index, item in enumerate(getattr(architecture, collection)):
            if item.evidence:
                yield collection, index, item


def claim_digest(collection: str, item) -> str:
    raw = item if isinstance(item, dict) else item.model_dump(mode="json")
    claim = ([raw["source"], raw["target"], raw["mode"], raw["local_transaction"]] if collection == "interactions"
             else sorted([raw["left"], raw["right"]]))
    return sha256(json.dumps([collection, claim], ensure_ascii=False).encode("utf-8")).hexdigest()


def binding_issues(architecture: Architecture, evidence: EvidenceBinding, *, collection: str, item) -> list[str]:
    source = next((item for item in architecture.requirements if item.id == evidence.source_id), None)
    issues = []
    if source is None:
        issues.append("Requirement làm căn cứ đã bị xóa.")
    else:
        if source.input_digest() != evidence.source_digest:
            issues.append("Nội dung hoặc phạm vi requirement đã đổi sau review.")
        if evidence.source_quote not in source.text:
            issues.append("Đoạn trích đã duyệt không còn trong nguồn.")
    if catalog_digest(architecture) != evidence.catalog_digest:
        issues.append("Danh mục component đã đổi sau review.")
    if claim_digest(collection, item) != evidence.claim_digest:
        issues.append("Mode, giao dịch hoặc hai đầu quan hệ đã đổi sau review.")
    return issues


def evidence_blockers(architecture: Architecture) -> list[dict]:
    return [{"collection": collection, "index": index, "source_id": item.evidence.source_id, "issues": issues}
            for collection, index, item in bound_items(architecture)
            if (issues := binding_issues(architecture, item.evidence, collection=collection, item=item))]


def ensure_current_evidence(architecture: Architecture) -> None:
    blockers = evidence_blockers(architecture)
    if blockers:
        raise EvidenceReviewRequired("Cần review lại căn cứ nguồn trước khi phân nhóm: "
                                     + ", ".join(dict.fromkeys(item["source_id"] for item in blockers)))


def rebind_evidence(architecture: Architecture, collection: str, index: int, *, source_id: str, quote: str,
                    actor: str, rationale: str) -> tuple[Architecture, dict]:
    if not actor.strip() or not rationale.strip():
        raise ValueError("Điền người review và lý do xác nhận lại căn cứ.")
    source = next((item for item in architecture.requirements if item.id == source_id), None)
    if source is None or not quote.strip() or quote not in source.text:
        raise ValueError("Chọn requirement hiện hành và đoạn trích nguyên văn làm căn cứ.")
    if collection not in {"interactions", "keep_apart"} or not 0 <= index < len(getattr(architecture, collection)):
        raise ValueError("Chọn quan hệ hiện hành cần review lại.")
    item = getattr(architecture, collection)[index]
    if item.evidence is None:
        raise ValueError("Quan hệ chưa có liên kết review để cập nhật.")
    data = architecture.model_dump(mode="json")
    data[collection][index]["evidence"].update(source_id=source_id, source_digest=source.input_digest(),
                                             catalog_digest=catalog_digest(architecture), source_quote=quote,
                                             claim_digest=claim_digest(collection, item),
                                             citation_provenance="HUMAN_DECISION", review_actor=actor.strip(),
                                             review_rationale=rationale.strip())
    changed = Architecture.model_validate(data)
    return changed, {"action": "SOURCE_EVIDENCE_RECONFIRMED", "actor": actor.strip(), "rationale": rationale.strip(),
                     "collection": collection, "index": index,
                     "before": architecture.model_dump(mode="json"), "after": changed.model_dump(mode="json")}


def restore_legacy_bindings(checkpoint: dict) -> None:
    """Enrich only in memory when an old recorded applied proposal matches the exact relationship."""
    architecture = checkpoint["architecture"]
    decision = checkpoint.get("event", {})
    for proposal in checkpoint.get("proposals", []):
        applied = proposal.get("applied")
        if not applied or proposal.get("status") not in {"APPROVED", "CORRECTED"}:
            continue
        item = None
        if applied.get("kind") == "INTERACTION":
            item = next((edge for edge in architecture["interactions"]
                         if (edge["source"], edge["target"], edge["mode"], edge["local_transaction"], edge["basis"])
                         == (applied["source"], applied["target"], applied["mode"], applied["local_transaction"], applied["quote"])), None)
        elif applied.get("kind") == "SEPARATION":
            item = next((rule for rule in architecture["keep_apart"]
                         if {rule["left"], rule["right"]} == {applied["left"], applied["right"]} and rule["basis"] == applied["quote"]), None)
        if item is None or item.get("evidence") is not None or item.get("cases"):
            continue
        latest = decision.get("proposal_id") == proposal["id"]
        item["evidence"] = EvidenceBinding(
            source_id=proposal["source_id"], source_digest=proposal["source_digest"], catalog_digest=proposal["catalog_digest"],
            claim_digest=claim_digest("interactions" if applied["kind"] == "INTERACTION" else "keep_apart", item),
            source_quote=applied["quote"], proposal_id=proposal["id"], run_id=proposal["run_id"],
            citation_provenance="HUMAN_DECISION" if proposal["status"] == "CORRECTED" else "LLM_PROPOSAL",
            review_actor=decision.get("actor", "UNKNOWN") if latest else "UNKNOWN",
            review_rationale=decision.get("rationale", "Khôi phục theo quyết định đã lưu.") if latest else "Khôi phục theo đề xuất đã áp dụng trong checkpoint cũ; reviewer UNKNOWN.",
        ).model_dump(mode="json")
