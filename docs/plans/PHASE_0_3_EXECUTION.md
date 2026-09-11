# Phase 0.3 — Architecture and Implementation Plan

## Plan status

- Status: Ready for implementation
- Target release: `0.3.0`
- Baseline release: `v0.2.0`
- Baseline release commit: `a662d5d0db6dddc0045f7705384eef9df3c217ee`
- Planning source commit: `23bfba08dad4f460eb180efe7d6c555136bbcb81`
- Planning date: 2026-09-11
- Supported Python: 3.11, 3.12, and 3.13
- Supported upstream train: `etlantic==0.51.0`,
  `etlantic-fastapi==0.51.0`, and optional
  `etlantic-sqlmodel==0.51.0`

This document is the implementation contract for Phase 0.3. It resolves the
settings, local-provider, compatibility, diagnostics, security, and ownership
decisions needed for implementation. It does not authorize production
persistence, identity, scheduling, worker, or migration behavior.

## Architecture summary

Phase 0.3 keeps the 0.2 facade intact and adds an explicit configuration and
local provider composition layer beside it.

```text
Explicit kwargs        SHUETL_* environment
       \                       /
        \                     /
         v                   v
               ShuETLSettings
        fail-closed profile validation
        secret-safe database reference
                        |
                        v
              LocalProviderBundle
      caller identity + ETLantic authorizer
      memory stores OR qualified SQLite stores
                        |
                        v
              upstream ETLanticAPI
                        |
                        v
                ShuETL 0.2 facade
                        |
                        v
                   FastAPI host

ShuETLSettings -------> DoctorReport -------> text / JSON
                              |
                              +-- no HTTP routes
                              +-- no migrations
                              +-- no pipeline execution
```

The ownership rules are unchanged:

- ETLantic owns definitions, submissions, events, authorization, and provider
  protocols.
- `etlantic-fastapi` owns HTTP routes, schemas, errors, and live `/ready`
  behavior.
- `etlantic-sqlmodel` owns relational stores, tables, schema revisions, and
  migrations.
- ShuETL owns validation of its settings, selection and wiring of a named local
  bundle, compatibility checks, and preflight diagnostics.
- The host owns identity adapters, authorization policy, application lifespan,
  and cleanup of a bundle it requested.

The following accepted decisions govern the work:

| Decision | Phase 0.3 constraint |
|---|---|
| ADR-0001 | ShuETL must continue to provide composition value without duplicating `etlantic-fastapi`. |
| ADR-0002 | Python 3.11–3.13 and the exact qualified upstream train remain lockstep. |
| ADR-0003 | New direct and optional dependencies require actual ShuETL imports or calls. |
| ADR-0004 | `ShuETL(api=...)` remains supported; settings add a separate bundle path rather than changing caller-owned graph semantics. |
| ADR-0005 | Bundle ownership does not silently alter host or facade lifespan behavior. |
| ADR-0006 | The only route preset is the complete upstream router. |
| ADR-0007 | Constructor arguments override `SHUETL_*`; implicit file-backed settings sources are disabled. |
| ADR-0008 | Local bundles compose upstream memory or SQLite stores while identity, authorization, and migrations remain external. |
| ADR-0009 | `shuetl doctor` emits a deterministic, versioned, redacted preflight report. |

## Repository and upstream ground truth

The plan is grounded in the released 0.2 facade and public 0.51.0 package
surfaces.

| Concern | Verified baseline |
|---|---|
| ShuETL facade | `ShuETL(api=api)`, `mount()`, `create_app()`, `lifespan`, and `compose_lifespan()` |
| Current ownership | The facade retains the exact caller-owned `ETLanticAPI` and invokes no provider lifecycle method |
| Required upstream graph | `authorizer`, `definitions`, `submissions`, `events`, and `context_factory` |
| Identity hooks | Public `ContextFactory` and `PrincipalDependency` contracts from `etlantic-fastapi` |
| Memory stores | Public `MemoryDefinitionRepository`, `MemorySubmissionStore`, and `MemoryEventStore` |
| Relational package | `etlantic-sqlmodel==0.51.0`, separately published and compatible with ETLantic 0.51.x |
| SQLite construction | Public `create_sqlite_engine()` plus SQLModel definition, submission, and event stores |
| SQLite schema inspection | Public `current_version()` reports migration state |
| SQLite migration head | `004_schedules_0_47` after public `apply_migrations()` |
| Migration ownership | `etlantic-sqlmodel`; ShuETL has no tables or migrations |
| Upstream live readiness | `ETLanticAPI.stores_ready()` and `GET /ready` check required injected stores only |
| Existing release gate | Lock, sync, Ruff, Pyright, boundaries, tests, artifacts, OpenAPI, clean wheel, and evidence |

The SQLModel package exposes individual stores and migration functions, not a
complete application identity or authorization policy. Phase 0.3 therefore
constructs only the stores it can own and requires the host to inject the
remaining upstream contracts.

## Change boundary

### Problem

The 0.2 API is deliberately safe but verbose for local use. Every application
must repeat provider construction and has no standard way to validate
configuration, identify an unsupported package mix, determine whether an
optional provider is installed, inspect SQLite schema state, or capture a
redacted diagnostic snapshot.

### Desired outcome

A developer can explicitly select a supported local profile, construct the
standard provider graph using host-owned identity and authorization, mount it
through the existing facade, and diagnose failures before serving traffic.
Memory remains the smallest path. SQLite is a separately installed,
development-only path whose schema is provisioned outside application startup.

### In scope

- A frozen `ShuETLSettings` model using explicit constructor and environment
  sources.
- Required, fail-closed selection of local profile, gateway role, provider,
  and host identity mode.
- Existing prefix validation and a single `complete` route preset.
- A bounded provider connection timeout used only by supported local provider
  preflight/construction.
- A redacted optional database URL for the SQLite profile.
- Runtime compatibility validation for the exact qualified package train.
- A public `LocalProviderBundle` containing upstream objects, not shadow types.
- Core memory-provider construction.
- Optional file-backed SQLite-provider construction through public
  `etlantic-sqlmodel` APIs.
- Read-only SQLite migration-head validation before bundle return.
- Explicit, idempotent bundle cleanup.
- A typed, versioned doctor report and text/JSON CLI rendering.
- An install-to-first-run memory tutorial and a separate SQLite qualification
  example.
- 0.3 evidence, artifact checks, clean-wheel checks, and CI coverage for core
  and SQLite-extra installations.

### Explicitly out of scope

- A default deployment profile, process role, provider, or identity mode.
- Any production profile or production durability claim.
- PostgreSQL or another network database.
- Automatic table creation, schema migration, repair, downgrade, or backup.
- ShuETL-owned database tables, SQLModel classes, or migration revisions.
- Anonymous, allow-all, or ShuETL-authored authorization behavior.
- Token validation, AuthMate, OAuth/OIDC clients, or another identity product.
- Arbitrary provider names, import strings, entry points, or plugin discovery.
- Registry, durable-work, schedule, history, governance, attestation, audit, or
  execution-provider construction.
