# Phase 0.6 qualification record

Status: implementation evidence is recorded; preview qualification remains open.

The records below include historical qualification results from ETLantic 0.56.0.
Those runs do not qualify the current implementation, which now targets ETLantic
0.56.2. OPEN means the required result has not been established for the current
source and artifact. AC-024 passes only as a ledger-integrity criterion.

## Environment and source

- Current source commit: 24ca3920b0a2171e827c5b607ac4c4907af8217f (ETLantic 0.56.2 implementation; hosted qualification pending).
- Historical source commits below identify the earlier 0.56.0 runs.
- Upstream: published ETLantic, etlantic-fastapi, and
  etlantic-sqlmodel wheels at 0.56.0; optional SQL and Foundry packages
  are pinned to 0.56.0.
- Local environment: macOS 26.6.2 arm64, CPython 3.13.9, uv 0.11.3.
- The local shell had no SHUETL_DATABASE_URL; PostgreSQL integration was
  not run. GitHub Actions has not run for this implementation revision.
- The proof registry maps each approved requirement to its exact source
  criterion, command, result section, and limitation.

## AC-001

Requirement: Source, wheel, lock, and clean-wheel metadata identify ShuETL `0.6.0`, Python 3.11–3.13, exact ETLantic core/FastAPI/SQLModel `0.56.2` pins (and SQL/Foundry `0.56.2` when enabled), the PostgreSQL extra, and migration head `014_cp1_complete_principal_idempotency_0_56`.

Command: uv lock --check && uv run python scripts/check_artifact.py

Result: PASS

Observed result: The current source passed `uv lock --check` and `scripts/check_artifact.py`; the clean-wheel environments resolve core and optional ETLantic packages to 0.56.2.

Source commit: bf72590.

Upstream: published ETLantic 0.56.2 wheels.

Environment: macOS 26.6.2 arm64, CPython 3.13.9, uv 0.11.3; local release gate.

Artifact: docs/evidence/0.6/contracts.md; implementation/test reference: package pins and artifacts.

Provenance: docs/plans/PHASE_0_6_EXECUTION.md#acceptance-criteria.

Limitation: Hosted metadata checks passed; the remaining runtime acceptance criteria are separate and remain open.

## AC-002

Requirement: An installed-artifact Gate 0 probe executes one real scheduled and one manual submission through the selected PostgreSQL-backed upstream roles; the worker produces an observable ETLantic report rather than no-op completion.

Command: uv run python scripts/check_clean_wheel.py

Result: OPEN

Observed result: Historical hosted PR run 37661869120 passed the installed-wheel manual and scheduled submission fixture on Python 3.11–3.13. The current 0.56.2 fixture now removes schema CREATE privileges; no hosted run has qualified this revision.

Source commit: a3018159e4243fd53a8f6ac3bde9a31e2adb91c8.

Upstream: published ETLantic 0.56.0 wheels.

Environment: GitHub Actions ubuntu-24.04, PostgreSQL 18.6, Python 3.11–3.13, uv 0.11.3; installed wheel and separate runtime role; hosted PR run 37661869120.

Artifact: docs/evidence/0.6/contracts.md; implementation/test reference: installed artifact Gate 0.

Provenance: docs/plans/PHASE_0_6_EXECUTION.md#acceptance-criteria.

Limitation: The current fixture removes schema `CREATE`, but no hosted 0.56.2 PostgreSQL run has validated it yet.

## AC-003

Requirement: A single built application artifact starts each of the three roles; wrong/missing role, mismatched `--role` and `SHUETL_ROLE`, local provider, demo identity, missing runner, or incompatible package fails before serving or claiming work.

Command: uv run pytest tests/unit/test_phase_0_6_runtime.py tests/unit/test_package.py -q

Result: OPEN

Observed result: Implementation or fixture status only; the required acceptance result has not been recorded.

Source commit: 6b947b82c7b46c5b38471142f1958f4dc6083144.

Upstream: published ETLantic 0.56.0 wheels.

Environment: macOS 26.6.2 arm64, CPython 3.13.9, uv 0.11.3; no local PostgreSQL URL; no hosted run for this revision.

Artifact: docs/evidence/0.6/contracts.md; implementation/test reference: role startup validation.

Provenance: docs/plans/PHASE_0_6_EXECUTION.md#acceptance-criteria.

