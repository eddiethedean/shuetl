"""Exercise supervisor failures with real ASGI and published role handles."""

from __future__ import annotations

import socket
import threading
import time
from contextlib import asynccontextmanager, contextmanager
from dataclasses import replace
from types import SimpleNamespace

import pytest
from etlantic_sqlmodel import create_managed_backend, create_sqlite_engine
from etlantic_sqlmodel.migrations import upgrade
from fastapi import FastAPI
from tests.unit.test_runtime_contract import _preview_settings
from tests.unit.test_runtime_failures import bindings

import shuetl.backend as backend_module
import shuetl.runtime as runtime_module
from shuetl.backend import BackendRuntime


def wait_for(predicate, timeout=5):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return
        time.sleep(0.01)
    raise AssertionError("supervisor did not reach the expected state")


@pytest.fixture
def supervisor(monkeypatch):
    states = []
    handlers = []
    real_probe = runtime_module.serve_probes

    def capture_probe(state, port):
        states.append(state)
        return real_probe(state, port)

    monkeypatch.setattr(runtime_module, "serve_probes", capture_probe)
    monkeypatch.setattr(
        runtime_module,
        "_install_signals",
        lambda callback: handlers.append(callback) or {},
    )
    monkeypatch.setattr(runtime_module, "_restore_signals", lambda previous: None)
    monkeypatch.setattr(
        "shuetl.postgresql.inspect_postgresql_engine",
        lambda engine: SimpleNamespace(state="head"),
    )

    @contextmanager
    def running(call):
        outcomes = []

        def invoke():
            try:
                outcomes.append(call())
            except BaseException as exc:
                outcomes.append(exc)

        thread = threading.Thread(target=invoke, daemon=True)
        thread.start()
        wait_for(lambda: (handlers and states) or outcomes)
        assert not outcomes or not isinstance(outcomes[0], BaseException), outcomes
        try:
            yield states[0], outcomes
        finally:
            handlers[0](15, None)
            thread.join(timeout=8)
            assert not thread.is_alive(), "supervisor failed to drain"
            assert not any(isinstance(value, BaseException) for value in outcomes)

    return running


def free_port():
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        return listener.getsockname()[1]


def gateway(app):
    return BackendRuntime(
        settings=_preview_settings(
            role="gateway", probe_port=free_port(), shutdown_grace_seconds=1
        ),
        bindings=bindings(),
        backend=SimpleNamespace(engine=None),
        role_handle=None,
        context=None,
        app=app,
    )


def test_gateway_is_unready_until_lifespan_and_listener_start(supervisor):
    entered = threading.Event()
    release = threading.Event()

    @asynccontextmanager
    async def lifespan(app):
        entered.set()
        import asyncio

        while not release.is_set():
            await asyncio.sleep(0.01)
        yield

    app = FastAPI(lifespan=lifespan)
    port = free_port()
    with supervisor(
        lambda: runtime_module._serve_gateway(gateway(app), host="127.0.0.1", port=port)
    ) as (state, outcomes):
        try:
            assert entered.wait(5)
            assert state.payload(False)[0] == 503
            with (
                pytest.raises(OSError),
                socket.create_connection(("127.0.0.1", port), timeout=0.1),
            ):
                pass
        finally:
            release.set()
        wait_for(lambda: state.payload(False)[0] == 200)
        with socket.create_connection(("127.0.0.1", port), timeout=1):
            pass
    assert outcomes == [0]


@pytest.mark.parametrize("failure", ["occupied_port", "lifespan", "system_exit"])
def test_gateway_startup_failures_exit_nonzero(supervisor, failure, monkeypatch):
    @asynccontextmanager
    async def lifespan(app):
        raise RuntimeError("lifespan failed")
        yield

    app = FastAPI(lifespan=lifespan) if failure == "lifespan" else FastAPI()
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        port = listener.getsockname()[1]
        if failure == "occupied_port":
            listener.listen()
        else:
            listener.close()
        if failure == "system_exit":
            import uvicorn

            def fail(server):
                raise SystemExit(0)

            monkeypatch.setattr(uvicorn.Server, "run", fail)
        with supervisor(
            lambda: runtime_module._serve_gateway(
                gateway(app), host="127.0.0.1", port=port
            )
        ) as (state, outcomes):
            wait_for(lambda: outcomes)
            assert state.payload(False)[0] == 503
        assert outcomes == [1]


