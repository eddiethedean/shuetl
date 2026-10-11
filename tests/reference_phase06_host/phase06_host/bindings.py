"""Host authentication and resource bridge used by the CLI qualification."""

from __future__ import annotations

import asyncio
import json
import os
import sys
import time
from pathlib import Path
from typing import Any

from etlantic.control_plane import (
    ControlPlaneContext,
    EnvironmentRef,
    MemoryAuthorizer,
    Principal,
    SecurityDomain,
    TenantRef,
    WorkspaceRef,
)
from etlantic.profile import Profile
from etlantic.registry import BindingDescriptor, PlanningContext
from sqlalchemy import create_engine, event
from sqlalchemy.engine import make_url

from shuetl import GatewayBindings, RuntimeBindings
from shuetl.settings import ShuETLSettings

AUTHORIZATIONS = (
    "definition.write",
    "run.submit",
    "run.read",
    "run.report",
    "input.read",
    "schedule.write",
    "schedule.read",
    "action.execute",
)
_cleanup_observer_installed = False


def _record_lifecycle(root: Path, event_name: str) -> None:
    token = os.environ.get("PHASE06_PROCESS_TOKEN")
    identity = f"{token}-{os.getpid()}" if token else str(os.getpid())
    path = root / f"lifecycle-{identity}.jsonl"
    with path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps({"event": event_name}) + "\n")


def _context(settings: ShuETLSettings) -> ControlPlaneContext:
    return ControlPlaneContext(
        principal=Principal("phase06-service", issuer="reference-host", kind="service"),
        tenant=TenantRef(settings.tenant_id or "tenant-a"),
        workspace=WorkspaceRef(
            settings.tenant_id or "tenant-a", settings.workspace_id or "workspace-a"
        ),
        environment=EnvironmentRef(settings.environment or "test"),
        security_domain=SecurityDomain(settings.security_domain or "domain-a"),
        resource_owner_id="phase06-service",
    )


