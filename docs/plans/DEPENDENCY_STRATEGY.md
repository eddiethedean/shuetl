# Dependency Strategy

## Principle

ShuETL depends directly only on libraries it uses for FastAPI composition and
ShuETL-owned configuration. ETLantic implementation mechanics remain behind
ETLantic packages and public contracts.

> **Depend on ETLantic contracts; do not reach through them to implementation
> libraries.**

Host applications depend on ShuETL. ShuETL has no build, runtime, test, or
optional-extra dependency on any consuming product. Data Mover is a reference
consumer of released ShuETL artifacts, not a package imported by ShuETL.

## Direct dependencies

The current package depends directly on:

```text
fastapi
pydantic
pydantic-settings
etlantic
etlantic-fastapi
```

The released 0.5 package and lock pin ETLantic core/FastAPI/SQLModel to 0.55.0.
Phase 0.6 reopens upstream selection under Gate U and
[ADR-0015](../adr/0015-backend-and-deployment-ownership.md). Version 0.57.0 is the
published candidate delivering the #278–282 public surfaces; the
[candidate audit](../reviews/ETLANTIC_0_57_CANDIDATE_AUDIT.md) records matching
upstream evidence and independent headless/gateway checks. [Coverage acceptance](../evidence/0.6/coverage-acceptance.md) closes Gate U.
Development metadata/lock use exact 0.57.0 pins and public schema inspection;
[PostgreSQL role feasibility](../evidence/0.6/README.md) passes on Python 3.11–3.13.
ShuETL role implementation and release qualification remain open.
Select exact published compatible versions only after upstream qualification;
update lock, compatibility checks and provider contract metadata together.
No patched wheels, floating versions or assumed future release number.

The [0.56 dependency map](ETLANTIC_0_56_DEPENDENCIES.md) and
[wheel audit](ETLANTIC_0_56_WHEEL_AUDIT.md) record the artifact evidence and
published API boundaries. The [0.6 execution contract](PHASE_0_6_EXECUTION.md)
requires upstream contracts followed by ShuETL service, OpenAPI, PostgreSQL
process and installed-artifact qualification before release. The selected
provider owns the required schema/status contract. Provision a fresh store;
retain 0.5/0.55 separately for rollback. Inspection and normal construction issue
no DDL or explicit commits; there is no constructor exception.

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

Connector and ETL execution extensions ship as independent backend provider
packages using public ETLantic contracts. Standard profiles name their qualified
package set; the operator installs/selects it, and the app supplies logical
specifications. New proprietary ETL implementations must also be packaged
independently of an adopter. The app may bridge its identity/credential store
without supplying extraction, transformation or loading code.

Developers may author private ETL extensions, including in the app's repository,
provided the backend package/artifact installs without the host application.
Public ETLantic extension contracts avoid any need for a ShuETL core change or
public package publication. Profile conformance, ownership and compatibility
evidence determine deployment support.

Explicit provider injection remains an advanced platform integration surface.
It does not satisfy the standard-consumer gate if an app must implement runtime
factories or coordinate ETL services. ShuETL must not require any adopter in its
distribution, core CI, hard-coded imports or clean-install examples.

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

FastAPI remains an installed composition dependency; `etlantic-fastapi` remains
authoritative for HTTP behavior. The headless promise concerns operation
without a server or synthetic request, not a FastAPI-free distribution. Moving
HTTP support into an optional extra would require a separate packaging decision.

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
