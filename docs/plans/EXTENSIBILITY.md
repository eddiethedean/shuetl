# ShuETL Extensibility

## Principle

ShuETL is extensible at the composition boundary.

> **Extend how ETLantic is configured and hosted; use ETLantic extension
> contracts for what ETLantic means and does.**

Broad domain-level extensibility in ShuETL would create a second plugin system
and is intentionally out of scope. Developers can extend pipeline behavior
through ETLantic's public contracts, including private implementations. Existing
extension points require no ShuETL core changes or upstream contribution.
See [DEVELOPER_CONTROL.md](DEVELOPER_CONTROL.md) for the complete control contract.

## One-way host relationship

Host applications install and depend on ShuETL. ShuETL stays independent of
those applications: it has no host-specific imports, extras, schemas, routes,
connectors, configuration branches, or test-time source dependencies. Data
Mover is a reference adopter whose own repository consumes released ShuETL
versions and tests its integration there.

The host keeps its product UI, identity, account model, credential enrollment,
application tables and canonical business specifications. Backend provider
packages supply connector and processing implementations and must be installable
without the consuming application. ShuETL's standard profile selects/configures
those providers; an app selects capabilities and supplies logical references.

Platform integrators may explicitly inject conforming provider objects through
public ETLantic protocols. This advanced surface is separate from the required
standard app path, which must not need provider factories, connector code or
ETL runtime orchestration. Apps may still compose business workflows over backend
commands. See [SPECIFICATION_CONTRACT.md](SPECIFICATION_CONTRACT.md).

Independent installation is an execution boundary, not a repository or
publication rule. A private extension may live beside the app in the same
repository. Its versioned backend package/artifact must load without importing
the host web app or its request context. The deploying team may qualify this
profile without inclusion in ShuETL's centrally supported provider list.

## Supported composition extensions

### Advanced provider composition

Platform/deployment code may construct a graph from independent backend
providers and supply the prebuilt API through the existing public facade:

```python
integration = ShuETL(api=prebuilt_etlantic_api)
```

The provider object remains an ETLantic provider. ShuETL does not wrap it in a
new semantic interface.

This is an advanced integration example, not the future standard app setup.
The standard profile is required to assemble the graph from deployment
configuration plus identity/resource bridges. New ETL primitives are added to
independent provider packages and selected through specifications; per-row
application callbacks or hidden legacy execution are not supported shortcuts.

### Custom processing and complete configuration

Developers may implement connectors, transforms, validators, UDFs, executors
and lifecycle hooks through public ETLantic extensions. The qualified backend
owns their invocation, resource access, cancellation and recovery. SQL/code
engines may accept immutable code artifacts or versioned source according to
their own contracts; ShuETL must not impose a built-in-operators-only language.

Extension schemas, engine/provider settings, version pins and permitted run
overrides remain available through canonical typed contracts. A convenience
preset cannot discard an extension field or require a wrapper change for each
new field. Existing implementation code may be reused if it satisfies backend
ownership and conformance; moving its files alone does not prove that boundary.

### Configuration presets

Organizations may define validated presets for:

- local development;
- PostgreSQL deployments;
- gateway, scheduler, and worker roles;
- approved optional ETLantic provider combinations;
- logging, metrics, and tracing integration;
- security requirements and deployment bounds.

Presets select capabilities; they cannot weaken upstream invariants silently.

### Identity adapters

A host adapter may map a trusted principal into ETLantic's public
control-plane context.

Adapters cannot:

- replace ETLantic authorization decisions;
- trust caller-selected scope without verification;
- expose provider ORM or token internals;
- resolve execution secrets in the gateway.

### FastAPI host integration

Hosts may customize:

- mount prefix and documented route preset;
- top-level lifespan composition;
- middleware owned by the host;
- dependency overrides;
- approved exception-handler integration;
- application metadata.

Customizations must preserve upstream route and schema semantics.

### Presentation adapters

Optional Hedron or other UI adapters consume the mounted ETLantic API/services
and authorization context. They do not become an authorization boundary or
define control-plane truth.

An embedding host may instead render ETLantic outcomes in its existing UI. That
UI consumes canonical upstream service results and may persist projections
keyed by ETLantic identities. It does not need to call the host's own HTTP API
or become an authorization boundary.

### Operational adapters

ShuETL may package configuration for process supervisors, containers,
observability exporters, or deployment platforms. These adapters invoke public
ShuETL and ETLantic entry points.

## Extensions that belong upstream

The following must use ETLantic extension points rather than ShuETL registries:

- pipeline and transformation semantics;
- executor/runtime implementations;
- schedule trigger types and firing policy;
- retries, cancellation, replay, and repair;
- artifact stores and artifact types;
- event payload types and publishers;
- report stores;
- durable submission and lease providers;
- secret/resource providers;
- policy and authorization providers.

If ETLantic lacks the necessary public extension contract, resolve that gap
upstream.

## Persistence extension

ShuETL does not offer subclassable SQLModel control-plane entities or managed
autogenerated migrations.

Applications needing additional metadata should prefer:

1. an upstream ETLantic metadata/extension field with bounded, versioned
   semantics;
2. a host-owned table keyed by the canonical ETLantic identity;
3. a separate host service or projection.

Host tables remain under host migrations. ETLantic provider tables remain under
provider migrations.

## Lifecycle

ShuETL lifecycle hooks are limited to application composition, such as provider
construction, readiness evaluation, and host lifespan cleanup.

Pipeline, run, schedule, artifact, and event lifecycle hooks belong to ETLantic.
ShuETL must not provide a second `before_run_execute` or similar hook sequence.
Developers may register implementations using the qualified upstream hook
contracts. Apps may independently consume events for product actions and
business workflows; those consumers do not replace backend execution hooks.

## Registration

Prefer ordinary constructor injection and explicit provider bundles over a
global plugin registry.

If named preset discovery is later required, it must:

- use explicit allowlists in production;
- inspect metadata before importing code where possible;
- report package identity and version;
- avoid caller-controlled entry-point loading;
- remain limited to composition factories.

Applications may select already registered capability identifiers and code
artifact references permitted by the backend. The restriction is on loading
arbitrary imports from requests, not on choosing among installed extensions.

## Conformance

Every composition extension must prove:

- it returns or configures public ETLantic providers;
- ETLantic identities and schemas are preserved;
- package/version compatibility is checked;
- startup and cleanup are deterministic;
- missing dependencies fail clearly;
- secrets are redacted;
- production security requirements cannot be downgraded implicitly;
- the same upstream contract passes when mounted without the extension;
- a consuming host can use the supported headless composition mode without
  importing ShuETL private modules or calling its own HTTP routes;
- ShuETL imports and tests successfully when the host application and all
  host-specific packages are absent;
- complete typed extension configuration survives canonical import/export,
  submission and result inspection without a ShuETL-specific whitelist;
- custom code executes through its declared backend lifecycle and needs no
  live app callback, web process or application ETL recovery loop.
