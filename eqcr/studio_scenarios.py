"""Reviewed six-part scenarios and conditional bounds under declared timing assumptions."""

from __future__ import annotations

from math import isclose, isfinite
import re
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

from .models import Scenario
from .studio_quality import QualityCharacteristic


Nonnegative = Annotated[float, Field(ge=0, allow_inf_nan=False, strict=True)]
Digest = Annotated[str, StringConstraints(pattern=r"^[a-f0-9]{64}$")]
PARTS = ("stimulus_source", "stimulus", "environment", "stimulated_artifact", "response", "response_measure")
UNIT_MS = {"ms": 1, "s": 1000, "min": 60000}


class TimingAssumptions(BaseModel):
    model_config = ConfigDict(extra="forbid")
    provenance: Literal["HUMAN_DECISION", "PREPARED_FIXTURE"]
    semantics: Literal["ASSUMED_UPPER_BOUND_INCLUDING_WAIT"]
    component_ms: dict[str, Nonnegative | None] = Field(default_factory=dict)
    sync_round_trip_ms: Nonnegative | None = None
    async_enqueue_ms: Nonnegative | None = None
    async_delivery_ms: Nonnegative | None = None
    detection_ms: Nonnegative | None = None
    rationale: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=1000)]


class ReviewedScenario(BaseModel):
    model_config = ConfigDict(extra="forbid")
    scenario: Scenario
    source_digest: Digest
    catalog_digest: Digest
    characteristic: QualityCharacteristic
    component_path: list[str] = Field(min_length=1, max_length=8)
    responsible_component_ids: list[str] = Field(min_length=1, max_length=8)
    metric: Literal["RESPONSE_LATENCY", "RECOVERY_TIME", "UNSUPPORTED"] = "UNSUPPORTED"
    target_value: Annotated[float, Field(gt=0, allow_inf_nan=False, strict=True)] | None = None
    target_unit: Literal["ms", "s", "min"] | None = None
    completion: Literal["CALLER_RESPONSE", "BUSINESS_COMPLETION"] = "BUSINESS_COMPLETION"
    assumptions: TimingAssumptions
    decision_provenance: Literal["HUMAN_DECISION", "PREPARED_FIXTURE"] = "HUMAN_DECISION"
    actor: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]
    rationale: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=1000)]


def scenario_issues(architecture, record: ReviewedScenario) -> list[str]:
    from .studio_evidence import catalog_digest

    source = next((item for item in architecture.requirements if item.id == record.scenario.source_ref.source_id), None)
    ref = record.scenario.source_ref
    issues = []
    if source is None or source.input_digest() != record.source_digest:
        issues.append("Requirement nguồn đã đổi hoặc không còn tồn tại.")
    elif source.text[ref.start:ref.end] != ref.quote:
        issues.append("Span nguồn scenario không còn khớp.")
    if source is not None and source.kind != "NFR":
        issues.append("Quality scenario cần requirement được phân loại NFR.")
    if catalog_digest(architecture) != record.catalog_digest:
        issues.append("Danh mục component đã đổi.")
    if not set([*record.component_path, *record.responsible_component_ids]) <= {item.id for item in architecture.components}:
        issues.append("Scenario trỏ tới component chưa khai báo.")
    if len(record.component_path) != len(set(record.component_path)):
        issues.append("Mô hình thời gian hiện hỗ trợ đường đi tuần tự không lặp.")
    if len(record.responsible_component_ids) != len(set(record.responsible_component_ids)):
        issues.append("Component chịu trách nhiệm scenario bị trùng.")
    if record.metric == "RECOVERY_TIME" and len(record.component_path) != 1:
        issues.append("Scenario khôi phục cần một component bị tác động làm đầu mối.")
    return issues


def target_is_cited(record: ReviewedScenario) -> bool:
    """Check the number/unit tokens, leaving comparator and entailment to the reviewer."""
    quote = record.scenario.target or ""
    if record.target_value is None or record.target_unit is None or not quote or quote not in record.scenario.source_ref.quote:
        return False
    units = {"ms": {"ms", "milliseconds", "mili giây"}, "s": {"s", "seconds", "giây"}, "min": {"min", "minutes", "phút"}}
    matches = re.findall(r"(?<![\w.])(\d+(?:[.,]\d+)?)\s*(milliseconds|mili giây|minutes|seconds|ms|min|phút|giây|s)\b", quote, re.IGNORECASE)
    return any(isclose(float(number.replace(",", ".")), record.target_value) and unit.casefold() in units[record.target_unit]
               for number, unit in matches)


def scenario_parts(record: ReviewedScenario) -> dict:
    result = {}
    for field in PARTS:
        value = (getattr(record.scenario, field) or "").strip()
        result[field] = {"value": value or None, "provenance": "UNKNOWN" if not value else
                         "SOURCE_REQUIREMENT" if value in record.scenario.source_ref.quote else record.decision_provenance}
    return result