def create(settings: ShuETLSettings) -> GatewayBindings | RuntimeBindings:
    """Return process-local bindings for an isolated disposable store."""
    global _cleanup_observer_installed
    root = Path(os.environ["PHASE06_ROOT"]).resolve()
    if not _cleanup_observer_installed:
        import shuetl.backend as runtime_backend

        create_backend = runtime_backend.create_managed_backend

        def observe_backend_creation(*args: Any, **kwargs: Any) -> Any:
            backend = create_backend(*args, **kwargs)
            event.listen(
                backend.engine,
                "engine_disposed",
                lambda _engine: _record_lifecycle(root, "backend.engine_disposed"),
            )
            # Qualification-only barrier around an unchanged public provider call.
            # Arm only after startup; a queued job is required for worker barriers.
            role = (
                f"worker-{settings.worker_kind}"
                if settings.role == "worker"
                else settings.role
            )
            selection = {
                "scheduler": (backend.schedule_store, "acquire_leader_lease"),
                "worker-runs": (backend.durable_work, "acquire_lease"),
                "worker-actions": (backend.durable_work, "claim_action_job"),
            }.get(role)
            if selection:
                target, method = selection
                original = getattr(target, method)

                def observe_call(*call_args: Any, **call_kwargs: Any) -> Any:
                    result = original(*call_args, **call_kwargs)
                    arm = root / f"arm-{role}"
                    if result is not None and arm.exists():
                        arm.unlink()
                        (root / f"reached-{role}").write_text(method, encoding="utf-8")
                        release = root / f"release-{role}"
                        deadline = time.monotonic() + 90
                        while not release.exists():
                            if time.monotonic() > deadline:
                                raise TimeoutError("qualification barrier not released")
                            time.sleep(0.02)
                        release.unlink()
                    return result

                setattr(target, method, observe_call)
            return backend

        runtime_backend.create_managed_backend = observe_backend_creation
        _cleanup_observer_installed = True

    context = _context(settings)
    authorizer = MemoryAuthorizer()
    for action in AUTHORIZATIONS:
        authorizer.grant(context, action)
    for action in (
        "connector.test",
        "connector.schema.inspect",
        "connector.preflight",
        "connector.action.read",
    ):
        authorizer.grant(context, action)
    resource_engines: dict[str, Any] = {}

    def close_resources() -> None:
        for engine in resource_engines.values():
            engine.dispose()
        if resource_engines:
            token = os.environ.get("PHASE06_PROCESS_TOKEN", str(os.getpid()))
            (root / f"resource-cleanup-{token}.json").write_text(
                json.dumps({"engines_disposed": len(resource_engines)})
            )
        _record_lifecycle(root, "bindings.close")

    action_handlers = {}
    if settings.role == "worker" and settings.worker_kind == "actions":
        from etlantic_sql import create_action_handlers

        def resolve_engine(ctx, connection_id, *, timeout_seconds):
            if ctx != context or not 0 < timeout_seconds <= 300:
                raise ValueError("reference resource authority mismatch")
            if connection_id == "slow-connection":
                time.sleep(min(timeout_seconds + 0.2, 3))
                raise TimeoutError("reference resolver deadline")
            if (
                connection_id not in {"saved-connection", "unavailable-connection"}
                or (root / "revoke-connection").exists()
            ):
                raise ValueError("reference resource unavailable")
            version_path = root / "connection-version"
            version = version_path.read_text().strip() if version_path.exists() else "1"
            url = os.environ["ETLANTIC_SQL_URL"]
            if connection_id == "unavailable-connection":
                url = (
                    make_url(url)
                    .set(
                        host="127.0.0.1",
                        port=int((root / "unavailable-port").read_text()),
                    )
                    .render_as_string(hide_password=False)
                )
                version = "unavailable"
            token = os.environ.get("PHASE06_PROCESS_TOKEN", str(os.getpid()))
            with (root / f"resource-calls-{token}.jsonl").open("a") as stream:
                stream.write(
                    json.dumps(
                        {
                            "connection_id": connection_id,
                            "version": version,
                            "pid": os.getpid(),
                            "timeout_seconds": timeout_seconds,
                            "authority_matches": True,
                        }
                    )
                    + "\n"
                )
            if version not in resource_engines:
                resource_engines[version] = create_engine(
                    url,
                    connect_args={
                        "connect_timeout": 2,
                        "options": "-c search_path=sink",
                    },
                )
            return resource_engines[version]

        action_handlers = create_action_handlers(resolve_engine)
    profile = Profile(
        name="phase06-reference",
        security_mode="production",
        plugin_allowlist={
            "etlantic": "0.57.2",
            "etlantic-local": "0.50.0",
            "etlantic-sql": "0.57.2",
            "postgresql": "0.57.2",
            "local-files": "0.57.2",
        },
        safe_io={"approved_roots": [str(root / "landing")]},
    )

    def planning_context_factory(
        _context: ControlPlaneContext, effective_profile: Profile
    ) -> PlanningContext:
        planning = PlanningContext.create(profile=effective_profile)
        planning.registry.register_binding(
            BindingDescriptor(
                binding="source",
                provider="local-files",
                kind="source",
                config={
                    "format": "csv",
                    "mode": "snapshot",
                    "root": ".",
                    "root_ref": "gate0-input",
                    "glob": "*.csv",
                },
            )
        )
        planning.registry.register_binding(
            BindingDescriptor(
                binding="sink",
                provider="postgresql",
                kind="sink",
                location="target",
                config={
                    "schema": "sink",
                    "mode": "append",
                    "effect_table": "sink.effects",
                },
            )
        )
        return planning

    if settings.role == "gateway":
        from shuetl import HostIdentityAdapter

        identity = HostIdentityAdapter.create(
            principal_dependency=lambda: context.principal,
            context_factory=lambda _principal, _request: context,
        )

        def qualification_route(app: Any) -> None:
            @app.get("/qualification/active-request", include_in_schema=False)
            async def active_request():
                (root / "reached-gateway").touch()
                deadline = time.monotonic() + 90
                while not (root / "release-gateway").exists():
                    if time.monotonic() > deadline:
                        raise TimeoutError("qualification request not released")
                    await asyncio.sleep(0.02)
                return {"completed": True}

        bindings = GatewayBindings(
            authorizer=authorizer,
            profile=profile,
            planning_context_factory=planning_context_factory,
            identity_adapter=identity,
            asgi_hook=qualification_route,
            artifact_root=str(root / "artifacts"),
            close=close_resources,
        )
    else:
        bindings = RuntimeBindings(
            authorizer=authorizer,
            profile=profile,
            planning_context_factory=planning_context_factory,
            context=context,
            artifact_root=str(root / "artifacts"),
            action_handlers=action_handlers,
            close=close_resources,
        )
    role_name = (
        f"worker-{settings.worker_kind}" if settings.role == "worker" else settings.role
    )
    imports = {
        "role": role_name,
        "pid": os.getpid(),
        "fastapi_imported": "fastapi" in sys.modules,
        "etlantic_fastapi_imported": "etlantic_fastapi" in sys.modules,
    }
    (root / f"imports-{role_name}.json").write_text(
        json.dumps(imports, sort_keys=True) + "\n", encoding="utf-8"
    )
    if settings.role != "gateway" and (
        imports["fastapi_imported"] or imports["etlantic_fastapi_imported"]
    ):
        raise RuntimeError("runtime bindings imported the HTTP stack")
    return bindings
