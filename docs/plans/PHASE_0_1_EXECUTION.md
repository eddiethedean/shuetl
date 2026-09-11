# Phase 0.1 Architecture and Implementation Contract

## Objective

Produce a reproducible ShuETL 0.1 evidence release that proves a separately
packaged composition layer is useful and technically viable without shipping
the 0.2 facade early.

The phase is complete when a reviewer can clone ShuETL without a neighboring
ETLantic checkout, run one release command, and verify packaging, public API
usage, the memory-provider HTTP flow, OpenAPI preservation, and architectural
boundaries.

This document is the authoritative implementation boundary for Phase 0.1. The
roadmap and high-level phase plan explain intent; when their detail conflicts
with this contract, this contract controls the 0.1 implementation.

## Repository Ground Truth

Ground truth was established on 2026-09-11 against:

- ShuETL commit `87da2af12e37bb5ae1dfd524c695d0e51b539709`;
- ETLantic commit `83f5e67e221d588ff895ad23f2cb7c684ac12c49`;
- published `etlantic==0.51.0` and `etlantic-fastapi==0.51.0`, both confirmed
  available from the configured Python package index;
- GitHub repositories `eddiethedean/shuetl` and `eddiethedean/etlantic`.

### ShuETL state

- The repository contains planning Markdown and a root README only.
- There is no `pyproject.toml`, package source, lock file, test suite, CI
  workflow, license file, changelog, script, migration, or release.
- `main` matches `origin/main` at the inspected commit.
- There are no open ShuETL GitHub issues and no feature issue defining a
  different 0.1 boundary.
- Existing planning consistently assigns domain and HTTP semantics upstream and
  reserves composition, compatibility, diagnostics, and deployment guidance
  for ShuETL.

### Upstream FastAPI seam

- `etlantic-fastapi` publicly exports `ETLanticAPI`, `include_router()`,
  `create_app()`, `install_exception_handlers()`, principal dependencies, and
  context factories.
- `ETLanticAPI` requires an authorizer, definition repository, submission store,
  event store, and context factory. Public memory implementations exist in
  `etlantic.control_plane`.
- `include_router()` writes `app.state.etlantic_api`, mounts the upstream router,
  returns `None`, and intentionally installs no lifespan, middleware, or
  exception handler.
- `create_app()` creates a dedicated FastAPI app, optionally installs the
  upstream problem handler and lifespan, and does not start execution work.
- Upstream tests already prove stable operation IDs, `202` submission,
  idempotent acceptance identity, authorization behavior, SSE contracts, and
  that embedded mode does not force exception handlers.
- The upstream adapter declares Python `>=3.11`, FastAPI `>=0.115,<1`, Pydantic
  `>=2.12,<3`, and ETLantic `>=0.51,<0.52`; its CI tests Python 3.11–3.13 on
  Linux, macOS, and Windows.

### Persistence and runtime seam

- `etlantic-sqlmodel==0.51.0` owns versioned control-plane migrations and
  exposes `current_version()`, `upgrade()`, `downgrade()`, and
  `apply_migrations()` from its migration package.
- ETLantic owns the `etlantic scheduler` and `etlantic worker` entry points.
- Phase 0.1 consumes neither SQLModel persistence nor execution roles. They are
  inventoried only so later work does not invent ShuETL-owned substitutes.

### Existing quality model

ShuETL has no existing gates to preserve. ETLantic provides the ecosystem
precedent: `uv`, Hatchling, Ruff, Pyright, pytest, locked dependencies, a
Python 3.11–3.13 OS matrix, documentation checks, and explicit release scripts.
Phase 0.1 adopts the smallest compatible subset described below.

## Architecture Summary

Phase 0.1 creates a typed but behaviorally inert `shuetl` distribution plus
repository-only proof tooling. The proof constructs the public ETLantic memory
graph and mounts the authoritative `etlantic-fastapi` router in an ordinary
FastAPI host. ShuETL does not wrap requests, responses, routes, providers, or
domain models.

```text
host FastAPI app
  ├── unrelated host route
  └── /etl → etlantic_fastapi.include_router(...)
                └── ETLanticAPI
                      ├── MemoryAuthorizer
                      ├── MemoryDefinitionRepository
                      ├── MemorySubmissionStore
                      └── MemoryEventStore
```

The package source contains no facade in 0.1. The spike, boundary checker,
OpenAPI comparator, and release verifier are repository tools. The output is
evidence that 0.2 can safely implement a narrow composition facade.

## Architectural Decisions

These decisions are resolved and authoritative. E04 records them as ADRs before
dependent implementation begins; E04 does not reopen them for the implementer.

| ADR | Decision |
|---|---|
| ADR-0001 | Keep ShuETL separate only while it owns material host composition, compatibility, diagnostics, and deployment value; merge upstream if it becomes only an alias for `include_router()` |
| ADR-0002 | Publish 0.1 for Python `>=3.11,<3.14`; prove exactly `etlantic==0.51.0` and `etlantic-fastapi==0.51.0`; record, but do not claim support for, the resolved FastAPI and Pydantic versions |
| ADR-0003 | The inert 0.1 package has no runtime dependencies; a `test` extra contains exact evidence dependencies; keep SQLModel, Alembic, schedulers, workers, and retry engines out of core |
| ADR-0004 | The 0.2 facade accepts a prebuilt `ETLanticAPI`; reference provider construction and settings begin in 0.3 |
| ADR-0005 | The 0.1 spike explicitly installs the upstream problem handler and uses no integration lifespan; the 0.2 facade must compose host lifespan and detect handler/state conflicts without silent replacement |
| ADR-0006 | The 0.2 facade exposes the complete upstream router under one validated prefix; it adds no route aliases or independent route presets |

