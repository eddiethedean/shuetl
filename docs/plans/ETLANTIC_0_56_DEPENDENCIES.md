# ETLantic Backend Dependencies for ShuETL 0.6

## Current dependency decision — 2026-10-09

[ADR-0015](../adr/0015-backend-and-deployment-ownership.md) and the revised
[execution contract](PHASE_0_6_EXECUTION.md) supersede selection of 0.56.0 as-is.
ETLantic `0.57.0` core/FastAPI/SQLModel is the **accepted exact development
train**. [Coverage acceptance](../evidence/0.6/coverage-acceptance.md) closes
U01–U05 with guarantee-specific consumer and provider evidence, supplementing
[the artifact audit](../reviews/ETLANTIC_0_57_CANDIDATE_AUDIT.md).
Metadata, lock and compatibility checks now agree. Non-ETLantic runtime pins
remain unchanged. PostgreSQL role feasibility is qualified in
[Gate 0 evidence](../evidence/0.6/README.md); release gates remain OPEN.

| Gate | Upstream issue | Required delivery | Status |
| --- | --- | --- | --- |
| U01 | [#278 — Neutral backend](https://github.com/eddiethedean/etlantic/issues/278) | Transport-independent services/role contracts, provider-owned SQL graph, explicit cleanup; separate HTTP adapter | PASS — 0.57.0 coverage accepted 2026-10-09 |
| U02 | [#279 — Schedule commands](https://github.com/eddiethedean/etlantic/issues/279) | Authorized public schedule command/query services with HTTP/headless parity | PASS — 0.57.0 coverage accepted 2026-10-09 |
| U03 | [#280 — Managed scheduler](https://github.com/eddiethedean/etlantic/issues/280) | Complete schedule-store/factory construction and explicit preparation/submission/recovery contract | PASS — 0.57.0 coverage accepted 2026-10-09 |
| U04 | [#281 — Provider inspection](https://github.com/eddiethedean/etlantic/issues/281) | Public provider-owned read-only schema compatibility/status, including partial/corrupt stores | PASS — 0.57.0 coverage accepted 2026-10-09 |
| U05 | [#282 — Runtime lifecycle](https://github.com/eddiethedean/etlantic/issues/282) | Public role-specific status and cooperative-stop guarantees for all role kinds | PASS — 0.57.0 coverage accepted 2026-10-09 |

The GitHub trackers still report OPEN on 2026-10-09. Track administrative issue
closure separately from delivered API surfaces and ShuETL's acceptance decision.

These five issues were opened from the
[responsibility review](../reviews/PHASE_0_6_RESPONSIBILITY_REVIEW.md). Canonical
capability schemas, plugin trust, handler loading, context validity and conformance
remain upstream; ShuETL qualifies its deployment combinations and public adapters.

## Inspected published artifacts

On 2026-10-09, independent isolated installations verified `0.57.0` neutral
backend construction, shared authorized schedule services, complete runtime
factories/status/drain and provider-owned read-only inspection. Gateway checks
also pass with ShuETL's current FastAPI/Pydantic/SQLAlchemy pins. Upstream CI
acceptance records 160 passing cases with no failures/errors/skips, including
PostgreSQL; its core/provider wheel hashes match PyPI. Exact signatures, hashes,
results and reproducible environments are in the
[candidate audit](../reviews/ETLANTIC_0_57_CANDIDATE_AUDIT.md).

The provider head remains `014_cp1_complete_principal_idempotency_0_56` with no
new 0.56-to-0.57 migration. This does not qualify a direct transition from the
retained 0.5/0.55 store. The initial SQLite probes are supplemented by PostgreSQL Gate 0.
Neither establishes process signal/grace qualification or final release evidence.

### Historical 0.56 observations

The original [0.56.0 wheel audit](ETLANTIC_0_56_WHEEL_AUDIT.md) remains historical
artifact evidence. Its hashes and upstream 44/44 result do not qualify the revised
Gate U or ShuETL 0.6 deployment.

On 2026-10-08, the review additionally installed exact core/FastAPI/SQLModel
`0.56.2` distributions in isolation and inspected the
[v0.56.2 release](https://github.com/eddiethedean/etlantic/releases/tag/v0.56.2).
[Issue #273](https://github.com/eddiethedean/etlantic/issues/273) is closed and
0.56.2 contains gateway import-isolation and read-only migration-version changes.
A disposable SQLite probe confirmed no CREATE in version inspection on a fresh
or migrated store. The former constructor-DDL exception is removed from 0.6.
Actual PostgreSQL runtime grants and full construction still require qualification.

That 0.56.2 probe confirmed its standard backend requires an HTTP context
factory and has no configured schedule store or scheduler factory. Wrapping a
submission callback still loses automatic preparer/recoverer discovery. Source
inspection found schedule command orchestration in HTTP handlers and incomplete
role status/stop contracts. U04 additionally requires schema integrity/required
objects behind a provider API; it does not re-file the fixed DDL defect.

Version 0.56.2 is historical inspected evidence; its remaining gaps above are
addressed by the 0.57.0 candidate. The development target is now ShuETL 0.6.0 with exact 0.57.0 pins;
the published 0.5/0.55 deployment remains the retained rollback baseline. Pin optional SQL/Foundry or other
providers only when enabled and compatible with the selected backend; retain
upstream conformance and separate live integration rows.

## Historical findings and 0.56 qualification map

These rows retain the original requirements for traceability. Their historical closure does not close the newly identified Gate U
requirements above; downstream claims still require ShuETL evidence.

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

- W00 reviews/accepts the published 0.57.0 candidate for U01–U05 using exact signatures and upstream
  conformance plus isolated-install checks. No semantic workaround in ShuETL.
- W01 pins the accepted compatible package train, hashes and public provider
  schema contract. Start with exact 0.57.0 candidates; do not automatically float.
- W02/Gate 0 proves isolated PostgreSQL role construction, actual runtime grants,
  manual/native-scheduled effects and authorized HTTP/headless command parity.
- W03/W04 implement ShuETL configuration, host bindings, upstream factory selection,
  process supervision and probes; ETL graphs and correctness remain upstream.
- Preserve a fresh separate store and the retained 0.5/0.55 deployment for rollback.
  No constructor DDL, old durable-store conversion or cross-store replay.
- Final installed-artifact acceptance covers all 33 criteria plus Gates U/0/A–C.
  Phase 0.7 retains the broader downstream operating/cutover qualification.
