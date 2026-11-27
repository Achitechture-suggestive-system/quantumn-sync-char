"""Optional-size CP-SAT optimizer for exact weighted responsibility partitions."""

from __future__ import annotations

from collections import defaultdict, deque
from decimal import Decimal
from importlib.metadata import version as package_version
from itertools import combinations
import math
from typing import Any

from ortools.sat.python import cp_model

from .models import Constraint


MAX_RESPONSIBILITIES = 50
MAX_WEIGHT_DECIMAL_PLACES = 9
MAX_OBJECTIVE_COEFFICIENT = 2**60
DEFAULT_TIME_LIMIT_SECONDS = 30.0
DEFAULT_OPTIMAL_CANDIDATE_LIMIT = 200


class CPSatOptimizerError(ValueError):
    """Raised when a partition problem cannot be represented safely in CP-SAT."""


def _bell_number(size: int) -> int:
    stirling = [1]
    for n in range(1, size + 1):
        next_row = [0] * (n + 1)
        for k in range(1, n + 1):
            same_groups = k * stirling[k] if k < len(stirling) else 0
            next_row[k] = stirling[k - 1] + same_groups
        stirling = next_row
    return sum(stirling)


def _scaled_soft_weights(constraints: list[Constraint]) -> tuple[int, dict[str, int]]:
    active = [item for item in constraints if item.enabled and item.hardness == "SOFT"]
    decimal_weights: dict[str, Decimal] = {}
    places = 0
    for item in active:
        try:
            weight = Decimal(str(item.weight))
        except Exception as exc:  # Decimal accepts a narrow set of values; fail with a domain error.
            raise CPSatOptimizerError(f"Constraint {item.id} has a non-decimal weight.") from exc
        if not weight.is_finite() or weight < 0:
            raise CPSatOptimizerError(f"Constraint {item.id} weight must be a finite non-negative decimal.")
        places = max(places, max(0, -weight.as_tuple().exponent))
        decimal_weights[item.id] = weight
    if places > MAX_WEIGHT_DECIMAL_PLACES:
        raise CPSatOptimizerError(
            f"CP-SAT supports at most {MAX_WEIGHT_DECIMAL_PLACES} decimal places in soft weights without rounding."
        )
    scale = 10**places
    scaled = {constraint_id: int(weight * scale) for constraint_id, weight in decimal_weights.items()}
    upper_bound = sum(scaled.values())
    if upper_bound > MAX_OBJECTIVE_COEFFICIENT:
        raise CPSatOptimizerError("Scaled soft-weight sum exceeds the safe CP-SAT signed-integer range.")
    return scale, scaled


def _hard_conflict_explanations(constraints: list[Constraint]) -> list[dict[str, Any]]:
    hard = [item for item in constraints if item.enabled and item.hardness == "HARD"]
    must_edges: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for item in hard:
        if item.relation == "MUST_LINK" and item.left != item.right:
            must_edges[item.left].append((item.right, item.id))
            must_edges[item.right].append((item.left, item.id))
    for neighbors in must_edges.values():
        neighbors.sort(key=lambda value: (value[0], value[1]))

    conflicts = []
    for cannot in hard:
        if cannot.relation != "CANNOT_LINK":
            continue
        queue = deque([cannot.left])
        previous: dict[str, tuple[str, str] | None] = {cannot.left: None}
        while queue and cannot.right not in previous:
            current = queue.popleft()
            for neighbor, constraint_id in must_edges.get(current, []):
                if neighbor not in previous:
                    previous[neighbor] = (current, constraint_id)
                    queue.append(neighbor)
        if cannot.right not in previous:
            continue
        path_ids = []
        cursor = cannot.right
        while cursor != cannot.left:
            prior, constraint_id = previous[cursor]  # type: ignore[misc]
            path_ids.append(constraint_id)
            cursor = prior
        constraint_ids = list(dict.fromkeys([*reversed(path_ids), cannot.id]))
        conflicts.append(
            {
                "pair": sorted((cannot.left, cannot.right)),
                "constraint_ids": constraint_ids,
                "relations": ["CANNOT_LINK", "MUST_LINK"],
                "status": "INFEASIBLE",
                "reason": "Cannot-link endpoints are connected by the must-link transitive closure.",
                "explanation_scope": "INCLUSION_MINIMAL_MUST_LINK_PATH_PLUS_CANNOT_LINK",
            }
        )
    return conflicts


