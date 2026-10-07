# Developer Control of Pipelines and Runs

## Product guarantee

ShuETL must preserve the full caller-facing control of the configured ETLantic
backend. A concise default interface must not impose a smaller pipeline
language, fixed workflow, connector list or run lifecycle on applications.
The bounded baseline is the minimum qualified experience, not a product ceiling.

Applications decide what work to perform, when to request it and which supported
policies to apply. The backend implements ETL algorithms, preparation, execution
and durable state transitions. Developers may also author backend extensions;
the backend loads and executes them through public ETLantic contracts.

This complements [SPECIFICATION_CONTRACT.md](SPECIFICATION_CONTRACT.md) and
[ADR-0013](../adr/0013-specifications-and-backend-ownership.md). It is a planned
contract; concrete schemas, commands and state transitions require upstream
qualification before they are advertised.

## Preserve available backend controls

For each qualified backend profile, inventory every public caller-facing
specification field, command, query and extension setting. ShuETL must expose
them through canonical typed contracts or a documented public service access
path. Python consumers must not be limited to operations with an HTTP route.
Where both transports exist, preserve their semantic parity and document any
upstream transport gap.

Convenience methods and UI presets may cover common cases. Apps can still use
the complete canonical schema and public services without private imports,
forking ShuETL or implementing another ETL engine. Provider-specific options
remain typed, versioned and discoverable; a common adapter must not drop them.
Unknown or incompatible options produce diagnostics instead of being ignored.

For an unavailable control, distinguish an upstream contract gap, missing
provider, incompatible version, deployment policy, caller authorization and a
temporary run-state precondition. A ShuETL exposure gap for an otherwise
qualified public control is an integration defect. Qualification gaps require
an explicit evidence/work item; they cannot become undocumented exclusions.

Defaults are overridable where the canonical contract permits. Operator
constraints must be explicit and discoverable to an authorized caller. Apps
can choose broader qualified profiles or install compatible extensions without
changing ShuETL core. Profile qualification states support level; it does not
restrict applications to a centrally curated catalog of providers.

## Application control inventory

The following families must be inventoried in 0.5. This lists required control
coverage, not a claim that every engine implements every feature. Implemented
families expose their complete public options; unavailable families have a
declared contract/delivery gap and an extension path.

| Control family | Application/developer choices | Backend responsibility |
|---|---|---|
| Authoring | Forms, files, API clients, generated definitions, templates, reusable subgraphs and programmatic builders | Normalize to canonical versioned specifications with diagnostics; no prescribed editor or file format beyond upstream contracts |
| Definition lifecycle | Create, revise, clone, compare, approve/promote, archive and delete through supported operations | Apply authorization/revision rules and retain references/history required by accepted work |
| Data and topology | Multiple sources/sinks, mappings, dependencies, joins, branches, conditional processing, fan-out/fan-in and supported iteration | Type-check and execute the selected logical graph; declare supported graph forms and reject unsupported semantics |
| Processing | Built-in or custom transforms/rules, expressions, SQL, UDF/code artifact references and engine-specific settings | Resolve approved versioned implementations and execute them in the qualified runtime |
| Data selection | Partitions, date windows, snapshots, incremental/CDC policy and authorized starting checkpoint references | Validate source consistency, offsets and effect semantics; manage checkpoints and state |
| Output and quality | Write modes, keys, schema evolution, transactional/publication guarantees, rule thresholds, warnings, fail/quarantine behavior and output artifacts | Enforce selected policies and expose truthful partial/uncertain effects |
| Run request | Definition/revision, typed parameters, permitted overrides, resource references, labels and business correlation | Resolve and record an immutable effective run specification and canonical identities |
| Execution preferences | Engine/provider version pins, approved execution pool, priority, concurrency, batch/partition hints, budgets and timeouts | Validate capabilities/policy, compute the physical plan and report effective settings and hint decisions |
| Timing and workflow | Native schedules, external events/orchestrators, manual runs, approval flows and dependencies between business activities | Own native firings, pipeline dependencies, admission and each accepted run |
| Lifecycle | Cancel, retry, rerun, replay, repair, backfill, and pause/resume or queued/live amendments where supported | Authorize commands, enforce state/effect preconditions, preserve lineage and audit decisions |
| Inspection and integration | Plan explanation, previews, complete authorized records, query/filter options, events, metrics, lineage and artifact access | Supply canonical observations, supported delivery contracts and bounded authorized data access |

An app may choose a physical strategy when an upstream engine exposes it as a
public setting or hint. Backend ownership of a computed plan does not remove
that choice. It means the backend validates, resolves and executes the choice.
It must report whether a hint was applied, constrained or unsupported.

## Definitions, run overrides and effective configuration

Do not require apps to edit a reusable definition for every run. Support typed
submission parameters and every upstream-declared overridable field. Qualify
precedence and validation across profile defaults, definition defaults and
explicit run choices; operator constraints are enforced as constraints, not
silent replacement values. Reject a field that is immutable for that operation
with a diagnostic and a supported alternative where one exists.

Record the effective specification, selected revisions, applied overrides,
resolved engine/resource bindings and decision provenance. Keep secret values
out of those records. Apps can inspect and compare runs or request another run
using a recorded specification. Reproducing remote input requires a qualified
snapshot/version capability and must not be inferred from equal parameters.