Limitation: No installed-artifact starts or full negative matrix for missing runner and incompatible packages has been captured.

## AC-004

Requirement: Existing gateway/local settings, facade, identity, HTTP/SSE and doctor contracts are requalified on 0.56 with fresh stores; `postgresql-pilot` stays gateway-only and no implicit preview or 0.55-store upgrade occurs.

Command: uv run pytest -q

Result: OPEN

Observed result: Implementation or fixture status only; the required acceptance result has not been recorded.

Source commit: 6b947b82c7b46c5b38471142f1958f4dc6083144.

Upstream: published ETLantic 0.56.0 wheels.

Environment: macOS 26.6.2 arm64, CPython 3.13.9, uv 0.11.3; no local PostgreSQL URL; no hosted run for this revision.

Artifact: docs/evidence/0.6/contracts.md; implementation/test reference: 0.56 regression compatibility.

Provenance: docs/plans/PHASE_0_6_EXECUTION.md#acceptance-criteria.

Limitation: Local PostgreSQL integration cases are skipped without a database; clean-store HTTP/SSE and doctor qualification on the hosted matrix remains open.

## AC-005

Requirement: Gateway construction and request handling never start scheduler/worker ticks, import the runner, resolve pipeline secrets, or execute a pipeline.

Command: uv run pytest tests/unit/test_phase_0_6_runtime.py -k gateway -q && uv run python scripts/check_clean_wheel.py

Result: OPEN

Observed result: Published ETLantic 0.56.2 fixes the gateway import boundary; the clean-wheel checker now imports `etlantic_fastapi` in a fresh interpreter and asserts neither execution module is loaded. The unit suite covers gateway/runtime separation. Process-level secret and execution isolation remain unqualified.

Source commit: 6b947b82c7b46c5b38471142f1958f4dc6083144.

Upstream: published ETLantic 0.56.0 wheels.

Environment: macOS 26.6.2 arm64, CPython 3.13.9, uv 0.11.3; no local PostgreSQL URL; no hosted run for this revision.

Artifact: docs/evidence/0.6/contracts.md; implementation/test reference: gateway execution boundary.

Provenance: docs/plans/PHASE_0_6_EXECUTION.md#acceptance-criteria.

Limitation: Import isolation is verified locally against the published wheel. Separate-process proofs for secret resolution and pipeline execution remain open.

## AC-006

Requirement: Scheduler and worker construct no FastAPI app or host credential verifier; each receives a trusted, scope-bound ETLantic service context and a unique owner ID.

Command: uv run pytest tests/unit/test_phase_0_6_runtime.py -k context -q

Result: OPEN

Observed result: Implementation or fixture status only; the required acceptance result has not been recorded.

Source commit: 6b947b82c7b46c5b38471142f1958f4dc6083144.

Upstream: published ETLantic 0.56.0 wheels.

Environment: macOS 26.6.2 arm64, CPython 3.13.9, uv 0.11.3; no local PostgreSQL URL; no hosted run for this revision.

Artifact: docs/evidence/0.6/contracts.md; implementation/test reference: runtime identity and ownership.

Provenance: docs/plans/PHASE_0_6_EXECUTION.md#acceptance-criteria.

Limitation: Typed scope checks are present; process startup and credential-verifier import isolation have not been exercised.

## AC-007

Requirement: All roles use the same provider schema/store identity. Scheduler passes the bound `submit_scheduled_run` method; crash/retry proofs cover occurrence preparation, firing claim, managed acceptance and linking on same-engine stores without assuming one atomic commit.

Command: uv run pytest tests/unit/test_phase_0_6_runtime.py::test_role_builder_uses_shared_headless_backend_and_bound_scheduler_callback -q

Result: OPEN

Observed result: Implementation or fixture status only; the required acceptance result has not been recorded.

Source commit: 6b947b82c7b46c5b38471142f1958f4dc6083144.

Upstream: published ETLantic 0.56.0 wheels.

Environment: macOS 26.6.2 arm64, CPython 3.13.9, uv 0.11.3; no local PostgreSQL URL; no hosted run for this revision.

Artifact: docs/evidence/0.6/contracts.md; implementation/test reference: shared store and scheduler recovery.

Provenance: docs/plans/PHASE_0_6_EXECUTION.md#acceptance-criteria.

Limitation: The bound callback and same-engine schedule-store wiring are unit-checked; crash and retry behavior across firing, acceptance, and linking commits has not been tested.

