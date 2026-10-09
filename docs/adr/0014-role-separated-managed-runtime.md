# ADR-0014: Role-Separated Managed Runtime Composition

- Status: Accepted implementation contract; qualification remains open.
- Revised: 2026-10-09.
- Governing contract: [Phase 0.6](../plans/PHASE_0_6_EXECUTION.md).

2026-10-09: [coverage acceptance](../evidence/0.6/coverage-acceptance.md) closes
U01–U05, and [installed-artifact PostgreSQL Gate 0](../evidence/0.6/README.md)
qualifies upstream role composition. W02 now freezes the ShuETL binding and CLI
surface below. The reference qualification package remains a test fixture;
final-wheel, lifecycle, failure-matrix and transition qualification remain open.

## Context

ShuETL deploys an upstream-complete backend through isolated gateway, scheduler,
run-worker and action-worker processes. The earlier 0.56.0 proposal relied on a
FastAPI-owned backend, bound-method recovery discovery and a DDL exception.
ADR-0015 replaces those choices with Gate U contracts. Version 0.56.2 fixes the
version-reader DDL defect; 0.57.0 publishes the remaining requested surfaces.
Acceptance is tracked in [the dependency register](../plans/ETLANTIC_0_56_DEPENDENCIES.md).

## Decision

### Standard composition and ownership

Select exact published upstream packages after Gate U. ShuETL configures the
transport-independent backend and its complete role factories. Upstream owns
service/store assembly and runtime semantics; a provider owns SQLModel engine,
schema and store requirements. `etlantic-fastapi` adapts the constructed service
graph for the gateway. Runtime roles require neither the adapter nor HTTP inputs.

ShuETL retains CLI/settings, host adapters, process/probe supervision, ownership
of constructed handles and deployment evidence. No standard binding supplies a
store, scheduler, runner, row callback or preparation coordinator.
Independent backend packages supply canonical plugins/handlers; runtime bindings
may reference their asynchronous action handlers for upstream composition.
Preserve advanced caller-owned facade/bundle interfaces.

`shuetl serve --role ROLE --factory package.module:callable` loads explicitly
trusted integration code after settings/import/version validation. `ROLE` must
match required `SHUETL_ROLE`. The factory receives validated settings and returns
a role-specific frozen composition object. `HostBindings`, `GatewayBindings` and
`RuntimeBindings` are public frozen dataclasses exported from `shuetl`.
`HostBindings` accepts the canonical authorizer, `Profile`, a planning-context
factory taking `(ControlPlaneContext, Profile)`, and an optional keyword-only
zero-argument cleanup callback. `GatewayBindings` adds a `HostIdentityAdapter`
and an optional ASGI hook. `RuntimeBindings` adds one canonical
`ControlPlaneContext` and an optional keyword-only `action_handlers` mapping,
forwarded to upstream backend configuration without implementing action behavior.
The trusted factory has signature
`factory(settings) -> HostBindings`; its `module:callable` path must match
`SHUETL_BINDINGS_FACTORY`.

| Binding | Gateway | Scheduler / run worker / action worker |
| --- | --- | --- |
| Authorizer | Canonical upstream contract | Canonical upstream contract where required by the role/backend |
| Identity | Existing `HostIdentityAdapter`; its guarded pair is authoritative | Trusted canonical scoped service/workload context; no demo/request credentials |
| HTTP context/principal dependency | Only the adapter's guarded pair | Absent; constructor must not require dummy HTTP callables |
| Resource/planning bridge | Canonical metadata/reference integration; no runtime secret resolution | Canonical authorized bridges appropriate to the role; no ETL callbacks |
| Host ASGI hook | Optional, receives constructed integration | Absent and not loaded |
| Binding cleanup | Optional cleanup for host-owned integration resources | Same ownership rule; no ownership of backend engine or ETL loop |

Factories can live in separate installed modules to keep runtime startup free
of the host authentication stack. Canonical context validity and authorization
are checked upstream; ShuETL additionally validates the deployment scope.

### Role construction

The gateway adapts the upstream backend into HTTP and never constructs execution
hosts. Headless consumers invoke the same authorized upstream service commands
with explicit context and no synthetic request or direct store operations.

The scheduler comes from an upstream factory that supplies its schedule store
and preparation/submission/recovery collaborators on the correct store identity.
ShuETL supplies profile, scope and a unique owner. No callback `__self__` discovery,
fingerprint computation or firing repair is a ShuETL responsibility. Upstream
schedule commands serve both headless and HTTP callers.

Run workers use the upstream managed execution factory; action workers select
its separate action role via `--kind actions` (`runs` is default). Upstream owns
handler loading/trust, claims, leases, cancellation, fencing and outcomes. Separate
processes establish concurrency and avoid long ETL ticks starving action jobs.
ShuETL dispatches through the qualified role lifecycle interface, initially using
one execution thread per worker; it does not assume unqualified method names.

