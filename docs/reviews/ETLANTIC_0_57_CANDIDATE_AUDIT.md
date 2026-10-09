# ETLantic 0.57.0 — Published Candidate Review for ShuETL 0.6

Reviewed: 2026-10-09. The initial published-candidate audit below is now
supplemented by [coverage acceptance](../evidence/0.6/coverage-acceptance.md):
U01–U05 PASS. ShuETL's development metadata/lock adopt exact core/FastAPI/SQLModel
`0.57.0`; other runtime pins are unchanged. Installed-artifact PostgreSQL role
qualification is recorded in [0.6 evidence](../evidence/0.6/README.md).
The 33 release acceptance criteria and Gates A–C remain OPEN.

This supersedes the current-gap observations made against 0.56.2 in the
[responsibility review](PHASE_0_6_RESPONSIBILITY_REVIEW.md). It does not change
[ADR-0015](../adr/0015-backend-and-deployment-ownership.md)'s ownership boundary.

## Publication and upstream evidence

The [v0.57.0 release](https://github.com/eddiethedean/etlantic/releases/tag/v0.57.0)
was published on 2026-10-08 at 20:40:25 UTC. PyPI supplies aligned core, FastAPI
and SQLModel distributions. Downloaded wheels were hashed and compared with
PyPI metadata; [the manifest](etlantic_0_57/wheel-manifest.json) records exact
filenames, source URLs and SHA-256 values.

| Wheel | SHA-256 |
| --- | --- |
| `etlantic-0.57.0-py3-none-any.whl` | `ff7939f9134a07c0ef1513d45b76623154e12931c935a01aedfceabcb93ab7b4` |
| `etlantic_fastapi-0.57.0-py3-none-any.whl` | `4545131b0e7d3a9cfc9972a0f46374d136b755807c47216b27a8156bf83b0c27` |
| `etlantic_sqlmodel-0.57.0-py3-none-any.whl` | `28641b7bfefb888b83bfc00f172f4293913e74717b747ed7a0289737a2d7051f` |

The tagged [upstream exit gate](https://github.com/eddiethedean/etlantic/blob/v0.57.0/docs/11_DEVELOPMENT/EXIT_GATE_0_57.md)
links [CI run 37832487031](https://github.com/eddiethedean/etlantic/actions/runs/37832487031),
attempt 2, at `94fe5c29182c37ab9398146b61609cb6ebc9a59a`. GitHub reports success.
The release tag is `d1f4e5a4d013e37f8adc54b4644ea9b2be66f801`, whose parent is
that candidate and whose commit records release qualification documentation.

Downloaded artifacts are retained here:

- [Upstream acceptance XML](etlantic_0_57/upstream-managed-acceptance.xml):
  160 tests, zero failures, errors or skips. Cases include PostgreSQL restricted
  runtime grants, scheduler restart/link recovery, migrations and concurrent
  admission; these are upstream executions, not local ShuETL results.
- [Upstream installed-wheel JSON](etlantic_0_57/upstream-headless-wheels.json):
  core/provider 0.57.0, FastAPI absent, all three runtime factories/ticks and
  drain. Both wheel hashes exactly match the downloaded PyPI wheels.

The old `LOCAL_HEADLESS_WHEEL_QUALIFICATION.json` in upstream's tagged tree
records a development build labeled 0.56.2; the exit gate labels it historical.
Use the commit-matched CI artifact above for 0.57 evidence. The published release
body also retains an “Unreleased” heading; publication is established by GitHub
release metadata and PyPI artifacts, not that stale heading.

## Contract findings

| Gate | Published public surface | Evidence and remaining downstream work |
| --- | --- | --- |
| U01 / #278 | Core `etlantic.control_plane.ManagedBackend`; provider `etlantic_sqlmodel.SQLModelBackendConfig` and `create_managed_backend`; HTTP `etlantic_fastapi.adapt_managed_backend` | Independent headless construction has no HTTP input or adapter installation. Gateway uses the same managed/schedule services. Preserve owned/borrowed cleanup and qualify host lifecycle integration. |
| U02 / #279 | `backend.schedule_service`, a `ScheduleApplicationService`, exposes create/amend/pause/resume/preview/trigger/get/list_definition/list_firings | Independent create/read/list/preview/pause/resume and cross-workspace denial pass; HTTP create/get reuse canonical records. Upstream parity/recovery coverage is present. Complete ShuETL's configured HTTP/headless parity fixture during Gate 0. |
| U03 / #280 | `backend.create_scheduler(owner_id=..., ttl_seconds=30, clock=None, wake=None)` supplies shared stores and explicit occurrence service | Independent scheduler construction/empty tick pass; installed factory supplies `managed_service` as the explicit collaborator. No standard-path callback introspection. Qualify real scheduled effects and restart boundaries on ShuETL's PostgreSQL topology. |
| U04 / #281 | `schema_requirements()` and `inspect_schema(engine)` with typed compatibility and safe reason codes | Fresh/compatible/partial SQLite results pass independently; inspection and construction have no DDL/data writes or commit. Upstream covers broader state/grant matrix. Consume this API and verify actual ShuETL runtime grants. |
| U05 / #282 | Scheduler, run worker and action worker expose `status()` and `request_drain()`; `RuntimeRoleStatus` records activity/admission/prerequisites/in-flight/capabilities | Independent initial unknown prerequisites, empty ticks and repeated drain pass. Status is cached local evidence, not independent provider health. Qualify freshness, signals, active work, grace and cleanup in ShuETL processes. |

All five GitHub issues still report OPEN as of this review. Their implementation
is present in published artifacts; an open tracker is not evidence of a missing
API. This review does not close issues or substitute for their maintainers'
acceptance. The dependency register tracks Gate U acceptance separately.

The provider schema head remains
`014_cp1_complete_principal_idempotency_0_56`; 0.57 introduces no new migration
from 0.56. This does not establish direct migration/replay from ShuETL's retained
0.5/ETLantic 0.55 deployment. Keep the planned fresh-store transition/rollback.

## Independent installed-artifact checks

Two isolated Python 3.13.9 environments outside both repositories ran
[contract_probe.py](etlantic_0_57/contract_probe.py) successfully:

- [Headless result](etlantic_0_57/headless-probe.json) and
  [environment](etlantic_0_57/headless-requirements.txt): core/provider only,
  no FastAPI installation; neutral construction, shared authorized schedules,
  provider inspection, all role factories/ticks, repeated drain and borrowed
  engine preservation after idempotent close.
- [Gateway result](etlantic_0_57/gateway-probe.json) and
  [environment](etlantic_0_57/gateway-requirements.txt): exact 0.57.0 packages,
  ShuETL's current FastAPI 0.141.1, Pydantic 2.13.5, settings 2.15.0 and SQLAlchemy
  2.0.52 pins. Adapter construction/mounting leaves execution-host modules
  unloaded; HTTP create/get and Python callers share canonical schedule records.

Results record module origins and public signatures. The probe uses disposable
in-memory SQLite with a shared connection pool for HTTP test threads; its partial
schema check drops one provider-declared object only in that disposable store.
It does not accept an application database URL. It executes no real ETL data
movement, active-drain race or PostgreSQL process/grant qualification.

To reproduce from any scratch directory, substitute absolute paths for the
review assets and use the recorded requirements:

```sh
uv venv --python 3.13 ./headless
uv pip install --python ./headless/bin/python -r /absolute/path/headless-requirements.txt
./headless/bin/python /absolute/path/contract_probe.py --mode headless --output ./headless-result.json
uv venv --python 3.13 ./gateway
uv pip install --python ./gateway/bin/python -r /absolute/path/gateway-requirements.txt
./gateway/bin/python /absolute/path/contract_probe.py --mode gateway --output ./gateway-result.json
```

## Implementation-plan adjustment

W00 now reviews the published 0.57.0 contracts and binds the exact artifacts,
signatures and upstream conformance to U01–U05. There is no observed missing
contract surface that requires a ShuETL semantic substitute. Any failure found
in full qualification still returns upstream.

The initial audit left coverage acceptance open. The subsequent
[guarantee-specific acceptance](../evidence/0.6/coverage-acceptance.md) closes
U01–U05 with additional consumer/lifecycle and provider/PostgreSQL executions.
Exact pins/public provider inspection are adopted, and installed-artifact Gate 0
passes on all supported Python minors. ShuETL API freeze and W03–W08 remain open;
the initial focused probes alone are not the Gate 0 or release proof.
