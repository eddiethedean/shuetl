# Phase 0.6 implementation review corrections

Recorded: 2026-10-09. All nine implementation-review findings are corrected.
This is a source-change verification record, not release approval. Exact dependency
pins are unchanged. Gates A–C and the remaining deployment acceptance work stay
open; existing evidence hashes refer to the earlier development build.

| Finding | Correction | Regression coverage |
| --- | --- | --- |
| Dispatch remains stalled after an outage | Permit paced, fresh-provider-checked bootstrap/recovery ticks. Upstream role handles own prerequisite checks and admission; recovered faults no longer force a failed graceful exit. | Real published scheduler with transient lease-store and thrown tick failures in `tests/integration/test_runtime_supervision.py`. |
| Evidence checker accepts placeholder PASS rows | Require all 33 audited proof bindings, approved requirements, locatable qualification/provenance, populated review fields, Gates U/0/A/B/C, all five upstream decisions and executed results without skips. | Complete synthetic ledger plus missing/substituted proofs, failed prerequisite gates, placeholders, skipped cases and extra criteria in `tests/unit/test_phase06_evidence.py`. |
| Host failures leak exception text through CLI | Limit detailed configuration reporting to settings/flag validation; factory/import/runtime failures use bounded diagnostics. | Credential sentinels in factory, import and serve failures in `tests/unit/test_runtime_failures.py`. |
| Active backend closure prematurely frees host resources | Preserve host resources and retryable wrapper state if upstream refuses close. Close bindings only after successful backend closure. | Blocked real upstream scheduler tick and successful later cleanup; isolated retry/close-order test. |
| Gateway reports ready before ASGI startup | Require completed lifespan/listener startup as well as fresh provider health. | Blocked real FastAPI lifespan, false readiness and refused connection before startup, followed by healthy listener/readiness. |
| Gateway bind failure exits successfully | Catch server-thread `SystemExit`; treat aborted startup and unexpected server return as failures. | Occupied socket, failing lifespan and `SystemExit(0)` all exit unsuccessfully. |
| Required action handlers cannot be configured | Add a keyword-only runtime binding mapping, snapshot it at the factory boundary and forward it to public upstream backend configuration. Gateway bindings omit this worker configuration. | Host handler executes a real canonical connector action job through the published action host; mapping mutation and malformed configuration tests. |
| Rejected wrong-role bindings leak resources | Put all validation after factory execution under a single cleanup guard; wrap accepted cleanup callbacks once. | Both role mismatches and malformed context release host resources exactly once. |
| Gate 0 assumes trust authentication | Generate independent disposable migration/runtime passwords and use the matching credentials in each connection URL. | Installed-artifact Gate 0 passes against PostgreSQL 18.6 with host authentication set to SCRAM-SHA-256. |

## Verification

- Full local suite: **244 passed, 6 skipped**. Five skips were unconfigured
  PostgreSQL tests; the remaining skip is the existing final-release hash test.
- Explicit disposable PostgreSQL regression: **5 passed, no skips**, confirmed
  with `check_pytest_no_skips.py`.
- Focused runtime, binding, evidence and supervision suite after final source
  changes: **43 passed**; includes **36 new regression cases**.
- Ruff lint/format, Pyright, boundary checks and `uv lock --check`: PASS.
- Fresh wheel installed outside the checkout on Python 3.13.9: Gate 0 PASS and
  four-role CLI startup/readiness/SIGTERM smoke PASS on PostgreSQL 18.6 with
  SCRAM authentication. Both harnesses report all four roles and clean shutdown.
- The release evidence checker intentionally rejects the current OPEN criteria,
  missing final proof registry/qualification/hosted record and open release gates.
- Disposable databases, roles, child processes and the owned PostgreSQL container
  were cleaned up. Hosted acceptance, complete live provider-action qualification,
  failure/transition rehearsals and final artifact promotion remain open.

The action-handler test establishes composition and canonical job execution; it
does not certify live provider behavior or close AC-033. No upstream persistence,
ETL, scheduler, authorization or action-result semantics were moved into ShuETL.
