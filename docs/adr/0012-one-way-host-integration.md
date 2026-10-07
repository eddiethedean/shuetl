# ADR-0012: One-Way Host Integration and Headless Composition

- Status: Accepted
- Date: 2026-09-29

## Context

ShuETL was initially framed mainly as a FastAPI route-composition package. An
independent host application such as Data Mover needs to use ETLantic as its ETL
backend while retaining its own UI, account model, credential store, and
product-specific behavior. Such a host may not expose the ETLantic HTTP API and
must not need to call its own server over HTTP.

ShuETL must remain independent of downstream hosts. A host may depend on a
versioned ShuETL release; ShuETL must not acquire a runtime, build, or test
dependency on a particular adopter.

## Decision

1. The supported dependency direction is `host application → ShuETL → ETLantic`.
   Data Mover is a downstream reference adopter, not a ShuETL component.
2. ShuETL supports FastAPI composition and headless in-process composition.
   Headless use composes public ETLantic services and records without requiring
   a listener or loopback HTTP. It does not introduce ShuETL-owned pipeline,
   run, schedule, event, report, or artifact semantics.
3. ShuETL uses only public ETLantic service and provider contracts. If a required
   headless operation is not public, the operation is added upstream before
   ShuETL supports it; private imports and alternate domain APIs are not
   accepted substitutes.
4. Host applications retain ownership of UI, identity, account-to-scope
   mapping, credential enrollment/storage, host schemas, and host-specific
   migrations. ETLantic owns canonical ETL control-plane and execution state.
5. Connector, credential-resource, and execution extensions are supplied by
   ETLantic provider packages or independent backend packages that implement
   public ETLantic contracts. ShuETL selects, composes and reports their
   capabilities without host-specific package requirements or hard-coded
   imports. ADR-0013 requires a standard profile configured without app provider
   factories; explicit provider-object injection remains an advanced surface.
6. ShuETL maintains generic host fixtures and a consumer conformance contract.
   Each adopter validates a released ShuETL artifact in its own repository.
   ShuETL core CI does not checkout or import adopter source.
7. Pure authoring checks have no provider I/O or secret resolution. Pipeline
   workers resolve resources after claim; catalog/test/preflight use separately
   authorized isolated provider actions before pipeline submission. The gateway
   receives safe results. Sample preview also uses the execution boundary.

## Consequences

The application-facing integration contract includes a headless composition
mode, provider capability discovery, trusted principal/resource mapping,
execution-scoped secret resolution, result/event projection guidance, and
role-separated runtime support. The host can retain a read-only UI projection
keyed by ETLantic identities but cannot become a second source of run truth.

ShuETL may mention Data Mover as a qualification consumer in its documentation.
It cannot add a `datamover` extra, Data Mover tables/routes/connectors, or
Data-Mover-specific branches. Data Mover owns its consumer dependency pin,
selection of independent backend packages, existing-record migration and
rollback procedure. Connector implementations belong in the backend packages.

[ADR-0013](0013-specifications-and-backend-ownership.md) strengthens this boundary:
the standard consumer controls specifications and commands without provider
factories or application ETL logic. Provider-object injection remains an
advanced surface. One backend command owns preparation and submission.

## Alternatives

- Make ShuETL depend on or embed Data Mover; rejected because it reverses the
  desired package boundary and prevents independent use.
- Require an embedding host to publish ETLantic routes and call them over
  loopback HTTP; rejected because it adds a network/service dependency without
  improving canonical upstream semantics.
- Add a Data-Mover-specific `validate`/`plan`/`run` API and shadow records to
  ShuETL; rejected because product logic and ETL semantics belong to the host
  and ETLantic, respectively.
- Allow ShuETL to access private ETLantic internals when a service operation is
  missing; rejected because such an adapter cannot have a reliable public
  compatibility contract.

## Validation

See [HOST_INTEGRATION.md](../plans/HOST_INTEGRATION.md) and the 0.5–0.9 host
integration gates in [ROADMAP.md](../plans/ROADMAP.md). ShuETL's generic
conformance suite proves the public boundary without an adopter installed.
Data Mover's own integration suite installs a released ShuETL wheel and proves
its account, credential, connector, run-monitoring, migration, and deployment
flows against that artifact.

[PHASE_0_5_EXECUTION.md](../plans/PHASE_0_5_EXECUTION.md) specifies the next
contract pilot and the upstream inventory/interface gates. The
[capability delivery matrix](../plans/CAPABILITY_DELIVERY.md) separates that
pilot from live provider and production qualification. This decision does not
assert that the headless surface already ships in 0.4.

## Revisit trigger

Revisit if ETLantic does not provide public service-level APIs required for
headless use, if an upstream provider cannot support the necessary host
resource/connector contracts, or if a proposed change would introduce a
reverse dependency on a consuming host.
