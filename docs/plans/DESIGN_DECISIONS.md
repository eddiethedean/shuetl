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

### Deferred until first use

These are required by the named later release, not by the 0.1 boundary proof:

1. exact settings constructor and configuration precedence — 0.3;
2. capability/readiness diagnostic schema — 0.3;
3. supported PostgreSQL driver and provider configuration — 0.4;
4. policy for invoking provider-owned migrations outside startup — 0.4;
5. gateway, scheduler, and worker CLI/process entry points — 0.6;
6. production route-selection presets, if distinct from the upstream surface —
   no later than 0.6.

Deferral does not authorize an implicit implementation decision. If earlier
work needs one of these choices, promote its ADR into the current release gate.
