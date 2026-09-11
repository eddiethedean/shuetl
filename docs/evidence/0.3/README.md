# Phase 0.3 evidence index

This index records the reproducible local proof for the Phase 0.3 contract.

| Field | Value |
| --- | --- |
| OS and architecture | macOS arm64 |
| Python version | 3.12 |
| uv version | recorded by the gate |
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
| SHA-256 wheel | `e89ae02c97d9f36707dab294709410d518a8f2a16f0dac5b4ee12c77ba4f32f3` |
| SHA-256 sdist | `fdfda5cb4dd997b0a6c78d983f39de1d5ddfb8f8a278c7f40e883a8bd762f218` |

## Acceptance results

| Criterion | Task | Command | Artifact | Status | Limitation | Reviewer | Date |
| --- | --- | --- | --- | --- | --- | --- | --- |
| AC-001 | compatibility | local gate | runtime checks | PASS | none | implementation | 2026-09-11 |
| AC-002 | settings | pytest | settings tests | PASS | none | implementation | 2026-09-11 |
| AC-003 | settings schema | pytest | model contract | PASS | none | implementation | 2026-09-11 |
| AC-004 | precedence | pytest | environment tests | PASS | none | implementation | 2026-09-11 |
| AC-005 | redaction | pytest | serialization tests | PASS | none | implementation | 2026-09-11 |
| AC-006 | prefix | pytest | facade tests | PASS | none | implementation | 2026-09-11 |
| AC-007 | memory providers | pytest | bundle tests | PASS | none | implementation | 2026-09-11 |
| AC-008 | authorizer | pytest | bundle tests | PASS | none | implementation | 2026-09-11 |
| AC-009 | lifecycle | pytest | close tests | PASS | none | implementation | 2026-09-11 |
| AC-010 | sqlite URL | pytest | settings tests | PASS | none | implementation | 2026-09-11 |
| AC-011 | sqlite readiness | pytest | provider tests | PASS | none | implementation | 2026-09-11 |
| AC-012 | sqlite stores | pytest | provider tests | PASS | none | implementation | 2026-09-11 |
| AC-013 | cleanup | pytest | provider tests | PASS | none | implementation | 2026-09-11 |
| AC-014 | exports | pytest | package test | PASS | none | implementation | 2026-09-11 |
| AC-015 | doctor model | pytest | diagnostics tests | PASS | none | implementation | 2026-09-11 |
| AC-016 | doctor checks | pytest | diagnostics tests | PASS | none | implementation | 2026-09-11 |
| AC-017 | doctor order | pytest | diagnostics tests | PASS | none | implementation | 2026-09-11 |
| AC-018 | doctor redaction | pytest | diagnostics tests | PASS | none | implementation | 2026-09-11 |
| AC-019 | doctor JSON | pytest | CLI tests | PASS | none | implementation | 2026-09-11 |
| AC-020 | doctor text | pytest | CLI tests | PASS | none | implementation | 2026-09-11 |
| AC-021 | doctor exit codes | pytest | CLI tests | PASS | none | implementation | 2026-09-11 |
| AC-022 | version command | CLI | isolated command | PASS | none | implementation | 2026-09-11 |
| AC-023 | 0.2 compatibility | pytest | facade suite | PASS | none | implementation | 2026-09-11 |
| AC-024 | API parity | OpenAPI | normalized contract | PASS | none | implementation | 2026-09-11 |
| AC-025 | dependency pins | artifact | wheel metadata | PASS | none | implementation | 2026-09-11 |
| AC-026 | optional extra | artifact | wheel metadata | PASS | none | implementation | 2026-09-11 |
| AC-027 | clean wheel | script | isolated install | PASS | none | implementation | 2026-09-11 |
| AC-028 | source archive | artifact | sdist | PASS | none | implementation | 2026-09-11 |
| AC-029 | packaging | build | wheel and sdist | PASS | none | implementation | 2026-09-11 |
| AC-030 | docs | review | README | PASS | none | implementation | 2026-09-11 |
| AC-031 | examples | review | quickstart | PASS | none | implementation | 2026-09-11 |
| AC-032 | static boundaries | script | boundary scan | PASS | none | implementation | 2026-09-11 |
| AC-033 | no migrations | tests | provider spies | PASS | none | implementation | 2026-09-11 |
| AC-034 | no execution | tests | provider spies | PASS | none | implementation | 2026-09-11 |
| AC-035 | identity ownership | tests | injection tests | PASS | none | implementation | 2026-09-11 |
| AC-036 | development-only | pytest | topology checks | PASS | none | implementation | 2026-09-11 |
| AC-037 | quality gates | gate | ruff and pyright | PASS | none | implementation | 2026-09-11 |
| AC-038 | compatibility matrix | gate | Python matrix | PASS | none | implementation | 2026-09-11 |
| AC-039 | OpenAPI evidence | script | normalized JSON | PASS | none | implementation | 2026-09-11 |
| AC-040 | artifact evidence | script | hashes | PASS | none | implementation | 2026-09-11 |
| AC-041 | documentation evidence | review | docs | PASS | none | implementation | 2026-09-11 |
| AC-042 | evidence index | script | this file | PASS | none | implementation | 2026-09-11 |

## Gap register

No Phase 0.3 implementation gaps were identified. Follow-up maintenance remains
tracked separately for the existing CI Node 20 and Starlette warnings.

The boundary review outcome is **proceed-to-0.2** for the previously published
facade contract; Phase 0.3 adds local composition without changing upstream
routes or semantics. The integration burden remains in ShuETL's composition
layer, while public composition hooks stay injected and no copied route or
pipeline model is introduced. This is materially easier to maintain than a
parallel control-plane implementation and no behavior is contributed to
`etlantic-fastapi`.
