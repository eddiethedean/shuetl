"""Process supervision and loopback health probes for ETLantic roles."""

from __future__ import annotations

import json
import logging
import math
import signal
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

from fastapi import FastAPI

from .errors import ProviderReadinessError
from .postgresql import inspect_postgresql_engine
from .runtime import ManagedRuntime

_LOG = logging.getLogger("shuetl.runtime")


class _ProbeState:
    def __init__(self, role: str, stale_after: float) -> None:
        self.role = role
        self.stale_after = stale_after
        self._lock = threading.Lock()
        self._lifecycle = "starting"
        self._reason = "startup"
        self._provider_ok = False
        self._provider_checked = 0.0
        self._supervisor_checked = time.monotonic()

    def mark_running(self) -> None:
        with self._lock:
            if self._lifecycle == "starting":
                self._lifecycle = "running"
                self._reason = (
                    "ready"
                    if self._provider_ok
                    and time.monotonic() - self._provider_checked <= self.stale_after
                    else "provider_unavailable"
                )

    def mark_draining(self) -> None:
        with self._lock:
            if self._lifecycle not in {"failed", "stopped"}:
                self._lifecycle = "draining"
                self._reason = "shutdown_in_progress"

    def mark_failed(self, reason: str) -> None:
        with self._lock:
            self._lifecycle = "failed"
            self._reason = reason

    def mark_stopped(self) -> None:
        with self._lock:
            self._lifecycle = "stopped"
            self._reason = "process_stopped"

    def provider_result(self, healthy: bool, reason: str) -> None:
        now = time.monotonic()
        with self._lock:
            self._provider_ok = healthy
            self._provider_checked = now
            self._supervisor_checked = now
            if self._lifecycle == "running":
                self._reason = "ready" if healthy else reason

    def is_ready(self) -> bool:
        """Return whether a recent provider inspection permits new work."""

        now = time.monotonic()
        with self._lock:
            return (
                self._lifecycle == "running"
                and self._provider_ok
                and now - self._provider_checked <= self.stale_after
            )

    def snapshot(self, path: str) -> tuple[int, bytes]:
        now = time.monotonic()
        with self._lock:
            live = self._lifecycle == "draining" or (
                self._lifecycle not in {"failed", "stopped"}
                and now - self._supervisor_checked <= self.stale_after
            )
            ready = (
                self._lifecycle == "running"
                and live
                and self._provider_ok
                and now - self._provider_checked <= self.stale_after
            )
            status = live if path == "/live" else ready
            reason = self._reason
            if not live:
                reason = "supervisor_stale"
            elif path == "/ready" and self._lifecycle == "draining":
                reason = "shutdown_in_progress"
            body = json.dumps(
                {
                    "role": self.role,
                    "state": self._lifecycle,
                    "live": live,
                    "ready": ready,
                    "reason": reason,
                },
                separators=(",", ":"),
            ).encode("utf-8")
        return (200 if status else 503), body


