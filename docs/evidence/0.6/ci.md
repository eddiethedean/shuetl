# Phase 0.6 CI and release gate

The workflow defines Python 3.11, 3.12, and 3.13 jobs, installs all qualified
extras, provisions a runtime PostgreSQL role without schema `CREATE`, uses a
PostgreSQL 18.6 service, and builds/checks wheel and source artifacts. The
release gate runs the PostgreSQL role fixture from an isolated installed wheel.
`check_pytest_no_skips.py` rejects skips in required PostgreSQL integration
tests. PRs run the implementation gate with open acceptance rows allowed; tag
runs use strict evidence mode.

| Gate | Workflow job | Current evidence |
| --- | --- | --- |
| A — static and regression | `quality` | Configured; hosted results not yet captured for this source revision. |
| B — PostgreSQL | `postgresql-integration` | PostgreSQL 18.6 matrix, restricted role, and runtime fixture configured; hosted results not yet captured. |
| C — clean artifact | `release-gate` | Wheel build, metadata checks, isolated extras, installed-wheel PostgreSQL role fixture, OpenAPI, boundary, and full check script configured; hosted results not yet captured. |

`scripts/check_release.py --allow-open` runs lock, sync, Ruff, Pyright,
boundary, test, build, artifact, OpenAPI, clean-wheel, and evidence consistency
checks without authorizing release. The default command adds
`check_evidence.py --release`, which rejects open criteria or gates. A release
tag cannot publish until all AC rows and Gate A–C are PASS and the evidence
outcome is `proceed-to-0.6-preview`.

This document records the committed workflow definition. No GitHub Actions run
for the implementation branch is included here yet.
