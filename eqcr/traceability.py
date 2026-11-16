"""Explicit, provenance-preserving links between inputs and derived artifacts."""

from __future__ import annotations

from typing import Any


def build_traceability_graph(artifacts: dict[str, Any]) -> dict[str, Any]:
    raw = artifacts["raw_requirements"]
    sources: dict[str, dict[str, Any]] = {}
    nodes: list[dict[str, Any]] = []
    node_ids: set[str] = set()
    edges: list[dict[str, Any]] = []
    edge_keys: set[tuple[str, str, str]] = set()
    issues: list[dict[str, str]] = []

    def add_node(node_id: str, kind: str, **details: Any) -> None:
        if node_id in node_ids:
            issues.append({"kind": "DUPLICATE_NODE_ID", "reference": node_id})
            return
        node_ids.add(node_id)
        nodes.append({"id": node_id, "kind": kind, **details})

    def add_edge(source: str, target: str, relation: str, **details: Any) -> None:
        if source not in node_ids or target not in node_ids:
            issues.append(
                {
                    "kind": "EDGE_ENDPOINT_MISSING",
                    "reference": f"{source} -> {target}",
                }
            )
            return
        edge_key = (source, target, relation)
        if edge_key in edge_keys:
            return
        edge_keys.add(edge_key)
        edges.append({"from": source, "to": target, "relation": relation, **details})

    def add_input_source(reference: dict[str, Any], *, kind: str, text: str) -> str:
        source_id = reference["source_id"]
        sources[source_id] = {"text": text, "kind": kind}
        node_id = f"source:{source_id}"
        start, end, quote = reference["start"], reference["end"], reference["quote"]
        span_valid = 0 <= start <= end <= len(text) and text[start:end] == quote
        add_node(
            node_id,
            "INPUT_SOURCE",
            source_id=source_id,
            source_kind=kind,
            span_status="EXACT_MATCH" if span_valid else "SPAN_MISMATCH",
            start=start,
            end=end,
            quote=quote,
        )
        return node_id

    context_id = raw.get("context_id")
    if context_id:
        add_node(
            f"context:{context_id}",
            "INITIAL_COMPONENT_CONTEXT",
            context_id=context_id,
            case_id=raw.get("case_id"),
            description=raw.get("context_description"),
            scope_status="INPUT_CONTEXT_ONLY",
        )

    for item in raw["requirements"]:
        requirement_id = f"requirement:{item['id']}"
        source_id = add_input_source(item["source_ref"], kind="REQUIREMENT", text=item["text"])
        add_node(requirement_id, "FUNCTIONAL_REQUIREMENT", requirement_id=item["id"], text=item["text"])
        add_edge(source_id, requirement_id, "SOURCE_FOR")
    for item in raw["workflows"]:
        workflow_id = f"workflow:{item['id']}"
        source_id = add_input_source(item["source_ref"], kind="WORKFLOW", text=item["text"])
        add_node(workflow_id, "WORKFLOW_INPUT", workflow_id=item["id"], text=item["text"])
        add_edge(source_id, workflow_id, "SOURCE_FOR")
    for item in raw["scenarios"]:
        scenario_id = f"scenario:{item['id']}"
        source_id = add_input_source(
            item["source_ref"], kind="QUALITY_SCENARIO", text=item["source_ref"]["quote"]
        )
        add_node(
            scenario_id,
            "QUALITY_SCENARIO_INPUT",
            scenario_id=item["id"],
            name=item["name"],
            target=item.get("target"),
            status=item.get("status"),
        )
        add_edge(source_id, scenario_id, "SOURCE_FOR")

    requirement_ids = {item["id"] for item in raw["requirements"]}
    workflow_ids = {item["id"] for item in raw["workflows"]}
    scenario_ids = {item["id"] for item in raw["scenarios"]}
    responsibility_by_id = {
        item["id"]: item for item in artifacts["responsibilities"]["items"]
    }
    evidence_by_id = {item["id"]: item for item in artifacts["evidence"]["items"]}
    relation_by_id = {
        item["id"]: item for item in artifacts.get("relation_registry", {}).get("items", [])
    }
    constraint_by_id = {item["id"]: item for item in artifacts["constraints"]["items"]}

    def add_citation(
        owner_id: str, reference: dict[str, Any], *, owner_provenance: str
    ) -> bool:
        source_id = reference["source_id"]
        if source_id in sources:
            source = sources[source_id]
            valid = (
                0 <= reference["start"] <= reference["end"] <= len(source["text"])
                and source["text"][reference["start"]:reference["end"]] == reference["quote"]
            )
            source_node_id = f"source:{source_id}"
            citation_status = "EXACT_INPUT_SPAN" if valid else "SPAN_MISMATCH"
        else:
            source_node_id = f"external-source:{source_id}"
            if source_node_id not in node_ids:
                if owner_provenance == "WHAT_IF_POLICY":
                    source_kind = "DECLARED_WHAT_IF_NOTE"
                    citation_status = "INLINE_POLICY_TEXT_NOT_EXTERNALLY_VERIFIED"
                elif owner_provenance == "HUMAN_OVERRIDE":
                    source_kind = "HUMAN_PROVIDED_REASON"
                    citation_status = "HUMAN_PROVIDED_NOT_EXTERNALLY_VERIFIED"
                else:
                    source_kind = "UNRESOLVED_EXTERNAL_SOURCE"
                    citation_status = "EXTERNAL_SOURCE_UNRESOLVED"
                add_node(
                    source_node_id,
                    source_kind,
                    source_id=source_id,
                    quote=reference["quote"],
                    start=reference["start"],
                    end=reference["end"],
                    span_status=citation_status,
                )
            else:
                citation_status = next(
                    node["span_status"] for node in nodes if node["id"] == source_node_id
                )
            valid = citation_status in {
                "INLINE_POLICY_TEXT_NOT_EXTERNALLY_VERIFIED",
                "HUMAN_PROVIDED_NOT_EXTERNALLY_VERIFIED",
            }
        add_edge(owner_id, source_node_id, "CITES", citation_status=citation_status)
        return valid

    responsibility_provenance = artifacts["responsibilities"].get("provenance", "UNKNOWN")
    workflow_mappings: list[dict[str, Any]] = []
    for responsibility_id, item in responsibility_by_id.items():
        node_id = f"responsibility:{responsibility_id}"
        add_node(
            node_id,
            "RESPONSIBILITY_CANDIDATE",
            responsibility_id=responsibility_id,
            name=item["name"],
            origin=responsibility_provenance,
            proposal_id=item.get("proposal_id"),
            review_status=item.get("review_decision_status", "REVIEW_REQUIRED"),
            semantic_status=item.get("semantic_status", "REVIEW_REQUIRED"),
        )
        proposal_id = item.get("proposal_id")
        if proposal_id:
            proposal_node = f"llm-responsibility:{proposal_id}"
            add_node(
                proposal_node,
                "LLM_RESPONSIBILITY_PROPOSAL",
                proposal_id=proposal_id,
                requirement_id=(item.get("requirement_ids") or [None])[0],
                provenance="LOCAL_OLLAMA_UNVERIFIED",
                review_status="REVIEW_REQUIRED",
                source_span_status="RESOLVED_FROM_CANDIDATE_INPUT",
            )
            for requirement_id in item.get("requirement_ids", []):
                if requirement_id in requirement_ids:
                    add_edge(f"requirement:{requirement_id}", proposal_node, "PROPOSED_FROM")
            add_edge(
                proposal_node,
                node_id,
                "USED_AS_UNVERIFIED_CANDIDATE_INPUT",
                review_status="REVIEW_REQUIRED",
            )
            for reference in item.get("source_refs", []):
                add_citation(
                    proposal_node,
                    reference,
                    owner_provenance="LOCAL_OLLAMA_UNVERIFIED",
                )
        for requirement_id in item.get("requirement_ids", []):
            target = f"requirement:{requirement_id}"
            add_edge(target, node_id, "PROPOSES_RESPONSIBILITY_FOR")
        for reference in item.get("source_refs", []):
            if not add_citation(node_id, reference, owner_provenance=responsibility_provenance):
                issues.append(
                    {
                        "kind": "UNRESOLVED_RESPONSIBILITY_CITATION",
                        "reference": responsibility_id,
                    }
                )
        mapped_ids = item.get("workflow_activity_ids", [])
        mapped = bool(mapped_ids) and set(mapped_ids) <= workflow_ids
        mapping_status = "MAPPED" if mapped else "UNRESOLVED"
        workflow_mappings.append(
            {
                "responsibility_id": responsibility_id,
                "workflow_activity_ids": mapped_ids,
                "status": mapping_status,
                "note": item.get("workflow_note", ""),
            }
        )
        for workflow_id in mapped_ids:
            if workflow_id in workflow_ids:
                add_edge(
                    f"workflow:{workflow_id}",
                    node_id,
                    "EXPLICIT_WORKFLOW_MAPPING",
                    status="MAPPED",
                )
            else:
                issues.append(
                    {
                        "kind": "UNKNOWN_WORKFLOW_REFERENCE",
                        "reference": f"{responsibility_id}:{workflow_id}",
                    }
                )

    llm_bundle = artifacts.get("ollama_proposals")
    if isinstance(llm_bundle, dict):
        for item in llm_bundle.get("normalized_requirements", []):
            requirement_id = item.get("id")
            proposal_id = f"normalized-requirement:{requirement_id}"
            add_node(
                proposal_id,
                "LLM_NORMALIZATION_PROPOSAL",
                requirement_id=requirement_id,
                provenance=llm_bundle.get("provenance", "LOCAL_OLLAMA_UNVERIFIED"),
                review_status=item.get("status", "REVIEW_REQUIRED"),
                source_span_status=(
                    "EXACT_INPUT_SPAN" if item.get("source_span_resolved") else "UNRESOLVED"
                ),
            )
            if requirement_id in requirement_ids:
                add_edge(proposal_id, f"requirement:{requirement_id}", "NORMALIZES")
        for item in llm_bundle.get("proposals", []):
            proposal_id = item.get("id", "")
            proposal_node = f"llm-responsibility:{proposal_id}"
            proposal_requirement_ids = item.get("requirement_ids") or [item.get("requirement_id")]
            proposal_node_exists = proposal_node in node_ids
            if proposal_node_exists:
                next(node for node in nodes if node["id"] == proposal_node).update(
                    {
                        "provenance": llm_bundle.get("provenance", "LOCAL_OLLAMA_UNVERIFIED"),
                        "review_status": item.get("status", "REVIEW_REQUIRED"),
                        "source_span_status": (
                            "EXACT_INPUT_SPAN" if item.get("source_spans_resolved") else "UNRESOLVED"
                        ),
                    }
                )
            else:
                add_node(
                    proposal_node,
                    "LLM_RESPONSIBILITY_PROPOSAL",
                    proposal_id=proposal_id,
                    requirement_ids=proposal_requirement_ids,
                    provenance=llm_bundle.get("provenance", "LOCAL_OLLAMA_UNVERIFIED"),
                    review_status=item.get("status", "REVIEW_REQUIRED"),
                    source_span_status=(
                        "EXACT_INPUT_SPAN" if item.get("source_spans_resolved") else "UNRESOLVED"
                    ),
                )
            for requirement_id in proposal_requirement_ids:
                if requirement_id in requirement_ids:
                    add_edge(f"requirement:{requirement_id}", proposal_node, "PROPOSED_FROM")
            responsibility = next(
                (
                    candidate
                    for candidate in responsibility_by_id.values()
                    if candidate.get("proposal_id") == proposal_id
                ),
                None,
            )
            if responsibility:
                add_edge(
                    proposal_node,
                    f"responsibility:{responsibility['id']}",
                    "USED_AS_UNVERIFIED_CANDIDATE_INPUT",
                    review_status="REVIEW_REQUIRED",
                )
            references = item.get("source_refs") or ([item["source_ref"]] if item.get("source_ref") else [])
            for reference in references:
                if not add_citation(
                    proposal_node,
                    reference,
                    owner_provenance="LOCAL_OLLAMA_UNVERIFIED",
                ):
                    issues.append(
                        {"kind": "UNRESOLVED_LLM_CITATION", "reference": proposal_id}
                    )

        for key, kind in (
            ("evidence_proposals", "LLM_EVIDENCE_PROPOSAL"),
            ("boundary_hypotheses", "LLM_BOUNDARY_HYPOTHESIS"),
        ):
            for item in llm_bundle.get(key, []):
                proposal_node = f"{key}:{item.get('id', '')}"
                add_node(
                    proposal_node,
                    kind,
                    provenance=llm_bundle.get("provenance", "LOCAL_OLLAMA_UNVERIFIED"),
                    review_status=item.get("review_status", "REVIEW_REQUIRED"),
                    validation_note=item.get("validation_note", ""),
                )
                cited_ids = item.get("source_requirement_ids", [])
                for requirement_id in cited_ids:
                    if requirement_id in requirement_ids:
                        add_edge(
                            f"requirement:{requirement_id}",
                            proposal_node,
                            "CITED_BY_LLM_PROPOSAL",
                        )
                for reference in item.get("source_refs", []):
                    if not add_citation(
                        proposal_node,
                        reference,
                        owner_provenance="LOCAL_OLLAMA_UNVERIFIED",
                    ):
                        issues.append(
                            {
                                "kind": "UNRESOLVED_LLM_CITATION",
                                "reference": item.get("id", ""),
                            }
                        )

        lock_bundle = llm_bundle.get("blind_annotation_lock")
        if isinstance(lock_bundle, dict) and isinstance(lock_bundle.get("lock"), dict):
            lock = lock_bundle["lock"]
            blind_node = f"blind-annotation:{lock.get('annotation_sha256', '')[:16]}"
            add_node(
                blind_node,
                "BLIND_ANNOTATION_CHECKPOINT",
                annotation_sha256=lock.get("annotation_sha256"),
                source_bundle_sha256=lock.get("source_bundle_sha256"),
                locked_at=lock.get("locked_at"),
                reviewer_id=lock.get("reviewer_id"),
                identity_status=lock.get("identity_status"),
            )
            for item in llm_bundle.get("proposals", []):
                add_edge(
                    blind_node,
                    f"llm-responsibility:{item.get('id', '')}",
                    "LOCKED_BEFORE_MODEL_PROPOSAL_REVIEW",
                )
            for key in ("evidence_proposals", "boundary_hypotheses"):
                for item in llm_bundle.get(key, []):
                    add_edge(
                        blind_node,
                        f"{key}:{item.get('id', '')}",
                        "LOCKED_BEFORE_MODEL_PROPOSAL_REVIEW",
                    )

    for evidence_id, item in evidence_by_id.items():
        evidence_node = f"evidence:{evidence_id}"
        refs = item.get("source_refs", [])
        if item.get("is_assumption"):
            support_status = "DECLARED_ASSUMPTION"
        elif not refs:
            support_status = "NO_SOURCE_REFERENCE"
        else:
            support_status = "SOURCE_REFERENCES_RECORDED"
        add_node(
            evidence_node,
            "EVIDENCE_RELATION",
            predicate=item["predicate"],
            evidence_status=item["status"],
            provenance=item.get("provenance", "UNKNOWN"),
            review_status=item.get("review_status", "REVIEW_REQUIRED"),
            support_status=support_status,
            is_assumption=item.get("is_assumption", False),
        )
        if item["subject_id"] in responsibility_by_id:
            add_edge(
                f"responsibility:{item['subject_id']}",
                evidence_node,
                "HAS_RECORDED_EVIDENCE",
            )
        elif item["subject_id"] in requirement_ids:
            add_edge(
                f"requirement:{item['subject_id']}",
                evidence_node,
                "HAS_RECORDED_EVIDENCE",
            )
        else:
            if item["subject_id"] == context_id and context_id:
                add_edge(
                    f"context:{context_id}",
                    evidence_node,
                    "HAS_SCOPED_EVIDENCE",
                )
            else:
                issues.append(
                    {
                        "kind": "UNKNOWN_EVIDENCE_SUBJECT",
                        "reference": f"{evidence_id}:{item['subject_id']}",
                    }
                )
        if item["object_id"] in requirement_ids:
            add_edge(
                evidence_node,
                f"requirement:{item['object_id']}",
                "RELATES_TO_REQUIREMENT",
            )
        elif item["object_id"] in responsibility_by_id:
            add_edge(
                evidence_node,
                f"responsibility:{item['object_id']}",
                "RELATES_TO_RESPONSIBILITY",
            )
        elif item.get("status") == "SCOPED_ABSENT":
            scoped_concept_node = f"scope-concept:{item['object_id']}"
            if scoped_concept_node not in node_ids:
                add_node(
                    scoped_concept_node,
                    "OUT_OF_SCOPE_CONCEPT",
                    concept_id=item["object_id"],
                    verification_status="NOT_PRESENT_IN_INPUT_SCOPE",
                )
            add_edge(
                evidence_node,
                scoped_concept_node,
                "DECLARES_OUTSIDE_INPUT_SCOPE",
            )
        else:
            issues.append(
                {
                    "kind": "UNKNOWN_EVIDENCE_OBJECT",
                    "reference": f"{evidence_id}:{item['object_id']}",
                }
            )
        for reference in refs:
            if not add_citation(evidence_node, reference, owner_provenance=item.get("provenance", "UNKNOWN")):
                issues.append(
                    {"kind": "UNRESOLVED_EVIDENCE_CITATION", "reference": evidence_id}
                )
    for relation_id, item in relation_by_id.items():
        relation_node = f"relation:{relation_id}"
        add_node(
            relation_node,
            "REVIEWED_RELATION_ANNOTATION",
            predicate=item.get("predicate"),
            direction=item.get("direction"),
            evidence_status=item.get("status"),
            review_status=item.get("review_status"),
            architecture_implication=item.get("architecture_implication"),
            provenance=item.get("provenance"),
        )
        for requirement_id in (item.get("subject_requirement_id"), item.get("object_requirement_id")):
            if requirement_id in requirement_ids:
                add_edge(f"requirement:{requirement_id}", relation_node, "RELATION_ENDPOINT")
        for reference in item.get("source_refs", []):
            if not add_citation(relation_node, reference, owner_provenance=item.get("provenance", "UNKNOWN")):
                issues.append({"kind": "UNRESOLVED_RELATION_CITATION", "reference": relation_id})
        for left, right in item.get("responsibility_pairs", []):
            for responsibility_id in (left, right):
                if responsibility_id in responsibility_by_id:
                    add_edge(
                        relation_node,
                        f"responsibility:{responsibility_id}",
                        "EXPLICIT_ARCHITECTURE_CANDIDATE_ENDPOINT",
                    )

    for evidence_id, item in evidence_by_id.items():
        relation_annotation_id = item.get("relation_annotation_id")
        relation_node = f"relation:{relation_annotation_id}"
        if relation_annotation_id and relation_node in node_ids:
            add_edge(
                relation_node,
                f"evidence:{evidence_id}",
                "MATERIALIZES_REVIEWED_ARCHITECTURE_PAIR",
            )

    constraints_without_evidence: list[dict[str, str]] = []
    for constraint_id, item in constraint_by_id.items():
        constraint_node = f"constraint:{constraint_id}"
        add_node(
            constraint_node,
            "ARCHITECTURE_CONSTRAINT",
            relation=item["relation"],
            hardness=item["hardness"],
            origin=item["origin"],
            enabled=item["enabled"],
            rationale=item["rationale"],
            evidence_ids=item.get("evidence_ids", []),
        )
        for side in ("left", "right"):
            responsibility_id = item[side]
            if responsibility_id in responsibility_by_id:
                add_edge(
                    constraint_node,
                    f"responsibility:{responsibility_id}",
                    "CONSTRAINS_ENDPOINT",
                    endpoint=side,
                )
            else:
                issues.append(
                    {
                        "kind": "UNKNOWN_CONSTRAINT_ENDPOINT",
                        "reference": f"{constraint_id}:{responsibility_id}",
                    }
                )
        for scenario_id in item.get("quality_scenario_ids", []):
            if scenario_id in scenario_ids:
                add_edge(
                    f"scenario:{scenario_id}",
                    constraint_node,
                    "QUALITY_CONTEXT_FOR",
                )
            else:
                issues.append(
                    {"kind": "UNKNOWN_CONSTRAINT_SCENARIO", "reference": f"{constraint_id}:{scenario_id}"}
                )
        for evidence_id in item.get("evidence_ids", []):
            if evidence_id in evidence_by_id:
                evidence = evidence_by_id[evidence_id]
                add_edge(
                    f"evidence:{evidence_id}",
                    constraint_node,
                    "EXPLICIT_EVIDENCE_LINK",
                    evidence_review_status=evidence.get("review_status", "REVIEW_REQUIRED"),
                )
            else:
                issues.append(
                    {"kind": "UNKNOWN_CONSTRAINT_EVIDENCE", "reference": f"{constraint_id}:{evidence_id}"}
                )
        if not item.get("evidence_ids"):
            constraints_without_evidence.append(
                {
                    "constraint_id": constraint_id,
                    "origin": item["origin"],
                    "status": "NO_EXPLICIT_EVIDENCE_LINK",
                }
            )
        for reference in item.get("source_refs", []):
            add_citation(constraint_node, reference, owner_provenance=item["origin"])

    partition_set_node = "partition-set:current"
    partition_data = artifacts["partitions"]
    candidate_rows = partition_data.get("reported_candidates", partition_data["feasible_candidates"])
    candidate_reporting_scope = partition_data.get("candidate_reporting_scope", "ALL_FEASIBLE_PARTITIONS")
    add_node(
        partition_set_node,
        "PARTITION_OPTIMIZATION" if partition_data.get("solver_backend") == "CP_SAT" else "PARTITION_ENUMERATION",
        enumerated_count=partition_data["enumerated_partition_count"],
        feasible_count=partition_data["feasible_candidate_count"],
        optimal_count=partition_data["optimal_candidate_count"],
        candidate_reporting_scope=candidate_reporting_scope,
        optimal_candidate_set_complete=partition_data.get("optimal_candidate_set_complete", True),
        solver_backend=partition_data.get("solver_backend", "EXHAUSTIVE_ENUMERATOR"),
        result_status=partition_data["result_status"],
    )
    partition_node_ids: set[str] = set()
    for candidate in candidate_rows:
        candidate_id = candidate["candidate_id"]
        candidate_node = f"partition:{candidate_id}"
        partition_node_ids.add(candidate_node)
        add_node(
            candidate_node,
            candidate.get("candidate_kind", "FEASIBLE_PARTITION_CANDIDATE"),
            candidate_id=candidate_id,
            groups=candidate["groups"],
            objective_cost=candidate["objective_cost"],
            is_optimal=candidate["is_optimal"],
            selected_for_display=candidate_id == partition_data["selected_candidate_id"],
        )
        add_edge(
            partition_set_node,
            candidate_node,
            "REPORTS_OPTIMAL_CANDIDATE" if candidate_reporting_scope == "OPTIMAL_CANDIDATES_ONLY" else "CONTAINS_FEASIBLE_CANDIDATE",
        )
        for group_index, group in enumerate(candidate["groups"], start=1):
            for responsibility_id in group:
                if responsibility_id in responsibility_by_id:
                    add_edge(
                        f"responsibility:{responsibility_id}",
                        candidate_node,
                        "MEMBER_OF_PARTITION",
                        group_index=group_index,
                    )
                else:
                    issues.append(
                        {
                            "kind": "UNKNOWN_PARTITION_RESPONSIBILITY",
                            "reference": f"{candidate_id}:{responsibility_id}",
                        }
                    )
        for constraint_id, constraint in constraint_by_id.items():
            if not constraint.get("enabled", True):
                continue
            together = any(
                constraint["left"] in group and constraint["right"] in group
                for group in candidate["groups"]
            )
            violated = (
                constraint["relation"] == "MUST_LINK" and not together
            ) or (
                constraint["relation"] == "CANNOT_LINK" and together
            )
            add_edge(
                f"constraint:{constraint_id}",
                candidate_node,
                "VIOLATED_BY_SOFT_RULE" if violated and constraint["hardness"] == "SOFT" else (
                    "SATISFIED_BY" if not violated else "INFEASIBLE_VIOLATION"
                ),
                hardness=constraint["hardness"],
            )

    for conflict_index, conflict in enumerate(partition_data.get("conflicts", []), start=1):
        conflict_node = f"constraint-conflict:{conflict_index}"
        add_node(conflict_node, "CONSTRAINT_CONFLICT", **conflict)
        add_edge(partition_set_node, conflict_node, "REPORTS_CONFLICT")
        for constraint_id in conflict.get("constraint_ids", []):
            if constraint_id in constraint_by_id:
                add_edge(
                    f"constraint:{constraint_id}",
                    conflict_node,
                    "CONTRIBUTES_TO_CONFLICT",
                )

    for quantum in artifacts["quanta"]["quanta"]:
        quantum_node = f"quantum:{quantum['id']}"
        add_node(
            quantum_node,
            "ARCHITECTURAL_QUANTUM_CANDIDATE",
            responsibility_ids=quantum["responsibility_ids"],
            status=quantum["status"],
            review_status=quantum["review_status"],
        )
        for responsibility_id in quantum["responsibility_ids"]:
            if responsibility_id in responsibility_by_id:
                add_edge(
                    f"responsibility:{responsibility_id}",
                    quantum_node,
                    "ASSIGNED_TO_QUANTUM_CANDIDATE",
                )

    for edge in artifacts["interactions"]["edges"]:
        interaction_node = f"interaction:{edge['id']}"
        add_node(
            interaction_node,
            "INTERACTION_HYPOTHESIS",
            label=edge["label"],
            review_status=edge["review_status"],
            selection_status=edge["selection_status"],
        )
        for responsibility_id in edge["responsibility_ids"]:
            if responsibility_id in responsibility_by_id:
                add_edge(
                    f"responsibility:{responsibility_id}",
                    interaction_node,
                    "PARTICIPATES_IN_INTERACTION",
                )
        for reference in edge.get("source_refs", []):
            add_citation(
                interaction_node,
                reference,
                owner_provenance="SOURCE_LINKED_CONDITIONAL_PATTERN_HYPOTHESES",
            )

    for profile in artifacts["quality_profiles"]["profiles"]:
        profile_node = f"quality-profile:{profile['scenario_id']}"
        add_node(
            profile_node,
            "QUALITY_PROFILE_CANDIDATE",
            scenario_id=profile["scenario_id"],
            target=profile.get("target"),
            measurement_status=profile["measurement_status"],
            review_status=profile["review_status"],
        )
        scenario_node = f"scenario:{profile['scenario_id']}"
        if scenario_node in node_ids:
            add_edge(scenario_node, profile_node, "ALLOCATED_AS_QUALITY_PROFILE")
        for responsibility_id in profile.get("responsibility_ids", []):
            if responsibility_id in responsibility_by_id:
                add_edge(
                    f"responsibility:{responsibility_id}",
                    profile_node,
                    "QUALITY_SCOPE",
                )
        for reference in [
            profile["scenario_source_ref"],
            *(item["source_ref"] for item in profile["evidence"]),
        ]:
            add_citation(
                profile_node,
                reference,
                owner_provenance="SOURCE_LINKED_SCENARIO_ALLOCATION",
            )

    artifact_nodes = {
        "responsibilities": {item: f"responsibility:{item}" for item in responsibility_by_id},
        "evidence": {item: f"evidence:{item}" for item in evidence_by_id},
        "relation_registry": {item: f"relation:{item}" for item in relation_by_id},
        "constraints": {item: f"constraint:{item}" for item in constraint_by_id},
        "quanta": {item["id"]: f"quantum:{item['id']}" for item in artifacts["quanta"]["quanta"]},
        "interactions": {
            item["id"]: f"interaction:{item['id']}" for item in artifacts["interactions"]["edges"]
        },
        "quality_profiles": {
            item["scenario_id"]: f"quality-profile:{item['scenario_id']}"
            for item in artifacts["quality_profiles"]["profiles"]
        },
    }
    decision_nodes: dict[str, str] = {}
    for item in artifacts["decisions"]["items"]:
        decision_id = item.get("decision_id", "UNKNOWN")
        node_id = f"decision:{decision_id}"
        decision_nodes[decision_id] = node_id
        add_node(
            node_id,
            "HUMAN_DECISION",
            action=item.get("action"),
            actor=item.get("actor"),
            reason=item.get("reason"),
            source=item.get("source"),
            result=item.get("result"),
        )
        artifact_name = item.get("target_artifact")
        object_id = item.get("object_id")
        if not artifact_name:
            artifact_name = {"02": "responsibilities", "04": "constraints"}.get(
                item.get("target_step")
            )
        target_node = artifact_nodes.get(artifact_name, {}).get(object_id)
        if not target_node and artifact_name in {"constraints", "responsibilities"}:
            target_node = f"artifact:{artifact_name}"
            if target_node not in node_ids:
                add_node(target_node, "ARTIFACT_COLLECTION", artifact=artifact_name)
        if target_node:
            add_edge(node_id, target_node, "REVIEWS_OR_CHANGES")
        source_label = item.get("source")
        if source_label:
            source_node = f"external-source:{source_label}"
            if source_node not in node_ids:
                add_node(
                    source_node,
                    "HUMAN_PROVIDED_REASON",
                    source_id=source_label,
                    span_status="HUMAN_PROVIDED_NOT_EXTERNALLY_VERIFIED",
                )
            add_edge(node_id, source_node, "HAS_REVIEW_SOURCE")

    for item in artifacts["revisions"]["items"]:
        revision_id = item.get("revision_id", "UNKNOWN")
        revision_node = f"revision:{revision_id}"
        add_node(
            revision_node,
            "HUMAN_REVISION",
            target_step=item.get("target_step"),
            object_id=item.get("object_id"),
            before=item.get("before"),
            after=item.get("after"),
            invalidated_artifacts=item.get("invalidated_artifacts", []),
            recomputed_artifacts=item.get("recomputed_artifacts", []),
        )
        decision_node = decision_nodes.get(item.get("decision_id"))
        if decision_node:
            add_edge(decision_node, revision_node, "RECORDED_AS_REVISION")
        for artifact_name in item.get("affected_artifacts", []):
            artifact_node = f"artifact:{artifact_name}"
            if artifact_node not in node_ids:
                add_node(artifact_node, "ARTIFACT_COLLECTION", artifact=artifact_name)
            add_edge(revision_node, artifact_node, "AFFECTS_ARTIFACT")

    assertions = {
        "node_ids_are_unique": len(nodes) == len(node_ids),
        "all_edge_endpoints_resolve": not any(
            edge["from"] not in node_ids or edge["to"] not in node_ids for edge in edges
        ),
        "responsibility_requirement_links_resolve": all(
            requirement_id in requirement_ids
            for item in responsibility_by_id.values()
            for requirement_id in item.get("requirement_ids", [])
        ),
        "evidence_review_status_is_preserved": all(
            any(
                node["id"] == f"evidence:{evidence_id}"
                and node["review_status"] == item.get("review_status", "REVIEW_REQUIRED")
                for node in nodes
            )
            for evidence_id, item in evidence_by_id.items()
        ),
        "relation_registry_endpoints_and_sources_resolve": not any(
            issue["kind"] in {"UNRESOLVED_RELATION_CITATION"}
            for issue in issues
        ) and all(
            item.get("subject_requirement_id") in requirement_ids
            and item.get("object_requirement_id") in requirement_ids
            for item in relation_by_id.values()
        ),
        "constraint_endpoints_and_evidence_links_resolve": not any(
            issue["kind"] in {
                "UNKNOWN_CONSTRAINT_ENDPOINT",
                "UNKNOWN_CONSTRAINT_EVIDENCE",
                "UNKNOWN_CONSTRAINT_SCENARIO",
            }
            for issue in issues
        ),
        "all_feasible_candidates_are_linked": (
            len(partition_node_ids) == partition_data["feasible_candidate_count"]
            if candidate_reporting_scope == "ALL_FEASIBLE_PARTITIONS"
            and partition_data["feasible_candidate_count"] is not None
            else None
        ),
        "all_reported_partition_candidates_are_linked": len(partition_node_ids) == len(candidate_rows),
        "workflow_mapping_gaps_are_explicit": len(workflow_mappings)
        == len(responsibility_by_id)
        and all(item["status"] in {"MAPPED", "UNRESOLVED"} for item in workflow_mappings),
        "input_and_evidence_citations_resolve": not any(
            issue["kind"]
            in {
                "UNRESOLVED_EVIDENCE_CITATION",
                "UNRESOLVED_RESPONSIBILITY_CITATION",
                "UNRESOLVED_LLM_CITATION",
                "EDGE_ENDPOINT_MISSING",
            }
            for issue in issues
        )
        and all(
            node.get("span_status") != "SPAN_MISMATCH"
            for node in nodes
            if node["kind"] == "INPUT_SOURCE"
        ),
        "no_unresolved_reference_issues": not issues,
    }
    all_valid = all(value is not False for value in assertions.values())
    return {
        "status": "PASS" if all_valid else "FAIL",
        "review_status": "REVIEW_REQUIRED",
        "nodes": nodes,
        "edges": edges,
        "workflow_mappings": workflow_mappings,
        "constraints_without_evidence_links": constraints_without_evidence,
        "unresolved_issues": issues,
        "summary": {
            "node_count": len(nodes),
            "edge_count": len(edges),
            "input_source_count": len(sources),
            "responsibility_count": len(responsibility_by_id),
            "evidence_count": len(evidence_by_id),
            "relation_annotation_count": len(relation_by_id),
            "constraint_count": len(constraint_by_id),
            "feasible_partition_count": len(partition_node_ids),
            "reported_partition_count": len(candidate_rows),
        },
        "assertions": assertions,
        "note": (
            "Links describe recorded references and transformations. They do not prove semantic support, "
            "policy truth, architecture quality, or empirical verification. CP-SAT reports only the optimal subset, "
            "so graph linkage does not imply that all feasible partitions were enumerated."
        ),
    }


def refresh_traceability_artifact(artifacts: dict[str, Any]) -> dict[str, Any]:
    graph = build_traceability_graph(artifacts)
    graph["artifact_metadata"] = {
        "provenance": {
            "kind": "EXPLICIT_PROVENANCE_AND_DEPENDENCY_GRAPH",
            "execution_mode": artifacts["metadata"]["execution_mode"],
            "source_artifacts": [
                "raw_requirements",
                "responsibilities",
                "evidence",
                "relation_registry",
                "constraints",
                "partitions",
                "decisions",
                "revisions",
            ],
        },
        "verification_status": graph["status"],
        "verification_scope": (
            "Graph endpoint, declared ID/reference, review-state, source-span, and candidate-membership checks only; "
            "semantic support and architecture quality remain unverified."
        ),
    }
    artifacts["traceability"] = graph
    report = artifacts.get("validation_report")
    if isinstance(report, dict):
        report.setdefault("assertions", {})["traceability_references_resolve"] = graph["assertions"][
            "no_unresolved_reference_issues"
        ]
        report["assertions"]["traceability_graph_well_formed"] = graph["status"] == "PASS"
    return artifacts
