# ShuETL Model and Persistence Strategy

## Principle

ShuETL does not own a parallel persistent control-plane data model.

ETLantic models are canonical across Python, persistence providers, HTTP, SSE,
and worker execution. ShuETL wires those models into FastAPI and may define only
integration configuration and diagnostics that are genuinely ShuETL-specific.

## Authoritative model sourcing

| Concept | Source |
|---|---|
| Pipeline definition and revision | ETLantic |
| Resolved pipeline plan and fingerprint | ETLantic |
| Execution profile and binding references | ETLantic |
| Submission/run and attempt | ETLantic control-plane contracts |
| Lease, fencing, checkpoint, effect, replay, and repair | ETLantic control-plane contracts |
| Schedule revision and firing | ETLantic schedule contracts |
| Run report and diagnostic | ETLantic runtime/report contracts |
| Event envelope and resume identity | ETLantic event contracts |
| Artifact identity, metadata, ownership, and reference | ETLantic artifact contracts |
| Principal and authorization context | ETLantic control-plane contracts, populated by the host |

ShuETL must not copy these models merely to rename fields or use a different base
class.

## Definition and revision rules

Registration accepts an ETLantic-supported canonical definition such as
`PipelineDefinition` and delegates revision creation to the configured
ETLantic registry.

ShuETL must preserve:

- the upstream definition schema identifier;
- revision identity;
- definition and plan fingerprints;
- profile/environment revision identity;
- ETLantic and plugin compatibility information;
- upstream validation diagnostics.

An importable Python object may be an authoring source, but it is not itself a
durable immutable revision. ShuETL relies on ETLantic's canonical serialized
definition and revision contracts.

## Durable submission rules

The selected ETLantic store remains authoritative for:

- caller-scoped idempotency keys and request fingerprints;
- accepted, dispatched, leased, running, terminal, and reconciliation states;
- append-only attempt history;
- lease ownership and fencing tokens;
- outbox or equivalent durable dispatch;
- checkpoints and external-effect evidence;
- cancellation, retry, replay, repair, and backfill distinctions.

ShuETL forwards these records unchanged through the authoritative FastAPI
adapter. It must not collapse them into a smaller ShuETL `Run` row.

## Scheduling rules

Schedules and firings use ETLantic schedule models.

Historical behavior must retain:

- schedule revision identity;
- nominal firing time;
- logical firing/idempotency key;
- timezone and DST policy;
- overlap and misfire decisions;
- the selected immutable definition/profile revisions;
- the resulting durable submission identity.

ShuETL does not maintain its own `next_run_at` calculation or scheduler lease.

## Results, reports, events, and artifacts

ShuETL exposes ETLantic records without changing their meaning.

- Reports remain ETLantic `PipelineRunReport`-compatible records.
- Events retain upstream event identity, ordering, schema version, and cursor
  semantics.
- Artifact metadata retains upstream ownership, classification, bounds, and
  logical location.
- Large result data stays outside generic control-plane response bodies.

Presentation-specific summaries may be derived, but they must identify their
source revision and must not masquerade as canonical records.

## ShuETL-owned models

ShuETL may define Pydantic models for:

- `ShuETLSettings`;
- deployment-role selection;
- provider configuration references;
- API mounting options;
- compatibility and capability reports;
- readiness diagnostics;
- optional adapter configuration.

These models must not reproduce ETLantic domain fields.

ShuETL should own no database tables in the MVP. If a later feature genuinely
requires ShuETL persistence, it needs an ADR explaining why the information
cannot live in host configuration or an ETLantic provider.

## Persistence providers

### Tests and local development

Use ETLantic memory providers or explicitly supported SQLite-backed providers.
Local convenience data may be disposable unless the selected provider documents
durability.

### Production reference

Use the PostgreSQL-capable stores supplied by `etlantic-sqlmodel` or another
conforming ETLantic provider. ShuETL configures them and reports readiness; it
does not implement their transactions or queries.

## Migration ownership

- ETLantic provider packages own migrations for their tables.
- The host owns migrations for application tables.
- AuthMate owns migrations for AuthMate tables when used.
- ShuETL owns migrations only if it later introduces explicitly approved
  ShuETL-specific tables.

ShuETL may expose commands that call documented provider status/upgrade
operations. It must not autogenerate migrations from arbitrary application model
subclasses or run inferred production DDL at startup.

## Schema and API compatibility

ShuETL pins and tests an explicit ETLantic minor-version range. Startup or
application construction should fail with a typed diagnostic when:

- required public contracts are absent;
- provider schema revisions are incompatible;
- installed ETLantic packages are from unsupported release trains;
- configured capabilities cannot satisfy the selected deployment profile.

Compatibility adapters must be small, versioned, and removed when their support
window closes.

## Testing obligations

Contract tests should prove:

- objects returned through ShuETL are the authoritative ETLantic models or
  lossless documented HTTP representations;
- definition, submission, schedule, event, and artifact identities survive
  FastAPI round trips;
- no ShuETL persistence layer can diverge from the configured ETLantic store;
- unsupported provider combinations fail before serving traffic;
- upgrades are tested with provider-owned migrations and rollback guidance.
