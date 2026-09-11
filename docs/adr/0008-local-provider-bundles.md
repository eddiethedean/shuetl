# ADR-0008: Local Provider Bundles

- Status: Accepted
- Date: 2026-09-11

## Context

The 0.2 facade deliberately accepts a caller-built `ETLanticAPI`. Phase 0.3 must
reduce local provider wiring without taking ownership of ETLantic semantics,
host identity, authorization policy, or database migrations.

ETLantic 0.51.0 supplies public memory stores. `etlantic-sqlmodel` 0.51.0 supplies
public SQLite engine, control-plane store, migration, and schema-version APIs,
but no ShuETL-owned schema is needed.

## Decision

Phase 0.3 adds an explicit `LocalProviderBundle` factory for two named providers:
`memory` and `sqlite`.

The caller must inject an ETLantic `Authorizer`, `ContextFactory`, and
`PrincipalDependency`. The bundle constructs only the definition, submission,
and event stores and the authoritative `ETLanticAPI`. It exposes those upstream
objects without wrapping or translating them.

SQLite is available only through the `shuetl[sqlite]` extra. It accepts a local
file-backed SQLite URL, requires the upstream schema to already be at
`004_schedules_0_47`, and never creates tables or applies migrations. The bundle
owns an engine it creates and exposes an idempotent `close()` operation; the host
must call it during cleanup. Memory bundles have a no-op `close()`.

The existing `ShuETL(api=...)` path and its caller-ownership behavior remain
unchanged. ShuETL never closes a bundle from `mount()` or its 0.2 lifespan.

## Consequences

The common local graph becomes short and typed while identity and authorization
remain explicit. SQLite development requires a separate, visible upstream
migration step and host cleanup, preventing gateway startup from mutating schema.

## Alternatives

- Construct an authorizer or anonymous principal automatically; rejected because
  ShuETL does not own identity or ETLantic authorization semantics.
- Run `apply_migrations()` during bundle construction; rejected because startup
  and provider construction must be schema-read-only.
- Add ShuETL tables or repository wrappers; rejected because ETLantic provider
  packages remain authoritative.
- Make SQLite part of the core install; rejected because relational support is
  optional and memory remains the smallest local profile.

## Validation

The released baseline is recorded in the 0.2
[contract inventory](../evidence/0.2/contracts.md) and
[ownership matrix](../evidence/0.2/ownership.md).

See AC-011 through AC-024 in
[`PHASE_0_3_EXECUTION.md`](../plans/PHASE_0_3_EXECUTION.md).

## Revisit trigger

Revisit for the 0.4 PostgreSQL pilot, a change to the upstream migration head, or
an upstream provider-bundle/lifecycle API that can replace ShuETL's narrow local
composition.