## AC-008

Requirement: Every role performs read-only compatibility/connectivity/schema preflight and health inspection. Backend construction under a runtime role without schema-creation privileges performs no DDL; missing/incorrect schema fails before construction. Migration is possible only through the explicit operator command.

Command: uv run python scripts/check_clean_wheel.py

Result: OPEN

Observed result: The PostgreSQL fixture now provisions the runtime role without schema `CREATE` and verifies that managed role construction leaves the schema snapshot and migration version unchanged. ETLantic 0.56.2's published `current_version()` check uses inspection and `SELECT`; the hosted 0.56.2 result is pending.

Source commit: 6b947b82c7b46c5b38471142f1958f4dc6083144.

Upstream: published ETLantic 0.56.0 wheels.

Environment: macOS 26.6.2 arm64, CPython 3.13.9, uv 0.11.3; no local PostgreSQL URL; no hosted run for this revision.

Artifact: docs/evidence/0.6/contracts.md; implementation/test reference: restricted database startup.

Provenance: docs/plans/PHASE_0_6_EXECUTION.md#acceptance-criteria.

Limitation: The fixture now withholds schema `CREATE` and compares schema/migration state; hosted PostgreSQL 18.6 execution is pending.

## AC-009

Requirement: Role-local liveness/readiness report startup, running, draining, provider outage, and schema mismatch without false success or secret-bearing output.

Command: uv run pytest tests/unit/test_phase_0_6_runtime.py::test_probe_lifecycle_reports_outage_drain_and_stale_state_without_secrets -q

Result: OPEN

Observed result: Implementation or fixture status only; the required acceptance result has not been recorded.

Source commit: 6b947b82c7b46c5b38471142f1958f4dc6083144.

Upstream: published ETLantic 0.56.0 wheels.

Environment: macOS 26.6.2 arm64, CPython 3.13.9, uv 0.11.3; no local PostgreSQL URL; no hosted run for this revision.

Artifact: docs/evidence/0.6/contracts.md; implementation/test reference: readiness and liveness.

Provenance: docs/plans/PHASE_0_6_EXECUTION.md#acceptance-criteria.

Limitation: Probe state is unit-tested; real process startup, schema mismatch, and database outage transitions remain unqualified.

## AC-010

Requirement: SIGTERM/SIGINT fail readiness, stop new request/tick dispatch, invoke drain and await in-flight work before one-time cleanup. Evidence distinguishes in-flight acceptance/claim windows and grace-period expiry; no concurrent engine disposal or fabricated terminal result occurs.

Command: uv run pytest tests/unit/test_phase_0_6_runtime.py::test_runtime_role_signal_drains_active_tick_before_one_time_cleanup -q

Result: OPEN

Observed result: Implementation or fixture status only; the required acceptance result has not been recorded.

Source commit: 6b947b82c7b46c5b38471142f1958f4dc6083144.

Upstream: published ETLantic 0.56.0 wheels.

Environment: macOS 26.6.2 arm64, CPython 3.13.9, uv 0.11.3; no local PostgreSQL URL; no hosted run for this revision.

Artifact: docs/evidence/0.6/contracts.md; implementation/test reference: signal drain and cleanup.

Provenance: docs/plans/PHASE_0_6_EXECUTION.md#acceptance-criteria.

Limitation: Deterministic unit coverage verifies signal-to-drain ordering and one-time cleanup for an active tick; separate-process SIGTERM/SIGINT, acceptance/lease/effect kill points, and grace expiry remain unqualified.

## AC-011

Requirement: Two gateway processes given the same scope and idempotency key yield one canonical accepted submission after concurrent requests and retry.

Command: NOT RUN (no separate-process gateway contention fixture exists)

Result: OPEN

Observed result: Implementation or fixture status only; the required acceptance result has not been recorded.

Source commit: 6b947b82c7b46c5b38471142f1958f4dc6083144.

Upstream: published ETLantic 0.56.0 wheels.

Environment: macOS 26.6.2 arm64, CPython 3.13.9, uv 0.11.3; no local PostgreSQL URL; no hosted run for this revision.

Artifact: docs/evidence/0.6/contracts.md; implementation/test reference: concurrent gateway idempotency.

Provenance: docs/plans/PHASE_0_6_EXECUTION.md#acceptance-criteria.

Limitation: Concurrent gateway acceptance and canonical retry identity have not been exercised across OS processes.

