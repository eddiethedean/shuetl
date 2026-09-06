# ShuETL Architecture

## High-level architecture

```text
                   ┌─────────────────────────┐
                   │       FastAPI App       │
                   │                         │
                   │ REST / OpenAPI / Auth   │
                   └────────────┬────────────┘
                                │
                     ┌──────────▼──────────┐
                     │   ShuETL Service    │
                     │                    │
                     │ Pipeline Registry  │
                     │ Version Manager    │
                     │ Schedule Manager   │
                     │ Run Manager        │
                     │ Result Registry    │
                     └───────┬─────┬──────┘
                             │     │
                    ┌────────▼┐   ┌▼────────────┐
                    │Database │   │ Scheduler    │
                    │         │   │              │
                    │Metadata │   │ cron/interval│
                    └─────────┘   └──────┬───────┘
                                         │
                               ┌─────────▼─────────┐
                               │   Run Executor    │
                               │                   │
                               │ Load version      │
                               │ Preflight         │
                               │ ETLantic run      │
                               │ Persist report    │
                               └─────────┬─────────┘
                                         │
                               ┌─────────▼─────────┐
                               │     ETLantic      │
                               │                   │
                               │ contracts         │
                               │ planning          │
                               │ execution         │
                               │ reports           │
                               └───────────────────┘
```

## Core components

### FastAPI application

Owns the HTTP lifecycle and exposes ShuETL routers.

Possible composition:

```python
from fastapi import FastAPI
from shuetl import ShuETL

app = FastAPI()

shuetl = ShuETL(database_url="postgresql://...")
app.include_router(shuetl.router)
```

A convenience factory may also be provided:

```python
app = shuetl.create_app()
```

### Pipeline registry

Responsible for:

- pipeline identity;
- pipeline metadata;
- version lookup;
- active-version selection;
- enabling/disabling pipelines;
- resolving persisted ETLantic definitions.

### Pipeline version manager

Pipeline definitions must be immutable once used by a run.

A change creates a new version.

```text
customers
  v1
  v2
  v3  <- active
```

Schedules reference an active or pinned version according to explicit policy.

### Schedule manager

Stores recurring schedules durably.

A schedule should contain:

- target pipeline;
- version policy;
- cron/interval/date trigger;
- timezone;
- enabled state;
- misfire policy;
- concurrency policy;
- optional parameter payload.

### Scheduler

The scheduler converts due schedules into durable run records.

The scheduler does **not** directly execute pipeline semantics.

```text
Schedule due
    ↓
Create Run(PENDING)
    ↓
Executor claims run
```

This split prevents scheduling from being coupled to HTTP or pipeline execution.

### Run manager

Owns the run lifecycle:

```text
PENDING
CLAIMED
RUNNING
SUCCEEDED
FAILED
CANCELLED
```

Potential future states:

```text
RETRY_WAIT
TIMED_OUT
SKIPPED
BLOCKED
```

### Executor

Loads an immutable pipeline version and executes it through ETLantic.

Conceptual flow:

```text
Claim run
  ↓
Load pipeline version
  ↓
Resolve execution profile
  ↓
Optional preflight
  ↓
ETLantic.run(...)
  ↓
Persist run report
  ↓
Register result artifacts
  ↓
Finalize run
```

### Persistence layer

Use SQLAlchemy 2.x as the default ORM/data-access layer.

Support:

- SQLite for local development;
- PostgreSQL as the production reference backend.

Database access should remain behind repository/service interfaces so a future backend can be added without changing public ShuETL APIs.

## Deployment modes

### Mode 1 — single service

```text
1 process
FastAPI
Scheduler
Executor
Database
```

Best for development and small deployments.

### Mode 2 — replicated API with single scheduler leader

```text
FastAPI replica 1
FastAPI replica 2
FastAPI replica 3

        │
        ▼
shared DB

one elected scheduler
one or more executors
```

Database-backed leases or advisory locks prevent duplicate scheduling.

### Mode 3 — separated control and execution

```text
FastAPI control plane
        ↓
durable run queue
        ↓
worker pool
        ↓
ETLantic
```

This must be a later extension, not a prerequisite for MVP.

## Architectural rule

The public run/schedule/pipeline model must not depend on whether execution is local or distributed.

## External identity and credential provider boundary

ShuETL must not own a general-purpose authentication framework.

Instead, it consumes generic security protocols supplied by an external provider.

Conceptual contracts:

