# ShuETL Roadmap

## Purpose

This roadmap defines ShuETL's independent 0.x release train.

ShuETL versions do not mirror ETLantic versions. Every ShuETL release instead
publishes an explicit compatibility matrix for ETLantic core,
`etlantic-fastapi`, `etlantic-sqlmodel`, FastAPI, Python, and optional
integration packages.

The roadmap is ordered by evidence and capability, not calendar dates. A release
does not advance until its exit gate is met.

## Product boundary for every release

All 0.x releases obey these invariants:

1. ETLantic owns pipeline definitions, plans, durable work, run state,
   scheduling, execution, reports, events, artifacts, and provider protocols.
2. `etlantic-fastapi` owns ETLantic HTTP routes, schemas, operation IDs,
   durable-accept behavior, errors, authorization placement, and SSE semantics.
3. ShuETL owns settings, provider wiring, FastAPI composition, deployment
   profiles, compatibility/readiness diagnostics, ecosystem adapters, and
   operator guidance.
4. ShuETL does not create shadow ETLantic domain models or control-plane tables.
5. Missing semantic behavior is resolved upstream rather than reimplemented in
   ShuETL.
6. Local one-process convenience is never presented as a production guarantee.
7. Production gateway processes do not execute ETLantic pipeline work.
8. Provider packages own their schemas and migrations; ShuETL does not infer
   production DDL.

Violating one of these invariants requires an ADR and a review of whether ShuETL
should instead merge into `etlantic-fastapi`.

## Release overview

| Release | Maturity | Primary outcome | Maximum support claim |
|---|---|---|---|
| 0.1 | Experimental | Boundary proof and package foundation | Architecture and integration spike only |
| 0.2 | Experimental | Embeddable FastAPI composition | Local/test use |
| 0.3 | Development Preview | Typed configuration and local developer experience | Documented local profile |
| 0.4 | Pilot | PostgreSQL-backed durable integration | Controlled single-tenant pilot |
| 0.5 | Secure Pilot | Host identity and fail-closed authorization | Authenticated single-tenant pilot |
| 0.6 | Production Preview | Separate gateway, scheduler, and worker roles | Bounded production preview |
| 0.7 | Production Candidate | Operability, recovery, and deployment qualification | Named reference profile only |
| 0.8 | Integration Preview | Compatibility expansion and optional ecosystem adapters | 0.7 baseline plus experimental adapters |
| 0.9 | Release Candidate | Public-contract freeze and 1.0 qualification | Bounded 1.0 release candidate |

Maturity labels apply only to the deployment profiles named by that release.
An experimental optional adapter does not weaken a supported baseline profile,
but it must be labeled separately.

---

## 0.1 — Boundary Proof and Package Foundation

### Outcome

Prove that ShuETL solves a real composition problem without duplicating
ETLantic or `etlantic-fastapi`.

The detailed execution plan, evidence format, and stop conditions are defined
in [PHASE_0_1.md](PHASE_0_1.md). Phase 0.1 is an evidence release; it does not
ship the public composition facade planned for 0.2.

### Deliverables

- Create the package skeleton, build metadata, typed-package marker, test
  layout, documentation entry point, and CI baseline.
- Inventory public contracts from installed packages in the selected ETLantic
  release train:
  definitions, registry, submissions, durable work, schedules, events, reports,
  artifacts, authorization, SQLModel stores, FastAPI routes, and runtime roles.
- Produce a feature ownership matrix naming the authoritative package for every
  capability ShuETL plans to expose.
- Build a disposable spike that:
  - constructs an ETLantic API with memory providers;
  - mounts it in an ordinary FastAPI application;
  - reads a seeded definition and accepts an idempotent submission through
    upstream HTTP routes;
  - generates normalized OpenAPI evidence without ShuETL shadow schemas.
- Record ADRs for:
  - ShuETL versus `etlantic-fastapi` ownership and the merge trigger;
  - initial ETLantic/FastAPI/Python compatibility range;
  - direct and optional dependency boundaries;
  - whether the facade accepts prebuilt providers, constructs a reference graph,
    or supports both;
  - the 0.2 lifespan and problem-handler composition boundary;
  - the 0.2 route-selection behavior.
- Add import-boundary checks preventing direct use of ETLantic implementation
  libraries such as APScheduler, Tenacity, SQLModel, or Alembic in ShuETL core.