def _partition_signature(groups: list[list[str]]) -> tuple[tuple[str, ...], ...]:
    return tuple(sorted((tuple(sorted(group)) for group in groups), key=lambda group: group[0]))


def _groups_from_values(
    responsibility_ids: list[str], pair_vars: dict[tuple[int, int], cp_model.IntVar], value_of: Any
) -> list[list[str]]:
    parent = list(range(len(responsibility_ids)))

    def root(index: int) -> int:
        while parent[index] != index:
            parent[index] = parent[parent[index]]
            index = parent[index]
        return index

    def union(left: int, right: int) -> None:
        left_root, right_root = root(left), root(right)
        if left_root != right_root:
            parent[right_root] = left_root

    for (left, right), variable in pair_vars.items():
        if value_of(variable):
            union(left, right)
    groups: dict[int, list[str]] = defaultdict(list)
    for index, responsibility_id in enumerate(responsibility_ids):
        groups[root(index)].append(responsibility_id)
    return [list(group) for group in _partition_signature(list(groups.values()))]


def _cost_int(
    groups: list[list[str]], constraints: list[Constraint], scaled_weights: dict[str, int]
) -> int:
    membership = {responsibility_id: index for index, group in enumerate(groups) for responsibility_id in group}
    total = 0
    for item in constraints:
        if not item.enabled or item.hardness != "SOFT":
            continue
        together = item.left == item.right or membership[item.left] == membership[item.right]
        violated = (item.relation == "MUST_LINK" and not together) or (
            item.relation == "CANNOT_LINK" and together
        )
        if violated:
            total += scaled_weights[item.id]
    return total


def _build_model(
    responsibility_ids: list[str],
    constraints: list[Constraint],
    scaled_weights: dict[str, int],
    *,
    fixed_objective: int | None = None,
):
    model = cp_model.CpModel()
    pair_vars: dict[tuple[int, int], cp_model.IntVar] = {}
    for left, right in combinations(range(len(responsibility_ids)), 2):
        pair_vars[left, right] = model.new_bool_var(f"same_{left}_{right}")

    def same_var(left_id: str, right_id: str):
        if left_id == right_id:
            return 1
        left = responsibility_ids.index(left_id)
        right = responsibility_ids.index(right_id)
        return pair_vars[min(left, right), max(left, right)]

    for left, middle, right in combinations(range(len(responsibility_ids)), 3):
        left_middle = pair_vars[left, middle]
        middle_right = pair_vars[middle, right]
        left_right = pair_vars[left, right]
        model.add(left_middle + middle_right - left_right <= 1)
        model.add(left_middle + left_right - middle_right <= 1)
        model.add(middle_right + left_right - left_middle <= 1)

    for item in constraints:
        if not item.enabled:
            continue
        together = same_var(item.left, item.right)
        if item.hardness == "HARD":
            model.add(together == (1 if item.relation == "MUST_LINK" else 0))

    violation_vars = []
    violation_weights = []
    for index, item in enumerate(constraints):
        if not item.enabled or item.hardness != "SOFT":
            continue
        violation = model.new_bool_var(f"violation_{index}")
        together = same_var(item.left, item.right)
        if item.relation == "MUST_LINK":
            model.add(violation + together == 1)
        else:
            model.add(violation == together)
        violation_vars.append(violation)
        violation_weights.append(scaled_weights[item.id])

    objective = sum(weight * variable for weight, variable in zip(violation_weights, violation_vars, strict=True))
    if fixed_objective is None:
        model.minimize(objective)
    else:
        model.add(objective == fixed_objective)
    return model, pair_vars, objective


