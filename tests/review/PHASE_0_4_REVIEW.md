# Phase 0.4 production review

Date: 2026-09-13. Verdict: **NEEDS FIXES**.

## Contract and review boundary

Authority: `docs/plans/PHASE_0_4_EXECUTION.md`, ADR-0010, and AC-001–AC-038.
Review target: the current uncommitted 0.4 implementation against released
0.3 commit `f5806be`. The change adds an explicit PostgreSQL pilot, exact
ETLantic 0.52.0/SQLAlchemy 2.0.52/Psycopg binary 3.3.5 providers, PostgreSQL
18.6 qualification, read-only readiness, explicit upstream migrations,
persistence/restart/concurrency qualification, operations documentation, and
release evidence. Domain schemas, routes, scheduler/worker execution, HA,
multi-tenant qualification, and external exactly-once effects remain excluded.
Backup automation is excluded; restore documentation and verification are not.

Production implementation was not modified. This review adds only this report
and `test_phase_0_4_contract.py`.

## Acceptance criteria

Code inspection is evidence where the behavior follows directly from exact
upstream object composition; it is not represented as a newly executed test.
Independent probes used disposable PostgreSQL 18.6, Python 3.12.13, and the
installed locked provider distributions. Other Python versions and live GitHub
Actions execution were not independently executed in this review.

| AC | Status | Evidence / remaining limitation |
|---|---|---|
| AC-001 | VERIFIED | Metadata, lock, artifact and isolated wheel gates |
| AC-002 | PARTIALLY SATISFIED | Actual server 18.6 verified; current acceptance ledger maps this ID to exports instead of server proof (SOL-010) |
| AC-003 | VERIFIED | Export assertions and isolated wheel imports |
| AC-004 | VERIFIED | Settings cross-field implementation and existing validation suite |
| AC-005 | VERIFIED | Structural URL validation, SecretStr conversion, bounded timeout and explicit TLS enum/default inspection |
| AC-006 | VERIFIED | Metadata-only validation precedes optional provider imports/engine creation; exact remediation and fail-closed flow |
| AC-007 | VERIFIED | Exact settings type/profile checks and explicit adapter validation; existing adapter tests |
| AC-008 | PARTIALLY SATISFIED | Correct native types/shared engine; bundle and API definition repositories differ (SOL-011) |
| AC-009 | PARTIALLY SATISFIED | Native production API and caller objects retained, but not the exposed definition object (SOL-011) |
| AC-010 | VERIFIED | Real fresh/behind/unknown/missing-table probes; bounded wrong-server/unreachable branches inspected |
| AC-011 | VERIFIED | Required inventory/head inspection; fresh and missing-head-table rejection demonstrated |
| AC-012 | VERIFIED | Real fresh catalog unchanged after doctor/bundle inspection; fixed read-only transaction and unchanged facade paths inspected |
| AC-013 | PARTIALLY SATISFIED | Lock/idempotent close and ordinary failure disposal inspected; cancellation leaks engine (SOL-014) |
| AC-014 | VERIFIED | CLI parsing/output/error flow and public migration delegation inspected; real CLI-facing helper exercised |
| AC-015 | VERIFIED | Fresh upstream migration on real server and required inventory integration test; provider constraint definitions inspected |
| AC-016 | VERIFIED | Each of four earlier heads seeded with canonical registry definition/revision, upgraded through CLI-facing helper, and compared unchanged |
| AC-017 | VERIFIED | Repeated-head upgrade passed; unknown version rejected and preserved; corrupt rejection inspected |
| AC-018 | VERIFIED | Two registry revisions compared across explicit bundle/engine close and reopen |
| AC-019 | VERIFIED | Canonical CP1 receipt equality across close/reopen; upstream persisted payload/receipt mapping inspected |
| AC-020 | VERIFIED | Same-key/payload receipt after restart; changed payload returned upstream 409 |
| AC-021 | VERIFIED | Eight barrier-synchronized independent engines/stores: one receipt ID, exactly one created result, no raw database error |
| AC-022 | VERIFIED | Restart replay plus persisted upstream cursor produced full event equality/order; scope filtering inspected |
| AC-023 | VERIFIED | Eight barrier-synchronized independent engines appended distinct sequences; replay ordered and unique |
| AC-024 | VERIFIED | Existing real integration test and independent durable-backed firing persisted across close/reopen |
| AC-025 | VERIFIED | Duplicate durable-backed claim returned same firing; native shared-engine atomic transaction and existing-firing early-return inspected |
| AC-026 | VERIFIED | Same exact upstream API/router mount path, existing HTTP/auth/OpenAPI compatibility tests, real pilot app OpenAPI construction |
| AC-027 | NOT SATISFIED | TLS mode absent; configured capabilities disappear when extra absent (SOL-012) |
| AC-028 | PARTIALLY SATISFIED | Stable bounded/redacted rendering and read-only inspection; required TLS-mode fact absent from both formats (SOL-012) |
| AC-029 | VERIFIED | Transactionally consistent custom-format pg_dump restored into another database; readiness passed and every canonical table row compared identical |
| AC-030 | VERIFIED | Original compatibility tests passed before new blocker artifacts |
| AC-031 | VERIFIED | Boundary gate and changed production code inspection; migrations/schema ownership remain upstream |
| AC-032 | VERIFIED | Isolated core/SQLite/PostgreSQL wheel environments and import gate passed |
| AC-033 | PARTIALLY SATISFIED | Exact service and 3.11/3.12/3.13 workflow configured; no executed current-change Actions run supplied (SOL-010 evidence must not claim one) |
| AC-034 | PARTIALLY SATISFIED | Original release command passed, but new behavioral blocker verification fails; see gate classification |
| AC-035 | NOT SATISFIED | Setup/TLS/privileges/migration/cleanup/pilot docs present, but no operator restore/admission procedure (SOL-013) |
| AC-036 | REGRESSED | Recycled 0.3 criterion meanings marked PASS; current checker accepts them (SOL-010) |
| AC-037 | VERIFIED | Published installed provider migration inventory plus fresh and all earlier-head probes |
| AC-038 | VERIFIED | Installed provider PostgreSQL advisory-lock allocator and independent barrier append probe |

