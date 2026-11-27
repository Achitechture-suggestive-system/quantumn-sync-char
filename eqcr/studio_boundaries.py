"""Source-bound interaction contracts and data ownership decisions for Studio candidates."""

from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
import json
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator

from .models import InteractionContract, SourceRef


Text = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=1000)]
Digest = Annotated[str, StringConstraints(pattern=r"^[a-f0-9]{64}$")]
CONTRACT_FIELDS = ("operation", "data_dependency", "request_fields", "response_fields", "versioning", "consistency",
                   "latency_budget", "failure_handling", "retry_policy", "timeout_policy", "idempotency_policy")
UNKNOWN_TEXT = {"", "unknown", "unresolved", "not_measured", "insufficient_evidence", "not_benchmarked"}


class ReviewContext(BaseModel):
    model_config = ConfigDict(extra="forbid")
    source_digests: dict[str, Digest] = Field(default_factory=dict)
    catalog_digest: Digest
    actor: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]
    rationale: Text
    provenance: Literal["HUMAN_DECISION", "PREPARED_FIXTURE"] = "HUMAN_DECISION"
    recorded_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @field_validator("recorded_at")
    @classmethod
    def timezone_required(cls, value):
        if value.tzinfo is None:
            raise ValueError("Thời điểm review cần múi giờ.")
        return value


class ReviewedContract(ReviewContext):
    source: str
    target: str
    contract: InteractionContract
    claim_digest: Digest
    data_scope: Literal["UNKNOWN", "NONE", "STORES"] = "UNKNOWN"
    store_ids: list[str] = Field(default_factory=list)
    store_digests: dict[str, Digest] = Field(default_factory=dict)
    reference_protocol: Literal["OUTBOX_INBOX_V1"] | None = None


class OwnershipDecision(ReviewContext):
    store_id: str
    store_digest: Digest
    review_status: Literal["DRAFT", "REVIEWED"] = "DRAFT"
    strategy: Literal["UNKNOWN", "SINGLE_WRITER", "PARTITIONED_WRITERS"] = "UNKNOWN"
    writers: list[str] = Field(default_factory=list)
    partition_key: str = "UNKNOWN"
    invariant: str = "UNKNOWN"
    consistency: str = "UNKNOWN"
    replication_lag_ms: Annotated[float, Field(ge=0, allow_inf_nan=False, strict=True)] | None = None
    source_refs: list[SourceRef] = Field(default_factory=list)


def fingerprint(value) -> str:
    return sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def store_fingerprint(store) -> str:
    return fingerprint({"id": store.id, "members": sorted(store.members), "policy": store.policy})


def source_digests(architecture, references: list[SourceRef]) -> dict[str, str]:
    sources = {item.id: item for item in architecture.requirements}
    if any(ref.source_id not in sources for ref in references):
        raise ValueError("SourceRef phải trỏ tới requirement hiện hành.")
    return {ref.source_id: sources[ref.source_id].input_digest() for ref in references}


def context_issues(architecture, review: ReviewContext, references: list[SourceRef]) -> list[str]:
    from .studio_evidence import catalog_digest

    issues = []
    sources = {item.id: item for item in architecture.requirements}
    if not references or set(review.source_digests) != {ref.source_id for ref in references}:
        issues.append("Chưa có tập nguồn/hash đầy đủ cho quyết định.")
    for ref in references:
        source = sources.get(ref.source_id)
        if source is None or review.source_digests.get(ref.source_id) != source.input_digest():
            issues.append(f"Nguồn {ref.source_id} đã đổi hoặc bị xóa.")
        elif not 0 <= ref.start < ref.end <= len(source.text) or source.text[ref.start:ref.end] != ref.quote:
            issues.append(f"Span {ref.source_id} không khớp văn bản hiện hành.")
    if review.catalog_digest != catalog_digest(architecture):
        issues.append("Danh mục component đã đổi sau review.")
    return list(dict.fromkeys(issues))


