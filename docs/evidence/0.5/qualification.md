# Phase 0.5 qualification record

Each entry below records a current Phase 0.5 command, the exact approved
acceptance text, a locatable artifact section, source provenance, result,
and limitation. Platform and hosted-CI scope is summarized in [ci.md](ci.md).
Published upstream artifact hashes and probes are in
[upstream-artifact-qualification.md](upstream-artifact-qualification.md).

## AC-001

Task: metadata and lock
Command: `uv run python scripts/check_artifact.py`
Requirement: 0.5 source/wheel metadata and exact lock identify Python 3.11–3.13, the recorded corrected ETLantic train, unchanged qualified database pins, and no core/extra authentication client dependency.
Provenance: `contracts.md#acceptance-criteria`
Limitation: Local Python 3.12.13, macOS arm64; see ci.md for execution scope.
Result: PASS

## AC-002

Task: public exports
Command: `uv run pytest tests/unit/test_package.py -q`
Requirement: All 0.4 top-level exports remain in order and only `HostIdentityAdapter` is appended; no principal/context/token/policy shadow schema appears.
Provenance: `contracts.md#acceptance-criteria`
Limitation: Local Python 3.12.13, macOS arm64; see ci.md for execution scope.
Result: PASS

## AC-003

Task: native dependencies
Command: `uv run pytest tests/unit/test_identity.py tests/integration/test_identity_dependencies.py -q`
Requirement: Host adapter accepts native sync/async/keyword-only/nested Security/Depends/yield principal dependencies without executing them at construction; FastAPI owns their execution and teardown.
Provenance: `contracts.md#acceptance-criteria`
Limitation: Local Python 3.12.13, macOS arm64; see ci.md for execution scope.
Result: PASS

## AC-004

Task: stable adapter repr
Command: `uv run pytest tests/unit/test_identity.py::test_adapter_properties_are_stable_immutable_and_redacted -q`
Requirement: Adapter properties retain stable callable identity, immutable mode metadata, and bounded repr without principal/callable/credential contents.
Provenance: `contracts.md#acceptance-criteria`
Limitation: Local Python 3.12.13, macOS arm64; see ci.md for execution scope.
Result: PASS

## AC-005

Task: malformed principal rejection
Command: `uv run pytest tests/unit/test_identity.py::test_invalid_resolved_principal_is_401_before_context_or_authorization -q`
Requirement: Missing/wrong/malformed Principal output returns the specified upstream 401 and invokes no context factory or protected service/store.
Provenance: `contracts.md#acceptance-criteria`
Limitation: Local Python 3.12.13, macOS arm64; see ci.md for execution scope.
Result: PASS

## AC-006

Task: context principal identity
Command: `uv run pytest tests/integration/test_identity_dependencies.py::test_nested_security_keyword_only_and_yield_dependencies_remain_native -q`
Requirement: Valid subject/issuer/kind and Principal object identity reach the context factory and canonical context unchanged.
Provenance: `contracts.md#acceptance-criteria`
Limitation: Local Python 3.12.13, macOS arm64; see ci.md for execution scope.
Result: PASS

## AC-007

Task: context factory failures
Command: `uv run pytest tests/unit/test_identity.py -q`
Requirement: Async/generator/nonconforming context factories fail at construction; malformed/mismatched context output or unexpected factory failure returns the specified constant 503 before protected use.
Provenance: `contracts.md#acceptance-criteria`
Limitation: Local Python 3.12.13, macOS arm64; see ci.md for execution scope.
Result: PASS

## AC-008

Task: scope preservation
Command: `uv run pytest tests/unit/test_identity.py -q`
Requirement: Guarded context preserves all accepted upstream scope/key objects and never substitutes caller-provided tenant/workspace/environment/security-domain authority.
Provenance: `contracts.md#acceptance-criteria`
Limitation: Local Python 3.12.13, macOS arm64; see ci.md for execution scope.
Result: PASS

## AC-009

Task: bundle identity forms
Command: `uv run pytest tests/unit/test_identity_bundles.py -q`
Requirement: Bundle factories accept exactly adapter or a complete raw callback pair and reject missing/mixed forms or a nonconforming authorizer before engine/app mutation.
Provenance: `contracts.md#acceptance-criteria`
Limitation: Local Python 3.12.13, macOS arm64; see ci.md for execution scope.
Result: PASS

## AC-010

