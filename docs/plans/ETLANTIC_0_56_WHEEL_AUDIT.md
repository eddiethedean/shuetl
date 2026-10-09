# ETLantic 0.56.0 Wheel Audit for ShuETL 0.6

Historical audit of exact 0.56.0 artifacts. As of 2026-10-08,
[ADR-0015](../adr/0015-backend-and-deployment-ownership.md) supersedes the adoption
disposition and DDL exception below. The [dependency register](ETLANTIC_0_56_DEPENDENCIES.md)
records the 0.56.2 fixes, accepted 0.57.0 train and Gate U/0 evidence.
Original observations and hashes
are retained; they do not select the final 0.6 artifacts.


Audit date: 2026-10-07
Scope: exact PyPI wheels and their fit against ShuETL's Phase 0.6 Gate 0 and
the ETLantic 0.56 dependency findings.
Result: **0.56.0 is a viable upstream qualification baseline, but ShuETL's
Phase 0.6 Gate 0 is not complete.**

Planning disposition after audit: the user selected published ETLantic
`0.56.0` as-is for Phase 0.6. The
[execution contract](PHASE_0_6_EXECUTION.md) supersedes the initial adoption
recommendation below: dependency selection is complete, a fresh store is the
reference transition, and the constructor's version-table statement has a
narrow non-mutating exception. The release-document discrepancy is tracked
without blocking adoption. Audit observations and unperformed checks remain
unchanged; ShuETL integration qualification is still required before release.

## Summary

The published core, FastAPI, SQLModel, SQL, and Foundry 0.56.0 wheel hashes
match the upstream 0.56 wheel manifest. The artifact includes the missing
managed application service, one configured SQLModel backend shared by
headless and HTTP callers, and a default worker backed by the managed ETL
runtime. Upstream's 0.56 release evidence records all 44 acceptance criteria as
passed, including a PostgreSQL managed-provider matrix and clean-wheel smokes.

ShuETL still needs its own process composition. ETLantic's scheduler and worker
CLI commands remain file-backed; the public Python scheduler requires a
submission callback, the standard backend has no scheduler factory, and the
worker has no `ready()` method. These are appropriate ShuETL supervision and
health responsibilities under the current Phase 0.6 contract, but the role
factory, service identity, readiness, drain, and shutdown contract must be
frozen and implemented before preview qualification.

The artifacts' release state also needs an upstream status reconciliation:
PyPI exposes the 0.56.0 files, while the tag's release documents still label
0.56.0 an unpublished candidate and 0.55.x the supported line. The code
qualification evidence is strong; publication and support language is
internally inconsistent.

## Artifact identity

The listed SHA-256 values were computed from the downloaded PyPI wheels and
matched the corresponding entries in the upstream
`docs/11_DEVELOPMENT/evidence/phase_0_56/WHEEL_MANIFEST.json` at tag `v0.56.0`.
PyPI upload timestamps are UTC on 2026-10-07.

| Distribution | Wheel SHA-256 | PyPI upload time |
|---|---|---|
| `etlantic==0.56.0` | `d204aae06921a3da05073403ec6b0c93cc7e464b9844f12b0b65191a6d7e2341` | 04:29:05Z |
| `etlantic-fastapi==0.56.0` | `25134beaed279e4c64814ec50e759de27c979847b8bd73fb8e43dc230f5b2e03` | 04:29:35Z |
| `etlantic-sqlmodel==0.56.0` | `fbaaf32dfaf97e429626af5935be5330cc14a294d811ccf549b733bb1dce7c45` | 04:29:25Z |
| `etlantic-sql==0.56.0` | `d3753769c8ddd7078950bab8406fb1ca21d50fa60782394eeac53d60430135cb` | 04:29:13Z |
| `etlantic-foundry==0.56.0` | `8da32bcf2eb17d5c1e3d98833683398c75afd5cc636fe83eb63cc8063364fca5` | 04:29:16Z |

An isolated CPython 3.11.14 environment installed the core, FastAPI, and
SQLModel wheels as 0.56.0. Their metadata resolves a compatible package set;
the FastAPI managed extra requires the exact SQLModel 0.56.0 train. This audit
did not install the SQL or Foundry wheels; their published hashes were verified
against the upstream wheel manifest.

## Gate 0 findings

