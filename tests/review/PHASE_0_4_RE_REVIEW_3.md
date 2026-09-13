# Phase 0.4 production re-review — third remediation audit

Date: 2026-09-13. Verdict: NEEDS FIXES.

Authority: `docs/plans/PHASE_0_4_EXECUTION.md`, ADR-0010 and AC-001–AC-038.
Baseline: released 0.3 commit `f5806beedaa5545061279347125a609c26665c7b`.
The latest implementation resolution report is the preceding conversation.
The approved PostgreSQL pilot scope and exclusions are unchanged. This review
adds only this report and one SOL-010 verification artifact. Production code,
evidence, documentation, configuration and previous verification are untouched.

## Acceptance criteria

Evidence combines fresh local gates and code inspection with the independently
executed runtime qualification recorded in `PHASE_0_4_REVIEW.md` and audited in
`PHASE_0_4_RE_REVIEW_2.md`. Earlier-head/revision/cursor/barrier/restore probes
were not all rerun here. Fresh execution used Python 3.12.13, macOS arm64,
locked published providers and disposable PostgreSQL 18.6. No Python 3.11/3.13
or current-change Actions execution is claimed.

| AC | Status | Evidence |
|---|---|---|
| AC-001 | VERIFIED | Fresh metadata, lock, artifact and isolated-wheel gates |
| AC-002 | VERIFIED | Fresh real integration asserts server 18.6 |
| AC-003 | VERIFIED | Exact exports and installed-wheel import gates |
| AC-004 | VERIFIED | Actual settings Literal and validate_provider_url matrix; existing tests |
| AC-005 | VERIFIED | Structural URL/TLS/SecretStr validation inspection and retained compatibility tests |
| AC-006 | VERIFIED | Exact metadata qualification precedes lazy optional imports/engine construction |
| AC-007 | VERIFIED | Exact settings type and explicit conforming host adapters |
| AC-008 | VERIFIED | Protected SOL-011 test, native shared-engine graph and fresh live construction |
| AC-009 | VERIFIED | Direct native production API retains bundle/caller objects; no invented providers |
| AC-010 | VERIFIED | Original real state probes and unchanged bounded classifier inspection |
| AC-011 | VERIFIED | Fresh head/inventory assertion and prior missing-table rejection probe |
| AC-012 | VERIFIED | Prior PostgreSQL catalog comparison, explicit read-only transaction and unchanged facade paths |
| AC-013 | VERIFIED | Protected cancellation verification and locked idempotent disposal inspection |
| AC-014 | VERIFIED | Actual cli.main directly calls upgrade_postgresql; bounded output/exit flow and prior real helper qualification |
| AC-015 | VERIFIED | Fresh public provider migration/inventory and prior constraint inspection |
| AC-016 | VERIFIED | Original seeded all-four-head runtime qualification; current ledger's reconstructed head names are wrong under AC-036 |
| AC-017 | VERIFIED | Prior repeat-head/unknown preservation probes and unchanged fail-closed path |
| AC-018 | VERIFIED | Original two-immutable-revision comparison across closed/reopened engines |
| AC-019 | VERIFIED | Original full canonical CP1 receipt restart comparison |
| AC-020 | VERIFIED | Original post-restart same-key result and changed-payload upstream 409 |
| AC-021 | VERIFIED | Original eight-party independent-engine submission barrier qualification |
| AC-022 | VERIFIED | Original full event replay and actual persisted-cursor restart proof |
| AC-023 | VERIFIED | Original independent barrier and fresh persistent event-sequence integration |
| AC-024 | VERIFIED | Prior durable-backed restart and fresh schedule/firing persistence integration |
| AC-025 | VERIFIED | Original durable-backed duplicate firing claim and native atomic early-return inspection |
| AC-026 | VERIFIED | Unchanged upstream mounting/API path, HTTP/auth/SSE/OpenAPI gates and fresh pilot OpenAPI construction |
| AC-027 | VERIFIED | Protected capability/TLS tests, retained doctor/1 contract and fresh real doctor assertions |
| AC-028 | VERIFIED | Protected bounded/redacted rendering tests plus read-only inspection |
| AC-029 | VERIFIED | Prior full canonical-row native dump/restore equality and restored readiness; procedure/provenance now locatable |
| AC-030 | VERIFIED | Fresh complete compatibility suite and separate real PostgreSQL integration |
| AC-031 | VERIFIED | Fresh boundary gate and unchanged upstream schema/store ownership |
| AC-032 | VERIFIED | Fresh separate installed core/SQLite/PostgreSQL wheel environments |
| AC-033 | PARTIALLY SATISFIED | Correct matrix configured; GitHub runs inspected cover released 0.3 HEAD, not uncommitted 0.4 changes |
| AC-034 | PARTIALLY SATISFIED | Baseline complete release gate passes; new factual-proof verification fails as intended |
| AC-035 | VERIFIED | Operator setup/restore/admission topics, protected doc test and prior corrected native runbook execution |
| AC-036 | PARTIALLY SATISFIED | Registry/reference binding fixed, but recorded procedure contains nonexistent migration heads and CLI helper |
| AC-037 | VERIFIED | Published provider VERSIONS inspected; fresh migration plus original seeded older-head runtime proof |
| AC-038 | VERIFIED | Published native allocator, original independent barrier and fresh concurrent-event integration |

## Previous blockers

| Finding | Status | Verification |
|---|---|---|
| SOL-010 | PARTIALLY FIXED | Topic/empty/unrelated-proof checks pass; manual-record audit and new factual verification fail |
| SOL-011 | VERIFIED FIXED | Protected identity assertion passes; one canonical definition object retained |
| SOL-012 | VERIFIED FIXED | Both protected tests pass; configured facts remain truthful and bounded |
| SOL-013 | VERIFIED FIXED | Protected operator-doc test passes; corrected native URL separation and prior populated restore proof retained |
| SOL-014 | VERIFIED FIXED | Protected cancellation test passes; BaseException cleanup propagates cancellation unchanged |

