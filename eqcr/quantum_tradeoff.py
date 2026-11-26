"""Compare architecture partitions under explicit coupling and quality preferences."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from collections.abc import Iterator
from hashlib import sha256
import json
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

from .pipeline import _partitions
from .studio_quality import QualityCharacteristic


Key = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=32, pattern=r"^[A-Za-z][A-Za-z0-9_-]*$")]
Label = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]
Cost = Annotated[int, Field(ge=0, le=10)]
Ranking = Literal["SYNC_FIRST", "CHARACTERISTIC_FIRST", "WEIGHTED"]


class InputModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Component(InputModel):
    id: Key
    name: Label
    characteristics: list[Label] = Field(default_factory=list, max_length=12)
    characteristic_requirements: dict[Label, list[Key]] = Field(default_factory=dict)


class QualityAllocation(InputModel):
    characteristic: QualityCharacteristic
    component_ids: list[Key] = Field(min_length=1, max_length=8)
    source_quote: str = Field(default="", max_length=600)


class RequirementGeneration(InputModel):
    model: Label
    case_id: Key
    proposal_number: int = Field(ge=1)
    response_sha256: Annotated[str, StringConstraints(pattern=r"^[a-f0-9]{64}$")]
    input_sha256: Annotated[str, StringConstraints(pattern=r"^[a-f0-9]{64}$")]
    characteristic: QualityCharacteristic | None = None
    quote: str = Field(default="", max_length=600)


class Requirement(InputModel):
    id: Key
    text: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=600)]
    kind: Literal["UNSPECIFIED", "FR", "NFR"] = "UNSPECIFIED"
    component_ids: list[Key] = Field(default_factory=list, max_length=8)
    quality_allocations: list[QualityAllocation] = Field(default_factory=list, max_length=9)
    generation: RequirementGeneration | None = None
    duplicate_of: Key | None = None

    def input_digest(self) -> str:
        source = [self.kind, self.text, sorted(self.component_ids)]
        if self.duplicate_of:
            source.append({"duplicate_of": self.duplicate_of})
        payload = json.dumps(source, ensure_ascii=False)
        return sha256(payload.encode("utf-8")).hexdigest()

    @property
    def matches_generated_input(self) -> bool:
        return self.generation is not None and self.input_digest() == self.generation.input_sha256

    @property
    def model_suggestion(self) -> tuple[QualityCharacteristic, str] | None:
        generated = self.generation
        if (self.matches_generated_input and self.kind == "NFR" and generated is not None
                and generated.characteristic and generated.quote and generated.quote in self.text):
            return generated.characteristic, generated.quote
        return None


class InteractionCase(InputModel):
    condition: Label
    mode: Literal["SYNC", "ASYNC"]
    source_id: Key
    source_digest: Annotated[str, StringConstraints(pattern=r"^[a-f0-9]{64}$")]
    source_quote: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=600)]


class ConstraintReviewPolicy(InputModel):
    protected: bool = False
    change_cost: int = Field(default=1, ge=1, le=1000)


class EvidenceBinding(InputModel):
    source_id: Key
    source_digest: Annotated[str, StringConstraints(pattern=r"^[a-f0-9]{64}$")]
    catalog_digest: Annotated[str, StringConstraints(pattern=r"^[a-f0-9]{64}$")]
    claim_digest: Annotated[str, StringConstraints(pattern=r"^[a-f0-9]{64}$")]
    source_quote: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=600)]
    proposal_id: Annotated[str, StringConstraints(min_length=1, max_length=200)]
    run_id: Annotated[str, StringConstraints(min_length=1, max_length=100)]
    citation_provenance: Literal["LLM_PROPOSAL", "HUMAN_DECISION"]
    review_provenance: Literal["HUMAN_DECISION"] = "HUMAN_DECISION"
    review_actor: Label
    review_rationale: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=1000)]


class Interaction(InputModel):
    source: Key
    target: Key
    mode: Literal["SYNC", "ASYNC", "UNKNOWN"]
    weight: Cost = 1
    local_transaction: bool = False
    basis: str = Field(default="", max_length=240)
    cases: list[InteractionCase] = Field(default_factory=list, max_length=4)
    review_policy: ConstraintReviewPolicy = Field(default_factory=ConstraintReviewPolicy)
    evidence: EvidenceBinding | None = None

    @model_validator(mode="after")
    def check_coupling(self):
        if self.source == self.target:
            raise ValueError("Hai đầu của quan hệ phải là component khác nhau.")
        if self.local_transaction and (self.mode != "SYNC" or not self.basis.strip()):
            raise ValueError("Giao dịch cục bộ cần quan hệ SYNC và căn cứ rõ ràng.")
        if self.cases and (self.mode != "UNKNOWN" or len(self.cases) < 2):
            raise ValueError("Quan hệ theo điều kiện cần UNKNOWN và ít nhất hai điều kiện được review.")
        if len({item.condition.casefold() for item in self.cases}) != len(self.cases):
            raise ValueError("Các điều kiện tương tác phải có tên khác nhau.")
        return self


class DataStore(InputModel):
    id: Key
    name: Label
    members: list[Key] = Field(min_length=1, max_length=8)
    policy: Literal["KEEP_SHARED", "SPLITTABLE"]
    weight: Cost = 1
    basis: str = Field(default="", max_length=240)
    review_policy: ConstraintReviewPolicy = Field(default_factory=ConstraintReviewPolicy)

    @model_validator(mode="after")
    def check_policy(self):
        if len(self.members) != len(set(self.members)):
            raise ValueError("Danh sách component của kho dữ liệu bị trùng.")
        if len(self.members) > 1 and not self.basis.strip():
            raise ValueError("Kho dùng chung cần ghi căn cứ giữ chung hoặc tách.")
        return self


class SeparatePair(InputModel):
    left: Key
    right: Key
    basis: Label
    review_policy: ConstraintReviewPolicy = Field(default_factory=ConstraintReviewPolicy)
    evidence: EvidenceBinding | None = None


class Architecture(InputModel):
    components: list[Component] = Field(min_length=1, max_length=8)
    interactions: list[Interaction] = Field(default_factory=list, max_length=56)
    stores: list[DataStore] = Field(default_factory=list, max_length=16)
    keep_apart: list[SeparatePair] = Field(default_factory=list, max_length=28)
    requirements: list[Requirement] = Field(default_factory=list, max_length=40)

    @model_validator(mode="after")
    def check_references(self):
        ids = {item.id for item in self.components}
        if len(ids) != len(self.components):
            raise ValueError("ID component phải duy nhất.")
        if len({item.id for item in self.stores}) != len(self.stores):
            raise ValueError("ID kho dữ liệu phải duy nhất.")
        requirement_ids = {requirement.id for requirement in self.requirements}
        if len(requirement_ids) != len(self.requirements):
            raise ValueError("ID requirement phải duy nhất.")
        for requirement in self.requirements:
            visited = {requirement.id}
            target = requirement
            while target.duplicate_of:
                if target.duplicate_of not in requirement_ids or target.duplicate_of in visited:
                    raise ValueError("Liên kết mục tiêu trùng bị lặp vòng hoặc trỏ tới nguồn chưa khai báo.")
                visited.add(target.duplicate_of)
                target = next(item for item in self.requirements if item.id == target.duplicate_of)
                if target.kind != "NFR" or requirement.kind != "NFR":
                    raise ValueError("Liên kết mục tiêu chất lượng trùng cần hai nguồn NFR.")
                if target.duplicate_of:
                    raise ValueError("Mục tiêu trùng phải trỏ trực tiếp tới bản gốc.")
            if requirement.duplicate_of and requirement.quality_allocations:
                raise ValueError("Nguồn cùng mục tiêu dùng ánh xạ của bản gốc. Tách mục tiêu trước khi gán ISO riêng.")
            scope = set(requirement.component_ids)
            if not scope <= ids or len(scope) != len(requirement.component_ids):
                raise ValueError(f"{requirement.id} có component phụ trách trùng hoặc chưa khai báo.")
            allocations = requirement.quality_allocations
            if allocations and requirement.kind != "NFR":
                raise ValueError(f"{requirement.id} phải là NFR để gắn characteristic ISO.")
            if len({item.characteristic for item in allocations}) != len(allocations):
                raise ValueError(f"{requirement.id} có characteristic ISO trùng.")
            for item in allocations:
                if not set(item.component_ids) <= ids or len(set(item.component_ids)) != len(item.component_ids):
                    raise ValueError(f"{requirement.id} có component ISO trùng hoặc chưa khai báo.")
                if item.source_quote and item.source_quote not in requirement.text:
                    raise ValueError(f"{requirement.id} có đoạn trích ISO không khớp nội dung nguồn.")
        for component in self.components:
            for label, linked_ids in component.characteristic_requirements.items():
                if label not in component.characteristics:
                    raise ValueError(f"{component.id} chưa được gán characteristic {label!r}.")
                unknown = set(linked_ids) - requirement_ids
                if unknown:
                    raise ValueError(f"{component.id} / {label} trỏ tới requirement chưa khai báo: {', '.join(sorted(unknown))}.")
                if len(linked_ids) != len(set(linked_ids)):
                    raise ValueError(f"{component.id} / {label} có mã requirement trùng.")
        pairs = set()
        for edge in self.interactions:
            pair = (edge.source, edge.target)
            if not set(pair) <= ids:
                raise ValueError(f"Quan hệ {edge.source} → {edge.target} trỏ tới component chưa khai báo.")
            if pair in pairs:
                raise ValueError(f"Quan hệ {edge.source} → {edge.target} bị trùng.")
            pairs.add(pair)
        for store in self.stores:
            if not set(store.members) <= ids:
                raise ValueError(f"Kho {store.id} trỏ tới component chưa khai báo.")
        separation = set()
        for rule in self.keep_apart:
            pair = frozenset((rule.left, rule.right))
            if len(pair) != 2 or not pair <= ids:
                raise ValueError("Cặp cần tách phải chứa hai ID component khác nhau đã khai báo.")
            if pair in separation:
                raise ValueError("Cặp cần tách bị trùng.")
            separation.add(pair)
        return self


class Preferences(InputModel):
    sync: Cost = 3
    data: Cost = 6
    async_seam: Cost = 1
    characteristics: Cost = 2

    @property
    def vector(self) -> tuple[int, ...]:
        return self.sync, self.data, self.async_seam, self.characteristics, self.characteristics


@dataclass(frozen=True)
class Candidate:
    id: str
    groups: tuple[tuple[str, ...], ...]
    sync: int
    data: int
    async_seam: int
    characteristic_spread: int
    characteristic_mix: int

    @property
    def vector(self) -> tuple[int, ...]:
        return self.sync, self.data, self.async_seam, self.characteristic_spread, self.characteristic_mix

    def score(self, weights: Preferences) -> int:
        return sum(units * weight for units, weight in zip(self.vector, weights.vector, strict=True))


@dataclass(frozen=True)
class Analysis:
    enumerated: int
    feasible: tuple[Candidate, ...]
    frontier: tuple[Candidate, ...]
    ranked: tuple[Candidate, ...]


@dataclass(frozen=True)
class CostDriver:
    axis: int
    subject: str
    components: tuple[str, ...]
    quanta: tuple[int, ...]
    units: int


@dataclass(frozen=True)
class HardConstraint:
    kind: Literal["KEEP_APART", "LOCAL_TRANSACTION", "KEEP_SHARED"]
    index: int
    components: tuple[str, ...]
    basis: str
    protected: bool = False
    change_cost: int = 1

    def violated_by(self, assignment: dict[str, int]) -> bool:
        together = len({assignment[item] for item in self.components}) == 1
        return together if self.kind == "KEEP_APART" else not together


def hard_constraints(architecture: Architecture) -> tuple[HardConstraint, ...]:
    return (
        *(HardConstraint("KEEP_APART", index, (rule.left, rule.right), rule.basis, rule.review_policy.protected, rule.review_policy.change_cost)
          for index, rule in enumerate(architecture.keep_apart)),
        *(HardConstraint("LOCAL_TRANSACTION", index, (edge.source, edge.target), edge.basis, edge.review_policy.protected, edge.review_policy.change_cost)
          for index, edge in enumerate(architecture.interactions) if edge.local_transaction),
        *(HardConstraint("KEEP_SHARED", index, tuple(store.members), store.basis, store.review_policy.protected, store.review_policy.change_cost)
          for index, store in enumerate(architecture.stores) if store.policy == "KEEP_SHARED" and len(store.members) > 1),
    )


def group_index(groups: tuple[tuple[str, ...], ...]) -> dict[str, int]:
    return {component_id: index for index, group in enumerate(groups, 1) for component_id in group}


def component_profiles(architecture: Architecture) -> dict[str, dict[str, list[str]]]:
    """Combine manual characteristics and ISO allocations scoped to one source NFR."""
    profiles = {
        component.id: {label: list(component.characteristic_requirements.get(label, []))
                       for label in component.characteristics}
        for component in architecture.components
    }
    by_id = {item.id: item for item in architecture.requirements}
    roots = {}
    for requirement in architecture.requirements:
        root = requirement
        while root.duplicate_of:
            root = by_id[root.duplicate_of]
        roots.setdefault(root.id, []).append(requirement.id)
    for requirement in architecture.requirements:
        if requirement.duplicate_of:
            continue
        for allocation in requirement.quality_allocations:
            label = f"{allocation.characteristic} · {requirement.id}"
            for component_id in allocation.component_ids:
                sources = profiles[component_id].setdefault(label, [])
                for source_id in roots[requirement.id]:
                    if source_id not in sources:
                        sources.append(source_id)
    return profiles


def merge_quality_requirement(architecture: Architecture, alias_id: str, target_id: str | None) -> Architecture:
    data = architecture.model_dump(mode="json")
    alias = next((item for item in data["requirements"] if item["id"] == alias_id), None)
    if alias is None or alias["kind"] != "NFR":
        raise ValueError("Chọn nguồn NFR đã khai báo để đối chiếu mục tiêu.")
    if target_id is not None:
        target = next((item for item in architecture.requirements if item.id == target_id), None)
        if target is None or target.id == alias_id or target.duplicate_of or not target.quality_allocations:
            raise ValueError("Chọn bản gốc đã có ánh xạ ISO và chưa hợp nhất vào nguồn khác.")
        for item in data["requirements"]:
            if item["duplicate_of"] == alias_id:
                item["duplicate_of"] = target_id
    alias["duplicate_of"] = target_id
    alias["quality_allocations"] = []
    return Architecture.model_validate(data)


def characteristic_index(profiles: dict[str, dict[str, list[str]]], assignment: dict[str, int]) -> tuple[dict[str, set[int]], dict[int, set[str]]]:
    locations: dict[str, set[int]] = defaultdict(set)
    labels: dict[int, set[str]] = defaultdict(set)
    for component, characteristics in profiles.items():
        group = assignment[component]
        for characteristic in characteristics:
            locations[characteristic].add(group)
            labels[group].add(characteristic)
    return dict(locations), dict(labels)


def _cost_drivers(architecture: Architecture, profiles: dict[str, dict[str, list[str]]], assignment: dict[str, int]) -> Iterator[CostDriver]:
    """Trace each contribution back to the input edge, store, or characteristic."""
    for edge in architecture.interactions:
        pair = (edge.source, edge.target)
        quanta = tuple(dict.fromkeys(assignment[component] for component in pair))
        crosses = len(quanta) > 1
        if not edge.weight:
            continue
        if edge.mode == "SYNC" and crosses:
            yield CostDriver(0, f"{edge.source} → {edge.target}", pair, quanta, edge.weight)
        if edge.mode == "ASYNC" and not crosses:
            yield CostDriver(2, f"{edge.source} → {edge.target}", pair, quanta, edge.weight)
    for store in architecture.stores:
        quanta = tuple(sorted({assignment[member] for member in store.members}))
        if len(quanta) > 1 and store.weight:
            yield CostDriver(1, store.name, tuple(store.members), quanta, store.weight * (len(quanta) - 1))
    locations, labels = characteristic_index(profiles, assignment)
    for label, quanta in sorted(locations.items()):
        if len(quanta) > 1:
            members = tuple(component for component, characteristics in profiles.items() if label in characteristics)
            yield CostDriver(3, label, members, tuple(sorted(quanta)), len(quanta) - 1)
    for group, characteristics in sorted(labels.items()):
        if len(characteristics) > 1:
            members = tuple(item for item, quantum in assignment.items() if quantum == group)
            yield CostDriver(4, ", ".join(sorted(characteristics)), members, (group,), len(characteristics) - 1)


def explain_candidate(architecture: Architecture, candidate: Candidate) -> tuple[CostDriver, ...]:
    return tuple(_cost_drivers(architecture, component_profiles(architecture), group_index(candidate.groups)))


def _evaluate(architecture: Architecture, profiles: dict[str, dict[str, list[str]]],
              rules: tuple[HardConstraint, ...], groups: tuple[tuple[str, ...], ...], index: int) -> Candidate | None:
    assignment = group_index(groups)
    if any(rule.violated_by(assignment) for rule in rules):
        return None
    totals = [0] * 5
    for driver in _cost_drivers(architecture, profiles, assignment):
        totals[driver.axis] += driver.units
    return Candidate(f"P{index:03d}", groups, *totals)


def ranking_key(candidate: Candidate, weights: Preferences, ranking: Ranking) -> tuple:
    weighted_order = (candidate.score(weights), len(candidate.groups), candidate.id)
    if ranking == "SYNC_FIRST":
        return (candidate.sync, candidate.async_seam, *weighted_order)
    if ranking == "CHARACTERISTIC_FIRST":
        return (candidate.characteristic_spread, candidate.characteristic_mix, *weighted_order)
    return weighted_order


def analyze(architecture: Architecture, weights: Preferences, *, ranking: Ranking = "WEIGHTED") -> Analysis:
    """Visit all partitions, filter hard rules, and retain the exact Pareto frontier."""
    from .studio_evidence import ensure_current_evidence

    ensure_current_evidence(architecture)
    feasible = []
    profiles = component_profiles(architecture)
    rules = hard_constraints(architecture)
    count = 0
    for count, groups in enumerate(_partitions([item.id for item in architecture.components]), 1):
        candidate = _evaluate(architecture, profiles, rules, groups, count)
        if candidate is not None:
            feasible.append(candidate)

    # Lexicographic order puts every potential dominator before the vector it dominates.
    frontier_vectors = []
    for vector in sorted({candidate.vector for candidate in feasible}):
        if not any(all(left <= right for left, right in zip(other, vector, strict=True)) for other in frontier_vectors):
            frontier_vectors.append(vector)
    eligible = set(frontier_vectors)
    frontier = tuple(candidate for candidate in feasible if candidate.vector in eligible)
    ranked = tuple(sorted(frontier, key=lambda item: ranking_key(item, weights, ranking)))
    return Analysis(count, tuple(feasible), frontier, ranked)
