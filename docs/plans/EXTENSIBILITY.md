# ShuETL Extensibility

## Principle

> **Useful defaults, extensible by contract.**

Every major ShuETL control-plane capability should expose a stable, typed extension surface where practical. Applications may extend supported persistence metadata, pipeline/run parameters, schedule and executor configuration, artifacts, events, publishers, policies, and lifecycle behavior without forking ShuETL.

> **Extensions must not weaken durable execution invariants implicitly.**

ShuETL remains authoritative for durable run identity/state transitions, schedule/run version binding, idempotency, concurrency policy, authorization boundaries, and secret-reference semantics.

## Extensible SQLModel metadata

Expose non-table SQLModel bases for selected entities where host applications commonly need domain metadata.

Potential supported bases:

```text
Pipeline metadata
Schedule metadata
Run metadata
ResultArtifact metadata
```

Conceptually:

```python
class Pipeline(ShuETLPipelineBase, table=True):
    __tablename__ = "shuetl_pipelines"

    owning_team: str | None = None
    business_domain: str | None = None
```

Do not make every internal coordination table subclassable. Run-claim leases, scheduler locks, migration state, and other correctness-critical internals remain ShuETL-owned.

## Managed Alembic migrations

As with AuthMate, developers should not need the Alembic CLI for normal supported ShuETL model extensions.

Expose a schema manager such as:

```python
shuetl.schema.status()
shuetl.schema.plan()
shuetl.schema.check()
shuetl.schema.upgrade()
```

and optional safe startup migration:

```python
ShuETL(
    pipeline_model=Pipeline,
    auto_migrate="safe",
)
```

Safe automatic changes are additive and validated. Destructive/ambiguous DDL is blocked for explicit action.

ShuETL and sibling packages sharing one database retain separate migration ownership/version namespaces.

## Extensible pipeline/run parameter contracts

Run parameters should support application-defined Pydantic models:

```python
class CustomerRunParameters(BaseModel):
    region: str
    full_refresh: bool = False
```

ShuETL validates parameters before durable execution and stores a versioned/serialized parameter snapshot appropriate for reproducibility.

Pipeline parameter schemas may be surfaced through JSON Schema/OpenAPI and consumed by Hedron or other clients.

## Schedule trigger extensions

ShuETL ships supported cron/interval/date trigger models but should define a typed trigger-provider contract so new schedule semantics can be added without changing core domain models.

All trigger providers normalize to ShuETL-owned schedule/next-run semantics and may not bypass durable Run creation.

## Executor extensions

Execution remains behind an `Executor` protocol.

Core ships `LocalExecutor`; optional/custom implementations may support Dramatiq, Celery, batch systems, containers, or organization-specific runtimes.

Executors must obey the same Run state machine, cancellation/result/error contracts, authorization context, and credential-reference behavior.

## Artifact providers and types

Applications may register additional artifact location/types and storage adapters using discriminated Pydantic contracts.

ShuETL retains authority over artifact identity, run relationship, metadata bounds, retention metadata, redaction, and authorization.

## Metadata publishers

Define a publisher protocol for Datdex, OpenLineage-style adapters, observability integrations, or custom metadata consumers:

```python
class MetadataPublisher(Protocol):
    async def publish(self, event: ShuETLEvent) -> None: ...
```

Publisher failure semantics must be explicit and cannot silently redefine pipeline success unless configured policy says so.

## Policy extensions

Typed provider contracts should cover configurable behavior such as:

- concurrency policy;
- retry policy;
- version-selection policy;
- preflight/activation policy;
- retention policy;
- artifact policy.

Default policies remain understandable and SQL-only.

## Event extensions

ShuETL owns a stable event envelope containing event identity, run/pipeline references, timestamps, correlation, producer, and event version.

Applications/adapters may register typed event payloads using Pydantic discriminated unions.

Core events include run/schedule/pipeline lifecycle, drift/preflight, artifact, and execution outcomes.

## Lifecycle hooks

Provide typed hooks/events for bounded customization, for example:

```text
before_pipeline_register
after_pipeline_register
before_pipeline_activate
after_pipeline_activate
before_run_create
after_run_create
before_run_execute
after_run_execute
run_failed
before_artifact_register
after_artifact_register
schedule_due
```

Hook ordering, transaction boundaries, timeout/cancellation, and failure semantics must be documented. Hooks may not bypass durable state transitions.

## Registration surface

Prefer explicit registration over monkey-patching:

```python
shuetl.register_executor(...)
shuetl.register_trigger_provider(...)
shuetl.register_artifact_provider(...)
shuetl.register_metadata_publisher(...)
shuetl.register_policy(...)
shuetl.register_hook(...)
```

## ETLantic boundary

ShuETL extensibility must not duplicate ETLantic's execution/inference/contract extension mechanisms. Pipeline-semantic extensions belong in ETLantic; control-plane extensions belong in ShuETL.

## Extension conformance

Ship conformance tests for extension families covering typed validation, async behavior, durable Run semantics, cancellation, error mapping, authorization context, secret redaction, lifecycle cleanup, and dependency-override testing.