Changing one of these decisions requires updating this contract and its
acceptance criteria before dependent implementation continues.

## Change Boundary

### Problem

The ShuETL concept is documented but not executable. There is no installable
artifact or isolated proof that the proposed host-composition boundary works
against published ETLantic packages. Without that proof, beginning the facade
would risk duplicating `etlantic-fastapi`, relying on private imports, or making
compatibility claims based only on a sibling checkout.

### Desired Outcome

After Phase 0.1:

- `shuetl` builds as a typed 0.1.0 wheel and source distribution;
- a clean environment can install that wheel and its test extra;
- a disposable spike mounts the published 0.51.0 upstream router at `/etl`;
- an unrelated host route, definition read, authorized idempotent submission,
  upstream errors, and OpenAPI parity are proven by tests;
- automated static checks enforce the intended package boundary;
- decisions and evidence make 0.2 implementable without architecture choices;
- a recorded boundary review chooses `proceed-to-0.2`,
  `blocked-on-upstream`, or `merge-into-etlantic-fastapi`.

### In Scope

- Python packaging, distribution metadata, PEP 561 marker, lock file, and
  changelog/license foundation.
- Repository test tooling and CI for Python 3.11, 3.12, and 3.13.
- The ETLantic 0.51 public-contract inventory and ShuETL ownership matrix.
- Six ADRs that record the decisions in this contract.
- One memory-provider integration spike using published packages.
- HTTP assertions for host coexistence, definition access, submission,
  idempotency, authentication failure, missing idempotency, and not-found.
- Direct-versus-embedded OpenAPI comparison and a normalized evidence snapshot.
- Static boundary checks against importable ShuETL source.
- Isolated wheel installation and one-command release verification.
- A release evidence index and explicit package-boundary decision.

### Touched Surface

The implementation may create or update only:

- root packaging and project files: `pyproject.toml`, `uv.lock`, `LICENSE`,
  `CHANGELOG.md`, and status text in `README.md`;
- `.github/workflows/ci.yml`;
- inert package files under `src/shuetl/`;
- repository-only proof code under `spikes/`, `scripts/`, and `tests/`;
- ADRs under `docs/adr/`;
- retained Phase 0.1 evidence under `docs/evidence/0.1/`;
- links or status updates in existing planning documents.

No ETLantic repository file is part of this change.

## Public Contract

### Required Behavior

The 0.1 public package contract is intentionally minimal:

- the distribution name is `shuetl` and its version is `0.1.0`;
- `Requires-Python` is `>=3.11,<3.14`;
- `import shuetl` succeeds after installing the wheel;
- `importlib.metadata.version("shuetl")` returns `0.1.0`;
- the wheel includes `shuetl/py.typed`;
- `shuetl` exports no facade, settings, provider, route, model, CLI, or runtime
  service in 0.1;
- the wheel declares no runtime dependency because importable 0.1 code consumes
  no third-party library;
- the `test` extra installs `etlantic==0.51.0`,
  `etlantic-fastapi==0.51.0`, FastAPI `>=0.115,<1`, and HTTPX `>=0.27,<1`;
- installed FastAPI and Pydantic versions are recorded in evidence, but 0.1
  makes no compatibility claim across their full allowed ranges;
- no behavior in `spikes/`, `scripts/`, `tests/`, or `docs/evidence/` is an
  end-user API compatibility promise.

The integration proof must preserve upstream behavior:

- `/etl/health` and the unrelated host route return successfully;
- authenticated callers can read the seeded definition;
- a valid submission with an idempotency key returns upstream `202` and the
  upstream acceptance representation;
- repeating the same submission returns the same acceptance and submission
  identities;
- missing authentication, missing idempotency, and missing definitions retain
  upstream status codes and `application/problem+json` responses;
- ETLantic operation IDs, response codes, media types, and component references
  match a direct upstream app after prefix normalization;
- no pipeline work executes during the HTTP request or through FastAPI
  `BackgroundTasks`.

### Validation and Errors

- The spike accepts no user configuration, imports, file paths, database URLs,
  or secrets.
- The fixed test prefix is `/etl`; configurable prefix validation is 0.2 work.
- The fixed principal is `alice`, mapped server-side to `tenant-a/ws-1`.
- An absent or unmapped principal must exercise upstream `401`/`PMCP401`.
- An unmapped or unauthorized principal must not receive the seeded definition.
- A submission without any upstream idempotency source must return upstream
  `400`/`PMCP400`.
- An authorized lookup of an unknown definition must return upstream
  `404`/`PMCP404`.
- Reusing an idempotency key with a different payload must return upstream
  `409`/`PMCP409` and preserve the original acceptance.
- Snapshot mismatch, forbidden import, missing artifact content, wrong import
  origin, or failed subprocess must make the verification command exit nonzero.

### Serialization

- HTTP serialization is entirely upstream-owned; the spike does not transform
  JSON bodies or define Pydantic response wrappers.
- The normalized OpenAPI artifact is repository evidence, not a public wire
  format. Its serializer sorts object keys and set-like lists and removes only
  fields explicitly listed as volatile.
- Release evidence must not contain machine-specific absolute paths, secrets,
  tokens, or timestamps whose only effect is nondeterminism.

### Extension Behavior

There is no ShuETL extension mechanism in 0.1. ETLantic optional providers may
appear in upstream OpenAPI, but the proof configures only the required memory
graph. Missing optional providers are neither installed nor replaced.

### Recommended Implementation

The required behavior does not depend on these internal choices, but the
preferred implementation is:

- Hatchling for builds;
- `uv` with a committed lock file;
- Ruff for format and lint;
- Pyright for type checking, matching the upstream ecosystem;
- pytest and FastAPI `TestClient` for proof tests;
- a stdlib `ast` boundary checker;
- a stdlib Python release orchestrator using checked subprocess calls;
- `tempfile.TemporaryDirectory` plus `venv` or `uv venv` for isolated wheel
  verification.