```python
class AuthorizationProvider(Protocol):
    async def authorize(
        self,
        principal: PrincipalRef,
        action: str,
        resource: ResourceRef,
    ) -> AuthorizationDecision: ...

class ServiceAccountProvider(Protocol):
    async def get_service_account(
        self,
        service_account_id: str,
    ) -> ServiceAccountRef: ...

class CredentialResolver(Protocol):
    async def resolve(
        self,
        principal: PrincipalRef,
        credential_id: str,
    ) -> ResolvedCredential: ...

class AuditSink(Protocol):
    async def record(self, event: SecurityAuditEvent) -> None: ...
```

ShuETL core should depend on these stable protocols, not AuthMate ORM or implementation types.

### Reference composition

```text
Hedron
  presentation
      │
      ▼
External Identity Provider
  authentication
  authorization
  service accounts
  credentials
      │
      ▼
ShuETL
  pipelines
  schedules
  runs
      │
      ▼
ETLantic
```

The reference implementation is AuthMate, but it must remain optional.

### Execution identity

Every production-capable pipeline should be able to declare an execution service account.

```text
Human user
  ↓ authorized to trigger
Pipeline
  ↓ executes as
Service account
  ↓ authorized to use
Credential
```

The triggering user and execution identity are distinct concepts and must both be persisted where applicable.

## Ecosystem composition principle

> **Independent by default, composable by contract.**

ShuETL is an independently deployable FastAPI-native package. It may compose with Hedron, AuthMate, or other FastAPI packages, but it must not require those application packages in core.

Cross-package interoperability must use:

- public FastAPI routers and dependency injection;
- stable Python protocols;
- generic resource/principal references;
- optional extras or adapter packages;
- documented integration contracts.

The full stack may be a supported reference deployment:

```text
FastAPI
├── Hedron
├── AuthMate
├── ShuETL
└── ETLantic
```

without changing the package boundary that Hedron, AuthMate, and ShuETL are peers.

A proposed feature is an architectural smell if it requires ShuETL core to import Hedron, depend on AuthMate implementation internals, or make another application package mandatory when a public protocol can express the same contract.

## Ecosystem composition rule

**Independent by default, composable by contract.**

ShuETL must not create direct core dependencies on Hedron or AuthMate. Integration should occur through:

- FastAPI routers and dependency injection;
- stable Python protocols;
- generic principal/resource references;
- optional adapters/extras;
- shared compatibility tests.

The full Hedron + AuthMate + ShuETL + ETLantic stack is a supported composition, not a required installation shape.

If a future feature requires ShuETL core to import Hedron or provider-specific AuthMate implementation types, that should be treated as an architectural smell and reviewed through an ADR.

## Dependency boundary

```text
ShuETL domain/services
   ├── APScheduler timing adapter
   ├── SQLAlchemy persistence
   ├── Tenacity retry mechanics
   ├── fsspec/UPath artifact adapter
   └── optional worker adapters
       ├── Dramatiq
       └── Celery
```

The public schedule/run/executor model remains stable regardless of implementation backend.

## Pydantic contract layer

ShuETL should maintain:

```text
FastAPI
  ↓
Pydantic ShuETL contracts
  ↓
ShuETL services
  ↓
SQLAlchemy / scheduler / executor adapters
  ↓
ETLantic
```

Pydantic defines ShuETL's public control-plane records and configuration. ETLantic remains authoritative for pipeline semantics.

## SQLModel-first persistence strategy

Use **SQLModel** by default where it cleanly unifies Pydantic domain models with relational persistence.

> **Prefer SQLModel for ordinary persisted domain entities; use SQLAlchemy directly for advanced persistence mechanics.**

SQLAlchemy remains an underlying dependency and escape hatch for:

- complex joins/window queries;
- explicit transaction/control-flow needs;
- advisory locks / `SELECT ... FOR UPDATE`;
- bulk operations;
- engine/session configuration;
- backend-specific features;
- migration internals;
- performance-critical paths that SQLModel does not express cleanly.

Alembic remains the migration tool.

Do not force SQLModel into areas where a plain Pydantic model or direct SQLAlchemy Core/ORM model is clearer.

## FastAPI runtime composition

FastAPI lifespan starts/stops ShuETL's scheduler/local executor resources.

DI composes sessions, identity, credentials, executors, artifact stores, and publishers.

Durable runs are explicitly decoupled from HTTP request lifetimes.

## Infrastructure baseline

The default deployment architecture is:

```text
FastAPI application
        +
relational SQL database
```

No other service is required for core functionality.

External infrastructure is always optional and must sit behind public provider/adapter contracts.

Examples of optional extensions:

```text
Redis / RabbitMQ
Kafka
OpenSearch / Elasticsearch
S3 / cloud object stores
Vault / cloud secret managers
external schedulers
separate worker fleets
```

A future feature that makes one of these mandatory for normal operation requires an explicit architectural review and should be presumed to violate the ecosystem baseline.