- Build and install the wheel in a clean environment, then run the spike against
  declared dependencies rather than a sibling source checkout.

### Explicit non-goals

- No stable public API.
- No production implementation retained from the disposable spike.
- No PostgreSQL production claim.
- No custom routes for runs, schedules, artifacts, or events.
- No ShuETL database models or migrations.
- No worker or scheduler implementation.

### Exit gate

- [ ] Wheel and sdist build, include `py.typed`, and the wheel imports in a clean
      environment.
- [ ] The memory-provider spike works under a prefix through public
      `etlantic-fastapi` APIs from installed distributions.
- [ ] A definition read and repeated idempotent submission return the expected
      upstream durable-accept results, including `202` and one canonical
      acceptance identity.
- [ ] The ownership matrix has no unexplained overlapping semantic owner.
- [ ] The public-contract inventory records owner, public import path, maturity,
      and version evidence for every upstream dependency needed through 0.2.
- [ ] Normalized OpenAPI evidence preserves upstream operation IDs and schema
      references rather than copied ShuETL models.
- [ ] Boundary tests fail on representative prohibited imports and shadow-model
      fixtures while accepting approved public composition imports.
- [ ] The distinct value of ShuETL is stated in one paragraph and validated by
      at least one working FastAPI integration.
- [ ] The six ADRs required to begin 0.2 are accepted and linked from a
      reproducible release-evidence index.
- [ ] No unresolved blocking upstream gap remains.

If the boundary cannot be defended at this gate, stop and contribute the
integration improvements directly to `etlantic-fastapi`.

---

## 0.2 — Embeddable FastAPI Composition

### Outcome

Ship the first usable ShuETL facade for local development and automated tests.

The authoritative public contract, acceptance criteria, and dependency-aware
implementation sequence are defined in
[PHASE_0_2_EXECUTION.md](PHASE_0_2_EXECUTION.md).

### Public surface

The intended shape is:

```python
integration = ShuETL(api=etlantic_api)
integration.mount(app, prefix="/etl")
```

and:

```python
app = integration.create_app()
```

Exact names may change before the 0.9 freeze.

### Deliverables

- Implement a minimal `ShuETL` composition facade.
- Accept a preconstructed supported `ETLanticAPI` graph.
- Mount the upstream router beneath a validated optional prefix.
- Provide a dedicated FastAPI application factory.
- Compose required ETLantic problem-detail handlers.
- Provide a documented lifespan-composition helper for host applications.
- Namespace ShuETL-owned application state without overwriting unrelated host
  state.
- Detect duplicate mounts, conflicting prefixes, and operation-ID collisions.
- Preserve upstream:
  - request and response models;
  - status codes;
  - durable-accept semantics of the configured store;
  - authorization ordering;
  - SSE response types and cursor inputs;
  - OpenAPI operation IDs and schema identities.
- Add dependency-override examples for application tests.

### Explicit non-goals

- No environment-driven provider construction.
- No production database profile.
- No promise that memory providers survive restart.
- No in-process scheduler or worker owned by ShuETL.
- No alternate convenience endpoint vocabulary.

### Exit gate

- [ ] Mount and dedicated-app modes pass the same API contract tests.
- [ ] Prefix mounting preserves route generation and OpenAPI references.
- [ ] Host lifespan setup and cleanup run exactly once.
- [ ] Upstream exception handlers can be installed without taking over unrelated
      host handlers.
- [ ] ETLantic dependency overrides work through ShuETL.
- [ ] No pipeline execution occurs in a request or FastAPI
      `BackgroundTasks`.
- [ ] The quick example runs from an installed wheel, not only a source checkout.

---

## 0.3 — Typed Configuration and Local Developer Experience

### Outcome

Make the common local ETLantic + FastAPI setup predictable and diagnosable.

The authoritative public contract, acceptance criteria, security boundaries,
and dependency-aware implementation sequence are defined in
[PHASE_0_3_EXECUTION.md](PHASE_0_3_EXECUTION.md).

### Deliverables

- Add frozen `ShuETLSettings` with constructor-over-environment precedence and
  no implicit dotenv, secrets-directory, or file source.
- Require explicit local profile, gateway role, memory/SQLite provider, and host
  identity mode; missing configuration never selects development behavior.