class _OptimalPartitionCollector(cp_model.CpSolverSolutionCallback):
    def __init__(self, responsibility_ids, pair_vars, candidate_limit, initial_groups):
        super().__init__()
        self.responsibility_ids = responsibility_ids
        self.pair_vars = pair_vars
        self.candidate_limit = candidate_limit
        self.groups_by_signature: dict[tuple[tuple[str, ...], ...], list[list[str]]] = {
            _partition_signature(initial_groups): initial_groups
        }
        self.limit_reached = False

    def on_solution_callback(self) -> None:
        groups = _groups_from_values(self.responsibility_ids, self.pair_vars, self.value)
        self.groups_by_signature.setdefault(_partition_signature(groups), groups)
        if len(self.groups_by_signature) >= self.candidate_limit:
            self.limit_reached = True
            self.stop_search()


def optimize_with_cpsat(
    responsibility_ids: list[str],
    constraints: list[Constraint],
    preferred_partition: list[list[str]] | None = None,
    selection_policy: str = "FIRST_OPTIMAL",
    *,
    time_limit_seconds: float = DEFAULT_TIME_LIMIT_SECONDS,
    max_optimal_candidates: int = DEFAULT_OPTIMAL_CANDIDATE_LIMIT,
    random_seed: int = 0,
) -> dict[str, Any]:
    """Minimize the declared pairwise disagreement objective and enumerate proven optima."""
    if len(responsibility_ids) != len(set(responsibility_ids)):
        raise CPSatOptimizerError("Responsibility IDs must be unique.")
    if len(responsibility_ids) > MAX_RESPONSIBILITIES:
        raise CPSatOptimizerError(f"CP-SAT is capped at {MAX_RESPONSIBILITIES} responsibilities.")
    try:
        normalized_time_limit = float(time_limit_seconds)
    except (TypeError, ValueError, OverflowError) as exc:
        raise CPSatOptimizerError("Time limit must be a finite positive number.") from exc
    if not math.isfinite(normalized_time_limit) or normalized_time_limit <= 0:
        raise CPSatOptimizerError("Time limit must be a finite positive number.")
    if isinstance(max_optimal_candidates, bool) or not isinstance(max_optimal_candidates, int) or max_optimal_candidates < 1:
        raise CPSatOptimizerError("Optimal-candidate limit must be a positive integer.")
    if isinstance(random_seed, bool) or not isinstance(random_seed, int) or not 0 <= random_seed <= 2**31 - 1:
        raise CPSatOptimizerError("Random seed must be an integer from 0 through 2^31-1.")
    responsibility_ids = sorted(responsibility_ids)
    known = set(responsibility_ids)
    if any({item.left, item.right} - known for item in constraints):
        raise CPSatOptimizerError("Every constraint endpoint must name a known responsibility.")
    constraint_ids = [item.id for item in constraints]
    if len(constraint_ids) != len(set(constraint_ids)):
        raise CPSatOptimizerError("Constraint IDs must be unique for reproducible rule evaluation.")
    scale, scaled_weights = _scaled_soft_weights(constraints)
    solver_parameters = {
        "time_limit_seconds": normalized_time_limit,
        "random_seed": random_seed,
        "num_search_workers": 1,
        "max_optimal_candidates": max_optimal_candidates,
        "objective_weight_scale": scale,
        "max_weight_decimal_places": MAX_WEIGHT_DECIMAL_PLACES,
    }
    base = {
        "solver_backend": "CP_SAT",
        "solver_version": package_version("ortools"),
        "solver_parameters": solver_parameters,
        "enumerated_partition_count": None,
        "bell_number_expected": _bell_number(len(responsibility_ids)),
        "feasible_candidate_count": None,
        "feasible_candidates": [],
        "candidate_reporting_scope": "OPTIMAL_CANDIDATES_ONLY",
        "optimal_candidate_set_complete": False,
        "objective_definition": "J = sum of weights for violated enabled SOFT constraints.",
        "conflicts": [],
        "optimal_candidates": [],
        "optimal_candidate_count": 0,
        "selected_candidate_id": None,
        "selected_groups": None,
        "selection_policy": selection_policy,
        "objective_minimum": None,
    }
    if not responsibility_ids:
        base.update(
            result_status="REVIEW_REQUIRED",
            solver_status="NOT_RUN_EMPTY_RESPONSIBILITY_SET",
            interpretation="No responsibility survived review; no partition was generated.",
        )
        return base

    model, pair_vars, _ = _build_model(responsibility_ids, constraints, scaled_weights)
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = normalized_time_limit
    solver.parameters.random_seed = random_seed
    solver.parameters.num_search_workers = 1
    status = solver.solve(model)
    status_name = {
        cp_model.OPTIMAL: "OPTIMAL",
        cp_model.FEASIBLE: "FEASIBLE",
        cp_model.INFEASIBLE: "INFEASIBLE",
        cp_model.MODEL_INVALID: "MODEL_INVALID",
        cp_model.UNKNOWN: "UNKNOWN",
    }.get(status, "UNKNOWN")
    base["solver_status"] = status_name
    base["solver_wall_time_seconds"] = solver.wall_time

    if status == cp_model.INFEASIBLE:
        conflicts = _hard_conflict_explanations(constraints)
        if not conflicts:
            conflicts = [
                {
                    "pair": [],
                    "constraint_ids": [item.id for item in constraints if item.enabled and item.hardness == "HARD"],
                    "relations": sorted({item.relation for item in constraints if item.enabled and item.hardness == "HARD"}),
                    "status": "INFEASIBLE",
                    "reason": "CP-SAT proved the declared hard constraints infeasible; no must-link path core was identified.",
                    "explanation_scope": "SOLVER_PROOF_WITHOUT_MINIMAL_CORE",
                }
            ]
        base.update(
            conflicts=conflicts,
            feasible_candidate_count=0,
            result_status="INFEASIBLE",
            interpretation="CP-SAT proved infeasibility for the declared hard constraints; this does not validate their justification.",
        )
        return base

    if status != cp_model.OPTIMAL:
        base.update(
            result_status="REVIEW_REQUIRED",
            interpretation="No optimality proof was obtained within the solver limit; no optimum is reported.",
        )
        return base

    initial_groups = _groups_from_values(responsibility_ids, pair_vars, solver.value)
    optimum_int = _cost_int(initial_groups, constraints, scaled_weights)
    enumeration_model, enumeration_pairs, _ = _build_model(
        responsibility_ids,
        constraints,
        scaled_weights,
        fixed_objective=optimum_int,
    )
    collector = _OptimalPartitionCollector(
        responsibility_ids,
        enumeration_pairs,
        max_optimal_candidates,
        initial_groups,
    )
    enumeration_solver = cp_model.CpSolver()
    enumeration_solver.parameters.max_time_in_seconds = normalized_time_limit
    enumeration_solver.parameters.random_seed = random_seed
    enumeration_solver.parameters.num_search_workers = 1
    enumeration_solver.parameters.enumerate_all_solutions = True
    enumeration_status = enumeration_solver.solve(enumeration_model, collector)
    signatures = collector.groups_by_signature
    optimal_set_complete = enumeration_status == cp_model.OPTIMAL and not collector.limit_reached
    objective_decimal = Decimal(optimum_int) / Decimal(scale)
    candidates = []
    for index, signature in enumerate(sorted(signatures), start=1):
        groups = signatures[signature]
        candidates.append(
            {
                "candidate_id": f"P{index:03d}",
                "groups": groups,
                "objective_cost": float(objective_decimal),
                "is_optimal": True,
                "candidate_kind": "OPTIMAL_PARTITION_CANDIDATE",
            }
        )
    preferred = next(
        (
            item
            for item in candidates
            if preferred_partition is not None
            and _partition_signature(preferred_partition) == _partition_signature(item["groups"])
        ),
        None,
    )
    if preferred is not None:
        selected = preferred
        effective_selection_policy = "PREFERRED_PARTITION"
    elif selection_policy == "MAXIMUM_GROUPS":
        selected = max(candidates, key=lambda item: len(item["groups"]))
        effective_selection_policy = selection_policy
    else:
        selected = candidates[0]
        effective_selection_policy = selection_policy
    base.update(
        objective_minimum=float(objective_decimal),
        optimal_candidates=candidates,
        optimal_candidate_count=len(candidates),
        optimal_candidate_set_complete=optimal_set_complete,
        selected_candidate_id=selected["candidate_id"],
        selected_groups=selected["groups"],
        selection_policy=effective_selection_policy,
        reported_candidates=candidates,
        optimal_enumeration_status={
            "solver_status": {
                cp_model.OPTIMAL: "OPTIMAL",
                cp_model.FEASIBLE: "FEASIBLE",
                cp_model.UNKNOWN: "UNKNOWN",
            }.get(enumeration_status, "OTHER"),
            "candidate_limit_reached": collector.limit_reached,
            "wall_time_seconds": enumeration_solver.wall_time,
        },
        result_status="REVIEW_REQUIRED",
        interpretation=(
            "CP-SAT proved the minimum for the declared objective. Only optima are reported; the feasible set is not exhaustively enumerated. "
            "The selected partition is a deterministic display candidate, not an architecture recommendation."
        ),
    )
    return base


