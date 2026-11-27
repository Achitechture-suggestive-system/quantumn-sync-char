"""Curated synthetic inputs for the existing Ticket Support workbench."""

from __future__ import annotations

from functools import cache
import json
from pathlib import Path

from .quantum_example import ticket_example
from .quantum_tradeoff import Architecture, Requirement, RequirementGeneration


STUDIO_CASE_FILE = Path(__file__).with_name("studio_demo") / "llm_ticket_requirements.json"


@cache
def ticket_requirement_cases() -> dict:
    return {case["id"]: case for case in json.loads(STUDIO_CASE_FILE.read_text(encoding="utf-8"))}


def case_requirements(case: dict) -> list[Requirement]:
    requirements = []
    for proposal in case["proposals"]:
        number = proposal["proposal_number"]
        item = Requirement(id=f"LLM-{case['id']}-{number:02d}", kind=proposal["kind"],
                           text=proposal["text"], component_ids=proposal["component_ids"])
        item.generation = RequirementGeneration(
            model=case["model"], case_id=case["id"], proposal_number=number,
            response_sha256=case["response_sha256"], input_sha256=item.input_digest(),
            characteristic=proposal["characteristic"], quote=proposal["quote"],
        )
        requirements.append(item)
    return requirements


def new_case_requirements(architecture: Architecture, case: dict) -> list[Requirement]:
    original_names = {item.id: item.name for item in ticket_example().components}
    names = {item.id: item.name for item in architecture.components}
    existing = {item.id for item in architecture.requirements}
    return [item for item in case_requirements(case) if item.id not in existing
            and all(names.get(key) == original_names[key] for key in item.component_ids)]