- Preserve the complete upstream router and existing prefix contract.
- Add explicit `LocalProviderBundle` construction using host-supplied ETLantic
  authorization and identity contracts.
- Support core ETLantic memory providers and an opt-in, file-backed SQLite local
  profile through the exact `etlantic-sqlmodel` train.
- Require SQLite schema provisioning through upstream tooling outside startup;
  inspect the exact migration head and expose explicit bundle cleanup.
- Add `shuetl doctor` with equivalent deterministic text and versioned JSON
  output for configuration, package compatibility, capabilities, provider
  readiness, schema state, and the development-only topology warning.
- Provide one install-to-first-run tutorial using an application-owned ETLantic
  definition.
- Provide settings examples for explicit Python construction and environment
  configuration.
- Redact database credentials and all secret-like values from settings,
  diagnostics, errors, and logs.

### Explicit non-goals

- No implicit production defaults.
- No automatic plugin discovery from caller-controlled values.
- No automatic table creation or database migration.
- No claim that SQLite is a production coordination backend.
- No host identity product.
- No registry, durable-work, scheduling, governance, worker, or execution graph.
- No new or filtered HTTP routes and no replacement for upstream `/ready`.

### Exit gate

- [ ] A new user reaches a working local API from a clean environment using the
      documented quickstart.
- [ ] Missing optional providers produce actionable capability diagnostics.
- [ ] Mixed unsupported ETLantic package versions fail before serving traffic.
- [ ] Unsupported production profiles and non-gateway roles fail validation;
      no local provider is constructed.
- [ ] Development-only behavior cannot be selected through missing
      configuration.
- [ ] Diagnostic snapshots contain no credentials or resolved secret values.
- [ ] Configuration tests cover explicit values, environment values, invalid
      combinations, and deterministic precedence.
- [ ] SQLite uses an already migrated file, applies no schema change during
      construction/startup, and closes its engine exactly once.
- [ ] Existing 0.2 facade, HTTP, authorization, lifecycle, and OpenAPI contracts
      remain unchanged.

---

## 0.4 — Durable PostgreSQL Pilot

### Outcome

Qualify a controlled, single-tenant PostgreSQL deployment using ETLantic's
relational providers and migrations.

### Deliverables

- Add a `shuetl[postgresql]` extra containing the supported
  `etlantic-sqlmodel` package and PostgreSQL driver.
- Construct the reference ETLantic provider graph for:
  - definition/registry persistence;
  - durable submissions;
  - events;
  - durable work;
  - schedules and firings;
  - any report/artifact metadata stores required by the supported upstream
    profile.
- Add database connectivity, schema-head, and migration compatibility checks to
  readiness and `shuetl doctor`.
- Provide explicit commands that invoke provider-owned migration APIs outside
  gateway startup.
- Prove that mounted endpoints preserve upstream idempotency, revision,
  submission, event, schedule, and firing identities.
- Add restart tests covering:
  - definition and revision persistence;
  - accepted submission persistence;
  - event replay;
  - schedule and firing persistence;
  - duplicate client submission using the same upstream idempotency key.
- Document backup inputs and provider-owned canonical data.
- Publish the exact PostgreSQL, driver, ETLantic, and migration versions tested.

### Explicit non-goals

- No ShuETL SQLModel tables.
- No inferred or automatically generated DDL.
- No destructive migration during application startup.
- No multi-tenant or high-availability claim.
- No exactly-once claim for external pipeline side effects.

### Exit gate

- [ ] A fresh database upgrades through provider-owned migrations.
- [ ] A database at every supported previous ShuETL pilot revision upgrades in
      integration tests.
- [ ] An incompatible or unknown schema prevents readiness.
- [ ] A committed submission remains visible after gateway restart.
- [ ] Idempotent resubmission returns the canonical upstream outcome.
- [ ] A canonical scheduled firing is created without a ShuETL scheduling loop.
- [ ] PostgreSQL integration tests run against a real server in CI.
- [ ] No production startup path calls `create_all()` or inferred migration
      generation.

---

## 0.5 — Secure Host Integration

### Outcome

Qualify authenticated, authorized single-tenant FastAPI deployments.

### Deliverables

- Accept a host FastAPI principal dependency through a stable ShuETL
  composition interface.