| Requirement | Finding | Status |
|---|---|---|
| Public headless service shared with HTTP | `ManagedApplicationService` is wired into `ETLanticAPI`; `create_managed_backend` configures the same service graph used by the HTTP app. Upstream evidence records headless/HTTP parity. | Pass at upstream artifact level |
| Standard PostgreSQL backend construction | `ManagedBackendConfig` and `create_managed_backend` construct registry, submission, event, durable-work, schedule, report, and input-resource stores on one SQLAlchemy engine. | Pass at API/code level |
| Real default worker | `ManagedBackend.create_execution_host()` supplies `ManagedExecutionAdapter`; `ExecutionHost` no longer defaults to a no-op runner. | Pass at API/code level |
| Scheduler role composition | `SchedulerService` is public and supports owner IDs, leader leases, `tick`, `ready`, and `drain`. It requires `run_submitter` for the standard run path; `ManagedBackend` does not provide a scheduler factory. The CLI scheduler still consumes JSON files. | Partial; ShuETL must wire and supervise it |
| Worker role readiness and shutdown | The public execution host has `drain()` and owner/lease behavior, but no `ready()` method. The CLI worker still consumes a JSON durable-store file. | Partial; ShuETL must supply process readiness and shutdown coordination |
| PostgreSQL schema | SQLModel migration list ends at `014_cp1_complete_principal_idempotency_0_56`. The migration API successfully upgraded a disposable local PostgreSQL 14.18 database to that head. | Pass for local migration smoke; target server version not qualified here |
| Same-store construction without migration privileges | `create_managed_backend` succeeded with the session switched to a role granted `CONNECT`, schema `USAGE`, and table `SELECT`, but no schema `CREATE`. | Pass for constructor smoke on an existing head |
| No-DDL readiness rule | Upstream `migrations.current_version()` contains `CREATE TABLE IF NOT EXISTS` before its version query. With the schema table present, the no-`CREATE` role smoke succeeded and PostgreSQL reported the existing table unchanged. This is effectively non-mutating on the qualified path, but it is still a DDL statement and is a strict-contract concern. | Partial; prefer a genuinely read-only version inspector |
| Version-0.55 data compatibility | The 0.56 upgrade notes require a fresh 0.56 store for runtime compatibility, do not read 0.55 durable state, and provide no offline converter. Keep the 0.55 application/store for rollback. | Blocker for in-place upgrade; requires an explicit fresh-store/cutover plan |
| Installed-wheel role acceptance on target PostgreSQL | This audit constructed the backend and roles but did not run manual and scheduled ETL through separate OS processes on PostgreSQL 18.6 or another ShuETL-qualified version. Local PostgreSQL was 14.18. | Open ShuETL Gate 0 evidence |

## Upstream qualification evidence

At tag `v0.56.0`, the upstream release index records 44/44 acceptance
criteria passed and release decision `GO`. The upstream local qualification
record reports managed headless/HTTP parity, real managed worker execution,
PostgreSQL persistence and multiprocess acceptance, and a 12-pairing Foundry /
PostgreSQL / immutable-CSV matrix. Its PostgreSQL runs used isolated 16.13 and
16.14 servers; this is upstream evidence and is not a ShuETL process-role run.

The exact 0.56 core, FastAPI, SQLModel, SQL, and Foundry hashes listed above
match that upstream wheel manifest. This ties the qualified candidate wheel
bytes to the published PyPI wheel bytes even though the release-status wording
was not updated consistently.

## Release-status discrepancy

PyPI marks `etlantic==0.56.0` released on 2026-10-07. The same tag's
`CHANGELOG.md` still labels 0.56.0 “Unreleased candidate (not published)”; the
0.56 capabilities and upgrade pages say 0.55.x remains the published supported
line; and `EXIT_GATE_0_56.md` says its GO decision approves proceeding with the
tagged release workflow but does not claim publication. PyPI's file metadata
also says the wheels were not uploaded through Trusted Publishing.

The initial audit recommended reconciling this release record and confirming
the upload workflow/provenance. The current Phase 0.6 disposition tracks the
documentation discrepancy without requiring an upstream change before
adoption: the published bytes match the qualified manifest. ShuETL's own
installed-artifact qualification still gates its supported preview claim.

## Initial audit recommendation and remaining evidence

The following recommendation preceded the planning disposition above. Consult
the execution contract for the selected baseline and current gate wording.

Use the 0.56.0 wheels as the candidate integration train; do not treat package
availability alone as completion of ShuETL Gate 0. Keep ShuETL's dependency
pins unchanged pending:

1. A role-composition ADR covering trusted scheduler/worker context, scheduler
   callback wiring, worker readiness, process loops, signal handling, drain,
   and one-time resource cleanup.
2. A documented fresh-store transition from 0.55.0, or a separately qualified
   compatibility/migration path. Do not promise resumption of 0.55 durable work
   on 0.56 without evidence.
3. An installed-wheel smoke that runs one manual and one scheduled real ETL
   through PostgreSQL-backed gateway/scheduler/worker processes, plus the
   specified crash/restart and duplicate-role cases.
4. PostgreSQL version selection and qualification. Upstream 0.56 evidence
   covers PostgreSQL 16.13/16.14; the current ShuETL pilot pins 18.6. The local
   audit's PostgreSQL 14.18 run is smoke evidence only.
5. Resolve the strict read-only version-inspection concern before using
   `create_managed_backend` in a role that promises no DDL statements at
   startup/readiness.

## Audit commands and limits

- Installed `etlantic`, `etlantic-fastapi`, and `etlantic-sqlmodel` 0.56.0 into
  an isolated CPython 3.11 environment; checked installed metadata and public
  class signatures.
- Downloaded five PyPI wheel files and verified their SHA-256 values against
  PyPI JSON and the upstream wheel manifest.
- Migrated a disposable local PostgreSQL 14.18 database to migration 014,
  constructed a managed backend, scheduler, and worker from the installed
  wheels, verified the worker adapter type and resource close, and repeated
  construction under a no-`CREATE` database role.
- Inspected the upstream tag's 0.56 exit gate, qualification record, wheel
  manifest, release index, package CLI help, and managed service/provider
  source.
- Did not rerun the upstream 44-criterion suite or the live PostgreSQL 16/18
  matrix. No ETL transfer or multi-process role acceptance was run locally.
