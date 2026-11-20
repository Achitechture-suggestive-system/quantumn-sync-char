"""Optional, evidence-gated quality analysis over the existing EQCR optimizer."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
import re
from typing import Literal

from pydantic import Field

from .iso_quality import ARCHITECTURE_DRIVERS, iso_registry, iso_subcharacteristics
from .models import Constraint, EvidenceRecord, RawRequirements, Responsibility, SourceRef, StrictModel
from .quality_interactions import InteractionAssessment, interaction_profile, propose_mode, validate_interaction
from .requirements_engine import (
    AtomicRequirementReview, RequirementDocument, ReviewRecord, classify_documents, require_span,
)

POLICY_ID = "EQCR-QUALITY-DECOMPOSITION"
POLICY_VERSION = "1.0.0"
COST_AXES = (
    "Configured soft penalty", "Accepted NFR scopes cut", "Approved workflow crossings",
    "Approved synchronous crossings", "Unresolved or unreviewed crossings",
)
ScenarioPart = Literal["stimulus_source", "stimulus", "environment", "artifact", "response", "response_measure"]
SCENARIO_PARTS = ("stimulus_source", "stimulus", "environment", "artifact", "response", "response_measure")
ACCEPTED = {"SOURCE_CONFIRMED", "HUMAN_APPROVED"}

COUPLING_PREDICATES = {
    "functional_cohesion": ("FUNCTIONAL_COHESION",),
    "workflow_dependency": ("WORKFLOW_DEPENDENCY", "BUSINESS_PRECEDES"),
    "domain_invariant": ("DOMAIN_INVARIANT", "SHARES_STATE_OR_INVARIANT", "VERIFIED_ATOMIC_INVARIANT"),
    "transactional_coupling": ("TRANSACTIONAL_COUPLING", "INDIVISIBLE_TRANSACTION"),
    "data_write_ownership": ("DATA_OWNERSHIP", "SHARED_WRITE", "SHARED_TABLE"),
    "static_dependency": ("STATIC_DEPENDENCY",),
    "synchronous_runtime": ("SYNCHRONOUS_RUNTIME",),
    "change_propagation": ("CHANGE_PROPAGATION", "REQUIRES_INDEPENDENT_CHANGE"),
    "security_boundary": ("SECURITY_BOUNDARY", "MANDATORY_SEPARATION"),
    "failure_propagation": ("FAILURE_PROPAGATION",),
    "scalability_independence": ("SCALABILITY_INDEPENDENCE",),
    "independent_deployability": ("INDEPENDENT_DEPLOYMENT_EVIDENCE",),
    "quality_scenario_interaction": ("QUALITY_SCENARIO_INTERACTION",),
}


class ScopePreference(StrictModel):
    relation: Literal["MUST_LINK", "CANNOT_LINK"]
    left: str
    right: str
    weight: float = Field(gt=0, allow_inf_nan=False)


class LatencyAllocation(StrictModel):
    kind: Literal["RESPONSIBILITY", "COMMUNICATION"]
    subject_id: str
    milliseconds: int = Field(ge=0)
    source_ref: SourceRef


class LatencyObservation(StrictModel):
    run_id: str = Field(min_length=1)
    metric: str = Field(min_length=1)
    milliseconds: int = Field(ge=0)
    source_ref: SourceRef
    review: ReviewRecord


class QualityScenarioInput(StrictModel):
    id: str = Field(min_length=1)
    nfr_id: str
    parts: dict[ScenarioPart, SourceRef] = Field(default_factory=dict)
    fr_ids: list[str] = Field(default_factory=list)
    responsibility_ids: list[str] = Field(default_factory=list)
    subcharacteristic_ids: list[str] = Field(default_factory=list)
    architecture_driver_ids: list[str] = Field(default_factory=list)
    target: SourceRef | None = None
    priority: SourceRef | None = None
    measurement_method: str | None = None
    assumptions: list[str] = Field(default_factory=list)
    review: ReviewRecord | None = None
    preferences: list[ScopePreference] = Field(default_factory=list)
    latency_ceiling_ms: int | None = Field(default=None, gt=0)
    latency_allocations: list[LatencyAllocation] = Field(default_factory=list)
    latency_observation: LatencyObservation | None = None


class HardConstraintReview(ReviewRecord):
    constraint_id: str
    requirement_atomic_id: str
    justification: SourceRef
    alternative_considered: str = Field(min_length=1)


class QualityDecompositionInput(StrictModel):
    source_documents: list[RequirementDocument] = Field(default_factory=list)
    classification_reviews: list[AtomicRequirementReview] = Field(default_factory=list)
    scenarios: list[QualityScenarioInput] = Field(default_factory=list)
    interactions: list[InteractionAssessment] = Field(default_factory=list)
    hard_constraint_reviews: list[HardConstraintReview] = Field(default_factory=list)

    def source_texts(self) -> dict[str, str]:
        sources = {item.id: item.text for item in self.source_documents}
        if len(sources) != len(self.source_documents):
            raise ValueError("Quality source document IDs must be unique.")
        return sources


@dataclass
class PreparedQualityDecomposition:
    constraints: list[Constraint]
    report: dict
    interactions: list[InteractionAssessment]
    evidence: list[EvidenceRecord]
    roles: dict[str, Responsibility]
    blocked_evidence_ids: set[str]


def _require_atomic_span(ref: SourceRef, atom: dict, texts: dict[str, str]) -> None:
    require_span(ref, texts)
    source = atom["source_ref"]
    if ref.source_id != source["source_id"] or not source["start"] <= ref.start < ref.end <= source["end"]:
        raise ValueError(f"{ref.source_id} span must be inside atomic requirement {atom['atomic_id']}.")


def _ms_in_span(value: int, ref: SourceRef) -> bool:
    return bool(re.search(rf"(?<![\w.,]){value}\s*ms\b", ref.quote, re.IGNORECASE))


def _scenario_row(scenario: QualityScenarioInput, atoms: dict, roles: dict[str, Responsibility],
                  fr_ids: set[str], texts: dict[str, str], taxonomy: dict, interactions: dict,
                  observation_sources: set[str]) -> dict:
    atom = atoms.get(scenario.nfr_id)
    if atom is None or atom["requirement_type"] != "NFR":
        raise ValueError(f"{scenario.id} must reference an atomic NFR.")
    if not set(scenario.fr_ids) <= fr_ids or not set(scenario.responsibility_ids) <= roles.keys():
        raise ValueError(f"{scenario.id} references an unknown FR or responsibility.")
    if any(not (set(roles[role].requirement_ids) & set(scenario.fr_ids)) for role in scenario.responsibility_ids):
        raise ValueError(f"{scenario.id} responsibility allocation must trace to its related FRs.")
    if not set(scenario.subcharacteristic_ids) <= taxonomy.keys() or not set(scenario.architecture_driver_ids) <= ARCHITECTURE_DRIVERS.keys():
        raise ValueError(f"{scenario.id} has an unknown ISO ID or architecture driver.")
    if len(set(scenario.subcharacteristic_ids)) != len(scenario.subcharacteristic_ids):
        raise ValueError(f"{scenario.id} contains duplicate ISO subcharacteristics.")
    for ref in [*scenario.parts.values(), scenario.target, scenario.priority]:
        if ref is not None:
            _require_atomic_span(ref, atom, texts)
    accepted = atom["review_status"] in ACCEPTED
    if scenario.review and not accepted:
        raise ValueError(f"{scenario.id} review requires an accepted source NFR.")
    scoped = set(scenario.responsibility_ids)
    related_edges = {key for key, item in interactions.items() if {item.caller, item.callee} <= scoped}
    budgeted = set()
    for allocation in scenario.latency_allocations:
        require_span(allocation.source_ref, texts)
        valid_ids = scoped if allocation.kind == "RESPONSIBILITY" else related_edges
        key = (allocation.kind, allocation.subject_id)
        if allocation.subject_id not in valid_ids or key in budgeted or not _ms_in_span(allocation.milliseconds, allocation.source_ref):
            raise ValueError(f"{scenario.id} has an unsupported, duplicate, or out-of-scope latency allocation.")
        budgeted.add(key)
    total_ms = sum(item.milliseconds for item in scenario.latency_allocations)
    if scenario.latency_ceiling_ms is not None and (
        not scenario.target or not re.search(
            rf"(?:<=|≤|at most|no more than|tối đa|không quá)\s*{scenario.latency_ceiling_ms}\s*ms\b",
            scenario.target.quote, re.IGNORECASE,
        )
        or total_ms > scenario.latency_ceiling_ms
    ):
        raise ValueError(f"{scenario.id} latency ledger exceeds or lacks its cited end-to-end ceiling.")
    source_text = atom["source_ref"]["quote"].casefold()
    scope_is_cited = bool(scoped) and all(
        re.search(rf"(?<!\w){re.escape(role.casefold())}(?!\w)", source_text) for role in scoped
    )
    mappings = [{
        **taxonomy[key], "mapping_status": (
            "HUMAN_APPROVED" if scenario.review else "SOURCE_CONFIRMED"
            if accepted and (key.casefold() in source_text or taxonomy[key]["name"].casefold() in source_text)
            else "PROPOSED"
        ),
    } for key in scenario.subcharacteristic_ids]
    observation = scenario.latency_observation
    measurement_status = "NOT_MEASURED"
    if observation:
        require_span(observation.source_ref, texts)
        measure = scenario.parts.get("response_measure")
        environment = scenario.parts.get("environment")
        if (
            not scenario.review or scenario.latency_ceiling_ms is None or not measure or not environment
            or observation.source_ref.source_id not in observation_sources
            or observation.source_ref.source_id == atom["source_ref"]["source_id"]
            or not observation.metric.strip() or observation.metric not in measure.quote
            or observation.metric not in observation.source_ref.quote or environment.quote not in observation.source_ref.quote
            or observation.run_id not in observation.source_ref.quote
            or not _ms_in_span(observation.milliseconds, observation.source_ref)
        ):
            raise ValueError(f"{scenario.id} observation requires a reviewed, separately cited run matching the target metric and environment.")
        measurement_status = "MEASURED_PASS" if observation.milliseconds <= scenario.latency_ceiling_ms else "MEASURED_FAIL"
    return {
        "id": scenario.id, "nfr_id": scenario.nfr_id, "nfr_source_ref": atom["source_ref"],
        "nfr_status": atom["review_status"], "fr_ids": scenario.fr_ids,
        "responsibility_ids": scenario.responsibility_ids, "interaction_ids": sorted(related_edges),
        "scope_status": "HUMAN_APPROVED" if scenario.review else "SOURCE_CONFIRMED" if accepted and scope_is_cited else "PROPOSED",
        "parts": {
            name: ({"value": scenario.parts[name].quote, "status": "SOURCE_CONFIRMED",
                    "source_ref": scenario.parts[name].model_dump(mode="json")}
                   if name in scenario.parts else {"value": None, "status": "UNKNOWN", "source_ref": None})
            for name in SCENARIO_PARTS
        },
        "iso_mappings": mappings, "architecture_driver_ids": scenario.architecture_driver_ids,
        "priority": scenario.priority.model_dump(mode="json") if scenario.priority else None,
        "assumptions": scenario.assumptions, "review": scenario.review.model_dump(mode="json") if scenario.review else None,
        "review_status": "HUMAN_APPROVED" if scenario.review else "PROPOSED",
        "target_status": "TARGET_SPECIFIED" if scenario.target else "MEASURE_MISSING",
        "end_to_end_target": scenario.target.model_dump(mode="json") if scenario.target else None,
        "measurement_method": scenario.measurement_method,
        "measurement_method_status": "HUMAN_APPROVED" if scenario.review and scenario.measurement_method else "PROPOSED" if scenario.measurement_method else "UNKNOWN",
        "measurement_feasibility": "PROPOSED" if scenario.measurement_method and scenario.target and "response_measure" in scenario.parts else "INSUFFICIENT_EVIDENCE",
        "measurement_status": measurement_status,
        "measurement": observation.model_dump(mode="json") if observation else None,
        "measurement_scope": "SYSTEM_SCENARIO_ONLY",
        "latency_budget": {
            "status": "PROPOSED" if scenario.latency_allocations else "UNALLOCATED",
            "ceiling_ms": scenario.latency_ceiling_ms, "declared_allocation_ms": total_ms if budgeted else None,
            "entries": [item.model_dump(mode="json") for item in scenario.latency_allocations],
            "composition": "Serial planning ledger only; no predicted or measured end-to-end latency.",
        },
    }


def _validate_hard_constraints(constraints: list[Constraint], reviews: list[HardConstraintReview], atoms: dict,
                               evidence: dict[str, EvidenceRecord], blocked: set[str], texts: dict[str, str]) -> None:
    by_id = {item.constraint_id: item for item in reviews}
    if len(by_id) != len(reviews):
        raise ValueError("Hard constraint reviews must have unique constraint IDs.")
    for constraint in constraints:
        if not constraint.enabled or constraint.hardness != "HARD":
            continue
        review = by_id.pop(constraint.id, None)
        atom = atoms.get(review.requirement_atomic_id) if review else None
        allowed_predicates = {"VERIFIED_ATOMIC_INVARIANT", "INDIVISIBLE_TRANSACTION"} if constraint.relation == "MUST_LINK" else {"MANDATORY_SEPARATION"}
        accepted_evidence = [
            evidence[key] for key in constraint.evidence_ids
            if key in evidence and key not in blocked and evidence[key].status == "PRESENT"
            and evidence[key].review_status == "APPROVED" and not evidence[key].is_assumption
            and evidence[key].provenance in {"SOURCE_BACKED", "HUMAN_OVERRIDE"}
            and {evidence[key].subject_id, evidence[key].object_id} == {constraint.left, constraint.right}
            and evidence[key].predicate.upper() in allowed_predicates and evidence[key].source_refs
        ]
        if (
            not review or not review.alternative_considered.strip() or not atom
            or atom["review_status"] not in ACCEPTED or atom["requirement_type"] not in {"FR", "ARCHITECTURAL_CONSTRAINT"}
            or constraint.origin not in {"SOURCE_BACKED", "HUMAN_OVERRIDE"} or not accepted_evidence
        ):
            raise ValueError(f"Unsupported hard constraint {constraint.id}: requires a reviewed FR/constraint and accepted binding evidence.")
        _require_atomic_span(review.justification, atom, texts)
        require_span(SourceRef.model_validate(atom["source_ref"]), texts)
        if not any(review.justification in item.source_refs for item in accepted_evidence):
            raise ValueError(f"Hard constraint {constraint.id} review must cite its accepted binding evidence.")
        for item in accepted_evidence:
            for ref in item.source_refs:
                require_span(ref, texts)
    if by_id:
        raise ValueError(f"Hard reviews refer to inactive or missing constraints: {sorted(by_id)}.")


def prepare_quality_decomposition(
    config: QualityDecompositionInput, raw: RawRequirements, responsibilities: list[Responsibility],
    evidence: list[EvidenceRecord], blocked: set[str], constraints: list[Constraint], texts: dict[str, str],
    *, prepared_fixture: bool = False,
) -> PreparedQualityDecomposition:
    provenance = "PREPARED_FIXTURE" if prepared_fixture else "SOURCE_REQUIREMENT"
    documents = [RequirementDocument(id=item.source_ref.source_id, text=item.text, declared_type="FR", provenance=provenance)
                 for item in raw.requirements] + config.source_documents
    classification = classify_documents(documents, config.classification_reviews)
    atoms = {item["atomic_id"]: item for document in classification["documents"] for item in document["atoms"]}
    role_map = {item.id: item for item in responsibilities}
    evidence_map = {item.id: item for item in evidence}
    proposal_sources = {document.id for document in documents if document.provenance == "LLM_PROPOSAL"}
    observation_sources = {document.id for document in documents if document.provenance == "SUPPLIED_OBSERVATION"}
    interactions = {item.id: item for item in config.interactions}
    if len(interactions) != len(config.interactions) or len({item.id for item in config.scenarios}) != len(config.scenarios):
        raise ValueError("Scenario and interaction IDs must be unique.")
    for item in interactions.values():
        validate_interaction(item, texts, set(role_map))
        basis = [*item.source_refs, *item.basis_refs.values(), item.deadline, item.distributed_proof]
        if item.review and any(ref and ref.source_id in proposal_sources for ref in basis):
            raise ValueError(f"{item.id} must cite original sources before approving a mode.")
        if not set(item.evidence_ids) <= evidence_map.keys() or blocked.intersection(item.evidence_ids):
            raise ValueError(f"{item.id} references unknown or structurally ambiguous evidence.")
        if item.review and any(evidence_map[key].status != "PRESENT" or evidence_map[key].review_status != "APPROVED"
                               for key in item.evidence_ids):
            raise ValueError(f"{item.id} refers to unaccepted supporting evidence for an approved mode.")
    taxonomy = iso_subcharacteristics()
    scenario_inputs = list(config.scenarios)
    covered_nfrs = {item.nfr_id for item in scenario_inputs}
    scenario_ids = {item.id for item in scenario_inputs}
    for atom_id, atom in atoms.items():
        if atom["requirement_type"] != "NFR" or atom["review_status"] not in ACCEPTED or atom_id in covered_nfrs:
            continue
        generated_id = f"QS-FROM-{atom_id}"
        if generated_id in scenario_ids:
            raise ValueError(f"{generated_id} conflicts with the scenario placeholder for {atom_id}.")
        source = atom["source_ref"]["quote"].casefold()
        explicit_codes = [key for key in taxonomy if key.casefold() in source]
        scenario_inputs.append(QualityScenarioInput(id=generated_id, nfr_id=atom_id, subcharacteristic_ids=explicit_codes))
    scenarios = [_scenario_row(item, atoms, role_map, {fr.id for fr in raw.requirements}, texts, taxonomy, interactions, observation_sources)
                 for item in scenario_inputs]
    _validate_hard_constraints(constraints, config.hard_constraint_reviews, atoms, evidence_map, blocked, texts)
    generated = []
    origins = []
    for scenario in config.scenarios:
        if scenario.preferences and not scenario.review:
            raise ValueError(f"{scenario.id} requires explicit review before it contributes preferences.")
        for index, rule in enumerate(scenario.preferences, 1):
            if rule.left == rule.right or not {rule.left, rule.right} <= set(scenario.responsibility_ids):
                raise ValueError(f"{scenario.id} preference endpoints must belong to its responsibility scope.")
            constraint_id = f"QUALITY-{scenario.id}-{index}"
            generated.append(Constraint(
                id=constraint_id, relation=rule.relation, left=rule.left, right=rule.right,
                weight=rule.weight, hardness="SOFT", origin="HUMAN_OVERRIDE", rationale=scenario.review.rationale,
                source_refs=[SourceRef.model_validate(atoms[scenario.nfr_id]["source_ref"])],
            ))
            origins.append({"constraint_id": constraint_id, "scenario_id": scenario.id, "reviewer": scenario.review.reviewer_id})
    for item in interactions.values():
        if item.review and item.review.optimizer_weight is not None:
            mode, _ = propose_mode(item)
            constraint_id = f"INTERACTION-{item.id}"
            generated.append(Constraint(
                id=constraint_id, relation="CANNOT_LINK" if mode.startswith("ASYNC") else "MUST_LINK",
                left=item.caller, right=item.callee, weight=item.review.optimizer_weight,
                hardness="SOFT", origin="HUMAN_OVERRIDE", rationale=item.review.rationale,
                evidence_ids=item.evidence_ids, source_refs=item.source_refs,
            ))
            origins.append({"constraint_id": constraint_id, "interaction_id": item.id, "reviewer": item.review.reviewer_id})
    if len({item.id for item in [*constraints, *generated]}) != len(constraints) + len(generated):
        raise ValueError("Quality-aware constraint IDs must be unique.")
    coupling = {
        dimension: [item.model_dump(mode="json") for item in evidence if item.predicate.upper() in predicates]
        for dimension, predicates in COUPLING_PREDICATES.items()
    }
    report = {
        "policy": {"id": POLICY_ID, "version": POLICY_VERSION, "interaction_decision_version": "1.0.0"},
        "iso_registry": iso_registry(), "source_documents": [item.model_dump(mode="json") for item in config.source_documents],
        "classification": classification, "quality_scenario_matrix": scenarios,
        "fr_responsibility_trace": [
            {"responsibility_id": item.id, "fr_ids": item.requirement_ids,
             "activity": item.activity, "workflow_activity_ids": item.workflow_activity_ids, "operation": item.operation,
             "workflow_mapping_status": item.workflow_mapping_status, "review_status": item.review_decision_status,
             "source_refs": [ref.model_dump(mode="json") for ref in item.source_refs]}
            for item in responsibilities
        ],
        "coupling": {"dimensions": coupling, "unrecorded_scope": "UNKNOWN", "blocked_evidence_ids": sorted(blocked)},
        "constraint_origins": origins, "hard_constraint_reviews": [x.model_dump(mode="json") for x in config.hard_constraint_reviews],
        "measurement_status": "PARTIALLY_MEASURED" if any(row["measurement"] for row in scenarios) else "NOT_MEASURED",
        "validation_scope": "STRUCTURE_AND_POLICY_ONLY",
    }
    return PreparedQualityDecomposition([*constraints, *generated], report, config.interactions, evidence, role_map, blocked)


def _assignment(groups: list[list[str]]) -> dict[str, str]:
    return {role: f"Q{index}" for index, group in enumerate(groups, 1) for role in group}


def _dominates(left: tuple, right: tuple) -> bool:
    return left != right and all(a <= b for a, b in zip(left, right, strict=True))


def build_quality_candidate_report(prepared: PreparedQualityDecomposition, optimization: dict) -> dict:
    scenarios = prepared.report["quality_scenario_matrix"]
    accepted_scopes = [item for item in scenarios if item["scope_status"] in ACCEPTED]
    workflow_pairs = [
        (item.subject_id, item.object_id) for item in prepared.evidence
        if item.predicate.upper() in COUPLING_PREDICATES["workflow_dependency"] and item.status == "PRESENT"
        and item.review_status == "APPROVED" and item.id not in prepared.blocked_evidence_ids
        and {item.subject_id, item.object_id} <= prepared.roles.keys()
    ]
    unknown_pairs = {
        tuple(sorted((item.subject_id, item.object_id))) for item in prepared.evidence
        if item.status == "UNKNOWN" and {item.subject_id, item.object_id} <= prepared.roles.keys()
    }
    known_interactions = [(item, propose_mode(item)[0]) for item in prepared.interactions]
    pools = []
    for item in optimization["feasible_candidates"] or optimization["optimal_candidates"]:
        assignment = _assignment(item["groups"])
        crossing = [(edge, mode) for edge, mode in known_interactions if assignment[edge.caller] != assignment[edge.callee]]
        vector = (
            Decimal(str(item["objective_cost"])),
            sum(len({assignment[role] for role in scenario["responsibility_ids"]}) > 1 for scenario in accepted_scopes),
            sum(assignment[left] != assignment[right] for left, right in workflow_pairs),
            sum(bool(edge.review) and mode == "SYNC_REQUEST_RESPONSE" for edge, mode in crossing),
            len({tuple(sorted((edge.caller, edge.callee))) for edge, mode in crossing
                 if mode in {"UNRESOLVED", "LOCAL"} or not edge.review}
                | {(left, right) for left, right in unknown_pairs if assignment[left] != assignment[right]}),
        )
        pools.append((vector, item, assignment))
    frontier_vectors = []
    for vector in sorted({vector for vector, _, _ in pools}):
        if not any(_dominates(other, vector) for other in frontier_vectors):
            frontier_vectors.append(vector)
    ordered = sorted(pools, key=lambda row: (row[0] not in frontier_vectors, row[0], row[1]["candidate_id"]))
    candidates = []
    for vector, candidate, assignment in ordered[:3]:
        profiles = []
        assessments = [interaction_profile(item, assignment) for item in prepared.interactions]
        for index, group in enumerate(candidate["groups"], 1):
            quantum_id = f"Q{index}"
            scoped = [row for row in scenarios if set(group).intersection(row["responsibility_ids"])]
            related = [row for row in assessments if quantum_id in {row["from_quantum"], row["to_quantum"]}]
            profiles.append({
                "quantum_id": quantum_id, "responsibility_ids": group,
                "fr_ids": sorted({fr for role in group for fr in prepared.roles[role].requirement_ids}),
                "quality_scenarios": [{
                    "scenario_id": scenario["id"], "nfr_id": scenario["nfr_id"],
                    "scope": "END_TO_END" if len({assignment[role] for role in scenario["responsibility_ids"]}) > 1 else "WITHIN_CANDIDATE",
                    "source_ref": scenario["nfr_source_ref"], "iso_mappings": scenario["iso_mappings"],
                    "architecture_driver_ids": scenario["architecture_driver_ids"],
                    "target_status": scenario["target_status"], "measurement_method": scenario["measurement_method"],
                    "measurement_status": "NOT_MEASURED",
                    "allocated_budget": [entry for entry in scenario["latency_budget"]["entries"]
                                         if entry["kind"] == "RESPONSIBILITY" and entry["subject_id"] in group],
                } for scenario in scoped],
                "boundary_evidence_ids": sorted(item.id for item in prepared.evidence
                                                if item.subject_id in group or item.object_id in group),
                "interaction_ids": [item["id"] for item in related],
                "allocation_rationale": [
                    {"responsibility_id": role, "fr_ids": prepared.roles[role].requirement_ids,
                     "workflow_activity_ids": prepared.roles[role].workflow_activity_ids,
                     "scenario_ids": [row["id"] for row in scoped if role in row["responsibility_ids"]],
                     "colocated_quality_scopes": [
                         {"scenario_id": row["id"], "other_responsibilities": sorted((set(group) - {role}) & set(row["responsibility_ids"]))}
                         for row in scoped if row["scope_status"] in ACCEPTED and role in row["responsibility_ids"]
                         and (set(group) - {role}) & set(row["responsibility_ids"])
                     ],
                     "applied_constraint_ids": [rule.id for rule in prepared.constraints
                                                if rule.enabled and role in {rule.left, rule.right}],
                     "counterfactual": "Re-evaluate if its source trace, scope, or interaction contract changes."}
                    for role in group
                ],
                "deployability": "INSUFFICIENT_EVIDENCE", "measurement_status": "NOT_MEASURED",
                "unresolved_risks": [row["id"] for row in related if row["status"] != "HUMAN_APPROVED"],
                "status": "PROPOSED", "confidence": "REVIEW_REQUIRED",
            })
        for interaction in assessments:
            scoped = [scenario for scenario in scenarios if interaction["id"] in scenario["interaction_ids"]]
            interaction["scenario_ids"] = [scenario["id"] for scenario in scoped]
            interaction["quality_profiles"] = [{
                "scenario_id": row["id"], "nfr_id": row["nfr_id"], "source_ref": row["nfr_source_ref"],
                "iso_mappings": row["iso_mappings"], "architecture_driver_ids": row["architecture_driver_ids"],
                "measurement_method": row["measurement_method"],
            } for row in scoped]
            interaction["communication_budget"] = [
                entry for scenario in scoped for entry in scenario["latency_budget"]["entries"]
                if entry["kind"] == "COMMUNICATION" and entry["subject_id"] == interaction["id"]
            ]
            interaction["communication_budget_status"] = "PROPOSED" if interaction["communication_budget"] else "UNALLOCATED"
        dominator = next((item["candidate_id"] for other, item, _ in ordered if _dominates(other, vector)), None)
        constraint_effects = [
            {"id": rule.id, "relation": rule.relation, "weight": rule.weight, "endpoints": [rule.left, rule.right],
             "violated": (assignment[rule.left] == assignment[rule.right]) != (rule.relation == "MUST_LINK"),
             "hardness": rule.hardness, "rationale": rule.rationale, "evidence_ids": rule.evidence_ids}
            for rule in prepared.constraints if rule.enabled
        ]
        coupling_exposure = {}
        for dimension, rows in prepared.report["coupling"]["dimensions"].items():
            known_pairs = [row for row in rows if {row["subject_id"], row["object_id"]} <= assignment.keys()]
            crossing_rows = [row for row in known_pairs if assignment[row["subject_id"]] != assignment[row["object_id"]]]
            coupling_exposure[dimension] = {
                "crossing_evidence_ids": {
                    state: sorted(row["id"] for row in crossing_rows if row["status"] == state)
                    for state in ("PRESENT", "SCOPED_ABSENT", "UNKNOWN")
                },
                "other_pair_scope": "UNKNOWN",
            }
        candidates.append({
            **candidate, "cost_vector": [float(vector[0]), *vector[1:]], "pareto": dominator is None,
            "dominated_by": dominator, "quality_profiles": profiles, "interaction_matrix": assessments,
            "constraint_effects": constraint_effects,
            "coupling_exposure": coupling_exposure,
            "comparison_to_first": {
                "candidate_id": ordered[0][1]["candidate_id"],
                "axis_deltas": {name: float(value - baseline) for name, value, baseline in
                                zip(COST_AXES, vector, ordered[0][0], strict=True)},
            },
            "operational_indicators": {
                "quantum_count": len(candidate["groups"]),
                "cross_quantum_connections": sum(row["from_quantum"] != row["to_quantum"] for row in assessments),
                "async_delivery_controls": [row["id"] for row in assessments if row["mode"].startswith("ASYNC")],
                "failure_isolation": "INSUFFICIENT_EVIDENCE", "scalability": "INSUFFICIENT_EVIDENCE",
            },
            "quality_feasibility": "INSUFFICIENT_EVIDENCE", "status": "PROPOSED",
        })
    return {
        **prepared.report,
        "candidate_pool": "REPORTED_CO_OPTIMA" if optimization.get("solver_backend") == "CP_SAT" else "ALL_FEASIBLE_PARTITIONS",
        "candidate_pool_size": len(pools), "candidate_count": len(candidates), "candidates": candidates,
        "optimization_status": optimization["result_status"], "core_conflicts": optimization["conflicts"],
        "cost_axes": list(COST_AXES),
        "cost_order": "Pareto over dimension-specific counts, then lexicographic vector and candidate ID.",
        "note": "The optimizer solves configured penalties. This shortlist assesses only the available solver pool.",
    }