- Adapt trusted host identity into ETLantic's public
  `ControlPlaneContext`/principal contract for the supported release.
- Require a conforming ETLantic authorizer in production profiles.
- Define explicit development-only static or unauthenticated examples.
- Preserve upstream:
  - action/resource authorization;
  - authorization before existence-sensitive lookup;
  - opaque not-found behavior;
  - list filtering before pagination;
  - SSE connection and cursor authorization;
  - artifact metadata/access authorization;
  - fail-closed provider-outage behavior.
- Add OIDC/session integration examples in which the host validates credentials
  and ShuETL receives only the resulting trusted principal.
- Add cross-scope adversarial tests even though the first supported profile is
  single-tenant.
- Document the boundary between triggering identity and ETLantic execution
  identity.
- Verify that resolved pipeline secrets never enter the gateway or ShuETL
  diagnostics.

### Explicit non-goals

- No built-in user database, login UI, token issuer, role engine, or secret
  manager.
- No AuthMate dependency in core.
- No caller-selected tenant/workspace authority.
- No guarantee for mutually untrusted code in one process.

### Exit gate

- [ ] Production construction fails without a principal adapter and authorizer.
- [ ] Every mounted mutation has an authorization test.
- [ ] Enumeration tests cover direct lookup, lists, pagination, SSE, and
      artifact metadata.
- [ ] Policy/provider outages fail closed.
- [ ] Redaction tests cover validation errors, problem details, logs, events,
      readiness, and OpenAPI examples.
- [ ] Development authentication bypass is impossible under a production
      profile.
- [ ] Security limitations and the supported trust boundary are documented.

---

## 0.6 — Role-Separated Production Preview

### Outcome

Run the FastAPI gateway, ETLantic scheduler, and ETLantic worker as separate
supervised roles using one ShuETL installation.

### Deliverables

- Add process entry points such as:

  ```text
  shuetl serve --role gateway
  shuetl serve --role scheduler
  shuetl serve --role worker
  ```

  These commands configure and invoke upstream ETLantic roles.
- Ensure the production gateway never starts a local execution loop.
- Add role-specific configuration validation, health, readiness, and shutdown
  behavior.
- Provide container and ordinary process-supervisor examples using one
  version-pinned artifact.
- Exercise ETLantic's upstream lease, fencing, retry, cancellation, and recovery
  contracts through ShuETL's provider configuration.
- Add failure-injection scenarios:
  - gateway death before and after durable acceptance;
  - scheduler death around firing acceptance;
  - worker death before and after lease acquisition;
  - lease expiry and stale-worker completion;
  - cancellation in accepted, leased, and running states;
  - database disconnection and reconnection;
  - duplicate scheduler and worker startup.
- Document at-least-once execution and the need for sink idempotency or
  reconciliation when external effects cannot be transactional.
- Confirm that the SQL-only profile requires no message broker while retaining
  process isolation.

### Explicit non-goals

- No ShuETL scheduler, worker, lease, or retry implementation.
- No unrestricted distributed-execution claim.
- No forced process termination guarantee beyond the selected ETLantic runtime.
- No multi-region or disaster-recovery claim.

### Exit gate

- [ ] Two gateways can accept work without creating duplicate logical
      submissions.
- [ ] Two scheduler instances cannot create a second canonical firing.
- [ ] Two workers respect upstream leases and fencing.
- [ ] A stale worker cannot publish an authoritative terminal result after
      ownership changes.
- [ ] Graceful shutdown stops acceptance before process termination.
- [ ] The gateway remains responsive while worker processes execute representative
      ETL workloads.
- [ ] Every failure-injection result is mapped to a documented upstream state or
      diagnostic.
- [ ] The supported preview topology is reproducible from the deployment guide.

---

## 0.7 — Production Candidate Operability

### Outcome

Turn the 0.6 topology into a bounded, operable production candidate.

### Deliverables

- Expand `shuetl doctor` with role-to-role and provider readiness checks.
- Publish structured logging and correlation guidance across gateway,
  scheduler, worker, submission, attempt, event, and report identities.
- Package configuration presets for supported metrics and tracing integrations
  using upstream hooks.
- Qualify SSE deployment behavior:
  - proxy buffering;
  - keep-alives;
  - connection duration and count limits;
  - graceful shutdown;
  - resume cursors;
  - retention gaps;
  - authentication expiry and reauthorization.
