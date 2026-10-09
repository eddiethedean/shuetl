# Host Application Integration Contract

## Purpose

This is a target contract. The [delivery matrix](CAPABILITY_DELIVERY.md) assigns
capabilities to releases and distinguishes required from conditional features.
Released 0.5 is the guarded identity/gateway baseline. The next implementation is
[Phase 0.6](PHASE_0_6_EXECUTION.md), gated on upstream contracts and live deployment
qualification under [ADR-0015](../adr/0015-backend-and-deployment-ownership.md).

The [specification contract](SPECIFICATION_CONTRACT.md) governs the app-facing
boundary: an app controls every supported ETL specification, while the backend
owns all preparation and execution. Provider independence alone is insufficient;
the standard consuming app must contain no ETL implementation.

The [developer-control contract](DEVELOPER_CONTROL.md) preserves every qualified
caller-facing option and command. Apps may generate specifications, choose
per-run overrides, manage run lifecycles and build business workflows. The
minimal consumer proves that backend execution needs no app ETL engine; it does
not restrict product code or developer-authored backend extensions.

ShuETL is an independently installable, host-agnostic integration package for
ETLantic. A host application may depend on ShuETL to configure and use ETLantic
as its ETL backend. Data Mover is a reference downstream adopter, not a ShuETL
component or dependency.

ShuETL's public contract must be useful to a host that embeds ETL operations in
its own user experience, including a server-rendered application that does not
publish ETLantic's routes as a public API. FastAPI route mounting remains
available, but it is not the only supported consumption mode.

## Dependency direction and ownership

```text
Host application (for example, Data Mover)
  owns business specifications, product UI, accounts, authorization policy,
  credential enrollment, host data, and host-specific migrations
             │ depends on a supported ShuETL release
             ▼
ShuETL
  owns qualified deployment profiles/commands, host integration, upstream
  factory selection, supervision, compatibility and process readiness
             │ depends on public ETLantic contracts and provider packages
             ▼
ETLantic and its providers
  own definitions, plans, execution, durable state, identities, events,
  reports, schedules, artifact semantics, and provider migrations
```

The dependency is one-way. ShuETL must not import, install, query, test against,
or encode the schemas, route names, connectors, settings, UI, or product rules
of Data Mover or another host. ShuETL must not ship a host-specific extra such
as `shuetl[datamover]`. Host applications pin and install ShuETL; ShuETL pins
and validates ETLantic packages. Named adopters appear in planning and
qualification records only.

The host owns authentication, account-to-scope mapping, credential enrollment,
and any host database records. ETLantic remains authoritative for ETL
definitions, revisions, submissions, attempts, schedules, events, reports,
artifacts, and execution outcomes. ShuETL composes the boundary and preserves
those upstream identities. It does not create a parallel backend database or
translate ETLantic records into a second canonical model.

Source, destination and transformation implementations ship in ETLantic provider
distributions or independent backend extension packages implementing public
upstream contracts. Standard profiles supply these implementations. Deployment
configuration selects the packages; apps specify connector kinds, references,
locators and behavior without implementing readers/writers or row callbacks.
Missing semantic contracts are resolved upstream before support is claimed.

The dependency restriction concerns package requirements, hard-coded imports
and knowledge of a host's internals. Explicit provider injection remains an
advanced platform integration surface. It cannot be required by the standard
application path or used to satisfy its no-ETL-implementation gate. New connector
primitives belong in backend packages installable without the consuming app.
Developers may maintain private extensions in the app's repository and qualify
them through public contracts without changing ShuETL core.

## Consumption modes

### FastAPI composition

The host mounts the authoritative `etlantic-fastapi` router or creates a
dedicated API application. ShuETL preserves upstream routes, schemas, status
codes, authorization ordering, idempotency, events, and readiness behavior.

### Headless in-process composition

ShuETL must support a host application that needs ETLantic capabilities from
Python without opening a listening socket or making loopback HTTP requests to
itself. Its standard interface accepts canonical specifications and backend
commands and returns canonical results. ShuETL configures an upstream-complete backend factory from deployment settings;
neither the app nor ShuETL reconstructs its semantic service graph. FastAPI
mounting is optional in this mode.

The headless surface is a composition handle over public upstream services, not
a new ShuETL domain API. It must not add alternate `Pipeline`, `Run`,
`Schedule`, result, or event models or rename upstream semantics for a host. If
ETLantic does not expose a stable public service contract for an operation,
ShuETL must not reach into private modules to provide it; the contract is added
upstream first. Ergonomic delegation to canonical services is permitted; the
restriction forbids duplicate semantics, not a concise application interface.

