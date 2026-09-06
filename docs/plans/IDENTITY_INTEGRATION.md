# Identity and Credential Integration

## Purpose

ShuETL must cleanly integrate with standalone FastAPI-native identity and credential systems without embedding identity management into ShuETL core.

AuthMate is the reference integration.

## Core boundary

```text
Identity provider
  authentication
  authorization
  service accounts
  credentials
  audit
        │
        ▼
ShuETL
  pipeline registry
  versions
  schedules
  runs
  artifacts
        │
        ▼
ETLantic
```

## Required provider contracts

ShuETL should define or depend on minimal public protocols for:

- `PrincipalRef`
- `ResourceRef`
- `AuthorizationDecision`
- `AuthorizationProvider`
- `ServiceAccountProvider`
- `CredentialResolver`
- `AuditSink`

These contracts must not expose provider-specific ORM types.

## Resource namespace

ShuETL owns permission/resource names such as:

```text
shuetl.pipeline
shuetl.pipeline_version
shuetl.schedule
shuetl.run
shuetl.artifact
```

and action names such as:

```text
shuetl.pipeline.read
shuetl.pipeline.run
shuetl.schedule.manage
shuetl.run.cancel
shuetl.artifact.read
```

The identity provider evaluates these names but does not define ShuETL semantics.

## Manual execution

```text
User
  ↓ authenticate
Authorize shuetl.pipeline.run
  ↓
Create Run(triggering_principal=user)
  ↓
Resolve pipeline service account
  ↓
Authorize credential use
  ↓
Resolve secrets
  ↓
Execute ETLantic
```

## Scheduled execution

```text
Schedule
  ↓
Run
  ↓
Pipeline service account
  ↓
Credential authorization
  ↓
Secret resolution
  ↓
ETLantic
```

A schedule must never inherit a creator's credentials.

## Hedron composition

Hedron may consume the same external provider to shape UI presentation.

For example, a Run button may be hidden when `shuetl.pipeline.run` is denied, while ShuETL independently enforces that permission at the API/service layer.

This yields:

```text
Hedron        -> presentation
AuthMate      -> identity/security
ShuETL        -> pipeline operations
ETLantic      -> pipeline execution
```

all within one FastAPI deployment if desired.

## Security rules

- no resolved secrets in pipeline definitions;
- no provider-specific identity objects serialized into ETLantic plans;
- no UI-only authorization;
- no silent fallback to global credentials;
- deny/block on missing required security evidence in production;
- secret resolution occurs as late as practical;
- credential use is auditable;
- disabling a service account or credential affects future runs immediately according to provider policy.

## Compatibility matrix

Required:

```text
ShuETL standalone/local
ShuETL + external identity provider
ShuETL + AuthMate
Hedron + ShuETL + AuthMate
Hedron + ShuETL + AuthMate + ETLantic
```