An implementer may adapt these internals only if every acceptance criterion and
the touched-surface boundary remain intact.

## Invariants

- ETLantic remains the sole semantic owner of definitions, submissions, runs,
  authorization, errors, events, reports, artifacts, schedules, and execution.
- `etlantic-fastapi` remains the sole owner of ETLantic HTTP routes, schemas,
  operation IDs, media types, and durable-accept behavior.
- Importable ShuETL source contains no ETLantic domain model, route, persistence
  model, scheduler, worker, or migration.
- The spike imports ETLantic contracts only from documented public package
  surfaces.
- Authorization occurs in the upstream route path before existence-sensitive
  access; the spike never performs a pre-authorization lookup.
- One idempotency key maps to one canonical upstream acceptance identity.
- The memory profile is labeled process-local and makes no restart-durability or
  production claim.
- Host routes and state outside `app.state.etlantic_api` remain untouched by the
  spike. The upstream state key itself is documented as an observed 0.51 seam.
- No request or application lifespan starts pipeline execution.
- All temporary environments are cleaned after success and failure.
- Verification uses installed wheels and fails if imports resolve from a
  sibling ETLantic checkout.

## Edge Cases and Failure Modes

| Case | Required result |
|---|---|
| Empty definition repository | list is empty through the upstream response; no synthetic ShuETL item appears |
| Known definition | upstream get/list returns `pipe-1` without ShuETL translation |
| Unknown definition with authorized caller | upstream `404` Problem Details response |
| Missing principal header | upstream unauthorized Problem Details response |
| Unmapped principal | upstream unauthorized response without definition disclosure |
| Missing idempotency key | upstream `400` and upstream problem code |
| Repeated identical submission | `202` with unchanged acceptance and submission identities |
| Same key with materially different request | upstream `409` conflict; the original acceptance remains canonical |
| Existing unrelated host route | route remains registered and returns its original response |
| Existing `app.state.etlantic_api` | record upstream overwrite behavior as a 0.2 conflict-detection requirement; do not solve it in the spike |
| Existing `ControlPlaneError` handler | record upstream replacement behavior; do not define 0.2 composition logic in 0.1 |
| Missing optional provider | baseline endpoints remain as upstream defines; no fallback provider is created |
| OpenAPI generation twice | normalized artifacts are byte-identical |
| Prohibited import fixture | checker exits nonzero with file, line, rule ID, and remediation |
| Package index unavailable | clean-wheel job fails clearly; cached editable/sibling code must not mask failure |
| Test interruption or subprocess failure | temporary environment is removed and release gate remains failed |

## Security and Reliability

- `X-Principal` is permitted only as an upstream demo/test adapter; no document
  may present it as production authentication.
- Membership scope is fixed in test setup and never derived from caller-supplied
  tenant or workspace values.
- Tests must cover missing and unmapped principals and confirm upstream problem
  responses are installed in embedded mode.
- Logs, committed evidence, snapshots, commands, and failure messages contain no
  resolved credential or secret-like value.
- The clean-wheel verifier clears or rejects `PYTHONPATH`, checks module origins,
  and runs outside the repository working directory.
- Test inputs are fixed and bounded; the spike opens no listener and contacts no
  service except the package index during environment installation.
- Memory stores are shared only within the test process. Concurrency,
  multiprocess coordination, restart recovery, and durable external effects are
  outside the support claim.
- Build, test, and evidence generation fail closed: missing snapshots, unknown
  allowlist entries, unresolved blocking gaps, or mismatched versions are
  failures.

## Compatibility

- Supported interpreter versions are CPython 3.11, 3.12, and 3.13.
- The evidence train is exactly ETLantic 0.51.0 plus
  `etlantic-fastapi` 0.51.0.
- FastAPI and Pydantic must satisfy the adapter's declared ranges and use the
  versions resolved in the committed lock file. Testing their full lower/upper
  range is not a 0.1 claim.
- HTTP compatibility is measured against `etlantic_fastapi.create_app()` built
  from an equivalent memory graph. Host-only routes and the `/etl` prefix are
  normalized before comparison.
- There is no persisted ShuETL data or migration compatibility obligation.
- There is no prior ShuETL package API to preserve.
- Optional ETLantic packages, AuthMate, Hedron, PostgreSQL, and plugin behavior
  are not compatibility targets for this phase.

## Planned repository shape

```text
.
├── .github/workflows/ci.yml
├── CHANGELOG.md
├── LICENSE
├── pyproject.toml
├── uv.lock
├── src/shuetl/
│   ├── __init__.py
│   └── py.typed
├── spikes/
│   └── phase_0_1_memory_mount.py
├── scripts/
│   ├── check_boundaries.py
│   ├── check_artifact.py
│   ├── check_clean_wheel.py
│   ├── capture_openapi.py
│   ├── check_evidence.py
│   └── check_release.py
├── tests/
│   ├── boundary/
│   │   ├── fixtures/
│   │   └── test_boundaries.py
│   ├── integration/test_memory_mount.py
│   └── unit/test_package.py
└── docs/
    ├── adr/
    │   ├── README.md
    │   └── 0001-...md through 0006-...md
    └── evidence/0.1/
        ├── README.md
        ├── contracts.md
        ├── ownership.md
        └── openapi.normalized.json
```

Only `src/shuetl` is shipped as importable code. The spike and evidence tooling
remain explicitly disposable.

## Acceptance Criteria

- **AC-001 — Distribution metadata:** Building the repository produces a
  `shuetl` 0.1.0 wheel and sdist whose metadata declares Python
  `>=3.11,<3.14` and no runtime dependencies.
