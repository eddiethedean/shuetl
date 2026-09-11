# Phase 0.2 evidence index

This record covers the 0.2.0 facade implementation on the supported Python
3.11–3.13 and ETLantic 0.51.0 train. Paths are intentionally repository-relative
so the evidence contains no machine-specific locations or secrets.

| Field | Value |
|---|---|
| Release status | Published to PyPI on 2026-09-11 |
| Release tag | [`v0.2.0`](https://github.com/eddiethedean/shuetl/releases/tag/v0.2.0) |
| Release commit | [`a662d5d0db6dddc0045f7705384eef9df3c217ee`](https://github.com/eddiethedean/shuetl/commit/a662d5d0db6dddc0045f7705384eef9df3c217ee) |
| Release workflow | [GitHub Actions run 34633107487](https://github.com/eddiethedean/shuetl/actions/runs/34633107487) |
| PyPI publication | [`shuetl 0.2.0`](https://pypi.org/project/shuetl/0.2.0/) |
| OS and architecture | CI ubuntu-latest x86_64; local qualification macOS arm64 |
| Python version | 3.11, 3.12, 3.13 |
| uv version | 0.11.3 |
| ETLantic source revision | etlantic 0.51.0 PyPI distribution |
| ShuETL import origin | installed wheel `shuetl` |
| ETLantic import origin | installed wheel `etlantic` |
| etlantic-fastapi import origin | installed wheel `etlantic_fastapi` |
| FastAPI import origin | installed wheel `fastapi` |
| Pydantic import origin | installed wheel `pydantic` |
| HTTPX import origin | installed test extra `httpx2` |
| SHA-256 wheel | `5d763f93da600eadffdc94370575a3bb26d0894bba885371a9b4589ece593d49` |
| SHA-256 sdist | `0f68e0f546c81ffb7fb7378c98c756abfda1cede8500e8f3d56c5a23864ff48f` |
| Published wheel SHA-256 | `d3ddba2e89609ade7360df226d7d1e63c8ea1dec0284ab4b09053ee279cb0a20` |
| Published sdist SHA-256 | `219a76bc1811a492e91132ac180bd27222ed8f45fbfae7ea82852b2d07ec3d5c` |

## Gates

| Gate | Scope | Result |
|---|---|---|
| Gate A | Ruff, Pyright, boundaries, tests | PASS |
| Gate B | Build, artifact, OpenAPI, clean wheel | PASS |
| Gate C | Evidence consistency and redaction | PASS |

## Acceptance results

| Criterion | Task / Requirement | Command | Artifact | Status | Limitation | Reviewer | Date |
|---|---|---|---|---|---|---|---|
| AC-001 | 0.2.0 metadata and qualified dependencies | pytest | package metadata | PASS | none | Codex | 2026-09-11 |
| AC-002 | exact public exports | pytest | installed wheel | PASS | none | Codex | 2026-09-11 |
| AC-003 | API identity and type validation | pytest | tests/unit/test_package.py; tests/unit/test_integration.py | PASS | none | Codex | 2026-09-11 |
| AC-004 | complete default mount | pytest | tests/unit/test_integration.py; tests/integration/test_shuetl_facade.py | PASS | none | Codex | 2026-09-11 |
| AC-005 | dedicated application factory | pytest | tests/unit/test_integration.py; tests/integration/test_shuetl_facade.py | PASS | none | Codex | 2026-09-11 |
| AC-006 | literal prefixes | pytest | tests/unit/test_integration.py | PASS | none | Codex | 2026-09-11 |
| AC-007 | invalid prefixes are atomic | pytest | tests/unit/test_integration.py; tests/review/test_phase_0_2_blockers.py | PASS | none | Codex | 2026-09-11 |
| AC-008 | OpenAPI parity | pytest; capture_openapi.py | tests/integration/test_phase_0_2_contract.py; openapi.normalized.json | PASS | none | Codex | 2026-09-11 |
| AC-009 | operation IDs and schemas | pytest; boundary check | tests/integration/test_phase_0_2_contract.py; OpenAPI evidence | PASS | none | Codex | 2026-09-11 |
| AC-010 | upstream error handler install | pytest | handler test | PASS | none | Codex | 2026-09-11 |
| AC-011 | exact handler preservation | pytest | tests/integration/test_phase_0_2_contract.py | PASS | none | Codex | 2026-09-11 |
| AC-012 | custom handler conflict | pytest | collision test | PASS | none | Codex | 2026-09-11 |
| AC-013 | state ownership record | pytest | state test | PASS | none | Codex | 2026-09-11 |
| AC-014 | reserved state conflicts | pytest | collision test | PASS | none | Codex | 2026-09-11 |
| AC-015 | repeated mount rejection | pytest | collision test | PASS | none | Codex | 2026-09-11 |
| AC-016 | prefix subtree rules | pytest | tests/unit/test_integration.py; tests/review/test_phase_0_2_blockers.py | PASS | none | Codex | 2026-09-11 |
| AC-017 | path and operation collisions | pytest | tests/unit/test_integration.py; tests/review/test_phase_0_2_blockers.py | PASS | none | Codex | 2026-09-11 |
| AC-018 | upstream operation validation | pytest | tests/unit/test_integration.py | PASS | none | Codex | 2026-09-11 |
| AC-019 | OpenAPI cache invalidation | pytest | tests/integration/test_phase_0_2_contract.py | PASS | none | Codex | 2026-09-11 |
| AC-020 | host preservation | pytest | tests/unit/test_integration.py; tests/integration/test_phase_0_2_contract.py | PASS | none | Codex | 2026-09-11 |
| AC-021 | bound lifespan state | pytest | tests/integration/test_phase_0_2_contract.py | PASS | none | Codex | 2026-09-11 |
| AC-022 | composed lifespan ordering | pytest | tests/unit/test_integration.py; tests/integration/test_phase_0_2_contract.py | PASS | none | Codex | 2026-09-11 |
| AC-023 | provider ownership | pytest; ownership evidence | tests/unit/test_integration.py; docs/evidence/0.2/ownership.md | PASS | no provider lifecycle calls are introduced | Codex | 2026-09-11 |
| AC-024 | dependency overrides | pytest | tests/integration/test_phase_0_2_contract.py | PASS | none | Codex | 2026-09-11 |
| AC-025 | definition contract | pytest | tests/integration/test_phase_0_2_contract.py; tests/integration/test_memory_mount.py | PASS | none | Codex | 2026-09-11 |
| AC-026 | accepted idempotent submission | pytest | tests/integration/test_phase_0_2_contract.py; tests/integration/test_memory_mount.py | PASS | none | Codex | 2026-09-11 |
| AC-027 | operability routes | pytest; OpenAPI evidence | tests/integration/test_phase_0_2_contract.py; openapi.normalized.json | PASS | qualified upstream route inventory | Codex | 2026-09-11 |
| AC-028 | SSE contract | pytest | tests/integration/test_phase_0_2_contract.py | PASS | qualified upstream behavior | Codex | 2026-09-11 |
| AC-029 | authorization ownership | pytest | tests/integration/test_phase_0_2_contract.py; tests/integration/test_memory_mount.py | PASS | none | Codex | 2026-09-11 |
| AC-030 | no duplicate execution layer | boundary check; pytest | scripts/check_boundaries.py; tests/boundary/test_boundaries.py | PASS | none | Codex | 2026-09-11 |
| AC-031 | independent app state | pytest | tests/unit/test_integration.py; tests/integration/test_phase_0_2_contract.py | PASS | none | Codex | 2026-09-11 |
| AC-032 | isolated wheel quickstart | check_clean_wheel.py | installed wheel | PASS | none | Codex | 2026-09-11 |
| AC-033 | artifact allowlist and metadata | check_artifact.py | wheel/sdist | PASS | none | Codex | 2026-09-11 |
| AC-034 | complete quality gates | check_release.py | scripts/check_release.py; CI workflow | PASS | Python matrix | Codex | 2026-09-11 |
| AC-035 | user documentation | pytest; documentation review | README.md; tests/review/test_phase_0_2_blockers.py | PASS | none | Codex | 2026-09-11 |
| AC-036 | complete redacted evidence | check_evidence.py | docs/evidence/0.2/README.md; scripts/check_evidence.py | PASS | none | Codex | 2026-09-11 |

## Boundary outcome

The public composition hooks and copied route review are recorded explicitly:
the integration burden is materially easier, and there is no copied route.
The Phase 0.1 boundary review found the integration burden and public
composition hooks sufficient to make ShuETL materially easier without a copied
route. ShuETL has not contributed to `etlantic-fastapi`; it composes its public
hooks. The result is `proceed-to-0.2`; future production deployment work
remains outside this release.