def contract_issues(architecture, review: ReviewedContract) -> list[str]:
    from .studio_evidence import claim_digest

    issues = context_issues(architecture, review, review.contract.source_refs)
    edge = next((item for item in architecture.interactions if (item.source, item.target) == (review.source, review.target)), None)
    if edge is None or review.claim_digest != claim_digest("interactions", edge):
        issues.append("Tương tác đã đổi sau review hợp đồng.")
    if review.contract.selected_mode == "UNDECIDED":
        issues.append("Hợp đồng đang là bản nháp, chưa có mode được duyệt.")
    elif edge and edge.mode != review.contract.selected_mode:
        issues.append("Mode hợp đồng không khớp cạnh hiện hành.")
    if review.contract.selected_mode != "UNDECIDED" and (review.actor.casefold() in UNKNOWN_TEXT or review.contract.reviewer_id != review.actor):
        issues.append("Reviewer hợp đồng không khớp quyết định hiện hành.")
    if review.data_scope == "UNKNOWN":
        issues.append("Phạm vi phụ thuộc kho dữ liệu chưa được review.")
    if review.data_scope == "NONE" and review.store_ids or review.data_scope == "STORES" and not review.store_ids:
        issues.append("Phạm vi dữ liệu và danh sách kho không nhất quán.")
    if not set(review.store_ids) <= {store.id for store in architecture.stores}:
        issues.append("Kho trong hợp đồng đã đổi hoặc không tồn tại.")
    if len(review.store_ids) != len(set(review.store_ids)):
        issues.append("Kho dữ liệu trong hợp đồng bị trùng.")
    stores = {store.id: store for store in architecture.stores}
    if set(review.store_digests) != set(review.store_ids) or any(
            key not in stores or store_fingerprint(stores[key]) != digest for key, digest in review.store_digests.items()):
        issues.append("Phạm vi hoặc chính sách kho trong hợp đồng đã đổi sau review.")
    if any(getattr(review.contract, field).strip().casefold() in UNKNOWN_TEXT for field in CONTRACT_FIELDS):
        issues.append("Hợp đồng còn trường chưa được xác định.")
    return issues


def save_contract(architecture, review: ReviewedContract):
    from .quantum_tradeoff import Architecture, EvidenceBinding
    from .studio_conflicts import enforce_protected_rules

    draft = review.contract.selected_mode == "UNDECIDED"
    issues = context_issues(architecture, review, review.contract.source_refs)
    edge = next((item for item in architecture.interactions if (item.source, item.target) == (review.source, review.target)), None)
    if edge is None:
        issues.append("Chọn một tương tác hiện hành để review hợp đồng.")
    if issues:
        raise ValueError(" ".join(issues))
    if not draft and (review.contract.reviewer_id != review.actor or review.actor.casefold() in UNKNOWN_TEXT):
        raise ValueError("Reviewer của hợp đồng phải khớp người ghi quyết định hiện tại.")
    data = architecture.model_dump(mode="json")
    previous = next((item for item in architecture.interaction_contracts if (item.source, item.target) == (review.source, review.target)), None)
    if draft and previous and previous.contract.selected_mode != "UNDECIDED":
        raise ValueError("Không thay hợp đồng đã duyệt bằng bản nháp. Gỡ hợp đồng có lý do trước khi lưu nháp mới.")
    if not draft:
        raw = next(item for item in data["interactions"] if (item["source"], item["target"]) == (review.source, review.target))
        # local_transaction remains unchanged; an ASYNC choice cannot silently remove this hard rule.
        raw.update(mode=review.contract.selected_mode, cases=[])
        first = review.contract.source_refs[0]
        raw["evidence"] = EvidenceBinding(source_id=first.source_id, source_digest=review.source_digests[first.source_id],
                                           catalog_digest=review.catalog_digest, claim_digest=review.claim_digest,
                                           source_quote=first.quote, proposal_id=f"contract-{review.contract.contract_id}",
                                           run_id="CONTRACT_REVIEW", citation_provenance=review.provenance,
                                           review_provenance=review.provenance,
                                           review_actor=review.actor, review_rationale=review.rationale).model_dump(mode="json")
    data["interaction_contracts"] = [item for item in data["interaction_contracts"]
                                      if (item["source"], item["target"]) != (review.source, review.target)]
    data["interaction_contracts"].append(review.model_dump(mode="json"))
    changed = Architecture.model_validate(data)
    enforce_protected_rules(architecture, changed)
    if not draft and (issues := contract_issues(changed, review)):
        raise ValueError(" ".join(issues))
    return changed, {"action": "CONTRACT_DRAFT_SAVED" if draft else "INTERACTION_CONTRACT_REVIEWED", "actor": review.actor,
                     "rationale": review.rationale, "provenance": review.provenance, "contract_id": review.contract.contract_id,
                     "before": architecture.model_dump(mode="json"), "after": changed.model_dump(mode="json")}


def remove_contract(architecture, source: str, target: str, *, actor: str, rationale: str,
                    provenance: Literal["HUMAN_DECISION", "PREPARED_FIXTURE"] = "HUMAN_DECISION"):
    from .quantum_tradeoff import Architecture

    if not actor.strip() or not rationale.strip():
        raise ValueError("Ghi người review và lý do gỡ hợp đồng, giữ giả định mode hiện hành.")
    record = next((item for item in architecture.interaction_contracts if (item.source, item.target) == (source, target)), None)
    if record is None:
        raise ValueError("Hợp đồng không còn trong mô hình hiện hành.")
    data = architecture.model_dump(mode="json")
    data["interaction_contracts"] = [item for item in data["interaction_contracts"] if (item["source"], item["target"]) != (source, target)]
    for edge in data["interactions"]:
        binding = edge.get("evidence")
        if (edge["source"], edge["target"]) == (source, target) and binding and binding["proposal_id"] == f"contract-{record.contract.contract_id}":
            edge["evidence"] = None
    changed = Architecture.model_validate(data)
    return changed, {"action": "CONTRACT_REMOVED_KEEP_MODE_POLICY", "actor": actor, "rationale": rationale,
                     "provenance": provenance, "source": source, "target": target,
                     "before": architecture.model_dump(mode="json"), "after": changed.model_dump(mode="json")}


