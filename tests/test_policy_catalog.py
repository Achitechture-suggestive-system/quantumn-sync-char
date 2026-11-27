"""Schema-level guards for the experimental evidence-to-constraint catalog."""

from copy import deepcopy

import pytest
from pydantic import ValidationError

from eqcr.fixture import get_fixture
from eqcr.models import EvidenceConstraintPolicyCatalog
from eqcr.pipeline import run_pipeline
from eqcr.tutor_support import get_tutor_support_fixture


def _catalog():
    return get_tutor_support_fixture()["constraint_policy_catalog"]


def test_tutor_policy_catalog_is_versioned_and_explicitly_unvalidated():
    catalog = EvidenceConstraintPolicyCatalog.model_validate(_catalog())
    assert catalog.catalog_id == "EQCR-P2-TUTOR-EXPERIMENTAL-POLICIES"
    assert catalog.version == "1.0.0"
    assert catalog.status == "EXPERIMENTAL_CASE_POLICY_CATALOG"
    assert catalog.review_status == "NOT_INDEPENDENTLY_VALIDATED"
    assert all(item.hardness == "SOFT" for item in catalog.entries)
    assert all(item.abstention_conditions for item in catalog.entries)


def test_catalog_rejects_hard_rules_and_semantically_mismatched_links():
    hard_policy = deepcopy(_catalog())
    hard_policy["entries"][0]["hardness"] = "HARD"
    with pytest.raises(ValidationError):
        EvidenceConstraintPolicyCatalog.model_validate(hard_policy)

    mismatched = deepcopy(_catalog())
    mismatched["entries"][0]["required_architecture_implication"] = "SEPARATE_CANDIDATE"
    with pytest.raises(ValidationError, match="MUST_LINK policies require"):
        EvidenceConstraintPolicyCatalog.model_validate(mismatched)


def test_catalog_rejects_duplicate_ids_and_missing_abstention_conditions():
    duplicate = deepcopy(_catalog())
    duplicate["entries"][1]["id"] = duplicate["entries"][0]["id"]
    with pytest.raises(ValidationError, match="entry IDs must be unique"):
        EvidenceConstraintPolicyCatalog.model_validate(duplicate)

    no_abstention = deepcopy(_catalog())
    no_abstention["entries"][0]["abstention_conditions"] = []
    with pytest.raises(ValidationError):
        EvidenceConstraintPolicyCatalog.model_validate(no_abstention)


def test_policy_evaluation_artifact_is_case_scoped_and_keeps_p0_constraint_shape():
    artifacts = run_pipeline(get_fixture())
    assert "policy_evaluation" not in artifacts["constraints"]