- Scheduler, worker, executor, retry, or background pipeline execution.
- Route filtering, aliases, new HTTP diagnostics, or a second readiness route.
- Network probes, package installation, or migrations from `shuetl doctor`.
- Reading `.env`, `pyproject.toml`, YAML, TOML, or a secrets directory as a
  settings source.
- General production operational bounds such as quotas, request limits, or
  worker concurrency before their authoritative upstream contracts are wired.
- Changes to ETLantic HTTP models, statuses, authorization order, or OpenAPI.

### Touched surface

Implementation is expected to touch only:

- `src/shuetl/settings.py`
- `src/shuetl/providers.py`
- `src/shuetl/compatibility.py`
- `src/shuetl/diagnostics.py`
- `src/shuetl/cli.py`
- `src/shuetl/errors.py`
- `src/shuetl/__init__.py`
- narrowly required reuse of prefix validation from
  `src/shuetl/integration.py`
- `pyproject.toml` and `uv.lock`
- focused unit, integration, contract, CLI, and review tests
- `examples/phase_0_3_quickstart.py`
- `examples/phase_0_3_sqlite.py`
- release scripts and `.github/workflows/checks.yml`
- `README.md`, `CHANGELOG.md`, the planning index, and `docs/evidence/0.3/`

No new routes, ETLantic domain models, database models, migrations, scheduler,
worker, or identity adapter are part of the expected change.

## Public contract

### Required behavior

Every observable rule from **Public exports** through **Doctor contract**, plus
the compatibility, invariant, security, and acceptance sections below, is
required. An implementation may change private structure only when all of those
behaviors remain demonstrably equivalent. No recommendation can weaken a
required behavior or acceptance criterion.

### Public exports

Phase 0.3 preserves all 0.2 exports and adds exactly these top-level names:

```python
from shuetl import (
    CapabilityError,
    CompatibilityError,
    DiagnosticCheck,
    DoctorReport,
    LocalProviderBundle,
    ProviderReadinessError,
    ShuETLSettings,
)
```

The complete `shuetl.__all__` is therefore:

```python
(
    "ShuETL",
    "ShuETLSettings",
    "LocalProviderBundle",
    "DoctorReport",
    "DiagnosticCheck",
    "ShuETLError",
    "InvalidPrefixError",
    "MountConflictError",
    "CompatibilityError",
    "CapabilityError",
    "ProviderReadinessError",
)
```

Provider kinds, profiles, roles, identity modes, route presets, capability IDs,
check IDs, and diagnostic statuses are serialized string vocabularies. They are
not additional public enum classes in 0.3.

### New exceptions

```python
class CompatibilityError(ShuETLError, RuntimeError): ...


class CapabilityError(ShuETLError, RuntimeError): ...


class ProviderReadinessError(ShuETLError, RuntimeError): ...
```

- `CompatibilityError` names incompatible distribution names and versions.
- `CapabilityError` names an unavailable selected capability and gives an
  install or configuration remediation.
- `ProviderReadinessError` names the failed readiness category and remediation.
- No exception includes a database URL, filesystem path, environment value,
  provider representation, raw driver error, or secret.
- Settings shape/value failures remain ordinary Pydantic `ValidationError`s;
  the CLI converts them to redacted diagnostic checks.

## Settings contract

### Model shape

`ShuETLSettings` is a frozen `pydantic-settings.BaseSettings` model with these
fields and no others:

| Field | Type | Default | Environment | Contract |
|---|---|---|---|---|
| `profile` | `Literal["local"]` | required | `SHUETL_PROFILE` | No implicit deployment profile. |
| `role` | `Literal["gateway"]` | required | `SHUETL_ROLE` | No scheduler, worker, or combined role in 0.3. |
| `provider` | `Literal["memory", "sqlite"]` | required | `SHUETL_PROVIDER` | Named built-ins only. |
| `identity` | `Literal["host"]` | required | `SHUETL_IDENTITY` | Caller must inject upstream identity contracts. |
| `api_prefix` | `str` | `"/etl"` | `SHUETL_API_PREFIX` | Uses the exact 0.2 prefix validator. |
| `route_preset` | `Literal["complete"]` | `"complete"` | `SHUETL_ROUTE_PRESET` | Complete upstream router only. |
| `database_url` | `SecretStr | None` | `None` | `SHUETL_DATABASE_URL` | Required only for SQLite; excluded from serialization. |
| `provider_connect_timeout_seconds` | constrained `float` | `2.0` | `SHUETL_PROVIDER_CONNECT_TIMEOUT_SECONDS` | Finite, `0.1 <= value <= 30.0`; local provider operations only. |

Configuration is `extra="forbid"`, `frozen=True`, `populate_by_name=True`,
validates defaults, and uses the exact uppercase `SHUETL_` prefix. Every field
declares its full uppercase environment `validation_alias`; this avoids relying
on case-normalization of Python field names. Case variants are not aliases.

### Source precedence

The complete precedence order is:

1. explicit `ShuETLSettings(...)` keyword arguments;
2. exact `SHUETL_*` process environment variables;
3. declared defaults for non-security-sensitive fields.

Dotenv, file-secret, pyproject, JSON, TOML, YAML, custom callback, and automatic
CLI parsing sources are disabled through `settings_customise_sources()`.
Unrecognized constructor fields fail. Unrecognized environment variables are
not consumed.

### Cross-field validation

- `memory` requires `database_url is None`.
- `sqlite` requires a database URL whose normalized driver is exactly
  `sqlite` or `sqlite+pysqlite` and whose target is a file.
- In-memory SQLite, URI mode, query strings, credentials, fragments, network
  hosts, and non-SQLite schemes are rejected.
- The database file need not exist at settings validation time; provider
  readiness handles that without exposing the path.
- The prefix validator runs during settings construction, not first mount.
- Values outside the one supported profile, role, identity mode, or route
  preset fail rather than being normalized or ignored.
- Strings are not whitespace-trimmed, case-folded, path-expanded, or
  environment-interpolated.

### Secret behavior

- `database_url` uses `SecretStr` and is excluded from `model_dump()` and
  `model_dump_json()`.
- `repr(settings)` and validation errors never contain its input value.
- A private provider helper is the only code allowed to call
  `get_secret_value()`.
- Diagnostics expose `database_configured: bool` and `database_driver` only.
- Redaction tests use credentials, query tokens, home-directory paths, control
  characters, Unicode, and deliberately raised driver errors.

## Compatibility contract

The compatibility check runs before `ShuETL` construction from a bundle,
provider import, engine construction, or app mounting.

Core requirements are exact:

- `shuetl==0.3.0`
- `etlantic==0.51.0`
- `etlantic-fastapi==0.51.0`
- `fastapi==0.141.1`
- `pydantic==2.13.5`
- `pydantic-settings==2.15.0`

