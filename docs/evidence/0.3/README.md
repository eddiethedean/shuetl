# Phase 0.3 evidence index

This index records the reproducible local proof for the Phase 0.3 contract.

| Field | Value |
| --- | --- |
| OS and architecture | macOS arm64 |
| Python version | 3.12 |
| uv version | 0.11.3 |
| ETLantic source revision | 0.51.0 package |
| ShuETL import origin | installed project package |
| ETLantic import origin | installed package |
| etlantic-fastapi import origin | installed package |
| FastAPI import origin | installed package |
| Pydantic import origin | installed package |
| HTTPX import origin | httpx2 test extra |
| Gate A | PASS |
| Gate B | PASS |
| Gate C | PASS |
| SHA-256 wheel | `737792f2f4583c6c4f4bb9aee3d6ed32521d7f641bb1dab2c209accdd8c30cbc` |
| SHA-256 sdist | `d913f36299b8f6a8267a052f32e19086ae160c88e60b59c5707513a74cbc8d8d` |

## Acceptance results

| Criterion | Task | Command | Artifact | Status | Limitation | Reviewer | Date |
| --- | --- | --- | --- | --- | --- | --- | --- |
| AC-001 | package metadata | artifact check | pyproject and wheel metadata | PASS | none | implementation | 2026-09-11 |
| AC-002 | exact public exports | pytest; clean wheel | package and installed wheel | PASS | none | implementation | 2026-09-11 |
| AC-003 | settings schema | pytest | model contract | PASS | none | implementation | 2026-09-11 |
| AC-004 | required fail-closed settings | pytest | omission matrix | PASS | none | implementation | 2026-09-11 |
| AC-005 | settings precedence | pytest | constructor and environment matrix | PASS | none | implementation | 2026-09-11 |
| AC-006 | disabled settings sources and dotenv | pytest | source-isolation tests | PASS | none | implementation | 2026-09-11 |
| AC-007 | prefix and route preset | pytest | settings and facade contract | PASS | none | implementation | 2026-09-11 |
| AC-008 | cross-field combinations | pytest | settings validation matrix | PASS | none | implementation | 2026-09-11 |
| AC-009 | provider timeout bounds | pytest | numeric boundary matrix | PASS | none | implementation | 2026-09-11 |
| AC-010 | secret redaction | pytest; evidence scan | settings, CLI, and evidence | PASS | none | implementation | 2026-09-11 |
| AC-011 | core compatibility | pytest | metadata mismatch tests | PASS | none | implementation | 2026-09-11 |
| AC-012 | ETLantic train compatibility | pytest | installed distribution inventory | PASS | none | implementation | 2026-09-11 |
| AC-013 | SQLite extra capability | pytest; clean wheel | core-only capability failure | PASS | none | implementation | 2026-09-11 |
| AC-014 | bundle input adapters | pytest; pyright | input validation contract | PASS | none | implementation | 2026-09-11 |
| AC-015 | memory stores and API | pytest | upstream runtime types | PASS | none | implementation | 2026-09-11 |
| AC-016 | identity and profile wiring | pytest | exact-object composition | PASS | none | implementation | 2026-09-11 |
| AC-017 | optional providers absent | pytest | upstream API provider fields | PASS | none | implementation | 2026-09-11 |
| AC-018 | bundle isolation | pytest | independent graph construction | PASS | none | implementation | 2026-09-11 |
| AC-019 | SQLite file readiness | pytest | URL and filesystem snapshots | PASS | none | implementation | 2026-09-11 |
| AC-020 | SQLModel stores and shared engine | pytest; SQLite example | qualified SQLite bundle | PASS | none | implementation | 2026-09-11 |
| AC-021 | schema failures and no migrations | pytest | read-only schema tests | PASS | none | implementation | 2026-09-11 |
| AC-022 | cleanup and disposal | pytest | failure and idempotent close tests | PASS | none | implementation | 2026-09-11 |
| AC-023 | 0.2 facade compatibility | pytest | unchanged facade suite | PASS | none | implementation | 2026-09-11 |
| AC-024 | HTTP provider parity | pytest; OpenAPI | integration suite and normalized contract | PASS | none | implementation | 2026-09-11 |
| AC-025 | doctor diagnostic models | pytest | frozen model and schema contract | PASS | none | implementation | 2026-09-11 |
| AC-026 | doctor diagnostic facts | pytest | memory and SQLite reports | PASS | none | implementation | 2026-09-11 |
| AC-027 | doctor version inventory | pytest | exact and mismatched package fixtures | PASS | none | implementation | 2026-09-11 |
| AC-028 | doctor capability truthfulness | pytest | provider capability matrix | PASS | none | implementation | 2026-09-11 |
| AC-029 | provider preflight side effects | pytest | readiness and no-startup-mutation tests | PASS | none | implementation | 2026-09-11 |
| AC-030 | doctor schema status | pytest | memory skip and SQLite head checks | PASS | none | implementation | 2026-09-11 |
| AC-031 | doctor check order | pytest | deterministic check contract | PASS | none | implementation | 2026-09-11 |
| AC-032 | doctor text, JSON, and redaction | pytest | rendering equivalence and sentinel scans | PASS | none | implementation | 2026-09-11 |
| AC-033 | doctor CLI | pytest; clean wheel | formats and exit-code matrix | PASS | none | implementation | 2026-09-11 |
| AC-034 | version CLI | pytest; clean wheel | isolated wheel command | PASS | none | implementation | 2026-09-11 |
| AC-035 | memory quickstart | clean-wheel script | authenticated installed-wheel example | PASS | none | implementation | 2026-09-11 |
| AC-036 | SQLite example | clean-wheel script | upstream provisioning and cleanup | PASS | none | implementation | 2026-09-11 |
| AC-037 | boundary rules | boundary checker; pytest | source scan and negative fixtures | PASS | none | implementation | 2026-09-11 |
| AC-038 | OpenAPI parity | capture script | normalized 0.2 contract | PASS | none | implementation | 2026-09-11 |
| AC-039 | artifact and clean installs | artifact and clean-wheel scripts | wheel, sdist, core, and SQLite environments | PASS | none | implementation | 2026-09-11 |
| AC-040 | release gate and Python matrix | check_release; checks workflow | Python 3.11, 3.12, and 3.13 | PASS | none | implementation | 2026-09-11 |
| AC-041 | user documentation | review; pytest | README and executable examples | PASS | none | implementation | 2026-09-11 |
| AC-042 | evidence index | evidence checker; pytest | AC map, hashes, and redaction scan | PASS | none | implementation | 2026-09-11 |

## Gap register

No Phase 0.3 implementation gaps were identified. Follow-up maintenance remains
tracked separately for the existing CI Node 20 and Starlette warnings.

The boundary review outcome is **proceed-to-0.2** for the previously published
facade contract; Phase 0.3 adds local composition without changing upstream
routes or semantics. The integration burden remains in ShuETL's composition
layer, while public composition hooks stay injected and no copied route or
pipeline model is introduced. This is materially easier to maintain than a
parallel control-plane implementation and no behavior is contributed to `etlantic-fastapi`.