## AC-012

Requirement: Killing a gateway before versus after durable acceptance produces the documented ambiguous-client/committed-store outcomes; retry with the same idempotency key recovers the canonical identity.

Command: NOT RUN (no gateway kill-point fixture exists)

Result: OPEN

Observed result: Implementation or fixture status only; the required acceptance result has not been recorded.

Source commit: 6b947b82c7b46c5b38471142f1958f4dc6083144.

Upstream: published ETLantic 0.56.0 wheels.

Environment: macOS 26.6.2 arm64, CPython 3.13.9, uv 0.11.3; no local PostgreSQL URL; no hosted run for this revision.

Artifact: docs/evidence/0.6/contracts.md; implementation/test reference: gateway commit-boundary recovery.

Provenance: docs/plans/PHASE_0_6_EXECUTION.md#acceptance-criteria.

Limitation: Before-commit and after-commit client ambiguity outcomes have not been injected or observed.

## AC-013

Requirement: Two scheduler processes scanning one due schedule create exactly one canonical firing and linked durable submission for the logical key.

Command: NOT RUN (no separate-process scheduler contention fixture exists)

Result: OPEN

Observed result: Implementation or fixture status only; the required acceptance result has not been recorded.

Source commit: 6b947b82c7b46c5b38471142f1958f4dc6083144.

Upstream: published ETLantic 0.56.0 wheels.

Environment: macOS 26.6.2 arm64, CPython 3.13.9, uv 0.11.3; no local PostgreSQL URL; no hosted run for this revision.

Artifact: docs/evidence/0.6/contracts.md; implementation/test reference: duplicate scheduler firing.

Provenance: docs/plans/PHASE_0_6_EXECUTION.md#acceptance-criteria.

Limitation: Two scheduler processes have not been raced against one due logical occurrence.

## AC-014

Requirement: A scheduler crash around firing claim and durable acceptance recovers without an orphaned success claim or a second logical firing.

Command: NOT RUN (no scheduler kill-point fixture exists)

Result: OPEN

Observed result: Implementation or fixture status only; the required acceptance result has not been recorded.

Source commit: 6b947b82c7b46c5b38471142f1958f4dc6083144.

Upstream: published ETLantic 0.56.0 wheels.

Environment: macOS 26.6.2 arm64, CPython 3.13.9, uv 0.11.3; no local PostgreSQL URL; no hosted run for this revision.

Artifact: docs/evidence/0.6/contracts.md; implementation/test reference: scheduler commit-boundary recovery.

Provenance: docs/plans/PHASE_0_6_EXECUTION.md#acceptance-criteria.

Limitation: Firing-claim, durable acceptance, and link recovery have not been fault-injected.

## AC-015

Requirement: Two workers contending for one item honor upstream leases; one authoritative attempt result is recorded while duplicate external effects remain subject to the documented at-least-once contract.

Command: NOT RUN (no separate-process worker contention fixture exists)

Result: OPEN

Observed result: Implementation or fixture status only; the required acceptance result has not been recorded.

Source commit: 6b947b82c7b46c5b38471142f1958f4dc6083144.

Upstream: published ETLantic 0.56.0 wheels.

Environment: macOS 26.6.2 arm64, CPython 3.13.9, uv 0.11.3; no local PostgreSQL URL; no hosted run for this revision.

Artifact: docs/evidence/0.6/contracts.md; implementation/test reference: duplicate worker and effect semantics.

Provenance: docs/plans/PHASE_0_6_EXECUTION.md#acceptance-criteria.

Limitation: Lease contention and duplicate external effects have not been observed across workers.

## AC-016

Requirement: Worker death before and after lease acquisition and on lease expiry leads to the exact upstream recovery state; no work is reported completed by an absent or no-op runner.

Command: NOT RUN (no worker kill-point fixture exists)

Result: OPEN

Observed result: Implementation or fixture status only; the required acceptance result has not been recorded.

Source commit: 6b947b82c7b46c5b38471142f1958f4dc6083144.

Upstream: published ETLantic 0.56.0 wheels.

Environment: macOS 26.6.2 arm64, CPython 3.13.9, uv 0.11.3; no local PostgreSQL URL; no hosted run for this revision.

Artifact: docs/evidence/0.6/contracts.md; implementation/test reference: worker loss and lease recovery.