The independent probes establish bounded technical behavior, not a substitute
for repairing the repository's reproducible evidence index. Its commands must
identify actual tests or recorded manual procedures, not merely rename tasks.

## Previous blockers

There is no earlier phase 0.4 review/remediation report in the repository.
The preserved phase 0.3 Sol verification artifacts and final fixes were audited.

| Finding | Status | Verification |
|---|---|---|
| SOL-001–SOL-009 | VERIFIED FIXED within their original scope | Existing phase 0.3 blocker tests pass; corresponding settings, compatibility, composition, docs, typing, diagnostics and wheel paths inspected |
| SOL-010 | REGRESSED in the new phase evidence path | Original 0.3 mapping test still passes; new 0.4 mapping test fails for eight distinct current requirements |

## Findings

### SOL-010 — Current evidence gate accepts a recycled acceptance contract

Severity: High. Disposition: BLOCKER. Related AC: AC-002, AC-033, AC-036.

Location: `docs/evidence/0.4/README.md` acceptance table;
`scripts/check_evidence.py` phase-specific proof validation.

Problem/evidence: AC-016 is labelled identity wiring rather than prior-head
upgrade, AC-021 schema safety rather than concurrent submissions, AC-029
preflight rather than backup/restore, and AC-036 SQLite example rather than
evidence. The table largely retains 0.3 meanings. All rows claim PASS/no
limitation. Proof validation only applies its semantic mapping to directory
0.3; the complete original release command therefore accepts this false ledger.

