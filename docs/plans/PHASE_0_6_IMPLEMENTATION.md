# Phase 0.6 — Implementation and Release Plan

Prepared: 2026-10-08.
Updated: 2026-10-09 after ETLantic 0.57.0 publication.
Status: Gate U accepted, exact pins adopted, PostgreSQL Gate 0 qualified.
W02 public-interface freeze and W03/W04 source implementation are complete.
The installed 0.6.0 wheel passes local and hosted PostgreSQL 18.6 startup,
readiness and signal smoke tests for all four roles. Hosted evidence is bound to
the `c0153da` ShuETL and reference-host wheel hashes in
[`docs/evidence/0.6/README.md`](../evidence/0.6/README.md). Runtime controls and
failure ordering have received follow-up source corrections. W04 failure and
active-work qualification, W05–W08, and hosted final-artifact acceptance remain
open.

The [implementation review corrections](../reviews/PHASE_0_6_REVIEW_FIXES.md)
fix nine startup, recovery, cleanup, binding, evidence and authentication issues.
Their source regressions and local SCRAM smoke checks do not close release gates.
The [review follow-up](../reviews/PHASE_0_6_REVIEW_FIXES_FOLLOWUP.md) closes the
remaining runtime, configuration, boundary and artifact-binding source findings;
hosted basic CLI smoke tests now pass, while failure qualification and final
artifact evidence remain outstanding.

This is the task sequence for the [execution contract](PHASE_0_6_EXECUTION.md).
The [verification plan](PHASE_0_6_VERIFICATION.md) remains the authority for
fixtures and evidence. [ADR-0015](../adr/0015-backend-and-deployment-ownership.md)
governs ownership; [ADR-0014](../adr/0014-role-separated-managed-runtime.md)
defines the role-composition requirements. If this checklist conflicts with a
contract, resolve and update the contract before implementing that behavior.

## Release objective and current starting point

Ship ShuETL 0.6.0 as a qualified deployment of an independently usable ETLantic
backend: authenticated gateway, native scheduler, run workers and separate action
workers, using PostgreSQL and explicitly shared resources. Hosts supply identity,
membership and resource bridges, then issue canonical specifications/commands.
ETLantic/providers supply the backend graph, schedule services, complete role
factories, schema inspection and runtime correctness.

Current development source is ShuETL 0.6.0, pinned to ETLantic core/FastAPI/
SQLModel 0.57.0; non-ETLantic runtime pins are retained. The published rollback
baseline remains ShuETL 0.5.0/ETLantic 0.55.0. The CLI supports doctor, database
upgrade and `serve --role` for gateway, scheduler, run-worker and action-worker
processes. W03/W04 source provides trusted bindings, upstream backend composition,
readiness/liveness, cooperative drain and cleanup. Installed CLI and PostgreSQL
lifecycle behavior still needs qualification.

[Coverage acceptance](../evidence/0.6/coverage-acceptance.md) records U01–U05 PASS.
[Gate 0 evidence](../evidence/0.6/README.md) records four separately launched roles,
restricted PostgreSQL 18.6 grants, real manual/native scheduled effects, canonical
reports and HTTP/headless schedule parity. The existing upstream issues remain
administratively OPEN. Publication/release criteria are not closed by feasibility.

The critical path is:

```text
W00: accept published 0.57.0 public contracts and artifact evidence
  → W01: exact dependency/schema selection and compatibility
  → W02: installed-artifact PostgreSQL Gate 0 + API freeze
  → W03: ShuETL settings, bindings and upstream factory selection
  → W04: CLI, supervision, probes and cleanup
  → W05/W06: live capability and process-failure qualification
  → W07: deploy/transition/rollback rehearsal
  → W08: final wheel, hosted gates and release decision
```

## Work permitted before Gate U closes

Prepare isolated test infrastructure, subprocess capture/barrier utilities,
runtime/migration grant fixtures, independent sink assertions, artifact packaging
for reference hosts, and evidence-checker design. Inventory the existing public
exports, settings, OpenAPI, doctor schema and lifecycle regressions. These tasks
can progress alongside upstream work without committing ShuETL to guessed APIs.

Use dedicated disposable databases and process groups. The existing PostgreSQL
test fixture drops/recreates its public schema; never aim it at an operator's
configured application database. Give new fixtures explicit isolated URLs and
ownership, bounded waits, and cleanup for partial process startup.

Keep preparatory branches against the existing package train until W01. Do not
implement a replacement backend, schedule coordinator, schema inspector or
runtime protocol while waiting. A provisional test harness is not a supported
public interface or release proof.

