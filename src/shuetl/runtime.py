"""Validated process lifecycle for gateway, scheduler and worker roles."""

from __future__ import annotations

import signal
import sys
import threading
import time
from contextlib import suppress
from typing import Any

from .backend import BackendRuntime, create_backend_runtime
from .errors import ProviderReadinessError
from .factory import load_bindings
from .probes import ProbeState, serve_probes
from .settings import ShuETLSettings

SERVER_REQUIREMENTS = {"uvicorn": "0.46.0"}


def serve(
    settings: ShuETLSettings,
    *,
    factory_path: str | None = None,
    host: str = "127.0.0.1",
    port: int = 8000,
) -> int:
    """Start one configured role and wait for a cooperative signal to drain."""
    if settings.profile != "postgresql-preview":
        raise ProviderReadinessError("serve requires the postgresql-preview profile")
    path = factory_path or settings.bindings_factory
    if path is None:
        raise ProviderReadinessError("a trusted bindings factory is required")
    from .compatibility import validate_core, validate_postgresql

    validate_core()
    validate_postgresql()
    if settings.role == "gateway":
        from .compatibility import validate_gateway_server

        validate_gateway_server()
    bindings = None
    runtime: BackendRuntime | None = None
    exit_code = 1
    try:
        bindings = load_bindings(path, settings)
        runtime = create_backend_runtime(settings, bindings)
        if settings.role == "gateway":
            exit_code = _serve_gateway(runtime, host=host, port=port)
        else:
            exit_code = _serve_worker(runtime)
    except KeyboardInterrupt:
        exit_code = 130
    except Exception as exc:
        print(
            f"shuetl serve failed ({type(exc).__name__}); "
            "inspect redacted process status",
            file=sys.stderr,
        )
        exit_code = 1
    finally:
        if runtime is not None:
            cleanup_complete = _close_when_drained(runtime)
            if exit_code == 0 and not cleanup_complete:
                exit_code = 1
        elif bindings is not None:
            with suppress(Exception):
                bindings.close()
    return exit_code


def _serve_gateway(runtime: BackendRuntime, *, host: str, port: int) -> int:
    _validate_server_pin()
    import uvicorn

    state = ProbeState("gateway")
    probe_server = serve_probes(state, runtime.settings.probe_port)
    stopping = threading.Event()
    server_exit = threading.Event()
    server: Any = None

    def request_stop(_signum: int, _frame: Any) -> None:
        if stopping.is_set():
            return
        stopping.set()
        state.update(
            state="draining",
            provider_ready=False,
            runtime_ready=False,
            reason="shutdown",
        )
        if server is not None:
            server.should_exit = True

    previous = _install_signals(request_stop)

    def refresh_gateway() -> None:
        while not stopping.is_set():
            try:
                from .postgresql import inspect_postgresql_engine

                schema = inspect_postgresql_engine(runtime.backend.engine)
                healthy = schema.state == "head"
                started = (
                    server is not None and server.started and not server_exit.is_set()
                )
                state.update(
                    provider_ready=healthy,
                    runtime_ready=healthy and started,
                    checked_at=time.monotonic(),
                    reason=(
                        "provider_unavailable"
                        if not healthy
                        else (None if started else "startup")
                    ),
                )
            except Exception:
                state.update(
                    provider_ready=False,
                    runtime_ready=False,
                    checked_at=time.monotonic(),
                    reason="provider_unavailable",
                )
            stopping.wait(0.5)

    readiness_thread = threading.Thread(
        target=refresh_gateway, name="shuetl-readiness", daemon=True
    )
    state.update(state="running", reason=None)
    readiness_thread.start()
    # Fail closed until the independent public provider inspection completes.
    ready_deadline = time.monotonic() + settings_timeout(runtime)
    while (
        not state.provider_available()
        and time.monotonic() < ready_deadline
        and not stopping.is_set()
    ):
        time.sleep(0.05)
    if stopping.is_set():
        readiness_thread.join(timeout=1.0)
        probe_server.shutdown()
        probe_server.server_close()
        _restore_signals(previous)
        return 0
    if not state.provider_available():
        stopping.set()
        readiness_thread.join(timeout=1.0)
        probe_server.shutdown()
        probe_server.server_close()
        _restore_signals(previous)
        raise ProviderReadinessError("gateway provider preflight failed")
    state.update(state="running", reason=None)
    server = uvicorn.Server(
        uvicorn.Config(
            runtime.app,
            host=host,
            port=port,
            log_config=None,
            access_log=False,
            timeout_graceful_shutdown=None,
        )
    )
    server_failure = threading.Event()

    def run_server() -> None:
        try:
            server.run()
        except BaseException:
            # Uvicorn uses SystemExit for socket bind failures.
            server_failure.set()
        finally:
            if not stopping.is_set():
                server_failure.set()
            state.update(runtime_ready=False, reason="server_stopped")
            server_exit.set()

    server_thread = threading.Thread(
        target=run_server, name="shuetl-asgi", daemon=False
    )

    try:
        server_thread.start()
        while not server_exit.wait(0.1):
            if stopping.is_set():
                break
        if stopping.is_set():
            server.should_exit = True
        server_thread.join(timeout=runtime.settings.shutdown_grace_seconds)
        if server_thread.is_alive():
            state.update(state="draining", reason="grace_expired")
            server_thread.join()
        state.update(
            state="failed" if server_failure.is_set() else "stopped",
            runtime_ready=False,
            reason="server_failed" if server_failure.is_set() else "stopped",
        )
        return 1 if server_failure.is_set() else 0
    finally:
        stopping.set()
        server.should_exit = True
        if server_thread.is_alive():
            server_thread.join()
        readiness_thread.join(timeout=2.0)
        probe_server.shutdown()
        probe_server.server_close()
        _restore_signals(previous)


