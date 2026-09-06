# Dependency Strategy

## Principle

ShuETL should own pipeline-operation semantics while delegating scheduling, persistence, retries, filesystems, and optional worker mechanics to mature libraries.

> **Own the contracts; reuse the mechanics.**

## Core dependencies

```text
fastapi
pydantic
pydantic-settings
sqlmodel
sqlalchemy>=2
alembic
apscheduler>=3.11,<4
tenacity
etlantic
```

## APScheduler

Use APScheduler 3.11.x as the MVP timing engine.

ShuETL remains authoritative for Schedule records, version policy, concurrency/misfire semantics, next-run bookkeeping, and durable Run creation.

APScheduler owns cron/interval/date trigger mechanics and timer behavior.

Do not persist APScheduler objects as ShuETL's canonical schedule model.

## Tenacity

Use for bounded retry/backoff mechanics where appropriate. ShuETL owns retry policy and reason-code semantics.

## Artifact extra

```text
shuetl[artifacts]
  fsspec
  universal-pathlib
```

Use for normalized local/cloud filesystem access while keeping ShuETL's artifact model provider-neutral.

## Distributed execution extras

Preferred first backend:

```text
shuetl[dramatiq]
```

Later compatibility:

```text
shuetl[celery]
```

Local execution remains the default and must not require Redis/RabbitMQ.

## Rules

- Public Schedule/Run/Executor schemas expose no backend-specific types.
- Backend changes cannot alter durable run-state semantics.
- Optional backends are conformance-tested.
- Heavy/cloud dependencies stay lazy and optional.

## SQLModel

Prefer `sqlmodel` for ordinary persistent control-plane entities.

Keep direct SQLAlchemy available for advanced scheduling/runtime coordination, locking, bulk queries, engine/session configuration, and Alembic integration.

## Infrastructure dependency rule

Python package dependencies are allowed when they run in-process.

The restriction applies to **external infrastructure/services**, not libraries.

Allowed default examples:

```text
FastAPI
Pydantic
SQLModel
SQLAlchemy
APScheduler
cryptography
SQLGlot
PyArrow
```

Not allowed as required default infrastructure:

```text
Redis
RabbitMQ
Kafka
OpenSearch / Elasticsearch
S3-compatible object storage
Vault
cloud secret managers
external schedulers
separate worker services
```

Optional adapters may support these without changing the baseline installation/deployment contract.
