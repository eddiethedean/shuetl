# Phase 0.4 audited qualification record

Authority: `docs/plans/PHASE_0_4_EXECUTION.md#acceptance-criteria`.
The reviewed `proofs.json` bindings identify specific verification/provenance,
not keywords inferred from Task labels. Registry edits require semantic review.
A consistency checker cannot decide whether arbitrary tests prove a requirement.

Manual results are attributed to the independent Sol reviews dated 2026-09-13;
they were NOT all rerun during this remediation. Procedures below reconstruct
the assessable observations recorded there, not recovered scripts or invented
new execution logs. Actual local environment: macOS arm64, Python 3.12.13,
uv 0.11.3, installed locked 0.52.0 providers, disposable PostgreSQL 18.6.

## Published 0.52.1 patch-train requalification

The original procedures below retain their historical provenance. The user
authorized a corrected 0.52.1 train for FINAL-001/002 without changing provider
ownership, migration heads or the AC IDs. On 2026-09-13, locked PyPI core,
FastAPI and SQLModel 0.52.1 packages were reinstalled; none retained a local-wheel
direct URL. See [remediation report](../../plans/PHASE_0_4_FINAL_BLOCKER_REMEDIATION.md#published-train-qualification-and-gates).

| Requirement | Newly executed proof | Result |
| --- | --- | --- |
| AC-005 | Seven byte-URL cases plus protected SOL-001 string-error test; both error text and JSON | 8 passed |
| AC-002/011/015/027 | `uv run pytest tests/integration/test_postgresql.py -q`; fresh public migrations, actual server 18.6, inventory and doctor | PASS |
| AC-024/025 | Same live suite's two-workspace claim with real leader leases, durable store, canonical IDs, one outbox per scope and restart duplicates | PASS |
| AC-023/038 | Same live suite's concurrent event appends and unique persistent sequences | PASS |
| AC-016/037 | Separately reset disposable schema at each of four earlier heads; public registry seed, public upgrade, unchanged canonical logical/revision records, full inventory, repeat upgrade | Four heads passed |

The complete live suite returned 4 passed with no skips. The earlier-head probe
does not claim to cover every possible persisted record type. It preserves the
approved canonical definition/revision upgrade proof. No local DDL, semantic
wrapper or upstream monkey patch was used.
Newly executed current-change Actions evidence for Python 3.11/3.12/3.13 is
recorded separately in `ci.md`; it does not imply that all historical manual
probes were rerun on each interpreter.

PASS means the referenced check/observation within its limitation, NOT release
approval. AC-033 now has passing live CI evidence at the explicitly recorded
source commit. Automated PostgreSQL commands require a disposable
SHUETL_DATABASE_URL and explicit SHUETL_POSTGRESQL_SSLMODE; a skip is not proof.

## AC-001

Requirement: Project and wheel metadata report `0.4.0`, Python 3.11–3.13, the exact qualified core train, and exact PostgreSQL extra including Psycopg 3.3.5 binary.

Verification: `uv run python scripts/check_artifact.py`

Procedure and evidence: Run deterministic artifact metadata checks and installed-wheel dependency comparisons: 0.4.0, Python classifiers, exact core and PostgreSQL pins.

Provenance: [Independent Sol record](../../../tests/review/PHASE_0_4_REVIEW.md#acceptance-criteria) — AC-001, 2026-09-13.

Result: PASS for the referenced check/observation. Limitation: local Python 3.12; see qualification record.

## AC-002

Requirement: PostgreSQL 18.6 is the only claimed server and the executed server version is recorded in CI/evidence.

Verification: `uv run pytest tests/integration/test_postgresql.py::test_schema_head_graph_and_doctor -q`

Procedure and evidence: Live schema integration asserts inspect_postgresql server_version == '18.6', head and doctor server output. Without a disposable database URL this skips and is NOT executed server proof.

Provenance: [Independent Sol record](../../../tests/review/PHASE_0_4_REVIEW.md#acceptance-criteria) — AC-002, 2026-09-13.

Result: PASS for the referenced check/observation. Limitation: local Python 3.12; see qualification record.

## AC-003

Requirement: All 0.3 public exports remain and source/wheel expose exactly the added `PostgreSQLProviderBundle`.

Verification: `uv run pytest tests/unit/test_package.py -q`

Procedure and evidence: Package surface assertions check __all__ and no new domain exports; isolated wheel gate locates public imports in installed site-packages.

Provenance: [Independent Sol record](../../../tests/review/PHASE_0_4_REVIEW.md#acceptance-criteria) — AC-003, 2026-09-13.

Result: PASS for the referenced check/observation. Limitation: local Python 3.12; see qualification record.

## AC-004

Requirement: Settings accept exactly the three documented profile/provider combinations and never select PostgreSQL implicitly.

Verification: `Recorded review: tests/review/PHASE_0_4_REVIEW.md#acceptance-criteria (AC-004, 2026-09-13)`

Procedure and evidence: Inspect ShuETLSettings.validate_provider_url and the role Literal: local/gateway/memory, local/gateway/sqlite, postgresql-pilot/gateway/postgresql exhaust the allowed combinations; identity is always host. Required fields have no implicit PostgreSQL defaults. Original Sol inspected this and existing validation tests.

Provenance: [Independent Sol record](../../../tests/review/PHASE_0_4_REVIEW.md#acceptance-criteria) — AC-004, 2026-09-13.

Result: PASS for the referenced check/observation. Limitation: prior independent review; not rerun in remediation.

## AC-005

Requirement: PostgreSQL URLs and TLS mode validate exactly as specified; invalid or secret-bearing errors contain no connection value or coordinate.

Verification: `Recorded review: tests/review/PHASE_0_4_REVIEW.md#acceptance-criteria (AC-005, 2026-09-13)`

Procedure and evidence: Trace structural URL validation, conversion to SecretStr before errors, exact psycopg scheme/user/host/database, prohibited query/fragment, bounded timeout, TLS enum and verify-full default. Original Sol inspected PostgreSQL validation; old SQLite/redaction tests alone are not this proof.

Provenance: [Independent Sol record](../../../tests/review/PHASE_0_4_REVIEW.md#acceptance-criteria) — AC-005, 2026-09-13.

Result: PASS for the referenced check/observation. Limitation: prior independent review; not rerun in remediation.

## AC-006

Requirement: Exact core/PostgreSQL versions are validated before optional imports or engine construction; missing/mismatched extras fail with the documented remediation and no fallback.

Verification: `Recorded review: tests/review/PHASE_0_4_REVIEW.md#acceptance-criteria (AC-006, 2026-09-13)`

Procedure and evidence: Trace exact metadata validation before optional PostgreSQL imports and engine construction. Missing/mixed extras raise bounded CapabilityError with documented remediation and no fallback. Original Sol recorded this code-inspection proof.

Provenance: [Independent Sol record](../../../tests/review/PHASE_0_4_REVIEW.md#acceptance-criteria) — AC-006, 2026-09-13.

Result: PASS for the referenced check/observation. Limitation: prior independent review; not rerun in remediation.

## AC-007

Requirement: Bundle construction requires the exact pilot settings and explicit conforming host authorizer, context factory, and principal dependency.

Verification: `Recorded review: tests/review/PHASE_0_4_REVIEW.md#acceptance-criteria (AC-007, 2026-09-13)`

Procedure and evidence: Inspect exact pilot settings and explicit conforming authorizer/context/principal validation before graph construction. Original Sol recorded inspection plus adapter tests.

Provenance: [Independent Sol record](../../../tests/review/PHASE_0_4_REVIEW.md#acceptance-criteria) — AC-007, 2026-09-13.

Result: PASS for the referenced check/observation. Limitation: prior independent review; not rerun in remediation.

## AC-008

Requirement: A qualified bundle contains exact upstream registry, registry-backed definition, submission, event, durable-work, schedule, and API objects over one engine.

Verification: `uv run pytest tests/review/test_phase_0_4_contract.py::test_sol_011_bundle_definitions_are_the_api_definitions -q`

Procedure and evidence: Protected SOL-011 uses genuine upstream graph types and asserts bundle.definitions is bundle.api.definitions. Inspect native registry/submission/events/durable/schedules sharing one engine; second Sol re-review recorded live construction and identity PASS.

Provenance: [Independent Sol record](../../../tests/review/PHASE_0_4_RE_REVIEW_2.md#acceptance-criteria) — AC-008, 2026-09-13.

Result: PASS for the referenced check/observation. Limitation: local Python 3.12; see qualification record.

## AC-009

Requirement: The API retains caller objects, uses upstream production profile, and exposes registry/durable/schedule providers without adding report/artifact/governance/execution providers.

Verification: `Recorded review: tests/review/PHASE_0_4_RE_REVIEW_2.md#acceptance-criteria (AC-009, 2026-09-13)`

Procedure and evidence: Inspect direct ETLanticAPI production-profile composition and retained caller/engine/store identities. SOL-011 now guards duplicated definitions. Second review records caller objects retained with no report/artifact/governance/execution providers.

Provenance: [Independent Sol record](../../../tests/review/PHASE_0_4_RE_REVIEW_2.md#acceptance-criteria) — AC-009, 2026-09-13.

Result: PASS for the referenced check/observation. Limitation: prior independent review; not rerun in remediation.

## AC-010

Requirement: Fresh, behind, unknown/ahead, corrupt, wrong-server, and unreachable databases produce the documented redacted readiness failures and no bundle.

Verification: `Recorded review: tests/review/PHASE_0_4_REVIEW.md#acceptance-criteria (AC-010, 2026-09-13)`

Procedure and evidence: Original Sol probed real fresh, behind, unknown-version and missing-head-table states and required bounded failure/no bundle. It inspected wrong-server/unreachable branches; those two branches are NOT claimed as newly executed probes.

Provenance: [Independent Sol record](../../../tests/review/PHASE_0_4_REVIEW.md#acceptance-criteria) — AC-010, 2026-09-13.

Result: PASS for the referenced check/observation. Limitation: prior independent review; not rerun in remediation.

## AC-011

Requirement: Exact head plus every required provider table is necessary and sufficient for database readiness.

Verification: `uv run pytest tests/integration/test_postgresql.py::test_schema_head_graph_and_doctor -q`

Procedure and evidence: Live test asserts exact head and required inventory. Original Sol additionally demonstrated missing-table-at-head rejection; inspect that extra tables are allowed but every minimum table is required.

Provenance: [Independent Sol record](../../../tests/review/PHASE_0_4_REVIEW.md#acceptance-criteria) — AC-011, 2026-09-13.

Result: PASS for the referenced check/observation. Limitation: local Python 3.12; see qualification record.

## AC-012

Requirement: Bundle construction, doctor, gateway startup, mount, app factory, and lifespan perform zero schema/table/version writes and invoke no migration/create-all API.

Verification: `Recorded review: tests/review/PHASE_0_4_REVIEW.md#acceptance-criteria (AC-012, 2026-09-13)`

Procedure and evidence: Original procedure: snapshot fresh PostgreSQL public catalog, invoke doctor/bundle inspection, compare catalog unchanged. Original Sol recorded PASS and inspected fixed read-only transaction plus unchanged app/mount/lifespan paths invoking neither upgrade nor create_all. A SQLite test is not the selected proof.

Provenance: [Independent Sol record](../../../tests/review/PHASE_0_4_REVIEW.md#acceptance-criteria) — AC-012, 2026-09-13.

Result: PASS for the referenced check/observation. Limitation: prior independent review; not rerun in remediation.

## AC-013

Requirement: Every construction failure disposes its engine once; successful bundle close is thread-safe, explicit, and idempotent.

Verification: `uv run pytest tests/review/test_phase_0_4_contract.py::test_sol_014_cancelled_construction_disposes_engine_once -q`

Procedure and evidence: Protected cancellation test injects CancelledError after engine creation, requires unchanged propagation and exactly one dispose. Second review inspected BaseException cleanup and lock-protected idempotent close for ordinary failure and successful lifecycle.

Provenance: [Independent Sol record](../../../tests/review/PHASE_0_4_RE_REVIEW_2.md#acceptance-criteria) — AC-013, 2026-09-13.

Result: PASS for the referenced check/observation. Limitation: local Python 3.12; see qualification record.

## AC-014

Requirement: `shuetl database upgrade` alone performs provider migrations with exact stdout/stderr and exit 0/1/2 behavior.

Verification: `Recorded review: tests/review/PHASE_0_4_REVIEW.md#acceptance-criteria (AC-014, 2026-09-13)`

Procedure and evidence: Original Sol inspected CLI parsing/output/error flow and exercised upgrade_postgresql on real PostgreSQL. Trace main -> upgrade_postgresql -> pinned public upgrade; stdout head/exit 0, redacted stderr/exit 1 and usage exit 2. The current CLI directly calls upgrade_postgresql; this path was checked against src/shuetl/cli.py during remediation. Runtime results remain attributed to the original review, not to the old review suite invoking database upgrade.

Provenance: [Independent Sol record](../../../tests/review/PHASE_0_4_REVIEW.md#acceptance-criteria) — AC-014, 2026-09-13.

Result: PASS for the referenced check/observation. Limitation: prior independent review; not rerun in remediation.

## AC-015

Requirement: Fresh PostgreSQL upgrades to the qualified head solely through the public provider migration API and has every required table/constraint.

Verification: `uv run pytest tests/integration/test_postgresql.py::test_schema_head_graph_and_doctor -q`

Procedure and evidence: Live fresh fixture calls public etlantic_sqlmodel.migrations.upgrade and checks qualified inventory/head. Original Sol inspected pinned provider constraints; inferred demo DDL is not accepted.

Provenance: [Independent Sol record](../../../tests/review/PHASE_0_4_REVIEW.md#acceptance-criteria) — AC-015, 2026-09-13.

Result: PASS for the referenced check/observation. Limitation: local Python 3.12; see qualification record.

## AC-016

Requirement: Every recognized earlier provider head upgrades to the qualified head without losing seeded canonical data.

Verification: `Recorded review: tests/review/PHASE_0_4_REVIEW.md#acceptance-criteria (AC-016, 2026-09-13)`

Procedure and evidence: Original procedure: seed canonical registry definition/revision at each of 001_registry_cp2, 002_durable_cp3, 003_cp4_governance and 004_schedules_0_47, capture data/IDs, run upgrade_postgresql, compare unchanged at 005_cp1_reference. Original Sol recorded all four passing. These identifiers were checked against the installed 0.52.0 etlantic_sqlmodel.migrations.VERSIONS during remediation; the prior runtime probes were not rerun. Fresh-schema three-test suite does not prove earlier-head upgrades.

Provenance: [Independent Sol record](../../../tests/review/PHASE_0_4_REVIEW.md#acceptance-criteria) — AC-016, 2026-09-13.

Result: PASS for the referenced check/observation. Limitation: prior independent review; not rerun in remediation.

## AC-017

Requirement: Repeating upgrade at head is a successful no-op; unknown/ahead/corrupt state is never downgraded, reset, repaired, or overwritten.

Verification: `Recorded review: tests/review/PHASE_0_4_REVIEW.md#acceptance-criteria (AC-017, 2026-09-13)`

Procedure and evidence: Original procedure: repeat upgrade at head, require successful no-op; supply unknown version and require rejection without mutation. Original Sol recorded both passing and inspected corrupt-state rejection. No executed corrupt-migration probe is claimed.

Provenance: [Independent Sol record](../../../tests/review/PHASE_0_4_REVIEW.md#acceptance-criteria) — AC-017, 2026-09-13.

Result: PASS for the referenced check/observation. Limitation: prior independent review; not rerun in remediation.

## AC-018

Requirement: A registry-backed definition and at least two immutable revisions remain readable with the same logical/revision IDs after engine and gateway restart.

Verification: `Recorded review: tests/review/PHASE_0_4_REVIEW.md#acceptance-criteria (AC-018, 2026-09-13)`

Procedure and evidence: Original procedure: create registry definition and two distinct immutable revisions, capture logical/revision IDs and contents, explicitly close gateway/bundle/engine, reopen a new graph and compare both records unchanged. Original Sol recorded equality PASS; ordinary restart test alone lacks two revisions.

Provenance: [Independent Sol record](../../../tests/review/PHASE_0_4_REVIEW.md#acceptance-criteria) — AC-018, 2026-09-13.

Result: PASS for the referenced check/observation. Limitation: prior independent review; not rerun in remediation.

## AC-019

Requirement: A committed CP1 submission remains readable after restart and preserves acceptance, submission, run, and definition identities.

Verification: `Recorded review: tests/review/PHASE_0_4_REVIEW.md#acceptance-criteria (AC-019, 2026-09-13)`

Procedure and evidence: Original procedure: commit CP1 submission, capture full canonical acceptance/submission/run/definition receipt identities, close gateway/engine, reopen/read and compare full receipt. Original Sol recorded equality PASS and inspected persisted receipt/payload mapping.

Provenance: [Independent Sol record](../../../tests/review/PHASE_0_4_REVIEW.md#acceptance-criteria) — AC-019, 2026-09-13.

Result: PASS for the referenced check/observation. Limitation: prior independent review; not rerun in remediation.

## AC-020

Requirement: Same-scope same-key same-payload submission before/after restart returns one canonical upstream outcome; changed payload returns upstream conflict.

Verification: `Recorded review: tests/review/PHASE_0_4_REVIEW.md#acceptance-criteria (AC-020, 2026-09-13)`

Procedure and evidence: Original procedure: accept same-scope/key/payload, close/reopen, accept again and require same canonical receipt; change payload with same key and require upstream 409. Original Sol recorded PASS. Pre-restart duplicate-only test is insufficient.

Provenance: [Independent Sol record](../../../tests/review/PHASE_0_4_REVIEW.md#acceptance-criteria) — AC-020, 2026-09-13.

Result: PASS for the referenced check/observation. Limitation: prior independent review; not rerun in remediation.

## AC-021

Requirement: Barrier-controlled concurrent same-key submissions through independent connections produce one durable canonical acceptance and no raw database exception.

Verification: `Recorded review: tests/review/PHASE_0_4_REVIEW.md#acceptance-criteria (AC-021, 2026-09-13)`

Procedure and evidence: Original procedure: eight workers with independent engines/submission stores in one scope synchronize same-key/payload calls at a barrier; collect outcomes and require one canonical receipt ID, exactly one created result, no raw database exception and durable acceptance. Original Sol recorded PASS. Process-local serialization or metadata tests cannot substitute.

Provenance: [Independent Sol record](../../../tests/review/PHASE_0_4_REVIEW.md#acceptance-criteria) — AC-021, 2026-09-13.

Result: PASS for the referenced check/observation. Limitation: prior independent review; not rerun in remediation.

## AC-022

Requirement: Events appended before restart replay from the beginning and a persisted cursor with the same IDs, sequences, order, payload, and scope.

Verification: `Recorded review: tests/review/PHASE_0_4_REVIEW.md#acceptance-criteria (AC-022, 2026-09-13)`

Procedure and evidence: Original procedure: capture complete scoped events and actual persisted upstream cursor, close/reopen engines, replay from beginning and after that cursor, compare IDs/sequences/order/payload/scope. Original Sol recorded PASS using real cursor, not event ID; scope filtering was inspected.

Provenance: [Independent Sol record](../../../tests/review/PHASE_0_4_REVIEW.md#acceptance-criteria) — AC-022, 2026-09-13.

Result: PASS for the referenced check/observation. Limitation: prior independent review; not rerun in remediation.

## AC-023

Requirement: Barrier-controlled concurrent same-scope event appends all persist with unique ordered sequences/cursors and expose no raw SQLAlchemy/Psycopg exception.

Verification: `uv run pytest tests/integration/test_postgresql.py::test_concurrent_event_appends_have_unique_sequences -q`

Procedure and evidence: Original procedure: eight barrier-synchronized independent engines append within one scope; collect all results and require unique ordered replay sequences/no driver errors. Original Sol recorded PASS. Fresh live concurrent-event test additionally checks persisted unique ordering.

Provenance: [Independent Sol record](../../../tests/review/PHASE_0_4_REVIEW.md#acceptance-criteria) — AC-023, 2026-09-13.

Result: PASS for the referenced check/observation. Limitation: local Python 3.12; see qualification record.

## AC-024

Requirement: A schedule and canonical firing created through upstream API/store behavior persist with the same identities after restart without a ShuETL scheduler loop.

Verification: `Recorded review: tests/review/PHASE_0_4_REVIEW.md#acceptance-criteria (AC-024, 2026-09-13)`

Procedure and evidence: Original procedure: create schedule and firing with durable-work store over shared engine, capture IDs, close/reopen/read and compare identities. Original Sol recorded PASS; existing live restart test separately covers schedule/firing persistence. No local scheduler loop.

Provenance: [Independent Sol record](../../../tests/review/PHASE_0_4_REVIEW.md#acceptance-criteria) — AC-024, 2026-09-13.

Result: PASS for the referenced check/observation. Limitation: prior independent review; not rerun in remediation.

## AC-025

Requirement: Duplicate schedule firing claim returns the canonical upstream firing and does not create a second durable submission.

Verification: `Recorded review: tests/review/PHASE_0_4_REVIEW.md#acceptance-criteria (AC-025, 2026-09-13)`

Procedure and evidence: Original procedure: claim identical scheduled occurrence twice with durable-work store supplied and compare canonical firing identities. Original Sol recorded PASS and inspected shared-engine atomic transaction plus existing-firing early return preventing another durable submission. Existing test lacking durable store is not proof.

Provenance: [Independent Sol record](../../../tests/review/PHASE_0_4_REVIEW.md#acceptance-criteria) — AC-025, 2026-09-13.

Result: PASS for the referenced check/observation. Limitation: prior independent review; not rerun in remediation.

## AC-026

Requirement: Mounted PostgreSQL endpoints preserve upstream authorization order, request/response schemas, statuses, errors, idempotency, SSE, operation IDs, and schema refs.

Verification: `uv run pytest tests/integration/test_phase_0_2_contract.py -q`

Procedure and evidence: Run HTTP authorization/schema/error/idempotency/SSE/OpenAPI contract suite. Original Sol also constructed real pilot OpenAPI and inspected identical upstream mount/router composition. Mocked HTTP tests alone are not persistence proof.

Provenance: [Independent Sol record](../../../tests/review/PHASE_0_4_REVIEW.md#acceptance-criteria) — AC-026, 2026-09-13.

Result: PASS for the referenced check/observation. Limitation: local Python 3.12; see qualification record.

## AC-027

Requirement: Doctor keeps `shuetl.doctor/1`, existing fields/check IDs/order, and reports truthful pilot capabilities, package/server versions, connection, schema, and non-development topology.

Verification: `uv run pytest tests/integration/test_postgresql.py::test_schema_head_graph_and_doctor -q`

Procedure and evidence: Live doctor assertions plus protected configured-capability/TLS tests establish pilot versions/capabilities. Second Sol inspected unchanged doctor/1 fields/check order and recorded live doctor PASS.

Provenance: [Independent Sol record](../../../tests/review/PHASE_0_4_RE_REVIEW_2.md#acceptance-criteria) — AC-027, 2026-09-13.

Result: PASS for the referenced check/observation. Limitation: local Python 3.12; see qualification record.

## AC-028

Requirement: Doctor text/JSON contain equivalent bounded facts and neither performs writes nor reveals credentials, coordinates, paths, TLS material, SQL, reprs, or raw exceptions.

Verification: `uv run pytest tests/review/test_phase_0_4_contract.py -q`

Procedure and evidence: Protected SOL-012 tests require equivalent visible TLS facts and truthful configured capabilities without missing-extra connection. Original/second reviews inspected bounded redacted rendering/read-only execution. Combine PostgreSQL SecretStr inspection (AC-005) and catalog probe (AC-012); no exhaustive fuzzing claim.

Provenance: [Independent Sol record](../../../tests/review/PHASE_0_4_RE_REVIEW_2.md#acceptance-criteria) — AC-028, 2026-09-13.

Result: PASS for the referenced check/observation. Limitation: local Python 3.12; see qualification record.

## AC-029

Requirement: Database backup/restore of provider-owned canonical tables preserves the AC-018 through AC-025 identities and passes readiness before traffic.

Verification: `Recorded review: tests/review/PHASE_0_4_RE_REVIEW_2.md#acceptance-criteria (AC-029, 2026-09-13)`

Procedure and evidence: Original consistent custom-format native dump/restore into isolated 18.6 passed readiness and every canonical row comparison. Second Sol repeated native libpq restore and sorted all-public-table JSON row snapshots: 17 tables, 26 rows equal, restored doctor exit 0. Exact row equality includes AC-018–025 persisted IDs. See native procedure below.

Provenance: [Independent Sol record](../../../tests/review/PHASE_0_4_RE_REVIEW_2.md#acceptance-criteria) — AC-029, 2026-09-13.

Result: PASS for the referenced check/observation. Limitation: prior independent review; not rerun in remediation.

## AC-030

Requirement: Existing memory, SQLite, caller-built API, mount, lifecycle, handler, OpenAPI, CLI, and doctor compatibility suites remain green.

Verification: `uv run pytest -q`

Procedure and evidence: Full compatibility suite preserves memory/SQLite/caller API/mount/lifecycle/handler/OpenAPI/CLI/doctor. Live PostgreSQL suite runs separately with disposable URL; its three skips in default full suite are not live integration proof.

Provenance: [Independent Sol record](../../../tests/review/PHASE_0_4_REVIEW.md#acceptance-criteria) — AC-030, 2026-09-13.

Result: PASS for the referenced check/observation. Limitation: local Python 3.12; see qualification record.

## AC-031

Requirement: Static boundaries find no ShuETL domain model, table, migration, store wrapper, route, scheduler, worker, executor, anonymous identity, or startup DDL.

Verification: `uv run python scripts/check_boundaries.py --openapi docs/evidence/0.4/openapi.normalized.json`

Procedure and evidence: Run static ownership scanner against normalized OpenAPI; original/second Sol also inspected upstream migration/provider ownership and unchanged routes. Scanner is a static boundary guard, not migration execution.

Provenance: [Independent Sol record](../../../tests/review/PHASE_0_4_REVIEW.md#acceptance-criteria) — AC-031, 2026-09-13.

Result: PASS for the referenced check/observation. Limitation: local Python 3.12; see qualification record.

## AC-032

Requirement: Core, SQLite, and PostgreSQL clean-wheel installs contain only their declared dependencies and all public imports resolve from the wheel.

Verification: `uv run python scripts/check_clean_wheel.py`

Procedure and evidence: After build, run separate isolated core, SQLite and PostgreSQL wheel installs, compare exact declared dependencies and public import origins. Workspace imports are not substituted.

Provenance: [Independent Sol record](../../../tests/review/PHASE_0_4_REVIEW.md#acceptance-criteria) — AC-032, 2026-09-13.

Result: PASS for the referenced check/observation. Limitation: local Python 3.12; see qualification record.

## AC-033

Requirement: Real PostgreSQL integration tests run in CI on Python 3.11, 3.12, and 3.13 using the exact locked server/driver/provider set.

Verification: `gh run view 34771524213 --json headSha,status,conclusion,jobs`

Procedure and evidence: GitHub Actions run 34771524213 tested current-change commit `114da1ab264088e487e7f216e7d1f14ee778f6aa` and completed successfully. All nine matrix jobs passed. Each real PostgreSQL job on Python 3.11/3.12/3.13 passed all three integration tests without skips, using `postgres:18.6-bookworm` and the committed exact locked provider/driver set. The schema/doctor test asserts actual server version 18.6. The primary run/job links, observed interpreter versions, commands and release-gate results are recorded in ci.md. This replaces configuration-only evidence; it is not an independent release verdict.

Provenance: [Completed CI execution](ci.md#qualified-runtime-matrix) — AC-033, 2026-09-13.

Result: PASS for the referenced check/observation. Limitation: qualifies recorded source revision; see ci.md for tested commit.

## AC-034

Requirement: Ruff, Pyright, boundary, unit, integration, migration, concurrency, build, artifact, OpenAPI, clean-wheel, redaction, and evidence gates pass.

Verification: `uv run python scripts/check_release.py`

Procedure and evidence: Run all check_release stages: lock/sync/format/lint/Pyright/boundaries/tests/build/artifact/OpenAPI/three isolated wheels/evidence-redaction. Refresh deterministic hashes after source changes. This local gate covers Python 3.12; separate live PostgreSQL qualification is recorded by Sol.

Provenance: [Independent Sol record](../../../tests/review/PHASE_0_4_REVIEW.md#acceptance-criteria) — AC-034, 2026-09-13.

Result: PASS for the referenced check/observation. Limitation: local Python 3.12 gate; live PostgreSQL qualified separately.

## AC-035

Requirement: Documentation states exact setup, TLS, privileges, migration, readiness, cleanup, backup/restore, canonical data, and pilot limitations and contains executable wheel-based examples.

Verification: `Recorded review: tests/review/PHASE_0_4_RE_REVIEW_2.md#acceptance-criteria (AC-035, 2026-09-13)`

Procedure and evidence: Read operator setup/TLS/privileges/migration/readiness/cleanup/backup/restore/canonical-data/pilot docs and wheel-based example. Protected SOL-013 checks restore/admission topics. Second Sol executed corrected native restore and compared rows before doctor PASS. Backup automation is not implemented.

Provenance: [Independent Sol record](../../../tests/review/PHASE_0_4_RE_REVIEW_2.md#acceptance-criteria) — AC-035, 2026-09-13.

Result: PASS for the referenced check/observation. Limitation: prior independent review; not rerun in remediation.

## AC-036

Requirement: The Phase 0.4 evidence index maps every AC exactly once to passing proof and contains no secret or machine-specific path.

Verification: `uv run python scripts/check_evidence.py --evidence docs/evidence/0.4`

Procedure and evidence: Run checker and protected SOL-010 tests, including tests/review/test_phase_0_4_manual_proof_contract.py::test_sol_010_recorded_upgrade_identifiers_are_real; audit every binding against approved requirement and recorded observations. Registry/reference consistency is independent of Task labels, rejects unrelated proof and checks redaction. The factual-proof test checks explicitly named revisions against the published provider and named CLI symbols against source. Green consistency checks are NOT independent release approval.

Provenance: [Independent Sol record](../../../tests/review/PHASE_0_4_REVIEW.md#acceptance-criteria) — AC-036, 2026-09-13.

Result: PASS for the referenced check/observation. Limitation: local Python 3.12; see qualification record.

## AC-037

Requirement: The qualified 0.52.1 provider train provisions submission/event tables through production migrations and upgrades preserve data.

Verification: `Recorded review: tests/review/PHASE_0_4_REVIEW.md#acceptance-criteria (AC-037, 2026-09-13)`

Procedure and evidence: Original Sol used installed published 0.52.0 production migrations, fresh inventory and all four seeded earlier-head upgrades with unchanged canonical data (AC-015/016). No copied local DDL or train assumption.

Provenance: [Independent Sol record](../../../tests/review/PHASE_0_4_REVIEW.md#acceptance-criteria) — AC-037, 2026-09-13.

Result: PASS for the referenced check/observation. Limitation: prior independent review; not rerun in remediation.

## AC-038

Requirement: The qualified 0.52.1 provider train provides a supported, tested concurrent event-append outcome meeting AC-023.

Verification: `uv run pytest tests/integration/test_postgresql.py::test_concurrent_event_appends_have_unique_sequences -q`

Procedure and evidence: Original Sol inspected installed 0.52.0 PostgreSQL advisory-lock allocator and independently barrier-tested event appends; live concurrent test repeats persistent unique ordering/no raw errors (AC-023). No ShuETL allocator.

Provenance: [Independent Sol record](../../../tests/review/PHASE_0_4_REVIEW.md#acceptance-criteria) — AC-038, 2026-09-13.

Result: PASS for the referenced check/observation. Limitation: local Python 3.12; see qualification record.

## Native restore procedure

Native tools require libpq `postgresql://` URLs; ShuETL requires a separate
`postgresql+psycopg://` input. Restore into an isolated empty database, never
onto a serving database. `disable` below is limited to the disposable service;
TLS deployments must consistently set verify-full and operator trust material.

```text
PGSSLMODE=disable pg_dump --format=custom --file=shuetl-0.4.backup "$PG_DUMP_DATABASE_URL"
PGSSLMODE=disable pg_restore --exit-on-error --dbname="$PG_RESTORE_DATABASE_URL" shuetl-0.4.backup
SHUETL_DATABASE_URL="$SHUETL_RESTORE_DATABASE_URL" shuetl doctor --format json
```

Before traffic compare sorted full-row JSON snapshots of every public canonical
table and migration version; reopen the restored gateway and compare definition
revisions, CP1 receipt IDs, event replay/persisted upstream cursor, schedules and
durable-backed firing identities. Restore, identity or readiness failure forbids
admission. Source result/provenance is AC-029 above (17 tables/26 rows in second
review). Credentials, TLS keys and external artifacts remain separate inputs.
