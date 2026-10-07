# Host Capability Delivery Matrix

## Status and use

This is the delivery index for the host backend described in
[HOST_INTEGRATION.md](HOST_INTEGRATION.md). It distinguishes a planned contract
from a qualified implementation. ShuETL 0.4.0 currently supplies FastAPI
composition and local/PostgreSQL provider bundles against ETLantic 0.52.1.
Those bundles do not establish headless service authorization, live connector
execution, worker startup, or production host qualification.

Every row below is **planned and unqualified** as a complete host capability.
Existing upstream components may satisfy parts of a row; the 0.5 inventory must
record exact public exports and evidence before marking it available. A
missing qualification is not proof that an upstream API is missing.

The [ETLantic 0.56 dependency map](ETLANTIC_0_56_DEPENDENCIES.md) records the
historical 0.55 candidate gaps and the published 0.56 evidence. Phase 0.6 uses
exact ETLantic `0.56.0` artifacts as its selected baseline. Each capability
still needs ShuETL composition evidence before it becomes available.

The 0.5 contract pilot uses a specification-driven reference app and controlled
external providers. The 0.6 ETL preview adds real providers, bounded transforms
and validation, and supervised roles.
The 0.7 production candidate requires a named downstream workload and operating
limits. All are narrower claims than general support for every connector.

## Required host backend capabilities

| ID | Required behavior | Semantic owner / host responsibility | ShuETL delivery and proof |
|---|---|---|---|
| HC-01 | Authorized specification/command access without a listener, synthetic request or caller-built provider graph | Public ETLantic services; ShuETL supplies the standard backend profile; host supplies trusted context | 0.5: standard consumer, explicit composition/lifecycle, HTTP and headless parity |
| HC-02 | Per-operation principal and owner/workspace isolation | Host authenticates/maps membership; ETLantic authorizes | 0.5: interleaved owners, missing identity, cross-scope lookup/list/cursor tests |
| HC-03 | Pure validation, deterministic planning, revision concurrency and immutable accepted work | ETLantic models, planner, registry and revision rules | 0.5: no network/secret resolution, concurrent edit rejection, frozen revision proof |
| HC-04 | Durable acceptance, scoped idempotency, accepted-request lookup after timeout | ETLantic submission service/store; backend computes canonical fingerprints | 0.5: duplicate/conflict/response-loss proof; 0.6: independent processes and worker execution |
| HC-05 | Authorized connection tests, catalog/schema inspection and read-only preflight | Public ETLantic/provider action contracts; host owns connection enrollment and cache presentation | 0.5: action boundary with controlled providers; 0.6: isolated live action execution, bounded discovery, stale preflight and outage cases |
| HC-06 | Opaque credential/resource references and explicit rotation/revocation behavior | Host or independent resource provider stores secrets; upstream boundary authorizes resolution | 0.5: reference/context contract and redaction; 0.6: real worker/action resolution without gateway access |
| HC-07 | Packaged connectors, source/destination pairing, write modes, writer policy and overlap protection | Independent backend providers implement connectors; operator enables writers; app supplies references/locators/policies | 0.6: every advertised pairing/mode qualified without app connector code, including aliases, upsert keys, disabled writers and schema drift |
| HC-08 | Uploaded/staged input ownership, checksum, immutable resource version and cleanup | Host enrolls files; ETLantic resource/artifact provider owns execution access | 0.6 when file inputs are advertised: cross-owner, changed/missing/expired input, size and retry-retention proofs |
| HC-09 | Bounded transfer, cancellation, leases/fencing, retry and uncertain external effects | ETLantic worker/runtime and sink providers | 0.6: real transfer and failure injection; 0.7: measured capacity, outage and shutdown envelope |
| HC-10 | Status, attempts, ordered progress, diagnostics, metrics, reports and artifacts | ETLantic records and providers; host derives UI projections | 0.5: canonical reads and unavailable-provider behavior; 0.6: real metrics/manifests and lost terminal-publication proof |
| HC-11 | Schedules through the same submission path, timezone/DST, overlap, misfire, revision and occurrence policies | ETLantic scheduler/firing store; host owns schedule UI | 0.5: service/context contract; 0.6: scheduler restart, duplicate firing and revision-selection proof |
| HC-12 | Independent package installation, supported train, diagnosis and migration | ShuETL composition; providers own schema upgrades; host owns product migration | 0.5: clean wheel and compatibility evidence; 0.6: generic consumer conformance; 0.7: downstream cutover/rollback report |
| HC-14 | Required bounded transformation and data-quality baseline | ETLantic/provider graph, types and algorithms; app selects canonical transforms, rules and policies | 0.5: schema/operator contract qualification; 0.6: select/drop/rename, casts, filters, scalar expressions, deterministic deduplication and schema/required/range/set rules with resource/publication evidence |
| HC-17 | Complete canonical specification contract and capability/schema discovery | ETLantic defines schemas and computed outputs; app authors every supported business option | 0.5: typed parameters, schema/constraint discovery, export/import, revision and specification-change proofs |
| HC-18 | One backend-owned submission/preparation command for manual and scheduled work | ETLantic coordinates normalization, fingerprinting, revision binding, planning, preflight and admission; ShuETL exposes it | 0.5: no required host ETL preparation orchestration, delayed preparation/response-loss proof; 0.6: live provider action and worker proof |
| HC-19 | Application consumption with no ETL implementation | ShuETL qualifies the standard path; backend packages supply runtime code; host owns UI/identity/resource bridges | 0.5: minimal reference app; 0.6: same app executes ETL using specification changes only; 0.7: downstream active runtime retirement evidence |
| HC-20 | Complete public control exposure and per-run effective configuration | ETLantic/provider schemas define settings and overrides; apps choose every supported option; ShuETL preserves them | 0.5: option/command parity, provider-specific fields, override precedence and effective-specification proof; 0.6: live behavior follows requested settings |
| HC-21 | Discoverable run actions with full command and lineage semantics | ETLantic owns transitions/effects; apps request lifecycle actions and inspect reasons/preconditions | 0.5: action inventory, state/identity contracts and unavailable-action diagnostics; 0.6: live cancel, safe failed-work retry and deliberate new run; 0.8: additional lifecycle profiles |
| HC-22 | Programmatic authoring, approvals and external business workflows | App owns product coordination; backend owns pipeline dependencies, native firings and execution | 0.5: generated specifications, approval flow and duplicate external-trigger fixture; 0.6: live command identity and workflow separation proof |
| HC-23 | Developer-authored backend extensions without ShuETL core changes | Developers implement public ETLantic extensions; backend loads/executes them; deploying team qualifies the profile | 0.5: private extension packaging, typed configuration and schema round trips; 0.6: live example transform/connector outside the app; 0.8: additional graph/code/engine profiles |

