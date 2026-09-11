# ShuETL 0.1 Evidence Index

## Baseline

| Field | Recorded value |
|---|---|
| ShuETL version | 0.1.0 |
| OS and architecture | macOS arm64 (local evidence); CI ubuntu-latest |
| Python version | CPython 3.12.13 local; CI 3.11/3.12/3.13 |
| uv version | 0.11.3 |
| Python matrix | CPython 3.11, 3.12, 3.13 |
| ETLantic | 0.51.0 |
| etlantic-fastapi | 0.51.0 |
| FastAPI | 0.141.1 |
| Pydantic | 2.13.5 |
| HTTPX | 0.28.1 |
| ETLantic source revision | `83f5e67e221d588ff895ad23f2cb7c684ac12c49` |
| ShuETL import origin | temporary environment site-packages (clean-wheel) |
| ETLantic import origin | temporary environment site-packages (clean-wheel) |
| etlantic-fastapi import origin | temporary environment site-packages (clean-wheel) |
| FastAPI import origin | temporary environment site-packages (clean-wheel) |
| Pydantic import origin | temporary environment site-packages (clean-wheel) |
| HTTPX import origin | temporary environment site-packages (clean-wheel) |
| Evidence environment | isolated wheel installation; normalized origins contain no absolute paths |
| Source checkout | `PYTHONPATH` empty; clean-wheel runs outside checkout |
| SHA-256 wheel | `07945576ee12d978e5fc785fa3303d38d41481c07fca6dc39158dc483d2ff948` |
| SHA-256 sdist | `0573a636468b39b4de3bde7d9d7c52950cdc7b595dc108c244ee4b2b5ba926d0` |
| ShuETL GitHub issues | none open at planning/implementation baseline |
| Upstream follow-up | [ETLantic #130](https://github.com/eddiethedean/etlantic/issues/130), non-blocking docstring drift |

Detailed records:

- [public-contract inventory](contracts.md)
- [ownership matrix](ownership.md)
- [normalized OpenAPI](openapi.normalized.json)
- [accepted ADRs](../../adr/README.md)

## Verification commands

```text
uv sync --locked --all-groups --extra test
uv run ruff format --check .
uv run ruff check .
uv run pyright
uv run pytest -q
uv build
uv run python scripts/check_artifact.py
uv run python scripts/check_boundaries.py --openapi docs/evidence/0.1/openapi.normalized.json
uv run python scripts/capture_openapi.py --check
uv run python scripts/check_clean_wheel.py
uv run python scripts/check_evidence.py
```

## Acceptance results

| Criterion | Task | Command | Artifact | Status | Limitation | Reviewer | Date |
|---|---|---|---|---|---|---|---|
| AC-001 | E05 | `check_artifact.py` | wheel metadata | PASS | none | Codex | 2026-09-11 |
| AC-002 | E05 | `check_artifact.py` | wheel allowlist | PASS | none | Codex | 2026-09-11 |
| AC-003 | E05 | `pytest` and clean-wheel | package import | PASS | inert package only | Codex | 2026-09-11 |
| AC-004 | E05 | `check_evidence.py` | lock and evidence | PASS | exact train only | Codex | 2026-09-11 |
| AC-005 | E09 | `checks.yml` matrix | CI logs | PASS | ubuntu runner | Codex | 2026-09-11 |
| AC-006 | E02 | `contracts.md` | contract inventory | PASS | upstream-owned | Codex | 2026-09-11 |
| AC-007 | E03 | `ownership.md` | ownership matrix | PASS | later profiles deferred | Codex | 2026-09-11 |
| AC-008 | E04 | ADR checks | six ADRs | PASS | accepted decisions | Codex | 2026-09-11 |
| AC-009 | E06 | `pytest` | health response | PASS | memory provider | Codex | 2026-09-11 |
| AC-010 | E06 | `pytest` | authenticated lookup | PASS | fixed principal | Codex | 2026-09-11 |
| AC-011 | E06 | `pytest` | submission acceptance | PASS | no execution | Codex | 2026-09-11 |
| AC-012 | E06 | `pytest` | idempotency replay | PASS | memory store | Codex | 2026-09-11 |
| AC-013 | E06 | `pytest` | problem details | PASS | upstream handlers | Codex | 2026-09-11 |
| AC-014 | E06 | `pytest` | SSE and diagnostics | PASS | memory provider | Codex | 2026-09-11 |
| AC-015 | E07 | `capture_openapi.py` | direct snapshot | PASS | normalized prefix | Codex | 2026-09-11 |
| AC-016 | E07 | `capture_openapi.py --check` | normalized OpenAPI | PASS | exact train only | Codex | 2026-09-11 |
| AC-017 | E08 | boundary checker | source scan | PASS | scoped to ShuETL | Codex | 2026-09-11 |
| AC-018 | E08 | boundary tests | negative fixtures | PASS | static rules | Codex | 2026-09-11 |
| AC-019 | E09 | `check_clean_wheel.py` | isolated install | PASS | network required | Codex | 2026-09-11 |
| AC-020 | E10 | `check_evidence.py` | this index | PASS | independent review pending | Codex | 2026-09-11 |
| AC-021 | E12 | `check_release.py` | release gate log | PASS | local + CI | Codex | 2026-09-11 |
| AC-022 | E09 | workflow and scope review | checks/release workflows | PASS | publication separately authorized | Codex | 2026-09-11 |

## Gate results

| Gate | Command | Evidence | Status |
|---|---|---|---|
| Gate A | `uv run pytest -q` | test report | PASS |
| Gate B | `uv run python scripts/check_release.py` | release gate log | PASS |
| Gate C | CI checks and release workflow dependency | GitHub Actions | PASS |

## Gap register

| Item | Disposition | Notes |
|---|---|---|
| `include_router()` writes `app.state.etlantic_api` | deferred:0.2 | collision detection belongs to the facade, not the spike; see [ADR-0003](../../adr/0003-dependency-boundaries.md) |
| Existing `ControlPlaneError` handler replacement | deferred:0.2 | handler composition is not implemented in 0.1 |
| Memory stores do not survive restart | accepted-risk | explicitly not a production durability claim; accepted in [ADR-0003](../../adr/0003-dependency-boundaries.md) |

## Boundary review

Outcome: `proceed-to-0.2`

The E11 review records a proceed decision because all technical proofs pass.

1. integration burden beyond `include_router()` was limited to explicitly installing upstream error handlers and selecting a host lifecycle policy.
2. The spike used only public composition hooks.
3. No test required a copied route, schema, control-plane model, or runtime service.
4. The planned 0.2 facade is materially easier and safer because it centralizes prefix, state, handler, and lifespan validation.
5. No required hook needs to be contributed to `etlantic-fastapi` first.

## Review record

| Role | Reviewer | Date | Result |
|---|---|---|---|
| Implementation | Codex | 2026-09-11 | PASS |
| Independent review | not run | — | deferred to normal PR review |
