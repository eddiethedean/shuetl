# ShuETL Vision

## Purpose

ShuETL gives application developers a supported, opinionated way to configure,
embed, expose, and operate ETLantic without assembling every ETLantic
control-plane provider and deployment role themselves. FastAPI route mounting
is one supported mode; a host may also use the configured ETLantic services
in-process without exposing a public ETL API.

A developer supplies canonical specifications, trusted identity/resource
integration and deployment configuration. ShuETL provides the supported backend
profile and command surface; ETLantic and its providers own preparation,
extraction, transformation, validation, loading, scheduling and recovery. The
standard app needs no runtime provider graph, connector implementation or ETL
coordinator. FastAPI hosts may also mount the authoritative HTTP surface.

ShuETL is independent of any particular host product. Data Mover is a named
downstream reference adopter: Data Mover may depend on a released ShuETL
package, while ShuETL has no Data Mover runtime, build, or test dependency.
ShuETL's provider-neutral host contract must remain useful to other consuming
applications.

## Product boundary

ETLantic owns the canonical meaning and behavior of pipeline definitions,
plans, execution, scheduling, durable work, retries, cancellation, reports,
events, artifacts, secrets, and provider protocols.

`etlantic-fastapi` owns the low-level ETLantic HTTP schemas, routes, errors, and
streaming semantics.

ShuETL owns:

- an ergonomic FastAPI composition facade;
- selection and configuration of ETLantic providers;
- application lifecycle and deployment-role integration;
- safe local defaults and explicit production profiles;
- compatibility validation across the selected package set;
- optional adapters to host identity and presentation systems;
- headless in-process composition for host applications that do not expose the
  ETL API over HTTP;
- operator-oriented documentation and integration tests.

ShuETL does not define a second pipeline representation, run state machine,
scheduler, executor protocol, artifact model, retry engine, secret resolver, or
migration system.

## Product principles

### Specifications control behavior

For every advertised ETL capability, the application changes its canonical
specification and issues backend commands. It controls supported sources,
parameters, mappings, transforms, rules, writes, schedules and execution policy
within explicit authorization/operator limits. The backend owns the algorithms,
computed plans and runtime state. Unsupported behavior is rejected rather than
delegated to application code. See [SPECIFICATION_CONTRACT.md](SPECIFICATION_CONTRACT.md).

### Complete developer control

The default experience preserves a path to every qualified public backend
control. Apps may author graphs programmatically, override permitted settings
per run, choose execution profiles, manage run lifecycles and compose business
workflows. Developers may supply private connectors, transformations, engines
and hooks through upstream extension contracts. ShuETL preserves those choices
without requiring an ETL runtime in the app or changes to ShuETL core. The
[developer-control contract](DEVELOPER_CONTROL.md) makes coverage and extension
proof part of qualification; the bounded baseline is a minimum capability set.

### Integration over reimplementation

Every exposed ETLantic capability retains its upstream model, identity,
versioning, validation, and failure semantics.

### One contract at every boundary

Python, HTTP, persistence, events, and tests should refer to the same ETLantic
records. ShuETL-specific models are limited to ShuETL configuration and
composition diagnostics.

### Explicit capability discovery

ShuETL reports which features are available from the configured providers. A
missing provider produces a clear unavailable/readiness result rather than a
partial ShuETL reimplementation.

### Safe deployment profiles

One-process execution is a local-development convenience. Production separates
the FastAPI gateway from scheduler/worker execution while allowing the roles to
share one installation, image, and SQL database.

### Upstream-first gaps

When ETLantic lacks a canonical semantic capability, ShuETL should contribute
the capability upstream or wait for an upstream contract. Temporary adapters
must be narrow, versioned, and explicitly non-authoritative.

### Stable host experience

ShuETL absorbs ordinary provider wiring and compatibility checks so host
applications do not need to understand every ETLantic implementation package.

## Primary users

- application developers who want to embed ETLantic as a backend;
- FastAPI developers who want to expose ETLantic operations through HTTP;
- operators who want a documented, supported deployment topology;
- ecosystem integrators connecting identity, UI, and observability systems to
  ETLantic through FastAPI.

## Success criteria

ShuETL succeeds when it materially reduces the integration and operational work
required to deploy ETLantic while preserving exact ETLantic behavior.

One success measure is that an independently developed host application can
install a supported ShuETL release, use ETLantic through the host integration
contract, and own all host-specific UI, identity, credentials, and data without
ShuETL importing or understanding that application.

The required stronger proof is a reference app that changes supported ETL
behavior by changing specifications alone. It contains no connector, planner,
rule evaluator, preflight/submission coordinator or execution/recovery loop.
The complete baseline includes bounded transformations and validation; a
transfer-only profile is an intermediate release. Advanced provider injection
does not substitute for this standard consumer experience.

The same qualification must prove full specification/run control and an
optional private extension. A small reference app must not restrict real apps'
authoring style, business workflows, available backend actions or custom logic.

Success is not measured by the number of domain abstractions implemented by
ShuETL. Prefer fewer ShuETL abstractions, smaller adapters, and more upstream
contract reuse.

## Non-goals

- implementing a general-purpose workflow orchestrator;
- redefining ETLantic pipeline, execution, scheduling, or result semantics;
- maintaining copies of ETLantic Pydantic or persistence models;
- unrestricted imports or package installation from request values; qualified
  code/SQL/UDF artifact contracts remain valid extension paths;
- running mutually untrusted code in the FastAPI process;
- hiding production topology or security requirements behind a development
  convenience factory;
- promising that every ETLantic feature is available when its provider has not
  been configured.