Task: production demo callback rejection
Command: `uv run pytest tests/unit/test_identity_bundles.py::test_postgresql_bundle_rejects_known_header_helpers_before_engine_creation tests/unit/test_identity_bundles.py::test_production_raw_callbacks_are_normalized_to_a_guard_pair -q`
Requirement: Genuine legacy PostgreSQL host callbacks normalize through host guards; known upstream header-demo dependencies and development adapters are rejected in production.
Provenance: `contracts.md#acceptance-criteria`
Limitation: Local Python 3.12.13, macOS arm64; see ci.md for execution scope.
Result: PASS

## AC-011

Task: local static identity
Command: `uv run pytest tests/unit/test_identity_bundles.py::test_development_static_settings_require_an_explicit_static_adapter tests/unit/test_identity_bundles.py::test_development_static_is_rejected_outside_local_profiles -q`
Requirement: `development_static` supplies only its validated fixed Principal/scope, still requires an authorizer, and is usable only with explicit local `development-static` settings.
Provenance: `contracts.md#acceptance-criteria`
Limitation: Local Python 3.12.13, macOS arm64; see ci.md for execution scope.
Result: PASS

## AC-012

Task: identity settings compatibility
Command: `uv run pytest tests/unit/test_identity_bundles.py tests/unit/test_phase_0_3.py -q`
Requirement: Existing settings/default/source/URL/TLS behavior remains; `development-static` is the sole added identity value, required explicitly and rejected outside local profiles.
Provenance: `contracts.md#acceptance-criteria`
Limitation: Local Python 3.12.13, macOS arm64; see ci.md for execution scope.
Result: PASS

## AC-013

Task: production identity preflight
Command: `uv run pytest tests/unit/test_identity.py::test_production_api_requires_adapter_before_router_materialization tests/integration/test_identity_dependencies.py::test_mount_rechecks_production_guard_before_mutating_the_host -q`
Requirement: Production/unknown-profile prebuilt APIs require a matching host guard pair and conforming authorizer at construction/mount; failure leaves host routes/state/handlers/lifespan/OpenAPI unchanged.
Provenance: `contracts.md#acceptance-criteria`
Limitation: Local Python 3.12.13, macOS arm64; see ci.md for execution scope.
Result: PASS

## AC-014

Task: provider object and lifecycle ownership
Command: `uv run pytest tests/unit/test_identity_bundles.py tests/review/test_phase_0_4_contract.py::test_sol_014_cancelled_construction_disposes_engine_once -q`
Requirement: The facade retains the exact API; bundles retain native store/caller-authorizer objects, one shared engine, explicit lifecycle ownership, and existing failure/cancellation/idempotent-close behavior.
Provenance: `contracts.md#acceptance-criteria`
Limitation: Local Python 3.12.13, macOS arm64; see ci.md for execution scope.
Result: PASS

## AC-015

Task: dependency overrides and OpenAPI security
Command: `uv run pytest tests/integration/test_identity_dependencies.py::test_nested_security_keyword_only_and_yield_dependencies_remain_native -q`
Requirement: Dependency overrides can target the original host callable and guarded upstream dependencies, can be removed normally, and preserve native security-scheme discovery/OpenAPI parity.
Provenance: `contracts.md#acceptance-criteria`
Limitation: Local Python 3.12.13, macOS arm64; see ci.md for execution scope.
Result: PASS

## AC-016

Task: mutation route security inventory
Command: `uv run pytest tests/security/test_mutation_authorization.py -q`
Requirement: Every mounted POST/PUT/PATCH/DELETE has a route-inventory-bound well-formed denial proof recording exact upstream action/resource/context before business lookup and demonstrating zero mutation; missing optional providers do not bypass denial.
Provenance: `contracts.md#acceptance-criteria`
Limitation: Local Python 3.12.13, macOS arm64; see ci.md for execution scope.
Result: PASS

## AC-017

Task: cross-scope denial probes
Command: `uv run pytest tests/security/test_scope_and_outages.py::test_collection_and_item_denials_do_not_disclose_cross_scope_data tests/security/test_scope_and_outages.py::test_protected_optional_reads_deny_before_unavailable_provider_lookup -q`
Requirement: Direct definition/run/registry/schedule/report/lineage/artifact-metadata probes preserve upstream 403/404 disclosure and reveal no protected cross-scope existence/content; only the documented caller-scoped run probe may follow denial.
Provenance: `contracts.md#acceptance-criteria`
Limitation: Local Python 3.12.13, macOS arm64; see ci.md for execution scope.
Result: PASS

## AC-018