def predict_scenario(architecture, candidate, record: ReviewedScenario) -> dict:
    from .quantum_tradeoff import group_index
    from .studio_uncertainty import possible_modes

    assignment = group_index(candidate.groups)
    parts = scenario_parts(record)
    issues = scenario_issues(architecture, record)
    target_ms = record.target_value * UNIT_MS[record.target_unit] if record.target_value is not None and record.target_unit else None
    if target_ms is not None and not isfinite(target_ms):
        target_ms = None
        issues.append("Target quy đổi vượt giới hạn biểu diễn số.")
    result = {"scenario_id": record.scenario.id, "source_id": record.scenario.source_ref.source_id,
              "candidate_id": candidate.id, "characteristic": record.characteristic.value,
              "scenario_parts": parts, "scope": record.responsible_component_ids, "component_path": record.component_path,
              "quanta": list(dict.fromkeys(f"Q{assignment[item]}" for item in record.responsible_component_ids if item in assignment)),
              "declared_target_ms": target_ms, "target_ms": target_ms if not issues and target_is_cited(record) else None,
              "target_provenance": "SOURCE_REQUIREMENT" if not issues and target_is_cited(record) else "UNKNOWN",
              "source_ref": record.scenario.source_ref.model_dump(mode="json"),
              "review_provenance": record.decision_provenance, "review_actor": record.actor,
              "prediction_status": "INSUFFICIENT_EVIDENCE", "predicted_upper_ms": None,
              "target_comparison": "UNKNOWN", "measurement_status": "NOT_MEASURED", "measurement": None,
              "assumption_provenance": record.assumptions.provenance, "model": "STUDIO-SERIAL-BOUND@1",
              "assumption_semantics": record.assumptions.semantics, "assumption_rationale": record.assumptions.rationale,
              "drivers": [], "issues": issues, "provenance": "DETERMINISTIC_TRANSFORMATION"}
    if issues:
        return result
    if not all(part["value"] for part in parts.values()):
        issues.append("Scenario chưa đủ sáu phần. Không dự đoán từ các phần còn UNKNOWN.")
    if not target_is_cited(record):
        issues.append("Số và đơn vị của target cần khớp đoạn nguồn đã review.")
    if record.metric == "UNSUPPORTED":
        issues.append("Chưa có adapter dự đoán cho metric này.")
    if issues:
        return result
    assumptions = record.assumptions
    total = 0.0

    def add(subject, value):
        nonlocal total
        if value is None:
            issues.append(f"Chưa có bound cho {subject}.")
        else:
            total += value
            if not isfinite(total):
                issues.append("Tổng bound vượt giới hạn biểu diễn số.")
            result["drivers"].append({"subject": subject, "upper_ms": value, "provenance": assumptions.provenance})

    if record.metric == "RECOVERY_TIME":
        add("Phát hiện lỗi", assumptions.detection_ms)
        quantum = assignment[record.component_path[0]]
        for component in next(group for group in candidate.groups if assignment[group[0]] == quantum):
            add(f"Khôi phục tuần tự {component}", assumptions.component_ms.get(component))
    else:
        add(record.component_path[0], assumptions.component_ms.get(record.component_path[0]))
        edges = {(edge.source, edge.target): edge for edge in architecture.interactions}
        for source, target in zip(record.component_path, record.component_path[1:]):
            edge = edges.get((source, target))
            if edge is None:
                issues.append(f"Chưa khai báo tương tác {source} → {target} trên đường đi.")
                break
            modes = possible_modes(architecture, edge)
            if len(modes) != 1:
                issues.append(f"Mode {source} → {target} còn nhiều giả thuyết. Cần chọn điều kiện rõ để dự đoán.")
                break
            mode = next(iter(modes))
            if mode == "ASYNC":
                if record.completion == "CALLER_RESPONSE":
                    add(f"Ghi nhận hàng đợi {source} → {target}", assumptions.async_enqueue_ms)
                    break
                add(f"Chờ/giao nhận ASYNC {source} → {target}", assumptions.async_delivery_ms)
            elif assignment[source] != assignment[target]:
                add(f"SYNC qua Quantum {source} → {target}", assumptions.sync_round_trip_ms)
            add(target, assumptions.component_ms.get(target))
    if issues:
        return result
    result.update(prediction_status="PREDICTED_UPPER_BOUND", predicted_upper_ms=total,
                  target_comparison="UPPER_BOUND_WITHIN_TARGET" if total <= target_ms else "UPPER_BOUND_EXCEEDS_TARGET")
    return result


def review_scenario(architecture, record: ReviewedScenario, *, allocate: bool = True):
    from .quantum_tradeoff import Architecture

    issues = scenario_issues(architecture, record)
    if issues:
        raise ValueError(" ".join(issues))
    source_id = record.scenario.source_ref.source_id
    if any(item.scenario.id == record.scenario.id and item.scenario.source_ref.source_id != source_id
           for item in architecture.quality_scenarios):
        raise ValueError("Mã scenario đang thuộc NFR khác. Chọn mã mới để giữ truy vết nguồn.")
    data = architecture.model_dump(mode="json")
    data["quality_scenarios"] = [item for item in data["quality_scenarios"] if item["scenario"]["id"] != record.scenario.id]
    data["quality_scenarios"].append(record.model_dump(mode="json"))
    if allocate:
        source = next(item for item in data["requirements"] if item["id"] == source_id)
        if source["kind"] != "NFR" or source["duplicate_of"]:
            raise ValueError("Chọn NFR gốc để đưa scope scenario vào ánh xạ ISO.")
        source["quality_allocations"] = [item for item in source["quality_allocations"] if item["characteristic"] != record.characteristic]
        source["quality_allocations"].append({"characteristic": record.characteristic.value,
                                              "component_ids": record.responsible_component_ids,
                                              "source_quote": record.scenario.source_ref.quote})
    changed = Architecture.model_validate(data)
    return changed, {"action": "QUALITY_SCENARIO_REVIEW", "actor": record.actor, "rationale": record.rationale,
                     "provenance": record.decision_provenance,
                     "scenario_id": record.scenario.id, "source_id": source_id, "allocate_iso": allocate,
                     "before": architecture.model_dump(mode="json"), "after": changed.model_dump(mode="json")}
