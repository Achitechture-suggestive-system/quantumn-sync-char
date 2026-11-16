"""Small, strict schemas for the persisted MVP artifacts."""

from __future__ import annotations

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
    target: str | None = None
    interaction_id: str | None = None
    related_requirement_ids: list[str] = Field(default_factory=list)
    interaction_source_requirement_ids: list[str] = Field(default_factory=list)
    quality_characteristic: str | None = None
    proposed_metric: str | None = None
    measurement_method: str | None = None
    status: ValidationStatus = "REVIEW_REQUIRED"
    source_ref: SourceRef


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
    id: str = Field(pattern=r"^R[1-6]$")
    proposal_id: str | None = None
    name: str
    activity: str
    operation: str
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
        "SCOPE_BOUNDARY",
        "UNKNOWN",
    ] = "UNKNOWN"
    review_status: Literal["REVIEW_REQUIRED", "APPROVED", "REJECTED", "DEFERRED"] = "REVIEW_REQUIRED"
    source_refs: list[SourceRef] = Field(default_factory=list)
    is_assumption: bool = False
    rationale: str


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
    evidence_predicate: str = Field(min_length=1)
    relation: Literal["MUST_LINK", "CANNOT_LINK"]
    hardness: Literal["HARD", "SOFT"] = "SOFT"
    weight: float = Field(default=1.0, ge=0)
    rationale: str = Field(min_length=1)


class LLMProposal(StrictModel):
    id: str = Field(min_length=1)
    name: str
    activity: str
    operation: str
    requirement_id: str = Field(pattern=r"^FR-\d{2}$")


class LLMNormalizedRequirement(StrictModel):
    id: str = Field(pattern=r"^FR-\d{2}$")
    normalized_text: str


RequirementCitationId = Annotated[str, Field(pattern=r"^FR-\d{2}$")]


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
    proposals: list[LLMProposal] = Field(min_length=6, max_length=6)
    evidence_proposals: list[LLMEvidenceProposal] = Field(min_length=1)
    boundary_hypotheses: list[LLMBoundaryHypothesis] = Field(min_length=1)
