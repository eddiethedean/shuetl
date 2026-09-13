# Phase 0.4 evidence index

This index records reproducible evidence for the PostgreSQL pilot and migration
boundary.  The release train is ETLantic 0.52.1 and the qualified PostgreSQL
server is 18.6.

## Published artifacts

ShuETL [0.4.0](https://pypi.org/project/shuetl/0.4.0/) was published on
2026-09-13 from tag `v0.4.0`, commit
`69f140f6f7343cc6e2bdbb97c34dba3d4eb324e0`. Both pre-tag CI and the
tag-triggered release workflow passed; see the [publication record](ci.md#published-release).

| Published PyPI file | SHA-256 |
| --- | --- |
| `shuetl-0.4.0-py3-none-any.whl` | `5a8ac20eab3553cc3fe65a815808f6e4fd4d0b7cea412dc3b47880e23bd170e9` |
| `shuetl-0.4.0.tar.gz` | `967a61fbea2937549e00b2e3b8984b95da6f4cd205febf3723ddd1e230be5efe` |

## Working-tree qualification

The build hashes below track deterministic builds of the current repository,
including post-release documentation updates. They are not replacements for
the immutable published artifact hashes above.

| Field | Value |
| --- | --- |
| OS and architecture | macOS arm64 (local); Ubuntu 24.04.5 x86_64 (CI executed) |
| Python version | 3.12.13 local; CI Python 3.11, 3.12 and 3.13 executed; see ci.md |
| uv version | 0.11.3 |
| ETLantic source revision | 0.52.1 package |
| ShuETL import origin | installed project package |
| ETLantic import origin | installed package |
| etlantic-fastapi import origin | installed package |
| FastAPI import origin | installed package |
| Pydantic import origin | installed package |
| HTTPX import origin | httpx2 test extra |
| Gate A | PASS |
| Gate B | PASS |
| Gate C | PASS |
| SHA-256 wheel | `23680c84a59149a4f81fe2e4e36dcdf678ac2055298c5954b7aa4d2836901d42` |
| SHA-256 sdist | `4af522c56017018e52bd383f29e01f05a972536dd211e36c7d58691b9c23c837` |

## Acceptance results

Proof bindings are audited in `proofs.json`; each artifact identifies a specific
section in `qualification.md` with procedure, result and source provenance.
Recorded review references are not newly executed test commands. AC-033 now
records the successful current-change CI matrix in `ci.md`, including its
tested source commit, live PostgreSQL results and primary job links.

| Criterion | Task | Command | Artifact | Status | Limitation | Reviewer | Date |
| --- | --- | --- | --- | --- | --- | --- | --- |
| AC-001 | metadata | `uv run python scripts/check_artifact.py` | `qualification.md#ac-001` | PASS | local Python 3.12; see qualification record | implementation / Sol record | 2026-09-13 |
| AC-002 | server 18.6 | `uv run pytest tests/integration/test_postgresql.py::test_schema_head_graph_and_doctor -q` | `qualification.md#ac-002` | PASS | local Python 3.12; see qualification record | implementation / Sol record | 2026-09-13 |
| AC-003 | public exports | `uv run pytest tests/unit/test_package.py -q` | `qualification.md#ac-003` | PASS | local Python 3.12; see qualification record | implementation / Sol record | 2026-09-13 |
| AC-004 | profile/provider combinations | `Recorded review: tests/review/PHASE_0_4_REVIEW.md#acceptance-criteria (AC-004, 2026-09-13)` | `qualification.md#ac-004` | PASS | prior independent review; not rerun in remediation | independent Sol record | 2026-09-13 |
| AC-005 | URL/TLS validation | `Recorded review: tests/review/PHASE_0_4_REVIEW.md#acceptance-criteria (AC-005, 2026-09-13)` | `qualification.md#ac-005` | PASS | prior independent review; not rerun in remediation | independent Sol record | 2026-09-13 |
| AC-006 | optional imports | `Recorded review: tests/review/PHASE_0_4_REVIEW.md#acceptance-criteria (AC-006, 2026-09-13)` | `qualification.md#ac-006` | PASS | prior independent review; not rerun in remediation | independent Sol record | 2026-09-13 |
| AC-007 | host adapters | `Recorded review: tests/review/PHASE_0_4_REVIEW.md#acceptance-criteria (AC-007, 2026-09-13)` | `qualification.md#ac-007` | PASS | prior independent review; not rerun in remediation | independent Sol record | 2026-09-13 |
| AC-008 | registry-backed objects | `uv run pytest tests/review/test_phase_0_4_contract.py::test_sol_011_bundle_definitions_are_the_api_definitions -q` | `qualification.md#ac-008` | PASS | local Python 3.12; see qualification record | implementation / Sol record | 2026-09-13 |
| AC-009 | production API caller objects | `Recorded review: tests/review/PHASE_0_4_RE_REVIEW_2.md#acceptance-criteria (AC-009, 2026-09-13)` | `qualification.md#ac-009` | PASS | prior independent review; not rerun in remediation | independent Sol record | 2026-09-13 |
| AC-010 | schema state matrix | `Recorded review: tests/review/PHASE_0_4_REVIEW.md#acceptance-criteria (AC-010, 2026-09-13)` | `qualification.md#ac-010` | PASS | prior independent review; not rerun in remediation | independent Sol record | 2026-09-13 |
| AC-011 | head required tables | `uv run pytest tests/integration/test_postgresql.py::test_schema_head_graph_and_doctor -q` | `qualification.md#ac-011` | PASS | local Python 3.12; see qualification record | implementation / Sol record | 2026-09-13 |
| AC-012 | read-only no writes | `Recorded review: tests/review/PHASE_0_4_REVIEW.md#acceptance-criteria (AC-012, 2026-09-13)` | `qualification.md#ac-012` | PASS | prior independent review; not rerun in remediation | independent Sol record | 2026-09-13 |
| AC-013 | cancellation disposal | `uv run pytest tests/review/test_phase_0_4_contract.py::test_sol_014_cancelled_construction_disposes_engine_once -q` | `qualification.md#ac-013` | PASS | local Python 3.12; see qualification record | implementation / Sol record | 2026-09-13 |
| AC-014 | database upgrade CLI | `Recorded review: tests/review/PHASE_0_4_REVIEW.md#acceptance-criteria (AC-014, 2026-09-13)` | `qualification.md#ac-014` | PASS | prior independent review; not rerun in remediation | independent Sol record | 2026-09-13 |
| AC-015 | fresh migration tables | `uv run pytest tests/integration/test_postgresql.py::test_schema_head_graph_and_doctor -q` | `qualification.md#ac-015` | PASS | local Python 3.12; see qualification record | implementation / Sol record | 2026-09-13 |
| AC-016 | earlier head upgrade | `Recorded review: tests/review/PHASE_0_4_REVIEW.md#acceptance-criteria (AC-016, 2026-09-13)` | `qualification.md#ac-016` | PASS | prior independent review; not rerun in remediation | independent Sol record | 2026-09-13 |
| AC-017 | repeat head unknown corrupt | `Recorded review: tests/review/PHASE_0_4_REVIEW.md#acceptance-criteria (AC-017, 2026-09-13)` | `qualification.md#ac-017` | PASS | prior independent review; not rerun in remediation | independent Sol record | 2026-09-13 |
| AC-018 | revisions restart | `Recorded review: tests/review/PHASE_0_4_REVIEW.md#acceptance-criteria (AC-018, 2026-09-13)` | `qualification.md#ac-018` | PASS | prior independent review; not rerun in remediation | independent Sol record | 2026-09-13 |
| AC-019 | CP1 submission restart | `Recorded review: tests/review/PHASE_0_4_REVIEW.md#acceptance-criteria (AC-019, 2026-09-13)` | `qualification.md#ac-019` | PASS | prior independent review; not rerun in remediation | independent Sol record | 2026-09-13 |
| AC-020 | idempotency conflict restart | `Recorded review: tests/review/PHASE_0_4_REVIEW.md#acceptance-criteria (AC-020, 2026-09-13)` | `qualification.md#ac-020` | PASS | prior independent review; not rerun in remediation | independent Sol record | 2026-09-13 |
| AC-021 | concurrent submission | `Recorded review: tests/review/PHASE_0_4_REVIEW.md#acceptance-criteria (AC-021, 2026-09-13)` | `qualification.md#ac-021` | PASS | prior independent review; not rerun in remediation | independent Sol record | 2026-09-13 |
| AC-022 | event cursor restart | `Recorded review: tests/review/PHASE_0_4_REVIEW.md#acceptance-criteria (AC-022, 2026-09-13)` | `qualification.md#ac-022` | PASS | prior independent review; not rerun in remediation | independent Sol record | 2026-09-13 |
| AC-023 | concurrent event ordered | `uv run pytest tests/integration/test_postgresql.py::test_concurrent_event_appends_have_unique_sequences -q` | `qualification.md#ac-023` | PASS | local Python 3.12; see qualification record | implementation / Sol record | 2026-09-13 |
| AC-024 | schedule firing restart | `Recorded review: tests/review/PHASE_0_4_REVIEW.md#acceptance-criteria (AC-024, 2026-09-13)` | `qualification.md#ac-024` | PASS | prior independent review; not rerun in remediation | independent Sol record | 2026-09-13 |
| AC-025 | duplicate firing durable | `Recorded review: tests/review/PHASE_0_4_REVIEW.md#acceptance-criteria (AC-025, 2026-09-13)` | `qualification.md#ac-025` | PASS | prior independent review; not rerun in remediation | independent Sol record | 2026-09-13 |
| AC-026 | mounted routes auth OpenAPI | `uv run pytest tests/integration/test_phase_0_2_contract.py -q` | `qualification.md#ac-026` | PASS | local Python 3.12; see qualification record | implementation / Sol record | 2026-09-13 |
| AC-027 | doctor versions capabilities | `uv run pytest tests/integration/test_postgresql.py::test_schema_head_graph_and_doctor -q` | `qualification.md#ac-027` | PASS | local Python 3.12; see qualification record | implementation / Sol record | 2026-09-13 |
| AC-028 | text JSON redaction TLS | `uv run pytest tests/review/test_phase_0_4_contract.py -q` | `qualification.md#ac-028` | PASS | local Python 3.12; see qualification record | implementation / Sol record | 2026-09-13 |
| AC-029 | backup restore readiness | `Recorded review: tests/review/PHASE_0_4_RE_REVIEW_2.md#acceptance-criteria (AC-029, 2026-09-13)` | `qualification.md#ac-029` | PASS | prior independent review; not rerun in remediation | independent Sol record | 2026-09-13 |
| AC-030 | compatibility suite | `uv run pytest -q` | `qualification.md#ac-030` | PASS | local Python 3.12; see qualification record | implementation / Sol record | 2026-09-13 |
| AC-031 | boundary ownership | `uv run python scripts/check_boundaries.py --openapi docs/evidence/0.4/openapi.normalized.json` | `qualification.md#ac-031` | PASS | local Python 3.12; see qualification record | implementation / Sol record | 2026-09-13 |
| AC-032 | wheel dependencies imports | `uv run python scripts/check_clean_wheel.py` | `qualification.md#ac-032` | PASS | local Python 3.12; see qualification record | implementation / Sol record | 2026-09-13 |
| AC-033 | CI Python server | `gh run view 34776217942 --json headSha,status,conclusion,jobs` | `qualification.md#ac-033` | PASS | qualifies recorded source revision; see ci.md for tested commit | GitHub Actions execution | 2026-09-13 |
| AC-034 | quality gates | `uv run python scripts/check_release.py` | `qualification.md#ac-034` | PASS | local Python 3.12 gate; live PostgreSQL qualified separately | implementation / Sol record | 2026-09-13 |
| AC-035 | operator docs restore example | `Recorded review: tests/review/PHASE_0_4_RE_REVIEW_2.md#acceptance-criteria (AC-035, 2026-09-13)` | `qualification.md#ac-035` | PASS | prior independent review; not rerun in remediation | independent Sol record | 2026-09-13 |
| AC-036 | evidence mapping | `uv run python scripts/check_evidence.py --evidence docs/evidence/0.4` | `qualification.md#ac-036` | PASS | local Python 3.12; see qualification record | implementation / Sol record | 2026-09-13 |
| AC-037 | migration 0.52 | `Recorded review: tests/review/PHASE_0_4_REVIEW.md#acceptance-criteria (AC-037, 2026-09-13)` | `qualification.md#ac-037` | PASS | prior independent review; not rerun in remediation | independent Sol record | 2026-09-13 |
| AC-038 | concurrent event 0.52 | `uv run pytest tests/integration/test_postgresql.py::test_concurrent_event_appends_have_unique_sequences -q` | `qualification.md#ac-038` | PASS | local Python 3.12; see qualification record | implementation / Sol record | 2026-09-13 |

## Gap register

TLS certificate verification, backup/restore automation, HA, and production
migration orchestration remain explicitly outside the pilot boundary. The
boundary outcome is **proceed-to-0.4** for the qualified PostgreSQL pilot: the
integration burden stays in ShuETL's composition layer, public composition hooks
remain injected, no copied route or pipeline model is introduced, and
the design is materially easier to maintain than a parallel control-plane
implementation. No behavior is contributed to `etlantic-fastapi`.
