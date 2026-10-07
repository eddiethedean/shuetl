# ShuETL Host Backend MVP

## Objective

Ship the smallest useful integration that lets an application developer
configure and operate ETLantic's existing control-plane capabilities without
learning or manually wiring every provider package. The host may mount the
FastAPI API or use ETLantic in-process as a headless backend.

The MVP proves composition value. It does not reimplement ETLantic features.

This is the cumulative host backend target, not the scope of one release.
0.5 proves specification-driven backend commands, 0.6 adds a bounded live ETL
profile with required transformations/validation, and 0.7 qualifies downstream
retirement of app ETL code. File inputs, provisioning, previews and additional
engines remain conditional on the advertised profile. See
[CAPABILITY_DELIVERY.md](CAPABILITY_DELIVERY.md)
and the narrower [0.5 execution contract](PHASE_0_5_EXECUTION.md).
The [developer-control contract](DEVELOPER_CONTROL.md) requires full public
control coverage in every qualified profile. This baseline sets a minimum;
applications can choose broader profiles and developer-authored extensions.

## Supported baseline

The current 0.4 implementation pins ETLantic 0.52.1 and matching companion
packages. The host backend must qualify the exact public services and provider
contracts it needs. A newer train, if required, is selected from evidence;
0.52.1 is not assumed to satisfy the complete future contract.

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

The required standard path accepts deployment configuration, identity/resource
bridges and canonical specifications. ShuETL supplies the qualified provider
graph and public backend command access. Connector invocation, row processing
and submission preparation run in the backend; developers may supply custom
backend extensions. The complete ownership contract is in
[SPECIFICATION_CONTRACT.md](SPECIFICATION_CONTRACT.md).

For advanced compatibility, continue accepting a preconstructed, supported
ETLantic API/provider graph and providing explicit bundle factories for reference
graphs from ShuETL settings. Preserve caller ownership. The 0.5 interface
decision determines how headless services are exposed without changing the
existing `ShuETL(api=...)` contract.

The facade mounts the authoritative `etlantic-fastapi` router and composes
required exception handlers and lifespan behavior.

### Host application integration

```python
integration = ShuETL(api=prebuilt_etlantic_api)
app = FastAPI(lifespan=integration.lifespan)
integration.mount(app)
```

Mounting into an existing FastAPI app and creating a dedicated app must expose
the same ETLantic contracts.

This is the existing caller-owned advanced facade pattern. The exact new standard
construction interface is frozen by Gate B of the 0.5 execution plan; no
`from_settings` factory is promised by this example.

An embedding host may instead use the same configured public ETLantic services
without mounting routes, starting an HTTP listener, or calling itself over
HTTP. This is a composition mode; it does not add ShuETL domain models or a
parallel execution API.

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

The host remains responsible for account/owner-to-principal/workspace mapping
and credential storage. Resource resolution uses opaque, versioned,
owner-authorized references through public ETLantic contracts in claimed
pipeline workers or separately authorized isolated provider actions. The
gateway receives only safe metadata.

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
- [ ] The dependency direction is host application → ShuETL → ETLantic;
      ShuETL has no adopter-specific imports, extras, schemas, or fixtures.
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

### Headless host composition

- [ ] A minimal host uses canonical specifications and backend commands without
      an HTTP server, caller provider graph or application ETL implementation.
- [ ] Schema/capability discovery and export/import preserve all supported
      business choices; backend-derived plans and hashes remain authoritative.
- [ ] One backend command owns planning, preflight and acceptance; the app
      needs no preparation sequence or recovery coordinator. Optional staged
      authoring/approval uses backend-validated references.
- [ ] Every qualified public caller option/command/query remains accessible,
      including provider-specific settings, run overrides and complete results.
- [ ] Effective run settings and allowed actions are discoverable, with explicit
      precedence, state/effect preconditions and retry-versus-rerun identities.
- [ ] Programmatic authoring, business workflows, external triggers and private
      backend extensions work without modifying ShuETL core.
- [ ] Headless and mounted modes preserve the same canonical validation,
      planning, durable submission, authorization, status, event, report, and
      artifact behavior.
- [ ] Provider capability pairing, destination-writer enablement, and
      source/destination object-overlap checks are enforced at authoring and
      durable submission boundaries.
- [ ] Owner-scoped catalog/connection checks, schema previews, optional
      destination provisioning, and host-managed file-source references use
      public provider contracts and do not leak credentials or row data.
- [ ] Pure validation/planning and live, bounded read-only provider preflight
      have separate contracts; failed preflight creates no pipeline submission.
- [ ] Host account/scope mapping and pipeline-worker/provider-action resolution
      are tested for cross-owner access, isolation and redaction.
- [ ] ShuETL does not depend on the generic host fixture or any named adopter.

### Providers and compatibility

- [ ] The supported ETLantic release range is explicit and enforced.
- [ ] Mismatched ETLantic package trains fail during construction or startup.
- [ ] Missing optional providers produce typed capability/readiness diagnostics.
- [ ] Local memory/SQLite configuration completes one documented example.
- [ ] PostgreSQL reference configuration is covered by integration tests.
- [ ] Provider-owned migrations are used; ShuETL does not infer DDL.

### End-to-end behavior

- [ ] The mandatory bounded transformation/validation profile executes entirely
      in backend packages with declared type, null, failure and resource behavior.
- [ ] Contrasting source/mapping/transform/rule/write/schedule specifications run
      through the same app without ETL implementation changes.
- [ ] Packaged connectors supply all advertised source/destination behavior;
      unsupported options cannot invoke an application ETL fallback.
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

Data Mover is a downstream adopter and owns its consumer-side integration
tests, saved-definition migration, and compatibility pin. ShuETL publishes the
host contract and generic conformance suite; it does not include Data Mover
code or schemas.

The downstream qualification must retire Data Mover's transfer engine,
connector implementations, submission preparation and lease/recovery logic
from the active path. Product schema/history migration remains Data Mover work.

## MVP stop condition

If the implementation cannot remain a thin composition of
`etlantic-fastapi` and public ETLantic providers, pause and decide whether the
needed changes belong upstream or whether ShuETL should merge into
`etlantic-fastapi`.
