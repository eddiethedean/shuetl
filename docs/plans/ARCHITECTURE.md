# ShuETL Architecture

## Architectural statement

ShuETL is an application integration layer over ETLantic's public control-plane
and FastAPI packages.

It must not become a second semantic layer between FastAPI and ETLantic.

```text
Host FastAPI application
        │
        ▼
ShuETL composition facade
  configuration · provider wiring · capability/readiness checks
        │
        ▼
etlantic-fastapi
  authoritative routes · HTTP schemas · errors · SSE
        │
        ▼
ETLantic public contracts and services
  definitions · plans · submissions · schedules · events · reports
        │
        ├───────────────┐
        ▼               ▼
ETLantic stores     ETLantic execution roles
memory / SQLModel   scheduler / worker / external runtime
```

## Ownership rule

A feature exposed through ShuETL may be implemented by ETLantic. “ShuETL
supports” means ShuETL selects, configures, exposes, documents, and tests that
upstream capability; it does not imply a ShuETL implementation.

Before adding a ShuETL domain abstraction, answer:

1. Does ETLantic already define the model, protocol, or behavior?
2. Could the missing capability be added to an ETLantic provider package?
3. Is the proposed code only FastAPI/application composition?

Only the third category belongs directly in ShuETL. An exception requires an
ADR describing why upstream reuse is impossible and how semantic drift is
prevented.

## Components

### ShuETL facade

The public ShuETL object should make composition concise while keeping providers
explicit:

```python
from fastapi import FastAPI
from shuetl import ShuETL, ShuETLSettings

integration = ShuETL.from_settings(
    ShuETLSettings.from_env(),
    principal_dependency=current_principal,
)

app = FastAPI(lifespan=integration.lifespan)
integration.mount(app)
```

The exact constructor remains an ADR. Regardless of syntax, the facade owns:

- validated ShuETL integration settings;
- construction or acceptance of ETLantic provider instances;
- mounting the authoritative `etlantic-fastapi` router;
- composition with a host lifespan without silently replacing it;
- readiness and capability reporting;
- deployment-role selection;
- compatibility diagnostics.

It does not own ETLantic records or execution semantics.

### `etlantic-fastapi`

`etlantic-fastapi` remains authoritative for:

- ETLantic HTTP route paths and operation IDs;
- request and response schemas;
- durable-accept response semantics;
- problem-detail/error representation;
- authorization placement;
- SSE event and resume behavior;
- API-level idempotency and optimistic-concurrency requirements.

ShuETL may select routes, add a mount prefix or tags, and configure dependencies.
It must not copy route implementations.

### ETLantic contracts and services

ETLantic remains authoritative for:

- pipeline definitions, revisions, and fingerprints;
- validation and resolved plans;
- profiles, bindings, and plugin capability decisions;
- submissions, attempts, leases, fencing, effects, and recovery;
- schedules and logical firing identity;
- retries, cancellation, timeouts, replay, and repair;
- reports, events, diagnostics, and artifact references;
- control-plane authorization context and provider protocols.

ShuETL consumes these public contracts directly.

### Providers

ShuETL configures ETLantic provider implementations. Initial profiles should use:

- ETLantic memory providers for tests and explicit local demos;
- `etlantic-sqlmodel` reference stores for relational persistence;
- PostgreSQL as the production reference database;
- SQLite as a local-development option where supported;
- ETLantic scheduler/worker roles or a supported external execution host.

Provider migrations and schema compatibility remain owned by the provider
package.

### Host application

The host owns:

- authentication and principal creation;
- top-level middleware, CORS, trusted proxies, and TLS termination;
- application-wide lifespan composition;
- deployment supervision and process scaling;
- selection of identity, secrets, logging, and observability integrations;
- business-specific pipeline definitions and runtime profiles.

ShuETL supplies adapters and documented integration points without taking over
the host.

## Core flows

### Definition registration

```text
Application-defined ETLantic PipelineDefinition
        ↓
ShuETL facade validates configured capability
        ↓
ETLantic definition/registry service
        ↓
ETLantic revision and fingerprint persisted by selected provider
```

ShuETL never invents a second version or fingerprint.

### Manual submission

```text
HTTP request
  ↓ host authenticates principal
ETLantic authorization context
  ↓
etlantic-fastapi submit route
  ↓
ETLantic durable acceptance transaction
  ↓
202 with canonical ETLantic submission/run record
  ↓
ETLantic worker or external execution host
```

Returning `202 Accepted` requires the upstream durable store to have accepted
the work. ShuETL does not return a synthetic success while work is only in
memory.

### Scheduled submission

```text
ETLantic schedule revision becomes due
        ↓
ETLantic scheduler creates one idempotent firing
        ↓
ETLantic durable submission
        ↓
ETLantic worker/execution host
```

ShuETL supplies configuration and process-entry integration. It does not
recalculate trigger semantics or create its own run record.

## Capability and readiness model

ShuETL should expose a typed composition report that distinguishes:

- configured;
- available;
- ready;
- unavailable because an optional provider is absent;
- incompatible because package versions or capabilities do not align;
- unsafe for the selected deployment profile.

Capability discovery must not turn an absent upstream feature into an implicit
fallback implementation.

## Deployment profiles

### Local development

```text
one process
├── FastAPI
├── ShuETL
├── ETLantic in-process development scheduler/worker
└── memory or SQLite providers
```

This profile optimizes for setup speed. It must be labeled as development and
must not imply crash isolation or multi-process safety.

### Production SQL-only reference

```text
same version-pinned application image
├── gateway role: FastAPI + ShuETL + etlantic-fastapi
├── scheduler role: ETLantic scheduler service
├── worker role: ETLantic worker service
└── PostgreSQL: selected ETLantic relational stores
```

No broker is required when the selected ETLantic durable provider supports SQL
coordination. Gateway and execution roles are nevertheless separate supervised
processes.

### External execution

```text
FastAPI + ShuETL
        ↓
ETLantic durable submission/provider contract
        ↓
supported external runtime or orchestrator
```

Public ETLantic submission and report semantics remain unchanged.

## Identity integration

The host resolves an authenticated principal. A ShuETL adapter converts the host
identity into ETLantic's public principal/control-plane context and injects the
configured ETLantic authorizer.

AuthMate may be a reference adapter when implemented, but neither ShuETL nor
ETLantic core depends on AuthMate ORM or token types.

## Migration boundary

ShuETL does not generate migrations for ETLantic-owned tables and does not
subclass provider persistence models to add application columns.

- ETLantic provider packages own their schemas and migrations.
- Host applications own host-specific tables and migrations.
- ShuETL may run read-only migration compatibility checks and invoke documented
  provider upgrade APIs.
- Production startup must fail clearly on an incompatible schema; it must not
  auto-generate DDL from runtime model inspection.

## Packaging boundary

Keep direct ShuETL dependencies narrow. ETLantic implementation dependencies
such as scheduling, retry, SQLModel, Alembic, and filesystem libraries should
normally arrive through the selected ETLantic packages rather than being used
directly by ShuETL.

## Architectural test

A valid ShuETL feature should still make sense when phrased as:

> “Configure or expose ETLantic capability X through FastAPI.”

If it instead reads:

> “Define ShuETL's version of ETLantic capability X,”

the feature is outside the intended boundary.
