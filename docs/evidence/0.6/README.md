# Phase 0.6 development qualification

Recorded: 2026-10-09. **Not a release approval.** Development metadata targets
ShuETL 0.6.0. Published ShuETL 0.5.0/ETLantic 0.55.0 remains the rollback baseline.

| Gate | Result |
| --- | --- |
| Gate U — upstream coverage acceptance | PASS |
| Gate 0 — installed-artifact PostgreSQL role feasibility | PASS |
| Gate A — final-wheel Python/hosted acceptance | OPEN |
| Gate B — lifecycle/failure/capability/transition acceptance | OPEN |
| Gate C — final dependency/boundary/release review | OPEN |

U01–U05 are accepted in [coverage-acceptance.md](coverage-acceptance.md), using
published-wheel provenance, upstream 160-case conformance, 12 direct consumer
assertions and 10 locally executed provider/PostgreSQL cases. The same 12
consumer assertions also pass on Python 3.11 and 3.12; these are repeated
interpreter checks, not additional distinct coverage.

| Reproducibility field | Value |
| --- | --- |
| OS and architecture | macOS, ARM64; exact platform in validation.json |
| Python version | 3.11.14, 3.12.13, 3.13.9 |
| uv version | Exact executable version in validation.json |
| ETLantic source revision | Release tag d1f4e5a4d013e37f8adc54b4644ea9b2be66f801 |
| ShuETL source commit | `40402b6c4f2788605ecfebfe5e25144ddd04a57c` |
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
`etlantic==0.57.0`, `etlantic-fastapi==0.57.0` and optional
`etlantic-sqlmodel==0.57.0`. Development ShuETL is 0.6.0. FastAPI 0.141.1,
Pydantic 2.13.5, settings 2.15.0, SQLAlchemy 2.0.52, psycopg/binary 3.3.5
and HTTPX2 2.12.0 are unchanged. Mixed ETLantic patch versions fail compatibility.
The gateway's new optional `server` extra pins Uvicorn 0.46.0; runtime roles do
not import the ASGI server. The clean-wheel check verifies this separate extra.
The separately packaged qualification host enables `etlantic-sql==0.57.0`;
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
come from [CI run 37984396221](https://github.com/eddiethedean/shuetl/actions/runs/37984396221)
and are bound to source commit `40402b6c4f2788605ecfebfe5e25144ddd04a57c`.
The ShuETL wheel SHA-256 is
`d1944eb7def4c707787b2b958dafb71db0bb7d4020bf83103b763be443ef98a1`;
Gate 0 reference workload SHA-256 is
`5eeb1756e0dce0b1f022adad94953a4680e01806f35b15df2679266be16062e2`; CLI
reference host SHA-256 is
`1c3773dd72daa9c34080d7249aba9bf759866167ad5062737399acb176f64769`.
These development artifacts close only the installed baseline qualification;
the final release candidate and broader acceptance gates remain open.
The [provider matrix](providers.md), [partial qualification record](qualification.md),
and [hosted CI record](ci.md) identify the demonstrated combinations and current
limitations.

```sh
python spikes/phase_0_6_gate_0.py \
  --disposable-admin-url "$DISPOSABLE_POSTGRES_ADMIN_URL" \
  --python "$INSTALLED_WHEEL_PYTHON" \
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
0.57.0; the reference profile trusts that exact descriptor and `etlantic-sql`
0.57.0. No wildcard or unpinned plugin trust is used.

## Installed CLI startup and signal smoke test

The separately installed 0.6.0 wheel and reference host pass a four-role CLI
smoke test against disposable PostgreSQL 18.6:
[local Python 3.13](cli-postgresql.json), [Python 3.11](cli-postgresql-3.11.json),
and [Python 3.12](cli-postgresql-3.12.json). Gateway, scheduler, run worker and
action worker each reach `/ready` and `/live`, receive SIGTERM, exit successfully,
and leave no seeded credential sentinels in captured logs. The runtime role has
no schema CREATE rights, migration-role membership or owned objects. The same
qualification passes in hosted CI on Python 3.11–3.13 for source commit
`40402b6c4f2788605ecfebfe5e25144ddd04a57c`; the redacted per-interpreter records
are in [hosted-cli/](hosted-cli/), and [CI run 37984396221](https://github.com/eddiethedean/shuetl/actions/runs/37984396221)
binds those results to ShuETL wheel SHA-256
`d1944eb7def4c707787b2b958dafb71db0bb7d4020bf83103b763be443ef98a1` and
reference-host wheel SHA-256
`1c3773dd72daa9c34080d7249aba9bf759866167ad5062737399acb176f64769`.
This qualifies basic installed startup and signal shutdown only; it does not
qualify active-work drain, outage/recovery, grace expiry, or failure injection.

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
records seven passing PostgreSQL integration tests on a separate disposable
database, including scheduler shutdown during an in-flight leader-lease
acquisition and readiness recovery after a TCP-level database connectivity
outage. Both lifecycle cases pass the hosted Python 3.11–3.13 matrix in
[CI run 37984396221](https://github.com/eddiethedean/shuetl/actions/runs/37984396221).
PostgreSQL URL configuration was scoped to that file to avoid contaminating
unit tests that inspect environment precedence.

Local Ruff, Pyright, artifact metadata and clean-wheel core/SQLite/PostgreSQL
import/example checks are recorded in [validation.json](validation.json).
[Artifact manifest](artifacts.json) binds the installed wheels and development
build. The expanded source/runtime checks are recorded in
[source-runtime-validation.md](source-runtime-validation.md). Local interpreter
checks do not establish hosted CI or release acceptance.

## Acceptance results

All 33 release criteria remain OPEN. Gate 0 feasibility, hosted basic CLI smoke
tests, and the newly added local PostgreSQL drain/outage tests do not qualify
all-role failure recovery, the advertised connector matrix or transition/rollback.
W02 API freeze and W03/W04 source implementation are recorded in ADR-0014 and the
implementation plan; hosted W04 fault qualification and W05–W08 remain required.

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

Role-specific ShuETL binding/API freeze; hosted active-work drain and provider
outage/recovery, exact cleanup, grace and process-failure qualification; complete
live capability matrix; fresh-store transition/rollback rehearsal; hosted
final-wheel checks and audited 33-row proofs. No upstream implementation change
was required by the completed qualification.

## Reproducible development build

Built with `SOURCE_DATE_EPOCH=1580601600 uv build`; the index is excluded from
the sdist to avoid self-referential hashes. This binds current development source
without approving release.

| Artifact | Value |
| --- | --- |
| SHA-256 wheel | `d1944eb7def4c707787b2b958dafb71db0bb7d4020bf83103b763be443ef98a1` |
| SHA-256 sdist | `da674f8d06553d2f489fa96f3ad42da4700e336a01a8a6d1f337d697bd517c5c` |

The fresh-build artifact-hash regression passed after the evidence build.
`check_evidence.py` intentionally rejects all 33 OPEN criteria and Gates A–C;
it cannot approve this development record for release.
