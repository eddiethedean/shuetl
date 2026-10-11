# Phase 0.6 development qualification

**Current status (2026-10-11):** ShuETL pins ETLantic 0.57.2. Some earlier
hosted records remain bound to 0.57.0. Current local qualification on the published
0.57.2 artifacts passes Gate 0 on Python 3.11–3.13, native CLI active drain and
force on Python 3.12, Linux container active drain, and the transition rehearsal.
The 22-case crash matrix passes 20 cases and fails two action-worker-death
reconciliation cases tracked in [ETLantic #299](https://github.com/eddiethedean/etlantic/issues/299).
Managed live preflight remains an upstream gap in
[ETLantic #121](https://github.com/eddiethedean/etlantic/issues/121). See the
[current qualification record](current-qualification.md) for candidate hashes,
limits, and the distinction between local and hosted results. Phase 0.6 is not
release qualified.

The [0.57.2 consumer audit](../../reviews/ETLANTIC_0_57_2_REQUIREMENTS_AUDIT.md)
records published-wheel provenance and verification of the sort and
action-handler fixes. The [current qualification record](current-qualification.md)
supersedes the older local 0.57.0 development snapshots for its stated checks.
Live preflight, crash reconciliation, remaining acceptance cases, and hosted
final artifacts remain open.

Recorded: 2026-10-09. **Not a release approval.** Development metadata targets
ShuETL 0.6.0. Published ShuETL 0.5.0/ETLantic 0.55.0 remains the rollback baseline.

| Gate | Result |
| --- | --- |
| Gate U — 0.57.2 published upstream contracts | PASS |
| Gate 0 — installed-artifact PostgreSQL role feasibility | PASS |
| Gate A — final-wheel Python/hosted acceptance | OPEN |
| Gate B — lifecycle/failure/capability/transition acceptance | BLOCKED by #299 and #121 |
| Gate C — final dependency/boundary/release review | OPEN |

Gate U is independently verified against the published 0.57.2 wheels. Gate 0's
current local installed-wheel workload, controls and resource-retention cases
pass on Python 3.11–3.13; earlier hosted records are linked below and remain
bound to their recorded commit and hashes. These gate-level feasibility results
do not close the reviewed 33-criterion release ledger.

U01–U05 are accepted in [coverage-acceptance.md](coverage-acceptance.md), using
published-wheel provenance, upstream 160-case conformance, 12 direct consumer
assertions and 10 locally executed provider/PostgreSQL cases. The same 12
consumer assertions also pass on Python 3.11 and 3.12; these are repeated
interpreter checks, not additional distinct coverage.

| Reproducibility field | Value |
| --- | --- |
| OS and architecture | macOS, ARM64; exact platform in validation.json |
| Historical hosted Python versions | 3.11.14, 3.12.13, 3.13.9; current local Gate 0 uses 3.11.15, 3.12.13, 3.13.16 (see current qualification) |
| uv version | Exact executable version in validation.json |
| ETLantic source revision | Release tag d1f4e5a4d013e37f8adc54b4644ea9b2be66f801 |
| ShuETL source commit | `c064aa9ead7b78d9f6451895d6799e088ab8682f` |
| ShuETL import origin | Isolated wheel site-packages/shuetl/__init__.py |
| ETLantic import origin | Isolated wheel site-packages/etlantic/__init__.py |
| etlantic-fastapi import origin | Isolated wheel site-packages/etlantic_fastapi/__init__.py |
| FastAPI import origin | Isolated wheel site-packages/fastapi/__init__.py |
| Pydantic import origin | Isolated wheel site-packages/pydantic/__init__.py |
| HTTPX import origin | Isolated test extra httpx2; clean-wheel logs bind installation |

[Clean-wheel logs](clean-wheel-3.13.log) preserve observed imports with temporary
host-directory names redacted. Public release provenance is in the candidate audit.

## Adopted dependencies and compatibility

`pyproject.toml`, `uv.lock` and runtime compatibility checks agree on exact
`etlantic==0.57.2`, `etlantic-fastapi==0.57.2` and optional
`etlantic-sqlmodel==0.57.2`. Development ShuETL is 0.6.0. FastAPI 0.141.1,
Pydantic 2.13.5, settings 2.15.0, SQLAlchemy 2.0.52, psycopg/binary 3.3.5
and HTTPX2 2.12.0 are unchanged. Mixed ETLantic patch versions fail compatibility.
The gateway's new optional `server` extra pins Uvicorn 0.46.0; runtime roles do
not import the ASGI server. The clean-wheel check verifies this separate extra.
The separately packaged qualification host enables `etlantic-sql==0.57.2`;
this connector is not an implicit core ShuETL dependency.

Provider schema contract: `014_cp1_complete_principal_idempotency_0_56`.
PostgreSQL, SQLite bundles and doctor now consume public provider inspection;
legacy inventory exports delegate to provider requirements. Host server/TLS policy
and doctor/1 fields are preserved. Only explicit operator migrations change schema.
No direct 0.55-store migration or rolling upgrade is qualified.

Current OpenAPI and authorization baselines are [openapi.normalized.json](openapi.normalized.json)
and [route_inventory.json](route_inventory.json); historical 0.1–0.5 evidence is
unchanged. Upstream now rejects caller execution snapshots and stale schedule
revisions; adapted fixtures use canonical inputs and explicitly assert rejection.

## Installed-artifact PostgreSQL Gate 0

Harness: [phase_0_6_gate_0.py](../../../spikes/phase_0_6_gate_0.py).
Reference workload: [separately built package](../../../tests/reference_phase06/pyproject.toml).
The harness is not a supported role CLI or a replacement runtime. Its workload
performs typed CSV and PostgreSQL-source normalization, filtering, quality
acceptance/rejection, and writes to independent PostgreSQL sinks. It verifies
append behavior and a primary-key upsert across two distinct runs, along with
exact sink rows, input read-only grants and effect receipts. Local and hosted
PostgreSQL 18.6 installed-wheel runs pass on Python 3.11–3.13. The committed
[hosted Gate 0 records](hosted-gate0/) and [installed CLI records](hosted-cli/)
come from [CI run 37989243217](https://github.com/eddiethedean/shuetl/actions/runs/37989243217)
and are bound to source commit `c064aa9ead7b78d9f6451895d6799e088ab8682f`.
The ShuETL wheel SHA-256 is
`3921b62c7d8c27b6a7d5be69e3a4e36ae1a3030ba9020a1db8dcbfbb73060d24`;
Gate 0 reference workload SHA-256 is
`5668ffa6f89724feba2b5b36d0fcfede08661676a602202818e7d8319226a714`; CLI
reference host SHA-256 is
`1bc27163c3c30487a386fd019210594f807253fc50a443ef289754cbf9c5621a`.
These development artifacts close installed baseline, multi-process
coordination and CLI cleanup qualification; the final release candidate and
broader acceptance gates remain open.
The independent reference host also executes an ETLantic portable plan and
records selection, projection, rename, quality and output-schema observations.
The historical 0.57.0 order-reversal case exposed a canonical sort/deduplication
defect. The installed 0.57.2 consumer audit passes the same reversed-order
requirement; see [ETLantic #283](https://github.com/eddiethedean/etlantic/issues/283)
and the [0.57.2 audit](../../reviews/ETLANTIC_0_57_2_REQUIREMENTS_AUDIT.md).
The [provider matrix](providers.md), [partial qualification record](qualification.md),
and [hosted CI record](ci.md) identify the demonstrated combinations and current
limitations.

```sh
python spikes/phase_0_6_gate_0.py \
  --disposable-admin-url "$DISPOSABLE_POSTGRES_ADMIN_URL" \
  --python "$INSTALLED_WHEEL_PYTHON" \
  --controls --resources --retention \
  --output docs/evidence/0.6/postgresql-gate0.json
```

The administrator URL must point to disposable PostgreSQL 18.6 infrastructure.
The harness creates its own database and two non-superuser roles, delegates
migrations to the operator connection, preprovisions independent source/sink
fixtures, and grants the runtime role read-only access to the PostgreSQL source
table and required sink DML/sequence access without schema CREATE, owned objects or
membership in the migration role. Cleanup stops children and drops only those
fixtures. No pre-existing application store is accepted or reset.

| Interpreter | Consumer acceptance | Gate 0 feasibility | Installed CLI startup |
| --- | --- | --- | --- |
| 3.11.14 | [12 PASS](gate-u-python-3.11.xml) | [PASS](hosted-gate0/python-3.11.json) | [PASS](hosted-cli/python-3.11.json) |
| 3.12.13 | [12 PASS](gate-u-python-3.12.xml) | [PASS](hosted-gate0/python-3.12.json) | [PASS](hosted-cli/python-3.12.json) |
| 3.13.9 | [12 PASS](gate-u.xml) | [PASS](hosted-gate0/python-3.13.json) | [PASS](hosted-cli/python-3.13.json) |

Each launch uses `python -I -m phase06_reference` outside the repository, with
installed ShuETL, provider and reference-host wheels. JSON records process IDs,
installed origins/versions, startup SQL operation traces, grants, readiness facts,
canonical preparation/run reports, firings and independently queried sink effects.
Gateway startup leaves execution-host modules unloaded; all three runtime
processes leave FastAPI unloaded. Construction commits/writes/DDL are asserted
absent. Borrowed engines remain usable after backend close.

A manual HTTP preparation is performed by the action worker and executed by the
run worker. The complete native scheduler independently admits another occurrence;
its run also succeeds. PostgreSQL independently contains the expected rows and
separate effect receipts. A further Python/HTTP duplicate trigger yields one
additional canonical occurrence/effect. Schedule create/amend/pause/resume/preview/
get/list/trigger/firing parity, stale revision conflicts and scope denial pass.
An injected public clock fixes nominal time; ETL, admission and scheduler logic
remain the published implementations. Worker-only `ETLANTIC_SQL_URL` supplies
connector access; the gateway/scheduler have no connector connection environment.

Production plugin trust is enabled. The core's published local compiler descriptor
uses `etlantic-local` version **0.50.0**, distinct from its containing core wheel
0.57.2; the reference profile trusts that exact descriptor and `etlantic-sql`
0.57.2. No wildcard or unpinned plugin trust is used.

## Installed CLI startup and signal smoke test

The separately installed 0.6.0 wheel and reference host pass a four-role CLI
smoke test against disposable PostgreSQL 18.6:
[hosted Python 3.13](cli-postgresql.json), [Python 3.11](hosted-cli/python-3.11.json),
and [Python 3.12](hosted-cli/python-3.12.json). Gateway, scheduler, run worker and
action worker each reach `/ready` and `/live`, receive SIGTERM, exit successfully,
and leave no seeded credential sentinels in captured logs. The runtime role has
no schema CREATE rights, migration-role membership or owned objects. Redacted
per-interpreter records are in [hosted-cli/](hosted-cli/), and
[CI run 37989243217](https://github.com/eddiethedean/shuetl/actions/runs/37989243217)
binds the results to source commit `c064aa9ead7b78d9f6451895d6799e088ab8682f`
and ShuETL wheel SHA-256
`3921b62c7d8c27b6a7d5be69e3a4e36ae1a3030ba9020a1db8dcbfbb73060d24` and
reference-host wheel SHA-256
`1bc27163c3c30487a386fd019210594f807253fc50a443ef289754cbf9c5621a`.
These hosted installed CLI records qualify basic startup, signal shutdown, and
exact cleanup ordering on the earlier recorded source. Separate source-level
PostgreSQL tests qualify role outage/recovery. The newer local installed-wheel
active-work drain/force results are in [current qualification](current-qualification.md);
hosted active-work/force qualification remains open.

The startup test exposed a lifecycle cycle: ETLantic roles report unknown
prerequisites until their first tick, while ShuETL previously dispatched only
after full readiness. The initial implementation permitted one tick after a
fresh provider check. Review then found that transient failures could permanently
prevent later ticks. The corrected supervisor permits provider-checked bootstrap
and recovery ticks; upstream owns prerequisite checks and admission. Failure-path
regressions cover this correction separately from the recorded installed-process
smoke test. The hashes below bind the reproducible development build; they are
not final release-candidate hashes and must be regenerated if source changes.

## Regression and build validation

[Regression XML](regression.xml) covers the existing facade/settings/identity,
HTTP/SSE, memory/SQLite, authorization, provider and boundary contracts plus
consumer acceptance. [PostgreSQL regression XML](postgresql-regression.xml)
records nine passing PostgreSQL integration tests on a separate disposable
database, including scheduler shutdown during an in-flight leader-lease
acquisition and readiness recovery after TCP-level database connectivity
outages for scheduler, run-worker and action-worker roles. All nine pass the
hosted Python 3.11–3.13 matrix in
[CI run 37989243217](https://github.com/eddiethedean/shuetl/actions/runs/37989243217).
PostgreSQL URL configuration was scoped to that file to avoid contaminating
unit tests that inspect environment precedence.

Local Ruff, Pyright, artifact metadata and clean-wheel core/SQLite/PostgreSQL
import/example checks are recorded in [validation.json](validation.json).
[Artifact manifest](artifacts.json) binds the installed wheels and development
build. The expanded source/runtime checks are recorded in
[source-runtime-validation.md](source-runtime-validation.md). Local interpreter
checks do not establish hosted CI or release acceptance.

## Acceptance results

All 33 release criteria remain OPEN because final reviewed proof bindings and
hosted candidate artifacts are not complete. Current local development
qualification now covers installed-process active-work drain, forced
termination, selected controls and resource retention, and a bounded transition
rehearsal; see [current qualification](current-qualification.md). Remaining
limits include the two accepted-preparation crash failures in #299, live
preflight in #121, the broader supported-capability matrix, production
transition/rollback evidence, and hosted final-artifact review.

| Criterion | Task | Command | Artifact | Status | Limitation | Reviewer | Date |
| --- | --- | --- | --- | --- | --- | --- | --- |
| AC-001 | Final release qualification | pending | pending | OPEN | W02–W08 required | pending | pending |
| AC-002 | Final release qualification | pending | pending | OPEN | W02–W08 required | pending | pending |
| AC-003 | Final release qualification | pending | pending | OPEN | W02–W08 required | pending | pending |
| AC-004 | Final release qualification | pending | pending | OPEN | W02–W08 required | pending | pending |
| AC-005 | Final release qualification | pending | pending | OPEN | W02–W08 required | pending | pending |
| AC-006 | Final release qualification | pending | pending | OPEN | W02–W08 required | pending | pending |
| AC-007 | Final release qualification | pending | pending | OPEN | W02–W08 required | pending | pending |
| AC-008 | Final release qualification | pending | pending | OPEN | W02–W08 required | pending | pending |
| AC-009 | Final release qualification | pending | pending | OPEN | W02–W08 required | pending | pending |
| AC-010 | Final release qualification | pending | pending | OPEN | W02–W08 required | pending | pending |
| AC-011 | Final release qualification | pending | pending | OPEN | W02–W08 required | pending | pending |
| AC-012 | Final release qualification | pending | pending | OPEN | W02–W08 required | pending | pending |
| AC-013 | Final release qualification | pending | pending | OPEN | W02–W08 required | pending | pending |
| AC-014 | Final release qualification | pending | pending | OPEN | W02–W08 required | pending | pending |
| AC-015 | Final release qualification | pending | pending | OPEN | W02–W08 required | pending | pending |
| AC-016 | Final release qualification | pending | pending | OPEN | W02–W08 required | pending | pending |
| AC-017 | Final release qualification | pending | pending | OPEN | W02–W08 required | pending | pending |
| AC-018 | Final release qualification | pending | pending | OPEN | W02–W08 required | pending | pending |
| AC-019 | Final release qualification | pending | pending | OPEN | W02–W08 required | pending | pending |
| AC-020 | Final release qualification | pending | pending | OPEN | W02–W08 required | pending | pending |
| AC-021 | Final release qualification | pending | pending | OPEN | W02–W08 required | pending | pending |
| AC-022 | Final release qualification | pending | pending | OPEN | W02–W08 required | pending | pending |
| AC-023 | Final release qualification | pending | pending | OPEN | W02–W08 required | pending | pending |
| AC-024 | Final release qualification | pending | pending | OPEN | W02–W08 required | pending | pending |
| AC-025 | Final release qualification | pending | pending | OPEN | W02–W08 required | pending | pending |
| AC-026 | Final release qualification | pending | pending | OPEN | W02–W08 required | pending | pending |
| AC-027 | Final release qualification | pending | pending | OPEN | W02–W08 required | pending | pending |
| AC-028 | Final release qualification | pending | pending | OPEN | W02–W08 required | pending | pending |
| AC-029 | Final release qualification | pending | pending | OPEN | W02–W08 required | pending | pending |
| AC-030 | Final release qualification | pending | pending | OPEN | W02–W08 required | pending | pending |
| AC-031 | Final release qualification | pending | pending | OPEN | W02–W08 required | pending | pending |
| AC-032 | Final release qualification | pending | pending | OPEN | W02–W08 required | pending | pending |
| AC-033 | Final release qualification | pending | pending | OPEN | W02–W08 required | pending | pending |

## Gap register

Remaining release gaps: close the upstream blockers #299 and #121; qualify the
complete advertised capability/resource matrix and production transition;
complete hosted final-wheel checks and the reviewed 33-row proof registry.
Deterministic portable deduplication passes on the selected 0.57.2 artifacts.

## Historical hosted development build

Built with `SOURCE_DATE_EPOCH=1580601600 uv build`; the index is excluded from
the sdist to avoid self-referential hashes. This binds current development source
without approving release.

| Artifact | Value |
| --- | --- |
| SHA-256 wheel | `3921b62c7d8c27b6a7d5be69e3a4e36ae1a3030ba9020a1db8dcbfbb73060d24` |
| SHA-256 sdist | `23042e70c4f34ffe35c94e61bc4626522e57b1ba98e47c6dfced6dfaa21c0a3a` |

These hashes belong to the hosted source commit recorded above, not the current
local candidate. The current local candidate wheel and its exact gate records
are listed in [current qualification](current-qualification.md). The fresh-build
artifact-hash regression passed after this historical evidence build.
`check_evidence.py` intentionally rejects all 33 OPEN criteria and Gates A–C;
it cannot approve this development record for release.
