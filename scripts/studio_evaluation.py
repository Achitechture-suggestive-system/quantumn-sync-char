"""Freeze source-only Studio studies and gate inference/scoring on independent references."""

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from eqcr.studio_evaluation import git_state, readiness, run_study, score_study
from eqcr.studio_evaluation_protocol import (PROTOCOL, EvaluationBlocked, _write_new, adjudicate, annotation_template,
                                            load_study, lock_annotation, prepare_study)


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    prepare = commands.add_parser("prepare")
    prepare.add_argument("--source", type=Path, required=True)
    prepare.add_argument("--folder", type=Path, required=True)
    prepare.add_argument("--model-digest", required=True)
    prepare.add_argument("--repetitions", type=int, default=3)
    for action in ("status", "lock", "adjudication-template", "adjudicate", "run", "score"):
        command = commands.add_parser(action)
        command.add_argument("--folder", type=Path, required=True)
        if action in {"status", "run", "score"}:
            command.add_argument("--reference", type=Path, required=action != "status")
        if action in {"lock", "adjudicate"}:
            command.add_argument("--submission", type=Path, required=True)
        if action in {"adjudicate", "adjudication-template"}:
            command.add_argument("--annotation-locks", type=Path, nargs=2, required=True)
        if action in {"lock", "adjudicate", "adjudication-template", "score"}:
            command.add_argument("--output", type=Path, required=True)
        if action == "score":
            command.add_argument("--run-folder", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "prepare":
            state = git_state()
            if state["dirty"]:
                raise EvaluationBlocked("Commit/thống nhất checkout trước khi freeze; không tự loại công việc đang sửa.")
            result = prepare_study(read(args.source), args.folder, model_digest=args.model_digest, code_sha=state["sha"], repetitions=args.repetitions)
        elif args.command == "status":
            result = readiness(args.folder, read(args.reference) if args.reference else None)
        elif args.command == "run":
            result = {"run_folder": str(run_study(args.folder, read(args.reference), progress=lambda value: print(json.dumps(value), flush=True)))}
        else:
            source, frozen = load_study(args.folder)
            if args.output.resolve().is_relative_to((args.folder / "source_only").resolve()):
                raise EvaluationBlocked("Ghi submission/lock/report ngoài package source-only để giữ blinding.")
            if args.command == "lock":
                result = lock_annotation(source, frozen, read(args.submission))
            elif args.command == "adjudicate":
                result = adjudicate(source, frozen, [read(p) for p in args.annotation_locks], read(args.submission))
            elif args.command == "adjudication-template":
                from eqcr.studio_evaluation_protocol import verify_annotation
                for path in args.annotation_locks:
                    verify_annotation(source, frozen, read(path))
                template = annotation_template(source, frozen["source_digest"])
                result = {"protocol": PROTOCOL, "package_digest": frozen["source_digest"], "adjudicator_id": "",
                          "provenance": "UNDECLARED", "no_model_output_exposure": False, "completed_at": None, "rows": template["rows"]}
            else:
                result = score_study(args.folder, args.run_folder, read(args.reference))
            _write_new(args.output, result)
        print(json.dumps(result, ensure_ascii=True))
        return 0
    except (ValueError, TypeError, KeyError, OSError) as exc:
        print(json.dumps({"status": "STUDIO_EVALUATION_BLOCKED", "reason": str(exc), "semantic_accuracy": None, "link_metrics": None}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
