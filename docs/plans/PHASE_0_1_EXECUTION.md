# Phase 0.1 Execution Plan

## Objective

Produce a reproducible ShuETL 0.1 evidence release that proves a separately
packaged composition layer is useful and technically viable without shipping
the 0.2 facade early.

The phase is complete when a reviewer can clone ShuETL without a neighboring
ETLantic checkout, run one release command, and verify packaging, public API
usage, the memory-provider HTTP flow, OpenAPI preservation, and architectural
boundaries.

## Working decisions to ratify

These defaults keep implementation moving, but each must be accepted in its
named ADR before code intended for 0.2 is merged.

| ADR | Working decision |
|---|---|
| ADR-0001 | Keep ShuETL separate only while it owns material host composition, compatibility, diagnostics, and deployment value; merge upstream if it becomes only an alias for `include_router()` |
| ADR-0002 | Start with Python 3.11–3.13, ETLantic and `etlantic-fastapi` `>=0.51,<0.52`, FastAPI `>=0.115,<1`, and Pydantic `>=2.12,<3`; use exact 0.51.0 inputs for the evidence snapshot |
| ADR-0003 | Declare a direct runtime dependency only when importable ShuETL code imports it; keep SQLModel, Alembic, schedulers, workers, and retry engines out of core |
| ADR-0004 | The 0.2 facade accepts a prebuilt `ETLanticAPI`; reference provider construction and settings begin in 0.3 |
| ADR-0005 | Existing-app integration explicitly composes the upstream problem handler and host lifespan, detects conflicts, and never replaces host behavior silently |
| ADR-0006 | The 0.2 facade exposes the complete upstream router under one validated prefix; it adds no route aliases or independent route presets |

If review rejects a working decision, update this plan before implementing any
dependent task.

## Planned repository shape