## W00 — Review and accept published upstream contracts

Owner: ShuETL for Gate U evidence review and acceptance; ETLantic/provider
maintainers for any qualification defects. Contract surfaces and upstream
conformance are delivered in 0.57.0. Use the existing issues for traceability:

| Issue / gate | Published outcome | Acceptance focus |
| --- | --- | --- |
| [#278](https://github.com/eddiethedean/etlantic/issues/278) / U01 | Neutral backend handle, public services and role contracts; optional provider-owned SQL graph; HTTP adapter consumes the backend; canonical context checks and explicit cleanup | Bind the isolated headless/shared-adapter evidence and ownership conformance. |
| [#281](https://github.com/eddiethedean/etlantic/issues/281) / U04 | Provider-owned read-only schema/connectivity status, integrity and required-object checks, reused during construction | Bind public inspection state/grant conformance; retain independent no-write checks. |
| [#279](https://github.com/eddiethedean/etlantic/issues/279) / U02 | Public authorized schedule commands/queries; HTTP delegates to them with equivalent scope, revisions and outcomes | Review parity/denial/revision/recovery coverage and retain full configured parity for Gate 0. |
| [#280](https://github.com/eddiethedean/etlantic/issues/280) / U03 | Complete managed scheduler factory including schedule store and explicit preparation/submission/recovery collaborators | Bind factory/collaborator and PostgreSQL recovery conformance; live ShuETL effects follow in Gate 0. |
| [#282](https://github.com/eddiethedean/etlantic/issues/282) / U05 | Public status/capability and cooperative-stop contracts for scheduler, run worker and action worker | Review cached-status/drain guarantees and active-work limits before supervisor design. |

Tasks:

- [x] Agree exact public imports, constructor inputs, returned handles, status
  results, stop guarantees and resource owners in upstream review.
- [x] Upstream delivered canonical behavior and semantic conformance in 0.57.0.
  Include context authorization, schedule command parity, missing collaborator
  rejection, schema corruption, recovery and in-flight stop limitations.
- [x] Independently prove the neutral upstream package works without installing the HTTP adapter.
  Gateway adaptation must preserve the fixed execution-import isolation.
- [x] Verify published compatible artifacts with source provenance and conformance evidence.
  Preserve compatibility entry points through delegation where feasible.
- [x] Independently install the published candidates outside both source checkouts.
  Record hashes, origins, signatures, upstream commands and observed outcomes.
- [x] Map upstream conformance to each requested guarantee, including schedule
  conflicts/trigger races, trusted-context checks, active role drain and
  owned/borrowed partial-close safety. Obtain additional upstream evidence for
  any uncovered guarantee; artifact totals alone do not establish coverage.
- [x] Record all five Gate U decisions; a closed issue without delivered evidence
  remains an open prerequisite.

Exit: U01–U05 pass on published artifacts. Stop at missing contracts and report
the exact upstream gap. No source-tree patch or guessed factory closes this gate.

## W01 — Select the package train and preserve compatibility

Owner: ShuETL. Depends on W00. Acceptance: AC-001/004/008.

- [x] Select exact compatible core, HTTP adapter, persistence and enabled connector
  packages. Verify Python 3.11–3.13 and declared dependency compatibility.
- [x] Update `pyproject.toml`, `uv.lock` and `src/shuetl/compatibility.py` together.
  Set the development target to 0.6.0; publish only through W08.
- [x] Replace downstream schema recognition in `postgresql.py`, provider bundles
  and doctor with public provider status/requirements. Keep ShuETL server/TLS
  qualification policy and safe remediation. No copied table inventories or SQL
  against internal version-table layouts remain in active inspection paths.
- [x] Preserve existing facade/bundle signatures, caller-owned lifecycle and
  `shuetl.doctor/1` fields. Where construction changes, delegate upstream while
  preserving documented behavior; record any unavoidable compatibility change.
- [x] Freeze a regression inventory for exports, settings/source precedence,
  identity guards, prefix/conflict checks, HTTP errors, SSE and OpenAPI. Exercise
  memory/SQLite as well as the gateway pilot on separately provisioned stores.
- [x] Record the provider's exact schema contract and fresh-store limitations.
  Never interpret a new migration head as 0.55 durable-state compatibility.

Exit: selected package metadata, lock and regression checks pass; normal provider
inspection/construction is read-only and schema ownership is upstream. Record
each compatibility difference before progressing to public API freeze.

## W02 — Prove Gate 0 and freeze the new interfaces

Owner: ShuETL integration. Depends on W01. Acceptance: AC-002/006–008/026/027.

- [x] Implement `spikes/phase_0_6_gate_0.py` using the selected installed factories
  and a separately installed reference binding package. The pre-CLI harness
  owns processes/resources only and invokes public upstream contracts.
- [x] Provision disposable PostgreSQL 18.6 using a migration user; launch actual
  runtime connections with DML grants and no schema CREATE, table ownership or
  inherited migration privileges. Preserve SQL traces and schema snapshots.
- [x] Construct gateway, scheduler, run worker and action worker with matching
  store/scope/profile/resource identities and unique process owners.
- [x] Observe manual and native-scheduled effects and canonical reports through
  separate processes. Use the action role when admission requires preparation.
- [x] Prove authorized Python/HTTP schedule create, amend, pause, resume, preview,
  trigger, read, list and firing parity, including conflicts and denials.
- [x] Freeze role-specific binding types, settings aliases, configuration
  precedence, public backend access, ownership/cleanup and lifecycle signatures.
  Record them in ADR-0014 and the 0.6 contract/ownership evidence.
- [x] Select a qualified ASGI server dependency for the gateway CLI if required;
  declare it directly where used, pin it, and record its startup/signal ownership.
  Scheduler/worker startup must not initialize it or the host authentication stack.

Exit: Gate 0 passes with actual sink evidence and no upstream workaround.
ADR-0014 records the frozen signatures. Gate 0 proves feasibility; final-wheel
acceptance remains W08 work.

## W03 — Implement settings, host bindings and backend selection

Owner: ShuETL. Depends on W02. Acceptance: AC-003/005/006/026/027/029.

The implemented public settings and binding surfaces are in these modules:

| Area | Files | Required behavior |
| --- | --- | --- |
| Settings | `src/shuetl/settings.py` | Add preview/role/kind/scope/store/probe/grace settings; preserve existing aliases and constructor precedence; reject incompatible role fields before imports/I/O. |
| Host binding contracts | `src/shuetl/bindings.py` | Separate gateway and runtime records using canonical upstream types; explicit owned integration cleanup. |
| Trusted binding loader | `src/shuetl/factory.py` | Validate `package.module:callable`, import explicitly trusted code, validate returned role shape, redact failures and close partially acquired owned resources. |
| Backend composition | `src/shuetl/backend.py` | Configure upstream-complete factories, consume public provider status, check deployment scope and expose canonical services for headless use. |
| Public interface | `src/shuetl/__init__.py`, existing facade/providers | Add only frozen composition exports; preserve old exports and caller-owned interfaces. |

- [x] Gateway bindings use the adapter's authoritative guarded pair; runtime
  bindings have no Request, HTTP context factory, principal dependency or ASGI hook.
- [x] Canonical context validity and command authorization stay upstream; reject
  deployment scope mismatches without remapping identity or request intent.
- [x] Preserve upstream profile/provider/action/resource types, governance
  providers, artifact roots and schedule parameter resolvers through the public
  backend config. Do not create another policy or capability vocabulary.
- [x] Add negative configuration, malformed binding, import-failure, scope and
  partial-cleanup checks mapped to the verification matrix.
- [x] Extend boundary checks for standard-path semantic graph assembly, SQL
  against provider-owned schemas and domain-route copies. Pair static checks with
  public-call traces.

Exit: source implementation consumes upstream factories and rejects unsafe
combinations before admission. Installed-artifact acceptance remains open.

## W04 — Implement role CLI, supervision and operational probes

Owner: ShuETL. Depends on W03 and qualified U05. Acceptance: AC-009/010/019/021/032.

- [x] Extend `src/shuetl/cli.py` with `serve --role` and worker `--kind`; verify
  agreement with required settings, safe errors and defined exit codes.
- [x] Add role entry points in `src/shuetl/runtime.py` with separate gateway and
  runtime import paths. Use a small process supervisor around frozen upstream
  dispatch/status/stop calls, one execution thread per worker initially.
- [x] Generate owner IDs per start and preserve stable service principals. Track
  process states separately from canonical ETL status.
- [x] Add a dedicated operational probe module serving loopback `/live` and
  `/ready`. Allow only these process endpoints through the boundary checker.
- [x] Refresh read-only provider/runtime evidence independently of active ticks;
  stale evidence fails readiness. Keep probes responsive during long work and
  allow healthy scheduler standby.
- [x] Handle signals, repeated shutdown, partial startup and dispatch races:
  fail readiness, stop new dispatch, call upstream cooperative stop, await active
  work, close backend and then bindings once. Grace expiry remains non-ready
  with incomplete-drain diagnostics until external supervisor termination.
- [x] Qualify installed-wheel construction, readiness/liveness, SIGTERM shutdown,
  clean exit and credential-sentinel absence for gateway, scheduler, run worker
  and action worker against PostgreSQL 18.6. Evidence: `docs/evidence/0.6/cli-postgresql.json`.
- [ ] Qualify cleanup order/count, active claims after signal, provider
  outage/recovery and grace expiry. Never adjust upstream leases, repair work or
  write terminal results.

Exit: source implementation supports all four kinds. Installed startup and basic
signal shutdown pass locally; drain with active work, outage/recovery and
grace-expiry behavior remain unqualified.

## W05 — Qualify advertised live capabilities

Owner: ShuETL deployment integration; ETLantic/providers supply conformance.
Depends on W03/W04. Acceptance: AC-020/027–031/033.

- [ ] Package an independent reference host and example backend extension as
  test artifacts, installed without source-checkout imports or host ETL code.
- [ ] Freeze the advertised pairing/write-mode/control matrix before final
  qualification. Minimum: immutable CSV/PostgreSQL sources to PostgreSQL sink.
  Optional Foundry, preview and provisioning require separate supported rows.
- [ ] Verify exact sink values, canonical reports, bounded transforms and quality
  success/failure, effective overrides, disabled-writer policy, aliases/upsert
  keys, schema drift, retry versus new-run identity and extension execution.
- [ ] Change specifications while reference host runtime code remains unchanged.
  Verify HTTP/headless canonical records and command/control parity.
- [ ] Exercise action workers for connection/catalog/schema/preflight; test
  deadlines, rotation/revocation, stale preflight and outages. No gateway secrets.
- [ ] Prove immutable input/report access across worker replacement, ownership,
  checksums, expiry, retry retention and bounded cleanup for advertised file support.
- [ ] Attach upstream conformance references and independent ShuETL process/sink
  observations to each row; mark unavailable features explicitly.

Exit: every advertised combination passes. Resolve semantic failures upstream;
adjust advertised scope only through an explicit contract change, never by
silently dropping the required baseline or accepting skipped cases.

## W06 — Qualify coordination and failure recovery

Owner: ShuETL subprocess fixtures, observing upstream outcomes. Depends on W04
and a working W05 fixture. Acceptance: AC-007/010–019/021/031/032.

- [ ] Run two processes of each role kind on one store with distinct owners.
  Include both action and run worker contention.
- [ ] Add deterministic barriers/observations around public commit boundaries,
  bounded deadlines, process-group cleanup and diagnostic capture. Avoid
  sleep-only synchronization and production fault hooks.
- [ ] Kill gateways before/after acceptance and retry the logical idempotency
  token; inspect one canonical submission and changed-intent conflicts.
- [ ] Kill schedulers across preparation, claim, accept and link; verify one
  logical firing and upstream recovery of unlinked accepted work.
- [ ] Kill workers before/after lease/effect/result publication, expire leases,
  reject stale completion, and inspect attempts plus actual sink effects.
- [ ] Exercise queued/leased/running cancellation, long-tick drain, grace expiry,
  provider outages and recovery without fallback stores or fabricated success.
- [ ] Scan outputs for seeded credential sentinels while retaining meaningful
  failure reasons and truthful uncertain-effect outcomes.

Exit: required failure rows pass on real PostgreSQL with separate processes.
Unit/thread tests supplement these checks but cannot replace them.

## W07 — Rehearse deployment and fresh-store transition

Owner: ShuETL operator documentation/integration. Depends on W05/W06.
Acceptance: AC-022/025.

- [ ] Provide one-artifact container and ordinary process-supervisor examples
  for every role, explicit ports/identities, TLS/grants, shared resources and
  migration-before-runtime ordering. No broker unless a selected provider needs it.
- [ ] Rehearse disabling old admissions/scheduling, provisioning a separate new
  store, public re-enrollment, unfinished-work/effect reconciliation and activation.
- [ ] Rehearse rollback to retained 0.5/0.55 with one trigger authority; no
  conversion or automatic replay of uncertain work between stores.
- [ ] Document supported provider modes, observable health, stop limitations and
  at-least-once effects using the qualified evidence.

Exit: commands work from the pinned installed artifact; transition and rollback
transcripts demonstrate the same topology and ownership claimed by the release.

## W08 — Enforce final-artifact gates and release

Owner: ShuETL release engineering. Checker/CI design can begin early; acceptance
depends on W00–W07. Acceptance: AC-023/024 and every release criterion.

- [ ] Extend `scripts/check_evidence.py` with the 0.6 plan, exactly 33 ACs,
  requirement/provenance bindings, Gate U/0 evidence and incomplete-result rejection.
- [ ] Extend `check_release.py`, `check_clean_wheel.py`, artifact/OpenAPI checks
  and no-skips enforcement for installed role/process fixtures and upstream gates.
- [x] Add a hosted PostgreSQL 18.6 matrix job that builds and installs ShuETL and
  the reference host outside the checkout, verifies installed origins, and runs
  the public CLI against all four roles on Python 3.11–3.13. Remaining hosted
  fault-integration and final-artifact acceptance are still required.
- [x] Locally and in hosted CI, build/install the development wheel and reference
  host outside the checkout, verify origins, and run all role kinds against
  PostgreSQL 18.6. Hosted startup/readiness/SIGTERM evidence is recorded for
  Python 3.11–3.13 under run 37974307758; fault-integration remains open.
- [ ] Create `docs/evidence/0.6/` with all verification-plan records. Record the
  exact commit, upstream artifacts, schema contract, environments, commands,
  results, identities, independent effects and limitations. No placeholder PASS.
- [ ] Resolve the current source-distribution hash check as part of artifact
  provenance: compare 0.6 builds with their own reproducible manifest, preserve
  historical 0.5 hashes, and avoid a hash record embedded in the artifact it hashes.
  Do not refresh historical evidence merely to make changed source match it.
- [ ] Review the final supported matrix, dependency/ownership boundaries,
  security/durability findings and migration/rollback instructions.
- [ ] Qualify a frozen source/artifact candidate. Gate evidence must include the
  source commit and SHA-256 of the ShuETL and reference-host wheels; Gate 0 and
  CLI qualification must agree on both hashes. The release build and post-download
  publish job now recheck the qualified hashes before publication. After any
  subsequent source or packaged-document change, rebuild and rerun affected gates.
- [ ] Publish/tag 0.6.0 only when Gates U/0/A–C and AC-001–033 pass with zero skipped
  required cases. Verify distribution metadata and clean-install role smoke tests
  for the published artifact; update release/status documentation to actual facts.

Exit: published artifacts match qualified provenance and the recorded support
claim. Closed issues, an earlier spike and green source-only tests are insufficient.

## Reviewable change sequence

Use separate reviewable changes for upstream features and ShuETL integration.
Do not combine both repositories' ownership in one implementation patch.

| Change | Scope | Merge prerequisite |
| --- | --- | --- |
| Preparation | Disposable fixtures, reference package scaffolding, regression inventory and CI/evidence design | Existing baseline checks; no new public API or Gate U PASS claim |
| Upstream delivery — published in 0.57.0 | U01–U05 with conformance and compatibility delegation | Candidate audit verified publication and evidence; any new defect is fixed upstream |
| Upstream acceptance | Gate U decisions for the exact published candidate | Bind signatures, artifact provenance, conformance and isolated checks to U01–U05 |
| ShuETL adoption | W01/W02 pins, public inspection integration, regression and Gate 0 harness | Published upstream artifacts; Gate U verification |
| ShuETL construction | W03 settings/bindings/factory selection and boundaries | Gate 0 and frozen signatures |
| ShuETL operation | W04 CLI, probes, supervisor and cleanup | Construction plus lifecycle qualification |
| ShuETL behavior | W05/W06 live providers/resources/extensions and subprocess faults | Working installed roles and declared support matrix |
| ShuETL release | W07/W08 deployment, transition, evidence and final CI | All required behavior gates; exact final artifact |

Sequence related changes as needed for review size. Preparatory test/CI work can
overlap upstream delivery; scheduled standard-path implementation stays behind
Gate U/0. Optional provider expansion can follow the minimum fixture, but every
advertised row must finish before publication.

## Completion tracking and first actions

Record each W00–W08 item as planned, implementing, blocked by a named dependency,
or qualified with an exact command/artifact reference. No inferred PASS from
issue closure. Use the dependency register for upstream state and the 0.6 ledger
for executed qualification; do not create a second acceptance vocabulary.

The next actions are W04 active-work/outage qualification and W05 capability
scope/effect evidence. W06 process-failure injection, W07 transition rehearsal
and W08 final-artifact/hosted acceptance remain release prerequisites. Do not
close Gates A–C based on source implementation, Gate 0 feasibility or the basic
hosted CLI smoke test.