SOL-001–SOL-009 remain verified fixed within their original 0.3 scope. Their
protected tests pass. No existing verification was weakened, deleted or skipped.

## Open finding

### SOL-010 — Reconstructed manual proof still contains nonexistent inputs

Severity: Medium (the broad arbitrary-proof acceptance is fixed; the remaining
defect is factual integrity of the required evidence record).

Disposition: BLOCKER.

Related AC: AC-036; AC-033 remains a separate execution-evidence limitation
already recorded throughout this finding's history.

Location: `docs/evidence/0.4/qualification.md:206` (AC-016) and `:182` (AC-014).

Problem: the new registry correctly binds rows to particular recorded proof,
independently of Task labels. Most formerly unrelated references now identify
the actual independent review and an assessable procedure. However, its manual
reconstruction names two migration heads that do not exist and traces a CLI
helper that is absent from the implementation. The record is marked PASS and
the consistency checker accepts it because references and strings match.

Evidence: installed published `etlantic_sqlmodel.migrations.VERSIONS` is:

```text
001_registry_cp2
002_durable_cp3
003_cp4_governance
004_schedules_0_47
005_cp1_reference
```

The reconstructed procedure instead names `001_registry_m1` and `002_cp3`.
The actual production allowlist agrees with published VERSIONS. The original
Sol report records all four earlier-head probes but does not provide those
incorrect names. Likewise, cli.main calls upgrade_postgresql directly; there
is no `_database_upgrade` helper named by the reconstructed trace.

The new verification fails with exactly:

```text
heads=['001_registry_m1', '002_cp3'], CLI symbols=['_database_upgrade']
```

Relationship to current change: these inaccurate details were introduced by
the latest evidence remediation. This is the remaining proof-fidelity portion
of SOL-010, not a new runtime migration defect or a new scope requirement.

Why it matters: an assessor following the named fixture inputs cannot perform
the claimed recognized-head procedure, and the stated execution trace cannot
be inspected as written. A green string/reference check is not semantic proof.

Why this blocks the current change: AC-036 requires relevant assessable passing
proof. The approved SOL-010 resolution specifically required grounded recorded
procedures/provenance, rather than an invented reconstruction accepted by the
gate. This contradiction is within the sticky evidence boundary.

Required behavior: correct the manual proof to the actual published versions
and execution path, or reference the adequate original independent evidence
without adding false details. Audit other reconstructed specifics for the same
issue. Do not rerun equivalent runtime probes solely to increase test count,
redesign production code, or replace a human evidence audit with keyword checks.

Acceptance criteria: any explicitly named provider revision exists in the
qualified published VERSIONS, any explicitly named CLI trace symbol exists in
the referenced source, and the record faithfully distinguishes prior results,
new execution and CI configuration. Current-change CI execution is still needed
for AC-033 before a full PASS; previous released-0.3 runs do not satisfy it.

Verification artifact:
`test_phase_0_4_manual_proof_contract.py::test_sol_010_recorded_upgrade_identifiers_are_real`.
The check constrains facts explicitly asserted by the proof; it does not demand
a particular private helper layout or force named revisions into the prose.

Verification status: EXPECTED BLOCKER VERIFICATION — confirmed failing for the
exact nonexistent names above. Earlier protected SOL-010 checks pass.

ESCALATION RECOMMENDED: SOL-010 has survived multiple attempts. The remaining
work is a code/package-grounded evidence audit and external CI qualification,
not an architectural redesign. The latest remediation made substantive progress
on binding integrity but reconstructed details without checking actual symbols.

## Quality gates

| Gate | Executed | Result / classification |
|---|---|---|
| Complete release gate before new verification/report | Yes | PASS: 112 passed, 3 PostgreSQL skips; lock/sync/Ruff/Pyright/boundary/build/artifact/OpenAPI/three isolated wheels/evidence |
| Existing protected suites plus implementation proof tests | Yes | 43 passed |
| Fresh real PostgreSQL integration on 18.6 | Yes | 3 passed; isolated disposable database, service stopped afterward |
| Published migration VERSIONS and actual CLI trace audit | Yes | FAIL — CHANGE-CAUSED factual evidence defect, SOL-010 |
| New SOL-010 verification | Yes | FAIL — EXPECTED BLOCKER VERIFICATION |
| Complete suite after new verification/report | Yes | 111 passed, 3 skipped, 2 failed: expected SOL-010 verification and review-induced stale sdist hash |
| Ruff format/lint, Pyright and diff whitespace after verification | Yes | PASS |
| Current-change Actions matrix | No | Existing successful runs only cover 0.3 baseline; execution not claimed |

New verification/report files alter sdist inputs. Normal remediation must
refresh artifact evidence; this review does not edit hashes or bypass the
fresh-build hash assertion. Prior manual restore/barrier/revision probes are
retained provenance, not claimed as executions in this re-review.

## Follow-ups, observations and convergence

Open GitHub issues were searched. Existing low-severity follow-ups #1 (Actions
Node.js runtime) and #2 (historical TestClient transport) remain outside scope.
No new follow-up was found or created. The existing non-failing BlockingPortal
deprecation warning remains an observation.

No new finding ID or runtime blocker is introduced. Four of five Phase 0.4
blockers remain verified fixed; one remains partially fixed. The loop is
converging: registry/reference integrity is now fixed, and remaining factual
record repair is small and explicit. CI execution evidence is still pending.
Hand back only SOL-010, not unrelated follow-ups or production refactoring.

NEEDS FIXES
