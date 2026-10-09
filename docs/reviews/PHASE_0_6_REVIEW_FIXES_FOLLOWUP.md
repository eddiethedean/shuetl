# Phase 0.6 implementation review follow-up

Recorded: 2026-10-09. This follow-up corrects the remaining source and evidence
findings from the full Phase 0.6 review. It does not close any release gate;
hosted qualification and final-artifact evidence must still be regenerated.

| Finding | Correction |
| --- | --- |
| Worker dispatch can die on `SystemExit` while health probes stay green | Catch `BaseException` at the worker-thread boundary, fail readiness, request upstream drain, wake the supervisor, and return a failed process exit. |
| SIGTERM can arrive during startup and a tick can still be admitted | Mark the role draining and call ETLantic `request_drain()` in the signal callback; suppress subsequent local ticks and retain ETLantic admission as the race-safe authority. |
| Gate 0 can claim a pass with another PostgreSQL or ETLantic train | Require PostgreSQL 18.6, the expected schema head, exact 0.57.0 ETLantic package versions, isolated installed origins/import flags, and four distinct role PIDs. |
| CLI evidence can describe a different build than the release artifact | Record source commit and ShuETL/reference-host wheel SHA-256 in Gate 0 and CLI evidence; require both records to agree and match the final wheel. Release build and downloaded publish artifact both pass artifact/evidence checks. |
| ETLantic governance and artifact controls are dropped at backend construction | Carry policy, approvals, quotas, audit, attestations, required-attestation flag, schedule parameter resolver, and artifact root through shared host bindings into `SQLModelBackendConfig`. |
| Async/generator authorizers pass the factory validator | Share the transport-neutral synchronous/protocol/signature validator between the factory and the HTTP identity layer, keeping runtime validation independent of FastAPI imports. |
| Human principals can be bound to worker roles | Require a canonical service or workload principal plus matching typed tenant/workspace and valid environment/security-domain references. |
| Boundary checks miss direct upstream graph construction and provider SQL | Extend the standard-path AST rules to reject semantic service graph imports/construction and SQL/schema statements in role-composition modules. |

The changes above are implementation corrections. No release evidence was
regenerated in this change, so prior development hashes and local feasibility
records do not qualify the final source commit or hosted release artifact.