Task: concrete list denial
Command: `uv run pytest tests/security/test_scope_and_outages.py::test_collection_and_item_denials_do_not_disclose_cross_scope_data tests/security/test_scope_and_outages.py::test_registry_workspace_list_filters_concrete_denials_and_denies_before_lookup -q`
Requirement: Collection denial prevents lookup, and wildcard collection allowance does not expose concrete list-denied definitions/workspaces or foreign-scope protected items.
Provenance: `contracts.md#acceptance-criteria`
Limitation: Local Python 3.12.13, macOS arm64; see ci.md for execution scope.
Result: PASS

## AC-019

Task: limited list filtering
Command: `uv run pytest tests/security/test_scope_and_outages.py::test_limited_lists_expand_until_visible_items_fill_existing_limit -q`
Requirement: Applicable item filtering occurs before existing limit/result-bound operations, so denied items occupy no result slots or reported totals/cursors; no new pagination API appears.
Provenance: `contracts.md#acceptance-criteria`
Limitation: Local Python 3.12.13, macOS arm64; see ci.md for execution scope.
Result: PASS

## AC-020

Task: concurrent principal contexts
Command: `uv run pytest tests/integration/test_identity_dependencies.py::test_concurrent_principals_keep_independent_scopes -q`
Requirement: Concurrent requests with different host principals/scopes deliver their own Principal/context to authorization/stores without request-state leakage or ShuETL global identity caching.
Provenance: `contracts.md#acceptance-criteria`
Limitation: Local Python 3.12.13, macOS arm64; see ci.md for execution scope.
Result: PASS

## AC-021

Task: SSE cursor ordering
Command: `uv run pytest tests/security/test_stream_authorization.py -q`
Requirement: SSE authorizes before cursor/event access, preserves foreign-run denial and authorized unknown/foreign-cursor 410, existing resume precedence/envelopes/follow caps, and dependency teardown on disconnect.
Provenance: `contracts.md#acceptance-criteria`
Limitation: Local Python 3.12.13, macOS arm64; see ci.md for execution scope.
Result: PASS

## AC-022

Task: run artifact metadata protection
Command: `uv run pytest tests/security/test_scope_and_outages.py::test_acceptance_receipt_metadata_authorizes_before_run_lookup -q`
Requirement: Existing acceptance-receipt artifact metadata is protected by `run.artifacts` before lookup; no artifact download/signing/storage implementation is added.
Provenance: `contracts.md#acceptance-criteria`
Limitation: Local Python 3.12.13, macOS arm64; see ci.md for execution scope.
Result: PASS

## AC-023

Task: identity and provider outages
Command: `uv run pytest tests/security/test_scope_and_outages.py tests/unit/test_identity.py::test_invalid_context_is_a_constant_503_without_exception_details -q`
Requirement: Host/membership/policy outages and required-provider failures yield unsuccessful sanitized responses and no identity/provider fallback, unauthorized mutation, fabricated acceptance, or partial-success list/stream.
Provenance: `contracts.md#acceptance-criteria`
Limitation: Local Python 3.12.13, macOS arm64; see ci.md for execution scope.
Result: PASS

## AC-024

Task: trigger identity persistence
Command: `uv run pytest tests/security/test_triggering_identity_and_execution_boundary.py::test_durable_submission_persists_only_trigger_identity_and_no_credentials tests/integration/test_postgresql.py::test_triggering_identity_is_persisted_without_host_credentials -q`
Requirement: Guarded triggering subject/issuer/kind persists in upstream durable submission metadata when that path is used; host tokens/cookies do not enter payloads/schedules and are not used as execution credentials.
Provenance: `contracts.md#acceptance-criteria`
Limitation: Local PostgreSQL 18.6 plus synthetic-memory credential sentinel; see ci.md.
Result: PASS

## AC-025

Task: secret resolution and execution boundary
Command: `uv run pytest tests/security/test_triggering_identity_and_execution_boundary.py::test_validate_plan_and_submit_never_resolve_secrets_or_execute -q`
Requirement: Instrumented gateway validate/plan/submit/schedule, composition/startup and doctor flows invoke no pipeline-secret resolution or pipeline executor.
Provenance: `contracts.md#acceptance-criteria`
Limitation: Local Python 3.12.13, macOS arm64; see ci.md for execution scope.
Result: PASS

## AC-026

Task: validation and credential redaction
Command: `uv run pytest tests/integration/test_identity_dependencies.py::test_upstream_validation_errors_are_redacted_without_changing_host_routes -q`
Requirement: Recognized credential-bearing inputs/sentinels are absent from the specified validation/problem/HTTP-422/log/event/SSE/readiness/doctor/OpenAPI/repr surfaces; invalid input still fails validation.
Provenance: `contracts.md#acceptance-criteria`
Limitation: Local Python 3.12.13, macOS arm64; see ci.md for execution scope.
Result: PASS

