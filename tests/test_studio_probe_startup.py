"""Inject readiness races; do not relax boundary protocol assertions or timeout policies."""

import json
from pathlib import Path

import pytest

from eqcr import studio_probe


class FakeProcess:
    def __init__(self):
        self.active = True
        self.terminations = 0
        self.waits = 0

    def poll(self):
        return None if self.active else 0

    def terminate(self):
        self.terminations += 1
        self.active = False

    def wait(self, timeout):
        self.waits += 1


def launcher(monkeypatch, *, port=23456):
    process = FakeProcess()
    def start(arguments, **kwargs):
        config = json.loads(Path(arguments[-1]).read_text(encoding="utf-8"))
        Path(config["ready"]).write_text(json.dumps({"port": port}), encoding="utf-8")
        return process
    monkeypatch.setattr(studio_probe.subprocess, "Popen", start)
    return process


def test_transient_permission_and_incomplete_json_are_retried_inside_startup_deadline(tmp_path, monkeypatch):
    process = launcher(monkeypatch)
    original = Path.read_text
    attempts, sleeps = [], []
    def read(path, *args, **kwargs):
        if path.name.endswith(".ready.json"):
            attempts.append(path)
            if len(attempts) == 1:
                raise PermissionError("TEST_ONLY_SHARING_LOCK")
            if len(attempts) == 2:
                return "{"
        return original(path, *args, **kwargs)
    monkeypatch.setattr(Path, "read_text", read)
    monkeypatch.setattr(studio_probe.time, "sleep", sleeps.append)
    worker = studio_probe.Worker(tmp_path, "producer")
    assert worker.port == 23456 and len(attempts) == 3 and sleeps == [0.02, 0.02]
    assert process.terminations == 0
    worker.stop()
    assert process.terminations == process.waits == 1


def test_persistent_permission_failure_times_out_and_stops_unregistered_worker(tmp_path, monkeypatch):
    process = launcher(monkeypatch)
    original = Path.read_text
    def read(path, *args, **kwargs):
        if path.name.endswith(".ready.json"):
            raise PermissionError("TEST_ONLY_PERSISTENT_LOCK")
        return original(path, *args, **kwargs)
    clock = iter([0, 3, 11])
    monkeypatch.setattr(Path, "read_text", read)
    monkeypatch.setattr(studio_probe.time, "monotonic", lambda: next(clock))
    monkeypatch.setattr(studio_probe.time, "sleep", lambda _: None)
    with pytest.raises(RuntimeError, match="PermissionError"):
        studio_probe.Worker(tmp_path, "producer")
    assert process.terminations == process.waits == 1 and not process.active


@pytest.mark.parametrize("port", [0, True, "23456"])
def test_invalid_ready_port_fails_and_cleans_up_before_worker_registration(tmp_path, monkeypatch, port):
    process = launcher(monkeypatch, port=port)
    with pytest.raises(RuntimeError, match="ready port"):
        studio_probe.Worker(tmp_path, "receiver")
    assert process.terminations == process.waits == 1 and not process.active
