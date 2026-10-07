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
- reject unsupported or ambiguous identity;
- map a host account or owner identifier to a stable ETLantic principal and
  authorized workspace/resource scope using server-side membership;
- preserve the original triggering principal and configured workload identity
  as distinct canonical identities.

It must not:

- trust caller-provided tenant or workspace identifiers without authorization;
- serialize provider ORM objects into ETLantic records;
- reinterpret an ETLantic authorization decision;
- resolve pipeline secrets in the gateway;
- silently substitute an application-global credential;
- accept a caller-selected owner/workspace as proof of ownership.

## Triggering and execution identities

ETLantic's canonical records distinguish the principal requesting a submission
from the workload identity or service account used during execution.

ShuETL preserves both identities through the FastAPI boundary. It does not
define new database fields or credential-binding semantics for them.

Scheduled work must never inherit the credentials of the user who created the
schedule.

An embedding host may retain its own encrypted credential store. It supplies an
opaque, versioned secret reference through the public ETLantic resource-provider
contract. For pipeline work, resolution occurs in the worker after the run is
claimed and the reference's owner, provider, purpose, scope and version have
been authorized. Catalog/test/preflight use separately authorized isolated
provider actions; they do not require a pipeline submission merely to check a
connection. Those executors resolve their own bounded references and return
safe metadata. They never make credentials available to the gateway.
ShuETL does not read host credential tables, receive plaintext credentials in
the gateway, or provide a global-credential fallback.

Host-specific account/credential adapters are implemented by the host or a
separate compatible package. ShuETL configures their public ETLantic contracts
and reports readiness without depending on their application packages.

The provider contract declares pinned-version or explicitly authorized
late-binding behavior, including rotation, deletion, revocation and audit of
the resolved version. A `current` alias must not be treated as an immutable
credential. Recheck permission and revocation when the resource is used.

Headless calls receive trusted context per operation. Concurrent requests,
threads and callbacks must not share mutable principal state. No synthetic
HTTP request is required for authentication or resource authorization. The
0.5 pilot proves these boundaries with fake resource providers; live executor
isolation and credential resolution are 0.6 qualification work.

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

An independent host-application conformance suite should additionally cover a
multi-user host with per-owner definitions and credentials, even when the
qualified ShuETL deployment profile is single-tenant at the organization
boundary. Data Mover's integration tests belong in the Data Mover repository
and install a released ShuETL artifact; ShuETL core tests use generic host
fixtures only.

Those suites validate adapters; they do not transfer ETLantic authorization
semantics into ShuETL.