Provenance: docs/plans/PHASE_0_6_EXECUTION.md#acceptance-criteria.

Limitation: Worker death before/after lease acquisition and lease expiry have not been tested.

## AC-017

Requirement: A stale worker cannot commit an authoritative terminal result after lease ownership or fencing token changes.

Command: NOT RUN (no process-level stale-worker fixture exists)

Result: OPEN

Observed result: Implementation or fixture status only; the required acceptance result has not been recorded.

Source commit: 6b947b82c7b46c5b38471142f1958f4dc6083144.

Upstream: published ETLantic 0.56.0 wheels.

Environment: macOS 26.6.2 arm64, CPython 3.13.9, uv 0.11.3; no local PostgreSQL URL; no hosted run for this revision.

Artifact: docs/evidence/0.6/contracts.md; implementation/test reference: stale fencing.

Provenance: docs/plans/PHASE_0_6_EXECUTION.md#acceptance-criteria.

Limitation: No stale worker completion has been rejected after ownership or fencing-token change in this runtime.

## AC-018

Requirement: Cancellation in accepted, leased, and running states maps to upstream outcomes; inability to interrupt an external effect is reported without fabricated completion.

Command: NOT RUN (no live cancellation fixture exists)

Result: OPEN

Observed result: Implementation or fixture status only; the required acceptance result has not been recorded.

Source commit: 6b947b82c7b46c5b38471142f1958f4dc6083144.

Upstream: published ETLantic 0.56.0 wheels.

Environment: macOS 26.6.2 arm64, CPython 3.13.9, uv 0.11.3; no local PostgreSQL URL; no hosted run for this revision.

Artifact: docs/evidence/0.6/contracts.md; implementation/test reference: cancellation outcomes.

Provenance: docs/plans/PHASE_0_6_EXECUTION.md#acceptance-criteria.

Limitation: Accepted, leased, and running cancellation outcomes and uncertain effects have not been exercised.

## AC-019

Requirement: Database disconnect and reconnect fail readiness and work admission/claim safely, then recover through upstream state without memory or file fallback.

Command: NOT RUN (no runtime disconnect/reconnect fixture exists)

Result: OPEN

Observed result: Implementation or fixture status only; the required acceptance result has not been recorded.

Source commit: 6b947b82c7b46c5b38471142f1958f4dc6083144.

Upstream: published ETLantic 0.56.0 wheels.

Environment: macOS 26.6.2 arm64, CPython 3.13.9, uv 0.11.3; no local PostgreSQL URL; no hosted run for this revision.

Artifact: docs/evidence/0.6/contracts.md; implementation/test reference: database outage recovery.

Provenance: docs/plans/PHASE_0_6_EXECUTION.md#acceptance-criteria.

Limitation: Readiness recovery and upstream work resumption after database restoration have not been demonstrated.

## AC-020

Requirement: A representative real ETL fixture performs an observable, idempotency-keyed sink effect in a worker while both gateways remain responsive.

Command: uv run python scripts/check_clean_wheel.py

Result: OPEN

Observed result: Historical hosted 0.56.0 qualification exercised two distinct gateway ASGI runtimes while a worker executed the PostgreSQL sink write; the 0.56.2 run is pending.

Source commit: 625a7b3f38e35fef2124accdfd0eba3dc0d6c847.

Upstream: published ETLantic 0.56.0 wheels.

Environment: GitHub Actions Ubuntu 24.04, CPython 3.11–3.13, uv 0.11.3, PostgreSQL 18.6; isolated installed-wheel qualification fixture.

Artifact: docs/evidence/0.6/contracts.md; implementation/test reference: tests/integration/test_postgresql.py::test_preview_runtime_executes_manual_and_scheduled_postgresql_work.

Provenance: docs/plans/PHASE_0_6_EXECUTION.md#acceptance-criteria.

Limitation: Historical 0.56.0 sink evidence used in-process TestClient instances; 0.56.2 installed-wheel execution on hosted PostgreSQL is pending.

## AC-021

Requirement: Request credentials and resolved secrets are absent from durable payloads, reports, events, errors, logs, doctor, and health output; execution credentials are resolved only inside the worker boundary.

Command: uv run python scripts/check_clean_wheel.py

Result: OPEN

Observed result: Implementation or fixture status only; the required acceptance result has not been recorded.

Source commit: 6b947b82c7b46c5b38471142f1958f4dc6083144.

