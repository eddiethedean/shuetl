# Phase 0.1 — Boundary Proof and Package Foundation

## Purpose

Phase 0.1 answers one question before ShuETL commits to a public facade:

> Does a separately packaged ShuETL remove meaningful application-integration
> work while leaving ETLantic and `etlantic-fastapi` authoritative?

This is an evidence release. Its output is a buildable package, a disposable
integration spike, boundary tests, and recorded decisions. It is not the first
usable ShuETL API; that begins in 0.2.

The concrete task sequence, target files, acceptance commands, and commit
boundaries are in [PHASE_0_1_EXECUTION.md](PHASE_0_1_EXECUTION.md).

## Evidence baseline

The spike starts from the ETLantic 0.51 release train and must revalidate these
facts against installed distributions rather than a sibling source checkout:

| Concern | 0.1 evidence baseline |
|---|---|
| Python | `>=3.11` |
| ETLantic | `etlantic==0.51.0` |
| FastAPI adapter | `etlantic-fastapi==0.51.0` |
| FastAPI range inherited by the adapter | `>=0.115,<1` |
| Pydantic range inherited by the adapter | `>=2.12,<3` |
| Embedding surface | `ETLanticAPI` and `include_router()` |
| Dedicated-app surface | `create_app()` |
| Required memory graph | authorizer, definitions, submissions, events, context factory |

These are spike inputs, not the final ShuETL support policy. The compatibility
ADR decides whether the published 0.1 metadata uses exact pins or a bounded
0.51 range. Evidence collected from editable installs or undeclared import
paths does not satisfy the release gate.

## Why a separate package is plausible

`etlantic-fastapi` already owns the routes and HTTP semantics. Its embedding
helper intentionally mounts the router without owning host lifespan,
middleware, or exception handlers, while its dedicated factory owns a complete
application. ShuETL has a defensible boundary if it can make those two modes
consistent for host applications, validate a supported provider graph, and
later add deployment-profile and readiness guidance without copying an
ETLantic model, route, or runtime service.

Phase 0.1 proves the upstream composition seam. Phase 0.2 is responsible for
turning that seam into a supported facade.

## Required artifacts

| Artifact | Required content | Completion evidence |
|---|---|---|
| Package foundation | `pyproject.toml`, `src/shuetl`, `py.typed`, tests, docs entry point, license/readme metadata | Wheel and sdist build; wheel imports in a clean environment |
| Compatibility record | Installed package versions, declared constraints, supported Python versions, and mismatch policy | ADR plus machine-readable test inputs |
| Public-contract inventory | Import path, owning distribution, stability/status, consumer in ShuETL, and upstream evidence for every used contract | Reviewed inventory with no private imports |
| Ownership matrix | Authoritative semantic owner, ShuETL responsibility, and prohibited duplication for every planned capability | No unexplained dual owner |
| Boundary ADR set | Six decisions listed in W3 | All accepted or the phase stops |
| Memory integration spike | Ordinary FastAPI host, upstream memory graph, upstream router, definition read/list, durable-accept submission contract, and OpenAPI generation | Executable test from an installed wheel |
| Boundary enforcement | Import rules and source checks | Positive and intentional negative tests |
| Release evidence index | Commands, artifact links, package versions, results, and unresolved observations | Reviewer can reproduce the gate without repository knowledge |

The inventory and matrix are different artifacts. The inventory records which
public symbols exist in the selected release; the matrix records which project
owns each product capability.

## Work packages

### W1 — Establish reproducible packaging

- Use a `src/` layout and expose only a version marker or similarly inert
  package surface.
- Mark the distribution as typed with `src/shuetl/py.typed`.
- Configure formatting, linting, typing, tests, distribution builds, and a
  clean-wheel smoke test.
- Test the supported Python versions selected by the compatibility ADR.
- Keep SQLModel, Alembic, schedulers, retry engines, workers, and artifact
  backends out of ShuETL's direct dependencies.

The package skeleton must not pre-empt the 0.2 constructor or settings ADRs.

### W2 — Inventory the upstream seam

Record public contracts for:

- `ETLanticAPI`, `include_router()`, `create_app()`, and exception handlers;
- principal and context factories and the ETLantic authorizer protocol;
- definition, submission, event, durable-work, schedule, history, report, and
  artifact contracts;
- memory-provider implementations used by the spike;
- SQLModel providers and provider-owned migration entry points intended for
  later phases;
- scheduler and worker entry points intended for role-separated deployment;
- upstream health, readiness, SSE, problem-detail, and OpenAPI behavior.

For every entry, capture the public import path, owner, version first inspected,
status or maturity stated upstream, and whether 0.1 uses it or merely reserves
it for a later phase. A source file existing upstream does not by itself make a
symbol public.

### W3 — Close only the decisions needed for 0.2

Phase 0.1 must accept ADRs for:

1. the ShuETL/`etlantic-fastapi` ownership line and merge trigger;
2. the initial Python, ETLantic, `etlantic-fastapi`, FastAPI, and Pydantic
   compatibility policy;