## AC-027

Task: doctor identity facts
Command: `uv run pytest tests/unit/test_identity_bundles.py::test_doctor_reports_configured_and_inspected_identity_without_authenticating -q`
Requirement: Doctor keeps its schema/shape/check order/exits and safely distinguishes configured host mode, inspected adapter mode and explicit local static development mode without authenticating or exposing identity/scope values.
Provenance: `contracts.md#acceptance-criteria`
Limitation: Local Python 3.12.13, macOS arm64; see ci.md for execution scope.
Result: PASS

## AC-028

Task: host OIDC and session recipes
Command: `uv run python scripts/check_clean_wheel.py`
Requirement: OIDC and session recipes consume already validated host identity through native dependencies, state host verification/CSRF/expiry requirements, reject invalid/outage cases in synthetic smoke harnesses, and add no credential validator to ShuETL.
Provenance: `contracts.md#acceptance-criteria`
Limitation: Local Python 3.12.13, macOS arm64; see ci.md for execution scope.
Result: PASS

## AC-029

Task: 0.4 compatibility regressions
Command: `uv run pytest -q`
Requirement: Existing local raw-callback, PostgreSQL persistence/restart/migration/idempotency/concurrency, CLI, mount/lifecycle/handler and OpenAPI contract assertions pass, except the explicitly documented production-security and corrected upstream list/422 changes.
Provenance: `contracts.md#acceptance-criteria`
Limitation: Local Python matrix and PostgreSQL 18.6; all hosted quality jobs passed on Python 3.11–3.13 in [CI run 36654619845](https://github.com/eddiethedean/shuetl/actions/runs/36654619845).
Result: PASS

## AC-030

Task: clean wheel imports
Command: `uv run python scripts/check_clean_wheel.py`
Requirement: Core/SQLite/PostgreSQL clean-wheel environments resolve exports from the wheel and execute a 0.5 identity smoke example without undeclared auth packages or repository-source imports.
Provenance: `contracts.md#acceptance-criteria`
Limitation: Clean wheel environments use the local Python 3.12.13 interpreter.
Result: PASS

## AC-031

Task: local release gate matrix
Command: `uv run python scripts/check_release.py`
Requirement: Ruff, Pyright, lock, boundary, unit/security/integration, build, artifact, OpenAPI and release/evidence gates pass; real PostgreSQL and 0.5 security tests execute on Python 3.11/3.12/3.13 in CI without required-test skips.
Provenance: `contracts.md#acceptance-criteria`
Limitation: Local release gate and all hosted quality, PostgreSQL, and release-gate jobs passed on Python 3.11–3.13 in [CI run 36654619845](https://github.com/eddiethedean/shuetl/actions/runs/36654619845).
Result: PASS

## AC-032

Task: evidence proof integrity
Command: `uv run pytest tests/unit/test_evidence_proofs.py tests/review/test_phase_0_4_evidence_contract.py tests/review/test_phase_0_4_evidence_semantics.py -q`
Requirement: A 0.5 evidence index maps each AC exactly once to its actual proof and limitations, binds the approved route/AC inventory and corrected train, rejects copied/unrelated/missing proofs, and contains no secrets or machine-specific paths.
Provenance: `contracts.md#acceptance-criteria`
Limitation: Local Python 3.12.13, macOS arm64; see ci.md for execution scope.
Result: PASS

## AC-033

Task: ETLantic 0.55 list-denial correction
Command: `uv run pytest tests/security/test_scope_and_outages.py::test_collection_and_item_denials_do_not_disclose_cross_scope_data tests/security/test_scope_and_outages.py::test_limited_lists_expand_until_visible_items_fill_existing_limit -q`
Requirement: Published upstream artifacts fix PB-001 with concrete collection-resource contracts, and installed-package tests demonstrate AC-018/019 through direct and ShuETL-mounted graphs.
Provenance: `contracts.md#acceptance-criteria`
Limitation: Published 0.55.0 installed artifacts; no ETLantic source is copied into ShuETL.
Result: PASS

## AC-034

Task: ETLantic 0.55 validation redaction
Command: `uv run pytest tests/integration/test_identity_dependencies.py::test_upstream_validation_errors_are_redacted_without_changing_host_routes -q`
Requirement: Published upstream artifacts fix PB-002 through a documented public seam, preserving safe HTTP-422 validation and unrelated host validation behavior in direct and embedded apps.
Provenance: `contracts.md#acceptance-criteria`
Limitation: Published 0.55.0 installed artifacts; unrelated host routes keep ordinary FastAPI errors.
Result: PASS
