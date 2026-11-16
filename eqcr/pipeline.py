"""Deterministic validation, exhaustive candidate generation, and quality tracing."""

from __future__ import annotations

from collections import defaultdict
from copy import deepcopy
from typing import Any, Iterable, Iterator

import networkx as nx

from .models import Constraint, EvidenceConstraintPolicy, EvidenceRecord, RawRequirements, Responsibility
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
    all_partitions = list(_partitions(responsibility_ids))
    active_hard = [c for c in constraints if c.enabled and c.hardness == "HARD"]
    active_soft = [c for c in constraints if c.enabled and c.hardness == "SOFT"]
    feasible: list[dict[str, Any]] = []
    for partition in all_partitions:
        if any(
            (c.relation == "MUST_LINK" and not _same_group(partition, c.left, c.right))
            or (c.relation == "CANNOT_LINK" and _same_group(partition, c.left, c.right))
            for c in active_hard
        ):
            continue
        cost = sum(
            c.weight
            for c in active_soft
            if (c.relation == "MUST_LINK" and not _same_group(partition, c.left, c.right))
            or (c.relation == "CANNOT_LINK" and _same_group(partition, c.left, c.right))
        )
        feasible.append({"groups": [list(g) for g in partition], "objective_cost": cost})

    conflicts = _constraint_conflicts(constraints)
    if not feasible and not conflicts:
        conflicts.append(
            {
                "pair": [],
                "constraint_ids": [c.id for c in active_hard],
                "relations": sorted({c.relation for c in active_hard}),
                "status": "INFEASIBLE",
                "reason": "No partition satisfies the active hard constraints together.",
            }
        )
    if feasible:
        min_cost = min(item["objective_cost"] for item in feasible)
        optimal = [item for item in feasible if item["objective_cost"] == min_cost]
    else:
        min_cost = None
        optimal = []
    for index, candidate in enumerate(feasible, start=1):
        candidate["candidate_id"] = f"P{index:03d}"
        candidate["is_optimal"] = candidate["objective_cost"] == min_cost

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
        "bell_number_expected": 203 if len(responsibility_ids) == 6 else None,
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
    policies: list[dict[str, Any]],
    source_texts: dict[str, str],
) -> list[Constraint]:
    """Apply declared soft policies only to human-approved evidence and responsibilities."""
    validated_policies = [EvidenceConstraintPolicy.model_validate(item) for item in policies]
    responsibility_by_id = {item.id: item for item in responsibilities}
    requirement_by_id = {item.id: item for item in raw.requirements}
    derived = []
    seen = set()
    for policy in validated_policies:
        for record in evidence:
            if (
                record.predicate != policy.evidence_predicate
                or record.status != "PRESENT"
                or record.review_status != "APPROVED"
                or not record.source_refs
            ):
                continue
            left, right = record.subject_id, record.object_id
            if left == right or left not in responsibility_by_id or right not in responsibility_by_id:
                continue
            if any(
                responsibility_by_id[rid].review_decision_status != "APPROVED"
                for rid in (left, right)
            ):
                continue
            source_refs_valid = all(
                ref.source_id in source_texts
                and ref.end <= len(source_texts[ref.source_id])
                and source_texts[ref.source_id][ref.start:ref.end] == ref.quote
                for ref in record.source_refs
            )
            endpoint_sources = {
                requirement.source_ref.source_id
                for responsibility_id in (left, right)
                for requirement_id in responsibility_by_id[responsibility_id].requirement_ids
                for requirement in [requirement_by_id.get(requirement_id)]
                if requirement is not None
            }
            cited_sources = {ref.source_id for ref in record.source_refs}
            if not source_refs_valid or not endpoint_sources or not endpoint_sources <= cited_sources:
                continue
            key = (policy.id, tuple(sorted((left, right))))
            if key in seen:
                continue
            seen.add(key)
            derived.append(
                Constraint(
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
                        f"Policy {policy.id}: {policy.rationale} "
                        f"Applied to reviewer-approved evidence {record.id}."
                    ),
                )
            )
    return derived


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
    return {
        "selected_candidate_id": None,
        "quanta": quanta,
        "primary_assignment": assignment,
        "membership_counts": membership_counts,
        "assignment_validation_status": "PASS" if all(count == 1 for count in membership_counts.values()) else "INFEASIBLE",
        "status": "PROPOSED_NOT_VERIFIED" if all(count == 1 for count in membership_counts.values()) else "INFEASIBLE",
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
    requirement_to_responsibility = {
        requirement_id: responsibility.id
        for responsibility in responsibilities
        for requirement_id in responsibility.requirement_ids
    }
    interactions = []
    for scenario in raw.scenarios:
        if len(scenario.related_requirement_ids) < 2:
            continue
        ids = [requirement_to_responsibility[item] for item in scenario.related_requirement_ids]
        for left, right in zip(ids, ids[1:]):
            left_quantum, right_quantum = assignment.get(left), assignment.get(right)
            if not left_quantum or not right_quantum:
                continue
            edge_id = scenario.interaction_id if len(ids) == 2 and scenario.interaction_id else f"EDGE-{scenario.id}-{left}-{right}"
            interactions.append((scenario, left, right, left_quantum, right_quantum, edge_id))
    if not interactions:
        return {
            "edges": [],
            "graph_summary": {"node_count": graph.number_of_nodes(), "directed_edge_count": 0},
            "status": "INSUFFICIENT_EVIDENCE",
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
                "contract": {
                    "operation": "UNKNOWN",
                    "data_dependency": "UNKNOWN",
                    "request_fields": "UNKNOWN",
                    "response_fields": "UNKNOWN",
                    "versioning": "UNKNOWN",
                    "retry_policy": "UNKNOWN",
                    "timeout_policy": "UNKNOWN",
                    "idempotency_policy": "UNKNOWN",
                },
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
    }


def _build_quality(raw: RawRequirements, responsibilities: list[Responsibility], quanta: dict[str, Any]) -> dict[str, Any]:
    assignment = quanta["primary_assignment"]
    requirement_to_responsibility = {
        requirement_id: responsibility.id
        for responsibility in responsibilities
        for requirement_id in responsibility.requirement_ids
    }
    profiles = []
    for scenario in raw.scenarios:
        responsibility_ids = [
            requirement_to_responsibility[item]
            for item in scenario.related_requirement_ids
            if item in requirement_to_responsibility
        ]
        quantum_ids = sorted({assignment[item] for item in responsibility_ids if item in assignment})
        requirement_refs = [
            next(item for item in raw.requirements if item.id == requirement_id).source_ref.model_dump(mode="json")
            for requirement_id in scenario.related_requirement_ids
        ]
        affected_edges = [
            edge["id"] for edge in _build_interactions(quanta, raw, responsibilities)["edges"]
            if set(edge["responsibility_ids"]) <= set(responsibility_ids)
        ]
        measured_target = scenario.target is not None and bool(scenario.proposed_metric or scenario.response_measure)
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
                "target": scenario.target,
                "proposed_metric": scenario.proposed_metric,
                "measurement_method": scenario.measurement_method,
                "measurement_plan_status": "PROPOSED" if measured_target and scenario.measurement_method else "INSUFFICIENT_EVIDENCE",
                "provenance": "SOURCE_BACKED_SCENARIO_TRACE",
                "evidence": [
                    {
                        "kind": "TARGET_SOURCE" if scenario.target is not None else "SCENARIO_SOURCE",
                        "source_ref": scenario.source_ref.model_dump(mode="json"),
                    },
                    *({"kind": "REQUIREMENT_SOURCE", "source_ref": ref} for ref in requirement_refs),
                ],
                "affected_interaction_edges": affected_edges,
                "measurement_status": "NOT_MEASURED" if measured_target else "INSUFFICIENT_EVIDENCE",
                "review_status": "REVIEW_REQUIRED",
                "measurement": None,
                "trace_status": "PASS" if responsibility_ids and len(quantum_ids) >= 1 else "INSUFFICIENT_EVIDENCE",
                "note": (
                    "Scenario target is source-backed; no benchmark has been run."
                    if measured_target
                    else "Scenario provides no measurable target and method; no pass/fail result is inferred."
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
        },
        {
            "id": "PRESENTATION-UNKNOWN",
            "layer": "PRESENTATION_APPLICATION",
            "label": "Presentation / application tier not specified",
            "status": "UNKNOWN",
            "evidence_ids": runtime_evidence_ids,
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
            "id": "INFRASTRUCTURE-UNKNOWN",
            "layer": "INFRASTRUCTURE_STORAGE",
            "label": "Infrastructure / storage not specified",
            "status": "UNKNOWN",
            "evidence_ids": runtime_evidence_ids,
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
                    },
                    {
                        "id": f"EDGE-{quantum['id']}-INFRASTRUCTURE-UNKNOWN",
                        "from": quantum["id"],
                        "to": "INFRASTRUCTURE-UNKNOWN",
                        "label": "UNKNOWN",
                        "status": "UNKNOWN",
                        "rationale": "No infrastructure or storage relationship was supplied.",
                    },
                ]
            )
    edges.extend(
        {
            "id": item["id"],
            "from": item["from_quantum"],
            "to": item["to_quantum"],
            "label": item["label"],
            "status": item["status"],
            "rationale": item["rationale"],
        }
        for item in interactions["edges"]
    )
    return {
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
    responsibility_ids = [item.id for item in responsibilities]
    if len(responsibility_ids) != len(set(responsibility_ids)):
        raise ValueError("Responsibility IDs must be unique.")
    known_requirement_ids = {item.id for item in raw.requirements}
    for responsibility in responsibilities:
        unknown_requirements = set(responsibility.requirement_ids) - known_requirement_ids
        if unknown_requirements:
            raise ValueError(
                f"{responsibility.id} references unknown requirement IDs: {sorted(unknown_requirements)}."
            )
    selected_constraints = fixture["constraints"] if constraints_override is None else constraints_override
    if constraints_override is None:
        constraint_source_texts = {
            item.source_ref.source_id: item.text for item in raw.requirements
        }
        constraint_source_texts.update({item.source_ref.source_id: item.text for item in raw.workflows})
        constraint_source_texts.update(
            {item.source_ref.source_id: item.source_ref.quote for item in raw.scenarios}
        )
        selected_constraints = [
            *selected_constraints,
            *[
                item.model_dump(mode="json")
                for item in _derive_evidence_constraints(
                    raw,
                    evidence,
                    responsibilities,
                    fixture.get("constraint_policies", []),
                    constraint_source_texts,
                )
            ],
        ]
    constraints = [Constraint.model_validate(item) for item in selected_constraints]
    known_responsibility_ids = set(responsibility_ids)
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
    quality = _build_quality(raw, responsibilities, quanta)

    has_conflict = bool(optimization["conflicts"]) or optimization["feasible_candidate_count"] == 0
    constraint_status = "INFEASIBLE" if has_conflict else "PASS"
    candidate_status = "INFEASIBLE" if not optimization["feasible_candidate_count"] else "PASS"
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
    report_steps = [
        _step("01", "Context Understanding", "PASS" if len(raw.requirements) >= 5 and raw_source_spans_valid else "FAIL", "Requirement IDs and source spans are present.", ["raw_requirements", "context"]),
        _step(
            "02",
            "Responsibility Identification",
            "PASS" if all(item.review_decision_status == "APPROVED" for item in responsibilities) else "REVIEW_REQUIRED",
            (
                "All responsibility items have an APPROVED reviewer decision; this records completion of the review gate, not semantic accuracy."
                if all(item.review_decision_status == "APPROVED" for item in responsibilities)
                else f"{responsibility_origin} records trace to source requirements; semantic interpretation remains review-required."
            ),
            ["responsibilities"],
        ),
        _step("03", "Evidence Modeling", "PASS" if any(item.status == "UNKNOWN" for item in evidence) else "REVIEW_REQUIRED", "Typed evidence keeps UNKNOWN distinct from false.", ["evidence"]),
        _step("04", "Constraint & Quality Reasoning", constraint_status, "Direct hard must/cannot conflicts are reported with their policy IDs.", ["constraints"]),
        _step("05", "Candidate Optimization", candidate_status, f"Enumerated {optimization['enumerated_partition_count']} partitions; {optimization['optimal_candidate_count']} optimal candidates.", ["partitions"]),
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
            "unknown_is_not_false": any(item.status == "UNKNOWN" for item in evidence),
            "bell_6_count_is_203": optimization["enumerated_partition_count"] == 203,
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
            "primary_quantum_assignment_exactly_once": quanta["assignment_validation_status"] == "PASS" if optimization["selected_groups"] else False,
            "interaction_unresolved_without_decision": all(
                edge["label"] == "UNRESOLVED"
                and edge["selection_status"] == "UNRESOLVED"
                and all(option["status"] == "PROPOSED_NOT_VERIFIED" for option in edge["options"])
                for edge in interactions["edges"]
            ) if interactions["edges"] else not optimization["feasible_candidate_count"],
            "interaction_option_sources_well_formed": interaction_option_sources_valid,
            "quality_profile_sources_well_formed": quality_sources_valid,
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
    artifacts = {
        "raw_requirements": raw_dict,
        "context": context,
        "responsibilities": {
            "items": responsibility_dicts,
            "status": "REVIEW_REQUIRED",
            "provenance": fixture.get("responsibility_provenance", fixture["fixture_label"]),
        },
        "evidence": {"items": evidence_dicts, "status": "PASS" if any(x.status == "UNKNOWN" for x in evidence) else "REVIEW_REQUIRED"},
        "constraints": {"items": constraint_dicts, "conflicts": optimization["conflicts"], "status": constraint_status},
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
            "fixture_label": fixture["fixture_label"],
            "fixture_note": fixture["fixture_note"],
            "responsibility_provenance": fixture.get("responsibility_provenance", fixture["fixture_label"]),
        },
    }
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
        "evidence": (
            "TYPED_EVIDENCE_RECORDS",
            ["raw_requirements", "responsibilities"],
            "PASS" if evidence_sources_valid and present_evidence_has_source else "FAIL",
            "Typed states and source references are checked; runtime relations are not verified.",
        ),
        "constraints": (
            "EXPLICIT_POLICY_AND_REVIEW_RECORDS",
            ["evidence", "responsibilities"],
            constraint_status,
            "Identifiers and hard-constraint consistency are checked; policy truth is not established.",
        ),
        "partitions": (
            "DETERMINISTIC_EXHAUSTIVE_ENUMERATION",
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
