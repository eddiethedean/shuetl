"""Typed host-owned identity/resource bindings for managed role startup."""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Mapping
from dataclasses import dataclass, field
from typing import Any

from etlantic.control_plane import Authorizer, ControlPlaneContext
from etlantic.profile import Profile
from etlantic.registry import PlanningContext

CloseCallback = Callable[[], None]
PlanningContextFactory = Callable[[ControlPlaneContext, Profile], PlanningContext]


def _noop() -> None:
    return None


@dataclass(frozen=True, slots=True)
class HostBindings:
    """Trusted, host-created non-HTTP bindings shared by managed roles."""

    authorizer: Authorizer
    profile: Profile
    planning_context_factory: PlanningContextFactory
    # Pass provider-owned controls through to ETLantic without interpreting
    # their policy or governance semantics in ShuETL.
    policy: Any = field(default=None, repr=False, compare=False, kw_only=True)
    approvals: Any = field(default=None, repr=False, compare=False, kw_only=True)
    quotas: Any = field(default=None, repr=False, compare=False, kw_only=True)
    audit: Any = field(default=None, repr=False, compare=False, kw_only=True)
    attestations: Any = field(default=None, repr=False, compare=False, kw_only=True)
    require_attestations: bool = field(default=False, kw_only=True)
    schedule_parameter_resolver: Any = field(
        default=None, repr=False, compare=False, kw_only=True
    )
    artifact_root: str | None = field(default=None, kw_only=True)
    close: CloseCallback = field(default=_noop, repr=False, compare=False, kw_only=True)


@dataclass(frozen=True, slots=True)
class GatewayBindings(HostBindings):
    """Gateway identity remains owned by the authenticated host."""

    identity_adapter: Any
    asgi_hook: Callable[[Any], None] | None = field(
        default=None, repr=False, compare=False
    )


@dataclass(frozen=True, slots=True)
class RuntimeBindings(HostBindings):
    """Workers receive a fixed canonical service/workload context."""

    context: ControlPlaneContext
    # Match the public provider ActionHandler shape without importing an
    # optional SQL provider or execution host into the binding module.
    action_handlers: Mapping[
        str, Callable[[Any, Mapping[str, Any]], Awaitable[Mapping[str, Any]]]
    ] = field(default_factory=dict, repr=False, compare=False, kw_only=True)
