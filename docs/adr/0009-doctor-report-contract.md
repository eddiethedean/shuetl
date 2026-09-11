# ADR-0009: Doctor Report Contract

- Status: Accepted
- Date: 2026-09-11

## Context

Local configuration failures currently surface across package installation,
provider construction, and application startup. Phase 0.3 needs one safe
preflight command for people and automation without creating a competing HTTP
readiness contract.

## Decision

`shuetl doctor` emits one versioned `shuetl.doctor/1` report. Text and JSON are
two renderings of the same typed `DoctorReport`; JSON is selected with
`--format json`. The report is deterministic and contains no timestamp, current
working directory, database URL, credential, secret value, or exception
representation.

Checks cover configuration validity, installed-package compatibility, optional
provider availability, selected profile and role, configured versus available
capabilities, provider readiness, relational schema status, explicit identity,
and the development-only topology warning.

Expected invalid or unavailable states are report results rather than uncaught
exceptions. Exit status is `0` when all required checks pass, `1` when a required
check fails, and `2` only for CLI usage errors. Warnings do not change a passing
exit status.

The command is a configuration/provider preflight. ETLantic's mounted `/ready`
route remains authoritative for the live API graph; `doctor` does not add an
HTTP route, contact remote services, apply migrations, or execute pipeline work.

## Consequences

CI and operators can consume stable JSON while terminal users receive actionable
summaries. The schema version makes future additions explicit and prevents
unversioned output drift.

## Alternatives

- Reuse `/ready` output; rejected because a CLI must diagnose installation and
  configuration before an application exists.
- Emit ad hoc log lines only; rejected because automation needs stable fields
  and exit behavior.
- Include raw exceptions for debugging; rejected because provider exceptions can
  contain URLs, credentials, paths, or environment values.

## Validation

The released baseline is recorded in the 0.2
[contract inventory](../evidence/0.2/contracts.md) and
[ownership matrix](../evidence/0.2/ownership.md).

See AC-025 through AC-036 in
[`PHASE_0_3_EXECUTION.md`](../plans/PHASE_0_3_EXECUTION.md).

## Revisit trigger

Increment the schema identifier before a breaking JSON-shape change. Production
network probes or migration commands require their own contract and are outside
this ADR.