- **AC-002 — Typed package contents:** The wheel contains only the intended
  importable package files, including `shuetl/__init__.py` and
  `shuetl/py.typed`, and contains no test, spike, ADR, evidence, migration, or
  provider module.
- **AC-003 — Minimal import contract:** In a clean wheel installation,
  `import shuetl` succeeds and `importlib.metadata.version("shuetl")` equals
  `0.1.0`; the package exports no facade, settings, route, provider, model, CLI,
  or runtime-service symbol.
- **AC-004 — Reproducible evidence dependencies:** Installing the wheel's
  `test` extra resolves exactly `etlantic==0.51.0` and
  `etlantic-fastapi==0.51.0`, compatible locked FastAPI/Pydantic versions, and
  no sibling or editable distribution.
- **AC-005 — Supported interpreter matrix:** Quality checks, tests, build, and
  the clean-wheel proof pass on Python 3.11, 3.12, and 3.13.
- **AC-006 — Public-contract inventory:** The inventory records every upstream
  symbol used by 0.1 or planned for 0.2 with its public import, owning
  distribution, version, maturity, evidence, first consumer, and disposition.
- **AC-007 — Ownership matrix:** Every roadmap capability has one semantic
  owner, an explicit ShuETL role, prohibited duplication, verification method,
  and first consuming release; no overlap is unexplained.
- **AC-008 — Architecture decisions:** ADR-0001 through ADR-0006 record the
  decisions in this contract, have status `Accepted`, and link to the relevant
  inventory and ownership evidence.
- **AC-009 — Host coexistence:** In the spike, a host-defined route returns its
  original `200` response after the ETLantic router is mounted at `/etl`.
- **AC-010 — Definition access:** Principal `alice` can list or fetch seeded
  definition `pipe-1` through the prefixed upstream route and receives the
  upstream response model without ShuETL translation.
- **AC-011 — Durable-accept contract:** An authorized submission carrying a
  fixed `Idempotency-Key` returns upstream `202`, status `accepted`, and
  nonempty acceptance and submission identities.
- **AC-012 — Idempotent replay:** Repeating the same submission with the same
  idempotency key returns `202` with the same acceptance and submission
  identities and does not create a second accepted record; reusing the key with
  a different payload returns upstream `409` without changing the original.
- **AC-013 — Upstream failures:** Missing authentication returns the upstream
  `401`/`PMCP401` Problem Details response, missing idempotency returns
  `400`/`PMCP400`, and an authorized unknown-definition lookup returns
  `404`/`PMCP404`; all use `application/problem+json`.
- **AC-014 — No request-owned execution:** The proof starts no scheduler,
  worker, execution loop, or FastAPI `BackgroundTasks` pipeline work.
- **AC-015 — OpenAPI parity:** After stripping `/etl` and excluding the host-only
  route, embedded ETLantic paths, methods, operation IDs, response codes, media
  types, and referenced component names equal those from an equivalent direct
  upstream `create_app()`.
- **AC-016 — Deterministic OpenAPI evidence:** Two consecutive normalized
  OpenAPI generations are byte-identical, operation IDs are unique, and no
  ETLantic domain component is replaced by a ShuETL schema.
- **AC-017 — Static boundary pass:** The boundary checker accepts the real
  `src/shuetl` tree and approved public-composition fixture.
- **AC-018 — Static boundary rejection:** A dedicated negative fixture for each
  prohibited import, private import, route decorator, shadow domain class, and
  migration directory fails with file, line, rule ID, and remediation.
- **AC-019 — Isolated wheel proof:** The clean-wheel verifier installs the built
  wheel and test extra in a temporary environment, runs from outside the
  repository, proves ShuETL and ETLantic import origins are installed
  distributions, executes the spike, and removes the environment on exit.
- **AC-020 — Evidence completeness:** The evidence index maps every AC to its
  proof and result, contains no unresolved blocking gap or sensitive/machine-
  specific value, and records one boundary-review outcome.
- **AC-021 — Single release gate:** `uv run python scripts/check_release.py`
  performs lock, format, lint, type, static boundary, test, build, artifact,
  clean-wheel, and evidence checks; it exits nonzero on any failure.
- **AC-022 — Scope containment:** The change adds no public facade, settings,
  provider builder, route, persistence model, migration, scheduler, worker,
  database integration, authentication product, deployment implementation, or
  production support claim.

## Verification Matrix

| AC | Preferred proof | Verification target |
|---|---|---|
| AC-001 | Build + contract test | wheel/sdist metadata inspection |
| AC-002 | Static artifact test | wheel member allowlist |
| AC-003 | Compatibility test | isolated interpreter import and metadata assertions |
| AC-004 | Compatibility test | installed distribution versions and origins |
| AC-005 | CI matrix | Python 3.11, 3.12, and 3.13 jobs |
| AC-006 | Static gate + manual review | contract inventory schema and completeness |
| AC-007 | Static gate + manual review | ownership matrix coverage and uniqueness |
| AC-008 | Static gate + manual review | ADR filenames, statuses, links, and decisions |
| AC-009 | Integration test | host route before/after upstream mount |
| AC-010 | Integration test | prefixed definition request |
| AC-011 | Integration/contract test | first submission receipt |
| AC-012 | Integration/contract test | repeated submission and store cardinality |
| AC-013 | Integration/contract test | 401/400/404 Problem Details cases |
| AC-014 | Static gate + integration assertion | no execution imports/startup/background tasks |
| AC-015 | Contract test | normalized direct-versus-embedded OpenAPI comparison |
| AC-016 | Determinism test | two generated snapshots and schema-owner assertions |
| AC-017 | Static gate | real source and positive fixture |
| AC-018 | Unit/property-style fixture matrix | one expected diagnostic per forbidden category |
| AC-019 | Clean-install integration test | temporary environment and import origins |
| AC-020 | Static evidence gate + manual review | AC coverage, gap dispositions, redaction, outcome |
| AC-021 | End-to-end release test | release orchestrator success and injected failure |
| AC-022 | Static gate + review | source/artifact allowlists and roadmap non-goals |

