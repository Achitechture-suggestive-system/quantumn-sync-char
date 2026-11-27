"""Source-only package and lock-validator tests; all annotation rows are test fixtures."""

import json
from pathlib import Path

import pytest

from eqcr.p2_protocol import (
    build_blind_annotation_template,
    lock_blind_annotation,
    verify_blind_annotation_lock,
)
from eqcr.p2_reviewer_package import (
    PACKAGE_FILES,
    SourceOnlyPackageError,
    build_source_only_reviewer_package,
    validate_source_only_reviewer_package,
)
from eqcr.tutor_support import get_tutor_support_fixture
from scripts.validate_p2_annotation_lock import main as validate_lock_main


def _test_lock(raw, package_root):
    submission = build_blind_annotation_template(raw, package_root)
    submission.update(
        {
            "reviewer_id": "test-only-reviewer",
            "source_only_attested": True,
            "no_prior_model_output_exposure": True,
            "unresolved_requirement_ids": [item["id"] for item in raw["requirements"]],
        }
    )
    return lock_blind_annotation(
        raw,
        submission,
        locked_at="2026-01-01T00:00:00+00:00",
        source_package_root=package_root,
    )


def test_committed_reviewer_package_contains_only_source_and_blank_annotation_material():
    raw = get_tutor_support_fixture()["raw_requirements"]
    package_root = Path(__file__).resolve().parents[1] / "docs" / "p2" / "source_only_reviewer"
    info = validate_source_only_reviewer_package(raw, package_root)
    present = {path.name for path in package_root.iterdir() if path.is_file()}
    assert present == PACKAGE_FILES
    assert info["source_count"] == 12

    source_data = json.loads((package_root / "SOURCE_DATA.json").read_text(encoding="utf-8"))
    assert len(source_data["requirements"]) == 6
    assert len(source_data["workflows"]) == 4
    assert len(source_data["quality_scenarios"]) == 2
    combined = "\n".join(path.read_text(encoding="utf-8") for path in package_root.iterdir() if path.suffix in {".json", ".md"})
    for forbidden_field in (
        "related_requirement_ids",
        "quality_characteristic",
        "constraint_policy_catalog",
        "responsibility_provenance",
        "P01",
        "E01",
        "B01",
        "selected_groups",
        "objective_minimum",
    ):
        assert forbidden_field not in combined


def test_source_package_builder_is_reproducible_and_validator_detects_file_tampering(tmp_path):
    raw = get_tutor_support_fixture()["raw_requirements"]
    package_root = tmp_path / "reviewer-package"
    first = build_source_only_reviewer_package(raw, package_root)
    second = build_source_only_reviewer_package(raw, package_root)
    assert first["manifest_sha256"] == second["manifest_sha256"]
    (package_root / "SOURCE_MATERIAL.md").write_text("changed source", encoding="utf-8")
    with pytest.raises(SourceOnlyPackageError, match="differs|hash mismatch"):
        validate_source_only_reviewer_package(raw, package_root)


def test_source_package_validator_rejects_missing_and_extra_files(tmp_path):
    raw = get_tutor_support_fixture()["raw_requirements"]
    package_root = tmp_path / "reviewer-package"
    build_source_only_reviewer_package(raw, package_root)
    (package_root / "SOURCE_DATA.json").unlink()
    with pytest.raises(SourceOnlyPackageError, match="file set"):
        validate_source_only_reviewer_package(raw, package_root)

    replacement = tmp_path / "second-package"
    build_source_only_reviewer_package(raw, replacement)
    (replacement / "model_notes.txt").write_text("must not be included", encoding="utf-8")
    with pytest.raises(SourceOnlyPackageError, match="file set"):
        validate_source_only_reviewer_package(raw, replacement)


def test_lock_requires_explicit_unresolved_fr_entries_and_binds_source_manifest(tmp_path):
    raw = get_tutor_support_fixture()["raw_requirements"]
    package_root = tmp_path / "reviewer-package"
    build_source_only_reviewer_package(raw, package_root)
    submission = build_blind_annotation_template(raw, package_root)
    assert submission["responsibility_annotations"] == []
    assert submission["unresolved_requirement_ids"] == []
    submission.update(
        {
            "reviewer_id": "test-only-reviewer",
            "source_only_attested": True,
            "no_prior_model_output_exposure": True,
        }
    )
    with pytest.raises(ValueError, match="List each FR"):
        lock_blind_annotation(raw, submission, source_package_root=package_root)

    submission["unresolved_requirement_ids"] = [item["id"] for item in raw["requirements"]]
    locked = lock_blind_annotation(
        raw,
        submission,
        locked_at="2026-01-01T00:00:00+00:00",
        source_package_root=package_root,
    )
    assert locked["lock"]["protocol_version"] == "P2-BLIND-ANNOTATION-v3"
    assert locked["lock"]["source_package_manifest_sha256"] == validate_source_only_reviewer_package(raw, package_root)["manifest_sha256"]
    assert verify_blind_annotation_lock(raw, locked, source_package_root=package_root)


def test_lock_rejects_future_timestamp(tmp_path):
    raw = get_tutor_support_fixture()["raw_requirements"]
    package_root = tmp_path / "reviewer-package"
    build_source_only_reviewer_package(raw, package_root)
    submission = build_blind_annotation_template(raw, package_root)
    submission.update(
        {
            "reviewer_id": "test-only-reviewer",
            "source_only_attested": True,
            "no_prior_model_output_exposure": True,
            "unresolved_requirement_ids": [item["id"] for item in raw["requirements"]],
        }
    )
    with pytest.raises(ValueError, match="cannot be in the future"):
        lock_blind_annotation(
            raw,
            submission,
            locked_at="2999-01-01T00:00:00+00:00",
            source_package_root=package_root,
        )


def test_lock_validator_checks_package_and_inference_order(tmp_path, capsys):
    raw = get_tutor_support_fixture()["raw_requirements"]
    package_root = tmp_path / "reviewer-package"
    build_source_only_reviewer_package(raw, package_root)
    locked = _test_lock(raw, package_root)
    lock_path = tmp_path / "locked-annotation.json"
    lock_path.write_text(json.dumps(locked, ensure_ascii=False), encoding="utf-8")

    result = validate_lock_main(
        [
            "--annotation-lock",
            str(lock_path),
            "--source-package",
            str(package_root),
            "--inference-started-at",
            "2026-01-01T00:00:01+00:00",
        ]
    )
    output = json.loads(capsys.readouterr().out)
    assert result == 0
    assert output["status"] == "ANNOTATION_LOCK_VALID"
    assert output["inference_order_status"] == "LOCK_PRECEDES_INFERENCE"
    assert "not independently authenticated" in output["identity_and_exposure_limitation"]

    result = validate_lock_main(
        [
            "--annotation-lock",
            str(lock_path),
            "--source-package",
            str(package_root),
            "--inference-started-at",
            "2025-12-31T23:59:59+00:00",
        ]
    )
    output = json.loads(capsys.readouterr().out)
    assert result == 2
    assert output["status"] == "ANNOTATION_LOCK_INVALID"
    assert "created after" in output["reason"]


def test_lock_verification_fails_if_pinned_reviewer_package_changes(tmp_path):
    raw = get_tutor_support_fixture()["raw_requirements"]
    package_root = tmp_path / "reviewer-package"
    build_source_only_reviewer_package(raw, package_root)
    locked = _test_lock(raw, package_root)
    (package_root / "README.md").write_text("changed instructions", encoding="utf-8")
    assert not verify_blind_annotation_lock(raw, locked, source_package_root=package_root)