The SQLite profile additionally requires:

- `etlantic-sqlmodel==0.51.0`
- the exact SQLAlchemy version qualified and locked for the 0.3 build, initially
  `sqlalchemy==2.0.52`, because ShuETL calls the returned public engine's URL,
  connection, and disposal APIs.

Rules:

- Compare installed distribution metadata without importing optional provider
  code first.
- Any installed `etlantic-*` distribution whose release train differs from
  the active core 0.51 train is a compatibility failure, even when the selected
  local bundle would not import it.
- A missing SQLite extra is a capability failure with
  `pip install "shuetl[sqlite]==0.3.0"` remediation.
- A missing core distribution is a compatibility failure.
- No automatic package installation or permissive fallback is allowed.
- Normal package resolver constraints remain the first defense; runtime checks
  cover forced or externally mutated environments.
- The existing caller-built `ShuETL(api=...)` constructor also runs the core
  compatibility check so an unsupported mix fails before traffic.

## Local provider-bundle contract

### Construction

```python
bundle = LocalProviderBundle.create(
    settings,
    authorizer=authorizer,
    context_factory=context_factory,
    principal_dependency=principal_dependency,
)
integration = ShuETL(api=bundle.api)
```

All four arguments are positional/keyword exactly as shown: `settings` is the
only positional argument and identity/authorization contracts are keyword-only.
`None`, duck-typed replacements that do not satisfy runtime-checkable upstream
protocols, and wrong callable shapes fail before provider construction. Error
messages name the argument, not its representation.

The frozen, slotted bundle exposes read-only properties:

- `settings: ShuETLSettings` — the exact settings object;
- `api: ETLanticAPI` — the exact composed upstream API;
- `authorizer: Authorizer` — the exact caller object;
- `definitions: DefinitionRepository` — the exact upstream store;
- `submissions: SubmissionStore` — the exact upstream store;
- `events: EventStore` — the exact upstream store;
- `provider: Literal["memory", "sqlite"]`;
- `development_only: Literal[True]`;
- `closed: bool`;
- `close() -> None` — idempotent cleanup.

It defines no repository methods, authorization methods, or domain records of
its own.

### Memory bundle

The memory profile constructs exactly:

- `MemoryDefinitionRepository`;
- `MemorySubmissionStore`;
- `MemoryEventStore`;
- `ETLanticAPI` with the injected authorizer, context factory, and principal
  dependency;
- upstream API profile `"development"`.

Optional upstream providers remain `None`. In particular, 0.3 does not silently
enable registry, durable work, schedules, history, policy, approvals, quotas,
erasure, audit, attestations, objectives, or execution. Their routes retain the
qualified upstream unavailable behavior.

Memory `close()` is safe, idempotent, and invokes no provider method. Each call
to `create()` returns an isolated graph.

### SQLite bundle

The SQLite path is available only after the compatibility and extra checks. It:

1. parses and validates the URL without logging or formatting the raw value;
2. verifies the target file already exists before opening an engine;
3. calls public `etlantic_sqlmodel.create_sqlite_engine()` with the configured
   bounded connection timeout;
4. calls public `current_version()` read-only;
5. requires the exact head `004_schedules_0_47`;
6. constructs `SQLModelDefinitionRepository`,
   `SQLModelSubmissionStore`, and `SqlModelEventStore` with the same engine;
7. constructs the authoritative `ETLanticAPI` with caller identity and
   authorization;
8. returns no bundle until every check and construction step succeeds.

If any step after engine creation fails, the engine is disposed before a
redacted `ProviderReadinessError` is raised. The host must call `bundle.close()`
at shutdown; it disposes the engine exactly once and never migrates or deletes
the database. Use-after-close through bundle-owned helpers is rejected, but
ShuETL does not attempt to intercept direct use of exposed upstream objects.

Documentation may show this explicit provisioning step outside application
startup:

```python
from etlantic_sqlmodel import apply_migrations, create_sqlite_engine

engine = create_sqlite_engine(database_url)
try:
    apply_migrations(engine)
finally:
    engine.dispose()
```

That snippet invokes the upstream provider directly. No ShuETL API wraps,
infers, or automatically calls it.

### Ownership and lifecycle

- The caller always owns injected identity and authorizer objects.
- The caller owns the returned bundle and must close it.
- `ShuETL(api=bundle.api)` still treats the API as caller-owned and does not
  discover or close the bundle.
- `mount()`, `lifespan`, and `create_app()` retain their 0.2 behavior.
- A host may close the bundle in the host portion of
  `compose_lifespan()` cleanup, after ShuETL exits.
- A closed bundle cannot be reused to create a new supported application.
- Memory and SQLite local profiles remain development-only regardless of file
  persistence or process topology.

## Doctor contract

### Python model

`DoctorReport.inspect(settings: ShuETLSettings | None = None,
bundle: LocalProviderBundle | None = None) -> DoctorReport` is the only public
diagnostic entry point. When `settings` is `None`, it constructs settings from
the environment and converts validation failure into a redacted report.

`DoctorReport` and `DiagnosticCheck` are frozen Pydantic models. The JSON shape
is exactly:

```json
{
  "schema": "shuetl.doctor/1",
  "status": "pass",
  "profile": "local",
  "role": "gateway",
  "provider": "memory",
  "identity": "host",
  "api_prefix": "/etl",
  "route_preset": "complete",
  "development_only": true,
  "database_configured": false,
  "database_driver": null,
  "versions": {
    "etlantic": "0.51.0",
    "etlantic-fastapi": "0.51.0",
    "fastapi": "0.141.1",
    "pydantic": "2.13.5",
    "pydantic-settings": "2.15.0",
    "shuetl": "0.3.0"
  },
  "configured_capabilities": [
    "control-plane.definitions",
    "control-plane.events",
    "control-plane.submissions"
  ],
  "available_capabilities": [
    "provider.memory"
  ],
  "checks": [
    {
      "id": "configuration.valid",
      "status": "pass",
      "summary": "Configuration is valid.",
      "remediation": null
    }
  ]
}
```

Exact check IDs are:

- `configuration.valid`;
- `compatibility.core`;
- `compatibility.etlantic_train`;
- `provider.available`;
- `provider.ready`;
- `provider.schema`;
- `identity.explicit`;
- `role.supported`;
- `routes.supported`;
- `topology.development_only`.

Statuses are `pass`, `warn`, `fail`, or `skip`. Report status is `fail` when any
check fails and `pass` otherwise. The development-only check is always `warn`
for the supported 0.3 profiles. The relational schema check is `skip` for
memory and required `pass` for SQLite.

Lists are sorted, check order follows the fixed list above, and version-map keys
are stable. Reports contain no timestamp, platform-specific path, current
directory, raw environment value, URL, secret, provider representation, or raw
exception. A bundle from different settings produces a failed
`provider.ready` check rather than being inspected ambiguously.

