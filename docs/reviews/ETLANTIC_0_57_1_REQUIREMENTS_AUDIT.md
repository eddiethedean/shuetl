# ETLantic 0.57.1 requirements audit

**Historical audit:** Current findings are in
[the 0.57.2 audit](ETLANTIC_0_57_2_REQUIREMENTS_AUDIT.md).

Verified on 2026-10-10 against published packages, after updating the ShuETL
candidate to the 0.57.1 train. This is an upstream requirement audit, not a ShuETL
0.6 release qualification or Gate 0 PASS.

## Confirmed upstream gaps reported

| Requirement | Installed-wheel observation | GitHub report |
| --- | --- | --- |
| HC-14 / AC-028 deterministic deduplication | Public portable `sort(id ASC, quantity ASC).dropDuplicates("id")` retains quantity 4 for input `[4, 3]` and quantity 3 for reversed input. Both must retain 3. The Local compiler advertises both operations. | [Existing #283, updated with the 0.57.1 reproduction](https://github.com/eddiethedean/etlantic/issues/283#issuecomment-6099658441). [Fix PR #284](https://github.com/eddiethedean/etlantic/pull/284) was open at audit time. |
| HC-05 / AC-033 connection testing, connector schema inspection and read-only preflight | Using the public SQL action-handler factory with the managed backend, accepted `connector.test`, `connector.schema.inspect`, and `connector.preflight` jobs all terminate `failed` / `handler_unavailable`. No credential/engine resolver is invoked. | [New #286](https://github.com/eddiethedean/etlantic/issues/286). Related broad readiness tracker: [#121](https://github.com/eddiethedean/etlantic/issues/121). |

The action issue is a missing implementation behind shipped request/job APIs.
It is not a PostgreSQL outage or a failure to supply credentials: the action host
has no corresponding handlers. The published SQL factory supplies only live
catalog, provisioning, and provisioning cleanup. The backend adds installed
catalog and run preparation. Host injection remains functional, but requiring
application-owned readiness or SQL schema logic would violate the agreed standard
consumer boundary. Independent provider packages may implement that logic.

The sort defect was reported on the existing issue to avoid a duplicate. The
compiler descriptor remains `etlantic-local==0.50.0` inside `etlantic==0.57.1`;
that descriptor alone is not an incompatible package pin.

## Previously requested contracts available

The existing [contract probe](etlantic_0_57/contract_probe.py) was rerun against
exact 0.57.1 core, SQLModel, and (gateway mode) FastAPI adapter packages.

| Contract | Evidence and limits |
| --- | --- |
| U01: neutral public managed backend | Headless construction succeeded without FastAPI installed; backend and worker role creation are public. |
| U02: shared authorized schedule commands | Create/get/list/preview/pause/resume and denied cross-scope lookup passed. Gateway reads and creates the same headless service records. |
| U03: managed scheduler composition | Public scheduler factory constructed and completed an empty tick. Native live firing/recovery remains deployment qualification. |
| U04: provider-owned read-only schema compatibility | Fresh, compatible and partial/corrupt SQLite states passed. Inspection and ordinary construction emitted no writes or explicit commits. |
| U05: runtime status and cooperative drain | Scheduler, run worker and action worker expose status and tolerate repeated idle drain. Active work, crash and process shutdown remain deployment qualification. |

Upstream #278–#282 are closed. No repeat issues were filed for these contracts.
Public API/source inspection also found the managed definition, run preparation,
run action/retry/rerun, report/artifact, immutable input resource, per-run request,
connector catalog, and action-handler configuration surfaces. API availability
does not establish every live acceptance scenario.

## Evidence and reproduction

- [Requirements reproducer](etlantic_0_57_1/requirements_probe.py)
- [Exact versions, Local descriptor, sort results and action failures](etlantic_0_57_1/requirements-probe.json)
- [Isolated headless contract probe](etlantic_0_57_1/headless-probe.json)
- [Isolated gateway contract probe](etlantic_0_57_1/gateway-probe.json)

Run the requirement probe from the repository root:

```sh
uv run --with etlantic-sql==0.57.1 python docs/reviews/etlantic_0_57_1/requirements_probe.py
```

It asserts all three ETLantic package versions are exactly 0.57.1. Its database is
disposable in-memory SQLite; no live PostgreSQL connection is needed to reproduce
missing dispatch handlers or Local compiler semantics.

Rerun the independent contract modes:

```sh
uv run --isolated --no-project --with etlantic==0.57.1 --with etlantic-sqlmodel==0.57.1 python docs/reviews/etlantic_0_57/contract_probe.py --mode headless --output docs/reviews/etlantic_0_57_1/headless-probe.json
uv run --isolated --no-project --with etlantic==0.57.1 --with etlantic-sqlmodel==0.57.1 --with etlantic-fastapi==0.57.1 --with httpx python docs/reviews/etlantic_0_57/contract_probe.py --mode gateway --output docs/reviews/etlantic_0_57_1/gateway-probe.json
```

The new reproducer passed Ruff formatting/lint checks. Both contract probes
passed. Historical 0.57.0 evidence was preserved separately.

## Remaining ShuETL release work

The confirmed gaps above prevent AC-028 and AC-033 qualification on the selected
published train. Other OPEN acceptance rows require ShuETL's PostgreSQL 18.6
process, grants, active drain/crash, live provider/extension, fault, deployment,
and hosted artifact evidence. Those missing proofs were not filed as upstream
feature defects. The evidence ledger and final artifact qualification remain
incomplete; this audit does not make 0.6.0 release ready.
