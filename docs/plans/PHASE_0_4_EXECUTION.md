# Phase 0.4 — Architecture and Implementation Plan

## Plan status

- Status: Implemented and locally qualified
- Target release: `0.4.0`
- Baseline release: `v0.3.0`
- Baseline release commit: `f5806beedaa5545061279347125a609c26665c7b`
- Planning source commit: `f5806beedaa5545061279347125a609c26665c7b`
- Planning date: 2026-09-11
- Implementation qualification date: 2026-09-13
- Supported Python: 3.11, 3.12, and 3.13
- Qualified PostgreSQL target: PostgreSQL `18.6`
- Qualified driver target: `psycopg==3.3.5` with
  `psycopg-binary==3.3.5`
- Qualified upstream train: `etlantic==0.52.1`,
  `etlantic-fastapi==0.52.1`, and `etlantic-sqlmodel==0.52.1`
- Previously blocking upstream issues, now closed and verified:
  [ETLantic #131](https://github.com/eddiethedean/etlantic/issues/131) and
  [ETLantic #132](https://github.com/eddiethedean/etlantic/issues/132)

This document is the implementation contract for Phase 0.4. It resolves
ShuETL's architecture and public behavior against the published 0.52.0 train;
the migration head and runtime behavior below were requalified on a real
PostgreSQL 18.6 server.

### Authorized patch-train requalification

The final release check found FINAL-001 (byte-valued URL error disclosure) and
FINAL-002 (workspace firing identity collision). The user authorized publishing
the upstream correction and qualifying the 0.52.1 patch train. Current dependency
requirements below therefore use 0.52.1; references to original 0.52.0 inspection
and review evidence remain historical. Scope, public API, migration head, AC IDs,
runtime support, and ownership boundaries are unchanged. Schedule and durable
submission deduplication must return the canonical occurrence within the caller's
tenant/workspace, without returning another workspace's firing.

## Architecture summary

Phase 0.4 adds one explicit, controlled PostgreSQL gateway profile beside the
0.3 local profiles. It composes public ETLantic relational stores over one
caller-independent SQLAlchemy engine and continues to expose the authoritative
upstream HTTP surface through the existing ShuETL facade.

```text
SHUETL_* / explicit kwargs
            |
            v
      ShuETLSettings
  postgresql-pilot + gateway
  host identity + complete routes
            |
            v
  PostgreSQLProviderBundle
            |
            +-- SqlModelRegistryProvider
            |       `-- RegistryDefinitionRepository
            +-- SQLModelSubmissionStore
            +-- SqlModelEventStore
            +-- SQLModelDurableWorkStore
            `-- SQLModelScheduleStore
            |
            v
  upstream ETLanticAPI(profile="production")
            |
            v
       ShuETL facade
            |
            v
       FastAPI gateway

operator -----------------> shuetl database upgrade
                                  |
                                  v
                     provider-owned migration API

doctor / bundle startup ---> read-only connection + schema checks
                             never migration or inferred DDL
```

Ownership remains strict:

- ETLantic owns definitions, revisions, submission/idempotency semantics,
  events, durable work, schedules, firings, protocols, and domain identities.
- `etlantic-fastapi` owns routes, schemas, errors, authorization ordering, and
  live API readiness.
- `etlantic-sqlmodel` owns relational tables, migrations, transactions, and
  store behavior.
- ShuETL owns configuration validation, exact dependency qualification, engine
  construction, graph wiring, read-only preflight, an explicit migration CLI,
  resource cleanup, and operational documentation.
- The host owns authentication, principal/context adapters, authorization
  policy, application supervision, credentials, TLS trust material, and backup
  execution.

[ADR-0010](../adr/0010-postgresql-pilot-and-migration-boundary.md) governs the
PostgreSQL driver, configuration, and migration boundary.

## Repository and upstream ground truth

The plan is based on the released 0.3 repository and live inspection of the
published upstream packages and a real PostgreSQL server.

| Concern | Verified ground truth |
|---|---|
| ShuETL baseline | `0.3.0`; clean `main`; Python `>=3.11,<3.14` |
| Existing facade | `ShuETL(api=...)`, mount/app modes, lifecycle composition, and upstream router preservation |
| Existing profiles | Required `local` profile with `memory` or file-backed `sqlite`; gateway and host identity only |
| Existing diagnostics | Deterministic, redacted `shuetl.doctor/1`; fixed check IDs; SQLite schema inspection is read-only |
| Qualified upstream train | Exact 0.52.0 ETLantic packages; SQLAlchemy 2.0.52 |
| Public relational stores | Registry, submission, event, durable-work, and schedule stores accept a SQLAlchemy `Engine` |
| Definition revisions | `ETLanticAPI.with_registry_definitions()` uses public `RegistryDefinitionRepository` over the registry provider |
| Migration API | Public `etlantic_sqlmodel.migrations.upgrade()` and `VERSIONS`; current head is `005_cp1_reference` |
| Migration inspection hazard | Public `current_version()` creates and commits the version table on a fresh database; it is not suitable for readiness inspection |
| PostgreSQL construction | Store constructors are dialect-neutral; no public PostgreSQL-named engine helper exists, so direct SQLAlchemy `create_engine()` is the supported seam |
| Schedule wiring | A relational schedule store is allowed with the upstream production profile and can atomically claim a firing with the durable store when both share an engine |
| Reports/artifacts | No required relational report or artifact metadata store exists in the inspected 0.52.0 graph; those optional API providers remain absent |
| Current quality gates | Lock, sync, Ruff, Pyright, boundaries, pytest, build, artifacts, OpenAPI, clean-wheel, and evidence checks on Python 3.11–3.13 |
| Live server spike | PostgreSQL 18.6 accepted the driver, migrations, and registry/durable/schedule store construction |

### Resolved upstream qualification evidence

The 0.52.0 provider train resolves the previously blocking findings:

1. On a fresh PostgreSQL 18.6 database,
   `etlantic_sqlmodel.migrations.upgrade()` reports head
   `005_cp1_reference` creates `cp_submissions` and `cp_events`; real
   submission acceptance and event replay succeed. This closes ETLantic #131.
2. Twenty concurrent event appends to one tenant/workspace from 10 independent
   connections committed with unique sequences and replayed in order, with no
   raw integrity errors. This closes ETLantic #132.

## Change boundary

### Problem

ShuETL 0.3 can compose memory and SQLite development providers but cannot make
a production durability claim. Operators lack a qualified PostgreSQL extra, a
complete relational ETLantic graph, an explicit migration command, remote
connectivity/schema diagnostics, and restart evidence for upstream identities.

### Desired outcome

After the upstream blockers are resolved and Phase 0.4 is implemented, an
operator can provision a supported PostgreSQL database explicitly, run a
single-tenant gateway using host identity and authorization, restart it without
losing required control-plane state, diagnose connection/schema incompatibility
without mutation, and rely on upstream canonical identities for definitions,
submissions, events, schedules, and firings.

### In scope

- A `postgresql-pilot` settings profile paired only with provider `postgresql`,
  role `gateway`, identity `host`, and route preset `complete`.
- A `shuetl[postgresql]` extra with an exact qualified
  `etlantic-sqlmodel`, SQLAlchemy, Psycopg, and binary implementation set.
- Validated `postgresql+psycopg` URLs, bounded connection timeout, and an
  explicit TLS mode whose secure default is `verify-full`.
- A public `PostgreSQLProviderBundle` using exact upstream interfaces and one
  SQLAlchemy engine.
- Relational registry-backed definitions/revisions, CP1 submissions, events,
  durable work, schedules, and firings.
- Upstream production profile selection for the composed `ETLanticAPI`.
- Read-only database connectivity, migration-head, and required-table checks in
  bundle construction and `shuetl doctor`.
- An explicit `shuetl database upgrade` command that invokes only the pinned
  provider migration API and never runs during gateway startup.
- Fresh and prior-head upgrade tests on real PostgreSQL.
- Restart, idempotency, event replay, schedule/firing, and concurrency tests.
- PostgreSQL CI, clean-wheel qualification, exact compatibility metadata, and
  Phase 0.4 evidence.
- Operator documentation covering TLS, provisioning, failure recovery,
  canonical data, backup inputs, restore verification, and pilot limitations.

### Touched surface

Implementation is expected to touch only:

- `src/shuetl/settings.py`
- `src/shuetl/providers.py`, or a narrowly split PostgreSQL provider module
- `src/shuetl/compatibility.py`
- `src/shuetl/diagnostics.py`
- `src/shuetl/cli.py`
- `src/shuetl/errors.py` only if a migration-specific subclass is necessary
- `src/shuetl/__init__.py`
- `pyproject.toml` and `uv.lock`
- focused unit, integration, migration, contract, CLI, security, concurrency,
  and compatibility tests
- PostgreSQL test infrastructure and `.github/workflows/checks.yml`
- release/evidence scripts required to qualify the new extra
- one PostgreSQL example and the README/operator documentation
- `CHANGELOG.md` and `docs/evidence/0.4/`

No ETLantic domain model, route, SQLModel table, migration revision, scheduler,
worker, executor, identity implementation, or result/artifact store belongs in
this surface.

## Public contract

### Required behavior

The contracts in this section, the invariants, and AC-001 through AC-038 are
required. An implementation may adapt private module layout but may not change
observable behavior or assume stronger semantics than the qualified upstream
providers demonstrate.

### Public exports

All 0.3 exports remain. Phase 0.4 adds exactly:

```python
from shuetl import PostgreSQLProviderBundle
```

`PostgreSQLProviderBundle` exposes upstream protocol-typed objects; it does not
introduce ShuETL domain wrappers. Migration helpers and engine builders remain
private because the supported operator surface is the CLI.

### Settings contract

`ShuETLSettings` retains its frozen, extra-forbidden, constructor-then-uppercase
environment precedence and gains these vocabulary extensions:

| Field | Phase 0.4 type/default | Required behavior |
|---|---|---|
| `profile` | `Literal["local", "postgresql-pilot"]`, required | No implicit profile. |
| `provider` | `Literal["memory", "sqlite", "postgresql"]`, required | Named built-ins only. |
| `postgresql_sslmode` | `Literal["verify-full", "verify-ca", "require", "disable"]`, default `"verify-full"` | Used only by PostgreSQL; `disable` is an explicit insecure opt-in. |

All existing fields and defaults otherwise remain unchanged. Exact valid
combinations are:

| Profile | Provider | Database URL | TLS field |
|---|---|---|---|
| `local` | `memory` | forbidden | must remain default and is ignored |
| `local` | `sqlite` | required file URL | must remain default and is ignored |
| `postgresql-pilot` | `postgresql` | required network URL | applied explicitly |

Every other profile/provider combination fails Pydantic validation. Role remains
`gateway`; identity remains `host`; route preset remains `complete`.

For PostgreSQL, `database_url` must:

- use exactly `postgresql+psycopg`;
- contain a non-empty username, host, and one database name;
- optionally contain a password and port;
- contain no fragment or query string;
- remain a `SecretStr`, excluded from repr, dumps, errors, reports, logs, and
  evidence.

TLS certificate and key material are supplied through the operator's libpq
trust configuration. ShuETL passes the selected `sslmode` explicitly and never
loads or serializes certificate contents. The existing finite timeout range
`0.1 <= value <= 30.0` remains and is rounded up to a Psycopg integer
`connect_timeout`, so the configured upper bound is never shortened.

`database_driver` returns `None`, `"sqlite"`, or `"psycopg"` according to the
selected provider. Existing local settings behavior remains otherwise
compatible.

### Dependency and compatibility contract

The PostgreSQL extra is exactly:

```toml
postgresql = [
  "etlantic-sqlmodel==0.52.1",
  "sqlalchemy==2.0.52",
  "psycopg[binary]==3.3.5",
]
```

The lock must contain `etlantic-sqlmodel==0.52.1`, `psycopg==3.3.5`, and `psycopg-binary==3.3.5`. Binary
Psycopg is an intentional pilot deployment choice for reproducible wheels; a
future system-libpq packaging option requires separate qualification.

`validate_postgresql()` must validate every exact distribution
before importing provider or driver modules. Missing or mismatched packages
raise a redacted `CapabilityError` or `CompatibilityError` with the exact
remediation `pip install "shuetl[postgresql]==0.4.0"`; no memory/SQLite fallback
is allowed.

PostgreSQL `18.6` is the reference server. CI and evidence must record the
actual `SHOW server_version` result. No compatibility claim is made for another
PostgreSQL major or minor in 0.4.

### PostgreSQL provider bundle

```python
PostgreSQLProviderBundle.create(
    settings,
    *,
    authorizer: Authorizer,
    context_factory: ContextFactory,
    principal_dependency: PrincipalDependency,
) -> PostgreSQLProviderBundle
```

Construction requires an exact `ShuETLSettings` instance for the
`postgresql-pilot` matrix and the same explicit, conforming host objects as the
0.3 local bundle. It performs these steps in order:

1. validate the core and PostgreSQL package set without importing unavailable
   optional packages;
2. construct one synchronous SQLAlchemy engine with `pool_pre_ping=True`, the
   bounded Psycopg timeout, and explicit SSL mode;
3. open a connection and verify the server reports exact PostgreSQL `18.6`;
4. inspect migration state and the minimum required table inventory without any
   DDL, commit, migration call, or application startup;
5. require the exact qualified migration head;
6. construct one `SqlModelRegistryProvider`;
7. use public `RegistryDefinitionRepository` over that registry for definitions;
8. construct exact public `SQLModelSubmissionStore`, `SqlModelEventStore`,
   `SQLModelDurableWorkStore`, and `SQLModelScheduleStore` instances using the
   same engine;
9. construct the exact upstream `ETLanticAPI` with the caller objects,
   `profile="production"`, registry-backed definitions, durable work, and the
   schedule store;
10. return the bundle only after every check succeeds.

The bundle exposes `settings`, `api`, `authorizer`, `registry`, `definitions`,
`submissions`, `events`, `durable_work`, `schedules`, `provider` equal to
`"postgresql"`, and `development_only` equal to `False`. Store values satisfy
the authoritative runtime-checkable ETLantic protocols and are the same objects
in the `ETLanticAPI` graph.

No history, governance, report, artifact, broker, or execution provider is
invented. Optional upstream routes continue to use their documented unavailable
behavior when a provider is absent.

The caller owns the returned bundle and calls `close()`. Cleanup disposes the
engine once, is thread-safe and idempotent, does not migrate, and does not delete
data. Every construction failure after engine creation also disposes it once.
The existing `ShuETL(api=...)` facade never discovers or closes a bundle.

### Schema inspection contract

Readiness must not call the provider `current_version()` implementation,
because that function writes a version table on fresh databases. ShuETL may use
SQLAlchemy inspection and a static parameter-free `SELECT` against the
provider-owned version table as a private compatibility adapter.

For PostgreSQL, schema inspection occurs on one transaction explicitly marked
read-only and returns only bounded classifications:

- `fresh`: version table absent;
- `behind`: recognized earlier provider head;
- `head`: exact qualified head and all minimum required tables present;
- `ahead_or_unknown`: unrecognized version;
- `corrupt`: missing/multiple/malformed version row or head with missing tables;
- `unreachable`: connection/authentication/TLS/timeout failure.

Only `head` is ready. Error text may name the classification and required head,
but never the URL, host, port, database, username, password, certificate path,
raw SQL, raw driver exception, or engine/store repr.

The minimum table inventory is taken from the exact qualified provider release
and includes the tables required by registry definitions, CP1 submissions,
events, durable work, schedules/firings, and the migration version. Additional
provider-owned tables do not fail readiness.

### Migration command

The sole new command is:

```text
shuetl database upgrade
```

It loads normal `ShuETLSettings` and is valid only for the
`postgresql-pilot`/`postgresql` matrix. It validates exact package compatibility,
constructs an engine with the same timeout/TLS rules, invokes the pinned public
`etlantic_sqlmodel.migrations.upgrade(engine)` once, verifies the returned and
read-back head plus required tables, and disposes the engine.

- Fresh and recognized earlier heads upgrade forward to the qualified head.
- Repeating the command at head is a successful no-op.
- Unknown/ahead/corrupt state fails closed; no downgrade, repair, reset, target
  override, SQL generation, or destructive option is exposed.
- Success writes one bounded line naming only the resulting migration head to
  stdout and exits `0`.
- Expected configuration, capability, connection, schema, or migration failure
  writes one redacted line to stderr and exits `1`.
- Argument/usage errors exit `2`.
- Gateway bundle construction, `ShuETL.mount()`, lifespan, application factory,
  and `doctor` never call this command or any migration/table-creation API.

Provider migration transaction and rollback semantics remain upstream-owned.
If a migration fails partially, the command reports failure and subsequent
readiness remains failed until an operator follows provider recovery guidance.

### Doctor and readiness contract

`DoctorReport` remains schema `shuetl.doctor/1`; its public fields and existing
check IDs/order remain unchanged. PostgreSQL extends values rather than adding a
parallel report or HTTP endpoint:

- `development_only` is `False`;
- `database_driver` is `"psycopg"`;
- configured capabilities add registry/revisions, durable work, schedules, and
  firings;
- available capabilities add `provider.postgresql` only when the exact extra is
  installed;
- `versions` includes the exact SQLModel, SQLAlchemy, Psycopg, Psycopg binary,
  and connected PostgreSQL server versions;
- `provider.ready` reports the bounded connectivity/server result;
- `provider.schema` reports migration-head and required-table compatibility;
- `topology.development_only` passes with a bounded controlled-pilot summary
  instead of the local warning.

Inspection starts no app, runs no pipeline, installs no package, changes no
schema, and makes no write. A settings/bundle mismatch fails as in 0.3. The live
upstream `/ready` route remains authoritative for the constructed API; ShuETL's
bundle gate ensures an incompatible database cannot reach serving state.

### Recommended implementation

- Split private engine/schema helpers into a small PostgreSQL-focused module if
  that keeps `providers.py` and `diagnostics.py` readable.
- Share one private schema-inspection result between doctor and bundle creation
  so the same classifications cannot drift.
- Import PostgreSQL-only distributions inside capability-validated paths.
- Exercise migration logic through the CLI-facing private function in tests;
  do not add a second public Python migration API.
- Use barrier-controlled concurrency tests with independent connections and
  bundle instances, rather than relying on one process lock.

These recommendations are subordinate to the required behavior.

## Invariants

1. ShuETL owns no ETLantic domain table, migration, model, identity, or route.
2. No startup, bundle, doctor, mount, or lifespan path mutates schema.
3. No PostgreSQL bundle exists unless dependencies, server, head, and required
   tables are exactly qualified.
4. Every exposed store and API field is the canonical upstream object over one
   engine; no semantic adapter or shadow repository is inserted.
5. Definition reads resolve registry revisions, not a separate mutable
   definition table.
6. A repeated same-scope/same-operation/same-key submission returns the same
   upstream canonical receipt; a different payload conflicts.
7. Event IDs, sequences, and cursors remain unique, ordered, replayable, and
   durable after restart under concurrent gateway traffic.
8. Schedule and firing identities are upstream-generated and persist after
   restart; ShuETL runs no scheduling loop.
9. Tenant/workspace/principal context continues to come from host adapters and
   ETLantic authorization runs before protected store access.
10. Database secrets and connection coordinates never enter public models,
    errors, diagnostics, logs, evidence, or reprs.
11. Engine cleanup is exactly once for success, failure, cancellation, and
    repeated close paths.
12. Memory, SQLite, caller-built API, mount, OpenAPI, handler, and lifecycle
    contracts from 0.2/0.3 remain compatible.

## Edge cases and failure modes

| Case | Required result |
|---|---|
| Missing profile/provider/identity/role | Validation failure; no default pilot or engine |
| Wrong profile/provider pairing | Validation failure before optional imports |
| Missing PostgreSQL extra | `CapabilityError`; exact install remediation; no fallback |
| Wrong package train | `CompatibilityError` before driver/provider import |
| Invalid URL scheme, missing host/user/database, query, or fragment | Redacted validation failure |
| TLS/auth/DNS/refusal/timeout | Bounded unreachable failure; raw driver detail retained only as chained cause |
| PostgreSQL version other than 18.6 | Readiness failure; no graph returned |
| Fresh database | Doctor/readiness fail without writes; explicit upgrade may provision |
| Recognized older head | Readiness fail; explicit upgrade may advance |
| Unknown/ahead/corrupt head | Readiness and upgrade fail closed; never downgrade or repair |
| Head with missing required table | Corrupt/incompatible failure even when version text matches |
| Repeated upgrade at head | Success without destructive work |
| Migration interruption/partial failure | Redacted failure, engine disposal, subsequent readiness failure |
| Same idempotency key and payload after restart | Same canonical upstream outcome |
| Same idempotency key with changed payload | Upstream conflict; no second acceptance |
| Concurrent same-key submissions | One canonical acceptance; all successful duplicates resolve to it |
| Concurrent event appends | Unique durable ordered events; no raw database exception |
| Unknown event cursor | Preserve upstream gone/error contract |
| Schedule/firing replay after restart | Same upstream IDs and nominal fire identity |
| Bundle creation cancelled or fails | No returned partial graph; engine disposed once |
| Close called repeatedly/concurrently | Harmless; one disposal |

## Security and reliability

- `verify-full` is the default. `disable`, `require`, and `verify-ca` require an
  explicit setting and must be visible by mode name in diagnostics without
  revealing trust material.
- Documentation labels `disable` as CI/local-network-only and does not show it
  as a production default.
- URL validation is structural and never interpolates connection data into SQL,
  errors, commands, or logs.
- Schema queries use fixed provider-owned identifiers. No configuration value is
  accepted as a schema/table/column name.
- Migration is an operator action with database privileges; gateway
  documentation recommends a runtime role without schema-change privileges.
- Connection timeout is bounded and pool liveness is checked. No retry loop can
  make startup unbounded.
- Schema checks run in a read-only transaction. PostgreSQL catalog/version reads
  must demonstrate zero writes on fresh and provisioned databases.
- Concurrent verification uses independent database connections so process-local
  serialization cannot create false confidence.
- ShuETL makes no exactly-once claim for external effects. This phase proves
  control-plane identity/idempotency only.
- Backups must include all provider-owned tables and the migration version table
  in a transactionally consistent PostgreSQL dump. Configuration, credentials,
  TLS keys, external artifacts, and external side effects are separate operator
  inputs and are not canonical database data.
- Restore verification runs the same read-only compatibility check and restart
  probes before traffic is admitted.

## Compatibility

- Python 3.11, 3.12, and 3.13 remain supported.
- All exact ETLantic packages must share one qualified train; mixed trains fail
  before serving traffic.
- Existing top-level names retain import paths and behavior; the new bundle is
  additive.
- Existing settings inputs remain valid. Only the new explicit profile/provider
  matrix selects PostgreSQL.
- `shuetl.doctor/1` remains the schema identifier and local report shape/content
  remains unchanged for equivalent 0.3 configurations.
- The complete mounted route set, OpenAPI operation IDs/schema references,
  request/response bodies, statuses, errors, SSE cursor semantics, and auth order
  remain upstream-owned.
- Memory and SQLite remain development-only and receive no durability upgrade or
  PostgreSQL dependency.
- There is no persisted ShuETL 0.3 PostgreSQL schema to migrate. Nevertheless,
  every provider head published by the qualified chain is an upgrade fixture.
- The `0.4.0` release does not claim compatibility with databases provisioned by
  `create_control_plane_tables()` or other demo-only/inferred DDL paths unless
  the upstream provider explicitly supplies and tests that migration path.

## Acceptance criteria

| ID | Observable acceptance criterion |
|---|---|
| AC-001 | Project and wheel metadata report `0.4.0`, Python 3.11–3.13, the exact qualified core train, and exact PostgreSQL extra including Psycopg 3.3.5 binary. |
| AC-002 | PostgreSQL 18.6 is the only claimed server and the executed server version is recorded in CI/evidence. |
| AC-003 | All 0.3 public exports remain and source/wheel expose exactly the added `PostgreSQLProviderBundle`. |
| AC-004 | Settings accept exactly the three documented profile/provider combinations and never select PostgreSQL implicitly. |
| AC-005 | PostgreSQL URLs and TLS mode validate exactly as specified; invalid or secret-bearing errors contain no connection value or coordinate. |
| AC-006 | Exact core/PostgreSQL versions are validated before optional imports or engine construction; missing/mismatched extras fail with the documented remediation and no fallback. |
| AC-007 | Bundle construction requires the exact pilot settings and explicit conforming host authorizer, context factory, and principal dependency. |
| AC-008 | A qualified bundle contains exact upstream registry, registry-backed definition, submission, event, durable-work, schedule, and API objects over one engine. |
| AC-009 | The API retains caller objects, uses upstream production profile, and exposes registry/durable/schedule providers without adding report/artifact/governance/execution providers. |
| AC-010 | Fresh, behind, unknown/ahead, corrupt, wrong-server, and unreachable databases produce the documented redacted readiness failures and no bundle. |
| AC-011 | Exact head plus every required provider table is necessary and sufficient for database readiness. |
| AC-012 | Bundle construction, doctor, gateway startup, mount, app factory, and lifespan perform zero schema/table/version writes and invoke no migration/create-all API. |
| AC-013 | Every construction failure disposes its engine once; successful bundle close is thread-safe, explicit, and idempotent. |
| AC-014 | `shuetl database upgrade` alone performs provider migrations with exact stdout/stderr and exit 0/1/2 behavior. |
| AC-015 | Fresh PostgreSQL upgrades to the qualified head solely through the public provider migration API and has every required table/constraint. |
| AC-016 | Every recognized earlier provider head upgrades to the qualified head without losing seeded canonical data. |
| AC-017 | Repeating upgrade at head is a successful no-op; unknown/ahead/corrupt state is never downgraded, reset, repaired, or overwritten. |
| AC-018 | A registry-backed definition and at least two immutable revisions remain readable with the same logical/revision IDs after engine and gateway restart. |
| AC-019 | A committed CP1 submission remains readable after restart and preserves acceptance, submission, run, and definition identities. |
| AC-020 | Same-scope same-key same-payload submission before/after restart returns one canonical upstream outcome; changed payload returns upstream conflict. |
| AC-021 | Barrier-controlled concurrent same-key submissions through independent connections produce one durable canonical acceptance and no raw database exception. |
| AC-022 | Events appended before restart replay from the beginning and a persisted cursor with the same IDs, sequences, order, payload, and scope. |
| AC-023 | Barrier-controlled concurrent same-scope event appends all persist with unique ordered sequences/cursors and expose no raw SQLAlchemy/Psycopg exception. |
| AC-024 | A schedule and canonical firing created through upstream API/store behavior persist with the same identities after restart without a ShuETL scheduler loop. |
| AC-025 | Duplicate schedule firing claim returns the canonical upstream firing and does not create a second durable submission. |
| AC-026 | Mounted PostgreSQL endpoints preserve upstream authorization order, request/response schemas, statuses, errors, idempotency, SSE, operation IDs, and schema refs. |
| AC-027 | Doctor keeps `shuetl.doctor/1`, existing fields/check IDs/order, and reports truthful pilot capabilities, package/server versions, connection, schema, and non-development topology. |
| AC-028 | Doctor text/JSON contain equivalent bounded facts and neither performs writes nor reveals credentials, coordinates, paths, TLS material, SQL, reprs, or raw exceptions. |
| AC-029 | Database backup/restore of provider-owned canonical tables preserves the AC-018 through AC-025 identities and passes readiness before traffic. |
| AC-030 | Existing memory, SQLite, caller-built API, mount, lifecycle, handler, OpenAPI, CLI, and doctor compatibility suites remain green. |
| AC-031 | Static boundaries find no ShuETL domain model, table, migration, store wrapper, route, scheduler, worker, executor, anonymous identity, or startup DDL. |
| AC-032 | Core, SQLite, and PostgreSQL clean-wheel installs contain only their declared dependencies and all public imports resolve from the wheel. |
| AC-033 | Real PostgreSQL integration tests run in CI on Python 3.11, 3.12, and 3.13 using the exact locked server/driver/provider set. |
| AC-034 | Ruff, Pyright, boundary, unit, integration, migration, concurrency, build, artifact, OpenAPI, clean-wheel, redaction, and evidence gates pass. |
| AC-035 | Documentation states exact setup, TLS, privileges, migration, readiness, cleanup, backup/restore, canonical data, and pilot limitations and contains executable wheel-based examples. |
| AC-036 | The Phase 0.4 evidence index maps every AC exactly once to passing proof and contains no secret or machine-specific path. |
| AC-037 | The qualified 0.52.1 provider train provisions submission/event tables through production migrations and upgrades preserve data. |
| AC-038 | The qualified 0.52.1 provider train provides a supported, tested concurrent event-append outcome meeting AC-023. |

## Verification matrix

| AC | Preferred proof |
|---|---|
| AC-001 | Packaging / Compatibility — source, lock, wheel, and isolated metadata assertions |
| AC-002 | Integration / Artifact — `SHOW server_version` against the pinned CI service |
| AC-003 | Contract / Compatibility — exact `__all__` and installed-wheel import snapshot |
| AC-004 | Unit / Property — full profile/provider/database/TLS combination table |
| AC-005 | Unit / Security — URL boundary table plus sentinel scans of all failure surfaces |
| AC-006 | Compatibility / Static — package metadata and optional-import/engine spies |
| AC-007 | Unit / Type — valid identity preservation and invalid-input construction ordering |
| AC-008 | Integration / Contract — exact upstream runtime types, protocol checks, object/engine identity |
| AC-009 | Integration / Contract — exact `ETLanticAPI` field and production-profile assertions |
| AC-010 | Integration / Failure injection — real server/auth/TLS/version/schema state matrix |
| AC-011 | Migration / Property — head plus required-table inventory mutation matrix |
| AC-012 | Static / Integration — DDL/migration spies and PostgreSQL before/after catalog snapshots |
| AC-013 | Unit / Concurrency — disposal counters under failure, cancellation, and concurrent close |
| AC-014 | CLI / Integration — subprocess matrix over success and every bounded failure class |
| AC-015 | Migration / Integration — fresh real database to head, inventory, and constraints |
| AC-016 | Migration / Compatibility — seeded fixture at every published earlier head |
| AC-017 | Migration / Property — repeated head plus unknown/ahead/corrupt fixtures |
| AC-018 | Integration / Restart — registry definition and revision round trip across new engine |
| AC-019 | Integration / Restart — CP1 receipt/run identity round trip |
| AC-020 | Contract / Restart — same/different idempotency payload matrix |
| AC-021 | Concurrency / Integration — barrier-controlled duplicate submissions with independent stores |
| AC-022 | Integration / Restart — event replay from null and persisted cursors |
| AC-023 | Concurrency / Integration — barrier-controlled append and full replay count/order |
| AC-024 | Integration / Restart — API schedule plus store firing round trip, no loop spy |
| AC-025 | Contract / Concurrency — repeated firing claim and durable submission identity |
| AC-026 | Contract / Compatibility — normalized upstream/ShuETL HTTP and OpenAPI comparison |
| AC-027 | Unit / Contract — local golden reports plus PostgreSQL golden report |
| AC-028 | Security / Static — read-only audit and secret/coordinate sentinel scans |
| AC-029 | Migration / Manual integration — `pg_dump`/restore runbook exercised in CI or release evidence |
| AC-030 | Compatibility — complete immutable 0.2/0.3 suites |
| AC-031 | Static gate — prohibited import/symbol/call fixtures and runtime spies |
| AC-032 | Artifact / Integration — isolated core/SQLite/PostgreSQL wheel environments |
| AC-033 | CI / Integration — PostgreSQL service job across the supported Python matrix |
| AC-034 | Static gate / Integration — one-command release gate and CI workflow |
| AC-035 | Manual / Static — documentation-topic assertions and executable snippets |
| AC-036 | Artifact / Static — evidence coverage, hash, redaction, and path checker |
| AC-037 | Upstream contract / Migration — published release notes plus fresh/prior-head tests |
| AC-038 | Upstream contract / Concurrency — published fix plus independent real-server reproducer |

## Implementation phases

### Phase 0 — Upstream unblock and requalification

- Goal: establish a provider train capable of satisfying the contract.
- Modules: no ShuETL production modules.
- Required behavior: ETLantic #131 and #132 remain fixed in published 0.52.1
  artifacts; exact versions and migration head are recorded; fresh, upgrade,
  submission, event, and concurrency spikes pass on PostgreSQL 18.6.
- Tests: standalone installed-package qualification, not source-checkout imports.
- Documentation/configuration: record the qualified 0.52.1 train and
  `005_cp1_reference` head in compatibility and evidence files.
- Dependency: complete; implementation may proceed.

### Phase 1 — Compatibility and settings

- Goal: add the exact optional dependency set and fail-closed profile matrix.
- Modules: `pyproject.toml`, lock, `compatibility.py`, `settings.py`.
- Tests: metadata, wheel, settings combination/property, URL/TLS, optional
  import ordering, and redaction tests.
- Documentation: compatibility matrix and exact version table.
- Dependency: Phase 0.

### Phase 2 — Read-only database qualification

- Goal: implement one non-mutating connectivity/schema classifier shared by
  bundle construction and doctor.
- Modules: private PostgreSQL/schema helpers and `diagnostics.py`.
- Tests: fresh/behind/head/ahead/unknown/corrupt/unreachable/wrong-server
  fixtures; catalog snapshots prove zero writes.
- Documentation: readiness meanings and remediations.
- Dependency: Phase 1 and the qualified provider inventory.

### Phase 3 — Explicit migrations

- Goal: expose the one-way provider-owned upgrade command outside startup.
- Modules: `cli.py` and a private migration helper.
- Tests: fresh, every earlier head, head no-op, failure injection, exit codes,
  redaction, cleanup, and no-startup-migration gates.
- Documentation: least-privilege migration/run roles and recovery procedure.
- Dependency: Phases 1–2.

### Phase 4 — PostgreSQL provider graph

- Goal: construct and close the exact upstream relational graph.
- Modules: provider module and `__init__.py`.
- Tests: protocol/type/object/engine identity, caller identity/auth retention,
  production profile, absent optional providers, failure disposal, and close.
- Documentation: application integration and lifecycle example.
- Dependency: Phases 1–3.

### Phase 5 — Durable behavior and adversarial verification

- Goal: prove the pilot's actual persistence, identity, authorization, and
  concurrency properties.
- Modules: tests and examples; no new semantic production layer.
- Tests: AC-018 through AC-026 including independent engine restarts and
  barrier-controlled concurrency.
- Documentation: explicit statement that ShuETL runs no scheduler/worker and
  external effects are not exactly once.
- Dependency: Phase 4.

### Phase 6 — Operations, CI, and release evidence

- Goal: make the qualification reproducible from built artifacts.
- Modules: workflows, release scripts, docs, example, changelog, evidence.
- Tests: real PostgreSQL 18.6 on Python 3.11–3.13, clean extras, backup/restore,
  full regression and artifact gates.
- Documentation: provisioning, TLS, migration, readiness, backups, restore,
  canonical data, limitations, and version evidence.
- Dependency: Phases 1–5.

## Risks

| Risk | Mitigation / release rule |
|---|---|
| Upstream migration reports head while required tables are absent | Require the 0.52.1 migration head and minimum table inventory |
| Concurrent event requests lose writes or leak driver errors | Require the 0.52.1 barrier-controlled event proof |
| `current_version()` mutates fresh databases | Never use it in doctor/startup; private read-only inspection contract |
| Direct SQLAlchemy engine construction drifts from provider assumptions | Exact pins, public `Engine` constructor seam, real-server store tests |
| Binary driver/libpq behavior differs from system packages | Limit 0.4 claim to exact Psycopg binary set; record runtime versions |
| TLS defaults are weakened for convenience | Default `verify-full`; explicit insecure opt-in; CI exception documented |
| Migration partial failure leaves ambiguous schema | Fail readiness, preserve provider recovery ownership, never auto-repair |
| Snapshot-backed durable/schedule stores have scaling limits | Controlled single-tenant pilot only; no HA/performance claim |
| Green mock tests hide dialect behavior | Real PostgreSQL and independent connection/restart tests are mandatory |
| Optional upstream routes look production-ready without providers | Document absent providers; do not claim reports/artifacts/governance |

## Explicit non-scope

- ShuETL-owned SQLModel tables, Alembic revisions, DDL, repositories, event
  sequence allocation, retry wrappers, or transaction semantics.
- Calling provider demo/test table helpers in production.
- Automatic migration, repair, downgrade, reset, or schema generation during
  application startup.
- PostgreSQL versions other than 18.6 or Psycopg installations other than the
  exact binary 3.3.5 pilot set.
- Multi-tenant qualification, horizontal gateway/worker HA, replicas,
  failover, pooling proxies, sharding, or performance/load claims.
- Scheduler or worker processes, pipeline execution, retry loops, leases owned
  by ShuETL, or a combined production process.
- Exactly-once external side effects.
- New identity/authentication implementation, AuthMate, OAuth/OIDC, token
  validation, anonymous access, or allow-all defaults.
- Report/artifact/history/governance stores not required by the qualified
  upstream graph.
- New HTTP routes, route aliases, alternate schemas/errors, or a ShuETL
  readiness endpoint.
- SQLite durability promotion or repair of unrelated 0.3 behavior.
- Backup scheduling, retention, encryption key management, or disaster-recovery
  automation; Phase 0.4 documents and verifies inputs/restore only.

## Known follow-up candidates

- ShuETL issue #1: upgrade GitHub Actions off deprecated Node.js runtimes.
- ShuETL issue #2: historical FastAPI TestClient/httpx transport warning; the
  active suite already uses `httpx2`, so close or update only in separate issue
  triage.
- A future system-libpq Psycopg installation option after separate packaging and
  TLS qualification.
- PostgreSQL minor/major expansion, multi-tenant isolation, HA, and performance
  qualification after the controlled pilot.
- A future upstream read-only migration-status API could replace ShuETL's narrow
  compatibility adapter.

ETLantic #131 and #132 were release blockers during planning and are now closed;
their fixes and the qualification evidence remain part of AC-037 and AC-038.

## Definition of done

Phase 0.4 is done only when:

- the published exact 0.52.1 upstream train continues to satisfy AC-037 and
  AC-038;
- every AC-001 through AC-038 is verified;
- required 0.2/0.3 compatibility is preserved;
- the change introduces no known substantive regression;
- every required local and real-PostgreSQL gate passes on Python 3.11–3.13;
- clean built artifacts reproduce the documented provider graph and CLI;
- documentation and evidence match the exact released behavior and versions;
- no release blocker attributable to this change remains.

The repository does not need to be globally defect-free. Follow-ups outside
this boundary do not prevent completion.

## Implementation decision

The 0.52.0 installed-package qualification on PostgreSQL 18.6 passed fresh and
prior-head migrations, required-table checks, registry/definition revisions,
submission idempotency, event replay, schedule/firing identity, restart
round-trips, and barrier-controlled concurrent event appends. The plan is ready
for the implementation sequence above. Any later upstream version change must
repeat this qualification and update only exact-version evidence unless the
contract changes.

READY FOR IMPLEMENTATION
