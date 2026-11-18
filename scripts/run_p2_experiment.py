"""Run a locked Tutor Support local-model proposal experiment and export its evidence."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from eqcr.p2_experiment import (  # noqa: E402
    EXPECTED_MODEL,
    P2ExperimentError,
    P2IndependentAnnotationBlocked,
    run_local_tutor_proposal_experiment,
)
from eqcr.p2_reviewer_package import default_source_package_root  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--annotation-lock", required=True, help="Path to the downloaded, hash-locked source-only annotation JSON.")
    parser.add_argument("--model", default=EXPECTED_MODEL, help=f"Exact installed local model tag (default: {EXPECTED_MODEL}).")
    parser.add_argument("--output-root", default=str(ROOT / "runs" / "p2-experiments"), help="New run folders are created here; existing runs are never overwritten.")
    parser.add_argument("--source-package", default=str(default_source_package_root()), help="Source-only reviewer package directory; every listed file and hash is checked before inference.")
    args = parser.parse_args(argv)
    try:
        lock_path = Path(args.annotation_lock)
        if not lock_path.is_file():
            raise P2IndependentAnnotationBlocked("No locked source-only annotation file was supplied or found.")
        lock_bundle = json.loads(lock_path.read_text(encoding="utf-8"))
        if not isinstance(lock_bundle, dict):
            raise P2IndependentAnnotationBlocked("Locked source-only annotation file is not a JSON object.")
        run_dir = run_local_tutor_proposal_experiment(
            lock_bundle,
            model=args.model,
            output_root=Path(args.output_root),
            repo_root=ROOT,
            source_package_root=Path(args.source_package),
        )
    except P2IndependentAnnotationBlocked as exc:
        print(json.dumps({"status": exc.status, "reason": str(exc)}, ensure_ascii=False))
        return 3
    except json.JSONDecodeError as exc:
        print(json.dumps({"status": "P2_BLOCKED_INDEPENDENT_ANNOTATION", "reason": f"Annotation lock JSON is invalid: {exc}"}, ensure_ascii=False))
        return 3
    except (OSError, json.JSONDecodeError, P2ExperimentError) as exc:
        print(json.dumps({"status": "P2_EXPERIMENT_NOT_RUN", "reason": str(exc)}, ensure_ascii=False))
        return 2
    print(json.dumps({"status": "P2_MODEL_PROPOSAL_COMPLETE_PENDING_HUMAN_REVIEW", "run_dir": str(run_dir)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
