# ADR-0013: Application Specifications and Complete Backend Ownership

- Status: Accepted
- Date: 2026-09-29

## Context

ADR-0012 establishes one-way host dependency and headless composition. A host
could still comply by constructing provider graphs, supplying connector
implementations and coordinating preparation before submission. That would
leave ETL implementation in an application such as Data Mover.

The intended boundary gives applications control of ETL specifications while
the backend owns all work required to execute the supported behavior.

## Decision

1. ShuETL owns the supported backend experience through public ETLantic
   services and provider packages. ETLantic remains the semantic authority;
   this responsibility does not introduce copied models or a new state machine.
2. The standard application path uses deployment configuration, trusted
   identity/resource integration, canonical specifications and backend commands.
   It does not require a provider graph, connector implementation, row callback
   or application ETL coordinator.
3. Applications control every advertised business specification option within
   authorization, operator policy and capability limits. The backend publishes
   schemas/constraints, enforces them and owns derived plans and fingerprints.
4. One logical backend submission command coordinates authorization, request
   normalization, deduplication, revision binding, planning, required preflight,
   admission and acceptance. Manual and scheduled execution share this command.
   Preparation may be asynchronous using upstream operation identity, without
   an application-owned preparation state machine.
5. Standard connector and transformation implementations ship in qualified
   backend packages independent of adopters. Custom ETL extensions also belong
   in independent provider packages. Existing advanced provider injection
   remains supported but does not satisfy the standard-consumer acceptance gate.
6. The complete ETL baseline requires bounded declarative transformations and
   validation. Transfer-only profiles may be intermediate releases. SQL,
   PySpark and other additional engines remain separately qualified options.
7. Qualification must prove a reference app can change supported specifications
   without ETL implementation changes, followed by a downstream cutover that
   removes application ETL code from the active execution path.
8. ShuETL preserves every qualified caller-facing specification, provider
   option, command and query through canonical interfaces or documented public
   service access. Defaults and the bounded baseline do not cap developer
   control. Per-run overrides and lifecycle actions remain upstream-defined.
9. Apps may use programmatic authoring, approval flows, external triggers and
   business workflows over backend runs. Developers may author private backend
   extensions, including qualified code/SQL/UDF functions and hooks. Independent
   installation does not require a separate repository or public publication.

## Consequences

[SPECIFICATION_CONTRACT.md](../plans/SPECIFICATION_CONTRACT.md) defines the
ownership matrix, operation contract and consumer proof. The 0.5 execution
plan must inventory and qualify the public upstream specification/submission
services before selecting concrete API symbols. Missing services are upstream
work; merely exposing individual providers is insufficient.

The restriction on duplicate domain APIs permits ergonomic delegation to public
upstream commands with unchanged records/errors. It forbids reimplementing
their semantics. Existing caller-owned facade/bundle contracts remain intact.

Applications retain their UI, business intent, authentication, credential
enrollment/storage bridges and product migrations. Operators retain deployment
supervision and policy. Neither responsibility requires ETL runtime logic in
the application. The minimal app is an acceptance fixture, not a restriction on
product code or developer-authored backend extensions.

[DEVELOPER_CONTROL.md](../plans/DEVELOPER_CONTROL.md) defines option parity,
effective run configuration, command semantics and extension requirements.
Explicit authorization, operator policy, state/effect preconditions and qualified
provider capabilities are the grounds for restricting a control. A narrow
ShuETL convenience interface must not introduce an additional restriction.

## Validation

HC-14 and HC-17–HC-23 in the
[delivery matrix](../plans/CAPABILITY_DELIVERY.md), H05-019–H05-032 in the
[0.5 execution plan](../plans/PHASE_0_5_EXECUTION.md), and the 0.6/0.7 gates in
the [roadmap](../plans/ROADMAP.md) enforce this decision. Source/import review
is paired with behavior; generic fixtures cannot substitute for live ETL
qualification or downstream retirement evidence.

## Revisit trigger

Revisit if a proposed standard integration requires an app to implement ETL
behavior, if a supported specification cannot be expressed through public
upstream contracts, or if an extension introduces a dependency on a consuming
application, or if ShuETL prevents use of an otherwise qualified public control.
Lack of an upstream service does not authorize host-side fallback.
