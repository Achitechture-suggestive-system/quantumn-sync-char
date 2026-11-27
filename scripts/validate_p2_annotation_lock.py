"""Validate a supplied P2 annotation lock against the source-only package."""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from eqcr.p2_protocol import verify_blind_annotation_lock  # noqa: E402
from eqcr.p2_reviewer_package import (  # noqa: E402
    SourceOnlyPackageError,
    default_source_package_root,
    validate_source_only_reviewer_package,
)
from eqcr.tutor_support import get_tutor_support_fixture  # noqa: E402


def _time(value: str, name: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{name} must be a valid ISO-8601 timestamp.") from exc
    if parsed.tzinfo is None:
        raise ValueError(f"{name} must include a timezone.")
    return parsed


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--annotation-lock", required=True, help="Path to the reviewer-supplied locked annotation JSON.")
    parser.add_argument("--source-package", default=str(default_source_package_root()), help="Reviewer package directory to verify.")
    parser.add_argument("--inference-started-at", help="Optional actual inference start timestamp; must follow the lock timestamp.")
    args = parser.parse_args(argv)

    try:
        raw = get_tutor_support_fixture()["raw_requirements"]
        package_root = Path(args.source_package)
        package_info = validate_source_only_reviewer_package(raw, package_root)
        lock_bundle = json.loads(Path(args.annotation_lock).read_text(encoding="utf-8"))
        if not isinstance(lock_bundle, dict) or not verify_blind_annotation_lock(
            raw,
            lock_bundle,
            source_package_root=package_root,
        ):
            raise ValueError("Annotation lock failed protocol, schema, attestation, source-hash, or integrity validation.")
        lock_info = lock_bundle["lock"]
        if args.inference_started_at:
            locked_at = _time(lock_info["locked_at"], "lock timestamp")
            inference_at = _time(args.inference_started_at, "inference start timestamp")
            if inference_at < locked_at:
                raise ValueError("The annotation lock was created after the supplied inference start time.")
            inference_status = "LOCK_PRECEDES_INFERENCE"
        else:
            inference_status = "NOT_CHECKED_NO_INFERENCE_TIMESTAMP_SUPPLIED"
        print(
            json.dumps(
                {
                    "status": "ANNOTATION_LOCK_VALID",
                    "case_id": raw["case_id"],
                    "protocol_version": lock_info["protocol_version"],
                    "source_package_manifest_sha256": package_info["manifest_sha256"],
                    "source_bundle_sha256": package_info["source_bundle_sha256"],
                    "annotation_sha256": lock_info["annotation_sha256"],
                    "reviewer_id": lock_info["reviewer_id"],
                    "locked_at": lock_info["locked_at"],
                    "source_count": package_info["source_count"],
                    "source_package_files": package_info["file_sha256"],
                    "inference_order_status": inference_status,
                    "identity_and_exposure_limitation": "Reviewer identity and prior exposure remain self-attested and are not independently authenticated by this validator.",
                },
                ensure_ascii=False,
            )
        )
        return 0
    except (OSError, json.JSONDecodeError, SourceOnlyPackageError, KeyError, TypeError, ValueError) as exc:
        print(json.dumps({"status": "ANNOTATION_LOCK_INVALID", "reason": str(exc)}, ensure_ascii=False))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
