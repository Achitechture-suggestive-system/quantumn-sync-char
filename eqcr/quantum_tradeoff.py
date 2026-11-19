"""Compare architecture partitions under explicit coupling and quality preferences."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from collections.abc import Iterator
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

from .pipeline import _partitions


Key = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=32, pattern=r"^[A-Za-z][A-Za-z0-9_-]*$")]
Label = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]
Cost = Annotated[int, Field(ge=0, le=10)]


class InputModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Component(InputModel):
    id: Key
    name: Label
    characteristics: list[Label] = Field(default_factory=list, max_length=12)


class Interaction(InputModel):
    source: Key
    target: Key
    mode: Literal["SYNC", "ASYNC", "UNKNOWN"]
    weight: Cost = 1
    local_transaction: bool = False
    basis: str = Field(default="", max_length=240)

    @model_validator(mode="after")
    def check_coupling(self):
        if self.source == self.target:
            raise ValueError("Hai đầu của quan hệ phải là component khác nhau.")
        if self.local_transaction and (self.mode != "SYNC" or not self.basis.strip()):
            raise ValueError("Giao dịch cục bộ cần quan hệ SYNC và căn cứ rõ ràng.")
        return self


class DataStore(InputModel):
    id: Key
    name: Label
    members: list[Key] = Field(min_length=1, max_length=8)
    policy: Literal["KEEP_SHARED", "SPLITTABLE"]
    weight: Cost = 1
    basis: str = Field(default="", max_length=240)

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


class Architecture(InputModel):
    components: list[Component] = Field(min_length=1, max_length=8)
    interactions: list[Interaction] = Field(default_factory=list, max_length=56)
    stores: list[DataStore] = Field(default_factory=list, max_length=16)
    keep_apart: list[SeparatePair] = Field(default_factory=list, max_length=28)

    @model_validator(mode="after")
    def check_references(self):
        ids = {item.id for item in self.components}
        if len(ids) != len(self.components):
            raise ValueError("ID component phải duy nhất.")
        if len({item.id for item in self.stores}) != len(self.stores):
            raise ValueError("ID kho dữ liệu phải duy nhất.")
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


def group_index(groups: tuple[tuple[str, ...], ...]) -> dict[str, int]:
    return {component_id: index for index, group in enumerate(groups, 1) for component_id in group}


def characteristic_index(architecture: Architecture, assignment: dict[str, int]) -> tuple[dict[str, set[int]], dict[int, set[str]]]:
    locations: dict[str, set[int]] = defaultdict(set)
    labels: dict[int, set[str]] = defaultdict(set)
    for component in architecture.components:
        group = assignment[component.id]
        for characteristic in component.characteristics:
            locations[characteristic].add(group)
            labels[group].add(characteristic)
    return dict(locations), dict(labels)


def _cost_drivers(architecture: Architecture, assignment: dict[str, int]) -> Iterator[CostDriver]:
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
    locations, labels = characteristic_index(architecture, assignment)
    for label, quanta in sorted(locations.items()):
        if len(quanta) > 1:
            members = tuple(item.id for item in architecture.components if label in item.characteristics)
            yield CostDriver(3, label, members, tuple(sorted(quanta)), len(quanta) - 1)
    for group, characteristics in sorted(labels.items()):
        if len(characteristics) > 1:
            members = tuple(item for item, quantum in assignment.items() if quantum == group)
            yield CostDriver(4, ", ".join(sorted(characteristics)), members, (group,), len(characteristics) - 1)


def explain_candidate(architecture: Architecture, candidate: Candidate) -> tuple[CostDriver, ...]:
    return tuple(_cost_drivers(architecture, group_index(candidate.groups)))


def _evaluate(architecture: Architecture, groups: tuple[tuple[str, ...], ...], index: int) -> Candidate | None:
    assignment = group_index(groups)
    if any(assignment[rule.left] == assignment[rule.right] for rule in architecture.keep_apart):
        return None
    if any(edge.local_transaction and assignment[edge.source] != assignment[edge.target]
           for edge in architecture.interactions):
        return None
    if any(store.policy == "KEEP_SHARED" and len({assignment[item] for item in store.members}) > 1
           for store in architecture.stores):
        return None
    totals = [0] * 5
    for driver in _cost_drivers(architecture, assignment):
        totals[driver.axis] += driver.units
    return Candidate(f"P{index:03d}", groups, *totals)


def analyze(architecture: Architecture, weights: Preferences) -> Analysis:
    """Visit all partitions, filter hard rules, and retain the exact Pareto frontier."""
    feasible = []
    count = 0
    for count, groups in enumerate(_partitions([item.id for item in architecture.components]), 1):
        candidate = _evaluate(architecture, groups, count)
        if candidate is not None:
            feasible.append(candidate)

    # Lexicographic order puts every potential dominator before the vector it dominates.
    frontier_vectors = []
    for vector in sorted({candidate.vector for candidate in feasible}):
        if not any(all(left <= right for left, right in zip(other, vector, strict=True)) for other in frontier_vectors):
            frontier_vectors.append(vector)
    eligible = set(frontier_vectors)
    frontier = tuple(candidate for candidate in feasible if candidate.vector in eligible)
    ranked = tuple(sorted(frontier, key=lambda item: (item.score(weights), len(item.groups), item.id)))
    return Analysis(count, tuple(feasible), frontier, ranked)