- Complete migration, backup, restore, upgrade, and rollback runbooks.
- Test a restore into a clean environment and reconcile restored control-plane
  state.
- Test rolling upgrades within the explicitly supported upstream compatibility
  window.
- Measure and publish a bounded capacity envelope for:
  - gateway submission latency;
  - list/pagination behavior;
  - SSE connections;
  - scheduler firing throughput;
  - worker claim throughput;
  - database connection use.
- Add incident runbooks for provider outage, schema mismatch, stuck work,
  abandoned attempts, event retention gaps, and failed rollback.
- Publish a support matrix separating Supported, Experimental, and
  adopter-owned behavior.

### Explicit non-goals

- No formal SLA.
- No unbounded-scale claim.
- No automatic repair of unknown external side effects.
- No support for provider combinations absent from the published matrix.

### Exit gate

- [ ] Backup and restore drills preserve canonical ETLantic identities.
- [ ] Upgrade and rollback drills have recorded evidence.
- [ ] Proxy/SSE tests pass in the reference deployment.
- [ ] Capacity limits are measured, documented, and enforced or fail closed.
- [ ] Readiness detects database, schema, authorizer, and execution-role
      failures.
- [ ] No unresolved critical/high security or durability finding remains for the
      named reference profile.
- [ ] Operator documentation covers startup, shutdown, migration, recovery,
      retention, and incident response.

---

## 0.8 — Compatibility and Ecosystem Integration Preview

### Outcome

Expand integration value without changing ShuETL's semantic boundary or
destabilizing the 0.7 reference profile.

### Core deliverables

- Add a second explicitly tested ETLantic minor train if compatibility is
  feasible without a shadow abstraction layer.
- Publish deprecation and compatibility-adapter rules.
- Add automated upstream OpenAPI and contract-diff checks.
- Add provider-profile templates for selected upstream capabilities, such as:
  - external execution hosts;
  - broker-backed durable providers;
  - cloud artifact/reference providers;
  - orchestration integrations;
  - additional supported relational configurations.
- Label every new provider profile Supported, Experimental, or adopter-owned
  independently.

### Optional ecosystem adapters

When the corresponding peer package is implemented and compatible:

- `shuetl[authmate]` adapts AuthMate identity/credential capabilities into
  public ETLantic contracts.
- `shuetl[hedron]` provides operator-facing views that consume authoritative
  ETLantic services/API responses.
- Observability extras package configuration for supported ETLantic metadata and
  telemetry providers.

### Adapter requirements

Every optional adapter must:

- use public APIs only;
- declare exact compatibility ranges;
- remain absent from core imports;
- preserve ETLantic identity, authorization, and redaction;
- include clean-install and integration tests;
- fail clearly when requested but unavailable;
- avoid redefining control-plane truth in a UI or adapter database.

### Explicit non-goals

- No requirement that AuthMate or Hedron exist for core ShuETL.
- No UI-only authorization.
- No generic plugin system duplicating ETLantic discovery.
- No promise that experimental adapters are covered by the baseline production
  profile.

### Exit gate

- [ ] The 0.7 reference profile remains backward-compatible.
- [ ] Contract-diff automation detects upstream breaking changes.
- [ ] Every shipped adapter has an independent capability and maturity label.
- [ ] Optional extras do not alter core import dependencies.
- [ ] AuthMate/Hedron adapters ship only if their public contracts and
      integration tests are available.
- [ ] New provider profiles reuse upstream records without lossy translation.

---

## 0.9 — Public Contract Freeze and 1.0 Release Candidate

### Outcome

Freeze ShuETL's application-facing integration contract and demonstrate that the
bounded reference deployment is ready for a 1.0 decision.

### Contract freeze

Freeze and document:

- `ShuETL` construction and provider injection;
- `ShuETLSettings` fields, precedence, and redaction;
- mount and dedicated-application behavior;
- lifespan-composition contract;
- deployment-profile and process-role names;
- capability/readiness diagnostic schema;
- CLI commands and exit codes;
- compatibility and deprecation policy;
- optional-adapter loading behavior.

ETLantic domain and HTTP contracts remain upstream-owned and are referenced by
supported version range rather than copied into the ShuETL stability promise.

### Qualification work