Manual review supplements executable proof only for architectural ownership and
the final proceed/merge decision. It does not replace an automatable acceptance
criterion.

## Implementation Phases

### Task Graph

| ID | Task | Depends on | Primary output | ACs | Gate |
|---|---|---|---|---|---|
| E01 | Capture the baseline | — | baseline evidence | AC-004, AC-020 | A |
| E02 | Inventory upstream contracts | E01 | `contracts.md` | AC-006 | A |
| E03 | Complete ownership matrix | E01 | `ownership.md` | AC-007 | A |
| E04 | Record six blocking ADRs | E02, E03 | accepted ADR-0001–0006 | AC-008 | A |
| E05 | Scaffold the distribution | E04 | buildable typed package | AC-001–AC-003 | B |
| E06 | Implement the disposable spike | E02, E05 | passing memory HTTP flow | AC-009–AC-014 | B |
| E07 | Capture normalized OpenAPI | E06 | reviewed snapshot and assertions | AC-015, AC-016 | B |
| E08 | Implement boundary enforcement | E03, E05 | checker and fixture tests | AC-014, AC-017, AC-018, AC-022 | B |
| E09 | Add CI and clean-wheel verification | E05–E08 | green supported-version matrix | AC-004, AC-005, AC-019 | C |
| E10 | Assemble release evidence | E09 | reproducible evidence index | AC-020 | C |
| E11 | Review the stop conditions | E10 | proceed/merge/upstream decision | AC-020, AC-022 | C |
| E12 | Cut the local 0.1 artifact | E11 | wheel, sdist, changelog entry | AC-001–AC-005, AC-019–AC-022 | C |

The critical path is E01 → E02/E03 → E04 → E05 → E06 → E07/E08 → E09 →
E10 → E11 → E12.

### Gate A — Boundary and decisions

#### E01 — Capture the baseline

Create `docs/evidence/0.1/README.md` with:

- OS and architecture;
- Python and `uv` versions;
- installed versions and import origins for ETLantic, `etlantic-fastapi`,
  FastAPI, Pydantic, and HTTPX;
- the command used to create the isolated environment;
- confirmation that `PYTHONPATH` is unset and no editable dependency is used;
- the ETLantic 0.51 public documentation or package source revision inspected.

Acceptance:

- [ ] every version and import origin is captured by a repeatable command;
- [ ] no import resolves from a sibling checkout or editable distribution;
- [ ] evidence inputs are exactly 0.51.0 where an ETLantic package is involved.

#### E02 — Inventory upstream contracts

Create `docs/evidence/0.1/contracts.md` with one row per consumed or reserved
contract. Required columns are:

```text
capability | public symbol | import path | distribution | version inspected |
upstream maturity | first ShuETL consumer | evidence | disposition
```

Inventory at minimum:

- `ETLanticAPI`, `include_router()`, `create_app()`, and
  `install_exception_handlers()`;
- principal dependency and context factory contracts;
- `Authorizer`, definition repository, submission store, and event store;
- the four memory implementations used by the spike;
- durable-work, schedule, registry, history, report, and artifact surfaces;
- health, readiness, problem details, SSE, operation IDs, and OpenAPI behavior;
- SQLModel persistence and migration entry points reserved for 0.4;
- scheduler and worker entry points reserved for 0.6.

For reserved contracts, “not consumed in 0.1” is an acceptable disposition.
Private modules, test-only helpers, and inferred behavior are not acceptable
public-contract evidence.

Acceptance:

- [ ] every symbol used by the spike appears in the inventory;
- [ ] every planned 0.2 dependency has a public import path;
- [ ] later-phase symbols are clearly marked reserved rather than supported;
- [ ] any missing public seam is classified as blocking, deferred, or upstream.

#### E03 — Complete the ownership matrix

Create `docs/evidence/0.1/ownership.md` with these columns:

```text
capability | semantic owner | HTTP owner | ShuETL role | prohibited ShuETL work |
verification | first release
```

Cover definitions, plans, submissions, runs, attempts, retries, schedules,
events, reports, artifacts, authorization, persistence, migrations, API routes,
OpenAPI, settings, provider wiring, lifespan, problem handlers, diagnostics,
deployment profiles, scheduler/worker startup, and optional adapters.

Acceptance:

- [ ] every capability named in the roadmap has exactly one semantic owner;
- [ ] every ShuETL responsibility is composition, validation, selection, or
      documentation;
- [ ] any exception has an accepted ADR and removal or merge strategy.

#### E04 — Record the blocking ADRs

Create `docs/adr/README.md` with an ADR status table and write:

1. `0001-package-boundary-and-merge-trigger.md`;
2. `0002-initial-compatibility-policy.md`;
3. `0003-dependency-boundaries.md`;
4. `0004-facade-input-policy.md`;
5. `0005-host-lifespan-and-problem-handlers.md`;
6. `0006-route-selection.md`.

Each ADR must contain context, the decision stated in this contract,
alternatives, consequences, validation evidence, and a revisit trigger.
ADR-0001 must include the explicit package stop conditions. ADR-0002 must state
that 0.1 proves the exact 0.51.0 ETLantic train and makes no broader FastAPI or
Pydantic range claim.

Acceptance:

- [ ] all six ADRs have status `Accepted` and reproduce this contract's
      decisions without introducing new choices;
