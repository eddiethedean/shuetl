"""Host authentication and resource bridge used by the CLI qualification."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

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


def _context(settings: ShuETLSettings) -> ControlPlaneContext:
    return ControlPlaneContext(
        principal=Principal("phase06-service", issuer="reference-host", kind="service"),
        tenant=TenantRef(settings.tenant_id or "tenant-a"),
        workspace=WorkspaceRef(
            settings.tenant_id or "tenant-a", settings.workspace_id or "workspace-a"
        ),
        environment=EnvironmentRef(settings.environment or "test"),
        security_domain=SecurityDomain(settings.security_domain or "domain-a"),
    )


def create(settings: ShuETLSettings) -> GatewayBindings | RuntimeBindings:
    """Return process-local bindings for an isolated disposable store."""
    root = Path(os.environ["PHASE06_ROOT"]).resolve()
    context = _context(settings)
    authorizer = MemoryAuthorizer()
    for action in AUTHORIZATIONS:
        authorizer.grant(context, action)
    profile = Profile(
        name="phase06-reference",
        security_mode="production",
        plugin_allowlist={
            "etlantic": "0.57.0",
            "etlantic-local": "0.50.0",
            "etlantic-sql": "0.57.0",
            "postgresql": "0.57.0",
            "local-files": "0.57.0",
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
        bindings = GatewayBindings(
            authorizer=authorizer,
            profile=profile,
            planning_context_factory=planning_context_factory,
            identity_adapter=identity,
        )
    else:
        bindings = RuntimeBindings(
            authorizer=authorizer,
            profile=profile,
            planning_context_factory=planning_context_factory,
            context=context,
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