Relationship: the 0.4 implementation copied the prior ledger and extended the
checker without the matching current contract validation. This is the same
mapping root cause as historical SOL-010, not a new finding ID.

Why it matters/blocks this change: AC-036 explicitly requires passing proof
for the current requirements. The required release gate cannot establish
current migration, concurrency or recovery qualification from unrelated tests.

Required behavior/acceptance for resolution: all 38 rows match the approved
0.4 meanings and identify actual executable or recorded manual proof, including
limitations and actual environments/server versions. The checker rejects
mis-mapped current-phase evidence. Do not claim Actions/Python executions that
did not occur. Preserve the existing 0.3 contract check.

Verification artifact: `test_sol_010_phase_0_4_evidence_matches_current_ac_meanings`.
Status: fails as expected for AC-002/016/018/021/023/025/029/036. This necessary
topic check is not sufficient proof on its own: remediation must link actual
behavioral verification, not keyword-only edits.

### SOL-011 — Bundle exposes a different definition repository than the API

Severity: Medium. Disposition: BLOCKER. Related AC: AC-008, AC-009.

Location: `src/shuetl/providers.py`, PostgreSQL graph construction.

Problem/evidence: construction makes `RegistryDefinitionRepository(registry)`
for the bundle, then `ETLanticAPI.with_registry_definitions` makes another
repository. Both share the registry, but `bundle.definitions is
bundle.api.definitions` is false. Confirmed with the real PostgreSQL graph and
an isolated wiring test using genuine upstream types.

Relationship: introduced by the new graph. Why it matters/blocks this change:
the approved public contract promises the exposed stores are the same objects
in the API, not merely equivalent repositories. Callers cannot treat the
bundle as the authoritative graph as documented.

Required behavior/acceptance for resolution: exactly one canonical upstream
registry-backed definition repository is retained by both bundle and API,
without a wrapper; preserve all other provider/engine/caller identities.

Verification artifact: `test_sol_011_bundle_definitions_are_the_api_definitions`.
Status: fails at object identity for the expected reason.

### SOL-012 — Doctor omits required TLS and configured-provider facts

Severity: Medium. Disposition: BLOCKER. Related AC: AC-027, AC-028 and the
approved security/doctor contract.

Location: `src/shuetl/diagnostics.py`, capability selection and check summaries.

Problem/evidence: explicit `sslmode=disable` is absent from JSON and text.
Configured registry/revisions/durable-work/schedules/firings are added only
when the optional dependencies are installed, so missing-extra diagnostics
misdescribe the selected graph. No connection occurs in the missing-extra test.

Relationship: new pilot diagnostic composition. Why it matters/blocks this
change: the contract explicitly makes insecure TLS opt-in visible and
distinguishes configured capabilities from available dependencies. Operators
currently cannot audit this security setting and receive incorrect remediation
facts about the configured topology.

Required behavior/acceptance for resolution: both renderings contain the
bounded selected TLS mode, including explicit disable/require/verify-ca;
configured pilot capabilities do not depend on package availability;
provider availability remains exact-version-gated. Keep doctor/1 fields and
existing check IDs/order, redaction, and no-connection missing-extra behavior.

Verification artifacts: both `test_sol_012_*` tests. Status: both fail for the
expected missing facts.

### SOL-013 — Operator documentation has no restore/admission procedure

Severity: Medium. Disposition: BLOCKER. Related AC: AC-035.

Location: README PostgreSQL operations section and operator-facing docs.

Problem/evidence: backup inputs are named, but operator-facing documentation
does not mention restore. Restore appears only in the implementation plan and
the evidence index's out-of-scope automation disclaimer. The independent
dump/restore probe succeeds, so this is not an alleged database data-loss bug.

Relationship: required operational documentation omitted by the current
change. Why it matters/blocks this change: AC-035 and the security contract
require a restore procedure with read-only readiness/restart verification
before admitting traffic. Excluding backup automation does not exclude this.