Headless composition also needs a request-independent lifecycle and an explicit
context on every invocation. It must not fabricate a FastAPI request or mutate
a shared current-user value. Caller-supplied providers remain caller-owned;
resources created by the standard backend factory need explicit ownership and
cleanup on partial startup. Existing 0.4 bundle ownership and mounted lifespan
behavior remain compatible. Headless use does not require removing FastAPI
from the package dependencies.

## Host workflow contract

The backend owns this workflow through public ETLantic services. The app may
request validation, explanation and preview while authoring, then issue a
single logical submission command. It is not responsible for sequencing
preparation services or persisting their state:

1. **Validate a draft.** Return normalized upstream diagnostics and field
   locations without resolving credentials or making provider network calls.
2. **Plan deterministically.** Produce the canonical plan, expected schemas,
   compatibility facts, and resource requirements without plaintext secrets.
   Bind each submission to an immutable definition/plan revision so later
   edits cannot change queued or running work.
3. **Preflight before submission.** Where the selected specification, provider
   or backend profile requires live readiness checks,
   dispatch a separate bounded, read-only, owner-authorized provider action
   outside the gateway. Bind the result to the selected revision, references
   and relevant policy. Report safe field-targeted remediation and create no
   pipeline submission on failure. Action/audit evidence may be retained.
4. **Submit durably.** The backend creates the canonical upstream submission
   with trusted caller scope, a backend-computed request fingerprint and the
   caller's logical idempotency token. A convenience method named `run`, if
   offered, means durable submission; it never executes data in the web request
   or treats acceptance as successful completion.
5. **Execute under the worker role.** ETLantic owns claim, lease, fencing,
   cancellation, retry, recovery, and effect semantics. Workers receive only
   the authorized runtime resources required by the immutable plan.
6. **Project canonical outcomes.** Hosts read status, attempts, ordered events,
   reports, and authorized artifact metadata by their ETLantic identities.
   Host-specific UI summaries may be derived, but cannot become another source
   of execution truth.

This preserves the useful distinction between pure authoring validation and a
live submission preflight. A host may keep a read-only UI projection keyed by
ETLantic identities; it must not dual-write run state or maintain a second
retry, lease, event-sequence, or reconciliation state machine.

For retries, authorize the caller and look up the scoped idempotency key before
repeating live preflight. Return an identical accepted request's record even
if the provider is now unavailable; reject a changed fingerprint. Recover a
lost response using the same key. Preflight cannot reserve remote state: the
worker rechecks authorization, resource revocation, writer policy and required
provider assumptions before effects. Concurrent edits use upstream revision
preconditions and cannot silently change the selected plan.

The standard submission service executes these checks even when the app did
not validate or plan separately. Long preparation may expose a canonical
operation identity for polling; the app never advances it by calling the next
ETL stage. Manual and scheduled requests use the same backend service. There
is no required application-side fingerprinting, physical-plan construction or
preparation recovery loop. Optional staged authoring/approval may use upstream
plan or preparation references; the backend validates them and owns admission.

## Identity and secret references

- The host authenticates users and derives principal, workspace, and resource
  scope from trusted server-side membership. Caller-supplied scope is never
  authoritative by itself.
- ShuETL adapts the trusted host principal to ETLantic's public context and
  supplies the configured authorizer. ETLantic decides access to ETL resources.
- A host may keep its existing encrypted credential store. Definitions and
  plans carry opaque, versioned references; they never carry credential values.
- For pipeline execution, a worker resolves a reference after claiming the
  authorized run. Catalog/test/preflight use a separately authorized isolated
  provider-action executor before any pipeline submission. Both boundaries
  verify owner/scope, provider, purpose and version; neither returns credentials
  to the gateway.
- Gateway requests, plans, reports, diagnostics, events, and logs never receive
  resolved credential values. A global fallback credential cannot replace a
  missing owner-authorized reference.
- Catalog browsing, connection tests, and preflight are separate bounded
  actions with host authorization and redacted outcomes.

The provider contract declares exact-version binding or explicitly authorized
late binding at execution. A mutable `current` reference is not a reproducible
credential version. Record safe resolved-version metadata for audit, recheck
revocation at use, and fail closed on removal or incompatible rotation. This
does not freeze the remote source's contents; source snapshot guarantees must
be advertised separately by its provider.

## Connector and data-plane capabilities

