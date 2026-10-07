# ADR-0014: Role-Separated Managed Runtime on ETLantic 0.56.0

- Status: Accepted for implementation; PostgreSQL role qualification remains open.
- Date: 2026-10-07.
- Governing contract: [Phase 0.6](../plans/PHASE_0_6_EXECUTION.md).

## Context

The published 0.56 managed backend supplies shared services and a real worker.
Its scheduler requires public-service wiring, its worker has no readiness
method, and its constructor's version inspector issues a
`CREATE TABLE IF NOT EXISTS` for the schema-version table. The managed firing,
submission and link operations span recoverable commit boundaries. ADR-0013
requires the standard host path to supply specifications and identity/resource
integration without building ETL service graphs. Source-level composition is
implemented; installed-wheel PostgreSQL 18.6 role and privilege behavior has
not yet been qualified.

## Decision

### Standard composition

Use exact 0.56.0 core/FastAPI/SQLModel packages and independently installed
0.56.0 SQL/Foundry packages when enabled. ShuETL constructs
`etlantic_fastapi.ManagedBackendConfig` and `create_managed_backend` after
read-only preflight. Each process owns its backend and engine, with the same
configured database, store ID, execution profile, tenant and workspace.
Dispose the temporary preflight engine before constructing the backend.

The standard CLI is `shuetl serve --role ROLE --factory package.module:callable`.
`ROLE` must match required `SHUETL_ROLE`. The explicitly trusted factory has
the signature `factory(settings: ShuETLSettings) -> HostRuntimeBindings`.
`HostRuntimeBindings` is a frozen ShuETL composition object, not an ETL domain
model. Its implemented Python fields are:

```python
from dataclasses import field


@dataclass(frozen=True, slots=True)
class HostRuntimeBindings:
    authorizer: Authorizer
    identity_adapter: HostIdentityAdapter | None = None
    service_context: ControlPlaneContext | None = None
    planning_context_factory: Callable[[Any, Any], PlanningContext] | None = None
    action_handlers: Mapping[str, ActionHandler] = field(default_factory=dict)
    secret_alias_authorizer: SecretAliasAuthorizer | None = None
    gateway_app_factory: Callable[[ShuETL], FastAPI] | None = None
    close: Callable[[], None] | None = None
```

| Binding | Meaning and role constraint |
| --- | --- |
| `authorizer` | Public ETLantic authorizer; required in all roles. |
| `identity_adapter` | Existing `HostIdentityAdapter`; required for gateway request identity, absent in runtime bindings. |
| `service_context` | Upstream `ControlPlaneContext` with a trusted service/workload `Principal` and matching tenant/workspace; required for scheduler/worker, absent in gateway bindings. |
| `planning_context_factory` | Optional upstream resource/planning bridge. May supply authorized resource references and metadata, never row transforms or a preparation coordinator. |
| `gateway_app_factory` | Optional trusted hook accepting the constructed ShuETL integration and returning a host ASGI app; gateway-only and not invoked or imported by runtime bindings. Without it, ShuETL builds the dedicated guarded app. |
| `close` | Optional cleanup of host-owned binding resources, invoked once after backend cleanup. No provider engine or execution loop is owned by these bindings. |

For gateway requests, ShuETL passes the adapter's guarded context and principal
dependencies to the managed constructor. Scheduler and worker API dependencies
reject HTTP identities; those roles call public upstream services with the
explicit service context. Backend profile and provider plugins are selected by deployment configuration.
Execution/resource implementations belong to independent packages. No standard
binding accepts an alternate scheduler, worker runner, store or row callback.
Preserve existing explicit facade/bundle injection as an advanced interface.
The CLI accepts one trusted module reference per process; the host can use
role-specific modules so runtime startup does not import a host authentication
stack.

### Role wiring

The gateway composes the existing identity guards and mounts the upstream API;
it never creates an execution host. Scheduler construction uses the backend's
schedule and durable stores, execution profile and unique process owner, with
`run_submitter=backend.api.managed_service.submit_scheduled_run` passed as a
bound method. This preserves discovery of occurrence preparation and recovery.
No lambda, fingerprint calculation or firing repair code belongs in ShuETL.

For gateway construction, the identity adapter's guarded context/principal
pair is authoritative; reject a supplied context factory that bypasses or
disagrees with that pair. Runtime contexts have no gateway principal dependency.

The worker uses `backend.create_execution_host(owner_id=..., ttl_seconds=...)`.
One supervisor-owned execution thread calls `tick(service_context, limit=1)`;
the upstream execution host owns lease heartbeats, cancellation and fencing.
Separate processes establish concurrency. Bind service scope explicitly and
require schedule workload identity to match the qualified upstream context
contract. Principals are stable role identities; lease owners are unique per
process start, including on the same machine. Owner IDs are not credentials.

`shuetl serve --role worker --kind actions` selects dedicated upstream
`backend.create_action_execution_host(worker_id=...)` processes. Default
worker kind is `runs`; the command kind must match configured `worker_kind`.
Action workers call public `tick(ctx, limit=1)` with independently packaged
provider handlers selected by the approved backend profile. They share the
same scope, resource and probe rules, but do not instantiate the run host.
Their supervisor stops dispatch and waits for active action ticks on signals;
no nonexistent upstream action-host `drain()` method is assumed. Handler
loading uses public package APIs fixed in W02, never host row/action callbacks.