The six core version keys in the example are always present. Installed official
`etlantic-*` distributions are added in sorted order; `etlantic-sqlmodel` and
`sqlalchemy` are therefore present for the SQLite profile and may be absent for
memory. Missing required distributions serialize as `null` rather than causing
an incomplete report.

### CLI

`pyproject.toml` exposes:

```toml
[project.scripts]
shuetl = "shuetl.cli:main"
```

The 0.3 grammar is intentionally small:

```text
shuetl doctor [--format text|json]
shuetl --version
```

- Text is the default format.
- JSON is one report object on stdout with deterministic indentation.
- Diagnostic content goes to stdout in both formats; unexpected internal errors
  produce one generic redacted message on stderr.
- Exit `0` means the report has no failed required check.
- Exit `1` means the report contains a failed required check.
- Exit `2` is reserved for argparse usage errors.
- `--version` prints only `shuetl 0.3.0` and exits `0`.
- There is no `--database-url` option; database secrets are supplied through the
  environment or Python settings construction, not shell history.
- The CLI never installs packages, creates a database, applies migrations,
  imports caller code, starts an app, or performs pipeline work.

The implementation uses stdlib `argparse`; it does not add Typer or Click as a
direct dependency merely because ETLantic currently depends on them.

## Recommended implementation

These details are non-normative. Luna may adapt them to repository reality while
preserving every required behavior and AC:

- Put settings, distribution checks, provider bundles, diagnostics, and CLI
  parsing in the named modules from the touched surface instead of enlarging
  `integration.py`.
- Extract the existing prefix validator to one private dependency-neutral module
  and import it from settings and the facade; do not duplicate the grammar.
- Implement settings sources with `settings_customise_sources()` and explicit
  per-field uppercase `validation_alias` values.
- Use `importlib.metadata` for compatibility inventory and defer optional
  imports until the inventory passes.
- Use SQLAlchemy's public URL parser for SQLite classification rather than
  hand-parsing or substring checks.
- Keep mutable bundle lifecycle state in a private object so the public bundle
  can remain frozen and slotted.
- Build `DoctorReport` from a private ordered check collector, then render both
  formats from that one model.
- Centralize authored remediation strings so exceptions, doctor output, tests,
  and documentation cannot drift.
- Isolate filesystem and distribution inspection behind narrow private helpers
  that tests can replace without mocking ETLantic behavior.

## Existing facade compatibility

All 0.2 contracts remain in force:

- `ShuETL(api=...)` retains exact API identity.
- Mounting and dedicated-app modes expose the complete upstream router.
- Prefix and collision behavior remains unchanged.
- Host state, handlers, metadata, middleware, and lifespan ownership remain
  unchanged.
- No provider lifecycle method is inferred from an arbitrary caller API.
- Dependency overrides still target upstream callables.
- HTTP status codes, idempotency, authorization order, SSE, schemas, and
  operation IDs remain upstream behavior.

The only constructor addition is a core package compatibility check performed
before storing the API. It must not import optional provider packages or mutate
the API.

## Required invariants

1. Missing configuration never selects a local/development behavior.
2. Only named, closed-set profiles and providers are accepted.
3. Settings source precedence is deterministic and filesystem-independent.
4. Secret values never appear in normal settings serialization or diagnostics.
5. ETLantic models and protocols cross the bundle boundary unchanged.
6. Host identity and authorization are always injected explicitly.
7. Memory and SQLite bundles are always labeled development-only.
8. SQLite schema is inspected but never created or migrated by ShuETL.
9. Provider construction is atomic from the caller's perspective.
10. Any internally created engine is disposed on construction failure.
11. Bundle cleanup is explicit and idempotent.
12. Compatibility failures occur before provider import/construction or traffic.
13. Missing optional dependencies fail with one exact install remediation.
14. Doctor text and JSON render the same facts and severities.
15. Doctor does not replace the live upstream readiness contract.
16. 0.2 facade, OpenAPI, authorization, and lifecycle behavior remains stable.
17. No request or diagnostic path executes pipeline work.
18. Package behavior is proven from installed wheels for every supported Python.

## Edge cases and required results

| Case | Required result |
|---|---|
| No `SHUETL_PROFILE` and no constructor value | Settings validation fails; no memory fallback |
| Constructor and environment disagree | Constructor wins exactly |
| Lowercase environment spelling | Not consumed |
| `.env` contains otherwise valid settings | Ignored |
| Unknown profile, role, provider, identity, or route preset | Validation failure |
| Invalid or root-slash prefix | Existing `InvalidPrefixError` semantics surfaced through Pydantic without mutation |
| Memory with database URL | Validation failure; URL absent from error |
| SQLite without database URL | Validation failure |
| SQLite network/non-file/in-memory URL | Validation failure; URL absent from error |
| Provider timeout is NaN, infinite, below 0.1, or above 30 | Validation failure |
| Core distribution missing or wrong | `CompatibilityError` / failed doctor check |
| Installed ETLantic plugin on a different minor train | Compatibility failure before provider import |
| SQLite selected without extra | `CapabilityError`; exact install remediation |
| SQLite database file missing | Redacted `ProviderReadinessError`; no file created |
| SQLite schema missing, behind, or ahead | Redacted failure; no migration attempted |
| SQLite schema at `004_schedules_0_47` | Bundle returned with three upstream SQLModel stores |
| Wrong identity or authorizer argument | Named `TypeError`; no provider constructed |
| Two memory bundles | Independent stores and APIs |
| Bundle construction fails after engine creation | Engine disposed exactly once |
| `close()` called twice | No error and one underlying disposal |
| Existing caller-built API | Same 0.2 identity and ownership behavior |
| Doctor without settings | Redacted failed report rather than traceback |
| Doctor memory schema check | `skip` |
| Doctor SQLite missing extra/schema | `fail` with remediation, no raw error |
| Doctor warning only | Overall pass and exit `0` |
| Doctor required check failure | Overall fail and exit `1` |
| Secret embedded in driver exception | Absent from text, JSON, logs, and stderr |
| Non-ASCII/control-value attack | Rejected or redacted without terminal control output |

## Security and reliability requirements

- Environment configuration is treated as untrusted input.
- No settings value becomes an import path, module name, entry point, executable,
  migration target, or arbitrary SQL string.
- SQLite URLs are parsed structurally; string prefix checks alone are
  insufficient.
- Database existence and schema inspection are read-only. Tests verify that a
  missing path remains absent.
- Provider exceptions are chained only internally; public messages and doctor
  output use bounded, authored text.
- Secret tests scan `repr`, `str`, model dumps, JSON, text output, logs, exception
  messages, tracebacks captured by the CLI, and evidence.
- The diagnostic timeout is finite and cannot be disabled with zero, infinity,
  NaN, or a negative value.