```text
.
├── .github/workflows/ci.yml
├── CHANGELOG.md
├── LICENSE
├── pyproject.toml
├── src/shuetl/
│   ├── __init__.py
│   └── py.typed
├── spikes/
│   └── phase_0_1_memory_mount.py
├── scripts/
│   ├── check_boundaries.py
│   ├── check_clean_wheel.py
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

## Task graph

| ID | Task | Depends on | Primary output | Gate |
|---|---|---|---|---|
| E01 | Capture the baseline | — | baseline section in evidence index | A |
| E02 | Inventory upstream contracts | E01 | `contracts.md` | A |
| E03 | Complete ownership matrix | E01 | `ownership.md` | A |
| E04 | Decide six blocking ADRs | E02, E03 | accepted ADR-0001–0006 | A |
| E05 | Scaffold the distribution | E04 | buildable typed package | B |
| E06 | Implement the disposable spike | E02, E05 | passing memory HTTP flow | B |
| E07 | Capture normalized OpenAPI | E06 | reviewed snapshot and assertions | B |
| E08 | Implement boundary enforcement | E03, E05 | checker and fixture tests | B |
| E09 | Add CI and clean-wheel verification | E05–E08 | green supported-version matrix | C |
| E10 | Assemble release evidence | E09 | reproducible evidence index | C |
| E11 | Review the stop conditions | E10 | proceed/merge/upstream decision | C |
| E12 | Cut the local 0.1 artifact | E11 | wheel, sdist, changelog entry | C |

The critical path is E01 → E02/E03 → E04 → E05 → E06 → E07/E08 → E09 →
E10 → E11 → E12.

## Gate A — Boundary and decisions

### E01 — Capture the baseline

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
- [ ] no import resolves from `/Volumes/T7/coding/etlantic` or another sibling
      checkout;
- [ ] evidence inputs are exactly 0.51.0 where an ETLantic package is involved.

### E02 — Inventory upstream contracts

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

### E03 — Complete the ownership matrix

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

### E04 — Decide the blocking ADRs

Create `docs/adr/README.md` with an ADR status table and write:

1. `0001-package-boundary-and-merge-trigger.md`;
2. `0002-initial-compatibility-policy.md`;
3. `0003-dependency-boundaries.md`;
4. `0004-facade-input-policy.md`;
5. `0005-host-lifespan-and-problem-handlers.md`;
6. `0006-route-selection.md`.

Each ADR must contain context, decision, alternatives, consequences, validation
evidence, and a revisit trigger. ADR-0001 must include the explicit package
stop conditions. ADR-0002 must distinguish the exact evidence pins from the
published compatibility range.

Acceptance:

- [ ] all six ADRs have status `Accepted`;
- [ ] each ADR links to relevant contract and ownership rows;
- [ ] no unresolved choice changes the 0.2 public shape or 0.1 dependency set;
- [ ] rejected alternatives are recorded rather than deleted.

Gate A passes when E01–E04 are complete. Do not implement package code meant to
survive into 0.2 before this gate.

## Gate B — Technical proof

### E05 — Scaffold the distribution

Create:

- `pyproject.toml` using `hatchling` and a `src/` layout;
- `src/shuetl/__init__.py` with only package metadata needed for 0.1;
- `src/shuetl/py.typed`;
- `tests/unit/test_package.py` covering import and version metadata;
- `LICENSE` and `CHANGELOG.md`;
- Ruff, mypy, and pytest configuration in `pyproject.toml`.

Dependency rules:

- use the ranges accepted in ADR-0002;
- do not add `pydantic-settings` until ShuETL imports it for 0.3 settings;
- put HTTPX and test tooling in a test dependency group or test extra;
- do not add a PostgreSQL extra in 0.1;
- do not export `ShuETL`, `ShuETLSettings`, provider builders, or lifecycle
  helpers yet.

Acceptance commands:

```bash
uv lock
uv sync --all-groups
uv run python -c "import shuetl"
uv build
```

Acceptance:

- [ ] wheel and sdist build successfully;
- [ ] the wheel contains `shuetl/__init__.py` and `shuetl/py.typed`;
- [ ] core imports succeed without optional packages;
- [ ] the public package surface contains no provisional 0.2 facade.

### E06 — Implement the disposable memory spike

Create `spikes/phase_0_1_memory_mount.py` and
`tests/integration/test_memory_mount.py`. The test may import reusable setup
from the spike, but no spike code may move into `src/shuetl`.

The spike must use public imports to:

1. import ShuETL and record its installed distribution version and origin;
2. construct `MemoryAuthorizer`, `MemoryDefinitionRepository`,
   `MemorySubmissionStore`, and `MemoryEventStore`;
3. create a membership context for principal `alice` in `tenant-a/ws-1`;
4. seed `pipe-1` through the public definition repository API;
5. grant only the actions required to read the definition and submit a run;
6. construct `ETLanticAPI`;
7. create an ordinary host `FastAPI` app with one unrelated host route;
8. explicitly install the upstream exception handler;
9. call upstream `include_router(app, api, prefix="/etl")`;
10. assert the host route still works;
11. fetch or list `pipe-1` through `/etl/v1/...`;
12. submit with `X-Principal` and `Idempotency-Key` headers and assert `202`;
13. repeat the same submission and assert the acceptance identity is unchanged;
14. verify an unauthorized principal cannot read the definition;
15. generate the host OpenAPI document.

The spike must not start a scheduler, worker, lifespan-owned executor, or
FastAPI `BackgroundTasks` job.

Acceptance:

```bash
uv run pytest tests/integration/test_memory_mount.py -q
uv run python spikes/phase_0_1_memory_mount.py
```

- [ ] both commands pass;
- [ ] the test asserts status codes and canonical IDs, not only response shape;
- [ ] every non-stdlib import is listed in `contracts.md` or is test tooling;
- [ ] the memory limitation is stated in the script output and evidence index.

### E07 — Capture normalized OpenAPI evidence

Commit `docs/evidence/0.1/openapi.normalized.json`. Normalize the generated
document to retain only stable evidence:

- OpenAPI major/minor version;
- sorted paths;
- method, operation ID, response status codes, and schema references;
- component schema names and their `$ref` relationships;
- media types, including `text/event-stream` where exposed.

Exclude server URLs, generation timestamps, and unrelated host metadata. Tests
must assert:

- every operation ID is unique;
- required ETLantic operation IDs are present under `/etl`;
- the seeded-definition and submission operations use upstream schemas;
- no component schema name starts with `ShuETL`;
- the only path-level transformation attributable to ShuETL is the `/etl`
  prefix;
- refreshing the snapshot is an explicit command, never an automatic test
  side effect.

Acceptance:

- [ ] the snapshot is deterministic across two consecutive generations;
- [ ] deleting or renaming a required upstream operation makes the test fail;
- [ ] introducing a ShuETL shadow response schema makes the test fail.

### E08 — Implement boundary enforcement

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

## Gate C — Reproducibility and release decision

### E09 — Add CI and clean-wheel verification

Create `.github/workflows/ci.yml` with:

- a quality job for Ruff, mypy, boundary checks, and all pytest tests;
- a Python 3.11, 3.12, and 3.13 test matrix;
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

### E10 — Assemble the release evidence

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

### E11 — Review the stop conditions

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

### E12 — Cut the local 0.1 artifact

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