### Configuration contract

Keep constructor-over-environment precedence and required role/profile/provider
settings. `identity=host` continues to describe gateway request identity;
runtime identity comes only from `service_context`, never demo mode or a token
copied from a request. Add the following planned preview configuration:

| Setting | Default or requirement |
| --- | --- |
| `store_id` | Required explicit value shared by all roles. |
| `tenant_id`, `workspace_id` | Required explicit scope matched by guarded contexts. |
| `execution_profile` | Required installed, operator-approved upstream profile; preserve full qualified settings. |
| `worker_kind` | `runs` by default; `actions` selects a dedicated provider-action worker, valid only for worker roles. |
| `owner_id` | Generated unique role-prefixed value per start; any operator override must still be unique. |
| `runtime_poll_interval_seconds` / `SHUETL_RUNTIME_POLL_INTERVAL_SECONDS` | 1 second; finite range 0.1–30. Controls supervision pacing only. |
| `lease_ttl_seconds` | 30 seconds; integer at least 3 and poll interval less than TTL/3. Passed upstream; this does not establish a maximum tick duration. |
| `probe_port` | Required for runtime roles; loopback-only, distinct per process. Gateway keeps upstream HTTP probes. |
| `probe_refresh_seconds` | 1 second; positive, independent of the synchronous execution tick. |
| `probe_stale_after_seconds` | 5 seconds; greater than refresh interval. Stale provider evidence fails readiness. |
| `shutdown_grace_seconds` | 30 seconds; positive supervisor grace budget, not a guarantee that all effects can be interrupted. |
| `artifact_root` / resource volume | Explicit shared location when file/artifact capabilities are advertised; identical resource identity across processes. Paths are absent from public diagnostics. |

Probe settings are required in `postgresql-preview`; factory references and
settings are validated before database access or trusted module loading. A
preview requires PostgreSQL, host identity, store/scope/profile identifiers,
and a loopback probe port. `postgresql-pilot` remains gateway-only. A
`worker_kind` is valid only for a worker, where it defaults to `runs`.

### Lifecycle and probes

Use process states `starting`, `running`, `draining`, `stopped` and `failed`.
These describe supervision, not an ETL run state. Loopback `/live` and `/ready`
return only role/state/reason codes. Provider checks use read-only queries and
do not renew leases, execute ticks or perform authentication. A standby
scheduler is healthy without owning leadership; `SchedulerService.ready()`
alone cannot prove database health. A long-running worker remains live when
its supervisor responds and provider checks remain fresh.

Signals fail readiness, stop dispatch and invoke upstream drain. Complete an
already dispatched tick before closing the backend and bindings once. Drain
does not retract an in-flight scheduler scan or lease acquisition. If grace
expires, retain a draining/non-ready process for supervisor termination and
record an incomplete drain. Never close the engine under its active tick or
publish success on behalf of the terminated runtime.

### Schema and transition

The reference deploys a fresh 0.56 store at head
`014_cp1_complete_principal_idempotency_0_56`; retain the 0.5 application/store
separately for rollback. Runtime connections cannot own provider tables,
inherit migration privileges or create schema objects. The sole construction
exception is upstream `CREATE TABLE IF NOT EXISTS` for the existing version
table, after preflight. Prove zero schema changes under real runtime grants.
Readiness/doctor never invoke the mutating version inspector.

This deliberately qualifies the Phase 0.6 construction exception to ADR-0010;
its health and explicit-migration rules remain applicable. No in-place durable
conversion or rolling upgrade is claimed. Rollback requires disabling the new
deployment's admission/scheduling, reconciling external effects and then
enabling the retained old deployment. Pending work is never automatically
replayed across stores.

## Consequences

ShuETL owns process lifecycle and provider health checks; ETLantic remains the
authority for schedule, durable admission, execution, leases, reports, and
recovery. Operators must supply a trusted host factory, restricted database
role, fresh 0.56 store, shared artifact resources where used, and separate
processes. The reference deployment remains a preview until its live role and
failure evidence is recorded.

## Alternatives

- Continue using ETLantic's file-backed CLI stores; rejected because the
  reference requires one PostgreSQL-backed graph shared by gateway, scheduler,
  and worker processes.
- Add ShuETL-owned scheduler or execution semantics; rejected because those
  duplicate upstream state, lease, recovery, and report behavior.
- Use the released 0.5 pilot store or automatically upgrade it; rejected
  because 0.56 requires an isolated fresh store and no converter is qualified.

## Validation

The implementation now records these signatures and role mappings. The
installed-wheel PostgreSQL 18.6 Gate 0 fixture must support them before this
decision is qualified. AC-002, AC-007–010, AC-025–027 and AC-032/033 verify this
decision. The remaining Phase 0.6 criteria establish the release claim. See the
[verification plan](../plans/PHASE_0_6_VERIFICATION.md) and the current
[`contracts`](../evidence/0.6/contracts.md) and
[`ownership`](../evidence/0.6/ownership.md) records.

## Revisit trigger

Revisit if these public APIs cannot support the isolated graph, bound-method
recovery, actual runtime grants or safe lifecycle. Missing semantics stay
upstream defects; they do not authorize a ShuETL execution or recovery engine.
