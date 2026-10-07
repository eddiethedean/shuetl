# Application Specifications and Backend Ownership

## Governing requirement

For every advertised ETL capability, an application changes canonical
specifications and issues backend commands. It does not implement extraction,
transformation, validation, loading, submission preparation or run recovery.

ShuETL owns the complete supported backend experience. ETLantic and its provider
packages own the canonical models, service semantics and implementation. This
internal division must not require an app to assemble its own ETL engine.
The package direction remains `application → ShuETL → ETLantic/providers`.

This is a planned contract under
[ADR-0013](../adr/0013-specifications-and-backend-ownership.md). The current 0.4
caller-owned facade remains supported as an advanced composition surface. The
required standard path starts with deployment configuration, identity/resource
integration and a pipeline specification, without a caller-built provider graph.

[DEVELOPER_CONTROL.md](DEVELOPER_CONTROL.md) requires complete exposure of
qualified public backend controls, per-run overrides, lifecycle commands,
programmatic authoring, business workflows and developer-authored extensions.
The standard path is a minimum convenient experience, not a ceiling on what
applications can express or control.

## Specification ownership

The application controls the intended business behavior. The backend owns the
canonical schema, validates the specification, produces the executable plan and
enforces the selected behavior. Exact field names and serialized forms must
come from qualified public ETLantic contracts; the following is a coverage
requirement, not a new ShuETL schema or proposed Python API.

| Application-controlled specification | Backend implementation responsibility |
|---|---|
| Source connector kind, connection/resource reference, locator, selection and supported source snapshot policy | Resolve resources, discover schema, read/page/stream data and enforce source identity |
| Typed parameters, defaults, required inputs and approved environment/profile references | Validate and bind values; normalize the canonical request and compute fingerprints |
| Ordered transformations or a supported logical graph, field mappings, casts, filters and expressions | Type-check and compile the graph, propagate schemas, select physical operations and execute them |
| Input/output schema contracts, quality rules, evaluation point, severity and permitted failure policy | Evaluate rules, enforce thresholds, collect safe diagnostics and apply supported failure/quarantine semantics |
| Destination, append/replace/upsert mode, keys, conflict behavior and supported schema-evolution policy | Check compatibility, stage/batch/load, manage transactions, verify publication and reconcile uncertain effects |
| Schedule, timezone, overlap/misfire policy and pinned/latest-approved definition selection | Calculate occurrences, deduplicate firings, bind revisions and invoke the standard submission service |
| Retry limits/backoff policy, cancellation, rerun/replay/backfill/repair and supported pause/resume intent | Enforce command/state/effect preconditions, manage leases/checkpoints, execute transitions and preserve lineage/effect evidence |
| Per-run parameters and supported overrides, engine/provider pins, resource profile, priority, execution hints, budgets and timeouts | Resolve the effective specification, enforce explicit operator constraints, plan execution and manage/clean up resources |
| Definition names, descriptions and allowed metadata | Persist canonical revisions and audit authorized changes |

Applications may set every supported business option through these
specifications. Operator policy can restrict capabilities, destinations and
budgets; the backend exposes those constraints and rejects violations with
field-level diagnostics. It must not silently ignore an option, substitute a
different behavior or ask the app to implement a missing primitive. Preserve
provider-specific typed settings and a public canonical service path beyond
convenience presets. Developers may supply new backend primitives through
upstream extension contracts without changing ShuETL core.

A requested retry cannot make an uncertain commit safe. A resource budget
cannot grant new privileges. These are enforced semantic and authorization
constraints, not application implementation tasks.

## Canonical authoring and discovery

The supported upstream authoring contract must provide:

- versioned, serializable definitions with typed parameter and operation schemas;
- discovery of supported connectors, transforms, rules, policies, allowed
  values, constraints and defaults, sufficient for an app to build its editor;
