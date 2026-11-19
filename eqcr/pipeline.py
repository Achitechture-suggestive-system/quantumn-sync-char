"""Deterministic validation, exhaustive candidate generation, and quality tracing."""

from __future__ import annotations

from collections import defaultdict
from copy import deepcopy
from decimal import Decimal
from typing import Any, Iterable, Iterator

import networkx as nx

from .models import (
    Constraint,
    EvidenceConstraintPolicyCatalog,
    EvidenceRecord,
    RawRequirements,
    RelationAnnotation,
    Responsibility,
)
from .evidence_audit import audit_evidence_records
from .cpsat_optimizer import optimize_with_cpsat
from .interaction_contracts import (
    INTERACTION_DECISION_TABLE,
    apply_interaction_contract_overrides,
    make_unresolved_contract,
)
from .traceability import refresh_traceability_artifact


def _partitions(items: list[str]) -> Iterator[tuple[tuple[str, ...], ...]]:
    """Yield every set partition once in deterministic restricted-growth order."""
    blocks: list[list[str]] = []

    def visit(index: int) -> Iterator[tuple[tuple[str, ...], ...]]:
        if index == len(items):
            yield tuple(tuple(block) for block in blocks)
            return
        item = items[index]
        for block_index in range(len(blocks)):
            blocks[block_index].append(item)
            yield from visit(index + 1)
            blocks[block_index].pop()
        blocks.append([item])
        yield from visit(index + 1)
        blocks.pop()

    yield from visit(0)


def _same_group(partition: tuple[tuple[str, ...], ...], left: str, right: str) -> bool:
    return any(left in group and right in group for group in partition)


def _partition_signature(groups: Iterable[Iterable[str]]) -> tuple[tuple[str, ...], ...]:
    return tuple(sorted((tuple(sorted(group)) for group in groups), key=lambda group: group[0]))


def _constraint_conflicts(constraints: list[Constraint]) -> list[dict[str, Any]]:
    enabled = [c for c in constraints if c.enabled and c.hardness == "HARD"]
    by_pair: dict[tuple[str, str], list[Constraint]] = defaultdict(list)
    for constraint in enabled:
        by_pair[tuple(sorted((constraint.left, constraint.right)))].append(constraint)
    conflicts = []
    for pair, pair_constraints in by_pair.items():
        relations = {c.relation for c in pair_constraints}
        if len(relations) > 1:
            conflicts.append(
                {
                    "pair": list(pair),
                    "constraint_ids": [c.id for c in pair_constraints],
                    "relations": sorted(relations),
                    "status": "INFEASIBLE",
                }
            )
    return conflicts


def _optimize(
    responsibility_ids: list[str],
    constraints: list[Constraint],
    preferred_partition: list[list[str]] | None = None,
    selection_policy: str = "FIRST_OPTIMAL",
) -> dict[str, Any]:
    if len(responsibility_ids) > 8:
        return optimize_with_cpsat(
            responsibility_ids,
            constraints,
            preferred_partition,
            selection_policy,
        )
    if not responsibility_ids:
        return {
            "enumerated_partition_count": 0,
            "bell_number_expected": 0,
            "feasible_candidate_count": 0,
            "objective_definition": "J = sum of weights for violated enabled SOFT constraints.",
            "objective_minimum": None,
            "optimal_candidate_count": 0,
            "conflicts": [],
            "feasible_candidates": [],
            "optimal_candidates": [],
            "selected_candidate_id": None,
            "selected_groups": None,
            "selection_policy": selection_policy,
            "result_status": "REVIEW_REQUIRED",
            "interpretation": "No responsibility survived review; no partition was generated.",
        }
    all_partitions = list(_partitions(responsibility_ids))
    active_hard = [c for c in constraints if c.enabled and c.hardness == "HARD"]
    active_soft = [c for c in constraints if c.enabled and c.hardness == "SOFT"]
    feasible: list[dict[str, Any]] = []
    exact_costs: list[Decimal] = []
    for partition in all_partitions:
        if any(
            (c.relation == "MUST_LINK" and not _same_group(partition, c.left, c.right))
            or (c.relation == "CANNOT_LINK" and _same_group(partition, c.left, c.right))
            for c in active_hard
        ):
            continue
        exact_cost = sum(
            (Decimal(str(c.weight))
            for c in active_soft
            if (c.relation == "MUST_LINK" and not _same_group(partition, c.left, c.right))
            or (c.relation == "CANNOT_LINK" and _same_group(partition, c.left, c.right))),
            Decimal(0),
        )
        exact_costs.append(exact_cost)
        feasible.append({"groups": [list(g) for g in partition], "objective_cost": float(exact_cost)})

    conflicts = _constraint_conflicts(constraints)
    if not feasible and not conflicts:
        def satisfies_hard_rules(
            partition: tuple[tuple[str, ...], ...],
            rules: list[Constraint],
        ) -> bool:
            return all(
                (rule.relation == "MUST_LINK" and _same_group(partition, rule.left, rule.right))
                or (rule.relation == "CANNOT_LINK" and not _same_group(partition, rule.left, rule.right))
                for rule in rules
            )

        core_indices = sorted(
            range(len(active_hard)),
            key=lambda index: (active_hard[index].id, index),
        )
        for candidate_index in tuple(core_indices):
            trial_indices = [index for index in core_indices if index != candidate_index]
            trial_rules = [active_hard[index] for index in trial_indices]
            trial_has_feasible_partition = any(
                satisfies_hard_rules(partition, trial_rules)
                for partition in all_partitions
            )
            if not trial_has_feasible_partition:
                core_indices = trial_indices
        core = [active_hard[index] for index in core_indices]
        conflicts.append(
            {
                "pair": [],
                "constraint_ids": [c.id for c in core],
                "relations": sorted({c.relation for c in core}),
                "status": "INFEASIBLE",
                "reason": (
                    "No partition satisfies these hard constraints together; removing any listed constraint "
                    "makes at least one partition feasible."
                ),
                "explanation_scope": "DELETION_MINIMAL_HARD_CONSTRAINT_CORE",
            }
        )
    if feasible:
        min_cost_exact = min(exact_costs)
        min_cost = float(min_cost_exact)
        optimal = [item for item, cost in zip(feasible, exact_costs, strict=True) if cost == min_cost_exact]
    else:
        min_cost = None
        optimal = []
    for index, candidate in enumerate(feasible):
        candidate["candidate_id"] = f"P{index + 1:03d}"
        candidate["is_optimal"] = min_cost is not None and exact_costs[index] == min_cost_exact

    preferred = next(
        (
            item for item in optimal
            if preferred_partition is not None
            and _partition_signature(item["groups"]) == _partition_signature(preferred_partition)
        ),
        None,
    )
    if preferred is not None:
        selected = preferred
    elif selection_policy == "MAXIMUM_GROUPS":
        selected = max(optimal, key=lambda item: len(item["groups"])) if optimal else None
    else:
        selected = optimal[0] if optimal else None
    return {
        "enumerated_partition_count": len(all_partitions),
        "bell_number_expected": len(all_partitions),
        "feasible_candidate_count": len(feasible),
        "objective_definition": "J = sum of weights for violated enabled SOFT constraints.",
        "objective_minimum": min_cost,
        "optimal_candidate_count": len(optimal),
        "conflicts": conflicts,
        "feasible_candidates": feasible,
        "optimal_candidates": optimal,
        "selected_candidate_id": selected["candidate_id"] if selected else None,
        "selected_groups": selected["groups"] if selected else None,
        "selection_policy": "PREFERRED_PARTITION" if preferred_partition else selection_policy,
        "result_status": "INFEASIBLE" if not feasible else "REVIEW_REQUIRED",
        "interpretation": "The selected candidate is a deterministic display choice among minimum-cost partitions, not an architecture recommendation.",
    }


