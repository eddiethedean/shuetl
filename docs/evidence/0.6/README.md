# Phase 0.6 evidence index

This index records the ShuETL 0.6.0 implementation against published
ETLantic 0.56.2. It is an open qualification record, not a preview support
claim. The planned acceptance contract is in
PHASE_0_6_EXECUTION.md; the contract, ownership, process observations,
provider status, transition, and CI definition provide supporting context.

## Implementation evidence

| Field | Value |
| --- | --- |
| Source commit | 3b27a55f28c9c4671a8eb7f057a81ac775d5420c (implementation source; hosted run 37668515171) |
| OS and architecture | macOS 26.6.2 arm64 local |
| Python version | CPython 3.13.9 local; hosted Python 3.11–3.13 matrix passed in run 37668515171 |
| uv version | 0.11.3 |
| ETLantic source revision | Published etlantic, etlantic-fastapi, and etlantic-sqlmodel 0.56.2 wheels; optional SQL/Foundry pins are 0.56.2 |
| ShuETL import origin | Editable local source at src/shuetl; isolated wheel uses site-packages |
| ETLantic import origin | ETLantic 0.56.2 installed wheel in project environment; isolated wheel check uses site-packages |
| etlantic-fastapi import origin | ETLantic FastAPI 0.56.2 installed wheel; isolated wheel check uses site-packages |
| FastAPI import origin | FastAPI 0.141.1 installed dependency; isolated wheel check uses site-packages |
| Pydantic import origin | Pydantic 2.13.5 installed dependency; isolated wheel check uses site-packages |
| HTTPX import origin | httpx2 2.12.0 test extra in isolated site-packages; clean-wheel output records its import origin |
| Gate A | Hosted quality and regression matrix on Python 3.11–3.13, pending 0.56.2 run | OPEN |
| Gate B | PostgreSQL 18.6 runtime integration with no schema `CREATE`, pending | OPEN |
| Gate C | Hosted artifact and installed-wheel qualification matrix, pending 0.56.2 run | OPEN |
| SHA-256 wheel | `34112e77cfa28ca48d50319ebea11c7594415350ea522c073cf9b8aa4fa4919a` |
| SHA-256 sdist | `f47e4d3c88003b65e98b3d0ab96f29efd3f967db66d699b98d8dedef8a9d9c23` |

## Acceptance results

The acceptance table follows the exact approved contract. Each row binds to
a qualification section and records the command and limitation. An open
result means no acceptance claim is made from code inspection, upstream
evidence, or a configured workflow alone.