- normalization and field/node-level diagnostics using stable upstream codes;
- canonical export/import and revision preconditions, preserving specification
  meaning; schema upgrades use upstream migration contracts;
- an explanation of the resolved plan, inferred schema and required resources;
- explicit unavailability for unsupported behavior before pipeline acceptance.

The application creates logical specifications and may render plan output.
Computed fingerprints, physical plans, resolved engine/provider version bindings,
execution state, counters and checkpoints are backend-owned outputs. The
standard command path does not trust caller-supplied hashes or a claimed
successful preflight. Form binding and UI presentation are app concerns;
schema inference, data conversion and row evaluation are backend concerns.
Apps may request supported engine/version pins, planning hints and approved
plan references; the backend validates and resolves them. Backend ownership
of an output must not erase control over the inputs that determine it.

Logical definition revisions remain editable through new revisions. Runs accept
typed parameters and supported overrides without mutating the saved definition.
Accepted work pins its effective specification and resolved bindings; supported
later run controls are explicit audited commands. App export/import must
not require serializing an executable Python object, provider instance or
callback. Immutable code/SQL/UDF references may be specified through a qualified
backend engine contract. Secret values never become specification parameters.

## Standard command contract

These are conceptual operations to map to public ETLantic services during 0.5
qualification. They do not introduce route aliases or replacement models.

| App request | Required backend behavior |
|---|---|
| Discover capabilities and authoring schemas | Return the supported specification vocabulary and policy constraints |
| Validate or explain a draft | Perform pure authoring checks/planning and return canonical diagnostics or plan metadata |
| Save or revise a definition | Authorize, normalize, apply revision preconditions and persist a canonical revision |
| Submit a specification or revision with parameters, supported overrides and an idempotency token | Own the complete preparation/admission flow, record effective values and return its canonical operation or accepted submission outcome |
| Inspect a connection, browse a catalog or request a preview | Authorize and dispatch the bounded backend action; preserve action identity and safe results |
| Create/update/pause a native schedule or submit from an external trigger | Own native firing calculation and backend acceptance; preserve the declared scheduling authority and trigger identity |
| Discover and invoke authorized run controls, including retry/rerun and supported replay/backfill/pause/resume/repair | Apply state/effect preconditions, execute the transition and preserve command identity, lineage and audit |
| Read/subscribe to outcomes | Return canonical status, reports, events and authorized artifact references |

UI validation, explanation and preview can be separate user actions. They are
not required app-side stages that must be sequenced correctly to make a run
safe. Direct submission repeats all required backend checks itself. Apps may
choose staged authoring/approval flows and qualified immutable plan references;
the backend still owns verification and acceptance.

### Backend-owned submission preparation

One logical submission command must own authorization, canonical request
normalization/fingerprinting, scoped accepted-key lookup, revision/parameter
binding, planning, required preflight, admission and durable acceptance.
An identical accepted request is returned before repeating live checks;
changed fingerprints conflict. The app supplies the logical idempotency token
and reuses it after a lost response; the backend computes and owns its meaning.

This command may span several upstream transactions and isolated provider
actions. Long preflight may return an upstream preparation-operation identity;
the app can poll or subscribe, but does not advance preparation by calling the
next ETL service. Only a committed pipeline submission is durable acceptance.
Failed preflight may leave action/audit evidence, but no pipeline submission.
Response loss, concurrent submissions and host shutdown must not require an
app callback or a host-managed preparation state machine to resume safely.

Manual runs and schedule firings use this same backend service. Workers recheck
time-sensitive authorization and provider assumptions before effects. If
ETLantic lacks this public service, add it upstream before claiming support;
neither ShuETL nor the app may invent a competing admission state machine.
ShuETL may provide ergonomic delegation to those public services while
preserving their models, identities and errors.

## Connector and extension ownership

A supported backend profile supplies qualified connector implementations in
ETLantic provider distributions or independent backend extension packages.
Deployment configuration selects and installs them; the app supplies connector
identifiers, logical connection references and operation parameters. The
standard path must not require readers, writers, connector registries,
transaction handlers or provider factories in the application process.

