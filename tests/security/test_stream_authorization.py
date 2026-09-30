"""SSE authorization precedes run lookup and cursor/event access."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from typing import Any

from etlantic.control_plane import (
    ControlPlaneContext,
    EnvironmentRef,
    MemoryEventStore,
    MemorySubmissionStore,
    Principal,
    SecurityDomain,
    TenantRef,
    WorkspaceRef,
)
from etlantic.control_plane.memory import MemoryAuthorizer, MemoryDefinitionRepository
from etlantic_fastapi import ETLanticAPI
from fastapi import Request
from fastapi.testclient import TestClient

from shuetl import HostIdentityAdapter, ShuETL


class EventStoreProbe:
    def __init__(self, inner: MemoryEventStore) -> None:
        self.inner = inner
        self.cursors: list[tuple[str, str | None]] = []

    def append(self, *args: Any, **kwargs: Any) -> Any:
        return self.inner.append(*args, **kwargs)

    def list_after_cursor(
        self, ctx: ControlPlaneContext, cursor: str | None, *, limit: int = 100
    ) -> Any:
        self.cursors.append((ctx.principal.subject, cursor))
        return self.inner.list_after_cursor(ctx, cursor, limit=limit)


def _context(principal: Principal, tenant: str, workspace: str) -> ControlPlaneContext:
    return ControlPlaneContext(
        principal=principal,
        tenant=TenantRef(tenant_id=tenant),
        workspace=WorkspaceRef(tenant_id=tenant, workspace_id=workspace),
        environment=EnvironmentRef(name="production"),
        security_domain=SecurityDomain(domain_id="default"),
    )


def _app() -> tuple[Any, dict[str, ControlPlaneContext], EventStoreProbe]:
    contexts = {
        "alice": _context(
            Principal("alice", issuer="https://issuer.example"),
            "tenant-a",
            "workspace-a",
        ),
        "bob": _context(
            Principal("bob", issuer="https://issuer.example"), "tenant-b", "workspace-b"
        ),
    }
    teardowns: list[str] = []

    async def authenticate(request: Request) -> AsyncIterator[Principal]:
        principal = contexts[request.headers.get("X-Principal", "alice")].principal
        try:
            yield principal
        finally:
            teardowns.append(principal.subject)

    def make_context(principal: Principal, _request: Request) -> ControlPlaneContext:
        return contexts[principal.subject]

    adapter = HostIdentityAdapter.create(
        principal_dependency=authenticate,
        context_factory=make_context,
    )
    authorizer = MemoryAuthorizer()
    authorizer.grant(contexts["alice"], "run.events")
    submissions = MemorySubmissionStore()
    events_inner = MemoryEventStore()
    receipt = submissions.accept(
        contexts["alice"],
        idempotency_key="stream-security-idempotency",
        payload={"definition_id": "private"},
        resource_id="alice-run",
    ).receipt
    event = events_inner.append(
        contexts["alice"],
        kind="run.accepted",
        payload={"run_id": "alice-run", "access_token": "stream-secret-sentinel"},
    )
    foreign_event = events_inner.append(
        contexts["bob"],
        kind="run.accepted",
        payload={"run_id": "bob-run", "private": "foreign-cursor-sentinel"},
    )
    events = EventStoreProbe(events_inner)
    api = ETLanticAPI(
        authorizer=authorizer,
        definitions=MemoryDefinitionRepository(),
        submissions=submissions,
        events=events,
        context_factory=adapter.context_factory,
        principal_dependency=adapter.principal_dependency,
        profile="development",
    )
    app = ShuETL(api=api).create_app(prefix="/etl")
    app.state.security_teardowns = teardowns
    app.state.stream_cursor = event.cursor
    app.state.foreign_cursor = foreign_event.cursor
    app.state.receipt = receipt
    return app, contexts, events


def test_sse_denial_precedes_event_cursor_access_and_authorized_bad_cursor_is_410() -> (
    None
):
    app, _contexts, events = _app()
    with TestClient(app) as client:
        denied = client.get(
            "/etl/v1/runs/alice-run/events?cursor=foreign-cursor",
            headers={"X-Principal": "bob"},
        )
        assert denied.status_code == 404
        assert events.cursors == []

        foreign_cursor = client.get(
            f"/etl/v1/runs/alice-run/events?cursor={app.state.foreign_cursor}",
            headers={"X-Principal": "alice"},
        )
        assert foreign_cursor.status_code == 410
        assert events.cursors == [("alice", app.state.foreign_cursor)]

        unknown = client.get(
            "/etl/v1/runs/alice-run/events?cursor=unknown-cursor",
            headers={"X-Principal": "alice"},
        )
        assert unknown.status_code == 410
        assert events.cursors == [
            ("alice", app.state.foreign_cursor),
            ("alice", "unknown-cursor"),
        ]

        replay = client.get(
            "/etl/v1/runs/alice-run/events?follow=false",
            headers={"X-Principal": "alice"},
        )
        assert replay.status_code == 200
        assert "run.accepted" in replay.text
        assert "alice-run" in replay.text
        assert "stream-secret-sentinel" not in replay.text
        assert "foreign-cursor-sentinel" not in replay.text

        # An explicit query cursor retains precedence over Last-Event-ID.
        precedence = client.get(
            f"/etl/v1/runs/alice-run/events?cursor={app.state.stream_cursor}",
            headers={"X-Principal": "alice", "Last-Event-ID": "unknown-cursor"},
        )
        assert precedence.status_code == 200
    assert events.cursors[:3] == [
        ("alice", app.state.foreign_cursor),
        ("alice", "unknown-cursor"),
        ("alice", None),
    ]
    assert events.cursors[-1] == ("alice", app.state.stream_cursor)
    assert "stream-secret-sentinel" not in precedence.text


def test_sse_disconnect_runs_native_yield_dependency_teardown() -> None:
    app, _contexts, _events = _app()
    run_id = app.state.receipt.resource_id
    request_body = {
        "type": "http.request",
        "body": b"",
        "more_body": False,
    }

    async def exercise() -> list[dict[str, Any]]:
        response_started = asyncio.Event()
        messages: list[dict[str, Any]] = []
        request_delivered = False

        async def receive() -> dict[str, Any]:
            nonlocal request_delivered
            if not request_delivered:
                request_delivered = True
                return request_body
            await response_started.wait()
            return {"type": "http.disconnect"}

        async def send(message: dict[str, Any]) -> None:
            messages.append(message)
            if message.get("type") == "http.response.body" and message.get("more_body"):
                response_started.set()

        scope = {
            "type": "http",
            "asgi": {"version": "3.0", "spec_version": "2.3"},
            "http_version": "1.1",
            "method": "GET",
            "scheme": "http",
            "path": f"/etl/v1/runs/{run_id}/events",
            "raw_path": f"/etl/v1/runs/{run_id}/events".encode(),
            "query_string": b"follow=true",
            "root_path": "",
            "headers": [(b"x-principal", b"alice")],
            "client": ("test", 50000),
            "server": ("test", 80),
            "state": {},
        }
        await app(scope, receive, send)
        return messages

    messages = asyncio.run(exercise())
    assert any(
        message.get("type") == "http.response.start" and message.get("status") == 200
        for message in messages
    )
    assert app.state.security_teardowns == ["alice"]
