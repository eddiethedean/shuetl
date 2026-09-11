# Identity and Credential Integration

## Purpose

ShuETL connects a host application's authentication system to ETLantic's public
control-plane authorization and execution-context contracts.

It does not define a competing principal, authorization, service-account,
credential, secret, or audit domain.

## Integration flow

```text
Host identity system
  authenticates request
        ↓
ShuETL identity adapter
  maps trusted claims to ETLantic principal/context
        ↓
ETLantic authorizer
  evaluates ETLantic action and resource
        ↓
etlantic-fastapi route/service
        ↓
ETLantic durable submission
        ↓
ETLantic execution boundary
  resolves authorized runtime resources/secrets
```

## Adapter contract

ShuETL should accept the principal dependency and context/authorizer interfaces
published by the supported `etlantic-fastapi` and ETLantic release.

A host-specific adapter may:

- validate that required issuer/subject identity is present;
- map immutable host claims into ETLantic principal fields;
- select tenant/workspace/environment only from server-authoritative membership
  or routing information;
- add correlation information;
- reject unsupported or ambiguous identity.

It must not:

- trust caller-provided tenant or workspace identifiers without authorization;
- serialize provider ORM objects into ETLantic records;
- reinterpret an ETLantic authorization decision;
- resolve pipeline secrets in the gateway;
- silently substitute an application-global credential.

## Triggering and execution identities

ETLantic's canonical records distinguish the principal requesting a submission
from the workload identity or service account used during execution.

ShuETL preserves both identities through the FastAPI boundary. It does not
define new database fields or credential-binding semantics for them.

Scheduled work must never inherit the credentials of the user who created the
schedule.

## AuthMate

AuthMate is a potential reference identity and credential adapter, not a core
dependency and not an MVP prerequisite while it remains unimplemented.

An eventual AuthMate adapter must depend only on public APIs from both projects:

- AuthMate authenticates and supplies trusted principal/membership information;
- the adapter constructs ETLantic control-plane context;
- ETLantic authorizes ETLantic operations;
- ETLantic runtime providers resolve execution credentials through an approved
  integration contract.

ShuETL core must not import AuthMate persistence, token, or internal service
types.

## Other identity systems

The same boundary should support host implementations based on OIDC/OAuth2,
sessions, API gateways, workload identity, or application-defined FastAPI
dependencies.

ShuETL should publish adapter examples rather than embed a general-purpose
identity provider.

## Local development

Local unauthenticated or static-principal behavior must be explicit in
`ShuETLSettings`, labeled development-only, and rejected by production
readiness checks.

## Compatibility testing

Core MVP tests use a small fake host principal dependency and the supported
ETLantic authorizer contract.

Optional integration suites may later cover:

- ShuETL + AuthMate;
- Hedron + ShuETL + AuthMate;
- the full Hedron + AuthMate + ShuETL + ETLantic application.

Those suites validate adapters; they do not transfer ETLantic authorization
semantics into ShuETL.