def _derive_evidence_constraints(
    raw: RawRequirements,
    evidence: list[EvidenceRecord],
    responsibilities: list[Responsibility],
    policy_catalog_data: dict[str, Any],
    source_texts: dict[str, str],
    blocked_evidence_ids: set[str] | None = None,
) -> tuple[list[Constraint], dict[str, Any]]:
    """Evaluate a versioned experimental catalog and explain every application or abstention."""
    catalog = EvidenceConstraintPolicyCatalog.model_validate(policy_catalog_data)
    responsibility_by_id = {item.id: item for item in responsibilities}
    requirement_by_id = {item.id: item for item in raw.requirements}
    derived = []
    seen = set()
    evaluations: list[dict[str, Any]] = []
    blocked_evidence_ids = blocked_evidence_ids or set()
    for policy in catalog.entries:
        for record in evidence:
            result = {
                "policy_id": policy.id,
                "policy_version": policy.version,
                "catalog_id": catalog.catalog_id,
                "catalog_version": catalog.version,
                "evidence_id": record.id,
                "status": "ABSTAINED",
                "reason": None,
                "derived_constraint_id": None,
                "responsibility_endpoints": [],
                "source_ids": [ref.source_id for ref in record.source_refs],
                "provenance": "DETERMINISTIC_TRANSFORMATION",
            }
            if record.predicate != policy.evidence_predicate:
                result.update(status="NOT_APPLICABLE", reason="Evidence predicate does not match this catalog entry.")
                evaluations.append(result)
                continue
            if record.id in blocked_evidence_ids:
                result["reason"] = "Evidence claim is duplicated or has mixed/contradictory status; reviewer resolution is required."
                evaluations.append(result)
                continue
            if record.status != "PRESENT":
                result["reason"] = "Only PRESENT evidence can satisfy this policy; UNKNOWN and SCOPED_ABSENT abstain."
                evaluations.append(result)
                continue
            if record.review_status != "APPROVED":
                result["reason"] = "Evidence has not been approved by human review."
                evaluations.append(result)
                continue
            if not record.source_refs:
                result["reason"] = "Evidence has no source citations."
                evaluations.append(result)
                continue
            if record.architecture_implication != policy.required_architecture_implication:
                result["reason"] = "Human architecture implication does not match this policy entry."
                evaluations.append(result)
                continue
            if not record.relation_annotation_id:
                result["reason"] = "The architectural implication has no linked human relation annotation."
                evaluations.append(result)
                continue
            left, right = record.subject_id, record.object_id
            if left == right or left not in responsibility_by_id or right not in responsibility_by_id:
                result["reason"] = "Responsibility endpoints are reflexive or unresolved."
                evaluations.append(result)
                continue
            if any(
                responsibility_by_id[rid].review_decision_status != "APPROVED"
                for rid in (left, right)
            ):
                result["reason"] = "One or both responsibility endpoints are not approved."
                evaluations.append(result)
                continue
            source_refs_valid = all(
                ref.source_id in source_texts
                and ref.end <= len(source_texts[ref.source_id])
                and source_texts[ref.source_id][ref.start:ref.end] == ref.quote
                for ref in record.source_refs
            )
            endpoint_requirement_ids = {
                value for value in (record.subject_requirement_id, record.object_requirement_id) if value
            }
            if endpoint_requirement_ids:
                if (
                    len(endpoint_requirement_ids) != 2
                    or record.subject_requirement_id not in responsibility_by_id[left].requirement_ids
                    or record.object_requirement_id not in responsibility_by_id[right].requirement_ids
                ):
                    result["reason"] = "Evidence requirement endpoints do not map to the named responsibility endpoints."
                    evaluations.append(result)
                    continue
                endpoint_sources = {
                    requirement_by_id[requirement_id].source_ref.source_id
                    for requirement_id in endpoint_requirement_ids
                    if requirement_id in requirement_by_id
                }
            else:
                endpoint_sources = {
                    requirement.source_ref.source_id
                    for responsibility_id in (left, right)
                    for requirement_id in responsibility_by_id[responsibility_id].requirement_ids
                    for requirement in [requirement_by_id.get(requirement_id)]
                    if requirement is not None
                }
            cited_sources = {ref.source_id for ref in record.source_refs}
            if not source_refs_valid or not endpoint_sources or not endpoint_sources <= cited_sources:
                result["reason"] = "Citations are invalid or do not cover both requirement endpoints."
                evaluations.append(result)
                continue
            key = (policy.id, tuple(sorted((left, right))))
            if key in seen:
                result["reason"] = "A prior evidence row already emitted this policy for the same responsibility pair."
                evaluations.append(result)
                continue
            seen.add(key)
            constraint = Constraint(
                id=f"D-{policy.id}-{record.id}",
                relation=policy.relation,
                left=left,
                right=right,
                hardness=policy.hardness,
                weight=policy.weight,
                evidence_ids=[record.id],
                origin="ARCHITECTURAL_POLICY",
                enabled=True,
                source_refs=record.source_refs,
                rationale=(
                    f"Catalog {catalog.catalog_id}@{catalog.version}; policy {policy.id}@{policy.version}: "
                    f"{policy.rationale} Applied to reviewer-approved evidence {record.id}."
                ),
            )
            derived.append(constraint)
            result.update(
                status="APPLIED",
                reason="All declared evidence, citation, human-decision, and responsibility-endpoint gates passed.",
                derived_constraint_id=constraint.id,
                responsibility_endpoints=[left, right],
            )
            evaluations.append(result)
    return derived, {
        "catalog_id": catalog.catalog_id,
        "catalog_version": catalog.version,
        "catalog_status": catalog.status,
        "catalog_review_status": catalog.review_status,
        "catalog_snapshot": catalog.model_dump(mode="json"),
        "evaluation_status": "EVALUATED",
        "provenance": "DETERMINISTIC_TRANSFORMATION",
        "results": evaluations,
        "interpretation": "Experimental case rules are not externally validated tactics or architectural facts.",
    }


def _build_quanta(responsibilities: list[Responsibility], selected: list[list[str]] | None) -> dict[str, Any]:
    by_id = {item.id: item for item in responsibilities}
    quanta = []
    assignment: dict[str, str] = {}
    for index, group in enumerate(selected or [], start=1):
        quantum_id = f"Q{index}"
        for rid in group:
            assignment[rid] = quantum_id
        quanta.append(
            {
                "id": quantum_id,
                "responsibility_ids": group,
                "responsibilities": [by_id[rid].name for rid in group],
                "ownership": "REVIEW_REQUIRED",
                "owner": None,
                "ownership_status": "UNKNOWN",
                "review_status": "REVIEW_REQUIRED",
                "role": "PROPOSED_BOUNDARY",
                "boundary_rationale": "Grouping follows the selected partition; independent deployment and runtime evidence are absent.",
                "dependencies": [],
                "relevant_evidence_ids": [],
                "unresolved_decisions": ["DEPLOYMENT-OWNERSHIP-UNKNOWN"],
                "status": "PROPOSED_NOT_VERIFIED",
            }
        )
    membership_counts = {rid: sum(rid in group for group in (selected or [])) for rid in by_id}
    assignment_status = (
        "PASS" if by_id and all(count == 1 for count in membership_counts.values())
        else "INSUFFICIENT_EVIDENCE" if not by_id
        else "INFEASIBLE"
    )
    return {
        "selected_candidate_id": None,
        "quanta": quanta,
        "primary_assignment": assignment,
        "membership_counts": membership_counts,
        "assignment_validation_status": assignment_status,
        "status": "PROPOSED_NOT_VERIFIED" if assignment_status == "PASS" else assignment_status,
        "verification_note": "A partition assignment is not evidence of independent deployability.",
    }


