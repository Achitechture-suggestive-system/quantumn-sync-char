"""Artifact bundles preserve run provenance and detect changed members."""

from __future__ import annotations

from io import BytesIO
import json
from pathlib import Path
import subprocess
import sys
from zipfile import ZipFile

import pytest

from eqcr.pipeline import run_pipeline
from eqcr.storage import make_export_zip, verify_export_zip
from eqcr.tutor_support import get_tutor_support_fixture


def test_artifact_bundle_records_provenance_hashes_and_solver_inputs():
    fixture = get_tutor_support_fixture()
    artifacts = run_pipeline(fixture, execution_mode="P2_TEST_ONLY")
    artifacts["metadata"]["run_id"] = "run-p2-manifest-test"
    payload = make_export_zip(artifacts, {"snapshots/v1.json": artifacts})

    result = verify_export_zip(payload)
    manifest = result["manifest"]

    assert result["status"] == "PASS"
    assert result["case_id"] == fixture["raw_requirements"]["case_id"]
    assert result["run_id"] == "run-p2-manifest-test"
    assert manifest["manifest_version"] == "EQCR-REPRODUCIBILITY-BUNDLE@1.0.0"
    assert manifest["input_hashes"]["raw_requirements_sha256"]
    assert manifest["optimizer"]["solver_backend"] == "EXHAUSTIVE_ENUMERATOR"
    assert manifest["provenance_summary"]["responsibilities"] == {"PREPARED_FIXTURE": 6}
    assert manifest["ci_status"] == "NOT_RECORDED"
    assert "snapshots/v1.json" in manifest["bundle_member_sha256"]


def test_artifact_bundle_validator_rejects_a_changed_artifact_member():
    artifacts = run_pipeline(get_tutor_support_fixture(), execution_mode="P2_TEST_ONLY")
    payload = make_export_zip(artifacts)
    changed = BytesIO()
    with ZipFile(BytesIO(payload), "r") as original, ZipFile(changed, "w") as tampered:
        for name in original.namelist():
            member = original.read(name)
            if name == "raw_requirements.json":
                member = member.replace(b"Tutor Support", b"Altered Support", 1)
            tampered.writestr(name, member)

    with pytest.raises(ValueError, match="checksum verification failed"):
        verify_export_zip(changed.getvalue())


def test_artifact_bundle_export_rejects_colliding_or_reserved_member_names():
    with pytest.raises(ValueError, match="Duplicate or reserved"):
        make_export_zip({"validation_report": {}}, {"validation_report.json": {}})
    with pytest.raises(ValueError, match="Duplicate or reserved"):
        make_export_zip({}, {"reproducibility_manifest.json": {}})


def test_artifact_bundle_checksums_include_manifest_and_every_payload():
    payload = make_export_zip({"validation_report": {"status": "REVIEW_REQUIRED"}})
    with ZipFile(BytesIO(payload), "r") as archive:
        checksums = json.loads(archive.read("checksums.sha256.json"))
        assert set(checksums) == set(archive.namelist()) - {"checksums.sha256.json"}
    assert verify_export_zip(payload)["verified_member_count"] == 3


def test_artifact_bundle_validation_script_reports_verified_bundle(tmp_path):
    repo_root = Path(__file__).resolve().parents[1]
    bundle_path = tmp_path / "run-artifacts.zip"
    bundle_path.write_bytes(make_export_zip({"validation_report": {"status": "REVIEW_REQUIRED"}}))

    result = subprocess.run(
        [sys.executable, str(repo_root / "scripts" / "validate_artifact_bundle.py"), str(bundle_path)],
        capture_output=True,
        text=True,
        cwd=repo_root,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert json.loads(result.stdout)["status"] == "PASS"