New proprietary connectors and transformation primitives belong in independently
versioned backend provider packages implementing public ETLantic contracts.
They must be installable without the consuming application. They may be private
and maintained in the same repository; a separate public project or publication
is not required. Their capability metadata and conformance evidence become
part of the backend profile. Apps
then select the new capability in their specification. No per-row application
callback, copied legacy connector or hidden in-app fallback satisfies support.

Advanced provider injection remains available for platform integrators and
existing deployments. It is not the standard application path and cannot be
used as evidence that specification-driven consumption is complete. This is
an optional developer capability, not a prohibition on expert integrations.

Host adapters may authenticate/map membership, enroll credentials/files and
connect an existing secret store to the public resource contract. Those bridges
must not implement ETL preparation, source/destination access or row processing.
The operator still owns deployment supervision and infrastructure selection;
the backend supplies the configured runtime entry points and execution logic.

## Required ETL baseline and capability limits

The complete backend baseline includes a bounded declarative transformation
and validation profile (HC-14). A transfer-only release is an intermediate
milestone, not completion of the application specification goal.

The first profile must support select/drop/rename, explicit casts, filters,
declared scalar normalization/expressions and deterministic deduplication,
together with schema, required-value and range/set validation. Each operation
publishes its parameters, type/null/error behavior and resource requirements.
All execution is owned by the backend. The exact operator vocabulary is
qualified upstream in 0.5 and exercised end to end in 0.6.

Cross-batch deduplication must declare key and tie-breaking semantics and
obtain bounded memory or spill resources. Whole-input validation before
publication requires validated staging or atomic destination publication.
If the provider cannot satisfy a selected guarantee or budget, reject that
specification; do not weaken it or delegate the work to the application.

Joins, full sorting, aggregates/windows, incremental/CDC modes, quarantine and
additional engines need separately advertised upstream contracts and evidence.
When offered, apps control their logical specification while the backend owns
state and algorithms. An unavailable capability never creates an app-side
implementation obligation. SQL and PySpark remain optional engine profiles.

## Acceptance: an app with no ETL implementation

The minimal reference app demonstrates specification/form binding, trusted
identity and resource-store bridges, top-level hosting, backend commands and
result presentation without ETL runtime code. Real apps may add programmatic
authoring, approvals, external triggers and business workflow orchestration.
Backend providers are installed independently. Qualify
the following in addition to the existing correctness/security criteria:

- change source/field mapping, transformation parameters, validation rules,
  supported write policy and schedule specification without changing app code;
- use canonical schemas for authoring, export/import and diagnostics;
- submit directly without an app-created plan, computed fingerprint, preflight
  receipt or sequence of preparation calls;
- recover response loss, provider-action delay and host shutdown using the
  same command identity with no application recovery loop;
- show that the app has no extract/load loops, ETL SDK calls, runtime provider
  factories, row callbacks, rule evaluator, planner or lease/retry scheduler;
- reject an unsupported specification without calling a legacy app fallback;
- retain the same app-facing contract when qualified backend providers change
  within a profile's supported compatibility contract.

Pair this minimal-consumer proof with the developer-control parity and extension
proofs. Reducing the app's available specifications or run actions to make the
minimal example pass is not acceptable qualification.

Use import/source inspection together with behavioral evidence; absence of a
particular package name alone cannot prove absence of ETL logic. 0.5 proves the
command/specification boundary with controlled external providers, 0.6 runs the
required ETL baseline, and 0.7 qualifies a downstream deployment.

For Data Mover, the downstream cutover report must show that its active path
no longer uses its transfer engine, source/destination connector implementations,
submission preparation, or lease/recovery loops. Legacy historical reads and
explicitly drained work remain migration concerns, with no silent fallback.
This proof lives in the adopter's repository; ShuETL stays independent of it.
