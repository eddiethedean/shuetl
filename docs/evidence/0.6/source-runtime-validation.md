# Phase 0.6 source/runtime implementation checks

Recorded: 2026-10-09 for source commit
`c064aa9ead7b78d9f6451895d6799e088ab8682f`. These checks and hosted artifacts
qualify selected implementation behavior; they do not close the 33 release
criteria or Gates A–C.

| Check | Command | Result | Scope |
| --- | --- | --- | --- |
| Lock | `uv lock --check` | PASS | Exact committed lock |
| Format | `uv run ruff format --check .` | PASS | 167 Python files |
| Lint | `uv run ruff check .` | PASS | Source, scripts and tests |
| Types | `uv run pyright` | PASS, 0 errors | Python 3.13.9 |
| Boundary | `uv run python scripts/check_boundaries.py` | PASS | Source and import boundaries |
| Regression | `uv run pytest -q --junitxml=docs/evidence/0.6/regression.xml` | 260 passed, 10 skipped | Nine PostgreSQL cases need the dedicated service; one final-hash case is release-gated |
| PostgreSQL regression | `uv run pytest tests/integration/test_postgresql.py -q --junitxml=docs/evidence/0.6/postgresql-regression.xml` | 9 passed, 0 skipped | Dedicated PostgreSQL 18.6 database; scheduler/run-worker/action-worker outage and recovery plus scheduler drain |
| Build/artifacts | `SOURCE_DATE_EPOCH=1580601600 uv build`; `uv run python scripts/check_artifact.py` | PASS | Wheel SHA-256 `3921b62c7d8c27b6a7d5be69e3a4e36ae1a3030ba9020a1db8dcbfbb73060d24`; sdist SHA-256 `23042e70c4f34ffe35c94e61bc4626522e57b1ba98e47c6dfced6dfaa21c0a3a` |
| OpenAPI | `uv run python scripts/capture_openapi.py --check` | PASS | Approved baseline unchanged |
| Clean wheel | `uv run python scripts/check_clean_wheel.py` | PASS | Isolated core, SQLite, PostgreSQL and server extras on Python 3.13.9 |
| Installed-wheel matrices | Hosted CI [37989243217](https://github.com/eddiethedean/shuetl/actions/runs/37989243217) | PASS | Python 3.11–3.13; Gate 0 coordination, four CLI roles, cleanup order and PostgreSQL integration |

The full-suite skips are explicit: PostgreSQL tests run separately with the
dedicated service, and final release hashes are recorded only after release
gates close. [Regression XML](regression.xml) and
[PostgreSQL XML](postgresql-regression.xml) retain the local outcomes. The
latest hosted test job rejects skipped PostgreSQL cases.

The evidence checker remains intentionally red for release because
`proofs.json` and audited per-criterion PASS records have not been produced,
all 33 criteria remain OPEN, and Gates A–C remain OPEN. These selected checks do
not qualify active installed-process termination, the complete provider/resource
contract, or transition/rollback.