HC-01–HC-07, HC-09–HC-12, HC-14 and HC-17–HC-23 form the target ETL backend
baseline. HC-08 is mandatory for a profile advertising file inputs. A
transfer-only profile may be an intermediate release, but it does not complete
the ETL backend goal. Live-provider support remains unqualified in 0.5.
Schedule execution requires HC-09 and HC-11; a manual-only profile states that
scheduling is unavailable. The specification and standard-consumer boundary
is defined in [SPECIFICATION_CONTRACT.md](SPECIFICATION_CONTRACT.md).

[DEVELOPER_CONTROL.md](DEVELOPER_CONTROL.md) prevents the baseline from becoming
a feature ceiling. HC-20–HC-23 require a complete public integration path for
each qualified profile; they do not claim every provider supports every graph
form or run transition. Record exact constraints and extension/delivery gaps.
An already-qualified public feature is exposed without waiting for a later
milestone merely because the default profile does not use it.

## Additional capabilities with separate gates

| ID | Capability | Required contract and delivery gate |
|---|---|---|
| HC-13 | Provision destination objects | Public provider create operation, operator policy, owner authorization, idempotency/uncertain-create evidence. Qualify per provider in 0.6 or later; never treat it as read-only preflight. |
| HC-15 | Bounded plan preview | Authorized isolated execution with sample/time/byte limits, no destination mutation, safe output handling and cleanup on timeout/cancellation. Prove source-read authorization and denied access to production sinks. Depends on HC-05/06/09 and the selected HC-14 engine; qualify in 0.6 or later. |
| HC-16 | SQL or PySpark execution | Separate engine/dialect/parameter/dependency contracts, worker image, sandbox, spool/checkpoint and retry qualification. Expansion target is 0.8; earlier opt-in qualification is allowed, with no automatic inclusion in the baseline. |