def _build_interactions(
    quanta: dict[str, Any],
    raw: RawRequirements,
    responsibilities: list[Responsibility],
) -> dict[str, Any]:
    assignment = quanta["primary_assignment"]
    graph = nx.DiGraph()
    graph.add_nodes_from(item["id"] for item in quanta["quanta"])
    requirement_to_responsibilities: dict[str, list[str]] = defaultdict(list)
    for responsibility in responsibilities:
        for requirement_id in responsibility.requirement_ids:
            requirement_to_responsibilities[requirement_id].append(responsibility.id)
    interactions = []
    seen_interactions = set()
    for scenario in raw.scenarios:
        if len(scenario.related_requirement_ids) < 2:
            continue
        candidate_pairs = []
        for left_fr, right_fr in zip(scenario.related_requirement_ids, scenario.related_requirement_ids[1:]):
            for left in requirement_to_responsibilities.get(left_fr, []):
                for right in requirement_to_responsibilities.get(right_fr, []):
                    if left == right:
                        continue
                    candidate_pairs.append((left, right))
        for left, right in candidate_pairs:
            left_quantum, right_quantum = assignment.get(left), assignment.get(right)
            if not left_quantum or not right_quantum:
                continue
            edge_id = (
                scenario.interaction_id
                if len(candidate_pairs) == 1 and len(scenario.related_requirement_ids) == 2 and scenario.interaction_id
                else f"EDGE-{scenario.id}-{left}-{right}"
            )
            edge_key = (scenario.id, left, right)
            if edge_key in seen_interactions:
                continue
            seen_interactions.add(edge_key)
            interactions.append((scenario, left, right, left_quantum, right_quantum, edge_id))
    if not interactions:
        return {
            "edges": [],
            "graph_summary": {"node_count": graph.number_of_nodes(), "directed_edge_count": 0},
            "status": "INSUFFICIENT_EVIDENCE",
            "contract_schema": {"id": "EQCR-INTERACTION-CONTRACT", "version": "1.0.0"},
            "decision_table": deepcopy(INTERACTION_DECISION_TABLE),
            "note": "No scenario links two responsibilities with a current quantum assignment.",
        }
    edges = []
    for scenario, left, right, left_quantum, right_quantum, edge_id in interactions:
        related_refs = [
            next(item for item in raw.requirements if item.id == requirement_id).source_ref.model_dump(mode="json")
            for requirement_id in scenario.interaction_source_requirement_ids
        ]
        proposal_sources = [scenario.source_ref.model_dump(mode="json"), *related_refs]
        unresolved_decisions = [
            "acknowledgement timing",
            "consistency guarantee",
            "latency budget",
            "failure handling",
            "retry and idempotency behavior",
        ]
        interaction_options = [
            {
                "id": f"OPT-{edge_id}-SYNC",
                "mode": "SYNC",
                "pattern": "Request-response",
                "status": "PROPOSED_NOT_VERIFIED",
                "review_status": "REVIEW_REQUIRED",
                "provenance": "DETERMINISTIC_PATTERN_HYPOTHESIS",
                "source_refs": proposal_sources,
                "condition": "Consider only if the initiating request must receive a completed outcome synchronously.",
                "rationale": f"Scenario {scenario.id} links the activities but does not specify synchronous completion.",
                "unresolved_decisions": unresolved_decisions,
            },
            {
                "id": f"OPT-{edge_id}-ASYNC",
                "mode": "ASYNC",
                "pattern": "Command with later completion notification",
                "status": "PROPOSED_NOT_VERIFIED",
                "review_status": "REVIEW_REQUIRED",
                "provenance": "DETERMINISTIC_PATTERN_HYPOTHESIS",
                "source_refs": proposal_sources,
                "condition": "Consider only if the initiating request may return before the linked activity completes.",
                "rationale": f"Scenario {scenario.id} does not establish pending-state or notification behavior.",
                "unresolved_decisions": unresolved_decisions,
            },
        ]
        same_quantum = left_quantum == right_quantum
        graph.add_edge(left_quantum, right_quantum, edge_id=edge_id, status="UNRESOLVED")
        contract = make_unresolved_contract(edge_id, proposal_sources, unresolved_decisions)
        edges.append(
            {
                "id": edge_id,
                "from_quantum": left_quantum,
                "to_quantum": right_quantum,
                "responsibility_ids": [left, right],
                "label": "UNRESOLVED",
                "review_status": "REVIEW_REQUIRED",
                "direction": f"{left} → {right}",
                "same_quantum": same_quantum,
                "source_refs": proposal_sources,
                "options": interaction_options,
                "selection_status": "UNRESOLVED",
                "consistency": "UNKNOWN",
                "latency_budget": "UNKNOWN",
                "failure_handling": "UNKNOWN",
                "contract": contract,
                "rationale": f"Scenario {scenario.id} links these activities but provides no interaction contract.",
                "status": "INSUFFICIENT_EVIDENCE",
            }
        )
    return {
        "edges": edges,
        "graph_summary": {
            "node_count": graph.number_of_nodes(),
            "directed_edge_count": graph.number_of_edges(),
        },
        "status": "INSUFFICIENT_EVIDENCE",
        "contract_schema": {"id": "EQCR-INTERACTION-CONTRACT", "version": "1.0.0"},
        "decision_table": deepcopy(INTERACTION_DECISION_TABLE),
    }


