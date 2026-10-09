"""Loopback-only, role-local process readiness and liveness probes."""

from __future__ import annotations

import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any


class ProbeState:
    def __init__(self, role: str) -> None:
        self.role = role
        self._lock = threading.Lock()
        self.process_state = "starting"
        self.reason_code: str | None = "startup"
        self.provider_ready = False
        self.runtime_ready = False
        self.checked_at = 0.0
        self.max_age_seconds = 15.0

    def update(
        self,
        *,
        state: str | None = None,
        provider_ready: bool | None = None,
        runtime_ready: bool | None = None,
        reason: str | None = None,
        checked_at: float | None = None,
    ) -> None:
        with self._lock:
            if state is not None:
                self.process_state = state
            if provider_ready is not None:
                self.provider_ready = provider_ready
            if runtime_ready is not None:
                self.runtime_ready = runtime_ready
            self.reason_code = reason
            if checked_at is not None:
                self.checked_at = checked_at

    def payload(self, live: bool) -> tuple[int, dict[str, Any]]:
        with self._lock:
            snapshot = {
                "role": self.role,
                "process_state": self.process_state,
                "reason_code": self.reason_code,
            }
            process_state = self.process_state
            ready = (
                process_state == "running"
                and self.provider_ready
                and self.runtime_ready
                and self.checked_at > 0
                and time.monotonic() - self.checked_at <= self.max_age_seconds
            )
        if live:
            return (
                200 if process_state not in {"failed", "stopped"} else 503,
                {**snapshot, "live": process_state not in {"failed", "stopped"}},
            )
        return (200 if ready else 503, {**snapshot, "ready": ready})

    def provider_available(self) -> bool:
        """Return whether a role tick has a fresh, healthy provider check."""
        with self._lock:
            return (
                self.process_state == "running"
                and self.provider_ready
                and self.checked_at > 0
                and time.monotonic() - self.checked_at <= self.max_age_seconds
            )


def serve_probes(state: ProbeState, port: int) -> ThreadingHTTPServer:
    """Start a private loopback HTTP listener and return its owner."""

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            if self.path not in {"/live", "/ready"}:
                self.send_error(404)
                return
            status, body = state.payload(self.path == "/live")
            encoded = json.dumps(body, sort_keys=True, separators=(",", ":")).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(encoded)))
            self.end_headers()
            self.wfile.write(encoded)

        def log_message(self, _format: str, *_args: object) -> None:
            return

    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    server.daemon_threads = True
    thread = threading.Thread(
        target=server.serve_forever, name="shuetl-probes", daemon=True
    )
    thread.start()
    return server