def serve_gateway(runtime: ManagedRuntime) -> int:
    """Run the gateway with provider-gated requests and a private health probe."""

    if runtime.settings.role != "gateway" or not isinstance(runtime.app, FastAPI):
        raise ProviderReadinessError("gateway runtime was not constructed")
    settings = runtime.settings
    if settings.probe_port is None:
        raise ProviderReadinessError("gateway probe port is required")
    state = _ProbeState("gateway", settings.probe_stale_after_seconds)
    stop = threading.Event()
    probe: ThreadingHTTPServer | None = None
    probe_thread: threading.Thread | None = None
    monitor = threading.Thread(
        target=_monitor_provider,
        args=(runtime, state, stop, settings.probe_refresh_seconds),
        name="shuetl-health-gateway",
        daemon=False,
    )
    probe_started = False
    monitor_started = False
    result = 0
    previous_sigterm_handler: Any | None = None
    try:
        import uvicorn
        from fastapi.responses import JSONResponse

        @runtime.app.middleware("http")
        async def require_provider_readiness(request: Any, call_next: Any) -> Any:
            health_path = f"{settings.api_prefix.rstrip('/')}/health"
            if request.url.path == health_path:
                return await call_next(request)
            if not state.is_ready():
                return JSONResponse(
                    status_code=503,
                    content={"detail": "Gateway is not ready."},
                )
            return await call_next(request)

        config = uvicorn.Config(
            runtime.app,
            host=settings.gateway_host,
            port=settings.gateway_port,
            access_log=False,
            log_config=None,
            timeout_graceful_shutdown=math.ceil(settings.shutdown_grace_seconds),
        )

        class ProbeAwareServer(uvicorn.Server):
            async def startup(self, sockets: Any = None) -> None:
                await super().startup(sockets=sockets)
                if self.started:
                    state.mark_running()

            def handle_exit(self, sig: int, frame: Any) -> None:
                state.mark_draining()
                super().handle_exit(sig, frame)

        server = ProbeAwareServer(config)
        if threading.current_thread() is threading.main_thread():
            # Uvicorn re-raises captured SIGTERM after graceful shutdown. Keep
            # that re-raise inside this function until its cleanup has run.
            previous_sigterm_handler = signal.signal(
                signal.SIGTERM, server.handle_exit
            )
        probe = _make_probe_server(settings.probe_port, state)
        probe_thread = threading.Thread(
            target=probe.serve_forever,
            name="shuetl-probe-gateway",
            daemon=True,
        )
        probe_thread.start()
        probe_started = True
        monitor.start()
        monitor_started = True
        server.run()
        if not server.started:
            result = 1
    except Exception:
        state.mark_failed("gateway_server_failed")
        _LOG.error("Gateway process failed (reason=gateway_server_failed)")
        result = 1
    finally:
        state.mark_draining()
        stop.set()
        if monitor_started:
            monitor.join()
        if probe is not None:
            if probe_started:
                probe.shutdown()
            probe.server_close()
        if probe_thread is not None and probe_started:
            probe_thread.join(timeout=2)
        if result == 0:
            state.mark_stopped()
        if not _close_runtime(runtime):
            result = 1
        if previous_sigterm_handler is not None:
            signal.signal(signal.SIGTERM, previous_sigterm_handler)
    return result


def serve_runtime_role(runtime: ManagedRuntime) -> int:
    """Supervise scheduler or worker ticks and serve loopback probes."""

    settings = runtime.settings
    if settings.role not in {"scheduler", "worker"} or runtime.service is None:
        raise ProviderReadinessError("runtime role was not constructed")
    if settings.probe_port is None:
        raise ProviderReadinessError("runtime probe port is required")

    state = _ProbeState(settings.role, settings.probe_stale_after_seconds)
    stop = threading.Event()
    tick_failed = threading.Event()
    probe: ThreadingHTTPServer | None = None
    probe_thread: threading.Thread | None = None
    monitor = threading.Thread(
        target=_monitor_provider,
        args=(runtime, state, stop, settings.probe_refresh_seconds),
        name=f"shuetl-health-{settings.role}",
        daemon=False,
    )
    tick_thread = threading.Thread(
        target=_run_ticks,
        args=(runtime, state, stop, tick_failed),
        name=f"shuetl-tick-{settings.role}",
        daemon=False,
    )
    previous_handlers: dict[int, Any] = {}
    monitor_started = False
    tick_started = False
    probe_started = False
    drain_called = False
    result = 0

    def request_shutdown(_signum: int, _frame: Any) -> None:
        state.mark_draining()
        stop.set()

    try:
        if threading.current_thread() is threading.main_thread():
            for signum in (signal.SIGINT, signal.SIGTERM):
                previous_handlers[signum] = signal.signal(signum, request_shutdown)
        probe = _make_probe_server(settings.probe_port, state)
        probe_thread = threading.Thread(
            target=probe.serve_forever,
            name=f"shuetl-probe-{settings.role}",
            daemon=True,
        )
        probe_thread.start()
        probe_started = True
        monitor.start()
        monitor_started = True
        state.mark_running()
        tick_thread.start()
        tick_started = True
        stop.wait()
        state.mark_draining()
    except OSError:
        stop.set()
        state.mark_failed("probe_bind_failed")
        _LOG.error("Runtime probe server failed (reason=probe_bind_failed)")
        result = 1
    except Exception:
        stop.set()
        state.mark_failed("runtime_supervisor_failed")
        _LOG.error("Runtime supervisor failed (reason=runtime_supervisor_failed)")
        result = 1
    finally:
        stop.set()
        if tick_started and not drain_called:
            _drain_service(runtime.service)
            drain_called = True
        if tick_started:
            deadline = time.monotonic() + settings.shutdown_grace_seconds
            tick_thread.join(max(0.0, deadline - time.monotonic()))
            if monitor_started:
                monitor.join(max(0.0, deadline - time.monotonic()))
            if tick_thread.is_alive() or (monitor_started and monitor.is_alive()):
                _LOG.error(
                    "Runtime drain exceeded its grace period; awaiting active work "
                    "before closing resources (reason=shutdown_grace_expired)"
                )
            # Keep the engine alive until no thread can still use it.
            tick_thread.join()
        if monitor_started:
            monitor.join()
        if probe is not None:
            if probe_started:
                probe.shutdown()
            probe.server_close()
        if probe_thread is not None and probe_started:
            probe_thread.join(timeout=2)
        if tick_failed.is_set():
            state.mark_failed("runtime_tick_failed")
            result = 1
        elif result == 0:
            state.mark_stopped()
        if not _close_runtime(runtime):
            result = 1
        for signum in (signal.SIGINT, signal.SIGTERM):
            previous = previous_handlers.get(signum)
            if previous is not None:
                signal.signal(signum, previous)
    return result


