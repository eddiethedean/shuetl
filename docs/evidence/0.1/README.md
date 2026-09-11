# ShuETL 0.1 Evidence Index

## Baseline

| Field | Recorded value |
|---|---|
| ShuETL version | 0.1.0 |
| Python matrix | CPython 3.11, 3.12, 3.13 |
| ETLantic | 0.51.0 |
| etlantic-fastapi | 0.51.0 |
| FastAPI | lock-resolved within upstream `>=0.115,<1` |
| Pydantic | lock-resolved within upstream `>=2.12,<3` |
| Evidence environment | isolated wheel installation; import origins recorded without absolute paths |
| Source checkout | none exposed through `PYTHONPATH` |
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

| Criterion | Status | Proof |
|---|---|---|
| AC-001 | PASS | `scripts/check_artifact.py` |
| AC-002 | PASS | wheel member allowlist |
| AC-003 | PASS | `tests/unit/test_package.py`, clean-wheel check |
| AC-004 | PASS | lock file and clean-wheel import origins |
| AC-005 | PASS | CI Python matrix |
| AC-006 | PASS | `contracts.md` |
| AC-007 | PASS | `ownership.md` |
| AC-008 | PASS | `docs/adr/README.md` and ADR files |
| AC-009 | PASS | `tests/integration/test_memory_mount.py` |
| AC-010 | PASS | `tests/integration/test_memory_mount.py` |
| AC-011 | PASS | `tests/integration/test_memory_mount.py` |
| AC-012 | PASS | `tests/integration/test_memory_mount.py` |
| AC-013 | PASS | `tests/integration/test_memory_mount.py` |
| AC-014 | PASS | spike and boundary checks |
| AC-015 | PASS | `scripts/capture_openapi.py` |
| AC-016 | PASS | normalized OpenAPI snapshot |
| AC-017 | PASS | `scripts/check_boundaries.py` |
| AC-018 | PASS | boundary negative fixtures |
| AC-019 | PASS | `scripts/check_clean_wheel.py` |
| AC-020 | PASS | this evidence index |
| AC-021 | PASS | `scripts/check_release.py` |
| AC-022 | PASS | artifact/source allowlists and scope review |

## Gap register

| Item | Disposition | Notes |
|---|---|---|
| `include_router()` writes `app.state.etlantic_api` | deferred:0.2 | collision detection belongs to the facade, not the spike |
| Existing `ControlPlaneError` handler replacement | deferred:0.2 | handler composition is not implemented in 0.1 |
| Memory stores do not survive restart | accepted-risk | explicitly not a production durability claim |

## Boundary review

Outcome: `proceed-to-0.2`

The E11 review records a proceed decision because all technical proofs pass.

## Review record

| Role | Reviewer | Date | Result |
|---|---|---|---|
| Implementation | Codex | 2026-09-11 | PASS |
| Independent review | not run | — | deferred to normal PR review |
