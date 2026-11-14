"""Negative structural checks and a labeled non-PetClinic synthetic input."""

import json
from copy import deepcopy
from pathlib import Path

import pytest

from eqcr.fixture import get_fixture
from eqcr.models import RawRequirements
from eqcr.pipeline import validate_project_package
from eqcr.project_io import load_project_json


SYNTHETIC_CASE = Path(__file__).parent / "fixtures" / "synthetic_tool_checkout_case.json"


def _load_synthetic_case():
    return json.loads(SYNTHETIC_CASE.read_text(encoding="utf-8"))


def test_synthetic_non_petclinic_case_has_valid_source_spans_and_explicit_label():
    fixture = _load_synthetic_case()
    assert fixture["fixture_label"] == "SYNTHETIC_TEST_FIXTURE"
    assert "not independent real-world validation" in fixture["fixture_note"]
    raw = RawRequirements.model_validate(fixture["raw_requirements"])
    assert len(raw.requirements) == 6
    assert raw.workflows[0].id == "WF-01"
    assert all(
        item.text[item.source_ref.start:item.source_ref.end] == item.source_ref.quote
        for item in raw.requirements
    )
    assert "PetClinic" not in raw.context_description


def test_missing_responsibility_citation_is_rejected():
    fixture = get_fixture()
    fixture["responsibilities"][0]["source_refs"] = []
    with pytest.raises(ValueError, match="all_responsibilities_have_fr_and_source_refs"):
        validate_project_package(fixture)


def test_mismatched_source_quote_is_rejected():
    fixture = get_fixture()
    fixture["responsibilities"][0]["source_refs"][0]["quote"] = "A quote absent from the requirement."
    with pytest.raises(ValueError, match="responsibility_sources_well_formed"):
        validate_project_package(fixture)


def test_unsupported_present_evidence_is_rejected():
    fixture = get_fixture()
    evidence = next(item for item in fixture["evidence"] if item["status"] == "PRESENT")
    evidence["source_refs"] = []
    evidence["is_assumption"] = False
    with pytest.raises(ValueError, match="present_evidence_has_source_or_assumption"):
        validate_project_package(fixture)


def test_evidence_citation_to_unknown_source_is_rejected():
    fixture = get_fixture()
    evidence = next(item for item in fixture["evidence"] if item["status"] == "PRESENT")
    evidence["source_refs"] = [dict(evidence["source_refs"][0])]
    evidence["source_refs"][0]["source_id"] = "SOURCE-NOT-IN-PACKAGE"
    with pytest.raises(ValueError, match="evidence_sources_well_formed"):
        validate_project_package(fixture)


@pytest.mark.parametrize(
    ("payload", "message"),
    [
        (b'{"raw_requirements": ', "Invalid project JSON"),
        (b"\xff\xfe", "must be UTF-8"),
        (b"[]", "must contain a project object"),
    ],
)
def test_invalid_project_json_is_rejected(payload, message):
    with pytest.raises(ValueError, match=message):
        load_project_json(payload)


def test_valid_project_json_decodes_object():
    fixture = get_fixture()
    decoded = load_project_json(json.dumps(fixture).encode("utf-8"))
    assert decoded["raw_requirements"]["case_id"] == fixture["raw_requirements"]["case_id"]


def test_unknown_constraint_responsibility_is_rejected():
    fixture = deepcopy(get_fixture())
    fixture["constraints"][0]["left"] = "R99"
    with pytest.raises(ValueError, match="unknown responsibility IDs"):
        validate_project_package(fixture)
