# ADR-0010: PostgreSQL Pilot and Migration Boundary

- Status: Accepted
- Date: 2026-09-11

## Context

Phase 0.4 must qualify durable PostgreSQL behavior without giving ShuETL
ownership of ETLantic's schema or semantics. The 0.3 settings support only local
memory/SQLite providers, and the 0.3 doctor intentionally avoids network probes
and migrations.

The relational stores publicly accept a SQLAlchemy `Engine`, but the inspected
provider train exposes no PostgreSQL-specific engine factory. Psycopg supports
the SQLAlchemy `postgresql+psycopg` dialect. Provider migration status cannot be
read safely through the current public `current_version()` implementation on a
fresh database because it creates and commits the version table.

## Decision

Phase 0.4 adds one explicit `postgresql-pilot` gateway profile and a separate
`PostgreSQLProviderBundle`. The optional extra uses an exact qualified
`etlantic-sqlmodel`/SQLAlchemy train plus `psycopg[binary]==3.3.5`. PostgreSQL
18.6 is the only server qualified for the pilot.

The bundle constructs one synchronous SQLAlchemy engine directly through the
public `create_engine()` seam, using a bounded timeout, `pool_pre_ping`, and
explicit TLS mode. `verify-full` is the default. The host continues to inject
identity and authorization and owns bundle cleanup.

Schema mutation is allowed only through the explicit
`shuetl database upgrade` operator command. That command invokes the exact
provider-owned public upgrade API. Gateway startup, provider construction,
doctor, facade mounting, and lifespan are read-only and never create or migrate
tables.

Readiness uses a narrow private compatibility adapter: SQLAlchemy inspection and
a fixed read-only query against the provider-owned version table. It requires
both the exact qualified head and the minimum table inventory. ShuETL does not
expose this adapter as a migration API and will replace it if the provider
publishes a suitable read-only status function.

The bundle uses registry-backed definitions and exact upstream submission,
event, durable-work, and schedule stores. ShuETL does not wrap missing or unsafe
provider behavior.

## Consequences

Operators receive a reproducible pilot graph, secure connection default,
non-mutating readiness, and visible migration step. Migration credentials can be
separated from gateway credentials. The binary driver choice favors reproducible
pilot installation over system-libpq customization.

The 0.52.0 ETLantic provider train supplies the production migration path and
concurrency-safe event append semantics required by this decision. The original
qualification findings remain recorded in ETLantic #131 and #132.

## Alternatives

- Use `create_control_plane_tables()` to fill migration gaps; rejected because
  upstream documents it for tests/local demos and it bypasses production
  migration history.
- Add ShuETL migrations/tables or wrap the event store; rejected because that
  transfers ETLantic semantic ownership to ShuETL.
- Run migrations during startup; rejected because serving and schema-change
  privileges/lifecycles must remain separate.
- Use the provider's current `current_version()` from doctor; rejected because
  the inspected implementation mutates a fresh database.
- Use async SQLAlchemy/Psycopg; rejected because the public upstream stores use
  synchronous `Engine` and sessions.
- Allow arbitrary PostgreSQL/libpq combinations; rejected until separately
  qualified.

## Validation

The released baseline is recorded in the 0.3
[contract inventory](../evidence/0.3/contracts.md) and
[ownership matrix](../evidence/0.3/ownership.md).

See AC-001 through AC-038 in
[`PHASE_0_4_EXECUTION.md`](../plans/PHASE_0_4_EXECUTION.md).

## Revisit trigger

Revisit when the provider exposes a PostgreSQL engine/bundle or read-only schema
API, the pilot expands beyond PostgreSQL 18.6/Psycopg binary 3.3.5, or production
topology grows beyond a controlled single-tenant gateway.
