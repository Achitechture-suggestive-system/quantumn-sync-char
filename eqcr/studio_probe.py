"""Bounded local execution evidence tied to a reviewed reference contract and candidate."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import socket
import subprocess
import sys
import time
from urllib.request import urlopen
from uuid import uuid4

from .studio_boundaries import contract_issues, fingerprint
from .studio_protocol import MAX_ATTEMPTS, TIMEOUT_SECONDS, protocol_issues
from .studio_probe_worker import request_json


def probe_binding(architecture, candidate, review) -> str:
    return fingerprint({"architecture": architecture.model_dump(mode="json"), "groups": candidate.groups,
                        "contract": review.model_dump(mode="json")})


def harness_hashes():
    return {name: sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()
            for name in ("studio_probe.py", "studio_probe_worker.py", "studio_protocol.py")}


def probe_is_current(architecture, candidate, review, report) -> bool:
    return report.get("binding") == probe_binding(architecture, candidate, review) and report.get("harness_sha256") == harness_hashes()


def probe_issues(architecture, candidate, review) -> list[str]:
    from .quantum_tradeoff import group_index, hard_constraints
    from .studio_evidence import evidence_blockers

    ids = [item for group in candidate.groups for item in group]
    if len(set(ids)) != len(ids) or set(ids) != {item.id for item in architecture.components}:
        return ["Phương án cần phủ đúng một lần mỗi component hiện hành."]
    assignment = group_index(candidate.groups)
    issues = contract_issues(architecture, review) + protocol_issues(review)
    if evidence_blockers(architecture):
        issues.append("Mô hình còn căn cứ cũ cần review trước khi chạy probe.")
    if any(rule.violated_by(assignment) for rule in hard_constraints(architecture)):
        issues.append("Phương án vi phạm hard constraint hiện hành.")
    if review.source not in assignment or review.target not in assignment or assignment.get(review.source) == assignment.get(review.target):
        issues.append("Chọn tương tác đi qua hai Quantum của phương án đang xem.")
    return issues


class Worker:
    def __init__(self, folder: Path, role: str, **config):
        self.ready = folder / f"{role}-{uuid4().hex}.ready.json"
        self.config_path = self.ready.with_suffix(".config.json")
        self.config_path.write_text(json.dumps({"role": role, "ready": str(self.ready), **config}), encoding="utf-8")
        self.error_path = self.ready.with_suffix(".stderr.txt")
        with self.error_path.open("wb") as error:
            self.process = subprocess.Popen([sys.executable, "-m", "eqcr.studio_probe_worker", "--config", str(self.config_path)],
                                            cwd=Path(__file__).parents[1], stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                                            stderr=error, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        deadline = time.monotonic() + 10
        while not self.ready.exists():
            if self.process.poll() is not None:
                raise RuntimeError(f"{role} không khởi động được: {self.error_path.read_text(encoding='utf-8')[-1000:]}")
            if time.monotonic() >= deadline:
                self.stop()
                raise RuntimeError(f"{role} quá thời hạn khởi động.")
            time.sleep(0.02)
        self.port = json.loads(self.ready.read_text(encoding="utf-8"))["port"]

    def stop(self):
        if self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait(timeout=3)

    def state(self):
        with urlopen(f"http://127.0.0.1:{self.port}/state", timeout=3) as response:
            return json.loads(response.read())

    def post(self, path, payload):
        return request_json(f"http://127.0.0.1:{self.port}{path}", payload, timeout=4)


def run_boundary_probe(architecture, candidate, review, *, root: Path | None = None) -> dict:
    """Run actual HTTP/process faults. No arbitrary endpoints or contract-to-code inference."""
    if issues := probe_issues(architecture, candidate, review):
        raise ValueError(" ".join(issues))
    from .storage import ARTIFACT_ROOT

    identifier = f"probe-{uuid4().hex}"
    folder = (root if root is not None else ARTIFACT_ROOT / "quantum-studio" / "boundary-probes") / identifier
    folder.mkdir(parents=True, exist_ok=False)
    inputs = {"architecture": architecture.model_dump(mode="json"), "candidate_id": candidate.id, "groups": candidate.groups,
              "contract_id": review.contract.contract_id, "binding": probe_binding(architecture, candidate, review)}
    (folder / "input.json").write_text(json.dumps(inputs, ensure_ascii=False, indent=2), encoding="utf-8")
    report = {"schema": "STUDIO-BOUNDARY-PROBE@1", "id": identifier, "recorded_at": datetime.now(timezone.utc).isoformat(),
              "binding": inputs["binding"], "candidate_id": candidate.id, "source": review.source, "target": review.target,
              "mode": review.contract.selected_mode, "contract_id": review.contract.contract_id,
              "reference_protocol": review.reference_protocol, "protocol_input_provenance": "PREPARED_FIXTURE",
              "review_provenance": review.provenance, "actor": review.actor, "provenance": "DETERMINISTIC_TRANSFORMATION",
              "evidence_kind": "LOCAL_RUNTIME_OBSERVATION", "deployability_status": "NOT_VERIFIED",
              "quality_measurement_status": "NOT_MEASURED", "status": "PROTOTYPE_CONTRACT_CHECK_FAILED", "checks": [],
              "runtime": {"python": sys.version, "sqlite": __import__('sqlite3').sqlite_version,
                          "platform": sys.platform, "timeout_per_attempt_ms": TIMEOUT_SECONDS * 1000,
                          "max_attempts_per_invocation": MAX_ATTEMPTS},
              "prepared_events": [{"v": 1, "event_id": "prepared-event-1", "value": 11},
                                  {"v": 1, "event_id": "prepared-event-2", "value": 7}],
              "limitations": ["Prepared APPLY_EVENT operation; no domain business logic or domain-store ownership proof.",
                              "Loopback HTTP, separate processes and SQLite files; no TLS, broker, cloud or power-loss test.",
                              "Bounded sequential fault schedule; no multi-writer, arbitrary interleaving or liveness proof.",
                              "Manual dispatch and bounded retries; no eventual delivery, global exactly-once or production SLO guarantee."]}
    workers = []
    raw_observations = []
    mode = review.contract.selected_mode
    control = folder / "receiver-control.json"

    def worker(role, **kwargs):
        item = Worker(folder, role, **kwargs)
        workers.append(item)
        return item

    def check(name, passed, observation):
        report["checks"].append({"name": name, "passed": bool(passed), "observation": observation,
                                  "provenance": "DETERMINISTIC_TRANSFORMATION", "evidence_kind": "LOCAL_RUNTIME_OBSERVATION"})
        raw_observations.append({"step": name, "observation": observation})

    def producer():
        return worker("producer", database=str(folder / "producer.sqlite"), receiver_control=str(control), mode=mode)

    def receiver(**faults):
        item = worker("receiver", database=str(folder / "receiver.sqlite"), **faults)
        control.write_text(json.dumps({"port": item.port}), encoding="utf-8")
        return item

    def delivery_details(response):
        deliveries = response[1].get("deliveries", [])
        return (deliveries[0] if deliveries else {}) if mode == "ASYNC" else response[1]

    event = {"v": 1, "event_id": "prepared-event-1", "value": 11}
    try:
        # Keep a bound, non-listening socket so the unavailable destination cannot be another service.
        with socket.socket() as reserved:
            reserved.bind(("127.0.0.1", 0))
            control.write_text(json.dumps({"port": reserved.getsockname()[1]}), encoding="utf-8")
            sender = producer()
            result = sender.post("/submit", event)
            state = sender.state()
            check("receiver_unavailable", result[0] == (202 if mode == "ASYNC" else 503)
                  and state["pending"] == (1 if mode == "ASYNC" else 0), {"response": result, "producer": state})
            if mode == "ASYNC":
                failed_dispatch = sender.post("/dispatch", {})
                attempts = delivery_details(failed_dispatch).get("attempts", [])
            else:
                failed_dispatch = result
                attempts = result[1].get("attempts", [])
            check("bounded_failed_attempts", len(attempts) == MAX_ATTEMPTS and all(item["status"] == 0 for item in attempts), failed_dispatch)
            sender.stop()
            sender = producer()
            state = sender.state()
            check("producer_restart", state["pending"] == (1 if mode == "ASYNC" else 0)
                  and state["accepted"] == (1 if mode == "ASYNC" else 0), state)
        consumer = receiver(drop_ack=True)
        delivery = sender.post("/dispatch", {}) if mode == "ASYNC" else sender.post("/submit", event)
        item = delivery_details(delivery)
        attempts = item.get("attempts", [])
        state = consumer.state()
        check("ack_lost_after_commit_then_retry", delivery[0] == 200 and len(attempts) == 2 and attempts[0]["status"] == 0
              and attempts[-1]["status"] == 200 and attempts[-1]["body"].get("duplicate") is True
              and state["effects"] == 1 and state["effect_sum"] == 11, {"delivery": delivery, "receiver": state})
        repeated = sender.post("/submit", event)
        conflict = sender.post("/submit", {**event, "value": 99})
        direct_conflict = consumer.post("/apply", {**event, "value": 99})
        check("duplicate_and_conflicting_payload", repeated[0] == (202 if mode == "ASYNC" else 200)
              and conflict[0] == direct_conflict[0] == 409 and consumer.state()["effects"] == 1,
              {"repeat": repeated, "conflict_producer": conflict, "conflict_receiver": direct_conflict, "receiver": consumer.state()})
        consumer.stop()
        consumer = receiver(delay_ack=True)
        check("receiver_restart_keeps_effect", consumer.state()["effects"] == 1, consumer.state())
        second = {**event, "event_id": "prepared-event-2", "value": 7}
        submission = sender.post("/submit", second)
        delivery = sender.post("/dispatch", {}) if mode == "ASYNC" else submission
        item = delivery_details(delivery)
        attempts = item.get("attempts", [])
        check("timeout_after_commit_then_retry", delivery[0] == 200 and len(attempts) >= 2
              and attempts[0]["status"] == 0 and attempts[0]["body"].get("transport_error") == "TimeoutError"
              and attempts[-1]["status"] == 200 and consumer.state()["effects"] == 2,
              {"delivery": delivery, "receiver": consumer.state()})
        bad_version = sender.post("/submit", {**event, "v": 2})
        check("unsupported_version_rejected", bad_version[0] == 400, bad_version)
        if mode == "ASYNC":
            final = sender.state()
            check("outbox_acknowledged", final["pending"] == 0 and final["accepted"] == 2, final)
        else:
            check("sync_returns_after_committed_effect", consumer.state()["effect_sum"] == 18, consumer.state())
        if all(item["passed"] for item in report["checks"]):
            report["status"] = "PROTOTYPE_CONTRACT_CHECK_PASSED"
    except (OSError, ValueError, RuntimeError) as exc:
        report["error"] = f"{type(exc).__name__}: {exc}"
    finally:
        for item in workers:
            item.stop()
        report["workers_stopped"] = all(item.process.poll() is not None for item in workers)
        if not report["workers_stopped"]:
            report["status"] = "PROTOTYPE_CONTRACT_CHECK_FAILED"
        report["worker_pids"] = [item.process.pid for item in workers]
        (folder / "observations.json").write_text(json.dumps(raw_observations, indent=2), encoding="utf-8")
        report["artifact_hashes"] = {name: sha256((folder / name).read_bytes()).hexdigest()
                                     for name in ("input.json", "observations.json", "producer.sqlite", "receiver.sqlite") if (folder / name).exists()}
        report["harness_sha256"] = harness_hashes()
        (folder / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report


def main():
    from .quantum_tradeoff import Architecture, Preferences, analyze

    parser = argparse.ArgumentParser(description="Run a reviewed prepared reference contract, not arbitrary domain logic")
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--candidate-id", required=True)
    parser.add_argument("--edge", nargs=2, required=True, metavar=("SOURCE", "TARGET"))
    parser.add_argument("--output-root", type=Path)
    arguments = parser.parse_args()
    model = Architecture.model_validate_json(arguments.model.read_text(encoding="utf-8"))
    candidate = next((item for item in analyze(model, Preferences()).feasible if item.id == arguments.candidate_id), None)
    review = next((item for item in model.interaction_contracts if (item.source, item.target) == tuple(arguments.edge)), None)
    if candidate is None or review is None:
        parser.error("Candidate hoặc hợp đồng chưa tồn tại trong model đã review.")
    report = run_boundary_probe(model, candidate, review, root=arguments.output_root)
    print(json.dumps({"id": report["id"], "status": report["status"], "checks": len(report["checks"])}))
    return 0 if report["status"] == "PROTOTYPE_CONTRACT_CHECK_PASSED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