def ownership_issues(architecture, review: OwnershipDecision) -> list[str]:
    issues = context_issues(architecture, review, review.source_refs)
    store = next((item for item in architecture.stores if item.id == review.store_id), None)
    if store is None or store_fingerprint(store) != review.store_digest:
        issues.append("Kho hoặc chính sách kho đã đổi sau review ownership.")
    if review.review_status != "REVIEWED" or review.strategy == "UNKNOWN":
        issues.append("Ownership đang là bản nháp.")
    if review.actor.casefold() in UNKNOWN_TEXT:
        issues.append("Cần khai báo người review ownership.")
    if not review.writers or len(review.writers) != len(set(review.writers)) or store and not set(review.writers) <= set(store.members):
        issues.append("Cần writer duy nhất theo ID, thuộc các component dùng kho.")
    if review.strategy == "SINGLE_WRITER" and len(review.writers) != 1:
        issues.append("SINGLE_WRITER cần đúng một component ghi dữ liệu.")
    required = [review.invariant, review.consistency] + ([review.partition_key] if review.strategy == "PARTITIONED_WRITERS" else [])
    if any(value.strip().casefold() in UNKNOWN_TEXT for value in required):
        issues.append("Invariant, consistency hoặc khóa phân vùng còn chưa xác định.")
    return issues


def save_ownership(architecture, review: OwnershipDecision):
    from .quantum_tradeoff import Architecture

    if review.review_status == "REVIEWED" and (issues := ownership_issues(architecture, review)):
        raise ValueError(" ".join(issues))
    if review.review_status == "DRAFT" and (issues := context_issues(architecture, review, review.source_refs)):
        raise ValueError(" ".join(issues))
    data = architecture.model_dump(mode="json")
    data["ownership_decisions"] = [item for item in data["ownership_decisions"] if item["store_id"] != review.store_id]
    data["ownership_decisions"].append(review.model_dump(mode="json"))
    changed = Architecture.model_validate(data)
    return changed, {"action": "DATA_OWNERSHIP_REVIEW", "actor": review.actor, "rationale": review.rationale,
                     "provenance": review.provenance, "store_id": review.store_id,
                     "before": architecture.model_dump(mode="json"), "after": changed.model_dump(mode="json")}


def boundary_profiles(architecture, candidate) -> dict:
    from .quantum_tradeoff import group_index

    assignment = group_index(candidate.groups)
    contracts = {(item.source, item.target): item for item in architecture.interaction_contracts}
    ownership = {item.store_id: item for item in architecture.ownership_decisions}
    edges, stores = [], []
    for edge in architecture.interactions:
        if assignment[edge.source] == assignment[edge.target]:
            continue
        review = contracts.get((edge.source, edge.target))
        issues = contract_issues(architecture, review) if review else ["Chưa có hợp đồng đã review cho ranh giới này."]
        edges.append({"source": edge.source, "target": edge.target, "mode": edge.mode,
                      "from_quantum": f"Q{assignment[edge.source]}", "to_quantum": f"Q{assignment[edge.target]}",
                      "contract_status": "REVIEWED_NOT_RUNTIME_VERIFIED" if not issues else "REVIEW_REQUIRED",
                      "contract": review.model_dump(mode="json") if review else None, "issues": issues})
    for store in architecture.stores:
        quanta = sorted({assignment[item] for item in store.members})
        if len(quanta) < 2:
            continue
        review = ownership.get(store.id)
        issues = ownership_issues(architecture, review) if review else ["Chưa có ownership đã review cho kho qua ranh giới."]
        stores.append({"store_id": store.id, "quanta": [f"Q{group}" for group in quanta],
                       "ownership_status": "REVIEWED_INVARIANT_NOT_PROVEN" if not issues else "REVIEW_REQUIRED",
                       "writer_quanta": {item: f"Q{assignment[item]}" for item in review.writers if item in assignment} if review else {},
                       "replication_lag_measurement_status": "NOT_MEASURED",
                       "ownership": review.model_dump(mode="json") if review else None, "issues": issues})
    return {"candidate_id": candidate.id, "interactions": edges, "stores": stores,
            "provenance": "DETERMINISTIC_TRANSFORMATION", "deployability_status": "NOT_VERIFIED"}
