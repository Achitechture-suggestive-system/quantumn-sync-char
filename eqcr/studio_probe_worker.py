"""Loopback-only, isolated reference producer/receiver used by the bounded Studio probe."""

from __future__ import annotations

import argparse
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
from pathlib import Path
import socket
import sqlite3
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .studio_protocol import MAX_ATTEMPTS, TIMEOUT_SECONDS


def request_json(url, payload, *, timeout=TIMEOUT_SECONDS):
    request = Request(url, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"})
    try:
        with urlopen(request, timeout=timeout) as response:
            return response.status, json.loads(response.read())
    except HTTPError as error:
        return error.code, json.loads(error.read())
    except (OSError, URLError, ValueError) as error:
        return 0, {"transport_error": type(error).__name__}


def valid_event(value):
    return (isinstance(value, dict) and set(value) == {"v", "event_id", "value"} and type(value["v"]) is int
            and value["v"] == 1 and isinstance(value["event_id"], str) and 0 < len(value["event_id"]) <= 100
            and type(value["value"]) is int and -(2**31) <= value["value"] < 2**31)


def serve(config):
    database = Path(config["database"])
    with sqlite3.connect(database) as connection:
        connection.executescript("""
            CREATE TABLE IF NOT EXISTS effects(event_id TEXT PRIMARY KEY, payload TEXT NOT NULL, value INTEGER NOT NULL);
            CREATE TABLE IF NOT EXISTS accepted(event_id TEXT PRIMARY KEY, payload TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS outbox(event_id TEXT PRIMARY KEY, payload TEXT NOT NULL, delivered INTEGER NOT NULL DEFAULT 0);
        """)

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_):
            pass

        def send(self, status, body):
            data = json.dumps(body).encode()
            try:
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)
            except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
                pass  # Expected when a deliberately delayed ACK outlives the client timeout.

        def do_GET(self):
            if self.path != "/state":
                return self.send(404, {})
            with sqlite3.connect(database) as connection:
                body = {"effects": connection.execute("SELECT count(*) FROM effects").fetchone()[0],
                        "effect_sum": connection.execute("SELECT coalesce(sum(value),0) FROM effects").fetchone()[0],
                        "accepted": connection.execute("SELECT count(*) FROM accepted").fetchone()[0],
                        "pending": connection.execute("SELECT count(*) FROM outbox WHERE delivered=0").fetchone()[0]}
            self.send(200, body)

        def deliver(self, payload):
            # The destination is a port emitted by the local receiver, never an input URL or remote address.
            port = int(json.loads(Path(config["receiver_control"]).read_text())["port"])
            observations = []
            for attempt in range(1, MAX_ATTEMPTS + 1):
                started = time.perf_counter()
                status, body = request_json(f"http://127.0.0.1:{port}/apply", payload)
                observations.append({"attempt": attempt, "status": status, "body": body,
                                     "elapsed_ms": round((time.perf_counter() - started) * 1000, 3)})
                if status in {200, 409}:
                    break
            return status, body, observations

        def do_POST(self):
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if not 0 < length <= 4096:
                    return self.send(400, {"error": "invalid_length"})
                payload = json.loads(self.rfile.read(length))
            except (ValueError, UnicodeError):
                return self.send(400, {"error": "invalid_json"})
            if config["role"] == "producer" and self.path == "/dispatch" and config["mode"] == "ASYNC":
                with sqlite3.connect(database) as connection:
                    pending = connection.execute("SELECT event_id,payload FROM outbox WHERE delivered=0 ORDER BY rowid LIMIT 10").fetchall()
                deliveries = []
                for event_id, raw in pending:
                    status, body, attempts = self.deliver(json.loads(raw))
                    if status == 200:
                        with sqlite3.connect(database) as connection:
                            connection.execute("UPDATE outbox SET delivered=1 WHERE event_id=?", (event_id,))
                    deliveries.append({"event_id": event_id, "status": status, "attempts": attempts, "response": body})
                return self.send(200, {"deliveries": deliveries})
            if not valid_event(payload):
                return self.send(400, {"error": "invalid_v1_envelope"})
            raw = json.dumps(payload, sort_keys=True, separators=(",", ":"))
            event_id = payload["event_id"]
            if config["role"] == "receiver" and self.path == "/apply":
                with sqlite3.connect(database) as connection:
                    connection.execute("BEGIN IMMEDIATE")
                    previous = connection.execute("SELECT payload FROM effects WHERE event_id=?", (event_id,)).fetchone()
                    if previous and previous[0] != raw:
                        return self.send(409, {"error": "id_conflict"})
                    duplicate = previous is not None
                    if not duplicate:
                        connection.execute("INSERT INTO effects VALUES(?,?,?)", (event_id, raw, payload["value"]))
                # Commit precedes both fault injection and the successful acknowledgement.
                if self.server.drop_ack and not duplicate:
                    self.server.drop_ack = False
                    self.close_connection = True
                    self.connection.shutdown(socket.SHUT_RDWR)
                    self.connection.close()
                    return
                if self.server.delay_ack and not duplicate:
                    time.sleep(TIMEOUT_SECONDS * 1.5)
                    self.server.delay_ack = False
                return self.send(200, {"applied": True, "duplicate": duplicate})
            if config["role"] == "producer" and self.path == "/submit":
                if config["mode"] == "SYNC":
                    status, body, attempts = self.deliver(payload)
                    return self.send(status if status in {200, 409} else 503, {"receiver": body, "attempts": attempts})
                with sqlite3.connect(database) as connection:
                    connection.execute("BEGIN IMMEDIATE")
                    previous = connection.execute("SELECT payload FROM accepted WHERE event_id=?", (event_id,)).fetchone()
                    if previous and previous[0] != raw:
                        return self.send(409, {"error": "id_conflict"})
                    if not previous:
                        connection.execute("INSERT INTO accepted VALUES(?,?)", (event_id, raw))
                        connection.execute("INSERT INTO outbox(event_id,payload) VALUES(?,?)", (event_id, raw))
                return self.send(202, {"durable": True, "completed": False, "duplicate": previous is not None})
            self.send(404, {})

    class Server(HTTPServer):
        allow_reuse_address = True

    server = Server(("127.0.0.1", config.get("port", 0)), Handler)
    server.drop_ack = config.get("drop_ack", False)
    server.delay_ack = config.get("delay_ack", False)
    ready = Path(config["ready"])
    temporary = ready.with_suffix(".tmp")
    temporary.write_text(json.dumps({"port": server.server_port}), encoding="utf-8")
    temporary.replace(ready)
    try:
        server.serve_forever(poll_interval=0.05)
    finally:
        server.server_close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    serve(json.loads(parser.parse_args().config.read_text(encoding="utf-8")))