The configured ETLantic runtime must report capabilities for each enabled
source, transform, validation step, and destination. Qualification covers the
selected provider packages and includes:

- source/destination capability pairing, with a distinct operator policy for
  enabling each destination writer; recheck eligibility at authoring,
  submission, and worker boundaries so stale UI or configuration cannot enable
  a forbidden write;
- canonical locator identity and overlap checks where the provider can expose
  them, rejecting a route that writes into its own selected source object or
  overlapping source set; include aliases and multi-file selections, and report
  a protected route unavailable when overlap cannot be established safely;
- owner-authorized connection tests, paginated catalog discovery, locator
  validation, schema description, and best-effort row-count/size previews;
  metadata caches must be credential-free, owner/provider scoped, bounded, and
  invalidated when the selected credential version changes;
- write-mode validation must cover schema compatibility, destination permissions,
  required key/constraint selection, and any provider-specific object binding;
  preflight rechecks those conditions read-only before submission;
- where the upstream engine supports preview, run a separate bounded sample
  against the draft or frozen plan through an isolated execution role; return
  schema propagation and safe diagnostics without destination writes. Preserve
  execution/audit identity and enforce row, byte, time and redaction limits;
  do not persist sampled cell values in logs, events or control-plane records;
- optional destination-object provisioning only through an advertised,
  operator-enabled provider capability with explicit create authorization;
  uncertain create outcomes are reported for reconciliation and are not
  blindly retried;
- host-managed upload or staged-file sources through opaque resource
  references, with owner/checksum/size validation before acceptance and at
  worker access; retain the pinned object through active attempts and allowed
  retries, reject changed/expired inputs, and assign cleanup to its provider;
- bounded streaming/backpressure, batch and memory limits, timeouts, spool or
  checkpoint requirements, and worker concurrency;
- provider-specific write modes, transaction boundaries, schema checks, and
  destination verification, plus truthful source/read, destination/acknowledged,
  rejected, and provider-confirmed verification metrics where available;
- cancellation boundaries and the distinction between safe retry and uncertain
  external effects;
- TLS trust, redirect policy, hostname/egress allowlists, and credential scope;
- ordered stage/progress events, manifest/artifact identity, and structured
  diagnostics that identify stage, field, provider, and safe remediation
  without exposing row values or credentials.

An unsupported capability is reported as unavailable before submission. ShuETL
does not claim a generic connector can provide a transaction or exactly-once
external effects that the provider cannot prove. Ambiguous external commits
remain an upstream reconciliation outcome and are never converted to success
or blindly retried.

SQL, PySpark, arbitrary expressions, user code, and other optional execution
engines require separate upstream contracts, sandboxing, resource limits, and
capability gates. Their presence in a host's product roadmap does not imply
support from ShuETL.

## Processing and validation requirements

Hosts express a transfer route or logical processing graph through an upstream
versioned specification of source, input rules, ordered transforms, output
rules and destination nodes.
ShuETL exposes public capability metadata and composes the supported engine.
The engine/provider owns graph typing, schema propagation, deterministic
fingerprints, node/rule versions and resource estimates.

The complete ETL baseline requires HC-14. Its first profile supplies select/drop/
rename, explicit casts, normalization, filters, approved expressions and
deterministic deduplication, with schema, required-value and range/set rules.
Rule contracts declare their evaluation point, severity and thresholds.
Additional uniqueness and whole-dataset aggregate rules require separately
advertised upstream support. Unsupported casts or schema drift produce canonical
diagnostics with node/rule/column identifiers and counts, without sensitive cell
values.

Dataset-wide sort, join, deduplication and aggregate rules may need complete
input or spill storage. A plan must declare and obtain those resources or fail
before admission. A promise to reject all invalid input before publishing any
destination data requires whole-input validation or a qualified staged/atomic
destination. A later invalid batch cannot undo already committed batches by
assertion; partial effects retain reconciliation semantics. Warning, quarantine
and rejected-row destinations each require explicit upstream contracts and
authorization before being advertised.

Preview is a separate authorized execution with an immutable plan identity,
bounded inputs and no destination mutation. It uses the worker/action boundary,
never the gateway request lifetime. Sample output needs data-read authorization
and classification/redaction policy; metadata-only output is the default.
Sample success does not prove full-input rule success or future source stability.
SQL/PySpark support remains separately gated in the delivery matrix.

## Scheduling requirements

