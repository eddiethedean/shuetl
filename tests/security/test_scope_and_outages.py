"""Scope isolation, bounded visibility, and fail-closed provider behavior."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pytest
from etlantic.control_plane import (
    AuthzDecision,
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
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from shuetl import HostIdentityAdapter, ShuETL


def _context(principal: Principal, tenant: str, workspace: str) -> ControlPlaneContext:
    return ControlPlaneContext(
        principal=principal,
        tenant=TenantRef(tenant_id=tenant),
        workspace=WorkspaceRef(tenant_id=tenant, workspace_id=workspace),
        environment=EnvironmentRef(name="test"),
        security_domain=SecurityDomain(domain_id="default"),
    )


def _api_and_contexts(
    *,
    durable_work: Any = None,
) -> tuple[ETLanticAPI, dict[str, ControlPlaneContext], MemoryAuthorizer]:
    contexts = {
        "alice": _context(
            Principal("alice", issuer="https://issuer.example"),
            "tenant-a",
            "workspace-a",
        ),
        "bob": _context(
            Principal("bob", issuer="https://issuer.example"), "tenant-b", "workspace-b"
        ),
        "carol": _context(
            Principal("carol", issuer="https://issuer.example"),
            "tenant-a",
            "workspace-c",
        ),
    }
    authorizer = MemoryAuthorizer()

    def principal_dependency(request: Request) -> Principal:
        user = request.headers.get("X-Principal", "alice")
        try:
            return contexts[user].principal
        except KeyError:
            raise ValueError("synthetic principal is not authenticated") from None

    def context_factory(principal: Principal, _request: Request) -> ControlPlaneContext:
        return contexts[principal.subject]

    adapter = HostIdentityAdapter.create(
        principal_dependency=principal_dependency,
        context_factory=context_factory,
    )
    api = ETLanticAPI(
        authorizer=authorizer,
        definitions=MemoryDefinitionRepository(),
        submissions=MemorySubmissionStore(),
        events=MemoryEventStore(),
        context_factory=adapter.context_factory,
        principal_dependency=adapter.principal_dependency,
        profile="development",
        durable_work=durable_work,
    )
    return api, contexts, authorizer


@pytest.fixture(params=["direct", "mounted"])
def scoped_app(request: pytest.FixtureRequest):
    api, contexts, authorizer = _api_and_contexts()
    visible = {"name": "visible-document", "marker": "visible-content"}
    hidden = {"name": "hidden-document", "marker": "hidden-content-sentinel"}
    foreign = {"name": "foreign-document", "marker": "foreign-content-sentinel"}
    api.definitions.put(contexts["alice"], "visible", visible)
    api.definitions.put(contexts["alice"], "hidden", hidden)
    api.definitions.put(contexts["bob"], "private", foreign)
    api.submissions.accept(
        contexts["bob"],
        idempotency_key="foreign-run-idempotency",
        payload={"definition_id": "private"},
        resource_id="foreign-run",
    )
    api.submissions.accept(
        contexts["alice"],
        idempotency_key="same-tenant-foreign-workspace-run",
        payload={"definition_id": "visible"},
        resource_id="same-tenant-private-run",
    )
    authorizer.grant(contexts["alice"], "definition.list")
    authorizer.grant(contexts["alice"], "definition.read")
    authorizer.grant(contexts["carol"], "definition.list")
    authorizer.grant(contexts["carol"], "definition.read")
    authorizer.forbidden_resources.update(
        {
            ("tenant-a", "workspace-a", "definition.list", "definition:hidden"),
            ("tenant-a", "workspace-a", "definition.read", "definition:hidden"),
        }
    )
    if request.param == "direct":
        app = ShuETL(api=api).create_app()
        prefix = ""
    else:
        app = FastAPI()
        ShuETL(api=api).mount(app, prefix="/etl")
        prefix = "/etl"
    return app, api, contexts, authorizer, prefix


def test_collection_and_item_denials_do_not_disclose_cross_scope_data(
    scoped_app,
) -> None:
    app, _api, _contexts, _authorizer, prefix = scoped_app
    with TestClient(app) as client:
        visible = client.get(
            f"{prefix}/v1/definitions", headers={"X-Principal": "alice"}
        )
        denied_item = client.get(
            f"{prefix}/v1/definitions/hidden", headers={"X-Principal": "alice"}
        )
        foreign_item = client.get(
            f"{prefix}/v1/definitions/private", headers={"X-Principal": "alice"}
        )
        foreign_collection = client.get(
            f"{prefix}/v1/definitions", headers={"X-Principal": "bob"}
        )
        foreign_workspace_item = client.get(
            f"{prefix}/v1/definitions/visible", headers={"X-Principal": "carol"}
        )
        foreign_workspace_run = client.get(
            f"{prefix}/v1/runs/same-tenant-private-run/report",
            headers={"X-Principal": "carol"},
        )

    assert visible.status_code == 200
    assert visible.json() == {"items": [{"definition_id": "visible"}]}
    assert denied_item.status_code == 403
    assert foreign_item.status_code == 404
    assert foreign_collection.status_code == 404
    assert foreign_workspace_item.status_code == 404
    assert foreign_workspace_run.status_code == 404
    for response in (
        visible,
        denied_item,
        foreign_item,
        foreign_collection,
        foreign_workspace_item,
        foreign_workspace_run,
    ):
        assert "hidden-content-sentinel" not in response.text
        assert "foreign-content-sentinel" not in response.text


@pytest.mark.parametrize(
    ("path", "principal"),
    [
        ("/v1/registry/workspaces/foreign-workspace", "alice"),
        ("/v1/schedules/foreign-schedule", "alice"),
        ("/v1/runs/foreign-run/report", "alice"),
        ("/v1/runs/foreign-run/lineage", "alice"),
        ("/v1/runs/foreign-run/artifacts", "alice"),
    ],
)
def test_protected_optional_reads_deny_before_unavailable_provider_lookup(
    scoped_app, path: str, principal: str
) -> None:
    app, _api, _contexts, _authorizer, prefix = scoped_app
    with TestClient(app) as client:
        response = client.get(f"{prefix}{path}", headers={"X-Principal": principal})
    assert response.status_code == 404
    assert "sentinel" not in response.text
    assert "not configured" not in response.text.lower()


@dataclass(frozen=True)
class _Outbox:
    outbox_id: str

    def to_dict(self) -> dict[str, str]:
        return {"outbox_id": self.outbox_id}


class _OutboxProbe:
    def __init__(self, records: list[_Outbox]) -> None:
        self.records = records
        self.limits: list[int] = []

    def pending_outbox(self, _ctx: ControlPlaneContext, *, limit: int) -> list[_Outbox]:
        self.limits.append(limit)
        return self.records[:limit]


def test_limited_lists_expand_until_visible_items_fill_existing_limit() -> None:
    durable = _OutboxProbe([_Outbox(f"item-{index:03d}") for index in range(102)])
    api, contexts, authorizer = _api_and_contexts(durable_work=durable)
    context = contexts["alice"]
    authorizer.grant(context, "durable.outbox.read")
    authorizer.forbidden_resources.update(
        (
            context.tenant.tenant_id,
            context.workspace.workspace_id,
            "durable.outbox.read",
            f"durable:outbox:item-{index:03d}",
        )
        for index in range(100)
    )
    app = ShuETL(api=api).create_app()

    with TestClient(app) as client:
        response = client.get("/v1/durable/outbox?limit=2")

    assert response.status_code == 200
    assert [row["outbox_id"] for row in response.json()] == ["item-100", "item-101"]
    assert durable.limits == [100, 200]


@pytest.mark.parametrize("prefix", ["", "/etl"])
def test_acceptance_receipt_metadata_authorizes_before_run_lookup(prefix: str) -> None:
    context = _context(
        Principal("artifact-reader", issuer="https://issuer.example"),
        "artifact-tenant",
        "artifact-workspace",
    )
    call_order: list[tuple[str, str]] = []

    class ArtifactAuthorizer:
        def authorize(
            self, ctx: ControlPlaneContext, action: str, resource: str
        ) -> AuthzDecision:
            del ctx, action
            call_order.append(("authorize", resource))
            if resource == "artifact:run-with-receipt:accept-receipt":
                return AuthzDecision(
                    allowed=False,
                    reason="receipt metadata is not visible",
                    disclosure="forbidden",
                )
            return AuthzDecision(allowed=True, reason="synthetic test grant")

    inner = MemorySubmissionStore()
    inner.accept(
        context,
        idempotency_key="receipt-metadata-test",
        payload={"definition_id": "receipt-definition"},
        resource_id="run-with-receipt",
    )

    class SubmissionProbe:
        def __getattr__(self, name: str) -> Any:
            target = getattr(inner, name)
            if name != "get_run":
                return target

            def get_run(*args: Any, **kwargs: Any) -> Any:
                call_order.append(("lookup", "run"))
                return target(*args, **kwargs)

            return get_run

    principal = context.principal
    adapter = HostIdentityAdapter.create(
        principal_dependency=lambda: principal,
        context_factory=lambda _principal, _request: context,
    )
    api = ETLanticAPI(
        authorizer=ArtifactAuthorizer(),
        definitions=MemoryDefinitionRepository(),
        submissions=SubmissionProbe(),  # type: ignore[arg-type]
        events=MemoryEventStore(),
        context_factory=adapter.context_factory,
        principal_dependency=adapter.principal_dependency,
        profile="development",
    )
    integration = ShuETL(api=api)
    if prefix:
        app = FastAPI()
        integration.mount(app, prefix=prefix)
        path = f"{prefix}/v1/runs/run-with-receipt/artifacts"
    else:
        app = integration.create_app()
        path = "/v1/runs/run-with-receipt/artifacts"

    with TestClient(app) as client:
        response = client.get(path)

    assert response.status_code == 200
    assert response.json() == {"run_id": "run-with-receipt", "items": []}
    assert call_order == [
        ("authorize", "run:run-with-receipt"),
        ("lookup", "run"),
        ("authorize", "artifact:run-with-receipt:accept-receipt"),
    ]


def test_item_authorizer_outage_fails_the_whole_list_without_partial_results() -> None:
    class FailingAuthorizer:
        def authorize(
            self,
            ctx: ControlPlaneContext,
            action: str,
            resource: str,
        ) -> AuthzDecision:
            del ctx, action
            if resource == "definition:*":
                return AuthzDecision(allowed=True, reason="collection grant")
            raise RuntimeError("policy-outage-sentinel")

    api, contexts, _authorizer = _api_and_contexts(durable_work=object())
    context = contexts["alice"]
    api.authorizer = FailingAuthorizer()
    api.definitions.put(context, "visible", {"name": "visible"})
    api.definitions.put(context, "other", {"name": "other"})
    app = ShuETL(api=api).create_app()

    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.get("/v1/definitions")

    assert response.status_code == 503
    assert "policy-outage-sentinel" not in response.text
    assert "visible" not in response.text
    assert "other" not in response.text


def test_required_provider_failure_is_sanitized_without_partial_list() -> None:
    api, contexts, authorizer = _api_and_contexts()
    context = contexts["alice"]
    authorizer.grant(context, "definition.list")
    api.definitions.put(context, "visible", {"name": "visible-sentinel"})

    class FailingDefinitions:
        def list(self, _ctx: ControlPlaneContext) -> list[str]:
            raise RuntimeError("provider-outage-sentinel")

    api.definitions = FailingDefinitions()  # type: ignore[assignment]
    app = ShuETL(api=api).create_app()
    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.get("/v1/definitions")

    assert response.status_code >= 500
    assert "provider-outage-sentinel" not in response.text
    assert "visible-sentinel" not in response.text
