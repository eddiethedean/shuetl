# Phase 0.6 — Implementation and Release Plan

**Train update (2026-10-11):** ETLantic core, FastAPI, SQLModel and SQL connector
are pinned to 0.57.2. Earlier hosted snapshots remain bound to their recorded
source commits. Current local installed-wheel checks now pass Gate 0 with
controls and retention on Python 3.11–3.13, active native CLI drain/force on
Python 3.12, a Linux container role run, and a 0.5-to-0.6 transition rehearsal. Crash qualification still has two
upstream failures (#299), live preflight remains open in #121, and hosted
final-artifact acceptance is pending.

The [0.57.2 audit](../reviews/ETLANTIC_0_57_2_REQUIREMENTS_AUDIT.md) records
published-wheel provenance and issue follow-ups. Current details and exact
candidate hashes are in the [development qualification record](../evidence/0.6/current-qualification.md).
Default preflight is static; live readiness remains upstream #121. These results
do not close the broader 33-criterion release matrix.

Prepared: 2026-10-08.
Updated: 2026-10-11 after ETLantic 0.57.2 publication and local candidate runs.
Status: W02 public-interface freeze and W03/W04 source implementation are
complete. Current local Gate 0 with controls and retention passes Python
3.11–3.13; current native active drain/force and container active-drain checks
and transition rehearsal pass on Python 3.12.
The crash matrix records 20 passes and two failures assigned to upstream #299.
Live preflight and hosted final-artifact review remain open. Current evidence and
wheel hashes are in
[`docs/evidence/0.6/current-qualification.md`](../evidence/0.6/current-qualification.md).
Hosted final-artifact acceptance, the broader W05 capability matrix, two W06
recovery failures, production W07 transition evidence, and W08 final review
remain open.

The installed Gate 0 reference workload executes CSV-to-PostgreSQL append,
PostgreSQL snapshot-to-PostgreSQL append, and a keyed PostgreSQL upsert with
typed normalization, filtering, quality accept/reject outputs, and independent
sink assertions. Local PostgreSQL 18.6 runs pass. The required hosted Python
3.11–3.13 Gate 0 matrix, two-process role coordination and installed-role CLI
matrix pass on source commit `c064aa9`; the exact CI records
and wheel hashes are stored under `docs/evidence/0.6/hosted-gate0/` and
`hosted-cli/`. This qualifies the development installed baseline only; final
artifact qualification and the broader acceptance matrix remain open.

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
SQLModel/SQL 0.57.2; non-ETLantic runtime pins are retained. Current Gate U
auditing and local Gate 0 evidence use 0.57.2; older hosted snapshots remain
bound to earlier source commits. The published rollback
baseline remains ShuETL 0.5.0/ETLantic 0.55.0. The CLI supports doctor, database
upgrade and `serve --role` for gateway, scheduler, run-worker and action-worker
processes. W03/W04 source provides trusted bindings, upstream backend composition,
readiness/liveness, cooperative drain and cleanup. Installed CLI and PostgreSQL
lifecycle behavior still needs qualification.

[Coverage acceptance](../evidence/0.6/coverage-acceptance.md) records U01–U05 PASS.
[Gate 0 evidence](../evidence/0.6/README.md) records four separately launched roles,
restricted PostgreSQL 18.6 grants, real manual/native scheduled effects, canonical
reports and HTTP/headless schedule parity. The existing U01–U05 upstream issues
are closed. Publication/release criteria are not closed by feasibility.

The critical path is:

```text
W00: accept published 0.57.2 public contracts and artifact evidence
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
conformance are delivered in 0.57.2. Use the existing issues for traceability:

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
- [x] Upstream delivered canonical behavior and semantic conformance in 0.57.2.
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
- [x] Add barrier-controlled drain regressions for the SQLite run worker and a
  PostgreSQL-backed scheduler. The PostgreSQL case proves SIGTERM leaves
  readiness false and runtime resources open after grace expiry while leader-
  lease acquisition is in flight, then closes after the call returns. Local and
  hosted Python 3.11–3.13 PostgreSQL integration pass.
- [x] Inject an unreachable provider-inspection result followed by a healthy
  result and verify `/ready` reports `provider_unavailable`, remains live, and
  recovers. This verifies supervisor status handling; it does not establish a
  real PostgreSQL connection outage/recovery.
- [x] Block the scheduler's PostgreSQL connections through a local TCP fault
  proxy, verify readiness drops while liveness remains healthy, restore
  connectivity, and verify readiness recovers before orderly shutdown. The
  disposable PostgreSQL test passed locally and in hosted Python 3.11–3.13 CI
  run 37984396221 with zero skips.
- [x] Extend the TCP fault-proxy test to scheduler, run-worker and action-worker
  roles. The full dedicated PostgreSQL 18.6 integration file passes locally
  (9 passed, 0 skipped), including readiness loss, continued liveness and
  recovery for all three roles. Hosted run 37989243217 passes this expanded
  suite on Python 3.11–3.13 with zero skipped cases.
- [x] Qualify exact cleanup order/count across all four installed CLI roles.
  The disposable PostgreSQL harness records one owned-engine disposal followed
  by one host-binding close after SIGTERM for gateway, scheduler, run worker and
  action worker; local Python 3.13 passed. Hosted verification remains pending.
- [x] Run installed native active-work drain and forced termination for
  scheduler, run worker and action worker against PostgreSQL 18.6 on Python
  3.12.13. Cooperative SIGTERM/SIGINT drain passes; forced SIGKILL leaves
  canonical state for upstream recovery without synthesizing a terminal result.
  Local evidence is in
  [`current-qualification.md`](../evidence/0.6/current-qualification.md).
- [ ] Run the native active-work/force case on hosted Python 3.11–3.13 and
  qualify active work through grace expiry in the Linux container for all
  applicable roles. Local native qualification currently covers Python 3.12.13.

Exit: source implementation supports all four kinds. Installed startup and basic
signal shutdown pass locally. PostgreSQL scheduler drain and scheduler, run-
worker and action-worker outage/recovery pass locally; hosted run 37989243217
passes the outage cases for all three runtime roles on Python 3.11–3.13. Exact
cleanup order/count passes locally and in hosted CI for all four CLI roles.
Hosted active drain and container force evidence remain open. Local native
Python 3.12 active drain/force and container active drain pass.

## W05 — Qualify advertised live capabilities

Owner: ShuETL deployment integration; ETLantic/providers supply conformance.
Depends on W03/W04. Acceptance: AC-020/027–031/033.

- [x] Package an independent reference host and example ETLantic `Transformation`
  workload as separate test wheels, installed without source-checkout imports or
  host ETL code. Hosted CLI and Gate 0 jobs verify the installed origins. This
  demonstrates one extension workload, not a complete private-extension API.
- [x] Freeze the 0.6 candidate pairing/write-mode/control matrix in
  [`docs/evidence/0.6/providers.md`](../evidence/0.6/providers.md) to the three
  executed rows and their observed control paths. No untested pairing, mode or
  path is included; release support remains conditional on AC-028–033, including
  file-resource immutability/expiry. Optional Foundry, preview and provisioning
  are excluded unless separately qualified.
- [x] Record the observed baseline and current exclusions in
  [`docs/evidence/0.6/providers.md`](../evidence/0.6/providers.md). It documents
  CSV and PostgreSQL snapshot sources to PostgreSQL append sinks, plus one
  PostgreSQL primary-key upsert, including exact sink observations and the
  current experimental-provider limit. All three rows pass the hosted matrix;
  this inventory is not the final advertised support contract.
- [x] Verify exact sink values, canonical reports, and a pinned ETLantic local
  portable plan for select/drop/rename, filtering, scalar lowercase, output
  schema, and required/range/set/uniqueness quality acceptance and rejection.
  The portable plan runs on the independent installed reference host; live
  PostgreSQL connector runs remain a separate provider observation and do not
  claim portable-plan pushdown.
- [x] Qualify deterministic keyed deduplication on the installed 0.57.2 local
  compiler with an order-reversal case. The historical 0.57.0 defect is fixed
  upstream in [ETLantic #283](https://github.com/eddiethedean/etlantic/issues/283);
  published-wheel evidence is in the 0.57.2 audit.
- [x] Verify selected effective/no-write options, aliases/upsert keys, schema
  drift, failed retry versus deliberate new-run identity, uncertain partial
  effect replay policy, and independent transformation package execution in the
  local control/provider fixtures. Alternate write modes and full option support
  remain outside the qualified matrix.
- [x] Add a concrete CSV/PostgreSQL-to-PostgreSQL fixture to Gate 0. It verifies
  integer normalization, lowercase, scalar arithmetic, filtering, projection,
  not-null/range/membership quality rules, accepted/rejected rows and independent
  sink effects. The exact passing fixture is bound to the hosted matrix job;
  this closes only the reference-workload slice, not the advertised support matrix.
- [x] Extend Gate 0 with a live PostgreSQL repeatable-snapshot source to append
  sinks, typed normalization and quality acceptance/rejection. The local and
  hosted installed-wheel runs pass on PostgreSQL 18.6; hosted Python 3.11–3.13
  evidence observes the expected rows and SELECT-only input grants.
- [x] Add a distinct PostgreSQL upsert fixture with a declared primary-key
  conflict key. Two separate accepted runs update the same destination key after
  a source snapshot change, preserving one row and recording independent effects.
  Local and hosted PostgreSQL 18.6 installed-wheel runs pass on Python 3.11–3.13;
  each hosted record binds two distinct run IDs and the single updated target row.
- [ ] Change specifications while reference host runtime code remains unchanged.
  Verify HTTP/headless canonical records and command/control parity.
  The installed Gate 0 harness now registers a changed canonical definition
  through the public managed service, changes its source/sink asset bindings,
  hashes the installed host runtime before and after, and compares the HTTP
  definition and plan with headless results. This remains unchecked until the
  candidate-wheel PostgreSQL run records a passing result.
- [x] Exercise action workers for connection/schema and static preflight;
  test deadlines, resource rotation/revocation and connector outage/recovery
  without gateway secrets. Managed preflight is only `read_only_plan`; live
  readiness remains blocked by [ETLantic #121](https://github.com/eddiethedean/etlantic/issues/121).
- [x] Prove selected immutable input/report access across worker replacement,
  owner/scope/checksum/version checks, expiry, retained retry bytes and bounded
  cleanup. Hosted final-candidate and broader file-mode evidence remain open.
- [x] Attach 0.57.2 upstream conformance references and independent ShuETL
  process/sink observations to the executed rows; the provider matrix marks
  excluded and still-unqualified capabilities. The full release evidence
  registry remains pending in W08.

Exit: every advertised combination passes. Resolve semantic failures upstream;
adjust advertised scope only through an explicit contract change, never by
silently dropping the required baseline or accepting skipped cases.

## W06 — Qualify coordination and failure recovery

Owner: ShuETL subprocess fixtures, observing upstream outcomes. Depends on W04
and a working W05 fixture. Acceptance: AC-007/010–019/021/031/032.

- [x] Run two processes of each role kind on one PostgreSQL store with distinct
  process/owner IDs. The installed Gate 0 harness now starts a second gateway,
  scheduler, run worker and action worker; concurrent same-key preparation,
  action/run worker claims and scheduler ticks each produce one canonical
  operation or claim. Local PostgreSQL 18.6 passed. [Hosted CI run 37988337495](https://github.com/eddiethedean/shuetl/actions/runs/37988337495)
  passed the expanded Gate 0 on Python 3.11–3.13 for source commit
  `87a9549dcc148bf5317b4b747d90a6bdcdbee6c2`.
- [x] Add deterministic subprocess barriers/observations around public commit
  boundaries, bounded deadlines, process-group cleanup and diagnostic capture.
  The installed crash fixture injects process death at named public-operation
  barriers and makes no production fault hooks.
- [x] Kill gateways before/after acceptance and retry the logical idempotency
  token; both cases recover one canonical operation.
- [x] Kill schedulers across preparation, claim, accept and link; the firing
  recovery cases pass with one canonical linked submission.
- [x] Kill run workers around lease/effect/result publication, expire leases,
  reject stale completion, and inspect attempts plus actual sink effects.
- [x] Exercise queued/leased/running cancellation, long-tick drain, grace expiry,
  provider outages and recovery without fallback stores or fabricated success.
- [x] Scan captured outputs for seeded credential sentinels while retaining
  failure reasons and uncertain-effect outcomes.
- [ ] Resolve the two accepted `run.prepare` recovery failures when the action
  worker dies after CP1 acceptance (before and after durable submission). The
  other 20 of 22 cases pass; see [ETLantic #299](https://github.com/eddiethedean/etlantic/issues/299)
  and the checked-in current crash record.

Exit: required failure rows pass on real PostgreSQL with separate processes.
Unit/thread tests supplement these checks but cannot replace them.

## W07 — Rehearse deployment and fresh-store transition

Owner: ShuETL operator documentation/integration. Depends on W05/W06.
Acceptance: AC-022/025.

- [x] Provide one-artifact container and ordinary process-supervisor examples
  for every role, explicit ports/identities, TLS/grants, shared resources and
  migration-before-runtime ordering. The Linux/amd64 container runs against
  PostgreSQL 18.6 locally; production supervisor behavior is not exercised.
- [x] Rehearse old-store rejection, provisioning a separate new store, public
  re-enrollment, no automatic replay and rollback mounting of retained 0.5/0.55.
  The accepted-work reconciliation record is seeded, not an interrupted effect;
  production cutover remains unqualified.
- [x] Document the selected provider modes, observable health, stop limitations
  and at-least-once effects using the qualification evidence.

Exit: commands work from the pinned installed artifact; transition and rollback
transcripts demonstrate the same topology and ownership claimed by the release.

## W08 — Enforce final-artifact gates and release

Owner: ShuETL release engineering. Checker/CI design can begin early; acceptance
depends on W00–W07. Acceptance: AC-023/024 and every release criterion.

- [x] Extend `scripts/check_evidence.py` with the 0.6 plan, exactly 33 ACs,
  requirement/provenance bindings, Gate U/0 evidence and incomplete-result rejection.
- [x] Wire the local `check_release.py` gate to format, lint, typing, boundaries,
  tests, reproducible build, artifact/OpenAPI checks, clean-wheel checks and the
  evidence ledger. The final evidence ledger correctly rejects this blocked
  candidate until all release rows pass.
- [x] Add a hosted PostgreSQL 18.6 matrix job that builds and installs ShuETL and
  the reference host outside the checkout, verifies installed origins, and runs
  the public CLI against all four roles on Python 3.11–3.13, including active
  drain/force and transition steps. These expanded workflow changes still need
  a hosted run against the committed candidate.
- [x] Add a separate hosted PostgreSQL 18.6 Gate 0 matrix job that builds and
  installs ShuETL and the independent reference workload outside the checkout,
  runs canonical manual/native-scheduled transfer, and uploads sink-backed
  evidence on Python 3.11–3.13, including PostgreSQL snapshot-source append,
  keyed-upsert, control, resource-retention and fault fixtures. The expanded
  workflow changes still need a hosted run against the committed candidate.
- [x] Locally and in hosted CI, build/install the development wheel and reference
  host outside the checkout, verify origins, and run all role kinds against
  PostgreSQL 18.6. The latest local run includes controls, retention, native
  force and a rebuilt container image; hosted qualification of these latest
  candidate hashes remains open.
- [x] Create the 0.6 evidence index and current local qualification records.
  Current raw artifacts bind candidate hashes, source base commit, environments,
  commands, identities, effects and limitations. The final proof registry still
  awaits remaining acceptance and hosted results; no placeholder PASS is used.
- [x] Resolve the source-distribution hash check as part of artifact
  provenance: compare 0.6 builds with their own reproducible manifest, preserve
  historical 0.5 hashes, and avoid a hash record embedded in the artifact it hashes.
  The reproducible development build now matches the bound wheel and sdist hashes;
  the evidence index is excluded from the sdist to avoid self-reference. Historical
  release evidence remains unchanged.
- [ ] Review the final supported matrix, dependency/ownership boundaries,
  security/durability findings and migration/rollback instructions.
- [ ] Qualify a frozen source/artifact candidate. Gate evidence must include the
  source commit and SHA-256 of the ShuETL wheel plus the distinct Gate 0 reference
  workload and CLI reference-host wheels. Gate 0 and CLI qualification must agree
  on the ShuETL wheel hash and source commit; each reference fixture is bound to
  its own hash. The release build and post-download publish job now recheck the
  qualified hashes before publication. The tag-gated hosted release check now
  downloads every Python-matrix qualification artifact and verifies its source
  commit, candidate wheel, reference wheel, and required pass cases against the
  frozen manifest before packaging can proceed. This wiring still needs a
  hosted run against a clean candidate. After any
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
| Upstream delivery — published in 0.57.2 | U01–U05 with conformance and compatibility delegation | Candidate audit verified publication and evidence; new recovery and live-preflight requirements are tracked in #299 and #121 |
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

The remaining actions are to receive ETLantic fixes for #299 and #121, rerun
the complete failure/preflight matrix, qualify hosted active-work/container
force and current candidate hashes, and complete production transition/rollback
evidence plus the reviewed 33-row ledger. Do not close Gates A–C based on local
evidence or on hosted runs bound to earlier commits.