| Criterion | Task | Command | Artifact | Status | Limitation | Reviewer | Date |
| --- | --- | --- | --- | --- | --- | --- | --- |
| AC-001 | package pins and artifacts | uv lock --check && uv run python scripts/check_artifact.py | qualification.md#ac-001 | PASS | Hosted metadata checks passed; the remaining runtime acceptance criteria are separate and remain open. | implementation run | 2026-10-07 |
| AC-002 | installed artifact Gate 0 | uv run python scripts/check_clean_wheel.py | qualification.md#ac-002 | OPEN | The current fixture removes schema `CREATE`, but no hosted 0.56.2 PostgreSQL run has validated it yet. | implementation run | 2026-10-08 |
| AC-003 | role startup validation | uv run pytest tests/unit/test_phase_0_6_runtime.py tests/unit/test_package.py -q | qualification.md#ac-003 | OPEN | No installed-artifact starts or full negative matrix for missing runner and incompatible packages has been captured. | implementation run | 2026-10-07 |
| AC-004 | 0.56 regression compatibility | uv run pytest -q | qualification.md#ac-004 | OPEN | Local PostgreSQL integration cases are skipped without a database; clean-store HTTP/SSE and doctor qualification on the hosted matrix remains open. | implementation run | 2026-10-07 |
| AC-005 | gateway execution boundary | uv run pytest tests/unit/test_phase_0_6_runtime.py -k gateway -q && uv run python scripts/check_clean_wheel.py | qualification.md#ac-005 | OPEN | Import isolation is verified locally against the published wheel. Separate-process proofs for secret resolution and pipeline execution remain open. | implementation run | 2026-10-08 |
| AC-006 | runtime identity and ownership | uv run pytest tests/unit/test_phase_0_6_runtime.py -k context -q | qualification.md#ac-006 | OPEN | Typed scope checks are present; process startup and credential-verifier import isolation have not been exercised. | implementation run | 2026-10-07 |
| AC-007 | shared store and scheduler recovery | uv run pytest tests/unit/test_phase_0_6_runtime.py::test_role_builder_uses_shared_headless_backend_and_bound_scheduler_callback -q | qualification.md#ac-007 | OPEN | The bound callback and same-engine schedule-store wiring are unit-checked; crash and retry behavior across firing, acceptance, and linking commits has not been tested. | implementation run | 2026-10-07 |
| AC-008 | restricted database startup | uv run python scripts/check_clean_wheel.py | qualification.md#ac-008 | OPEN | The fixture now withholds schema `CREATE` and compares schema/migration state; hosted PostgreSQL 18.6 execution is pending. | implementation run | 2026-10-08 |
| AC-009 | readiness and liveness | uv run pytest tests/unit/test_phase_0_6_runtime.py::test_probe_lifecycle_reports_outage_drain_and_stale_state_without_secrets -q | qualification.md#ac-009 | OPEN | Probe state is unit-tested; real process startup, schema mismatch, and database outage transitions remain unqualified. | implementation run | 2026-10-07 |
| AC-010 | signal drain and cleanup | NOT RUN (no signal-driven in-flight process fixture exists) | qualification.md#ac-010 | OPEN | SIGTERM/SIGINT during active acceptance, lease claim, effect, and grace expiry have no process-level evidence. | implementation run | 2026-10-07 |
| AC-011 | concurrent gateway idempotency | NOT RUN (no separate-process gateway contention fixture exists) | qualification.md#ac-011 | OPEN | Concurrent gateway acceptance and canonical retry identity have not been exercised across OS processes. | implementation run | 2026-10-07 |
| AC-012 | gateway commit-boundary recovery | NOT RUN (no gateway kill-point fixture exists) | qualification.md#ac-012 | OPEN | Before-commit and after-commit client ambiguity outcomes have not been injected or observed. | implementation run | 2026-10-07 |
| AC-013 | duplicate scheduler firing | NOT RUN (no separate-process scheduler contention fixture exists) | qualification.md#ac-013 | OPEN | Two scheduler processes have not been raced against one due logical occurrence. | implementation run | 2026-10-07 |
| AC-014 | scheduler commit-boundary recovery | NOT RUN (no scheduler kill-point fixture exists) | qualification.md#ac-014 | OPEN | Firing-claim, durable acceptance, and link recovery have not been fault-injected. | implementation run | 2026-10-07 |
| AC-015 | duplicate worker and effect semantics | NOT RUN (no separate-process worker contention fixture exists) | qualification.md#ac-015 | OPEN | Lease contention and duplicate external effects have not been observed across workers. | implementation run | 2026-10-07 |
| AC-016 | worker loss and lease recovery | NOT RUN (no worker kill-point fixture exists) | qualification.md#ac-016 | OPEN | Worker death before/after lease acquisition and lease expiry have not been tested. | implementation run | 2026-10-07 |
| AC-017 | stale fencing | NOT RUN (no process-level stale-worker fixture exists) | qualification.md#ac-017 | OPEN | No stale worker completion has been rejected after ownership or fencing-token change in this runtime. | implementation run | 2026-10-07 |
| AC-018 | cancellation outcomes | NOT RUN (no live cancellation fixture exists) | qualification.md#ac-018 | OPEN | Accepted, leased, and running cancellation outcomes and uncertain effects have not been exercised. | implementation run | 2026-10-07 |
| AC-019 | database outage recovery | NOT RUN (no runtime disconnect/reconnect fixture exists) | qualification.md#ac-019 | OPEN | Readiness recovery and upstream work resumption after database restoration have not been demonstrated. | implementation run | 2026-10-07 |
| AC-020 | observable ETL sink effect | uv run python scripts/check_clean_wheel.py | qualification.md#ac-020 | OPEN | Historical 0.56.0 sink evidence used in-process TestClient instances; 0.56.2 installed-wheel execution on hosted PostgreSQL is pending. | implementation run | 2026-10-08 |
| AC-021 | credential and secret redaction | uv run python scripts/check_clean_wheel.py | qualification.md#ac-021 | OPEN | The CLI mismatch smoke checks URL redaction; durable payload, report, event, log, and worker-secret boundaries are not comprehensively tested. | implementation run | 2026-10-07 |
| AC-022 | deployment recipes | NOT RUN (Compose and systemd services have not been rehearsed) | qualification.md#ac-022 | OPEN | Compose and systemd examples are present; digest identity, ordinary supervisor startup, and shutdown have not been rehearsed. | implementation run | 2026-10-07 |
| AC-023 | hosted release matrix | Pending current 0.56.2 GitHub Actions run | qualification.md#ac-023 | OPEN | Historical 0.56.0 matrix passed, but the current source revision has not run in hosted CI. | implementation run | 2026-10-08 |
| AC-024 | criterion evidence ledger | uv run python scripts/check_evidence.py --evidence docs/evidence/0.6 | qualification.md#ac-024 | PASS | This check validates ledger structure and references only; it does not establish the underlying runtime acceptance results. | implementation run | 2026-10-07 |
| AC-025 | fresh-store cutover and rollback | NOT RUN (no migration or rollback rehearsal exists) | qualification.md#ac-025 | OPEN | The handoff sequence is documented; live re-enrollment, reconciliation, sole-authority rollback, and no-replay behavior remain untested. | implementation run | 2026-10-07 |
| AC-026 | trusted factory and typed bindings | uv run pytest tests/unit/test_phase_0_6_runtime.py -q | qualification.md#ac-026 | OPEN | Core binding and scope checks are unit-tested; full malformed-factory, redaction, and installed-role matrix is open. | implementation run | 2026-10-07 |
| AC-027 | independent reference host | uv run python scripts/check_clean_wheel.py | qualification.md#ac-027 | OPEN | The transfer fixture covers manual/scheduled API shape; independent host specifications, transformations, quality, and headless parity are not qualified. | implementation run | 2026-10-07 |
| AC-028 | provider and transformation matrix | NOT RUN (provider-pairing and quality matrix fixture is absent) | qualification.md#ac-028 | OPEN | Only the PostgreSQL upsert fixture is configured; CSV, transforms, quality failures, and other advertised write modes remain unsupported or unqualified. | implementation run | 2026-10-07 |
| AC-029 | canonical discovery and controls | NOT RUN (live discovery and option-round-trip fixture is absent) | qualification.md#ac-029 | OPEN | Schema/control discovery and effective per-run options have no ShuETL live evidence. | implementation run | 2026-10-07 |
| AC-030 | retry, rerun, and extension | NOT RUN (retry/rerun and independent-extension fixture is absent) | qualification.md#ac-030 | OPEN | No live retry/rerun identity proof or independently installed example extension is included. | implementation run | 2026-10-07 |
| AC-031 | immutable input and report artifacts | NOT RUN (cross-worker resource lifecycle fixture is absent) | qualification.md#ac-031 | OPEN | Checksum, owner/version access, expiry, retry retention, cross-worker availability, and bounded cleanup are not qualified. | implementation run | 2026-10-07 |
| AC-032 | runtime probe and log safety | uv run pytest tests/unit/test_phase_0_6_runtime.py::test_probe_lifecycle_reports_outage_drain_and_stale_state_without_secrets -q | qualification.md#ac-032 | OPEN | Probe state and bounded reasons are unit-tested; live execution, idle, outage, drain, and seeded-secret log checks are not captured. | implementation run | 2026-10-07 |
| AC-033 | provider action workers | uv run pytest tests/unit/test_phase_0_6_runtime.py::test_action_worker_requires_external_handlers_and_uses_upstream_host -q | qualification.md#ac-033 | OPEN | Host selection is unit-tested; live catalog, schema, preflight, preview, provisioning, revocation, and deadline cases remain open. | implementation run | 2026-10-07 |

## Gap register

The no-`CREATE` database-startup boundary, multiprocess failure injection,
provider and transformation coverage, and transition rehearsal remain open.
The integration burden stays in ShuETL's composition layer; public composition hooks
remain injected; no copied route or ETL state machine has been introduced. The
boundary outcome is qualification-open until the remaining acceptance criteria
and Gate B are satisfied.

Hosted run 37668515171 passed the earlier 0.56.0 Gate A, Gate C, and PostgreSQL
integration matrix. It does not qualify the current 0.56.2 implementation.
Current hosted results are pending; all open acceptance criteria and the
preview decision remain open.
