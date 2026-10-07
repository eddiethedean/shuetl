# ShuETL Initial Design Decisions

These decisions define ShuETL's integration boundary. Material changes require
an ADR.

## D1 — ShuETL is an ETLantic + FastAPI integration product

ShuETL exists to make ETLantic straightforward to configure, mount, deploy, and
operate in FastAPI applications.

## D2 — ETLantic is authoritative

ETLantic owns pipeline definitions, plans, runtime/control-plane state,
scheduling, durable work, retries, cancellation, reports, events, artifacts,
security references, and provider contracts.

## D3 — `etlantic-fastapi` owns ETLantic HTTP semantics

ShuETL mounts and configures the existing adapter. It does not fork its routes,
schemas, operation IDs, errors, idempotency behavior, or SSE protocol.

## D4 — ShuETL owns composition

ShuETL owns settings, provider wiring, FastAPI integration, deployment-role
configuration, compatibility checks, readiness diagnostics, optional ecosystem
adapters, and operator documentation.

## D5 — No shadow domain models

ShuETL does not define parallel Pipeline, Plan, Run, Attempt, Schedule, Firing,
Event, Report, Artifact, Executor, retry, or authorization models.

## D6 — Upstream-first gaps

Missing semantic behavior belongs in ETLantic or an ETLantic provider package.
A temporary ShuETL adapter requires an ADR, explicit version bounds, and a
removal plan.

## D7 — No ShuETL control-plane schema in the MVP

Use ETLantic persistence providers. ShuETL owns no control-plane tables,
SQLModel subclasses, or Alembic revisions in the MVP.

## D8 — Provider-owned migrations

ShuETL checks schema compatibility and may invoke documented provider migration
commands. It does not autogenerate or infer production DDL.

## D9 — FastAPI-native host integration

ShuETL supports router mounting, application factories, dependency injection,
exception-handler composition, OpenAPI, and lifespan composition without taking
over unrelated host behavior.

## D10 — Development and production topologies differ

In-process execution may be offered for explicit local development. The
production reference separates gateway, scheduler, and worker roles.

## D11 — SQL-only does not mean one process

The production reference may avoid a required broker when PostgreSQL-backed
ETLantic providers supply durability and coordination. Execution remains outside
the gateway process.

## D12 — Identity is host-provided and ETLantic-authorized

The host authenticates principals. ShuETL adapts them into ETLantic context, and
ETLantic authorizer contracts govern ETLantic resources.

## D13 — AuthMate and Hedron are optional adapters

Neither is a core dependency or MVP blocker. Integration uses public contracts
when the peer package is implemented and supported.

## D14 — Pydantic is limited to ShuETL-owned concerns

ShuETL uses Pydantic for settings and composition diagnostics. ETLantic models
are reused for ETLantic domain data.

## D15 — Direct dependencies remain narrow

Scheduling, retry, persistence, migrations, filesystem, and worker libraries are
normally dependencies of ETLantic provider packages, not direct ShuETL
implementation dependencies.

## D16 — Lockstep compatibility is explicit

The first release supports one tested ETLantic minor train. ShuETL rejects
unsupported mixed versions and publishes a compatibility matrix.

## D17 — No convenience HTTP fork

ShuETL does not add alternate route vocabularies for the same ETLantic
operations. Convenience belongs in configuration, clients, or upstream routes.

## D18 — Merge rather than duplicate

If ShuETL cannot remain meaningfully distinct from `etlantic-fastapi`, the
projects should merge rather than maintain two competing integration surfaces.

## Open ADRs

### Blocking Phase 0.1

These decisions must close before work intended to survive into 0.2 is merged:

1. ShuETL versus `etlantic-fastapi` ownership, the package-boundary exit test,
   and the merge trigger;
2. initial Python, ETLantic, `etlantic-fastapi`, FastAPI, and Pydantic
   compatibility policy;
3. direct and optional dependency boundaries;
4. whether the 0.2 facade accepts only a prebuilt `ETLanticAPI`, constructs a
   reference provider graph, or supports both;
5. lifespan and problem-handler composition for existing FastAPI applications;
6. route-selection behavior for 0.2.

### Resolved for Phase 0.3

1. exact settings constructor and configuration precedence —
   [ADR-0007](../adr/0007-settings-sources-and-precedence.md);
2. local memory/SQLite provider construction and lifecycle —
   [ADR-0008](../adr/0008-local-provider-bundles.md);
3. capability/readiness diagnostic schema —
   [ADR-0009](../adr/0009-doctor-report-contract.md).

### Resolved for Phase 0.4

1. supported PostgreSQL driver and provider configuration —
   [ADR-0010](../adr/0010-postgresql-pilot-and-migration-boundary.md);
2. provider-owned migration invocation outside startup —
   [ADR-0010](../adr/0010-postgresql-pilot-and-migration-boundary.md).

Phase 0.4 is released against the published 0.52.1 provider train. The
qualification evidence and exact migration head are recorded in
[PHASE_0_4_EXECUTION.md](PHASE_0_4_EXECUTION.md); a future train change requires
requalification.

### Resolved for Phase 0.5

Phase 0.5 identity composition and production guard decisions are recorded in
[ADR-0011](../adr/0011-host-identity-composition-and-production-guards.md).
The implementation and published ETLantic 0.55.0 artifact qualification are
recorded in [PHASE_0_5_EXECUTION.md](PHASE_0_5_EXECUTION.md) and
[`docs/evidence/0.5/`](../evidence/0.5/). The final source commit passed hosted
CI, and the tag-triggered release workflow published ShuETL 0.5.0.

### Required before Phase 0.6 implementation

The [Phase 0.6 execution contract](PHASE_0_6_EXECUTION.md) records the
selected published ETLantic `0.56.0` train and the acceptance boundary.
The [proposed ADR-0014](../adr/0014-role-separated-managed-runtime.md) specifies:

1. the ShuETL process supervisor invoking the published managed backend,
   public scheduler ticks and managed execution host;
2. typed trusted host bindings, scoped scheduler/worker service identity and
   context, and ShuETL-owned construction of the managed worker;
3. role-local readiness transport and drain behavior, including a worker
   probe that does not assume an upstream `ready()` method;
4. the fresh 0.56 store transition and narrow non-mutating constructor DDL
   exception, with read-only preflight and health inspection.

Dependency selection is complete; these composition choices must be qualified
before `shuetl serve --role gateway|scheduler|worker` can make a
production-preview claim. Freeze the ADR's public signatures and qualify its
installed-wheel Gate 0 fixture before accepting it. The
[verification plan](PHASE_0_6_VERIFICATION.md) maps all 33 release criteria.
The existing `complete` route preset remains the baseline; add a different
production preset only if route inventory demonstrates a need and
an ADR preserves upstream route ownership.

These decisions belong to the named later release, not the 0.1 boundary proof:

1. gateway, scheduler, and worker CLI/process entry points — 0.6;
2. production route-selection presets, if distinct from the upstream surface —
   no later than 0.6.

Deferral does not authorize an implicit implementation decision. If earlier
work needs one of these choices, promote its ADR into the current release gate.
