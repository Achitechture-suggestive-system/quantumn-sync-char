"""Small, strict schemas for the persisted MVP artifacts."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True)


EvidenceStatus = Literal["PRESENT", "SCOPED_ABSENT", "UNKNOWN"]
ValidationStatus = Literal[
    "PASS", "FAIL", "REVIEW_REQUIRED", "INSUFFICIENT_EVIDENCE", "NOT_MEASURED", "INFEASIBLE"
]


class SourceRef(StrictModel):
    source_id: str = Field(min_length=1)
    quote: str = Field(min_length=1)
    start: int = Field(ge=0)
    end: int = Field(gt=0)


class Requirement(StrictModel):
    id: str = Field(pattern=r"^FR-\d{2}$")
    text: str = Field(min_length=1)
    source_ref: SourceRef


class Workflow(StrictModel):
    id: str = Field(min_length=1)
    text: str = Field(min_length=1)
    source_ref: SourceRef


class Scenario(StrictModel):
    id: str = Field(min_length=1)
    name: str
    stimulus: str
    response_measure: str
    stimulus_source: str | None = None
    environment: str | None = None
    stimulated_artifact: str | None = None
    response: str | None = None
    target: str | None = None
    interaction_id: str | None = None
    related_requirement_ids: list[str] = Field(default_factory=list)
    interaction_source_requirement_ids: list[str] = Field(default_factory=list)
    quality_characteristic: str | None = None
    proposed_metric: str | None = None
    measurement_method: str | None = None
    status: ValidationStatus = "REVIEW_REQUIRED"
    source_ref: SourceRef


class InteractionContract(StrictModel):
    contract_id: str = Field(min_length=1)
    schema_id: Literal["EQCR-INTERACTION-CONTRACT"] = "EQCR-INTERACTION-CONTRACT"
    schema_version: Literal["1.0.0"] = "1.0.0"
    decision_table_id: Literal["EQCR-SYNC-ASYNC-DECISION"] = "EQCR-SYNC-ASYNC-DECISION"
    decision_table_version: Literal["1.0.0"] = "1.0.0"
    selected_mode: Literal["SYNC", "ASYNC", "UNDECIDED"] = "UNDECIDED"
    selection_status: Literal["UNDECIDED", "APPROVED"] = "UNDECIDED"
    decision_basis_status: Literal["INSUFFICIENT_EVIDENCE", "HUMAN_DECISION"] = "INSUFFICIENT_EVIDENCE"
    provenance: Literal["DETERMINISTIC_TRANSFORMATION", "HUMAN_DECISION"] = "DETERMINISTIC_TRANSFORMATION"
    reviewer_id: str | None = None
    reviewed_at: datetime | None = None
    source_refs: list[SourceRef] = Field(default_factory=list)
    decision_rationale: str = "No human-approved interaction-mode evidence is available."
    request_must_wait_for_completion: bool | None = None
    request_may_return_before_completion: bool | None = None
    operation: str = "UNKNOWN"
    data_dependency: str = "UNKNOWN"
    request_fields: str = "UNKNOWN"
    response_fields: str = "UNKNOWN"
    versioning: str = "UNKNOWN"
    consistency: str = "UNKNOWN"
    latency_budget: str = "UNKNOWN"
    failure_handling: str = "UNKNOWN"
    retry_policy: str = "UNKNOWN"
    timeout_policy: str = "UNKNOWN"
    idempotency_policy: str = "UNKNOWN"
    unresolved_decisions: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def selected_mode_has_human_evidence(self):
        if self.selected_mode == "UNDECIDED":
            if self.selection_status != "UNDECIDED" or self.decision_basis_status != "INSUFFICIENT_EVIDENCE":
                raise ValueError("An undecided contract cannot be marked approved or human-decided.")
            return self
        mode_signal_present = (
            self.request_must_wait_for_completion is True
            if self.selected_mode == "SYNC"
            else self.request_may_return_before_completion is True
        )
        contradictory_signal = (
            self.request_may_return_before_completion is True
            if self.selected_mode == "SYNC"
            else self.request_must_wait_for_completion is True
        )
        unresolved_contract_fields = [
            self.operation,
            self.data_dependency,
            self.request_fields,
            self.response_fields,
            self.versioning,
            self.consistency,
            self.latency_budget,
            self.failure_handling,
            self.retry_policy,
            self.timeout_policy,
            self.idempotency_policy,
        ]
        if (
            self.selection_status != "APPROVED"
            or self.decision_basis_status != "HUMAN_DECISION"
            or self.provenance != "HUMAN_DECISION"
            or not (self.reviewer_id and self.reviewer_id.strip())
            or not self.reviewed_at
            or self.reviewed_at.tzinfo is None
            or not self.source_refs
            or not self.decision_rationale.strip()
            or not mode_signal_present
            or contradictory_signal
            or any(not value.strip() or value == "UNKNOWN" for value in unresolved_contract_fields)
            or self.unresolved_decisions
        ):
            raise ValueError("An approved interaction mode requires a complete, cited, non-contradictory human-reviewed contract.")
        return self


class RawRequirements(StrictModel):
    case_id: str
    context_id: str
    context_description: str
    requirements: list[Requirement]
    workflows: list[Workflow]
    scenarios: list[Scenario]

    @model_validator(mode="after")
    def identifiers_are_unique(self):
        groups = {
            "requirement": [item.id for item in self.requirements],
            "workflow": [item.id for item in self.workflows],
            "scenario": [item.id for item in self.scenarios],
            "source": [
                item.source_ref.source_id
                for item in [*self.requirements, *self.workflows, *self.scenarios]
            ],
        }
        duplicates = [name for name, values in groups.items() if len(values) != len(set(values))]
        if duplicates:
            raise ValueError(f"Duplicate identifiers found in: {', '.join(duplicates)}.")
        requirement_ids = set(groups["requirement"])
        for scenario in self.scenarios:
            unknown_related = set(scenario.related_requirement_ids) - requirement_ids
            unknown_interaction = set(scenario.interaction_source_requirement_ids) - requirement_ids
            if unknown_related or unknown_interaction:
                raise ValueError(
                    f"Scenario {scenario.id} references unknown requirements: "
                    f"{sorted(unknown_related | unknown_interaction)}."
                )
            if not set(scenario.interaction_source_requirement_ids) <= set(scenario.related_requirement_ids):
                raise ValueError(
                    f"Scenario {scenario.id} interaction citation requirements must be related requirements."
                )
        return self


class Responsibility(StrictModel):
    id: str = Field(pattern=r"^R[1-9]\d*$")
    proposal_id: str | None = None
    provenance: Literal[
        "PREPARED_FIXTURE",
        "LOCAL_OLLAMA_PROPOSAL",
        "LOCAL_OLLAMA_PROPOSAL_UNBLINDED",
        "HUMAN_CORRECTION",
        "HUMAN_ADDITION",
        "P2_TEST_ONLY",
    ] | None = None
    name: str
    activity: str
    operation: str
    decomposition_rationale: str = ""
    requirement_ids: list[str]
    source_refs: list[SourceRef]
    workflow_activity_ids: list[str] = Field(default_factory=list)
    workflow_mapping_status: Literal["MAPPED", "UNRESOLVED"] = "UNRESOLVED"
    workflow_note: str = ""
    review_decision_status: Literal["REVIEW_REQUIRED", "APPROVED", "REJECTED", "DEFERRED"] = "REVIEW_REQUIRED"
    semantic_status: ValidationStatus = "REVIEW_REQUIRED"


class EvidenceRecord(StrictModel):
    id: str
    subject_id: str
    predicate: str
    object_id: str
    status: EvidenceStatus
    provenance: Literal[
        "SOURCE_BACKED",
        "ASSUMPTION",
        "POLICY",
        "HUMAN_OVERRIDE",
        "MODEL_PROPOSED",
        "MODEL_PROPOSED_UNBLINDED_DEMO",
        "P2_TEST_ONLY",
        "SCOPE_BOUNDARY",
        "UNKNOWN",
    ] = "UNKNOWN"
    review_status: Literal["REVIEW_REQUIRED", "APPROVED", "REJECTED", "DEFERRED"] = "REVIEW_REQUIRED"
    source_refs: list[SourceRef] = Field(default_factory=list)
    is_assumption: bool = False
    rationale: str
    relation_annotation_id: str | None = None
    subject_requirement_id: str | None = None
    object_requirement_id: str | None = None
    architecture_implication: Literal[
        "NONE", "UNRESOLVED", "COLOCATE_CANDIDATE", "SEPARATE_CANDIDATE"
    ] = "UNRESOLVED"


class Constraint(StrictModel):
    id: str
    relation: Literal["MUST_LINK", "CANNOT_LINK"]
    left: str
    right: str
    hardness: Literal["HARD", "SOFT"] = "HARD"
    weight: float = Field(default=1.0, ge=0)
    quality_scenario_ids: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    origin: Literal["SOURCE_BACKED", "WHAT_IF_POLICY", "ARCHITECTURAL_POLICY", "HUMAN_OVERRIDE"]
    enabled: bool = True
    source_refs: list[SourceRef] = Field(default_factory=list)
    rationale: str


class EvidenceConstraintPolicy(StrictModel):
    id: str = Field(min_length=1)
    version: str = Field(pattern=r"^\d+\.\d+\.\d+$")
    evidence_predicate: str = Field(min_length=1)
    relation: Literal["MUST_LINK", "CANNOT_LINK"]
    hardness: Literal["SOFT"] = "SOFT"
    weight: float = Field(default=1.0, ge=0)
    quality_driver: str = Field(min_length=1)
    rationale: str = Field(min_length=1)
    source_basis_status: Literal["INTERNAL_EXPERIMENTAL_CASE_POLICY"]
    assumptions: list[str] = Field(min_length=1)
    abstention_conditions: list[str] = Field(min_length=1)
    required_architecture_implication: Literal["COLOCATE_CANDIDATE", "SEPARATE_CANDIDATE"]

    @model_validator(mode="after")
    def relation_matches_architecture_implication(self):
        if any(not value.strip() for value in [self.quality_driver, self.rationale, *self.assumptions, *self.abstention_conditions]):
            raise ValueError("Policy rationale, quality driver, assumptions, and abstention conditions must be non-empty.")
        if self.relation == "MUST_LINK" and self.required_architecture_implication != "COLOCATE_CANDIDATE":
            raise ValueError("MUST_LINK policies require a COLOCATE_CANDIDATE implication.")
        if self.relation == "CANNOT_LINK" and self.required_architecture_implication != "SEPARATE_CANDIDATE":
            raise ValueError("CANNOT_LINK policies require a SEPARATE_CANDIDATE implication.")
        return self


class EvidenceConstraintPolicyCatalog(StrictModel):
    catalog_id: str = Field(min_length=1)
    version: str = Field(pattern=r"^\d+\.\d+\.\d+$")
    status: Literal["EXPERIMENTAL_CASE_POLICY_CATALOG"]
    review_status: Literal["NOT_INDEPENDENTLY_VALIDATED"]
    entries: list[EvidenceConstraintPolicy] = Field(min_length=1)

    @model_validator(mode="after")
    def policy_ids_are_unique(self):
        ids = [item.id for item in self.entries]
        if len(ids) != len(set(ids)):
            raise ValueError("Policy catalog entry IDs must be unique.")
        return self


class RelationAnnotation(StrictModel):
    id: str = Field(min_length=1)
    subject_requirement_id: str = Field(pattern=r"^FR-\d{2}$")
    predicate: Literal[
        "BUSINESS_PRECEDES",
        "SHARES_STATE_OR_INVARIANT",
        "REQUIRES_INDEPENDENT_CHANGE",
    ]
    object_requirement_id: str = Field(pattern=r"^FR-\d{2}$")
    direction: Literal["DIRECTED", "UNDIRECTED"]
    status: EvidenceStatus
    review_status: Literal["REVIEW_REQUIRED", "APPROVED", "REJECTED", "DEFERRED"]
    provenance: Literal[
        "LOCAL_OLLAMA_UNVERIFIED",
        "LOCAL_OLLAMA_REVIEWED",
        "LOCAL_OLLAMA_UNBLINDED_DEMO",
        "HUMAN_OVERRIDE",
        "P2_TEST_ONLY",
    ]
    source_requirement_ids: list[str] = Field(default_factory=list)
    source_workflow_ids: list[str] = Field(default_factory=list)
    source_refs: list[SourceRef] = Field(default_factory=list)
    rationale: str
    architecture_implication: Literal[
        "NONE", "UNRESOLVED", "COLOCATE_CANDIDATE", "SEPARATE_CANDIDATE"
    ] = "UNRESOLVED"
    architecture_rationale: str = ""
    responsibility_pairs: list[tuple[str, str]] = Field(default_factory=list)
    proposal_id: str | None = None

    @model_validator(mode="after")
    def relation_semantics_are_separate(self):
        if self.subject_requirement_id == self.object_requirement_id:
            raise ValueError("Relation annotations cannot be reflexive.")
        if self.predicate == "BUSINESS_PRECEDES" and self.direction != "DIRECTED":
            raise ValueError("BUSINESS_PRECEDES must be directed.")
        if self.predicate != "BUSINESS_PRECEDES" and self.direction != "UNDIRECTED":
            raise ValueError("Architectural relation registry predicates must be undirected.")
        if self.direction == "UNDIRECTED" and self.subject_requirement_id >= self.object_requirement_id:
            raise ValueError("Undirected relation endpoints must use canonical lexical order.")
        if self.predicate == "BUSINESS_PRECEDES" and self.architecture_implication not in {"NONE", "UNRESOLVED"}:
            raise ValueError("Business ordering alone cannot create an architectural implication.")
        if self.predicate == "SHARES_STATE_OR_INVARIANT" and self.architecture_implication == "SEPARATE_CANDIDATE":
            raise ValueError("Shared-state evidence cannot be used to assert independent-change separation.")
        if self.predicate == "REQUIRES_INDEPENDENT_CHANGE" and self.architecture_implication == "COLOCATE_CANDIDATE":
            raise ValueError("Independent-change evidence cannot be used to assert co-location.")
        if len(self.responsibility_pairs) != len(set(self.responsibility_pairs)):
            raise ValueError("A relation annotation cannot repeat responsibility pairs.")
        if any(left == right for left, right in self.responsibility_pairs):
            raise ValueError("A relation annotation responsibility pair must contain distinct R IDs.")
        if self.architecture_implication in {"COLOCATE_CANDIDATE", "SEPARATE_CANDIDATE"}:
            if self.status != "PRESENT" or not self.architecture_rationale.strip() or not self.responsibility_pairs:
                raise ValueError("An architectural candidate requires PRESENT evidence, a separate rationale, and explicit R pairs.")
        return self


RequirementCitationId = Annotated[str, Field(pattern=r"^FR-\d{2}$")]


class LLMProposal(StrictModel):
    id: str = Field(min_length=1)
    name: str
    activity: str
    operation: str
    requirement_ids: list[RequirementCitationId] = Field(min_length=1)
    decomposition_rationale: str = Field(min_length=1)

    @model_validator(mode="after")
    def requirement_ids_are_unique(self):
        if len(self.requirement_ids) != len(set(self.requirement_ids)):
            raise ValueError("A responsibility proposal cannot repeat requirement IDs.")
        return self


class LLMNormalizedRequirement(StrictModel):
    id: str = Field(pattern=r"^FR-\d{2}$")
    normalized_text: str


class LLMEvidenceProposal(StrictModel):
    id: str = Field(min_length=1)
    subject_requirement_id: str = Field(pattern=r"^FR-\d{2}$")
    predicate: str = Field(min_length=1)
    object_requirement_id: str = Field(pattern=r"^FR-\d{2}$")
    proposed_status: EvidenceStatus
    source_requirement_ids: list[RequirementCitationId] = Field(min_length=1)
    rationale: str = Field(min_length=1)


class LLMBoundaryHypothesis(StrictModel):
    id: str = Field(min_length=1)
    requirement_ids: list[RequirementCitationId] = Field(min_length=2)
    boundary_rationale: str = Field(min_length=1)
    source_requirement_ids: list[RequirementCitationId] = Field(min_length=1)


class LLMProposalBundle(StrictModel):
    context_summary: str
    normalized_requirements: list[LLMNormalizedRequirement] = Field(min_length=6, max_length=6)
    proposals: list[LLMProposal] = Field(default_factory=list, max_length=8)
    evidence_proposals: list[LLMEvidenceProposal] = Field(min_length=1)
    boundary_hypotheses: list[LLMBoundaryHypothesis] = Field(min_length=1)
