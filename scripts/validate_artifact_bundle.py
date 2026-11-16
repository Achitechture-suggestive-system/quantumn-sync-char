"""Verify hashes and manifest coverage in an exported EQCR artifact bundle."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from eqcr.storage import verify_export_zip  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bundle", type=Path, help="Path to an exported run artifacts ZIP.")
    args = parser.parse_args(argv)
    try:
        result = verify_export_zip(args.bundle.read_bytes())
    except (OSError, ValueError) as exc:
        print(json.dumps({"status": "FAIL", "reason": str(exc)}, ensure_ascii=False))
        return 1
    print(
        json.dumps(
            {
                "status": result["status"],
                "manifest_version": result["manifest_version"],
                "case_id": result["case_id"],
                "run_id": result["run_id"],
                "verified_member_count": result["verified_member_count"],
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
