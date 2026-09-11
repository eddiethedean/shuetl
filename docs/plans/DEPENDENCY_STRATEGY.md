# Dependency Strategy

## Principle

ShuETL depends directly only on libraries it uses for FastAPI composition and
ShuETL-owned configuration. ETLantic implementation mechanics remain behind
ETLantic packages and public contracts.

> **Depend on ETLantic contracts; do not reach through them to implementation
> libraries.**

## Initial direct dependencies

The first implementation is expected to depend directly on:

```text
fastapi
pydantic
pydantic-settings
etlantic
etlantic-fastapi
```

The exact version bounds are fixed in the Phase 0 compatibility ADR. The initial
target is a lockstep ETLantic 0.51.x package train rather than unbounded 0.x
compatibility.

A package used in ShuETL imports should be declared directly even if it is also
transitive.

## Reference persistence extra

```text
shuetl[postgresql]
  etlantic-sqlmodel
  supported PostgreSQL driver
```

This extra configures ETLantic's relational control-plane stores. ShuETL does
not use SQLModel or Alembic to define its own versions of those stores.

SQLite support may use the same upstream provider where supported. It remains a
local-development profile.

## Optional ecosystem extras

Potential extras include:

```text
shuetl[authmate]
shuetl[hedron]
shuetl[observability]
shuetl[external-runtime]
```

Each extra must:

- depend only on public APIs;
- pin a tested compatibility range;
- remain absent from core imports;
- fail with a clear capability diagnostic when requested but unavailable;
- have an integration test against the supported release train.

## Dependencies ShuETL should not own directly

Unless an ADR approves a narrow ShuETL-specific use, do not add direct
dependencies for:

- APScheduler or another scheduling engine;
- Tenacity or another execution retry engine;
- Dramatiq, Celery, or another worker system;
- SQLModel or Alembic for ETLantic control-plane tables;
- fsspec/UPath or cloud SDKs for ETLantic artifacts;
- ETLantic engine and compiler libraries not used by ShuETL composition code.

Those dependencies belong to ETLantic and its selected providers.

## FastAPI boundary

FastAPI is foundational to ShuETL, but `etlantic-fastapi` remains authoritative
for ETLantic route and schema behavior.

ShuETL uses FastAPI directly only for:

- mounting and application construction;
- dependency and lifespan composition;
- host-level integration diagnostics;
- documented exception-handler/middleware integration where the upstream
  adapter requires it.

## Pydantic boundary

Pydantic is used for ShuETL settings, provider-selection configuration, and
composition/readiness diagnostics.

ETLantic domain records retain their upstream classes and schemas. ShuETL does
not derive replacement models from them.

## Version policy

ETLantic 0.x packages evolve in lockstep. ShuETL must:

- support an explicit minor range;
- verify all installed ETLantic packages belong to a compatible train;
- test the exact lowest and highest supported versions;
- reject known-incompatible mixes at construction or startup;
- publish upgrade and rollback notes;
- expand compatibility deliberately rather than through permissive specifiers.

## Infrastructure policy

Python dependencies and external services are different concerns.

The initial production profile aims to require:

```text
FastAPI gateway process
ETLantic scheduler/worker process
PostgreSQL
```

Gateway, scheduler, and worker may use the same package installation or image.
Redis, RabbitMQ, Kafka, object storage, and external orchestration remain
optional when the configured upstream providers do not require them.

## Dependency review gate

Every proposed dependency must answer:

1. Is ShuETL importing and using it directly?
2. Is the capability already owned by ETLantic?
3. Could the dependency live in an optional ETLantic provider instead?
4. What compatibility and security burden does it add?

A dependency is not justified merely because the underlying exposed ETLantic
feature uses it.
