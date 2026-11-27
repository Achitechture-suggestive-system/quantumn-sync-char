"""Build the source-only Tutor reviewer package from the frozen case input."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from eqcr.p2_reviewer_package import build_source_only_reviewer_package, default_source_package_root  # noqa: E402
from eqcr.tutor_support import get_tutor_support_fixture  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default=str(default_source_package_root()), help="New or empty directory for the source-only reviewer package.")
    args = parser.parse_args(argv)
    output = Path(args.output)
    if output.exists() and any(output.iterdir()):
        parser.error(f"Refusing to overwrite non-empty reviewer package directory: {output}")
    package_info = build_source_only_reviewer_package(get_tutor_support_fixture()["raw_requirements"], output)
    print(json.dumps(package_info, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