Plan/explain, preview and read-only preflight may be explicit app actions.
Apps may implement approval workflows and, where the upstream contract allows,
submit a reference to an approved immutable plan or preparation result. The
backend revalidates authorization, identity, freshness and required live facts;
an optional staged UX never replaces the backend's admission responsibilities.
Direct submission remains complete without that UX.

## Run command semantics

Provide discoverable allowed actions for the current caller, run state and
provider. Document command inputs, revision/state preconditions, idempotency,
whether completion is asynchronous and resulting identities. Recheck those
preconditions on invocation; an action displayed earlier grants no authority.

- Retrying a lost submission response keeps its logical idempotency token.
- An explicit failed-work retry follows upstream attempt/recovery semantics.
- A deliberate new run uses a fresh submission identity and records its lineage,
  selected input scope and revisions. Replay and repair preserve their upstream
  command/attempt/execution identities instead of being collapsed into request
  retry. Selective stage/partition replay requires validated dependencies and
  provider effect guarantees.
- Backfill names a bounded interval/partition selection and policy for already
  completed work. The backend expands, deduplicates and records the resulting
  work; apps do not need to synthesize canonical scheduler firings.
- Cancellation, safe pause/resume, repair and configuration amendments use
  backend commands. Expose unavailable transitions and reasons. Never simulate
  pause by reporting a cancelled run as resumable.

The 0.6 baseline must qualify submission, inspection, cancellation, explicit
safe failed-work retry and a deliberate new run from a chosen specification.
Backfill, selective replay, checkpoint resume and live amendments are expansion
targets in 0.8 with separate upstream/provider evidence; any already-qualified
public controls are exposed earlier without a ShuETL-only embargo.

Accepted work keeps its original specification and history. A supported queued
or live change creates an authorized, versioned control record with a defined
effective boundary. Apps never directly rewrite a run row, checkpoint or
claimed effect. An intentional rerun with possible repeated writes must expose
that meaning and any upstream confirmation policy.

## Business workflows and external orchestration

Applications may generate specifications dynamically, collect approvals, issue
commands from external schedulers/events, coordinate several backend runs and
react to outcomes with product actions or notifications. They may persist their
own business workflow state and correlations to canonical ETL identities.
The minimal reference app is a proof of a convenient entry point, not a limit
on the amount or shape of product code an app may contain.

ETLantic owns dependencies inside an ETL pipeline and all accepted execution
state. External orchestration calls the same authorized submission/run services
and may decide when to request a retry or new run. It does not claim backend
leases or implement attempt recovery and effect reconciliation.
Duplicate external deliveries use scoped command identities. A trigger has one
declared scheduling authority: native ETLantic schedules own their firings;
external triggers use their external event identity and do not impersonate
native firing records. Callback/webhook delivery uses qualified upstream or
host integration contracts with explicit retry and deduplication ownership.

## Developer-authored backend extensions

Developers may supply proprietary connectors, transforms, validators, engines,
policies and execution hooks using public ETLantic extension contracts. Existing
extension points do not require a change to ShuETL or a contribution to ETLantic
core. A missing semantic extension contract is upstream work.

Extensions may live in the same repository as the application and remain
private. A backend-loadable package/artifact must have independent installation,
versioning and declared dependencies so workers need no web app or its request
context. No separate public repository, package index publication or mandatory
review by ShuETL maintainers is required. The deploying team qualifies its
profile and is responsible for the extension's implementation.
Ownership audits examine package dependencies and active execution paths;
co-location of backend extension source with app source is not a failure.

For code/SQL/UDF engines, use the engine's typed parameters and immutable code
artifact/revision contract. The qualified backend performs compilation/loading,
resource enforcement, execution and recovery. A restriction on host-process
row callbacks is not a prohibition on custom processing. Registered backend
hooks and data-processing functions are available when their contracts are
qualified. Arbitrary imports from request strings remain outside the contract.

Optional expert provider injection and direct public service access retain
canonical authorization and lifecycle semantics. They are supported choices
for integrators; ordinary applications must not be forced to use them to obtain
advertised controls.

## Qualification evidence

- Compare ShuETL exposure against every caller-facing option/operation of the
  qualified profile, including a provider-specific setting absent from presets.
- Use the same definition for runs with different parameters, write policy,
  engine/resource preferences and budgets; verify recorded effective values
  and unchanged definition history.
- Exercise valid, denied, stale and unavailable run commands, including retry
  versus deliberate rerun identities and explanation of unavailable pause.
- Author a canonical spec programmatically and run an approval/external-trigger
  workflow with duplicate delivery and no application ETL executor.
- Install a private example transform/connector extension without changing
  ShuETL core or installing the host application in the worker; round-trip its
  typed configuration and qualify its execution separately.
- Preserve complete authorized records and artifact access through canonical
  service calls when convenience presentation omits detail.

The 0.5 pilot proves the contract with controlled providers; 0.6 adds live run
and extension evidence, 0.7 checks downstream control parity, and 0.8 qualifies
additional graph/engine/lifecycle profiles. Missing upstream support is visible
release work, not a permanent restriction imposed on application developers.