- Optional provider imports occur only after distribution/version validation.
- A capability failure never silently falls back from SQLite to memory.
- A schema failure never silently falls back to a new database.
- The host-supplied authorizer remains deny-by-default or otherwise entirely the
  host's responsibility; ShuETL grants no action.
- The principal dependency and context factory are passed unchanged to
  `ETLanticAPI`.
- The CLI performs no remote network operation in 0.3.

## Packaging and compatibility

Phase 0.3 changes the project version to `0.3.0` and adds:

- core dependency `pydantic-settings==2.15.0`;
- optional extra `sqlite` with `etlantic-sqlmodel==0.51.0` and the exact
  SQLAlchemy version used directly by ShuETL;
- console script `shuetl = "shuetl.cli:main"`.

The wheel still contains only `shuetl`, `py.typed`, and distribution metadata.
No tests, examples, evidence, database, `.env`, or migration file enters the
wheel. The sdist may include tests/examples/evidence according to the existing
allowlist, but must contain no generated SQLite database.

Core clean-wheel testing installs the ordinary wheel. A second isolated test
installs `shuetl[sqlite]`, provisions a temporary database only through public
upstream migration APIs, constructs and closes the bundle, and verifies import
origins outside the checkout.

## Acceptance criteria

| ID | Observable acceptance criterion |
|---|---|
| AC-001 | Project metadata reports `0.3.0`, Python 3.11–3.13, the exact core train, `pydantic-settings`, the SQLite extra, and the `shuetl` script. |
| AC-002 | `shuetl.__all__` contains exactly the documented 0.2 and 0.3 public names; the installed wheel matches source. |
| AC-003 | `ShuETLSettings` is frozen, forbids extra constructor fields, and exposes exactly the documented fields and JSON schema. |
| AC-004 | Profile, role, provider, and identity are required; omission never selects memory or another development behavior. |
| AC-005 | Explicit constructor values override exact uppercase environment values, which override only documented non-sensitive defaults. |
| AC-006 | Dotenv, secrets-directory, pyproject, structured-file, lowercase, and custom implicit sources are not consumed. |
| AC-007 | Settings reuse the 0.2 prefix grammar and accept only the `complete` route preset. |
| AC-008 | Provider/database and profile/role/identity cross-field combinations fail exactly as specified. |
| AC-009 | The provider timeout accepts only finite values from 0.1 through 30.0 seconds. |
| AC-010 | Database values are absent from settings repr/serialization, validation errors, diagnostics, logs, exceptions, and evidence. |
| AC-011 | Core package versions are validated before any provider construction and wrong/missing distributions raise `CompatibilityError`. |
| AC-012 | Any installed mismatched `etlantic-*` train is rejected before traffic without importing its code. |
| AC-013 | SQLite selection without the extra raises `CapabilityError` with the exact versioned install remediation and no fallback. |
| AC-014 | Bundle construction requires the exact settings object and explicit conforming authorizer, context factory, and principal dependency. |
| AC-015 | A memory bundle contains exact upstream memory definition/submission/event stores and an exact upstream `ETLanticAPI`. |
| AC-016 | The composed API retains caller authorizer/context/principal identity and maps the ShuETL local profile to upstream development. |
| AC-017 | Optional registry, durable, schedule, history, governance, and execution providers remain absent in the core local bundle. |
| AC-018 | Separate bundle constructions share no store, API, settings, or mutable provider state except caller objects explicitly reused. |
| AC-019 | SQLite accepts only validated file URLs, does not create a missing file, and checks schema state through public upstream APIs. |
| AC-020 | SQLite at migration head constructs the exact upstream SQLModel definition/submission/event stores over one engine. |
| AC-021 | Missing, behind, or ahead SQLite schema fails with a redacted `ProviderReadinessError`; no migration or table creation occurs. |
| AC-022 | Any engine created before a failed bundle return is disposed once; successful bundle `close()` is explicit and idempotent. |
| AC-023 | The 0.2 caller-built API path, mount behavior, lifespan behavior, route set, and provider ownership remain unchanged. |
| AC-024 | Memory and SQLite modes preserve upstream API/OpenAPI, authorization order, submission, idempotency, event, and readiness behavior. |
| AC-025 | `DoctorReport` and `DiagnosticCheck` are frozen and serialize exactly the versioned `shuetl.doctor/1` contract. |
| AC-026 | Doctor reports configuration, profile, role, provider, identity, prefix, route preset, database presence/driver, and development-only status. |
| AC-027 | Doctor reports core and installed ETLantic package versions and rejects unsupported combinations. |
| AC-028 | Configured and available capability lists are distinct, sorted, bounded, and truthful for memory, SQLite, and missing-extra cases. |
| AC-029 | Provider readiness is checked without application startup, package installation, migration, table creation, or pipeline execution. |
| AC-030 | Relational schema status is `skip` for memory and required pass/fail for SQLite against `004_schedules_0_47`. |
| AC-031 | Doctor check order, IDs, severities, report status, and remediations are deterministic. |
| AC-032 | Doctor text and JSON contain the same facts; neither contains a timestamp, path, URL, secret, repr, or raw provider exception. |
| AC-033 | `shuetl doctor` uses environment settings, supports exact text/JSON formats, and returns exit 0/1/2 as specified. |
| AC-034 | `shuetl --version` works from an isolated wheel and no other 0.3 command is exposed. |
| AC-035 | The clean memory quickstart reaches the mounted API from an installed wheel using an application-owned definition and explicit host identity/authorization. |
| AC-036 | The SQLite example provisions only through upstream APIs outside startup, constructs the local bundle, serves no traffic before readiness, and closes it. |
| AC-037 | Static/runtime gates find no ShuETL domain model, route, migration, table, anonymous authorizer, plugin discovery, scheduler, worker, or execution path. |
| AC-038 | Existing normalized 0.2 OpenAPI remains identical for equivalent 0.3 bundles after prefix normalization. |
| AC-039 | Wheel/sdist and core/SQLite clean-install checks pass with allowlisted contents and no generated database or settings file. |
| AC-040 | Ruff, Pyright, boundaries, all tests, builds, artifacts, OpenAPI, clean-wheel, CLI, redaction, and evidence pass on Python 3.11–3.13. |
| AC-041 | User documentation states all required settings, precedence, ownership, cleanup, local-only limits, SQLite provisioning, diagnostics, and non-goals. |
| AC-042 | The 0.3 evidence index maps AC-001–AC-042 exactly once to passing proof and contains no secret or machine-specific path. |

## Verification matrix