- [ ] each ADR links to relevant contract and ownership rows;
- [ ] no unresolved choice changes the 0.2 public shape or 0.1 dependency set;
- [ ] rejected alternatives are recorded rather than deleted.

Gate A passes when E01–E04 are complete. Do not implement package code meant to
survive into 0.2 before this gate.

### Gate B — Technical proof

#### E05 — Scaffold the distribution

Create:

- `pyproject.toml` using `hatchling` and a `src/` layout;
- `src/shuetl/__init__.py` with only package metadata needed for 0.1;
- `src/shuetl/py.typed`;
- `tests/unit/test_package.py` covering import and distribution metadata;
- `LICENSE` and `CHANGELOG.md`;
- Ruff, Pyright, and pytest configuration in `pyproject.toml`.

Dependency rules:

- set `requires-python = ">=3.11,<3.14"`;
- leave `[project].dependencies` empty because 0.1 importable code has no
  third-party imports;
- provide a `test` extra with `etlantic==0.51.0`,
  `etlantic-fastapi==0.51.0`, `fastapi>=0.115,<1`, and `httpx>=0.27,<1`;
- commit the resolved FastAPI and Pydantic versions in `uv.lock` and evidence;
- do not add `pydantic-settings` until ShuETL imports it for 0.3 settings;
- put build, Ruff, Pyright, and pytest tooling in the development dependency
  group;
- do not add a PostgreSQL extra in 0.1;
- do not export `ShuETL`, `ShuETLSettings`, provider builders, or lifecycle
  helpers yet.

Acceptance commands:

```bash
uv lock
uv sync --all-groups --extra test
uv run python -c "import shuetl; from importlib.metadata import version; assert version('shuetl') == '0.1.0'"
uv build
```

Acceptance:

- [ ] wheel and sdist build successfully;
- [ ] the wheel contains `shuetl/__init__.py` and `shuetl/py.typed`;
- [ ] artifact metadata has no unconditional runtime `Requires-Dist` entries and
      includes the declared test extra;
- [ ] core imports succeed without optional packages;
- [ ] the public package surface contains no provisional 0.2 facade.

#### E06 — Implement the disposable memory spike

Create `spikes/phase_0_1_memory_mount.py` and
`tests/integration/test_memory_mount.py`. The test may import reusable setup
from the spike, but no spike code may move into `src/shuetl`.

The spike must use public imports to:

1. import ShuETL and record its installed distribution version and origin;
2. construct `MemoryAuthorizer`, `MemoryDefinitionRepository`,
   `MemorySubmissionStore`, and `MemoryEventStore`;
3. create a membership context for principal `alice` in `tenant-a/ws-1`;
4. grant `definition.list`, `definition.read`, and `run.submit` to that context;
5. construct `ETLanticAPI`;
6. create an ordinary host `FastAPI` app with one unrelated host route;
7. explicitly install the upstream exception handler;
8. call upstream `include_router(app, api, prefix="/etl")`;
9. assert the host route still works;
10. assert the initial definition list is empty;
11. seed `pipe-1` through the public definition repository API;
12. list and fetch `pipe-1` through `/etl/v1/...`;
13. submit with `X-Principal` and `Idempotency-Key` headers and assert `202`;
14. repeat the same submission and assert both canonical identities are
    unchanged;
15. reuse that key with a changed payload and assert upstream `409` while the
    original acceptance remains unchanged;
16. assert the submission store still contains one logical accepted record;
17. assert missing principal, unmapped principal, missing idempotency, and
    authorized missing-definition requests retain upstream error behavior;
18. generate the embedded host OpenAPI document;
19. build a separate, equivalent memory graph with upstream `create_app()` and
    generate its direct OpenAPI document.

The spike must not start a scheduler, worker, lifespan-owned executor, or
FastAPI `BackgroundTasks` job.

Acceptance:

```bash
uv run pytest tests/integration/test_memory_mount.py -q
uv run python spikes/phase_0_1_memory_mount.py
```

- [ ] both commands pass;
- [ ] the test asserts status codes and canonical IDs, not only response shape;
- [ ] error assertions include status, media type, and stable upstream problem
      code where one is published;
- [ ] every non-stdlib import is listed in `contracts.md` or is test tooling;
- [ ] the memory limitation is stated in the script output and evidence index.

#### E07 — Capture normalized OpenAPI evidence

Create `scripts/capture_openapi.py` and commit
`docs/evidence/0.1/openapi.normalized.json`. Generate both an embedded document
and a direct upstream `create_app()` document from equivalent provider graphs.
Normalize them to retain only stable evidence:

- OpenAPI major/minor version;
- sorted paths;
- method, operation ID, response status codes, and schema references;
- component schema names and their `$ref` relationships;
- media types, including `text/event-stream` where exposed.

Exclude server URLs, generation timestamps, unrelated host metadata, and the
host-only route. Strip `/etl` only for the embedded-to-direct comparison. Tests
must assert:

- every operation ID is unique;
- required ETLantic operation IDs are present under `/etl` before normalization;
- normalized upstream paths, methods, operation IDs, response codes, media
  types, and referenced component names match the direct upstream app;
- definition and submission operations use upstream schemas;
- no component schema name starts with `ShuETL`;
- the only path-level difference attributable to the embedding proof is the
  `/etl` prefix;
- refreshing the snapshot is an explicit command, never an automatic test
  side effect.

Acceptance:

- [ ] the snapshot is deterministic across two consecutive generations;
- [ ] deleting or renaming a required upstream operation makes the test fail;
- [ ] introducing a ShuETL shadow response schema makes the test fail.

#### E08 — Implement boundary enforcement

Create an AST-based `scripts/check_boundaries.py` and pytest fixtures. Scan only
`src/shuetl` for production rules; use fixtures to prove each failure mode.