Optional capabilities become mandatory gates for any profile that advertises
them. The Data Mover migration must compare its enabled current features with
the selected profile. An unsupported existing feature must be migrated later
under an explicit host cutover plan; it cannot silently disappear or use a
hidden legacy execution fallback.

## Reference workload provenance

The reference host requirements were reviewed against Data Mover revision
`834481f61a811e192ed914d9beaddd9d77e2df76`:

- [Pipeline lifecycle](https://github.com/eddiethedean/user-token-management-app/blob/834481f61a811e192ed914d9beaddd9d77e2df76/docs/data-pipelines.md)
  informs transfer, provider, scheduling, processing and preview requirements.
- [ETL integration note](https://github.com/eddiethedean/user-token-management-app/blob/834481f61a811e192ed914d9beaddd9d77e2df76/docs/plans/etl-integration-note.md)
  informs the host validation/planning/execution boundary.
- [Secret-reference contract](https://github.com/eddiethedean/user-token-management-app/blob/834481f61a811e192ed914d9beaddd9d77e2df76/docs/plans/secret-reference-contract.md)
  informs owner, provider, purpose and version binding.

These documents supply requirements, not package dependencies or proof that a
ShuETL capability is implemented. An adopter's later changes must be mapped to
the generic contract in its own integration plan.

## Upstream contract and evidence record

For every claimed HC capability, the release inventory records:

- exact package/version and public import/export, protocol and schema version;
- semantic owner and ShuETL composition entry point;
- required providers, supported operations and limitations;
- full caller-facing specification/command/query coverage, including
  provider-specific controls, per-run overrides and optional expert access;
- defaults, operator constraints, allowed-action preconditions and precise
  unavailability reasons, with an issue for any ShuETL exposure gap;
- construction, per-operation authorization and cleanup ownership;
- its phase acceptance criteria, executable proof and built wheel identity;
- qualification status: unassessed, upstream work needed, qualified, or
  intentionally unavailable for this profile;
- an upstream issue/release reference when a missing contract is confirmed.

Do not substitute a private module, a host model, a copied connector registry,
or HTTP route-handler invocation for a missing public service contract.
Requalify changed contracts on an upstream upgrade; a new version number alone
does not clear a blocker. A skipped test is not qualification evidence.

## Capability, readiness and user connection health

Keep three distinct facts visible through upstream contracts and ShuETL's
existing diagnostics:

1. **Capability:** the installed and enabled provider can perform the operation.
2. **Role readiness:** required stores, schema, authorization and execution
   dependencies are usable for the selected deployment profile.
3. **Connection/preflight result:** a particular owner's reference and selected
   resources passed a bounded action at a recorded time and version.

A successful connection test does not enable a disabled writer or reserve a
remote object. A failed owner's connection does not make every other owner's
gateway unready. Missing optional capabilities are reported as unavailable;
missing required profile capabilities prevent readiness. Diagnostics must not
enumerate owners or decrypt/test every user's credentials during startup.

## Qualification ownership

ShuETL maintains generic conformance fixtures and installed-artifact checks.
Provider maintainers qualify their advertised modes and failure behavior.
Data Mover owns product migration, selection of independent backend packages,
user flows and its integration suite against a released ShuETL artifact in its
own repository. ETL connector implementations and execution stay in the backend.
ShuETL CI must pass without checking out or installing any adopting application.

The 0.7 adopter report records exact dependency pins, supported capability IDs,
workload and topology, cutover of active work, historical-read policy, rollout
and rollback evidence, limits, and proof that no application ETL implementation
remains in the active path. The reference app must change supported behavior
through specifications alone. The adopter also proves that ShuETL preserves
its required controls and custom extensions without an app-side ETL fallback.
It qualifies that profile only. Private, developer-qualified profiles may use
public extension contracts without inclusion in ShuETL's production support
matrix or publication of their source.

See [PHASE_0_5_EXECUTION.md](PHASE_0_5_EXECUTION.md) for the next implementation
sequence and [ROADMAP.md](ROADMAP.md) for later production gates.