| AC | Preferred proof | Required assertion or artifact |
|---|---|---|
| AC-001 | Compatibility / Packaging | Source and wheel METADATA contain the exact version, dependencies, extra, Python range, and console entry point. |
| AC-002 | Unit / Artifact | Source and isolated-wheel `__all__` equal the documented tuple and import every name. |
| AC-003 | Unit / Contract | Model field and JSON-schema snapshots prove exact fields, frozen state, and forbidden extras. |
| AC-004 | Unit / Property | The complete omission matrix fails and constructs no provider. |
| AC-005 | Unit / Property | A constructor/environment/default Cartesian table proves field-level precedence. |
| AC-006 | Unit / Compatibility | Temporary dotenv, secret, project, structured, and case-variant sources do not affect settings. |
| AC-007 | Unit / Contract | The complete accepted/rejected prefix table matches 0.2 and non-`complete` presets fail. |
| AC-008 | Unit / Property | Every provider/database/profile/role/identity combination has the specified pass/fail result. |
| AC-009 | Unit / Property | Boundary values pass; NaN, infinity, and out-of-range values fail. |
| AC-010 | Unit / Static Gate | Sentinel values are absent from repr, dumps, errors, logs, reports, CLI output, and evidence. |
| AC-011 | Unit / Compatibility | Simulated missing/wrong core metadata raises before a provider constructor spy is called. |
| AC-012 | Compatibility / Static Gate | An isolated mixed-train environment fails while optional-module import spies remain untouched. |
| AC-013 | Integration / Compatibility | Core-only wheel plus SQLite selection returns the exact capability remediation and no memory bundle. |
| AC-014 | Unit / Type | Valid upstream inputs pass by identity; each missing/wrong argument fails before store construction. |
| AC-015 | Unit / Integration | Runtime type and identity checks prove the three memory stores and `ETLanticAPI` are upstream instances. |
| AC-016 | Unit / Integration | API fields are the exact injected objects and its profile equals upstream `development`. |
| AC-017 | Unit / Contract | Every optional `ETLanticAPI` provider field is asserted `None`. |
| AC-018 | Property / Integration | Two bundles have disjoint APIs/stores/mutable state while explicitly reused caller objects retain identity. |
| AC-019 | Unit / Integration | URL matrix and before/after filesystem snapshots prove only file SQLite is accepted and no missing file is created. |
| AC-020 | Integration | A provider-migrated temporary DB produces three exact SQLModel store types sharing one engine. |
| AC-021 | Migration / Integration | Empty, behind, ahead, and corrupt databases fail; migration/table-call spies record zero calls. |
| AC-022 | Unit / Integration | Engine disposal counters prove one cleanup on every failed path and one total cleanup across repeated `close()`. |
| AC-023 | Contract / Compatibility | The unchanged complete 0.2 facade suite passes against caller-built APIs. |
| AC-024 | Contract / Integration | Shared memory/SQLite HTTP tests prove equivalent upstream statuses, bodies, authorization order, idempotency, events, and readiness. |
| AC-025 | Unit / Contract | Frozen-model and golden-schema assertions match `shuetl.doctor/1`. |
| AC-026 | Unit / Contract | Golden reports contain every selected setting and topology fact with no undocumented field. |
| AC-027 | Unit / Compatibility | Missing, exact, and mismatched metadata fixtures yield the documented version map and result. |
| AC-028 | Unit / Property | Capability lists for memory, SQLite, and missing-extra fixtures are distinct, sorted, and exact. |
| AC-029 | Unit / Static Gate | Startup, installer, migration, table, and execution spies remain untouched during inspection. |
| AC-030 | Unit / Migration | Memory emits `skip`; SQLite head/mismatch fixtures emit required pass/fail schema checks. |
| AC-031 | Unit / Contract | Golden check arrays prove exact order, IDs, status reduction, and remediation text. |
| AC-032 | Unit / Security | Text/JSON fact comparison and sentinel scans prove equivalent content and complete redaction. |
| AC-033 | Integration / CLI | Subprocess matrix proves environment loading, format selection, stdout/stderr, and exit 0/1/2. |
| AC-034 | Integration / Artifact | Isolated wheel prints exact version and rejects every undocumented subcommand. |
| AC-035 | Integration / Manual | The memory tutorial runs outside the checkout and proves definition ownership plus an authenticated API response. |
| AC-036 | Integration / Migration | The SQLite example records separate upstream provisioning, no startup mutation, successful request, and one close. |
| AC-037 | Static Gate / Integration | Boundary fixtures fail on prohibited models/routes/imports/calls and runtime spies observe no execution. |
| AC-038 | Contract / Compatibility | Normalized memory and SQLite OpenAPI equal the immutable 0.2 document. |
| AC-039 | Artifact / Integration | Core and SQLite clean installs pass allowlists/import-origin checks and contain no DB/settings files. |
| AC-040 | Static Gate / Compatibility | The one-command gate passes on the Python 3.11, 3.12, and 3.13 CI matrix. |
| AC-041 | Manual / Static Gate | Documentation-topic assertions and executable snippets cover the complete required user contract. |
| AC-042 | Static Gate / Artifact | Evidence checker finds AC-001–042 exactly once, verifies hashes, and passes the path/secret scan. |

Behavioral acceptance must exercise production package code and real upstream
providers. A source string, mock bundle, or monkeypatched doctor report is not
sufficient proof for a behavioral criterion.

## Implementation sequence

### E01 — Freeze settings and diagnostic schemas in tests

Goal: turn ADR-0007 and ADR-0009 into failing contract tests before adding
production behavior.

Relevant surface: new settings/diagnostic/CLI tests, shared fixtures, and the
unchanged 0.2 regression suite.

Required work:

- Add exact settings field/schema and source-precedence fixtures.
- Add invalid-combination and malicious secret fixtures.
- Add the canonical doctor JSON fixture, check order, and text fact inventory.
- Add CLI exit/stdout/stderr expectations.
- Preserve existing 0.2 tests unchanged as regression coverage.

Verification: collect the new tests successfully and record their expected
failures; no production module is added in this phase.

Documentation/configuration: commit golden settings and doctor fixtures as test
data only; do not edit package metadata yet.

Dependencies: accepted ADRs 0007–0009.

Exit: AC-003–010 and AC-025–034 are represented by failing tests only because
0.3 types do not yet exist.

### E02 — Update metadata and compatibility inventory

Goal: establish the exact install surface before importing new packages.

Relevant surface: `pyproject.toml`, `uv.lock`, package/artifact tests, and the
0.3 contract inventory.

Required work:

- Set version `0.3.0`.
- Add and lock `pydantic-settings==2.15.0`.
- Add the `sqlite` extra with exact qualified dependencies.
- Add the console entry point.
- Record public imports, versions, migration head, and ownership in 0.3 evidence.
- Add isolated mismatch fixtures that do not mutate the project environment.

Verification: inspect built metadata and entry points in both core and SQLite
isolated installations.

Documentation/configuration: record the compatibility table and optional-extra
installation contract; make no runtime provider change.

Dependencies: E01.

Exit: AC-001 and the inventory portion of AC-011–013 pass.

### E03 — Implement fail-closed settings

Goal: make every supported local topology explicit and reproducible.

Relevant surface: `src/shuetl/settings.py`, the shared private prefix validator,
and settings/redaction tests.

Required work:

- Implement the frozen settings model and disabled implicit sources.
- Reuse one prefix validator rather than copying its grammar.
- Implement strict cross-field database and timeout validation.
- Exclude database values from all ordinary serialization.
- Keep raw secret resolution in one private provider function.

Verification: run the source, cross-field, boundary, immutability, schema, and
secret-sentinel matrices from AC-003–010.

Documentation/configuration: add the exact environment-variable table and
precedence statement to the settings reference draft.

Dependencies: E02.

Exit: AC-003–010 pass.

### E04 — Implement compatibility and capability checks

Goal: reject impossible environments before provider imports or side effects.

Relevant surface: `src/shuetl/compatibility.py`, `src/shuetl/errors.py`, the
existing facade constructor, and isolated compatibility fixtures.

Required work:

- Inspect distribution metadata using `importlib.metadata`.
- Validate exact core and installed ETLantic train versions.
- Validate optional SQLite distributions before importing provider code.
- Add bounded authored errors and exact remediation strings.
- Invoke the core check from `ShuETL.__init__` without changing API identity.

Verification: use distribution metadata and import/construction spies for every
missing, wrong, mixed, and exact package case.

Documentation/configuration: publish exact supported and remediation tables;
do not widen dependency ranges.

Dependencies: E02.

Exit: AC-011–013 and the compatibility regression portion of AC-023 pass.

### E05 — Implement the memory provider bundle

Goal: provide the minimal useful local construction path.

Relevant surface: `src/shuetl/providers.py`, `src/shuetl/__init__.py`, provider
unit tests, and memory integration fixtures.

Required work:

- Validate injected upstream identity/authorization contracts.
- Construct only the three public memory stores.
- Construct `ETLanticAPI` with exact object identity and development profile.
- Implement frozen properties, isolation, development-only metadata, and no-op
  idempotent cleanup.
- Add no grant, anonymous principal, or convenience authorization policy.

Verification: assert exact upstream types and identities, optional-provider
absence, graph isolation, and no-op cleanup.

Documentation/configuration: draft the explicit host identity/authorization
portion of the memory quickstart.

Dependencies: E03 and E04.

Exit: AC-014–018 pass for memory.

### E06 — Implement the qualified SQLite bundle

Goal: add persistent local evaluation without claiming production support.

Relevant surface: the optional branch in `src/shuetl/providers.py`, SQLite
fixtures, migration-state fixtures, and cleanup/redaction tests.

Required work:

- Parse only the approved local file URL forms.
- Prove missing-file checks and doctor checks are non-creating.
- Build the engine through the public upstream helper.
- Inspect exact migration head without applying migrations.
- Construct the three upstream SQLModel stores over one engine.
- Dispose the engine on every failed path and through idempotent `close()`.
- Test behind, current, ahead, corrupt, locked, and driver-error cases with
  complete redaction.

Verification: use real temporary provider databases plus spies around table and
migration APIs; snapshot filesystem state and engine disposal counts.

Documentation/configuration: document the optional extra, supported file URLs,
upstream-only provisioning step, expected head, and mandatory cleanup.

Dependencies: E05.

Exit: AC-019–022 pass.

### E07 — Implement typed diagnostics and CLI

Goal: make configuration/provider failures actionable to humans and automation.

Relevant surface: `src/shuetl/diagnostics.py`, `src/shuetl/cli.py`, the console
entry point, golden reports, and subprocess tests.

Required work:

- Implement exact frozen report/check models.
- Collect stable distribution, settings, capability, readiness, schema, and
  topology facts.
- Convert expected settings/provider errors into authored checks.
- Render equivalent text and deterministic JSON.
- Implement the exact argparse grammar and exit behavior.
- Add an outer redaction guard for unexpected CLI exceptions.

Verification: compare typed facts across text/JSON, exercise all check statuses
and CLI exits, and scan stdout/stderr/logs with the secret sentinel corpus.

Documentation/configuration: add command syntax, report schema, check meanings,
exit codes, and remediation guarantees.

Dependencies: E03–E06.

Exit: AC-025–034 pass.

### E08 — Prove facade and upstream behavior preservation

Goal: demonstrate that configuration is composition, not a new control plane.

Relevant surface: existing facade and HTTP tests, bundle-parameterized contract
fixtures, boundary checks, and OpenAPI capture tooling.

Required work:

- Run existing 0.2 facade and HTTP contracts unchanged.
- Parameterize the applicable suite across memory and SQLite bundles.
- Compare normalized OpenAPI to the 0.2 evidence document.
- Spy for provider lifecycle, migration, table creation, route creation,
  background work, and execution.
- Verify `bundle.close()` remains host-controlled.

Verification: run the unchanged 0.2 suite, shared real-provider HTTP contracts,
normalized OpenAPI comparison, and prohibited-call spies.

Documentation/configuration: record compatibility evidence only; do not change
the 0.2 user contract or route documentation.

Dependencies: E06.

Exit: AC-023, AC-024, AC-037, and AC-038 pass.

### E09 — Add installed-wheel tutorials and documentation

Goal: provide a truthful install-to-first-run local experience.

Relevant surface: both Phase 0.3 examples, `README.md`, `CHANGELOG.md`, and a
focused configuration/doctor guide if needed for readability.

Required work:

- Add a memory quickstart with explicit settings, host identity/context,
  deny-by-default authorization grants, an application-owned definition, mount,
  and request proof.
- Add a SQLite example with a visibly separate upstream provisioning step,
  schema preflight, bundle construction, and `finally: bundle.close()`.
- Document every environment variable, precedence rule, doctor status, exit
  code, remediation, lifecycle responsibility, and local-only limitation.
- Keep examples executable outside the source checkout.

Verification: execute copied examples from core and SQLite wheel installations
with no repository import path.

Documentation/configuration: complete all user-facing settings, environment,
ownership, migration, cleanup, diagnostics, and limitation material.

Dependencies: E07 and E08.

Exit: AC-035, AC-036, and AC-041 pass.

### E10 — Generalize gates and assemble 0.3 evidence

Goal: produce one self-bootstrapping release gate for core and optional paths.

Relevant surface: release scripts, clean-wheel/artifact/evidence checks,
`.github/workflows/checks.yml`, and `docs/evidence/0.3/`.

Required work:

- Remove remaining hardcoded 0.2 labels/paths from release scripts and CI.
- Run core and SQLite-extra clean-wheel checks in isolated environments.
- Capture 0.3 environment, compatibility, ownership, CLI, schema, redaction,
  OpenAPI, artifact, and AC evidence.
- Retain 0.1 and 0.2 evidence as history.
- Ensure artifacts and evidence contain no SQLite file or secret value.

Verification: run the one-command gate locally, then from a source archive, and
validate exact artifact/evidence hashes.

Documentation/configuration: make gate/evidence paths version-derived and CI
job names phase-neutral while preserving the release workflow trust chain.

Dependencies: E09.