Reject:

- direct import roots `apscheduler`, `tenacity`, `sqlmodel`, `alembic`,
  `celery`, and `dramatiq`;
- ETLantic or `etlantic_fastapi` import segments beginning with `_`;
- FastAPI route decorators in ShuETL source;
- ShuETL classes named `Pipeline`, `Plan`, `Run`, `Attempt`, `Schedule`,
  `Firing`, `Event`, `Report`, `Artifact`, `Executor`, or `Authorizer`;
- production directories named `migrations` or `alembic`;
- duplicate OpenAPI operation IDs in the generated integration document.

Allow public `etlantic`, `etlantic.control_plane`, and `etlantic_fastapi`
imports used for composition. Keep rule exceptions in a reviewed data structure
that requires an ADR identifier and explanation.

Acceptance:

```bash
uv run python scripts/check_boundaries.py
uv run pytest tests/boundary -q
```

- [ ] the real source tree and positive fixture pass;
- [ ] one fixture per prohibited category fails for the expected reason;
- [ ] checker diagnostics include file, line, rule ID, and remediation;
- [ ] the checker does not scan documentation prose as production code.

Gate B passes when E05–E08 are complete and all acceptance commands pass.

### Gate C — Reproducibility and release decision

#### E09 — Add CI and clean-wheel verification

Create `.github/workflows/ci.yml` with:

- a quality job for Ruff, Pyright, boundary checks, and all pytest tests;
- a Python 3.11, 3.12, and 3.13 test matrix;
- dependency installation via `uv sync --locked --all-groups --extra test`;
- a build job for wheel and sdist;
- a clean-wheel job that does not install ShuETL editable and does not expose
  the repository root or sibling checkout through `PYTHONPATH`;
- uploaded wheel, sdist, and normalized OpenAPI evidence artifacts.

Create `scripts/check_clean_wheel.py`. It must create a temporary virtual
environment, install the built wheel with only its declared test dependencies,
copy the spike to a temporary working directory, run it there, verify import
origins, and delete the environment on exit.

Acceptance:

- [ ] all supported Python jobs pass;
- [ ] `importlib.metadata` reports the expected ShuETL and ETLantic versions;
- [ ] `shuetl.__file__` resolves inside the temporary environment;
- [ ] ETLantic imports resolve from installed distributions;
- [ ] the spike passes when the repository is not the working directory.

#### E10 — Assemble the release evidence

Finish `docs/evidence/0.1/README.md` as the gate index. For every Phase 0.1 exit
criterion, link:

- the responsible task;
- the test or command;
- the retained artifact;
- the result;
- any residual limitation;
- the reviewer and review date.

Add a gap register with only these dispositions:

- `blocking` — Phase 0.1 cannot pass;
- `upstream` — requires an ETLantic or `etlantic-fastapi` change;
- `deferred:<release>` — intentionally owned by a later ShuETL release;
- `accepted-risk` — requires an ADR and cannot contradict a stop condition.

No raw credential, environment secret, absolute developer-home path, or
unstable timestamp belongs in committed evidence.

#### E11 — Review the stop conditions

Conduct one explicit package-boundary review. Answer:

1. What integration burden did the spike expose beyond `include_router()`?
2. Can ShuETL address it using only public composition hooks?
3. Did any test require a copied route, schema, control-plane model, or runtime
   service?
4. Is the planned 0.2 facade materially easier and safer than direct upstream
   composition?
5. Is any required hook better contributed to `etlantic-fastapi` first?

Record exactly one outcome in the evidence index:

- `proceed-to-0.2`;
- `blocked-on-upstream` with linked upstream work;
- `merge-into-etlantic-fastapi` with rationale.

Only `proceed-to-0.2` permits E12.

#### E12 — Cut the local 0.1 artifact

Create `scripts/check_release.py` as the single local gate command. It should
run discrete subprocesses and stop on the first failure:

```text
lock check
format check
lint
typing
boundary checks
tests
build
artifact-content check
clean-wheel spike
evidence consistency check
```

Then:

- add the 0.1 entry to `CHANGELOG.md`;
- update the root README status to “0.1 boundary proof”;
- build final wheel and sdist;
- record their SHA-256 digests in the evidence index;
- verify the working tree contains no generated environment or credential;
- create a release tag or publish only as a separately authorized release
  action.

Final acceptance command:

```bash
uv run python scripts/check_release.py
```

Gate C passes only when the command exits zero and the E11 outcome is
`proceed-to-0.2`.

## Test inventory

| Test | Proves | Task |
|---|---|---|
| package import and version | typed wheel foundation is coherent | E05 |
| host route survives mounting | embedding does not take over unrelated routes | E06 |
| definition read/list | upstream definition contract remains reachable | E06 |
| first submission returns `202` | upstream durable-accept contract is preserved | E06 |
| repeated idempotency key returns same identity | ShuETL introduces no duplicate submission semantics | E06 |
| unauthorized definition request is denied | upstream authorization remains in the request path | E06 |
| normalized OpenAPI snapshot | operation IDs and schema references remain upstream-owned | E07 |
| boundary positive fixture | approved public composition imports remain possible | E08 |
| boundary negative fixtures | prohibited dependencies and shadow concepts are rejected | E08 |
| clean-wheel spike | proof does not depend on editable or sibling sources | E09 |
| Python 3.11–3.13 matrix | declared interpreter range is exercised | E09 |

## Commit boundaries

Use small reviewable commits in this order:

1. `docs: record 0.1 upstream contracts and ownership`
2. `docs: accept 0.1 boundary ADRs`
3. `build: scaffold typed shuetl distribution`
4. `test: add 0.1 memory-provider integration spike`
5. `test: preserve upstream OpenAPI evidence`
6. `test: enforce shuetl package boundaries`
7. `ci: add isolated wheel and supported-python gates`
8. `docs: record 0.1 release evidence and decision`