def _make_probe_server(port: int, state: _ProbeState) -> ThreadingHTTPServer:
    class ProbeHandler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def do_GET(self) -> None:  # noqa: N802 - stdlib handler API
            path = self.path.split("?", 1)[0]
            if path not in {"/live", "/ready"}:
                status, body = 404, b'{"reason":"not_found"}'
            else:
                status, body = state.snapshot(path)
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Connection", "close")
            self.end_headers()
            self.wfile.write(body)
            self.close_connection = True

        def log_message(self, _format: str, *args: object) -> None:
            del args

    return ThreadingHTTPServer(("127.0.0.1", port), ProbeHandler)


def _monitor_provider(
    runtime: ManagedRuntime,
    state: _ProbeState,
    stop: threading.Event,
    interval: float,
) -> None:
    while not stop.is_set():
        try:
            result = inspect_postgresql_engine(runtime.backend.engine)
            healthy = result.state == "head" and result.version is not None
            reason = "ready" if healthy else f"schema_{result.state.replace('-', '_')}"
            state.provider_result(healthy, reason)
        except Exception:
            state.provider_result(False, "database_unavailable")
        stop.wait(interval)


def _run_ticks(
    runtime: ManagedRuntime,
    state: _ProbeState,
    stop: threading.Event,
    failed: threading.Event,
) -> None:
    service = runtime.service
    context = runtime.context
    if service is None or context is None:
        state.mark_failed("runtime_binding_missing")
        failed.set()
        stop.set()
        return
    while not stop.is_set():
        if not state.is_ready():
            stop.wait(runtime.settings.runtime_poll_interval_seconds)
            continue
        try:
            if runtime.settings.role == "scheduler":
                service.tick(context)
            elif runtime.settings.role == "worker":
                if runtime.settings.worker_kind == "actions":
                    service.tick(context, limit=1)
                else:
                    service.tick(context, limit=1)
            else:
                raise ProviderReadinessError("unsupported runtime tick role")
        except Exception as exc:
            if _is_database_error(exc):
                state.provider_result(False, "database_unavailable")
                _LOG.warning("Runtime tick paused (reason=database_unavailable)")
            else:
                state.mark_failed("runtime_tick_failed")
                failed.set()
                stop.set()
                return
        if stop.wait(runtime.settings.runtime_poll_interval_seconds):
            return


def _drain_service(service: Any) -> None:
    drain = getattr(service, "drain", None)
    if callable(drain):
        try:
            drain()
        except Exception:
            _LOG.error("Upstream drain failed (reason=upstream_drain_failed)")


def _close_runtime(runtime: ManagedRuntime) -> bool:
    try:
        runtime.close()
    except Exception:
        _LOG.error("Runtime cleanup failed (reason=resource_close_failed)")
        return False
    return True


def _is_database_error(error: Exception) -> bool:
    return any(
        cls.__module__.startswith(("sqlalchemy.", "psycopg"))
        for cls in type(error).__mro__
    )


__all__ = ["serve_gateway", "serve_runtime_role"]