def _build_quality(
    raw: RawRequirements,
    responsibilities: list[Responsibility],
    quanta: dict[str, Any],
    interactions: dict[str, Any],
) -> dict[str, Any]:
    assignment = quanta["primary_assignment"]
    requirement_to_responsibilities: dict[str, list[str]] = defaultdict(list)
    for responsibility in responsibilities:
        for requirement_id in responsibility.requirement_ids:
            requirement_to_responsibilities[requirement_id].append(responsibility.id)
    profiles = []
    for scenario in raw.scenarios:
        responsibility_ids = sorted({
            responsibility_id
            for requirement_id in scenario.related_requirement_ids
            for responsibility_id in requirement_to_responsibilities.get(requirement_id, [])
        })
        quantum_ids = sorted({assignment[item] for item in responsibility_ids if item in assignment})
        requirement_refs = [
            next(item for item in raw.requirements if item.id == requirement_id).source_ref.model_dump(mode="json")
            for requirement_id in scenario.related_requirement_ids
        ]
        affected_edges = [
            edge["id"] for edge in interactions["edges"]
            if set(edge["responsibility_ids"]) <= set(responsibility_ids)
        ]
        scenario_part_values = {
            "stimulus_source": scenario.stimulus_source,
            "stimulus": scenario.stimulus,
            "environment": scenario.environment,
            "stimulated_artifact": scenario.stimulated_artifact,
            "response": scenario.response,
            "response_measure": scenario.response_measure,
        }
        scenario_quote = scenario.source_ref.quote
        scenario_parts = {}
        for part_id, value in scenario_part_values.items():
            normalized_value = value.strip() if isinstance(value, str) else ""
            source_backed = bool(normalized_value and normalized_value in scenario_quote)
            scenario_parts[part_id] = {
                "value": value,
                "status": "SPECIFIED" if source_backed else "UNSUPPORTED" if normalized_value else "UNKNOWN",
                "provenance": "SOURCE_BACKED" if source_backed else "PREPARED_FIXTURE" if normalized_value else "UNKNOWN",
                "source_ref": scenario.source_ref.model_dump(mode="json") if source_backed else None,
            }
        unresolved_parts = [
            part_id for part_id, part in scenario_parts.items() if part["status"] != "SPECIFIED"
        ]
        target_value = scenario.target.strip() if scenario.target else ""
        target_source_backed = bool(target_value and target_value in scenario_quote)
        metric_value = scenario.proposed_metric.strip() if scenario.proposed_metric else ""
        metric_source_backed = bool(metric_value and metric_value in scenario_quote)
        method_value = scenario.measurement_method.strip() if scenario.measurement_method else ""
        method_source_backed = bool(method_value and method_value in scenario_quote)
        measured_target = target_source_backed and bool(scenario_parts["response_measure"]["status"] == "SPECIFIED")
        characteristic_value = scenario.quality_characteristic.strip() if scenario.quality_characteristic else ""
        characteristic_source_backed = bool(characteristic_value and characteristic_value in scenario_quote)
        profiles.append(
            {
                "scenario_id": scenario.id,
                "scenario_name": scenario.name,
                "scenario_source_ref": scenario.source_ref.model_dump(mode="json"),
                "responsibility_id": responsibility_ids[0] if len(responsibility_ids) == 1 else None,
                "responsibility_ids": responsibility_ids,
                "quantum_id": quantum_ids[0] if len(quantum_ids) == 1 else None,
                "quantum_ids": quantum_ids,
                "iso_characteristic": scenario.quality_characteristic or "UNKNOWN",
                "quality_characteristic_mapping": {
                    "standard": "ISO/IEC 25010:2023",
                    "status": "UNMAPPED" if scenario.quality_characteristic else "UNSPECIFIED",
                    "source_label": scenario.quality_characteristic,
                    "characteristic_id": None,
                    "label_provenance": (
                        "SOURCE_BACKED_SCENARIO_TRACE"
                        if characteristic_source_backed
                        else "PREPARED_FIXTURE"
                        if characteristic_value
                        else "UNKNOWN"
                    ),
                    "label_source_ref": scenario.source_ref.model_dump(mode="json") if characteristic_source_backed else None,
                    "mapping_provenance": "DETERMINISTIC_TRANSFORMATION",
                    "review_status": "REVIEW_REQUIRED",
                },
                "scenario_schema": {"id": "QAME-SIX-PART-SCENARIO", "version": "1.0.0"},
                "scenario_parts": scenario_parts,
                "scenario_completeness": "COMPLETE" if not unresolved_parts else "PARTIAL",
                "unresolved_scenario_parts": unresolved_parts,
                "target": scenario.target,
                "proposed_metric": scenario.proposed_metric,
                "measurement_method": scenario.measurement_method,
                "measurement_plan_status": "PROPOSED" if measured_target and scenario.measurement_method else "INSUFFICIENT_EVIDENCE",
                "provenance": "DETERMINISTIC_TRANSFORMATION",
                "target_status": "SPECIFIED" if target_source_backed else "UNSUPPORTED" if target_value else "INSUFFICIENT_EVIDENCE",
                "target_provenance": "SOURCE_BACKED" if target_source_backed else "PREPARED_FIXTURE" if target_value else "UNKNOWN",
                "proposed_metric_provenance": "SOURCE_BACKED" if metric_source_backed else "PREPARED_FIXTURE" if metric_value else "UNKNOWN",
                "measurement_method_provenance": "SOURCE_BACKED" if method_source_backed else "PREPARED_FIXTURE" if method_value else "UNKNOWN",
                "evidence": [
                    {
                        "kind": "TARGET_SOURCE" if target_source_backed else "SCENARIO_SOURCE",
                        "source_ref": scenario.source_ref.model_dump(mode="json"),
                    },
                    *({"kind": "REQUIREMENT_SOURCE", "source_ref": ref} for ref in requirement_refs),
                ],
                "affected_interaction_edges": affected_edges,
                "measurement_status": "NOT_MEASURED" if target_value else "INSUFFICIENT_EVIDENCE",
                "review_status": "REVIEW_REQUIRED",
                "measurement": None,
                "trace_status": "PASS" if responsibility_ids and len(quantum_ids) >= 1 else "INSUFFICIENT_EVIDENCE",
                "note": (
                    "Scenario target is source-backed; no benchmark has been run."
                    if measured_target
                    else "Target text is not backed by its scenario SourceRef; measurement remains insufficient evidence."
                    if target_value
                    else "Scenario provides no measurable target; no pass/fail result is inferred."
                ),
            }
        )
    return {"profiles": profiles, "status": "NOT_MEASURED"}


def _build_architecture_graph(
    raw: RawRequirements,
    quanta: dict[str, Any],
    interactions: dict[str, Any],
    evidence: list[EvidenceRecord],
) -> dict[str, Any]:
    """Show known and explicitly unknown layers without inventing components."""
    actor_source = raw.requirements[0].source_ref
    runtime_evidence_ids = [
        item.id for item in evidence if item.predicate == "independent_deployment_evidence"
    ]
    nodes = [
        {
            "id": "ACTOR-USER",
            "layer": "ACTOR",
            "label": "User",
            "status": "PRESENT",
            "source_ref": actor_source.model_dump(mode="json"),
            "provenance": "SOURCE_BACKED",
        },
        {
            "id": "PRESENTATION-UNKNOWN",
            "layer": "PRESENTATION_APPLICATION",
            "label": "Presentation / application tier not specified",
            "status": "UNKNOWN",
            "evidence_ids": runtime_evidence_ids,
            "provenance": "ARCHITECTURAL_POLICY",
        },
    ]
    nodes.extend(
        {
            "id": item["id"],
            "layer": "QUANTUM",
            "label": f"{item['id']}: {', '.join(item['responsibility_ids'])}",
            "status": item["status"],
            "relevant_evidence_ids": item["relevant_evidence_ids"],
        }
        for item in quanta["quanta"]
    )
    nodes.append(
        {
            "id": "INTEGRATION-UNKNOWN",
            "layer": "INTEGRATION",
            "label": "Integration / connectivity not specified",
            "status": "UNKNOWN",
            "evidence_ids": runtime_evidence_ids,
            "provenance": "ARCHITECTURAL_POLICY",
        }
    )
    nodes.append(
        {
            "id": "INFRASTRUCTURE-UNKNOWN",
            "layer": "INFRASTRUCTURE_STORAGE",
            "label": "Infrastructure / storage not specified",
            "status": "UNKNOWN",
            "evidence_ids": runtime_evidence_ids,
            "provenance": "ARCHITECTURAL_POLICY",
        }
    )
    edges = [
        {
            "id": "EDGE-USER-PRESENTATION-UNKNOWN",
            "from": "ACTOR-USER",
            "to": "PRESENTATION-UNKNOWN",
            "label": "UNKNOWN",
            "status": "UNKNOWN",
            "rationale": "The requirements mention a user but do not describe a presentation or application tier.",
            "provenance": "ARCHITECTURAL_POLICY",
        }
    ]
    if quanta["quanta"]:
        for quantum in quanta["quanta"]:
            edges.extend(
                [
                    {
                        "id": f"EDGE-PRESENTATION-{quantum['id']}-UNKNOWN",
                        "from": "PRESENTATION-UNKNOWN",
                        "to": quantum["id"],
                        "label": "UNKNOWN",
                        "status": "UNKNOWN",
                        "rationale": "No tier-to-responsibility mapping was supplied.",
                        "provenance": "ARCHITECTURAL_POLICY",
                    },
                    {
                        "id": f"EDGE-{quantum['id']}-INTEGRATION-UNKNOWN",
                        "from": quantum["id"],
                        "to": "INTEGRATION-UNKNOWN",
                        "label": "UNKNOWN",
                        "status": "UNKNOWN",
                        "rationale": "No integration or inter-quantum contract was supplied.",
                        "provenance": "ARCHITECTURAL_POLICY",
                    },
                ]
            )
    edges.append(
        {
            "id": "EDGE-INTEGRATION-INFRASTRUCTURE-UNKNOWN",
            "from": "INTEGRATION-UNKNOWN",
            "to": "INFRASTRUCTURE-UNKNOWN",
            "label": "UNKNOWN",
            "status": "UNKNOWN",
            "rationale": "No infrastructure or storage relationship was supplied.",
            "provenance": "ARCHITECTURAL_POLICY",
        }
    )
    edges.extend(
        {
            "id": item["id"],
            "from": item["from_quantum"],
            "to": item["to_quantum"],
            "label": item["label"],
            "status": item["status"],
            "rationale": item["rationale"],
            "source_refs": item["source_refs"],
            "provenance": "DETERMINISTIC_TRANSFORMATION",
        }
        for item in interactions["edges"]
    )
    return {
        "schema": {"id": "EQCR-ARCHITECTURE-GRAPH", "version": "1.0.0"},
        "layers": [
            "ACTOR",
            "PRESENTATION_APPLICATION",
            "QUANTUM",
            "INTEGRATION",
            "INFRASTRUCTURE_STORAGE",
        ],
        "nodes": nodes,
        "edges": edges,
        "status": "REVIEW_REQUIRED",
        "note": "Unknown tiers and infrastructure are displayed as unknown placeholders, not proposed system components.",
    }


