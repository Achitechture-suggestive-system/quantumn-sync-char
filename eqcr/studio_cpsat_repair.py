"""Bounded weighted repair search with protected policies and logical minimality checks."""

import time

from ortools.sat.python import cp_model

from .quantum_tradeoff import group_index
from .studio_cpsat import SEED, hard_blocks, partition_variables, seed_partitions


def bounded_repairs(architecture, rules, *, time_limit_seconds=6.0, limit=3):
    from .studio_conflicts import Repair

    ids = [item.id for item in architecture.components]
    if not hard_blocks(ids, rules)[1]:
        return ()
    protected = tuple(rule for rule in rules if rule.protected)
    protected_blocks, protected_conflict = hard_blocks(ids, protected)
    if protected_conflict:
        return ()
    started = time.monotonic()
    deadline = started + time_limit_seconds

    def violations(groups):
        assignment = group_index(groups)
        return frozenset(index for index, rule in enumerate(rules) if rule.violated_by(assignment))

    def cost(indices):
        return sum(rules[index].change_cost for index in indices)

    def minimal(indices):
        result = set(indices)
        for index in sorted(indices, key=lambda item: (-rules[item].change_cost, item)):
            proposed = result - {index}
            if not hard_blocks(ids, [rule for number, rule in enumerate(rules) if number not in proposed])[1]:
                result = proposed
        return frozenset(result)

    seeds = list(seed_partitions(architecture, protected_blocks, protected))
    initial = min(seeds, key=lambda groups: (cost(violations(groups)), len(violations(groups))))
    fallback = minimal(violations(initial))
    found = {fallback: Repair(tuple(rules[index] for index in sorted(fallback)), None, "NOT_RUN", False)}
    model = cp_model.CpModel()
    groups, _ = partition_variables(model, len(ids))
    by_id = dict(zip(ids, groups, strict=True))
    equality_cache = {}

    def equal(left, right):
        pair = tuple(sorted((left, right)))
        if pair not in equality_cache:
            bit = model.new_bool_var(f"equal_{len(equality_cache)}")
            model.add(by_id[left] == by_id[right]).only_enforce_if(bit)
            model.add(by_id[left] != by_id[right]).only_enforce_if(~bit)
            equality_cache[pair] = bit
        return equality_cache[pair]

    violation_vars = []
    for index, rule in enumerate(rules):
        if rule.kind == "KEEP_APART":
            violation = equal(*rule.components)
        else:
            violation = model.new_bool_var(f"violated_{index}")
            model.add_max_equality(violation, [1 - equal(rule.components[0], item) for item in rule.components[1:]])
        if rule.protected:
            model.add(violation == 0)
        violation_vars.append(violation)
    price = sum(rule.change_cost * bit for rule, bit in zip(rules, violation_vars, strict=True))
    model.minimize(price * (len(rules) + 1) + sum(violation_vars))
    assignment = group_index(initial)
    labels = {}
    for item, variable in by_id.items():
        model.add_hint(variable, labels.setdefault(assignment[item], len(labels)))
    for attempt in range(limit + 1):
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            break
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = remaining / max(1, limit - attempt)
        solver.parameters.num_search_workers = 1
        solver.parameters.random_seed = SEED
        solver.parameters.absolute_gap_limit = 0
        solver.parameters.relative_gap_limit = 0
        status = solver.solve(model)
        if status == cp_model.MODEL_INVALID:
            raise ValueError("Studio repair model invalid: " + model.validate())
        if status not in {cp_model.OPTIMAL, cp_model.FEASIBLE}:
            break
        groups_by_label = {}
        for item, variable in by_id.items():
            groups_by_label.setdefault(solver.value(variable), []).append(item)
        indices = minimal(violations(groups_by_label.values()))
        if not indices or any(rules[index].protected for index in indices):
            raise ValueError("Repair candidate removed a protected rule or failed to explain infeasibility.")
        found[indices] = Repair(tuple(rules[index] for index in sorted(indices)), None, solver.status_name(status), status == cp_model.OPTIMAL)
        # Exclude this correction and all its supersets; remaining answers can be inclusion-minimal alternatives.
        model.add(sum(violation_vars[index] for index in indices) <= len(indices) - 1)
        if len(found) >= limit and attempt > 0:
            break
    return tuple(sorted(found.values(), key=lambda item: (item.review_cost, len(item.rules), tuple((rule.kind, rule.index) for rule in item.rules)))[:limit])