Upstream: published ETLantic 0.56.0 wheels.

Environment: macOS 26.6.2 arm64, CPython 3.13.9, uv 0.11.3; no local PostgreSQL URL; no hosted run for this revision.

Artifact: docs/evidence/0.6/contracts.md; implementation/test reference: credential and secret redaction.

Provenance: docs/plans/PHASE_0_6_EXECUTION.md#acceptance-criteria.

Limitation: The CLI mismatch smoke checks URL redaction; durable payload, report, event, log, and worker-secret boundaries are not comprehensively tested.

## AC-022

Requirement: Container and ordinary supervisor examples use the same digest-pinned artifact, separate processes, one PostgreSQL service, and no broker; startup and shutdown commands are reproducible.

Command: NOT RUN (Compose and systemd services have not been rehearsed)

Result: OPEN

Observed result: Implementation or fixture status only; the required acceptance result has not been recorded.

Source commit: 6b947b82c7b46c5b38471142f1958f4dc6083144.

Upstream: published ETLantic 0.56.0 wheels.

Environment: macOS 26.6.2 arm64, CPython 3.13.9, uv 0.11.3; no local PostgreSQL URL; no hosted run for this revision.

Artifact: docs/evidence/0.6/contracts.md; implementation/test reference: deployment recipes.

Provenance: docs/plans/PHASE_0_6_EXECUTION.md#acceptance-criteria.

Limitation: Compose and systemd examples are present; digest identity, ordinary supervisor startup, and shutdown have not been rehearsed.

## AC-023

Requirement: The release gate and hosted Python 3.11–3.13 matrix run real PostgreSQL, subprocess failure injection, clean-wheel role smoke checks, artifact/OpenAPI/boundary checks, and reject skipped required cases.

Command: Pending current 0.56.2 GitHub Actions run

Result: OPEN

Observed result: Historical run 37668515171 passed the matrix for the earlier 0.56.0 implementation; current 0.56.2 run pending.

Source commit: 3b27a55f28c9c4671a8eb7f057a81ac775d5420c.

Upstream: published ETLantic 0.56.0 wheels.

Environment: GitHub Actions ubuntu-24.04, PostgreSQL 18.6, Python 3.11–3.13, uv 0.11.3; hosted PR run 37668515171.

Artifact: docs/evidence/0.6/contracts.md; implementation/test reference: hosted release matrix.

Provenance: docs/plans/PHASE_0_6_EXECUTION.md#acceptance-criteria.

Limitation: Historical 0.56.0 matrix passed, but the current source revision has not run in hosted CI.

## AC-024

Requirement: A Phase 0.6 evidence ledger maps every AC to an exact command, observed result, source commit, upstream version, environment, artifact, and limitation.

Command: uv run python scripts/check_evidence.py --evidence docs/evidence/0.6

Result: PASS

Observed result: The evidence checker validates the record and references.

Source commit: 6b947b82c7b46c5b38471142f1958f4dc6083144.

Upstream: published ETLantic 0.56.0 wheels.

Environment: macOS 26.6.2 arm64, CPython 3.13.9, uv 0.11.3; no local PostgreSQL URL; no hosted run for this revision.

Artifact: docs/evidence/0.6/contracts.md; implementation/test reference: criterion evidence ledger.

Provenance: docs/plans/PHASE_0_6_EXECUTION.md#acceptance-criteria.

Limitation: This check validates ledger structure and references only; it does not establish the underlying runtime acceptance results.

## AC-025

Requirement: The reference deployment provisions a fresh 0.56 store, rejects use of the 0.55 store, documents re-enrollment and reconciliation of unfinished work, and demonstrates rollback to the retained 0.5 application/store without concurrent trigger authority or automatic replay of uncertain effects.

Command: NOT RUN (no migration or rollback rehearsal exists)

Result: OPEN

Observed result: Implementation or fixture status only; the required acceptance result has not been recorded.

Source commit: 6b947b82c7b46c5b38471142f1958f4dc6083144.

Upstream: published ETLantic 0.56.0 wheels.

Environment: macOS 26.6.2 arm64, CPython 3.13.9, uv 0.11.3; no local PostgreSQL URL; no hosted run for this revision.

Artifact: docs/evidence/0.6/contracts.md; implementation/test reference: fresh-store cutover and rollback.

Provenance: docs/plans/PHASE_0_6_EXECUTION.md#acceptance-criteria.