Required behavior/acceptance for resolution: an operator-facing, referenced
procedure explains consistent canonical-table backup, separate operator inputs,
restore into an appropriate database, and compatibility/identity verification
before traffic. Document failure admission behavior and pilot limitations;
verify the documented procedure against PostgreSQL 18.6.

Verification artifact: `test_sol_013_operator_documentation_explains_restore_admission`.
Status: fails because no operator-facing restore procedure exists. Manual
review of the finished runbook remains required beyond the necessary topic test.

### SOL-014 — Cancelled bundle construction does not dispose its engine

Severity: Medium. Disposition: BLOCKER. Related AC: AC-013.

Location: `src/shuetl/providers.py`, PostgreSQL construction exception cleanup.

Problem/evidence: cleanup catches named exceptions and `Exception`, but
`asyncio.CancelledError` derives from `BaseException`. Injecting cancellation
after engine creation propagates cancellation with zero calls to dispose.

Relationship: new bundle failure lifecycle. Why it matters/blocks this change:
the approved edge-case/invariant contract explicitly requires disposal on
cancelled construction and no partial returned graph. Ordinary-error cleanup
does not satisfy that requirement.

Required behavior/acceptance for resolution: dispose the created engine
exactly once on cancelled construction, propagate cancellation unchanged,
retain redacted ordinary errors, and preserve successful explicit close.
Do not convert cancellation into a compatibility/readiness error.

Verification artifact: `test_sol_014_cancelled_construction_disposes_engine_once`.
Status: fails because dispose was called zero times.

## Quality gates

| Gate | Executed | Result / classification |
|---|---|---|
| Full `scripts/check_release.py` before review additions | Yes | PASS, including lock/sync/format/lint/type/boundary/tests/build/artifact/OpenAPI/three isolated wheel environments/evidence |
| Original tests | Yes | 97 passed, 3 PostgreSQL tests skipped without URL |
| Existing PostgreSQL integration suite on real 18.6 | Yes | 3 passed |
| Independent prior-head/restart/barrier/recovery probes | Yes | PASS as described in AC table; actual upstream cursor used, not event ID |
| Format, Ruff, Pyright, boundary after review tests | Yes | PASS |
| New blocker verification | Yes | 6 failed for the expected reasons across 5 blockers: EXPECTED BLOCKER VERIFICATION |
| Complete suite after review tests | Yes | 96 passed, 3 skipped, 7 failed |
| Additional complete-suite failure | Yes | Existing fresh-build sdist hash assertion now fails because new verification artifacts change source contents; wheel hash unchanged. REVIEW-VERIFICATION-INDUCED, not a separate production blocker; refresh artifact evidence during normal remediation |
| Current-change live Actions matrix | No | Workflow inspected, execution not claimed |

No required gates were disabled or tests weakened. The initial green release
gate did not detect the semantic evidence error or the uncovered behavior.

## Follow-ups and observations

No new substantive unrelated defects warrant another issue in this review.
Existing open GitHub issues were inspected; neither enters remediation:

| Finding | Severity | GitHub |
|---|---|---|
| Pre-existing Actions runtime deprecation | Low | EXISTING ISSUE #1 |
| Historical TestClient transport migration | Low | EXISTING ISSUE #2 |

Observation: the active suite emits an AnyIO BlockingPortal deprecation warning.
It does not fail a gate or demonstrate an in-scope behavioral defect.

## Convergence

Nine historical blocker IDs remain resolved within their original contract.
SOL-010 recurs in the new evidence path. Five current blocker IDs remain;
four are new current-change findings, none attributable to a phase 0.4
remediation attempt (none is recorded yet). No new follow-up issues were needed.
The technical PostgreSQL qualification probes passed and the remaining work is
bounded. No repeated phase 0.4 implementation-attempt failure is established,
so escalation is not yet warranted. Only SOL-010–SOL-014 enter remediation.

NEEDS FIXES