Do not combine an ADR decision and its dependent implementation in the same
commit; reviewers must be able to accept or replace the decision first.

## Phase completion checklist

- [ ] E01–E04 complete; Gate A recorded.
- [ ] E05–E08 complete; Gate B recorded.
- [ ] E09–E12 complete; Gate C recorded.
- [ ] Six blocking ADRs are accepted.
- [ ] Contract inventory and ownership matrix are reviewed.
- [ ] All tests run against installed ETLantic 0.51 distributions.
- [ ] Clean-wheel spike passes outside the repository.
- [ ] OpenAPI evidence is deterministic and contains no shadow schemas.
- [ ] Boundary checker has passing and failing fixtures.
- [ ] Release command exits zero on Python 3.11–3.13 CI.
- [ ] Evidence index records `proceed-to-0.2`.
- [ ] No 0.2 facade or 0.3 settings API leaked into the 0.1 package.

## Risks

| Risk | Impact | Required treatment |
|---|---|---|
| `include_router()` overwrites `app.state.etlantic_api` | A host collision could make the future facade unsafe | Record the observed behavior; test only a collision-free host in 0.1; require detection/composition in ADR-0005 and 0.2 |
| `install_exception_handlers()` can replace a same-type host handler | Silent handler takeover would violate host composition | Use a host with no prior `ControlPlaneError` handler in the spike; record collision handling as 0.2 work |
| ETLantic 0.x public surface changes quickly | Evidence can become stale | Exact-pin 0.51.0, store normalized evidence, and do not claim later minor compatibility |
| Optional upstream routes appear in OpenAPI without configured providers | A raw full-document snapshot may overstate supported capabilities | Compare contract shape for parity but label the configured baseline separately from optional route availability |
| Sibling checkout masks packaging defects | Local success would not prove installability | Clear/reject `PYTHONPATH`, inspect import origins, and run the spike from a temporary directory |
| Evidence tooling leaks into the wheel | Repository-only experiments could become accidental API | Enforce a wheel member allowlist in AC-002 |
| Static name rules create false positives | Legitimate future composition code could be blocked | Scope scanning to `src/shuetl`, use rule IDs, and require documented ADR-bound exceptions |
| Package-index or network outage | Clean installation cannot complete | Fail the gate clearly; do not fall back to editable or sibling sources |
| The spike proves only an alias-sized value | A separate package may not be justified | E11 requires an explicit merge/upstream/proceed decision before the artifact is cut |

## Explicit Non-Scope

The following are not required for Phase 0.1 and must not be added to satisfy a
review comment unless this contract is deliberately revised:

- `ShuETL` or `ShuETLSettings` implementation;
- configurable mounting, duplicate-mount detection, prefix validation, handler
  conflict resolution, lifespan composition, or app-state namespacing;
- environment-driven configuration or provider construction;
- PostgreSQL, SQLite, SQLModel stores, database connectivity, or migrations;
- scheduler, worker, executor, retry, lease, fencing, or process-role code;
- persistence, restart recovery, multiprocess concurrency, or production
  topology proof;
- custom HTTP routes, copied handlers, alternate schemas, clients, or generated
  endpoint vocabulary;
- AuthMate, Hedron, observability, artifact-store, broker, cloud, or identity
  integrations;
- CLI commands, application server startup, container files, deployment
  manifests, runbooks, or publication automation;
- full FastAPI/Pydantic lower-and-upper-bound testing;
- support for ETLantic releases other than exactly 0.51.0;
- repair of upstream defects that do not block the public 0.51 composition seam;
- cleanup or modernization of planning documents unrelated to the 0.1 gate.

## Known Follow-Up Candidates

- **ETLantic issue
  [#130](https://github.com/eddiethedean/etlantic/issues/130):** the
  `etlantic_fastapi` package docstring says 0.39.0 while package metadata and
  `__version__` say 0.51.0. This is upstream documentation drift and does not
  block 0.1.
- **0.2 host-state collision handling:** decide the exact error and behavior
  when `app.state.etlantic_api` already exists, consistent with ADR-0005.
- **0.2 exception-handler composition:** define how a host-owned
  `ControlPlaneError` handler is detected, preserved, or explicitly replaced.
- **0.2 lifespan API:** implement the already-decided composition responsibility
  without changing the 0.1 spike into production code.
- **0.3 configuration:** add settings, reference memory-provider construction,
  diagnostics, and local developer experience.
- **0.4 persistence:** qualify `etlantic-sqlmodel`, provider-owned migrations,
  and PostgreSQL separately.
- **0.6 roles:** integrate upstream scheduler and worker entry points in
  separate processes.

No follow-up candidate is a hidden Phase 0.1 acceptance criterion. Promote one
only by revising this contract and its AC/verification mapping.

## Definition of Done

This change is done when:

- AC-001 through AC-022 are satisfied with the proofs named in the verification
  matrix;
- Gate A, Gate B, and Gate C are recorded as passed;
- the exact ETLantic 0.51.0 and Python 3.11–3.13 compatibility claim is true;
- Ruff, Pyright, pytest, boundary, build, artifact, clean-wheel, OpenAPI, and
  evidence checks pass;
- required documentation matches observable behavior;
- the change introduces no known substantive regression to the documentation
  repository;
- independently discovered upstream or later-phase work remains classified as
  follow-up;
- no release blocker attributable to Phase 0.1 remains;
- E11 records `proceed-to-0.2` before a tag or publication is attempted.

The repository does not need to be globally defect-free, and ETLantic issue
#130 does not block this definition of done.

## Plan Status

**READY FOR IMPLEMENTATION**