Limitation: The handoff sequence is documented; live re-enrollment, reconciliation, sole-authority rollback, and no-replay behavior remain untested.

## AC-026

Requirement: The trusted factory receives validated settings and returns only typed host bindings. ShuETL constructs the managed graph, scheduler callback and execution host; malformed bindings, wrong scope, demo identity and invalid role-specific fields fail with redacted diagnostics.

Command: uv run pytest tests/unit/test_phase_0_6_runtime.py -q

Result: OPEN

Observed result: Implementation or fixture status only; the required acceptance result has not been recorded.

Source commit: 6b947b82c7b46c5b38471142f1958f4dc6083144.

Upstream: published ETLantic 0.56.0 wheels.

Environment: macOS 26.6.2 arm64, CPython 3.13.9, uv 0.11.3; no local PostgreSQL URL; no hosted run for this revision.

Artifact: docs/evidence/0.6/contracts.md; implementation/test reference: trusted factory and typed bindings.

Provenance: docs/plans/PHASE_0_6_EXECUTION.md#acceptance-criteria.

Limitation: Core binding and scope checks are unit-tested; full malformed-factory, redaction, and installed-role matrix is open.

## AC-027

Requirement: An independently installed reference host changes canonical source/destination/transform/quality/schedule specifications and executes real manual/scheduled ETL without constructing stores, implementing connectors or supplying runtime callbacks. Headless and HTTP paths preserve canonical identities and outcomes.

Command: uv run python scripts/check_clean_wheel.py

Result: OPEN

Observed result: Implementation or fixture status only; the required acceptance result has not been recorded.

Source commit: 6b947b82c7b46c5b38471142f1958f4dc6083144.

Upstream: published ETLantic 0.56.0 wheels.

Environment: macOS 26.6.2 arm64, CPython 3.13.9, uv 0.11.3; no local PostgreSQL URL; no hosted run for this revision.

Artifact: docs/evidence/0.6/contracts.md; implementation/test reference: independent reference host.

Provenance: docs/plans/PHASE_0_6_EXECUTION.md#acceptance-criteria.

Limitation: The transfer fixture covers manual/scheduled API shape; independent host specifications, transformations, quality, and headless parity are not qualified.

## AC-028

Requirement: Every advertised provider pairing/write mode has live source/sink evidence, enabled-writer policy, alias/upsert-key and schema-drift cases. The minimum CSV/PostgreSQL-to-PostgreSQL fixture proves select/drop/rename, casts, filters, scalar expressions, deterministic deduplication and schema/required/range/set quality rules, including failing quality without a falsely successful publication.

Command: NOT RUN (provider-pairing and quality matrix fixture is absent)

Result: OPEN

Observed result: Implementation or fixture status only; the required acceptance result has not been recorded.

Source commit: 6b947b82c7b46c5b38471142f1958f4dc6083144.

Upstream: published ETLantic 0.56.0 wheels.

Environment: macOS 26.6.2 arm64, CPython 3.13.9, uv 0.11.3; no local PostgreSQL URL; no hosted run for this revision.

Artifact: docs/evidence/0.6/contracts.md; implementation/test reference: provider and transformation matrix.

Provenance: docs/plans/PHASE_0_6_EXECUTION.md#acceptance-criteria.

Limitation: Only the PostgreSQL upsert fixture is configured; CSV, transforms, quality failures, and other advertised write modes remain unsupported or unqualified.

## AC-029

Requirement: Canonical schema/control discovery, complete option round trips and per-run effective configuration agree with live behavior. Missing provider/policy/authorization/state requirements produce upstream diagnostics; supported controls are accessible without a ShuETL-only restriction.

Command: NOT RUN (live discovery and option-round-trip fixture is absent)

Result: OPEN

Observed result: Implementation or fixture status only; the required acceptance result has not been recorded.

Source commit: 6b947b82c7b46c5b38471142f1958f4dc6083144.

Upstream: published ETLantic 0.56.0 wheels.

Environment: macOS 26.6.2 arm64, CPython 3.13.9, uv 0.11.3; no local PostgreSQL URL; no hosted run for this revision.

Artifact: docs/evidence/0.6/contracts.md; implementation/test reference: canonical discovery and controls.

Provenance: docs/plans/PHASE_0_6_EXECUTION.md#acceptance-criteria.

Limitation: Schema/control discovery and effective per-run options have no ShuETL live evidence.