- Run clean-install tests for every supported extra.
- Test supported Python and FastAPI versions at the lower and upper bounds.
- Test every supported ETLantic package combination.
- Freeze OpenAPI parity evidence for the reference profile.
- Repeat security, failure-injection, backup/restore, upgrade/rollback, SSE, and
  capacity campaigns from earlier releases.
- Audit dependencies, licenses, package metadata, type information, and
  supply-chain publication.
- Publish a complete operator guide and a minimal application-developer guide.
- Publish a migration guide from every supported 0.x public surface.
- Remove deprecated experimental APIs that will not enter 1.0.
- Record all residual risks and adopter-owned responsibilities.

### Explicit non-goals

- No new major features.
- No late addition of domain models or persistence tables.
- No expansion to unqualified providers or topologies.
- No claim broader than the tested support matrix.

### Exit gate

- [ ] The public ShuETL contract is frozen with a documented compatibility
      policy.
- [ ] The reference profile passes clean-install, integration, security,
      failure-injection, recovery, and capacity gates.
- [ ] All supported provider migrations and rollback paths are documented and
      exercised.
- [ ] No unresolved critical/high finding remains.
- [ ] Optional adapters cannot weaken the baseline profile.
- [ ] Documentation clearly distinguishes ShuETL-owned behavior from exposed
      ETLantic behavior.
- [ ] The merge-versus-separate package decision is reviewed one final time.
- [ ] A 1.0 release record names the exact supported deployment envelope.

Failure of a mandatory gate results in another 0.9.x release or a scope
reduction, not a weakened 1.0 claim.

---

## Cross-cutting workstreams

These tracks run through the release train but do not independently authorize a
support claim.

### Compatibility

- Maintain a machine-readable package compatibility matrix.
- Pin one ETLantic minor train initially.
- Test lower and upper supported bounds.
- Reject unsupported mixed ETLantic package versions at construction/startup.
- Use upstream contract and OpenAPI diffs to assess upgrades.
- Prefer narrow version-specific adapters over permanent abstraction copies.

### Security

- Keep production identity and authorization fail closed.
- Preserve upstream non-enumeration and scope behavior.
- Redact credentials and secret-like values in every ShuETL-owned output.
- Treat installed Python extensions as trusted code selected by operators.
- Keep mutually untrusted execution outside the gateway process.
- Review every optional adapter independently.

### Durability and recovery

- Test upstream guarantees through the composed system.
- Preserve idempotency, lease, fencing, attempt, event, and effect identities.
- Never equate durable submission with exactly-once external effects.
- Exercise restarts and failure boundaries continuously after 0.4.
- Keep migration, backup, restore, and rollback evidence current.

### Developer experience

- Maintain a clean-install quickstart.
- Keep the minimal path concise without hiding production requirements.
- Provide typed settings, useful diagnostics, and actionable errors.
- Test examples as executable artifacts.
- Keep local defaults explicit and clearly labeled.

### Operations

- Treat gateway, scheduler, and worker as distinct roles.
- Expose role-appropriate health and readiness.
- Document resource bounds and graceful shutdown.
- Preserve correlation across canonical ETLantic identities.
- Maintain runbooks alongside behavior changes.

### Documentation

Every release documents:

- maturity and supported profiles;
- owned versus upstream-provided behavior;
- dependencies and compatibility;
- new and changed public surfaces;
- migration and rollback actions;
- security and operational limitations;
- known residual risks.

## Release-wide definition of done

Every 0.x release must:

- pass formatting, typing, unit, integration, and clean-install tests relevant to
  its scope;
- build wheel and source distributions;
- verify imports with optional extras absent;
- publish a compatibility statement;
- update the feature ownership matrix;
- update security and deployment limitations;
- include upgrade notes from the previous minor;
- avoid undocumented changes to the supported OpenAPI surface;
- leave the repository with no unexplained duplicate ETLantic contract.

## 1.0 graduation target

Version 1.0 should mean:

- ShuETL has a stable, narrow composition API;
- the named PostgreSQL gateway/scheduler/worker profile is reproducibly
  deployable and operationally qualified;
- security, durability, recovery, and compatibility claims match evidence;
- ETLantic remains the sole semantic authority;
- users gain a materially simpler FastAPI deployment experience without
  acquiring a second control plane.

The goal is not maximum feature count. The goal is a trustworthy integration
boundary.