Scheduled work uses the configured ETLantic workload identity and explicitly
authorized secret references. It never inherits the credentials of the person
who created the schedule. The schedule contract must make timezone and DST
behavior, next-occurrence preview, overlap, missed-run/catch-up policy, and
definition selection (latest approved revision or pinned revision) visible to
the host. Each occurrence has a durable idempotency identity. Pausing or
deleting a schedule prevents future occurrences without changing submissions
already accepted.

The upstream firing identity includes the authorized scope and nominal
occurrence. Resolve a latest-approved revision once for that firing, then keep
it immutable across retries. History must distinguish missed/skipped firings,
accepted submissions and terminal execution outcomes. Schedules use the same
admission, preflight policy and idempotent submission path as manual runs.

External event sources, workflow tools and application schedulers may submit
through that same public command path. Their event identity and scheduling
authority remain explicit; they do not fabricate native ETLantic firings.
Applications may manage business dependencies and request supported run actions
without implementing backend attempts, leases or effect reconciliation.

## Migration and adoption

ShuETL migrates only ETLantic provider schemas through provider-owned APIs. A
host owns migration of its existing definitions, credential references,
account/scope mapping, and UI projections to canonical ETLantic identities. A
host migration plan records mapping, cutover, coexistence, rollback, and
historical-read requirements; ShuETL never reads a host application's tables.

Cutover must drain or explicitly account for queued/in-flight legacy work and
prevent both runtimes executing the same logical transfer. Mapping/backfill is
restartable and idempotent in the host's migration process. Retained legacy
history stays labeled as legacy evidence. Rollback stops new admission and
accounts for accepted ShuETL work; it cannot undo external destination effects
or safely replay them by reverting an application database alone.

The completed downstream cutover must retire application transfer engines,
connector implementations, submission preparation and lease/recovery loops from
the active path. Installing independent backend provider packages is permitted;
moving unchanged application ETL behind an adapter is not proof of backend
ownership. Historical reads and explicitly drained legacy work remain separate
migration concerns without a silent runtime fallback.

Existing connector or transform implementation code may be reused in qualified
backend extensions. The cutover proof concerns invocation, lifecycle and state
ownership; it does not require a rewrite, separate repository or public release
of a proprietary extension.

ShuETL publishes a consumer conformance suite and a supported compatibility
matrix. Its own CI uses generic host fixtures and does not checkout or import
Data Mover. Each adopting host installs a released ShuETL artifact and runs its
own end-to-end integration suite against that version. Data Mover is the first
named reference adopter for this one-way contract.

## Host conformance gate

The 0.5 subset is enumerated as H05-001–032 in the execution plan. The following
is the complete production gate; generic fixtures alone cannot satisfy it.

Before a production support claim for embedded use, qualification must prove:

- every qualified caller-facing option/command/query remains accessible,
  including per-run overrides, state-dependent actions and extension settings;
- business workflow/external-trigger fixtures and private backend extensions
  work without ShuETL core changes or app ETL runtime logic;

- a clean host environment installs the released ShuETL wheel and only the
  declared ETLantic/provider train;
- the standard app consumes canonical specifications and commands without
  runtime provider factories, connector code, row callbacks or ETL orchestration;
- changing supported source/mapping/transform/rule/write/schedule specifications
  changes behavior without changing the reference app's code;
- the required bounded transformation/validation baseline runs through
  qualified backend packages and is not delegated to the application;
- a host can validate, plan, perform read-only preflight, durably submit, and
  inspect outcomes without exposing a public ETLantic API or using HTTP loopback;
- a host identity maps to the intended principal/workspace and cannot read or
  submit for another owner's definitions, runs, events, artifacts, or secrets;
- repeated submissions preserve canonical idempotency and revision identities;
- source/destination compatibility, same-object protection, and writer policy
  cannot be bypassed by changing a locator or stale provider configuration;
- catalog, connection-test, schema/sample-preview, upload-reference, and
  optional destination-provisioning paths preserve owner scope and safe error
  semantics;
- worker credentials remain scoped and redacted through success and failure;
- ordered stage events, progress, reports, cancellation, restart recovery, and
  uncertain external effects remain truthful;
- scheduled occurrence deduplication, timezone/DST behavior, overlap and
  misfire decisions, and the selected definition revision survive restarts;
- the deployment separates gateway work from execution where required and
  enforces the selected resource, network, and shutdown bounds;
- the host can migrate and roll back its own records without ShuETL creating a
  second source of truth;
- ShuETL remains importable and qualified without the adopter package installed.

The exact provider and workload envelope is published as a Supported,
Experimental, or adopter-owned profile. Qualification of one host does not
make every connector, transform engine, or deployment topology supported.