## AC-030

Requirement: Live failed-work retry and deliberate new-run commands preserve upstream attempt/run/lineage identities and admission policy. An independently packaged example extension executes without host ETL code or ShuETL core changes.

Command: NOT RUN (retry/rerun and independent-extension fixture is absent)

Result: OPEN

Observed result: Implementation or fixture status only; the required acceptance result has not been recorded.

Source commit: 6b947b82c7b46c5b38471142f1958f4dc6083144.

Upstream: published ETLantic 0.56.0 wheels.

Environment: macOS 26.6.2 arm64, CPython 3.13.9, uv 0.11.3; no local PostgreSQL URL; no hosted run for this revision.

Artifact: docs/evidence/0.6/contracts.md; implementation/test reference: retry, rerun, and extension.

Provenance: docs/plans/PHASE_0_6_EXECUTION.md#acceptance-criteria.

Limitation: No live retry/rerun identity proof or independently installed example extension is included.

## AC-031

Requirement: Advertised file-input/report-artifact support proves immutable checksums, owner/version access, changed/missing/expired input, retry retention, cross-worker availability and bounded cleanup; gateway artifact delivery does not expose runtime credentials or arbitrary filesystem paths.

Command: NOT RUN (cross-worker resource lifecycle fixture is absent)

Result: OPEN

Observed result: Implementation or fixture status only; the required acceptance result has not been recorded.

Source commit: 6b947b82c7b46c5b38471142f1958f4dc6083144.

Upstream: published ETLantic 0.56.0 wheels.

Environment: macOS 26.6.2 arm64, CPython 3.13.9, uv 0.11.3; no local PostgreSQL URL; no hosted run for this revision.

Artifact: docs/evidence/0.6/contracts.md; implementation/test reference: immutable input and report artifacts.

Provenance: docs/plans/PHASE_0_6_EXECUTION.md#acceptance-criteria.

Limitation: Checksum, owner/version access, expiry, retry retention, cross-worker availability, and bounded cleanup are not qualified.

## AC-032

Requirement: Runtime probe state remains accurate during active execution, idle/standby, outage, recovery and drain; stale inspection fails readiness. Probe output, upstream runtime logs and exception handling pass seeded-secret redaction checks without hiding process failure.

Command: uv run pytest tests/unit/test_phase_0_6_runtime.py::test_probe_lifecycle_reports_outage_drain_and_stale_state_without_secrets -q

Result: OPEN

Observed result: Implementation or fixture status only; the required acceptance result has not been recorded.

Source commit: 6b947b82c7b46c5b38471142f1958f4dc6083144.

Upstream: published ETLantic 0.56.0 wheels.

Environment: macOS 26.6.2 arm64, CPython 3.13.9, uv 0.11.3; no local PostgreSQL URL; no hosted run for this revision.

Artifact: docs/evidence/0.6/contracts.md; implementation/test reference: runtime probe and log safety.

Provenance: docs/plans/PHASE_0_6_EXECUTION.md#acceptance-criteria.

Limitation: Probe state and bounded reasons are unit-tested; live execution, idle, outage, drain, and seeded-secret log checks are not captured.

## AC-033

Requirement: Dedicated action workers perform live connection/catalog/schema/preflight operations through public upstream jobs without gateway secret resolution. Scope, resource rotation/revocation, deadline, outage and stale-preflight cases preserve canonical action results. Advertised sample preview is bounded/read-only with cleanup; provisioning requires separate explicit mutation authorization and qualification.

Command: uv run pytest tests/unit/test_phase_0_6_runtime.py::test_action_worker_requires_external_handlers_and_uses_upstream_host -q

Result: OPEN

Observed result: Implementation or fixture status only; the required acceptance result has not been recorded.

Source commit: 6b947b82c7b46c5b38471142f1958f4dc6083144.

Upstream: published ETLantic 0.56.0 wheels.

Environment: macOS 26.6.2 arm64, CPython 3.13.9, uv 0.11.3; no local PostgreSQL URL; no hosted run for this revision.

Artifact: docs/evidence/0.6/contracts.md; implementation/test reference: provider action workers.

Provenance: docs/plans/PHASE_0_6_EXECUTION.md#acceptance-criteria.

Limitation: Host selection is unit-tested; live catalog, schema, preflight, preview, provisioning, revocation, and deadline cases remain open.