@pytest.fixture
def sql_runtime(tmp_path, monkeypatch):
    engine = create_sqlite_engine(f"sqlite:///{tmp_path / 'runtime.db'}")
    upgrade(engine)

    def factory(config, **kwargs):
        return create_managed_backend(
            replace(config, database_url=None, engine_options={}),
            engine=engine,
            **kwargs,
        )

    monkeypatch.setattr(backend_module, "create_managed_backend", factory)
    runtimes = []

    def construct(role="scheduler", **kwargs):
        binding = bindings(**kwargs)
        runtime = backend_module.create_backend_runtime(
            _preview_settings(
                role=role,
                worker_kind="actions" if role == "worker" else "runs",
                probe_port=free_port(),
                shutdown_grace_seconds=0.1,
                dispatch_interval_seconds=0.05,
            ),
            binding,
        )
        runtimes.append(runtime)
        return runtime

    yield construct
    for runtime in runtimes:
        runtime.close()
    engine.dispose()


@pytest.mark.parametrize("failure", ["lease_store", "exception"])
def test_scheduler_recovers_after_transient_failure(supervisor, sql_runtime, failure):
    runtime = sql_runtime()
    role = runtime.role_handle
    store = runtime.backend.schedule_store
    calls = []
    operation = store.acquire_leader_lease if failure == "lease_store" else role.tick

    def intermittent(*args, **kwargs):
        calls.append(1)
        if len(calls) == 1:
            raise OSError("temporary outage")
        return operation(*args, **kwargs)

    if failure == "lease_store":
        store.acquire_leader_lease = intermittent
    else:
        role.tick = intermittent
    with supervisor(lambda: runtime_module._serve_worker(runtime)) as (state, outcomes):
        wait_for(lambda: len(calls) >= 2 and state.payload(False)[0] == 200)
        assert role.status().prerequisites == "usable"
    assert outcomes == [0]


def test_active_upstream_close_retains_host_resources(sql_runtime):
    calls = []
    runtime = sql_runtime(close=lambda: calls.append("host"))
    entered = threading.Event()
    release = threading.Event()
    store = runtime.backend.schedule_store
    original = store.acquire_leader_lease

    def blocked(*args, **kwargs):
        entered.set()
        assert release.wait(5)
        return original(*args, **kwargs)

    store.acquire_leader_lease = blocked
    worker = threading.Thread(target=lambda: runtime.role_handle.tick(runtime.context))
    worker.start()
    try:
        assert entered.wait(5)
        with pytest.raises(RuntimeError, match="active"):
            runtime.close()
        assert calls == []
        assert not runtime.closed
    finally:
        release.set()
        worker.join(5)
    runtime.close()
    assert runtime.closed
    assert calls == ["host"]


def test_host_handler_executes_a_canonical_action_job(sql_runtime):
    observed = []

    async def handler(ctx, request):
        observed.append((ctx.tenant.tenant_id, dict(request)))
        return {"connected": True}

    runtime = sql_runtime(role="worker", action_handlers={"connector.test": handler})
    runtime.bindings.authorizer.grant(runtime.context, "connector.test")
    runtime.bindings.authorizer.grant(runtime.context, "connector.action.read")
    service = runtime.backend.managed_service
    job = service.submit_connector_action(
        runtime.context,
        "connector.test",
        {"provider": "postgresql", "connection_id": "saved-connection"},
        idempotency_key="handler-regression",
    )
    assert runtime.role_handle.tick(runtime.context) == 1
    result = service.get_connector_action(runtime.context, job["action_id"])
    assert result["status"] == "succeeded", result
    assert result["result"] == {"connected": True}
    assert observed == [
        ("tenant-a", {"provider": "postgresql", "connection_id": "saved-connection"})
    ]