### Configuration ownership

Constructor values override environment sources. Missing role/profile/provider
fails closed; CLI/config role or worker-kind disagreement is an error. Local
providers and static identity remain development-only. A preview uses one explicit
scope/store/profile per configured role instance.

| Setting | Ownership and planned deployment default |
| --- | --- |
| Store identity, tenant/workspace | Required explicit canonical values, consistent across roles |
| Execution profile/provider configuration | Canonical upstream types, approved installed packages; preserve supported controls |
| Worker kind | Deployment role selector: `runs` default or `actions` |
| Owner ID | Unique role-prefixed value per process start; never a credential |
| Poll interval | ShuETL dispatch pacing; default 1 second, finite 0.05–60 seconds |
| Lease TTL | Upstream runtime configuration; selected role factory default; constraints validated by upstream and deployment policy; never used to implement local lease logic |
| Probe port | Explicit loopback port per runtime process; gateway uses upstream HTTP probes |
| Probe refresh / stale threshold | ShuETL evidence freshness; planned 1 / 5 seconds, threshold greater than refresh |
| Shutdown grace | ShuETL supervision budget; planned 30 seconds, no forced effect interruption guarantee |
| Artifact/resource volume | Explicit shared deployment location passed to upstream; identity/access/retention semantics upstream |

Aliases use the `SHUETL_` prefix and are case-sensitive. Constructor values
override environment values. Upstream safety constraints are authoritative;
deployment may add documented tighter limits. Do not duplicate ETL profile,
action catalog, retention or per-run policy models in ShuETL.

### Lifecycle and probes

ShuETL process states are `starting`, `running`, `draining`, `stopped`, `failed`.
Combine public non-mutating upstream runtime/provider facts with process
responsiveness, deployment scope, probe freshness and drain state. Standby is
not an error; a zero tick is not a health check. Keep probes responsive during
active work and never claim/renew work or resolve credentials to inspect health.

Runtime loopback `/live` and `/ready` expose only role/state/bounded reason codes.
They are operational probes, the narrowly permitted ShuETL-owned endpoints;
ETLantic domain routes remain exclusively in its HTTP adapter. `doctor` inspects
configuration/provider facts and cannot prove another process's health.

Signals stop dispatch and fail readiness, then request the upstream role-specific
cooperative stop. Document already-dispatched acceptance/claim windows. Finish
active work before closing the backend and then bindings exactly once. Grace
expiry stays draining/non-ready and reports incomplete shutdown; the external
supervisor owns termination. Never close resources under an active tick, alter
leases or fabricate a terminal outcome. Use upstream status/stop contracts from
U05 rather than infer guarantees from current `ready`/`drain` method names.

### Schema and transition

Use a fresh separately provisioned store at the schema contract selected in W01;
retain 0.5/0.55 separately for rollback. Read public provider inspection results
for connectivity, required objects, version integrity and compatibility. Normal
construction and inspection issue no DDL or explicit commits. Only explicit
provider migration delegation may change schema. Runtime roles have required
DML grants but no schema CREATE, provider-table ownership or migration-role access.

The former constructor-DDL exception is removed. Version 0.57.0 supplies public
provider inspection beyond 0.56.2's read-only version fix; consume it and qualify
the full U04 contract. Preserve
fresh-store handoff, one trigger authority and explicit uncertain-effect
reconciliation; no rolling upgrade, durable conversion or cross-store replay.

## Alternatives

- Assemble missing stores and semantic callbacks in ShuETL: rejected by ADR-0015.
- Require dummy HTTP context factories in runtime roles: rejected; neutral
  construction is a Gate U prerequisite.
- Treat present `ready()`/zero tick as health: rejected; use qualified runtime
  facts plus independent provider and process evidence.
- Close an engine when shutdown grace expires: rejected while work is active.

## Consequences

The implementation follows qualified upstream contracts. ShuETL remains a
deployment product without inheriting ETL semantics. The standard host path stays
simple, while upstream library users can construct complete roles independently.

## Validation

Gate U/0 and AC-002/006–010/025–027/032/033 in the execution and verification
plans qualify these requirements. Preserve the
[0.5 contract evidence](../evidence/0.5/contracts.md) and
[ownership baseline](../evidence/0.5/ownership.md) as regression inputs. Unit
coverage exercises settings, imports, probes and close order; it does not
substitute for final-wheel PostgreSQL lifecycle or failure qualification.

## Revisit trigger

Revisit if upstream contracts cannot support isolated roles, safe supervision,
authorized headless parity or real runtime grants without ShuETL semantic code.
