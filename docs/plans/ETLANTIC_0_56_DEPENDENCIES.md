# ETLantic 0.56 Backend Dependencies

## Audited upstream baseline

The 2026-09-29 review examined ETLantic main commit
[`fb0dd748860cdbafceea473f315ed8934a329b27`](https://github.com/eddiethedean/etlantic/commit/fb0dd748860cdbafceea473f315ed8934a329b27),
the merged 0.55 release candidate. The newest tag at review time was 0.54.0.
That review is historical source evidence. On 2026-10-07 ETLantic 0.56.0 and
the lockstep FastAPI, SQLModel, SQL, and Foundry wheels appeared on PyPI. The
wheel hashes for all five packages match the upstream 0.56 qualification
manifest. Upstream's 0.56 release index records all 44 acceptance criteria as
passed, including managed execution and provider matrices.

The [ShuETL wheel audit](ETLANTIC_0_56_WHEEL_AUDIT.md) checked the exact
published artifacts and the Gate 0 contract. It found that the 0.56 tag still
labels the release an unpublished candidate, and the PyPI page says the upload
was not Trusted Publishing. Phase 0.6 now selects the exact published `0.56.0`
train as its implementation baseline. The release wording remains an audit
finding, not a dependency-adoption gate. ShuETL still must qualify its role
composition and PostgreSQL 18.6 process behavior. The execution plan selects
a fresh 0.56 store and records the constructor's non-mutating version-table
statement as a narrow startup exception. ShuETL 0.5.0 currently pins ETLantic
0.55.0; updating package pins and the lock is 0.6 implementation work.

ETLantic's canonical definitions, RunRequest controls, portable transforms,
quality, connector SDK and CP1–CP4 provide substantial foundations. The
historical 0.55 candidate review found the integration and provider gaps
listed below; upstream's 0.56 release evidence records their closure. ShuETL
qualifies the published services in its own composition. The scheduler's
public submission callback is wiring to those services and must not contain
copied admission, scheduling or ETL semantics.

The published upstream baseline is **0.56 — Complete Application ETL Backend**:

- [Source findings and evidence](https://github.com/eddiethedean/etlantic/blob/v0.56.0/docs/11_DEVELOPMENT/FINDINGS_0_56.md)
- [Implementation contract and 44 acceptance criteria](https://github.com/eddiethedean/etlantic/blob/v0.56.0/docs/11_DEVELOPMENT/IMPLEMENTATION_PLAN_0_56.md)
- [Execution sequence and release gates](https://github.com/eddiethedean/etlantic/blob/v0.56.0/docs/11_DEVELOPMENT/EXECUTION_PLAN_0_56.md)

Existing ETLantic brownfield, console, broader provider and modeling phases move
to 0.57–0.60. This renumbering does not change ShuETL's independent version train.

## Historical findings and 0.56 qualification map

These rows retain the original requirements for traceability. They are not
open prerequisites for selecting a future upstream version; downstream
capability claims still require the corresponding ShuETL evidence.

| Upstream finding | Required completion | ShuETL capabilities |
|---|---|---|
| F056-01 | Authorized public services shared by headless and HTTP adapters; standard construction and lifecycle | HC-01/02/19 |
| F056-02 | Complete specification/option discovery, typed effective run settings and lossless public control exposure | HC-03/14/16/17/20/23 |
| F056-03 | One resumable preparation/admission/acceptance command with backend fingerprints and durable idempotency | HC-03/04/18/22 |
| F056-04 | Real managed runtime, heartbeat/cancel, fencing, crash recovery and effect-aware completion | HC-09/19 |
| F056-05 | Actual durable status, events, reports, artifacts and lineage | HC-10 |
| F056-06 | Isolated connection/catalog/schema/preflight/preview/provision operations | HC-05/13/15 |
| F056-07 | Trusted owner/workload context in secret/resource access; explicit version/rotation/revocation rules | HC-02/06 |
| F056-08 | Immutable upload references, checksums, leases, retention and cleanup | HC-08 |
| F056-09 | Scheduled/manual/external triggers share preparation and admission, with revision/occurrence identity | HC-11/18/22 |
| F056-10 | Executable retry/replay/resume/repair/backfill and allowed-action/amendment semantics | HC-20/21/22 |
| F056-11 | Independent Foundry package, live PostgreSQL and CSV qualification, all advertised pairings/modes | HC-07/12/14/19/23 |
| F056-12 | Honor explicit opaque run-denial policy, including existing upstream issue #150 | HC-02 |

The historical 0.55 candidate review found a no-op default runner, report
stubs and an in-memory authoring service. The 0.56 wheel audit confirms the
managed application service, SQLModel backend and real managed execution
adapter now available for ShuETL composition. Those earlier gaps must not be
described as current 0.56 limitations.

MSS and MCS-COP are Foundry configurations, not Microsoft SQL Server. The
upstream floor covers two Foundry sources plus PostgreSQL and CSV, targeting two
Foundry destinations plus PostgreSQL: 12 pairings, expanded by supported write
modes. Packages stay generic and independently installable without Data Mover.

## Effect on ShuETL delivery

- [ShuETL Phase 0.6 Gate 0](PHASE_0_6_EXECUTION.md) qualifies composition on
  the selected published `0.56.0` artifacts. See the
  [wheel audit](ETLANTIC_0_56_WHEEL_AUDIT.md) for hashes, installed backend
  smoke and remaining role/provider evidence.
- Adopt exact `0.56.0` core/FastAPI/SQLModel pins during implementation;
  enabled SQL/Foundry packages use the same train. Qualify the managed backend,
  scheduler callback, worker lifecycle and fresh-store setup as published.
- Implementation proceeds against this baseline. Missing ShuETL acceptance
  evidence blocks its release claim, not dependency selection. Optional
  features stay unavailable until qualified; an advertised feature must meet
  its gate. Actual semantic defects found during qualification remain upstream
  defects and cannot be hidden by ShuETL replacements.
- ShuETL 0.6 still qualifies live process/provider composition and 0.7 still
  proves the downstream operating/cutover envelope. Upstream 0.56 evidence does
  not automatically establish either claim.
- The full [developer-control contract](DEVELOPER_CONTROL.md) remains in force.
  Reference transfers and baseline profiles cannot become a ceiling on existing
  qualified transforms, engines, run settings, commands or private extensions.
