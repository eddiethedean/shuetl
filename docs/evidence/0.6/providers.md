# Phase 0.6 provider and capability status

## Declared packages

| Package/provider | Composition status | ShuETL live qualification |
| --- | --- | --- |
| `etlantic-sql` 0.56.0 PostgreSQL source | Optional `sql` extra; selected for the integration fixture. | Open; hosted fixture result not yet captured. |
| `etlantic-sql` 0.56.0 PostgreSQL sink | Optional `sql` extra; connector uses a configured effect ledger and explicit write mode. | Open; hosted fixture result not yet captured. |
| ETLantic local immutable CSV source | Upstream capability; available when the profile and resource references select it. | Not advertised as qualified in the 0.6 deployment template. |
| ETLantic Foundry source/sink | Optional `foundry` extra pinned to 0.56.0. | Not advertised; requires a separate live integration and action-handler qualification. |
| Other providers and write modes | Not enabled by the reference deployment. | Unsupported until listed and qualified here. |

The first role integration test provisions distinct PostgreSQL source, target,
and effect-ledger tables. Its production profile uses ETLantic's local
dataframe engine for the straight-through transfer; PostgreSQL source and sink
access still use the `etlantic-sql` connectors. The profile allows
`etlantic-sql` with `>=0.50.0,<0.57.0` and `etlantic-local` with
`==0.50.0`. ETLantic SQL 0.56.0 exposes its SQL plugin at 0.56.0 and its SQL
transform compiler at 0.50.0 under the same plugin identity; ETLantic core's
`etlantic-local` compiler is also 0.50.0 and is not a separate distribution.
ShuETL validates the `etlantic-sql` specifier against the installed 0.56.0
distribution, and ETLantic validates the discovered plugin versions. The
project compatibility gate continues to pin every package in the selected
train exactly. The test uses upsert with an explicit key. The test source
contains no ShuETL connector or transform callback. It verifies both a manual
and a scheduled accepted run have successful ETLantic reports and visible sink
effects when run against the configured CI database. The control-plane
runtimes use a separate CI database role. ETLantic 0.56.0's managed-backend
constructor requires that role to have `CREATE` on the public schema because
its current-version helper executes `CREATE TABLE IF NOT EXISTS` unconditionally.
Test setup and observation use the disposable service administrator. This
broader runtime grant means the fixture does not satisfy the planned
least-privilege acceptance; AC-008 remains open.

That fixture is code only until the hosted PostgreSQL 18.6 result is captured.
No support claim is made for CSV-to-PostgreSQL, Foundry, append/replace modes,
transform and quality coverage, enabled-writer policy, schema drift, connector
actions, provisioning, or arbitrary user extensions. These remain open
acceptance work.

## Resources and credentials

The host integration supplies secret references and their worker-side
authorization. Gateway role bindings reject a secret alias authorizer and
provider action handlers. Run workers can receive a
`SecretAliasAuthorizer`; action handlers are constructed from separate provider
packages and selected only for `worker --kind actions`.

File input and report support requires an identical shared artifact root for
every role. Immutable checksum, owner/version access, mutation, expiry,
cross-worker availability, report delivery, credential redaction, and bounded
cleanup have no Phase 0.6 live result yet.