def _step(step_id: str, name: str, status: str, details: str, artifact_ids: list[str]) -> dict[str, Any]:
    return {"step": step_id, "name": name, "status": status, "details": details, "artifact_ids": artifact_ids}


def run_pipeline(
    fixture: dict[str, Any],
    *,
    constraints_override: list[dict[str, Any]] | None = None,
    decisions: list[dict[str, Any]] | None = None,
    revisions: list[dict[str, Any]] | None = None,
    execution_mode: str = "OFFLINE_FIXTURE",
) -> dict[str, Any]:
    """Run deterministic steps 01-10 and return serializable, traceable artifacts."""
    raw = RawRequirements.model_validate(fixture["raw_requirements"])
    responsibilities = [Responsibility.model_validate(item) for item in fixture["responsibilities"]]
    evidence = [EvidenceRecord.model_validate(item) for item in fixture["evidence"]]
    relation_annotations = [
        RelationAnnotation.model_validate(item) for item in fixture.get("relation_annotations", [])
    ]
    evidence_audit = audit_evidence_records(evidence, relation_annotations)
    relation_ids = [item.id for item in relation_annotations]
    if len(relation_ids) != len(set(relation_ids)):
        raise ValueError("Relation annotation IDs must be unique.")
    evidence_ids = [item.id for item in evidence]
    if len(evidence_ids) != len(set(evidence_ids)):
        raise ValueError("Evidence IDs must be unique.")
    responsibility_ids = [item.id for item in responsibilities]
    if len(responsibility_ids) != len(set(responsibility_ids)):
        raise ValueError("Responsibility IDs must be unique.")
    known_requirement_ids = {item.id for item in raw.requirements}
    known_workflow_ids = {item.id for item in raw.workflows}
    known_responsibility_ids = set(responsibility_ids)
    requirement_by_id = {item.id: item for item in raw.requirements}
    workflow_by_id = {item.id: item for item in raw.workflows}
    constraint_source_texts = {
        item.source_ref.source_id: item.text for item in raw.requirements
    }
    constraint_source_texts.update({item.source_ref.source_id: item.text for item in raw.workflows})
    constraint_source_texts.update(
        {item.source_ref.source_id: item.source_ref.quote for item in raw.scenarios}
    )
    for responsibility in responsibilities:
        unknown_requirements = set(responsibility.requirement_ids) - known_requirement_ids
        if unknown_requirements:
            raise ValueError(
                f"{responsibility.id} references unknown requirement IDs: {sorted(unknown_requirements)}."
            )
    for relation in relation_annotations:
        if relation.subject_requirement_id not in known_requirement_ids or relation.object_requirement_id not in known_requirement_ids:
            raise ValueError(f"Relation annotation {relation.id} references an unknown FR endpoint.")
        if not set(relation.source_requirement_ids) <= known_requirement_ids or not set(relation.source_workflow_ids) <= known_workflow_ids:
            raise ValueError(f"Relation annotation {relation.id} references an unknown source ID.")
        if relation.status in {"PRESENT", "SCOPED_ABSENT"} and not relation.source_refs:
            raise ValueError(f"Relation annotation {relation.id} is missing its cited source spans.")
        if any(
            ref.source_id not in constraint_source_texts
            or ref.end > len(constraint_source_texts[ref.source_id])
            or constraint_source_texts[ref.source_id][ref.start:ref.end] != ref.quote
            for ref in relation.source_refs
        ):
            raise ValueError(f"Relation annotation {relation.id} contains an unresolved source span.")
        if relation.architecture_implication in {"COLOCATE_CANDIDATE", "SEPARATE_CANDIDATE"}:
            for left, right in relation.responsibility_pairs:
                if left not in known_responsibility_ids or right not in known_responsibility_ids:
                    raise ValueError(f"Relation annotation {relation.id} references an unknown responsibility pair.")
                role_by_id = {item.id: item for item in responsibilities}
                if relation.subject_requirement_id not in role_by_id[left].requirement_ids or relation.object_requirement_id not in role_by_id[right].requirement_ids:
                    raise ValueError(f"Relation annotation {relation.id} pair does not match its cited FR endpoints.")
    known_relation_ids = set(relation_ids)
    relation_by_id = {item.id: item for item in relation_annotations}
    evidence_by_relation: dict[str, list[EvidenceRecord]] = defaultdict(list)
    for item in evidence:
        if not item.relation_annotation_id:
            continue
        if item.relation_annotation_id not in known_relation_ids:
            raise ValueError(f"Evidence {item.id} references unknown relation annotation {item.relation_annotation_id}.")
        relation = relation_by_id[item.relation_annotation_id]
        if relation.architecture_implication not in {"COLOCATE_CANDIDATE", "SEPARATE_CANDIDATE"}:
            raise ValueError(f"Evidence {item.id} is materialized from a relation without an architecture candidate implication.")
        if (
            relation.review_status != "APPROVED"
            or relation.status != "PRESENT"
            or item.review_status != "APPROVED"
            or item.status != "PRESENT"
            or item.predicate != relation.predicate
            or item.subject_requirement_id != relation.subject_requirement_id
            or item.object_requirement_id != relation.object_requirement_id
            or item.architecture_implication != relation.architecture_implication
        ):
            raise ValueError(f"Evidence {item.id} does not preserve the approved relation status and semantics.")
        if (item.subject_id, item.object_id) not in relation.responsibility_pairs:
            raise ValueError(f"Evidence {item.id} responsibility pair is absent from its reviewed relation annotation.")
        if {ref.source_id for ref in item.source_refs} != {ref.source_id for ref in relation.source_refs}:
            raise ValueError(f"Evidence {item.id} source IDs differ from its reviewed relation annotation.")
        evidence_by_relation[item.relation_annotation_id].append(item)
    for relation in relation_annotations:
        if relation.architecture_implication in {"COLOCATE_CANDIDATE", "SEPARATE_CANDIDATE"}:
            relation_evidence = evidence_by_relation.get(relation.id, [])
            actual_pairs = [(item.subject_id, item.object_id) for item in relation_evidence]
            expected_pairs = set(relation.responsibility_pairs)
            if len(actual_pairs) != len(expected_pairs) or set(actual_pairs) != expected_pairs:
                raise ValueError(
                    f"Relation annotation {relation.id} must have exactly one evidence row per approved responsibility pair."
                )
    selected_constraints = fixture["constraints"] if constraints_override is None else constraints_override
    policy_evaluation = None
    policy_catalog_data = fixture.get("constraint_policy_catalog")
    if constraints_override is None:
        derived_constraints = []
        if policy_catalog_data is not None:
            derived_constraints, policy_evaluation = _derive_evidence_constraints(
                raw,
                evidence,
                responsibilities,
                policy_catalog_data,
                constraint_source_texts,
                set(evidence_audit["blocked_evidence_ids"]),
            )
        selected_constraints = [
            *selected_constraints,
            *[item.model_dump(mode="json") for item in derived_constraints],
        ]
    elif policy_catalog_data is not None:
        catalog = EvidenceConstraintPolicyCatalog.model_validate(policy_catalog_data)
        policy_evaluation = {
            "catalog_id": catalog.catalog_id,
            "catalog_version": catalog.version,
            "catalog_status": catalog.status,
            "catalog_review_status": catalog.review_status,
            "catalog_snapshot": catalog.model_dump(mode="json"),
            "evaluation_status": "BYPASSED_BY_EXPLICIT_CONSTRAINT_OVERRIDE",
            "provenance": "DETERMINISTIC_TRANSFORMATION",
            "results": [],
            "interpretation": "Explicit constraint override supplied; catalog rules were not applied in this run.",
        }
    constraints = [Constraint.model_validate(item) for item in selected_constraints]
    known_scenario_ids = {item.id for item in raw.scenarios}
    known_evidence_ids = {item.id for item in evidence}
    for constraint in constraints:
        unknown_responsibilities = {constraint.left, constraint.right} - known_responsibility_ids
        if unknown_responsibilities:
            raise ValueError(
                f"{constraint.id} references unknown responsibility IDs: {sorted(unknown_responsibilities)}."
            )
        unknown_scenarios = set(constraint.quality_scenario_ids) - known_scenario_ids
        if unknown_scenarios:
            raise ValueError(f"{constraint.id} references unknown quality scenarios: {sorted(unknown_scenarios)}.")
        unknown_evidence = set(constraint.evidence_ids) - known_evidence_ids
        if unknown_evidence:
            raise ValueError(f"{constraint.id} references unknown evidence IDs: {sorted(unknown_evidence)}.")
    raw_dict = raw.model_dump(mode="json")
    responsibility_dicts = [item.model_dump(mode="json") for item in responsibilities]
    evidence_dicts = [item.model_dump(mode="json") for item in evidence]
    constraint_dicts = [item.model_dump(mode="json") for item in constraints]

    context = {
        "context_id": raw.context_id,
        "case_id": raw.case_id,
        "description": raw.context_description,
        "requirement_count": len(raw.requirements),
        "requirement_ids": [item.id for item in raw.requirements],
        "workflow_count": len(raw.workflows),
        "scenario_ids": [item.id for item in raw.scenarios],
        "provenance": fixture["fixture_label"],
        "llm_normalization_proposal": deepcopy(fixture.get("context_proposal")),
        "status": "REVIEW_REQUIRED",
        "note": "Frozen fixture normalization; all extracted semantics remain reviewable.",
    }
    optimization = _optimize(
        [item.id for item in responsibilities],
        constraints,
        fixture.get("preferred_partition"),
        fixture.get("candidate_selection_policy", "FIRST_OPTIMAL"),
    )
    quanta = _build_quanta(responsibilities, optimization["selected_groups"])
    quanta["selected_candidate_id"] = optimization["selected_candidate_id"]
    interactions = _build_interactions(quanta, raw, responsibilities)
    interactions = apply_interaction_contract_overrides(
        interactions,
        fixture.get("interaction_contracts_override", []),
        constraint_source_texts,
    )
    evidence_by_id = {item.id: item for item in evidence}
    quantum_by_id = {item["id"]: item for item in quanta["quanta"]}
    for quantum in quanta["quanta"]:
        members = set(quantum["responsibility_ids"])
        quantum["relevant_evidence_ids"] = sorted(
            item.id for item in evidence if item.subject_id in members or item.object_id in members
        )
    for edge in interactions["edges"]:
        source_quantum = quantum_by_id.get(edge["from_quantum"])
        target_quantum = quantum_by_id.get(edge["to_quantum"])
        if source_quantum and target_quantum and source_quantum["id"] != target_quantum["id"]:
            source_quantum["dependencies"].append(
                {"quantum_id": target_quantum["id"], "interaction_id": edge["id"], "status": edge["status"]}
            )
    quanta["unresolved_decisions"] = [
        {
            "id": "DEPLOYMENT-OWNERSHIP-UNKNOWN",
            "question": "Are these proposed responsibility groups independently owned or deployable?",
            "status": "UNKNOWN",
            "evidence_ids": sorted(
                item.id for item in evidence if item.predicate == "independent_deployment_evidence"
            ),
        }
    ]
    quanta["architecture_graph"] = _build_architecture_graph(raw, quanta, interactions, evidence)
    quality = _build_quality(raw, responsibilities, quanta, interactions)

    has_conflict = optimization["result_status"] == "INFEASIBLE"
    constraint_status = "INFEASIBLE" if has_conflict else "PASS"
    candidate_status = (
        "INFEASIBLE"
        if has_conflict
        else "PASS"
        if optimization["selected_candidate_id"]
        else "REVIEW_REQUIRED"
    )
    if optimization.get("solver_backend") == "CP_SAT":
        optimization_summary = (
            f"CP-SAT status {optimization['solver_status']}; reported {optimization['optimal_candidate_count']} "
            f"optimal candidates; complete optimum enumeration={optimization['optimal_candidate_set_complete']}."
        )
    else:
        optimization_summary = (
            f"Enumerated {optimization['enumerated_partition_count']} partitions; "
            f"{optimization['optimal_candidate_count']} optimal candidates."
        )
    source_texts = {
        item.source_ref.source_id: item.text for item in raw.requirements
    }
    source_texts.update({item.source_ref.source_id: item.text for item in raw.workflows})
    source_texts.update({item.source_ref.source_id: item.source_ref.quote for item in raw.scenarios})
    raw_source_spans_valid = all(
        ref.source_id == expected_source_id
        and text[ref.start:ref.end] == ref.quote
        and ref.end - ref.start == len(ref.quote)
        for expected_source_id, text, ref in [
            (item.source_ref.source_id, item.text, item.source_ref) for item in raw.requirements
        ]
        + [
            (item.source_ref.source_id, item.text, item.source_ref) for item in raw.workflows
        ]
        + [
            (item.source_ref.source_id, item.source_ref.quote, item.source_ref) for item in raw.scenarios
        ]
    )
    trace_valid = all(
        ref.source_id in source_texts
        and ref.end <= len(source_texts[ref.source_id])
        and source_texts[ref.source_id][ref.start:ref.end] == ref.quote
        for item in responsibilities
        for ref in item.source_refs
    )
    evidence_sources_valid = all(
        ref.source_id in source_texts
        and ref.end <= len(source_texts[ref.source_id])
        and source_texts[ref.source_id][ref.start:ref.end] == ref.quote
        for item in evidence
        for ref in item.source_refs
    )
    interaction_option_sources_valid = all(
        ref["source_id"] in source_texts
        and ref["end"] <= len(source_texts[ref["source_id"]])
        and source_texts[ref["source_id"]][ref["start"] : ref["end"]] == ref["quote"]
        for edge in interactions["edges"]
        for option in edge.get("options", [])
        for ref in option["source_refs"]
    )
    quality_sources_valid = all(
        ref["source_id"] in source_texts
        and ref["end"] <= len(source_texts[ref["source_id"]])
        and source_texts[ref["source_id"]][ref["start"] : ref["end"]] == ref["quote"]
        for profile in quality["profiles"]
        for ref in [profile["scenario_source_ref"], *(item["source_ref"] for item in profile["evidence"])]
    )
    present_evidence_has_source = all(
        item.status != "PRESENT" or bool(item.source_refs) or item.is_assumption
        for item in evidence
    )
    responsibility_origin = fixture.get("responsibility_provenance", fixture["fixture_label"])
    responsibility_review_complete = bool(
        fixture.get("responsibility_review_complete")
        or (responsibilities and all(item.review_decision_status == "APPROVED" for item in responsibilities))
    )
    requirement_role_counts = {
        requirement_id: sum(requirement_id in item.requirement_ids for item in responsibilities)
        for requirement_id in known_requirement_ids
    }
    unresolved_requirement_ids = sorted(
        fixture.get("unresolved_requirement_ids", [
            requirement_id for requirement_id, count in requirement_role_counts.items() if count == 0
        ])
    )
    derived_unresolved_requirement_ids = sorted(
        requirement_id for requirement_id, count in requirement_role_counts.items() if count == 0
    )
    if unresolved_requirement_ids != derived_unresolved_requirement_ids:
        raise ValueError("Declared unresolved FR IDs must exactly match FRs with zero reviewed responsibilities.")
    responsibility_review_status = (
        "PASS" if responsibility_review_complete and not unresolved_requirement_ids else "REVIEW_REQUIRED"
    )
    report_steps = [
        _step("01", "Context Understanding", "PASS" if len(raw.requirements) >= 5 and raw_source_spans_valid else "FAIL", "Requirement IDs and source spans are present.", ["raw_requirements", "context"]),
        _step(
            "02",
            "Responsibility Identification",
            responsibility_review_status,
            (
                f"Every model responsibility received an explicit disposition; zero-to-many FR mapping is preserved, with unresolved FRs {unresolved_requirement_ids}. This records gate completion, not semantic accuracy."
                if responsibility_review_complete
                else f"{responsibility_origin} records trace to source requirements; semantic interpretation remains review-required."
            ),
            ["responsibilities"],
        ),
        _step("03", "Evidence Modeling", "PASS" if any(item.status == "UNKNOWN" for item in evidence) else "REVIEW_REQUIRED", "Typed evidence keeps UNKNOWN distinct from false.", ["evidence"]),
        _step("04", "Constraint & Quality Reasoning", constraint_status, "Direct hard must/cannot conflicts are reported with their policy IDs.", ["constraints"]),
        _step("05", "Candidate Optimization", candidate_status, optimization_summary, ["partitions"]),
        _step("06", "Quantum Boundary Refinement", quanta["assignment_validation_status"], "Primary assignment is checked for exactly-once coverage; deployability remains unverified.", ["quanta"]),
        _step("07", "Interaction Design — Sync / Async", interactions["status"], "Conditional Sync and Async patterns are listed as hypotheses; protocol selection remains unresolved without consistency and runtime evidence.", ["interactions"]),
        _step("08", "Quality Allocation — QAME", quality["status"], "Each supplied quality scenario is traced to its responsibility and proposed quantum; missing targets and measurements remain explicit.", ["quality_profiles"]),
        _step("09", "Human-in-the-Loop Review", "PASS" if decisions else "REVIEW_REQUIRED", "Every applied change stores actor, reason, source, before/after, and impacts.", ["decisions", "revisions"]),
        _step("10", "Verification & Iteration", "INFEASIBLE" if has_conflict else "REVIEW_REQUIRED", "Local structural and provenance-graph gates ran; no empirical architecture or performance verification is claimed.", ["traceability", "validation_report"]),
    ]
    overall = "INFEASIBLE" if has_conflict else "REVIEW_REQUIRED"
    fixture_optimization_check_applies = (
        constraints_override is None and execution_mode in {"OFFLINE_FIXTURE", "OLLAMA_ASSISTED"}
    )
    validation_report = {
        "status": overall,
        "execution_mode": execution_mode,
        "fixture_label": fixture["fixture_label"],
        "steps": report_steps,
        "assertions": {
            "all_requirements_have_unique_ids": len({item.id for item in raw.requirements}) == len(raw.requirements),
            "all_raw_source_spans_valid": raw_source_spans_valid,
            "all_responsibilities_have_fr_and_source_refs": all(item.requirement_ids and item.source_refs for item in responsibilities),
            "responsibility_review_complete": responsibility_review_complete,
            "fr_responsibility_mapping_is_zero_to_many": (
                requirement_role_counts
                == {
                    requirement_id: sum(requirement_id in item.requirement_ids for item in responsibilities)
                    for requirement_id in known_requirement_ids
                }
                and set(unresolved_requirement_ids) == set(derived_unresolved_requirement_ids)
            ),
            "optimizer_responsibility_cap_respected": (
                len(responsibilities) <= 8
                or optimization.get("solver_backend") == "CP_SAT" and len(responsibilities) <= 50
            ),
            "unknown_is_not_false": any(item.status == "UNKNOWN" for item in evidence),
            "bell_6_count_is_203": (
                optimization["enumerated_partition_count"] == 203
                if len(responsibilities) == 6
                else None
            ),
            "fixture_has_10_zero_cost_optima": (
                (
                    not has_conflict
                    and optimization["optimal_candidate_count"] == 10
                    and optimization["objective_minimum"] == 0
                )
                if fixture_optimization_check_applies
                else None
            ),
            "hard_constraint_conflicts_reported": (not has_conflict) or all(c["constraint_ids"] for c in optimization["conflicts"]),
            "primary_quantum_assignment_exactly_once": quanta["assignment_validation_status"] == "PASS" if responsibilities and optimization["selected_groups"] else None,
            "interaction_decisions_match_contract_state": all(
                (
                    edge["contract"]["selected_mode"] == "UNDECIDED"
                    and edge["label"] == "UNRESOLVED"
                    and edge["selection_status"] == "UNRESOLVED"
                    and all(option["status"] == "PROPOSED_NOT_VERIFIED" for option in edge["options"])
                )
                or (
                    edge["contract"]["selected_mode"] in {"SYNC", "ASYNC"}
                    and edge["label"] == edge["contract"]["selected_mode"]
                    and edge["selection_status"] == "APPROVED"
                    and edge["review_status"] == "APPROVED"
                )
                for edge in interactions["edges"]
            ) if interactions["edges"] else not optimization["feasible_candidate_count"],
            "interaction_option_sources_well_formed": interaction_option_sources_valid,
            "quality_profile_sources_well_formed": quality_sources_valid,
            "quality_scenarios_have_six_part_status": all(
                set(profile["scenario_parts"]) == {
                    "stimulus_source", "stimulus", "environment", "stimulated_artifact", "response", "response_measure"
                }
                and all(part["status"] in {"SPECIFIED", "UNKNOWN", "UNSUPPORTED"} for part in profile["scenario_parts"].values())
                and profile["scenario_completeness"] in {"COMPLETE", "PARTIAL"}
                for profile in quality["profiles"]
            ),
            "quality_scenario_part_citations_resolve": all(
                (
                    part["status"] == "SPECIFIED"
                    and part["source_ref"] is not None
                    and part["value"].strip() in part["source_ref"]["quote"]
                    and part["source_ref"]["source_id"] in source_texts
                    and source_texts[part["source_ref"]["source_id"]][part["source_ref"]["start"] : part["source_ref"]["end"]]
                    == part["source_ref"]["quote"]
                )
                or (
                    part["status"] in {"UNKNOWN", "UNSUPPORTED"}
                    and part["source_ref"] is None
                )
                for profile in quality["profiles"]
                for part in profile["scenario_parts"].values()
            ),
            "quality_scenarios_allocated_without_fake_pass": (
                {profile["scenario_id"] for profile in quality["profiles"]} == {item.id for item in raw.scenarios}
                and all(
                    profile["measurement"] is None
                    and profile["measurement_status"] in {"NOT_MEASURED", "INSUFFICIENT_EVIDENCE"}
                    for profile in quality["profiles"]
                )
            ),
            "responsibility_sources_well_formed": trace_valid,
            "evidence_sources_well_formed": evidence_sources_valid,
            "present_evidence_has_source_or_assumption": present_evidence_has_source,
            "evidence_claim_audit_clear": evidence_audit["status"] == "NO_FINDINGS",
        },
        "assertion_applicability": {
            "fixture_has_10_zero_cost_optima": (
                "APPLIED" if fixture_optimization_check_applies else "NOT_APPLICABLE_AFTER_REVIEW_OR_INPUT_EDIT"
            ),
        },
        "limitations": [
            "Configured constraints are policy inputs; their presence does not establish domain truth.",
            "The selected partition is a deterministic tie-break among equal-cost candidates.",
            "Runtime coupling, release independence, and deployability have not been assessed.",
            "Quality targets have not been measured.",
        ],
    }
    constraint_artifact = {
        "items": constraint_dicts,
        "conflicts": optimization["conflicts"],
        "status": constraint_status,
    }
    if policy_evaluation is not None:
        constraint_artifact["policy_evaluation"] = policy_evaluation
    artifacts = {
        "raw_requirements": raw_dict,
        "context": context,
        "responsibilities": {
            "items": responsibility_dicts,
            "status": responsibility_review_status,
            "provenance": fixture.get("responsibility_provenance", fixture["fixture_label"]),
            "coverage_by_requirement": requirement_role_counts,
            "unresolved_requirement_ids": unresolved_requirement_ids,
            "review_complete": responsibility_review_complete,
        },
        "evidence": {
            "items": evidence_dicts,
            "audit": evidence_audit,
            "status": "PASS" if any(x.status == "UNKNOWN" for x in evidence) else "REVIEW_REQUIRED",
        },
        "relation_registry": {
            "items": [item.model_dump(mode="json") for item in relation_annotations],
            "status": "REVIEW_REQUIRED" if relation_annotations else "INSUFFICIENT_EVIDENCE",
        },
        "constraints": constraint_artifact,
        "partitions": optimization,
        "quanta": quanta,
        "interactions": interactions,
        "quality_profiles": quality,
        "review_request": None,
        "decisions": {"items": deepcopy(decisions or [])},
        "revisions": {"items": deepcopy(revisions or [])},
        "validation_report": validation_report,
        "metadata": {
            "execution_mode": execution_mode,
            "optimizer_backend": optimization.get("solver_backend", "EXHAUSTIVE_ENUMERATOR"),
            "fixture_label": fixture["fixture_label"],
            "fixture_note": fixture["fixture_note"],
            "responsibility_provenance": fixture.get("responsibility_provenance", fixture["fixture_label"]),
        },
    }
    if execution_mode == "EXPLORATORY_UNBLINDED_DEMO":
        validation_report["research_eligibility"] = "EXCLUDED_FROM_BLIND_RESEARCH"
        artifacts["metadata"]["research_eligibility"] = "EXCLUDED_FROM_BLIND_RESEARCH"
        artifacts["metadata"]["demo_status"] = (
            "AWAITING_DEMO_REVIEW" if not decisions else "DEMO_REVIEW_RECORDED"
        )
    refresh_traceability_artifact(artifacts)
    validation_report["assertions"]["traceability_workflow_mappings_explicit"] = artifacts["traceability"][
        "assertions"
    ]["workflow_mapping_gaps_are_explicit"]
    provenance_specs = {
        "raw_requirements": (
            fixture["fixture_label"],
            [],
            "PASS" if raw_source_spans_valid else "FAIL",
            "Schema and exact source-span structure only.",
        ),
        "context": ("DETERMINISTIC_CONTEXT_PROJECTION", ["raw_requirements"], "REVIEW_REQUIRED", "Input coverage is checked; requirement meaning is not accepted."),
        "responsibilities": (
            responsibility_origin,
            ["raw_requirements"],
            "REVIEW_REQUIRED",
            "Requirement/source links are checked; responsibility semantics remain review-required.",
        ),
        "relation_registry": (
            "HUMAN_REVIEWED_TYPED_RELATION_ANNOTATIONS",
            ["raw_requirements", "decisions"],
            "REVIEW_REQUIRED" if relation_annotations else "INSUFFICIENT_EVIDENCE",
            "Relation direction, predicate, source spans, and architecture implication are separate; unannotated pairs are not negative labels.",
        ),
        "evidence": (
            "TYPED_EVIDENCE_RECORDS",
            ["raw_requirements", "responsibilities"],
            "PASS" if evidence_sources_valid and present_evidence_has_source else "FAIL",
            "Typed states, source references, exact duplicate citations, and direct status conflicts are checked structurally; semantics remain unverified.",
        ),
        "constraints": (
            "EXPLICIT_POLICY_AND_REVIEW_RECORDS",
            ["evidence", "responsibilities"],
            constraint_status,
            "Identifiers and hard-constraint consistency are checked; policy truth is not established.",
        ),
        "partitions": (
            "CP_SAT_INTEGER_OPTIMIZER"
            if optimization.get("solver_backend") == "CP_SAT"
            else "DETERMINISTIC_EXHAUSTIVE_ENUMERATION",
            ["responsibilities", "constraints"],
            optimization["result_status"],
            "Set-partition coverage and configured constraints only; architectural quality is not verified.",
        ),
        "quanta": (
            "DERIVED_FROM_SELECTED_PARTITION",
            ["partitions", "responsibilities", "evidence"],
            quanta["status"],
            "Exactly-once responsibility membership only; independent deployment is not verified.",
        ),
        "interactions": (
            "SOURCE_LINKED_CONDITIONAL_PATTERN_HYPOTHESES",
            ["raw_requirements", "quanta"],
            interactions["status"],
            "Citation links and unresolved alternatives only; no Sync/Async choice or contract is verified.",
        ),
        "quality_profiles": (
            "SOURCE_LINKED_SCENARIO_ALLOCATION",
            ["raw_requirements", "responsibilities", "quanta", "interactions"],
            quality["status"],
            "Scenario trace and measurement-state checks only; no empirical quality result is claimed.",
        ),
        "decisions": (
            "HUMAN_REVIEW_AUDIT_LOG",
            ["responsibilities", "evidence", "quanta", "interactions", "quality_profiles"],
            "PASS" if decisions else "REVIEW_REQUIRED",
            "Audit-record presence and fields only; a human action does not certify architecture quality.",
        ),
        "revisions": (
            "HUMAN_REVISION_AUDIT_LOG",
            ["decisions", "constraints", "responsibilities"],
            "PASS" if revisions else "REVIEW_REQUIRED",
            "Before/after and impact records only; revalidation is structural, not empirical.",
        ),
        "validation_report": (
            "NON_LLM_STRUCTURAL_VALIDATION",
            ["raw_requirements", "context", "responsibilities", "evidence", "constraints", "partitions", "quanta", "interactions", "quality_profiles", "decisions", "revisions", "traceability"],
            overall,
            "Local schema, traceability, constraint, allocation, and audit checks only.",
        ),
        "traceability": (
            "EXPLICIT_PROVENANCE_AND_DEPENDENCY_GRAPH",
            ["raw_requirements", "responsibilities", "evidence", "constraints", "partitions", "decisions", "revisions"],
            artifacts["traceability"]["status"],
            "Declared IDs, source spans, review states, dependency links, and candidate membership only; semantic support remains unverified.",
        ),
        "metadata": ("LOCAL_RUN_METADATA", [], "PASS", "Execution-mode and input-label record only."),
    }
    for artifact_name, spec in provenance_specs.items():
        artifacts[artifact_name]["artifact_metadata"] = {
            "provenance": {
                "kind": spec[0],
                "execution_mode": execution_mode,
                "source_artifacts": spec[1],
            },
            "verification_status": spec[2],
            "verification_scope": spec[3],
        }
    validation_report["assertions"]["all_artifacts_have_provenance_and_verification_status"] = all(
        isinstance(payload.get("artifact_metadata"), dict)
        and bool(payload["artifact_metadata"].get("provenance", {}).get("kind"))
        and bool(payload["artifact_metadata"].get("verification_status"))
        and bool(payload["artifact_metadata"].get("verification_scope"))
        for payload in artifacts.values()
        if isinstance(payload, dict)
    )
    return artifacts


def validate_project_package(fixture: dict[str, Any]) -> dict[str, Any]:
    """Reject malformed structured input while preserving unresolved domain questions."""
    artifacts = run_pipeline(fixture, execution_mode="STRUCTURED_INPUT")
    assertions = artifacts["validation_report"]["assertions"]
    required = [
        "all_requirements_have_unique_ids",
        "all_raw_source_spans_valid",
        "all_responsibilities_have_fr_and_source_refs",
        "responsibility_sources_well_formed",
        "evidence_sources_well_formed",
        "traceability_references_resolve",
        "present_evidence_has_source_or_assumption",
    ]
    failures = [name for name in required if not assertions.get(name)]
    if failures:
        raise ValueError(f"Structured input failed validation checks: {', '.join(failures)}.")
    return artifacts
