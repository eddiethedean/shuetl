# ShuETL Security

## Security posture

ShuETL exposes a control plane capable of triggering data movement. Its security
responsibility is to preserve and correctly compose host and ETLantic security
boundaries—not to create a second identity or secret system.

## Responsibility split

### Host application or identity provider

- authenticates users and workloads;
- validates tokens, sessions, or trusted proxy identity;
- supplies an immutable principal;
- owns credential issuance and revocation;
- owns TLS, top-level middleware, CORS, CSRF where applicable, and proxy trust.

### ETLantic

- defines control-plane principal/context and authorization contracts;
- owns action/resource semantics for ETLantic operations;
- enforces durable-submission and runtime trust rules;
- owns secret references, plugin allowlists, execution envelopes, redaction,
  artifact authorization, and audit evidence contracts.

### ShuETL

- adapts host identity into ETLantic's public context;
- requires explicit security configuration for production profiles;
- wires the authoritative ETLantic authorizer and providers;
- preserves authorization and non-enumeration behavior through mounting;
- validates that selected providers satisfy the deployment profile;
- documents residual risks and secure deployment requirements.

## Secure defaults

Production mode must fail closed when:

- no authenticated principal adapter is configured;
- no conforming ETLantic authorizer is configured;
- a required policy, registry, submission, event, schedule, or artifact provider
  is unavailable;
- package or database schema compatibility cannot be established;
- an execution host lacks required trust/capability evidence;
- a configured plugin or destination is not allowlisted.

An unauthenticated mode may exist only under an explicit local-development
profile. It must not be selected by missing configuration.

## Authorization

ShuETL does not define its own permission namespace for ETLantic resources. It
uses ETLantic's action/resource contracts and preserves service-level checks.

Mounting and presentation must not weaken:

- authorization before resource lookup;
- tenant/workspace/environment scoping;
- list filtering before pagination;
- event-stream and cursor authorization;
- artifact metadata and access authorization;
- cancellation, retry, replay, and administrative action checks.

## Code and plugin trust

ShuETL accepts only ETLantic-supported canonical definition forms and trusted
application registration paths.

The public API must not accept arbitrary Python source, import paths, package
installation, plugin entry points, filesystem paths, or network destinations
unless an upstream ETLantic contract explicitly permits and validates them.

Mutually untrusted code must run in separate processes or containers.

## Secrets

ShuETL configuration contains secret references or provider configuration, not
resolved pipeline credentials.

Secret values must not enter:

- ShuETL settings serialization or diagnostics;
- pipeline definitions or plans;
- HTTP request/response models;
- logs, events, reports, or audit metadata;
- schedule records;
- compatibility or readiness reports.

Resolution occurs inside the authorized ETLantic execution boundary through an
upstream secret/resource provider.

## Denial-of-service controls

ShuETL configures and tests upstream bounds for:

- request and parameter size;
- pagination and list filters;
- event-stream duration and concurrency;
- inline report/artifact previews;
- submission rate and concurrency;
- schedule frequency and catch-up;
- execution capacity.

If the selected providers cannot enforce required production bounds, readiness
fails.

## Auditability

Security and operational events use ETLantic audit/event contracts. ShuETL may
attach bounded composition metadata such as deployment role and package
versions, but it does not maintain a competing audit log.

## Migration and startup safety

ShuETL does not infer or automatically apply production DDL. It verifies provider
schema compatibility and either invokes a documented provider migration command
or stops with an actionable diagnostic.

## Security testing

The integration suite must cover:

- missing and invalid identity;
- authorization before lookup;
- cross-scope list, cursor, SSE, and artifact access;
- provider outage fail-closed behavior;
- redaction across errors, logs, OpenAPI examples, events, and readiness output;
- malicious definitions, parameters, URIs, and plugin identifiers;
- gateway/worker role separation;
- incompatible package and database schema rejection.
