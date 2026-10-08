# ETLantic 0.56.2 Wheel Audit

This audit covers the published 0.56.2 artifacts selected by the Phase 0.6
implementation. It supersedes the 0.56.0 findings for import isolation and
migration-version inspection; ShuETL still has to qualify the behavior through
its installed artifact and PostgreSQL role tests.

## Published artifacts

The package versions and hashes below were read from the PyPI release metadata
and checked against the published wheel bytes.

| Distribution | Wheel | SHA-256 |
| --- | --- | --- |
| `etlantic` | `etlantic-0.56.2-py3-none-any.whl` | `ab21c220d2a7bafe474feac98f9c8d67c18ed661b20978adf5d2978aa1629666` |
| `etlantic-fastapi` | `etlantic_fastapi-0.56.2-py3-none-any.whl` | `32d3ca78177a8d596fecabadd37bd8bd767356aa4f2bc58b1b46ee9341714b74` |
| `etlantic-sqlmodel` | `etlantic_sqlmodel-0.56.2-py3-none-any.whl` | `30296beb00da0f92edd1d38dc0470050c1032ab49025fac11adaae62250d6225` |
| `etlantic-sql` | `etlantic_sql-0.56.2-py3-none-any.whl` | `5685b86d5a881d91ea9fddee05a92355bd785d478062681aa2404f082e641c17` |
| `etlantic-foundry` | `etlantic_foundry-0.56.2-py3-none-any.whl` | `4b6feccc1d6bf0eb5b59e390401a429f99fa506e029fd87b4d03ea55ad72b89a` |

The upstream release is [ETLantic v0.56.2](https://github.com/eddiethedean/etlantic/releases/tag/v0.56.2), source commit
[`fc798e4297340d91d887686e6ac2492bc288728a`](https://github.com/eddiethedean/etlantic/commit/fc798e4297340d91d887686e6ac2492bc288728a).
The ShuETL findings that motivated the release are tracked by
[ETLantic issue #273](https://github.com/eddiethedean/etlantic/issues/273),
closed as completed.

## Relevant API checks

| Finding | Published-wheel observation | ShuETL requirement |
| --- | --- | --- |
| FastAPI gateway imports execution modules | A fresh Python 3.13 environment importing `etlantic_fastapi==0.56.2` loaded neither `etlantic.runtime.execute` nor `etlantic.runtime.action_execution_host`. `etlantic_fastapi.managed` keeps its `ActionExecutionHost` import under `TYPE_CHECKING` and imports run/action hosts only inside their constructors. | Keep a clean-wheel fresh-process assertion and exercise gateway startup and requests without worker ticks. |
| Managed startup runs migration DDL | `etlantic_sqlmodel.migrations.current_version()` first checks for the version table and then issues a `SELECT`. `create_managed_backend()` rejects a missing table before calling this check and rejects a version behind the latest migration. Table creation remains in explicit migration functions. | Exercise startup using the actual runtime database role without schema `CREATE`, table ownership, or migration grants; compare schema state before and after. |

The public migration head remains
`014_cp1_complete_principal_idempotency_0_56`. An isolated environment
resolved ETLantic core, FastAPI and SQLModel to 0.56.2 and the source checks
above were performed against those installed wheels. A PostgreSQL 18.6 role
test is still required to establish the ShuETL runtime privilege contract.

## Limits

Upstream release notes and wheel inspection establish package contents and
import/migration behavior. They do not qualify ShuETL's managed graph, actual
runtime grants, multiprocess behavior, action workers, provider capabilities,
failure recovery, deployment or transition procedures. Those remain Phase 0.6
acceptance evidence.
