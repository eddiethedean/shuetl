# ETLantic 0.57.2 requirements audit

Verified on 2026-10-11 using published 0.57.2 packages and the locally built
ShuETL 0.6.0 wheel. This supersedes the active findings in the
[0.57.1 audit](ETLANTIC_0_57_1_REQUIREMENTS_AUDIT.md); earlier evidence is preserved.
This is local qualification of a modified working tree, not hosted final-release
approval. [Provenance and artifact hashes](etlantic_0_57_2/qualification.json)
identify the base commit and the uncommitted changes.

## Upstream findings

| Requirement | Observed result | Tracking |
| --- | --- | --- |
| HC-14 / AC-028 deterministic sort before keyed deduplication | PASS: both input orders retain `{id: 1, quantity: 3}` using public portable authoring and the installed Local compiler. | [#283](https://github.com/eddiethedean/etlantic/issues/283), fixed in 0.57.2. |
| HC-05 / AC-033 connection test and bounded schema inspection | PASS: published SQL handlers execute through durable jobs in a separate worker against PostgreSQL 18.6, with a scoped timeout-aware resource bridge and no worker HTTP imports. | [#286](https://github.com/eddiethedean/etlantic/issues/286), delivered in 0.57.2. |
| Saved-definition preflight dispatch and revision identity | PASS: the backend-owned handler returns the first accepted revision after a definition edit and same-key retry. Result mode is `read_only_plan`. | [#286](https://github.com/eddiethedean/etlantic/issues/286). |
| Read-only live pipeline readiness | OPEN: default preflight validates/plans and authorizes the pinned definition; it does not establish live source/target connection, schema or publication readiness. | [Follow-up on existing #121](https://github.com/eddiethedean/etlantic/issues/121#issuecomment-6110747363). |

The original missing handler implementations are delivered. The broader live
preflight requirement remains on its existing feature tracker. ShuETL must not
interpret static plan success as live provider readiness or implement ETL
readiness rules in application callbacks.

## Independent verification

| Check | Result and scope |
| --- | --- |
| Requirements probe, Python 3.11.15 / 3.12.13 / 3.13.16 | PASS on all three. Positive connection/schema/preflight jobs succeed, a revoked reference fails, a slow resolver times out, another resource owner cannot read the receipt, and credential/source-row sentinels are absent. The data schema and rows are unchanged. |
| Installed-wheel PostgreSQL Gate 0, Python 3.11–3.13 | PASS on all three. Restricted runtime grants, distinct role processes, manual/native scheduled transfers, PostgreSQL source/upsert effects, canonical reports, portable transform/quality observations and process contention. |
| Installed four-role CLI, Python 3.11–3.13 | PASS on all three. Loopback probes, HTTP import isolation, explicit migrations, runtime grants, SIGTERM shutdown and backend-before-binding cleanup. This is idle-role qualification. |
| Isolated headless and gateway contract probes, Python 3.12 | PASS. Shared authorized schedule services and HTTP/headless records, read-only fresh/compatible/partial schema inspection, role status and repeated idle drain. |
| Source pytest, Python 3.12 | 260 passed, 10 skipped. Nine PostgreSQL cases ran separately below; the final-artifact hash case remains gated by the open release ledger. |
| PostgreSQL integration, Python 3.12 / PostgreSQL 18.6 | 9 passed, no skips. Dedicated disposable database. |
| Ruff format/lint, Pyright, boundaries, lock and whitespace | PASS. |
| Wheel/sdist contents and dependency pins; clean-wheel examples | PASS on Python 3.12, including core, SQLite, PostgreSQL imports, server extra and host authentication recipes. |

The action probe waits for worker initialization before accepting the short
deadline, so interpreter startup does not substitute for provider execution.
It uses explicit resource-owner identity. The runtime role has only SELECT on
the data schema and DML on the control-plane schema, without schema CREATE or
object ownership.

## Repository changes

- Pin core, FastAPI, SQLModel and independently installed SQL connector fixtures
  to exact 0.57.2; refresh the lockfile and compatibility/doctor messages.
- Require deterministic sort/deduplication in the reference fixture and release
  checker. The checker requires 0.57.2 provenance and rejects the former defective
  sort observation.
- Update the handler regression assertion for upstream's worker-only
  `_deadline_at` control, matching the accepted job deadline.
- Preserve historical 0.57.0 and 0.57.1 evidence separately.

## Evidence and reproduction

- [Reproducer](etlantic_0_57_2/requirements_probe.py) and requirement results:
  [3.11](etlantic_0_57_2/requirements-probe-3.11.json),
  [3.12](etlantic_0_57_2/requirements-probe.json),
  [3.13](etlantic_0_57_2/requirements-probe-3.13.json).
- Installed Gate 0:
  [3.11](etlantic_0_57_2/postgresql-gate0-3.11.json),
  [3.12](etlantic_0_57_2/postgresql-gate0.json),
  [3.13](etlantic_0_57_2/postgresql-gate0-3.13.json).
- Installed CLI:
  [3.11](etlantic_0_57_2/cli-postgresql-3.11.json),
  [3.12](etlantic_0_57_2/cli-postgresql.json),
  [3.13](etlantic_0_57_2/cli-postgresql-3.13.json).
- [Headless](etlantic_0_57_2/headless-probe.json) and
  [gateway](etlantic_0_57_2/gateway-probe.json) contract results.
- [Source pytest](etlantic_0_57_2/source-tests.xml),
  [PostgreSQL pytest](etlantic_0_57_2/postgresql-tests.xml), and
  [clean-wheel log](etlantic_0_57_2/clean-wheel.log).

Run with an isolated interpreter containing the published core, SQL and SQLModel
packages:

```sh
python -I docs/reviews/etlantic_0_57_2/requirements_probe.py \
  --disposable-admin-url "$DISPOSABLE_POSTGRESQL_URL" \
  --output /tmp/etlantic-0572-requirements.json
```

The probe creates and removes uniquely named databases/roles on an explicitly
disposable PostgreSQL 18.6 server. Do not target an application database. The
qualification container was stopped after these runs.

## Release status

The two originally reported implementation blockers are resolved. Read-only live
preflight remains a capability requirement under #121. The main ledger still has
33 OPEN acceptance rows and Gates A–C OPEN. A later local qualification now
records active-work drain/forced termination, selected provider controls and
resource-retention cases, a bounded transition rehearsal, and a 22-case fault
matrix; see [the current Phase 0.6 qualification](../evidence/0.6/current-qualification.md).
Twenty fault cases pass, while two accepted-preparation recovery failures remain
tracked in #299. Live preflight, the full advertised capability matrix,
production transition, hosted final-artifact qualification and reviewed release
ledger remain open. These results do not close the full release gates.