def analyze_weight_sensitivity(
    responsibility_ids: list[str],
    constraints: list[Constraint],
    scenarios: dict[str, dict[str, float]],
    *,
    time_limit_seconds: float = DEFAULT_TIME_LIMIT_SECONDS,
    max_optimal_candidates: int = DEFAULT_OPTIMAL_CANDIDATE_LIMIT,
    random_seed: int = 0,
) -> dict[str, Any]:
    """Compare explicit soft-weight assignments without changing the source constraints."""
    soft_by_id = {item.id: item for item in constraints if item.enabled and item.hardness == "SOFT"}
    results = []
    for scenario_name, weight_updates in scenarios.items():
        unknown_ids = set(weight_updates) - set(soft_by_id)
        if unknown_ids:
            raise CPSatOptimizerError(f"Weight scenario {scenario_name} names unknown/non-soft constraints: {sorted(unknown_ids)}.")
        scenario_constraints = []
        for item in constraints:
            values = item.model_dump(mode="json")
            if item.id in weight_updates:
                values["weight"] = weight_updates[item.id]
            scenario_constraints.append(Constraint.model_validate(values))
        optimized = optimize_with_cpsat(
            responsibility_ids,
            scenario_constraints,
            time_limit_seconds=time_limit_seconds,
            max_optimal_candidates=max_optimal_candidates,
            random_seed=random_seed,
        )
        results.append(
            {
                "scenario": scenario_name,
                "weight_assignments": {
                    item.id: item.weight
                    for item in scenario_constraints
                    if item.enabled and item.hardness == "SOFT"
                },
                "solver_status": optimized["solver_status"],
                "result_status": optimized["result_status"],
                "objective_minimum": optimized["objective_minimum"],
                "optimal_candidates": optimized["optimal_candidates"],
                "optimal_candidate_set_complete": optimized["optimal_candidate_set_complete"],
                "reported_candidate_count": optimized["optimal_candidate_count"],
            }
        )
    return {
        "provenance": "DETERMINISTIC_TRANSFORMATION",
        "analysis_status": "SCENARIO_COMPARISON_ONLY",
        "interpretation": "Weight scenarios are analyst-specified sensitivity inputs, not empirical or domain-validated weight ranges.",
        "scenarios": results,
    }