Exit: AC-039, AC-040, and AC-042 pass locally.

### E11 — Final release qualification

Goal: establish a reviewable 0.3.0 candidate.

Relevant surface: the exact candidate commit, built distributions, CI run,
release evidence, documentation, and review reports; no new feature module.

Required work:

1. Run the complete release gate in the working repository.
2. Run it again from an archive or fresh clone of the exact candidate commit.
3. Execute both examples from installed wheels outside the checkout.
4. Run core and SQLite-extra paths on Python 3.11, 3.12, and 3.13 in CI.
5. Verify artifact hashes, import origins, migration head, normalized OpenAPI,
   doctor fixtures, and the redaction sentinel set.
6. Audit every changed file against the touched surface and explicit non-scope.
7. Obtain normal production review and an independent release check before a
   `v0.3.0` tag.

Verification: all AC evidence, full gates, clean installs, examples, and review
verdicts must refer to the same candidate commit.

Documentation/configuration: freeze release notes and evidence to observed
behavior; do not revise public scope during qualification.

Dependencies: E10.

Exit: every AC maps to passing evidence and no release blocker remains.

## Risks and mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| Missing config silently selects memory | Development behavior reaches an unintended environment | Make profile, role, provider, and identity required literals |
| Settings source surprise | A local file overrides reviewed environment/config | Disable dotenv, file-secret, and structured-file sources |
| Database URL leaks | Credentials or machine paths enter logs/evidence | `SecretStr`, serialization exclusion, authored errors, sentinel scans |
| Optional import occurs before validation | Wrong plugin code executes in an incompatible environment | Inspect distribution metadata before provider import |
| SQLite fallback to memory | Apparent success loses persistence | Fail with exact capability/readiness errors; never fallback |
| Doctor creates a missing DB | A read-only command mutates the filesystem | Check parsed file target before engine creation and assert absence afterward |
| Startup migrates schema | Deployment mutates state implicitly | Never call create/migrate functions; require exact pre-existing head |
| Engine leaks on failure | File locks/resource leaks make local use unreliable | Dispose on every failed path and make `close()` idempotent |
| Bundle takes identity ownership | Local convenience weakens auth boundary | Require caller authorizer/context/principal inputs with no defaults |
| Provider bundle grows into domain facade | ShuETL duplicates ETLantic semantics | Expose exact upstream protocols and no repository methods |
| Doctor becomes a second `/ready` | Conflicting operational contracts | CLI/Python preflight only; no route and no live service claim |
| Route preset implies filtering | OpenAPI/HTTP contract drifts | Accept only literal `complete`; retain ADR-0006 |
| Full memory provider graph balloons scope | Optional control-plane semantics are enabled accidentally | Construct only definitions, submissions, and events |
| Direct SQLAlchemy use widens dependency burden | Transitive implementation detail becomes accidental API | Keep it optional, exact-pinned, limited to URL/connection/disposal, and revisit on upstream lifecycle support |
| 0.2 regressions hide behind new tests | Existing users break while local DX passes | Run the entire unchanged 0.2 suite and compare OpenAPI |

## Known pre-existing problems and follow-up candidates

Repository and upstream issue searches found these open, non-blocking items:

- [ShuETL #1](https://github.com/eddiethedean/shuetl/issues/1) tracks upgrading
  GitHub Actions away from deprecated Node.js 20 runtimes. Current CI passes
  because GitHub applies its compatibility runtime. Phase 0.3 must not absorb
  that upgrade unless the existing actions prevent an in-scope gate from
  running.
- [ShuETL #2](https://github.com/eddiethedean/shuetl/issues/2) tracks the
  deprecated Starlette `TestClient` path and related `BlockingPortal` warning.
  The test dependency now uses `httpx2`, but the upstream Starlette warning is
  still visible. It is a follow-up unless it causes a Phase 0.3 test failure or
  invalidates an HTTP assertion.
- [ETLantic #130](https://github.com/eddiethedean/etlantic/issues/130) tracks a
  stale `etlantic-fastapi` package docstring version. Runtime metadata is
  authoritative; this documentation defect does not block compatibility checks.
- PostgreSQL selection, production schema policy, and provider-owned migration
  commands remain Phase 0.4 work in the roadmap. They are planned scope, not a
  newly discovered defect, so no duplicate issue is needed.
- Production identity adapters remain Phase 0.5 work; scheduler/worker CLI roles
  and broader operational bounds remain Phase 0.6 work. Phase 0.3 must reject
  those selections rather than partially implement them.
- An upstream lifecycle wrapper for SQLModel provider bundles could later remove
  ShuETL's narrow optional SQLAlchemy lifecycle dependency. This is an
  architectural simplification candidate, not a correctness blocker for the
  bounded 0.3 contract.

No newly discovered unrelated repository defect lacks an appropriate existing
issue or roadmap owner. Do not require Luna to fix the items above for 0.3.

## Stop conditions

Stop implementation and return to architecture review if any is true:

- `etlantic-sqlmodel` cannot report schema state without mutation;
- a missing SQLite path cannot be diagnosed without creating a file;
- the exact SQLite stores cannot satisfy the same upstream HTTP contracts;
- engine cleanup requires a ShuETL database abstraction or migration ownership;
- `pydantic-settings` cannot disable implicit file sources deterministically;
- mixed package versions cannot be detected before importing optional code;
- redaction requires suppressing actionable check identifiers or statuses;
- local bundle construction requires ShuETL to invent identity, authorization,
  ETLantic domain models, routes, or execution semantics;
- the existing facade cannot remain backward-compatible.

If SQLite alone hits a stop condition, do not weaken its gate or silently ship
memory-only under the promised scope. Record the blocker, update ADR-0008 and
the roadmap, and make an explicit release-scope decision before continuing.

## Definition of done

Phase 0.3 is complete only when:

- every AC-001 through AC-042 criterion is satisfied by installed package code;
- all four security-sensitive selections are explicit;
- settings precedence and ignored sources are proven;
- memory and SQLite provider bundles use exact upstream objects;
- SQLite schema provisioning remains outside construction and startup;
- compatibility and capability failures happen before traffic and without
  fallback;
- provider resources are closed deterministically;
- doctor text/JSON, exit codes, and redaction are stable;
- the 0.2 facade and normalized OpenAPI remain compatible;
- both clean-wheel paths and examples pass on Python 3.11–3.13;
- evidence maps every AC exactly once and contains no secret or machine path;
- no deferred production, identity, migration, scheduling, worker, or execution
  work entered the release;
- normal production review and the independent release check approve tagging.

## Final planning decision

The 0.51.0 public memory and SQLModel APIs are sufficient for a bounded local
configuration release when identity remains caller-owned, SQLite requires an
already migrated file, and bundle cleanup stays explicit. ADRs 0007–0009 remove
the settings, provider, and diagnostic choices that were previously deferred.

**READY FOR IMPLEMENTATION**
