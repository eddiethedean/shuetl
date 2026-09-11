# ShuETL MVP

## Objective

Ship the smallest useful integration that lets a FastAPI developer configure,
mount, and operate ETLantic's existing control-plane capabilities without
learning or manually wiring every provider package.

The MVP proves composition value. It does not reimplement ETLantic features.

## Supported baseline

The first implementation targets one explicit, lockstep ETLantic release train,
initially ETLantic 0.51.x and matching optional packages. Support expands only
after compatibility tests exist.

## Required ShuETL capabilities

### Configuration

Provide a typed `ShuETLSettings` model covering:

- deployment profile and role;
- API prefix and route-selection preset;
- local versus relational store selection;
- database connection reference;
- identity/principal dependency requirements;
- enabled optional providers;
- operational bounds accepted by upstream providers.

Settings must not reproduce ETLantic domain configuration.

### Composition facade

Provide one `ShuETL` facade that can either:

- accept a preconstructed, supported ETLantic API/provider graph; or
- construct the reference graph from explicit ShuETL settings.

The facade mounts the authoritative `etlantic-fastapi` router and composes
required exception handlers and lifespan behavior.

### Host application integration

```python
integration = ShuETL.from_settings(settings)
app = FastAPI(lifespan=integration.lifespan)
integration.mount(app)
```

Mounting into an existing FastAPI app and creating a dedicated app must expose
the same ETLantic contracts.

### Local-development profile

Offer a clearly labeled local profile using supported ETLantic memory or SQLite
providers and, where supported, in-process development roles.

This profile optimizes for a quick first run. It is not the production default.

### Production reference profile

Document and test:

- PostgreSQL-backed ETLantic providers;
- a FastAPI gateway role;
- separate ETLantic scheduler and worker roles;
- schema and package compatibility checks;
- no required Redis/RabbitMQ/Kafka when the chosen ETLantic SQL provider does
  not require them.

### Capability and readiness diagnostics

Provide a `shuetl doctor` command or equivalent API that reports:

- installed and supported package versions;
- selected deployment profile and role;
- configured provider capabilities;
- database connectivity and provider schema compatibility;
- missing identity/authorization requirements;
- whether the topology is development-only or production-supported.

### Identity bridge

Accept a host FastAPI principal dependency and adapt it into the supported
ETLantic control-plane context. Core tests use a fake provider. AuthMate is not
required for the MVP.

### Upstream feature exposure

When the required ETLantic providers are configured, the mounted API exposes the
upstream operations for definitions, validation/planning, durable submission,
runs, schedules, events, reports, and artifacts.

ShuETL adds no alternative routes or domain models for those operations.

## MVP acceptance criteria

### Boundary

- [ ] ShuETL imports and uses ETLantic public models and protocols directly.
- [ ] No ShuETL `Pipeline`, `Run`, `Schedule`, `Attempt`, `Event`,
      `Artifact`, `Executor`, or retry-policy model exists.
- [ ] ShuETL owns no control-plane database tables or migrations.
- [ ] A source check prevents accidental copies of selected ETLantic schema
      identifiers or domain models.

### FastAPI composition

- [ ] A normal FastAPI app can mount ShuETL under a configurable prefix.
- [ ] A dedicated application factory exposes the same route/OpenAPI contract.
- [ ] ETLantic operation IDs, response models, problem details, and SSE media
      types remain intact.
- [ ] Existing host lifespan and middleware can be composed safely.
- [ ] No ETLantic pipeline executes in a request or FastAPI
      `BackgroundTasks`.

### Providers and compatibility

- [ ] The supported ETLantic release range is explicit and enforced.
- [ ] Mismatched ETLantic package trains fail during construction or startup.
- [ ] Missing optional providers produce typed capability/readiness diagnostics.
- [ ] Local memory/SQLite configuration completes one documented example.
- [ ] PostgreSQL reference configuration is covered by integration tests.
- [ ] Provider-owned migrations are used; ShuETL does not infer DDL.

### End-to-end behavior

- [ ] A canonical ETLantic definition can be registered through the mounted API.
- [ ] A manual submission returns the upstream durable record and `202` only
      after durable acceptance.
- [ ] Status, events, report, and artifact metadata round-trip without lossy
      ShuETL translation.
- [ ] A configured ETLantic schedule produces a canonical firing and durable
      submission without a ShuETL scheduling loop.
- [ ] Restart and idempotent-resubmission tests exercise upstream durability
      through ShuETL.

### Security

- [ ] Production configuration fails closed without principal and authorizer
      integration.
- [ ] Development-only unauthenticated behavior requires explicit selection.
- [ ] Authorization occurs before existence-sensitive lookup and list/event
      filtering.
- [ ] Secrets and credentials never enter ShuETL settings output, diagnostics,
      logs, or API wrappers.
- [ ] Arbitrary Python source, import paths, and package installation are not
      accepted through ShuETL.

### Operations

- [ ] `shuetl doctor` distinguishes liveness, readiness, capability, and
      production support.
- [ ] Gateway, scheduler, and worker roles can use the same pinned installation
      while running as separate supervised processes.
- [ ] The production guide documents shutdown, migrations, backup/restore,
      rolling upgrades, and provider-specific residual risks.

## Explicitly deferred

- AuthMate and Hedron reference adapters;
- operator UI;
- additional ETLantic release trains;
- cloud/external execution presets;
- broker-backed deployment presets;
- custom ShuETL persistence;
- domain-level extension registries;
- pipeline-specific convenience endpoints.

## MVP stop condition

If the implementation cannot remain a thin composition of
`etlantic-fastapi` and public ETLantic providers, pause and decide whether the
needed changes belong upstream or whether ShuETL should merge into
`etlantic-fastapi`.
