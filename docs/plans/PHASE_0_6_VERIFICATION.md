# Phase 0.6 — Verification and Evidence Plan

Status: Gate U and installed-artifact PostgreSQL Gate 0 PASS;
33 release criteria and Gates A–C remain OPEN. This document refines the
[execution contract](PHASE_0_6_EXECUTION.md) and
[accepted role implementation contract](../adr/0014-role-separated-managed-runtime.md).
Paths and commands below distinguish existing source checks from pending
qualification claims. Use exact published artifacts selected after Gate U,
PostgreSQL 18.6 and Python 3.11–3.13. Published 0.57.0 is accepted and pinned.
[Current evidence](../evidence/0.6/README.md) distinguishes contract acceptance
and role feasibility from final release qualification.
[ADR-0015](../adr/0015-backend-and-deployment-ownership.md) governs ownership.
The [implementation and release plan](PHASE_0_6_IMPLEMENTATION.md) orders the
work that produces this evidence; this document retains the verification matrix.

## Upstream contract gate and evidence ownership

| Gate | Upstream evidence required | ShuETL verification |
| --- | --- | --- |
| U01 / [#278](https://github.com/eddiethedean/etlantic/issues/278) | Neutral backend/provider graph, cleanup and canonical context contracts | Install headless backend without HTTP adapter; no Request, HTTP factory or principal dependency; gateway adapts same services. |
| U02 / [#279](https://github.com/eddiethedean/etlantic/issues/279) | Authorized schedule command conformance | HTTP/Python create/amend/pause/resume/preview/trigger/read/list/firing parity, denial, revision and identity tests. |
| U03 / [#280](https://github.com/eddiethedean/etlantic/issues/280) | Complete scheduler/store factory and explicit recovery integration | Construction and restart faults through selected public factory; no caller callback introspection. |
| U04 / [#281](https://github.com/eddiethedean/etlantic/issues/281) | Read-only provider compatibility/status including partial/corrupt schemas | No downstream table SQL; inspect/construct under runtime grants with no DDL/explicit commit; separate runtime DML proof. |
| U05 / [#282](https://github.com/eddiethedean/etlantic/issues/282) | Role-specific status/stop facts and lifecycle conformance | Process readiness/freshness/signals/cleanup through each role, including standby and active action work. |

All five surfaces pass [coverage acceptance](../evidence/0.6/coverage-acceptance.md).
Exact dependency pins are adopted; [PostgreSQL Gate 0](../evidence/0.6/README.md)
uses separately installed wheels and four independent processes. GitHub issues
remain administratively OPEN. No release AC is closed by these preparatory gates.

ETLantic/providers own exhaustive semantic conformance for connectors, transforms,
quality, resources, scheduling and recovery. ShuETL owns deployment configuration,
identity/HTTP adaptation, supervision and final-artifact integration evidence.
For AC-028–033 attach both upstream evidence and live ShuETL observations for each
advertised combination. Neither replaces the other; no required cases become skips.

## Reproducible fixtures

| Fixture | Required setup and observed result |
| --- | --- |
| F00 — package boundary | Isolated upstream headless installation without etlantic-fastapi; exact service/factory signatures; role bindings reject HTTP fields; standard ShuETL path imports no schema-table SQL or semantic callbacks. Provider inspection and service commands remain public upstream calls. |
| F01 — installed role graph | Disposable fresh database at the selected provider schema head, separate migration/runtime users, one explicit scope/store/profile, independently installed host bindings and built ShuETL wheel. One gateway, scheduler and worker complete both manual and scheduled real ETL. Record wheel hashes, import origins, grants and server version. |
| F02 — contention and faults | Expand F01 to two instances of each role with unique owners. A test-only independently installed harness supplies barriers at upstream public-call boundaries before/after durable accept, firing claim, managed submit/link, lease acquisition, effect and result publication. Kill/restart OS processes and observe canonical state without modifying production semantics. |
| F03 — live specification control | Immutable CSV and PostgreSQL sources, separate PostgreSQL sink schema, declared enabled write modes, independent connector packages and deterministic rows. Change only canonical specifications to exercise transforms/quality, typed overrides, revision selection and manual/native/external trigger identity. Verify source/sink values and canonical reports/events/lineage. |
| F04 — resources and isolation | Worker-only resource credentials with seeded sentinels; shared immutable input/report volume; changed/missing/expired/checksum-mismatched resources, cross-owner requests, worker replacement and cleanup. Gateway may enroll/read authorized resource metadata but cannot resolve runtime secrets or execute data access. |
| F05 — lifecycle and health | Idle/standby, long active tick, provider outage/recovery, stale probe evidence, invalid scope/adapter, SIGTERM/SIGINT, repeated shutdown and grace expiry. Queue a second work item to prove no new tick dispatch after drain; preserve the explicitly documented in-flight window. |
| F06 — transition | Retained 0.5 application/store plus separate fresh store for the selected upstream schema. Seed pending and uncertain-effect work, disable old admissions/schedules, re-enroll via public APIs, reconcile effects, enable new deployment, then rehearse rollback with only one trigger authority. No cross-store auto-replay. |
| F07 — isolated provider actions | Dedicated `worker --kind actions` processes with live PostgreSQL/CSV backend handlers. Gateway submits canonical connection/catalog/schema/preflight jobs; workers resolve resources and publish bounded results. Exercise revoked/rotated references, stale preflight, outage/deadline and advertised preview/provisioning policy with independent destination-state observations. |

Every fixture has an explicit deadline, expected terminal/nonterminal state,
cleanup owner and redacted output. Runtime users need CONNECT/schema USAGE and
the actual table/sequence DML grants required by installed stores, without
schema CREATE, table ownership or inherited migration privileges. Check grants
on a direct connection and preserve schema snapshots before/after startup.

After Gate U passes, use a disposable role harness for Gate 0 before
implementing `shuetl serve`.
The full release matrix repeats the role scenarios through the built wheel's
public CLI. A source-only harness cannot satisfy installed-artifact acceptance.

Fault synchronization uses barriers and explicit store observations rather
than sleep-based timing assertions. Real clock/deadline waits may be used for
lease expiry and scheduler due times with bounded tolerances. Capture the
upstream state/event/result and the actual sink effect independently: durable
completion does not prove exactly-once external effects. An unlinked firing is
an allowed intermediate state; its recoverable link and canonical submission
identity are the assertions.

## Planned boundary enforcement

Extend `scripts/check_boundaries.py` and package-boundary tests for F00: runtime
composition must not depend on the HTTP adapter; ShuETL must not duplicate schema
inventories, direct table SQL, schedule fingerprints or recovery orchestration.
Allow only the dedicated operational-probe module to define ShuETL process routes;
continue rejecting domain-route copies. Pair static checks with public-call and
HTTP/headless behavior proofs, since class-name/import checks alone are insufficient.
These checker changes belong to W03/W08; the existing 0.5 checker is not claimed
to enforce the new rules yet.

## Criterion mapping

All AC rows start OPEN independently of Gate U. Implement the proposed test
modules before entering their commands as passing evidence.

| Acceptance IDs | Planned check / fixture | Evidence to retain |
| --- | --- | --- |
| AC-001 | Artifact/lock checks; installed metadata inventory | Exact versions, hashes, import origins and the public provider schema requirement/status contract. |
| AC-002 | `spikes/phase_0_6_gate_0.py`; F01 | Upstream-complete scheduler construction, service scope, HTTP/headless command parity, canonical identities, report and actual sink rows. |
| AC-003, AC-026 | `tests/unit/test_phase_0_6_settings.py`, `test_runtime_bindings.py`; negative role/factory matrix | Validation before import/network, factory signature, guarded binding shape and redacted failures. |
| AC-004 | Existing facade/local/PostgreSQL/identity/HTTP/SSE suite rerun on selected upstream artifacts | Regression outcomes, selected-artifact fresh-store setup, stable settings and doctor schema, normalized OpenAPI diff. |
| AC-005, AC-006, AC-021 | `tests/security/test_runtime_roles.py`; F01/F04 | Import/call tracing, worker-only execution/secret resolution, cross-scope denials and sentinel scans. |
| AC-007, AC-013, AC-014 | `tests/integration/test_runtime_scheduling.py`; F02 | Claim/submit/link boundaries, prepared/recovered occurrence identity, immutable revision/input snapshot, one canonical accepted run. |
| AC-008 | `tests/integration/test_runtime_schema.py`; F01 | Runtime grants, read-only preflight/health statement trace, zero DDL/explicit commit during inspection/construction and unchanged schema snapshots; missing/behind/unknown/corrupt negatives. |
| AC-009, AC-010, AC-032 | `tests/integration/test_runtime_lifecycle.py`; F05 | Probe status/state/reason, freshness and active-tick response, drain dispatch boundary, cleanup count and timeout/restart behavior. |
| AC-011, AC-012 | `tests/integration/test_runtime_gateway.py`; F02 | Concurrent/retried same-key receipts, changed-intent conflict and before/after-commit client ambiguity. |
| AC-015, AC-016, AC-017 | `tests/integration/test_runtime_workers.py`; F02 | Lease owner/token, attempt/result publication, stale-write rejection and independent effect marker. |
| AC-018 | `tests/integration/test_runtime_actions.py`; F02/F03 | Accepted/leased/running cancellation, actual sink effect and upstream interruption/uncertainty outcome. |
| AC-019 | Runtime lifecycle/worker suites; F02/F05 | Database loss/restoration, non-ready state, no memory/file fallback and recovered canonical state. |
| AC-020 | Runtime gateway/worker suites; F03 | Worker process identity, observable sink write, gateways respond to control reads while execution is blocked. |
| AC-022 | `scripts/check_clean_wheel.py`; F01/F05 | Wheel/container digests, supervisor commands, broker absence, PostgreSQL/resource-volume prerequisites and shutdown transcript. |
| AC-023 | `.github/workflows/checks.yml`, `scripts/check_release.py` | Hosted Python 3.11–3.13 real PostgreSQL and clean-wheel subprocess jobs, JUnit results and zero skipped required cases. |
| AC-024 | `scripts/check_evidence.py`; complete ledger | 33 exact approved requirements bound to executed commands, artifacts/provenance and reviewed limitations. |
| AC-025 | `tests/integration/test_runtime_transition.py`; F06 | Separate store identities, no old-store startup, schedule/admission authority handoff and rollback/reconciliation transcript. |
| AC-027 | Installed reference host fixture; F01/F03 | Neutral backend dependency/import inventory, role-specific bindings, unchanged host code across specification edits, authorized HTTP/headless schedule and run command parity without direct stores or synthetic requests. |
| AC-028 | `tests/integration/test_runtime_providers.py`; F03 | Support matrix per pairing/mode, exact sink values, transform/quality success and failure, schema drift, writer policy, aliases/upsert keys. |
| AC-029 | `tests/integration/test_runtime_controls.py`; F03 | Public option/command inventory, schema round trips, requested/effective configuration and live behavior; explicit qualified/unavailable reasons. |
| AC-030 | Runtime actions/controls suites; F03 plus independent extension wheel | Failed-work retry versus deliberate new run, lineage/attempt identities, extension installation and execution with no core changes. |
| AC-031 | `tests/integration/test_runtime_resources.py`; F04 | Immutable ownership/version/checksum, retention/expiry, cross-worker report reads and bounded cleanup without exposed paths/secrets. |
| AC-033 | `tests/integration/test_runtime_provider_actions.py`; F07 | Public action-host/handler paths, resource identity changes, action canonical results, independent read-only preview and explicit mutation policy when advertised. |

## Evidence layout and checker work

Create `docs/evidence/0.6/` during implementation with:

- `README.md`: environment, artifact identities, gate summary and all 33 AC rows.
- `upstream.md`: U01–U05 issue/release/artifact/signature/conformance records and independent verification; no issue-closure-only PASS.
- `contracts.md` and `ownership.md`: exact public imports/signatures and
  ETLantic/ShuETL/host responsibilities; include binding and probe schemas.
- `qualification.md` and `proofs.json`: executed requirement bindings with
  command, artifact, exact approved requirement, provenance and limitation.
- `processes.md`: role/scope/store mapping, fault barriers, commit observations,
  lease/firing/submission/attempt/report/effect identities and cleanup.
- `providers.md`: advertised pairing/mode/control matrix, resource-volume and
  independent-package evidence; distinguish upstream evidence from ShuETL runs.
- `transition.md`: fresh-store handoff, unfinished-work reconciliation and
  rollback rehearsal.
- `ci.md` and `openapi.normalized.json`: final hosted jobs and canonical route
  schema evidence with reviewed upstream changes.

Add 0.6 to the evidence checker's plan map, expected count (33), proof bindings,
semantic validation and release script. Keep immutable prior release evidence;
Gate U validation is required in addition to the unchanged count of 33 ACs;
new runtime statuses or probe shapes cannot silently alter `shuetl.doctor/1`.
Use synthetic credentials and scrub local paths/URLs/principal values from
public logs. Retain redacted role instance IDs for fault correlation.

## CI and release gates

Gate A runs formatting, lint, typing, import/route boundaries, configuration,
identity and regression tests on Python 3.11–3.13. Gate B runs real PostgreSQL
18.6 process/lifecycle/provider tests with explicit runtime grants and shared
resource setup on the same Python matrix. Gate C builds distributions and
installs the wheel plus host/extension fixtures into clean environments outside
the source checkout; it repeats manual/scheduled execution, validates OpenAPI,
artifact metadata and the full evidence registry.

Use `check_pytest_no_skips.py` on every required integration/clean-wheel JUnit
result. Missing database/provider fixtures or failed subprocess setup fail
the job. Optional unadvertised providers have explicit unavailable support
rows, not a skipped required criterion. Freeze the support matrix before final
qualification and review every gap against the capability-delivery contract.

The release workflow consumes the qualified artifact and exact source commit,
not an earlier spike's PASS. Publish only when Gate U, Gate 0, Gates A–C and all
33 criteria pass on the final selected artifacts with no unresolved semantic
defect in the supported profile.