def _serve_worker(runtime: BackendRuntime) -> int:
    settings = runtime.settings
    role = (
        "scheduler"
        if settings.role == "scheduler"
        else ("action_worker" if settings.worker_kind == "actions" else "run_worker")
    )
    state = ProbeState(role)
    state.max_age_seconds = max(15.0, settings.dispatch_interval_seconds * 5)
    probe_server = serve_probes(state, settings.probe_port)
    stop = threading.Event()
    active = threading.Event()
    dispatch_fault = threading.Event()
    provider_fault = threading.Event()

    def refresh() -> None:
        while not stop.is_set():
            try:
                from .postgresql import inspect_postgresql_engine

                schema = inspect_postgresql_engine(runtime.backend.engine)
                if schema.state == "head":
                    provider_fault.clear()
                else:
                    provider_fault.set()
                role_status = runtime.role_handle.status()
                prereq = getattr(
                    role_status.prerequisites, "value", role_status.prerequisites
                )
                usable = (
                    schema.state == "head"
                    and prereq == "usable"
                    and not dispatch_fault.is_set()
                )
                now = time.monotonic()
                state.update(
                    provider_ready=schema.state == "head",
                    runtime_ready=usable,
                    checked_at=now,
                    reason=(
                        None
                        if usable
                        else (
                            "dispatch_failed"
                            if dispatch_fault.is_set()
                            else (
                                "provider_unavailable"
                                if schema.state == "unreachable"
                                else "prerequisites_unavailable"
                            )
                        )
                    ),
                )
            except Exception:
                provider_fault.set()
                state.update(
                    provider_ready=False,
                    runtime_ready=False,
                    checked_at=time.monotonic(),
                    reason="provider_unavailable",
                )
            stop.wait(min(5.0, max(0.5, settings.dispatch_interval_seconds)))

    def dispatch() -> None:
        while not stop.is_set():
            # Upstream ticks recheck prerequisites and control admission. Use
            # fresh provider health for both bootstrap and recovery; stale role
            # readiness must not block the operation that can restore it.
            if (
                not stop.is_set()
                and not signal_received.is_set()
                and state.provider_available()
            ):
                active.set()
                try:
                    runtime.role_handle.tick(runtime.context)
                    dispatch_fault.clear()
                except Exception:
                    # An ordinary tick failure can be transient. Keep the
                    # process alive and unready; the paced loop retries after
                    # a fresh provider check and ETLantic re-evaluates its own
                    # prerequisites and admission state.
                    dispatch_fault.set()
                    state.update(runtime_ready=False, reason="dispatch_failed")
                except BaseException:
                    # SystemExit and other process-level failures must wake the
                    # supervisor and produce a failed process exit.
                    dispatch_fault.set()
                    state.update(runtime_ready=False, reason="dispatch_failed")
                    signal_received.set()
                    stop.set()
                    with suppress(Exception):
                        runtime.role_handle.request_drain()
                finally:
                    active.clear()
            stop.wait(settings.dispatch_interval_seconds)

    state.update(state="running", reason=None)
    refresh_thread = threading.Thread(
        target=refresh, name="shuetl-readiness", daemon=True
    )
    dispatch_thread = threading.Thread(
        target=dispatch, name="shuetl-dispatch", daemon=True
    )
    signal_received = threading.Event()

    def request_stop(_signum: int, _frame: Any) -> None:
        if signal_received.is_set():
            return
        signal_received.set()
        state.update(state="draining", runtime_ready=False, reason="shutdown")
        try:
            runtime.role_handle.request_drain()
        except Exception:
            dispatch_fault.set()

    previous = _install_signals(request_stop)
    try:
        refresh_thread.start()
        dispatch_thread.start()
        signal_received.wait()
        state.update(state="draining", runtime_ready=False, reason="shutdown")
        stop.set()
        with suppress(Exception):
            runtime.role_handle.request_drain()
        dispatch_thread.join(timeout=settings.shutdown_grace_seconds)
        if dispatch_thread.is_alive() or active.is_set():
            state.update(state="draining", runtime_ready=False, reason="grace_expired")
            # Keep the process/probe alive and the backend open until active
            # work finishes or an external supervisor force terminates it.
            dispatch_thread.join()
        refresh_thread.join(timeout=2.0)
        state.update(
            state="stopped", provider_ready=False, runtime_ready=False, reason="stopped"
        )
        return 1 if dispatch_fault.is_set() or provider_fault.is_set() else 0
    finally:
        stop.set()
        with suppress(Exception):
            runtime.role_handle.request_drain()
        if dispatch_thread.ident is not None and dispatch_thread.is_alive():
            dispatch_thread.join()
        if refresh_thread.ident is not None:
            refresh_thread.join(timeout=2.0)
        _restore_signals(previous)
        probe_server.shutdown()
        probe_server.server_close()


