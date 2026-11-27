"""Bounded Studio CP-SAT search with the same five costs, not the research pairwise objective."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, replace
from hashlib import sha256
from importlib.metadata import version
from itertools import combinations
import json
import math
import time

from ortools.sat.python import cp_model

from .quantum_tradeoff import (Analysis, Architecture, Candidate, Preferences, _evaluate, component_profiles,
                               group_index, hard_constraints, ranking_key)
from .studio_uncertainty import possible_modes, score_bounds


SEED = 611
SAFE_OBJECTIVE = 2**60


def hard_blocks(ids, rules):
    parent = {item: item for item in ids}

    def root(item):
        while parent[item] != item:
            parent[item] = parent[parent[item]]
            item = parent[item]
        return item

    for rule in rules:
        if rule.kind != "KEEP_APART":
            for item in rule.components[1:]:
                parent[root(item)] = root(rule.components[0])
    groups = defaultdict(list)
    for item in ids:
        groups[root(item)].append(item)
    conflict = any(root(rule.components[0]) == root(rule.components[1]) for rule in rules if rule.kind == "KEEP_APART")
    return tuple(tuple(group) for group in groups.values()), conflict


def partition_variables(model, size):
    """Restricted-growth labels: exactly one representation of each unlabeled partition."""
    groups = [model.new_int_var(0, index, f"group_{index}") for index in range(size)]
    previous_max = groups[0]
    for index in range(1, size):
        model.add(groups[index] <= previous_max + 1)
        current_max = model.new_int_var(0, index, f"prefix_max_{index}")
        model.add_max_equality(current_max, [previous_max, groups[index]])
        previous_max = current_max
    membership = {}
    for index, group in enumerate(groups):
        for slot in range(index + 1):
            bit = model.new_bool_var(f"in_{index}_{slot}")
            model.add(group == slot).only_enforce_if(bit)
            model.add(group != slot).only_enforce_if(~bit)
            membership[index, slot] = bit
        model.add_exactly_one([membership[index, slot] for slot in range(index + 1)])
    return groups, membership


@dataclass
class Compiled:
    model: cp_model.CpModel
    blocks: tuple
    groups: list
    axes: list
    bounds: tuple[int, ...]
    group_count: object
    weighted: object
    weighted_bound: int
    lower: object
    upper: object
    uncertain_bound: int

    def partition(self, value_of):
        found = defaultdict(list)
        for block, variable in zip(self.blocks, self.groups, strict=True):
            found[value_of(variable)].extend(block)
        return tuple(sorted(tuple(sorted(group)) for group in found.values()))


def compile_partition(architecture: Architecture, weights: Preferences) -> Compiled:
    ids = [item.id for item in architecture.components]
    rules = hard_constraints(architecture)
    blocks, conflict = hard_blocks(ids, rules)
    if conflict:
        raise ValueError("Hard constraints conflict before compilation.")
    model = cp_model.CpModel()
    groups, membership = partition_variables(model, len(blocks))
    block_of = {item: index for index, block in enumerate(blocks) for item in block}
    for rule in rules:
        if rule.kind == "KEEP_APART":
            model.add(groups[block_of[rule.components[0]]] != groups[block_of[rule.components[1]]])
    same_cache, presence_cache = {}, {}

    def same(left, right):
        pair = tuple(sorted((block_of[left], block_of[right])))
        if pair[0] == pair[1]:
            return 1
        if pair not in same_cache:
            bit = model.new_bool_var(f"same_{pair[0]}_{pair[1]}")
            model.add(groups[pair[0]] == groups[pair[1]]).only_enforce_if(bit)
            model.add(groups[pair[0]] != groups[pair[1]]).only_enforce_if(~bit)
            same_cache[pair] = bit
        return same_cache[pair]

    def presence(members, slot):
        indices = tuple(sorted(set(members)))
        key = indices, slot
        if key not in presence_cache:
            bits = [membership[index, slot] for index in indices if (index, slot) in membership]
            if len(bits) < 2:
                presence_cache[key] = bits[0] if bits else 0
            else:
                bit = model.new_bool_var(f"present_{len(presence_cache)}")
                model.add_max_equality(bit, bits)
                presence_cache[key] = bit
        return presence_cache[key]

    slots = range(len(blocks))
    used = [presence(range(len(blocks)), slot) for slot in slots]
    group_count = sum(used)
    terms = [[], [], [], [], []]
    bounds = [0] * 5
    for edge in architecture.interactions:
        if edge.mode in {"SYNC", "ASYNC"}:
            axis = 0 if edge.mode == "SYNC" else 2
            together = same(edge.source, edge.target)
            terms[axis].append(edge.weight * (1 - together if axis == 0 else together))
            bounds[axis] += edge.weight
    for store in architecture.stores:
        members = {block_of[item] for item in store.members}
        terms[1].append(store.weight * (sum(presence(members, slot) for slot in slots) - 1))
        bounds[1] += store.weight * (len(members) - 1)
    profiles = component_profiles(architecture)
    label_blocks = defaultdict(set)
    for item, labels in profiles.items():
        for label in labels:
            label_blocks[label].add(block_of[item])
    label_presence = [presence(members, slot) for members in label_blocks.values() for slot in slots]
    all_labeled = set().union(*label_blocks.values()) if label_blocks else set()
    terms[3] = [sum(label_presence) - len(label_blocks)]
    terms[4] = [sum(label_presence) - sum(presence(all_labeled, slot) for slot in slots)]
    bounds[3] = sum(len(members) - 1 for members in label_blocks.values())
    bounds[4] = max(0, sum(len(members) for members in label_blocks.values()) - int(bool(label_blocks)))
    axes = [model.new_int_var(0, bound, f"axis_{axis}") for axis, bound in enumerate(bounds)]
    for axis, values in enumerate(terms):
        model.add(axes[axis] == sum(values))
    weighted = sum(axis * weight for axis, weight in zip(axes, weights.vector, strict=True))
    weighted_bound = sum(bound * weight for bound, weight in zip(bounds, weights.vector, strict=True))
    upper_extra, lower_extra, uncertainty = [], [], 0
    for edge in architecture.interactions:
        if edge.mode != "UNKNOWN":
            continue
        modes = possible_modes(architecture, edge)
        together = same(edge.source, edge.target)
        contribution = (edge.weight * weights.sync * (1 - together) if "SYNC" in modes else 0)
        contribution += edge.weight * weights.async_seam * together if "ASYNC" in modes else 0
        upper_extra.append(contribution)
        if len(modes) == 1:
            lower_extra.append(contribution)
        uncertainty += edge.weight * max(weights.sync, weights.async_seam)
    return Compiled(model, blocks, groups, axes, tuple(bounds), group_count, weighted, weighted_bound,
                    weighted + sum(lower_extra), weighted + sum(upper_extra), weighted_bound + uncertainty)


def lexicographic(terms):
    expression, bound = 0, 0
    for term, upper_bound in terms:
        next_bound = bound * (upper_bound + 1) + upper_bound
        if next_bound > SAFE_OBJECTIVE:
            raise ValueError("Studio objective vượt miền integer an toàn; không làm tròn hoặc đổi trọng số.")
        expression = expression * (upper_bound + 1) + term
        bound = next_bound
    return expression


def primary_terms(compiled, ranking, conservative=False):
    ending = [(compiled.group_count, len(compiled.blocks))]
    if conservative:
        return [(compiled.upper, compiled.uncertain_bound), (compiled.lower, compiled.uncertain_bound), *ending]
    prefixes = {"SYNC_FIRST": [0, 2], "CHARACTERISTIC_FIRST": [3, 4], "WEIGHTED": []}[ranking]
    return [(compiled.axes[index], compiled.bounds[index]) for index in prefixes] + [(compiled.weighted, compiled.weighted_bound), *ending]


def candidate_for_groups(architecture, groups, profiles=None, rules=None):
    canonical = tuple(sorted(tuple(sorted(group)) for group in groups))
    item = _evaluate(architecture, profiles or component_profiles(architecture), hard_constraints(architecture) if rules is None else rules, canonical, 0)
    if item is None:
        raise ValueError("Solver candidate violates a declared hard rule.")
    signature = sha256(json.dumps(canonical).encode()).hexdigest()[:16]
    return replace(item, id=f"CP-{signature}")


def seed_partitions(architecture, blocks, rules=None):
    """Validated feasible starting points, not LLM proposals or exhaustive search."""
    rules = hard_constraints(architecture) if rules is None else rules
    forbidden = {frozenset(rule.components) for rule in rules if rule.kind == "KEEP_APART"}

    def compatible(left, right):
        return all(frozenset((a, b)) not in forbidden for a in left for b in right)

    yield blocks
    count = 0
    for left, right in combinations(range(len(blocks)), 2):
        if compatible(blocks[left], blocks[right]):
            yield (tuple([*blocks[left], *blocks[right]]), *(block for index, block in enumerate(blocks) if index not in {left, right}))
            count += 1
            if count == 2:
                break
    clusters = []
    for block in blocks:
        target = next((group for group in clusters if compatible(group, block)), None)
        if target is None:
            clusters.append(list(block))
        else:
            target.extend(block)
    yield tuple(tuple(group) for group in clusters)
    profiles = component_profiles(architecture)
    clusters, fingerprints = [], []
    for block in blocks:
        fingerprint = frozenset(label for item in block for label in profiles[item])
        target = next((index for index, group in enumerate(clusters) if fingerprints[index] == fingerprint and compatible(group, block)), None)
        if target is None:
            clusters.append(list(block))
            fingerprints.append(fingerprint)
        else:
            clusters[target].extend(block)
    yield tuple(tuple(group) for group in clusters)

    def merge_affinities(pairs):
        clusters = {index: list(block) for index, block in enumerate(blocks)}
        owner = {item: index for index, block in clusters.items() for item in block}
        for left, right in pairs:
            a, b = owner[left], owner[right]
            if a != b and compatible(clusters[a], clusters[b]):
                for item in clusters[b]:
                    owner[item] = a
                clusters[a].extend(clusters.pop(b))
        return tuple(tuple(group) for group in clusters.values())

    yield merge_affinities((edge.source, edge.target) for edge in sorted(architecture.interactions, key=lambda item: -item.weight)
                           if edge.mode == "SYNC" and edge.weight)
    yield merge_affinities((store.members[0], member) for store in sorted(architecture.stores, key=lambda item: -item.weight)
                           if store.weight for member in store.members[1:])


def pool_analysis(candidates, ranking, weights, report):
    values = tuple(candidates.values())
    vectors = {item.vector for item in values}
    nondominated = {vector for vector in vectors if not any(other != vector and all(a <= b for a, b in zip(other, vector, strict=True)) for other in vectors)}
    frontier = tuple(item for item in values if item.vector in nondominated)
    return Analysis(None, values, frontier, tuple(sorted(frontier, key=lambda item: ranking_key(item, weights, ranking))), report)


def analyze_cpsat(architecture: Architecture, weights: Preferences, *, ranking="WEIGHTED", conservative=False,
                  time_limit_seconds=8.0) -> Analysis:
    from .studio_evidence import ensure_current_evidence

    ensure_current_evidence(architecture)
    if not math.isfinite(time_limit_seconds) or not 0 < time_limit_seconds <= 60:
        raise ValueError("Chọn thời hạn Studio lớn hơn 0 và không quá 60 giây.")
    started = time.monotonic()
    deadline = started + time_limit_seconds
    blocks, conflict = hard_blocks([item.id for item in architecture.components], hard_constraints(architecture))
    report = {"backend": "CP-SAT", "solver_version": version("ortools"), "seed": SEED, "workers": 1,
              "status": "INFEASIBLE" if conflict else "FEASIBLE", "primary_status": "NOT_RUN", "optimality_proven": False,
              "frontier_scope": "FOUND_POOL", "complete_feasible_set": False, "time_limit_seconds": time_limit_seconds,
              "conservative": conservative, "ranking": ranking, "attempts": [], "cost_validation": "PYTHON_RECOMPUTED",
              "tie_policy": "GROUP_COUNT_THEN_FOUND_POOL_ID; GLOBAL_PARETO_NOT_ENUMERATED"}
    report["optimality_scope"] = "REQUESTED_PRIMARY_COSTS; GLOBAL_PARETO_AND_ID_TIES_NOT_PROVEN"
    if conflict:
        report.update(infeasibility_proof="MUST_LINK_CLOSURE_CONFLICTS_WITH_KEEP_APART", elapsed_seconds=time.monotonic() - started)
        return Analysis(None, (), (), (), report)
    profiles, rules = component_profiles(architecture), hard_constraints(architecture)
    candidates = {}
    for groups in seed_partitions(architecture, blocks):
        item = candidate_for_groups(architecture, groups, profiles, rules)
        candidates[item.id] = item
    compiled = compile_partition(architecture, weights)
    default = Preferences().vector
    default_expr = sum(value * weight for value, weight in zip(compiled.axes, default, strict=True))
    default_bound = sum(value * weight for value, weight in zip(compiled.bounds, default, strict=True))
    objectives = [("REQUESTED", primary_terms(compiled, ranking, conservative)),
                  ("DEFAULT_WEIGHTED", [(default_expr, default_bound), (compiled.group_count, len(blocks))])]
    objectives += [(f"AXIS_{index}", [(compiled.axes[index], compiled.bounds[index]), (compiled.weighted, compiled.weighted_bound),
                                    (compiled.group_count, len(blocks))]) for index in range(5)]
    hint = min(candidates.values(), key=lambda item: (score_bounds(architecture, item, weights).upper if conservative else ranking_key(item, weights, ranking)))
    for index, (name, terms) in enumerate(objectives):
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            break
        compiled.model.minimize(lexicographic(terms))
        compiled.model.clear_hints()
        assignment = group_index(hint.groups)
        labels = {}
        for block, variable in zip(blocks, compiled.groups, strict=True):
            label = labels.setdefault(assignment[block[0]], len(labels))
            compiled.model.add_hint(variable, label)
        if problem := compiled.model.validate():
            raise ValueError(f"Studio CP-SAT model invalid: {problem}")
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = remaining * .65 if index == 0 else remaining / (len(objectives) - index)
        solver.parameters.num_search_workers = 1
        solver.parameters.random_seed = SEED
        solver.parameters.absolute_gap_limit = 0
        solver.parameters.relative_gap_limit = 0
        status = solver.solve(compiled.model)
        status_name = solver.status_name(status)
        numeric_bound = solver.best_objective_bound
        attempt = {"objective": name, "solver_status": status_name, "wall_seconds": solver.wall_time,
                   "branches": solver.num_branches, "best_bound_numeric": numeric_bound if math.isfinite(numeric_bound) else None}
        report["attempts"].append(attempt)
        if index == 0:
            report["primary_status"] = status_name
            report["optimality_proven"] = status == cp_model.OPTIMAL
            report["status"] = "OPTIMAL" if report["optimality_proven"] else "FEASIBLE"
        if status in {cp_model.INFEASIBLE, cp_model.MODEL_INVALID}:
            raise ValueError("CP-SAT rejected a model with a Python-validated feasible seed; objective/constraint mismatch.")
        if status not in {cp_model.OPTIMAL, cp_model.FEASIBLE}:
            continue
        item = candidate_for_groups(architecture, compiled.partition(solver.value), profiles, rules)
        if tuple(solver.value(axis) for axis in compiled.axes) != item.vector:
            raise ValueError("CP-SAT cost vector differs from the Python cost drivers.")
        bounds = score_bounds(architecture, item, weights)
        if (solver.value(compiled.lower), solver.value(compiled.upper)) != (bounds.lower, bounds.upper):
            raise ValueError("CP-SAT uncertainty objective differs from Python score bounds.")
        attempt.update(candidate_id=item.id, vector=item.vector, objective_values=[solver.value(term) for term, _ in terms])
        candidates[item.id] = item
        hint = item
    report.update(elapsed_seconds=time.monotonic() - started, candidate_count_lower_bound=len(candidates))
    return pool_analysis(candidates, ranking, weights, report)