3. direct versus optional dependency policy;
4. the 0.2 facade input policy—prebuilt `ETLanticAPI`, ShuETL-constructed
   providers, or both;
5. host lifespan and problem-handler composition responsibility;
6. route-selection behavior for 0.2, including whether it is all upstream
   routes only.

Settings fields, PostgreSQL driver selection, migration invocation, diagnostic
schemas, and scheduler/worker CLI names are explicitly deferred to the release
that first needs them.

### W4 — Prove the integration path

The spike must:

1. construct the required graph exclusively from public ETLantic memory
   providers;
2. seed one definition through the public definition repository contract;
3. mount the upstream router under `/etl` in an otherwise ordinary FastAPI app;
4. install the upstream problem-detail handler explicitly, because the
   embedding helper does not do so;
5. list or fetch the seeded definition through HTTP;
6. submit a run with the upstream idempotency mechanism and assert `202`;
7. repeat the submission and assert the canonical acceptance identity is
   unchanged;
8. generate OpenAPI and retain a normalized evidence snapshot.

The spike may live under `spikes/` or tests, but not under the importable
`shuetl` package. It is allowed to be replaced completely by the 0.2 facade.

### W5 — Enforce the boundary

Automated checks must reject:

- imports from private ETLantic modules or private `etlantic-fastapi` modules;
- direct imports of APScheduler, Tenacity, SQLModel, Alembic, or worker
  libraries from ShuETL core;
- ShuETL classes or modules named as ETLantic domain concepts such as
  `Pipeline`, `Run`, `Attempt`, `Schedule`, `Event`, `Report`, or `Artifact`;
- ShuETL-owned control-plane ORM models or migration revisions;
- copied FastAPI route functions or duplicate operation IDs.

Name-based checks are guardrails, not proof by themselves. Keep a narrow
allowlist for documentation, tests, and future adapters, and require an ADR for
each production-code exception.

### W6 — Assemble release evidence

- Run the test suite against declared dependencies, not the neighboring
  ETLantic repository.
- Build both distribution formats and inspect their contents.
- Install the wheel into a clean environment and run the spike there.
- Record the normalized upstream operation IDs and component-schema references.
- Link each exit-gate item to its test, ADR, matrix row, or command output.
- Classify every discovered upstream gap as blocking, deferred, or upstream
  work; do not silently fill it in ShuETL.

## OpenAPI proof rule

The OpenAPI assertion must establish all of the following:

- expected upstream operation IDs are present beneath the configured prefix;
- every operation ID is unique;
- ETLantic request and response component references are retained;
- no ShuETL component substitutes for an ETLantic domain schema;
- differences from the upstream schema are limited to documented host-level
  metadata and path prefixing.

A checked snapshot is evidence for the exact 0.1 baseline, not a promise that
all future upstream schemas remain byte-for-byte identical.

## Ordered execution

```text
W1 packaging ───────┐
                    ├─> W4 integration spike ─> W6 release evidence
W2 inventory ─> W3 ADRs ─> W5 boundary checks ─┘
```

W1 and W2 may proceed together. W3 must close before code intended to survive
into 0.2 is added. A disposable W4 experiment may inform W3, but it must not
quietly become the public facade.

## Exit gate

Phase 0.1 passes only when:

- [ ] wheel and sdist builds succeed, contain `py.typed`, and pass a clean-wheel
      import test;
- [ ] the spike uses only public APIs from installed ETLantic 0.51
      distributions;
- [ ] a prefixed host app can read a seeded definition and return the upstream
      durable-accept result for an idempotent submission through
      `etlantic-fastapi`;
- [ ] normalized OpenAPI evidence preserves upstream operation IDs and schema
      references without ShuETL shadow models;
- [ ] the public-contract inventory identifies status and owner for every
      upstream dependency planned through 0.2;
- [ ] the ownership matrix has no unexplained overlapping semantic owner;
- [ ] boundary checks fail on representative prohibited imports and shadow
      model fixtures while allowing the approved composition imports;
- [ ] all six 0.1 blocking ADRs are accepted and linked from the evidence index;
- [ ] CI runs formatting, linting, typing, unit/boundary tests, distribution
      builds, and the clean-wheel spike;
- [ ] the evidence index contains no unresolved blocking upstream gap.

## Stop conditions

Stop 0.1 and propose upstream work or a package merge if any of these is true:

- mounting safely requires copying or wrapping upstream route implementations;
- preserving HTTP behavior requires ShuETL-owned ETLantic domain schemas;
- ShuETL's only durable value is a shorter alias for `include_router()`;
- the needed composition hooks cannot be public and supported upstream;
- the ownership matrix requires ShuETL to own ETLantic runtime semantics.

An upstream issue may unblock the phase later. It must be recorded as an
external dependency rather than hidden behind temporary product behavior.

## Definition of “done, not polished”

0.1 may ship with internal names, a disposable spike, and incomplete end-user
documentation. It may not ship with an accidental public facade, unpublished
dependency assumptions, editable-install-only evidence, or an ambiguous product
boundary.