def _close_when_drained(runtime: BackendRuntime) -> bool:
    cleanup_complete = True
    role = runtime.role_handle
    if role is not None:
        try:
            role.request_drain()
            while getattr(role.status(), "in_flight", 0) > 0:
                time.sleep(0.05)
        except Exception:
            print("shuetl drain status unavailable", file=sys.stderr)
            cleanup_complete = False
    try:
        runtime.close()
    except Exception:
        print("shuetl cleanup incomplete", file=sys.stderr)
        cleanup_complete = False
    return cleanup_complete


def settings_timeout(runtime: BackendRuntime) -> float:
    return runtime.settings.provider_connect_timeout_seconds * 2


def _validate_server_pin() -> None:
    from importlib.metadata import PackageNotFoundError, version

    try:
        installed = version("uvicorn")
    except PackageNotFoundError:
        installed = None
    if installed != SERVER_REQUIREMENTS["uvicorn"]:
        raise ProviderReadinessError("install the pinned ShuETL server extra")


def _install_signals(handler: Any) -> dict[int, Any]:
    previous: dict[int, Any] = {}
    for signum in (signal.SIGINT, signal.SIGTERM):
        previous[signum] = signal.getsignal(signum)
        signal.signal(signum, handler)
    return previous


def _restore_signals(previous: dict[int, Any]) -> None:
    for signum, handler in previous.items():
        signal.signal(signum, handler)
