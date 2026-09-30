# Phase 0.5 evidence index

This ledger records Phase 0.5 qualification against the published ETLantic 0.55.0 train and ShuETL 0.5.0 release. ShuETL 0.5.0 was published to PyPI on 2026-09-30 UTC from tag `v0.5.0` at commit `d846c3dd15b517def5c736e831202a603ca0e080`; the tag-triggered workflow passed all checks, built both distributions, and published them through Trusted Publishing. The initial hosted baseline run predates the AC-017 remediation; the later pre-tag and release runs qualify the final commit with that proof included. See [published artifact details](#published-artifacts), [the approved contract](contracts.md), [ownership](ownership.md), [per-criterion qualification](qualification.md), [workflow and release records](ci.md), and [the exact upstream artifacts](upstream-artifact-qualification.md).

## Published artifacts

PyPI reports both files uploaded at 02:27 UTC on 2026-09-30. Their SHA-256
digests identify the immutable release distributions:

| Published PyPI file | SHA-256 |
| --- | --- |
| `shuetl-0.5.0-py3-none-any.whl` | `cfa560e22d9ab6b4d956408a7062e9cc04752798e5c8b17c394877a292ad84b6` |
| `shuetl-0.5.0.tar.gz` | `f4d9dacdc650879d14c7bba302ababd5597d4db5c7e2e999323bdf7caaa10924` |

## Implementation qualification

| Field | Value |
| --- | --- |
| OS and architecture | macOS 26.5.2 arm64 local |
| Python version | 3.11.15, 3.12.13, and 3.13.11 local; hosted CI passed on 3.11, 3.12, and 3.13 |
| uv version | 0.11.3 |
| ETLantic source revision | etlantic, etlantic-fastapi and etlantic-sqlmodel 0.55.0 release wheels |
| ShuETL import origin | installed project or isolated built wheel; see clean-wheel gate |
| ETLantic import origin | installed 0.55.0 wheel; see clean-wheel gate |
| etlantic-fastapi import origin | installed 0.55.0 wheel; see clean-wheel gate |
| FastAPI import origin | installed exact dependency; see clean-wheel gate |
| Pydantic import origin | installed exact dependency; see clean-wheel gate |
| HTTPX import origin | installed httpx2 2.12.0 test extra; see clean-wheel gate |
| PostgreSQL server | 18.6 local disposable service and hosted PostgreSQL matrix |
| Gate A | local source / Python matrix | PASS |
| Gate B | live PostgreSQL 18.6 integration | PASS |
| Gate C | local build, artifact, wheel and evidence gate | PASS |
| Build hash scope | deterministic builds of this documentation-updated checkout; published PyPI digests are listed above |
| SHA-256 wheel | `e928dccd879a11411c12aa05eeb2480f9946ce3cb8b10672afbc4d0da2cd623a` |
| SHA-256 sdist | `e33d7b77acd745cec54a5dd3a8015c052c41f15a1a4dfa0b85c3eea0db82e930` |

## Acceptance results

The proof registry binds the exact approved requirement, executable command, qualification section, provenance, and limitation. Commands and outcomes are not carried forward from 0.4. Local qualification and hosted CI both pass; the hosted matrix is recorded in [ci.md](ci.md).

| Criterion | Task | Command | Artifact | Status | Limitation | Reviewer | Date |
| --- | --- | --- | --- | --- | --- | --- | --- |
| AC-001 | metadata and lock | `uv run python scripts/check_artifact.py` | `qualification.md#ac-001` | PASS | Local Python 3.12.13, macOS arm64; see ci.md for execution scope. | implementation run | 2026-09-29 |
| AC-002 | public exports | `uv run pytest tests/unit/test_package.py -q` | `qualification.md#ac-002` | PASS | Local Python 3.12.13, macOS arm64; see ci.md for execution scope. | implementation run | 2026-09-29 |
| AC-003 | native dependencies | `uv run pytest tests/unit/test_identity.py tests/integration/test_identity_dependencies.py -q` | `qualification.md#ac-003` | PASS | Local Python 3.12.13, macOS arm64; see ci.md for execution scope. | implementation run | 2026-09-29 |
| AC-004 | stable adapter repr | `uv run pytest tests/unit/test_identity.py::test_adapter_properties_are_stable_immutable_and_redacted -q` | `qualification.md#ac-004` | PASS | Local Python 3.12.13, macOS arm64; see ci.md for execution scope. | implementation run | 2026-09-29 |
| AC-005 | malformed principal rejection | `uv run pytest tests/unit/test_identity.py::test_invalid_resolved_principal_is_401_before_context_or_authorization -q` | `qualification.md#ac-005` | PASS | Local Python 3.12.13, macOS arm64; see ci.md for execution scope. | implementation run | 2026-09-29 |
| AC-006 | context principal identity | `uv run pytest tests/integration/test_identity_dependencies.py::test_nested_security_keyword_only_and_yield_dependencies_remain_native -q` | `qualification.md#ac-006` | PASS | Local Python 3.12.13, macOS arm64; see ci.md for execution scope. | implementation run | 2026-09-29 |
| AC-007 | context factory failures | `uv run pytest tests/unit/test_identity.py -q` | `qualification.md#ac-007` | PASS | Local Python 3.12.13, macOS arm64; see ci.md for execution scope. | implementation run | 2026-09-29 |
| AC-008 | scope preservation | `uv run pytest tests/unit/test_identity.py -q` | `qualification.md#ac-008` | PASS | Local Python 3.12.13, macOS arm64; see ci.md for execution scope. | implementation run | 2026-09-29 |
| AC-009 | bundle identity forms | `uv run pytest tests/unit/test_identity_bundles.py -q` | `qualification.md#ac-009` | PASS | Local Python 3.12.13, macOS arm64; see ci.md for execution scope. | implementation run | 2026-09-29 |
| AC-010 | production demo callback rejection | `uv run pytest tests/unit/test_identity_bundles.py::test_postgresql_bundle_rejects_known_header_helpers_before_engine_creation tests/unit/test_identity_bundles.py::test_production_raw_callbacks_are_normalized_to_a_guard_pair -q` | `qualification.md#ac-010` | PASS | Local Python 3.12.13, macOS arm64; see ci.md for execution scope. | implementation run | 2026-09-29 |
| AC-011 | local static identity | `uv run pytest tests/unit/test_identity_bundles.py::test_development_static_settings_require_an_explicit_static_adapter tests/unit/test_identity_bundles.py::test_development_static_is_rejected_outside_local_profiles -q` | `qualification.md#ac-011` | PASS | Local Python 3.12.13, macOS arm64; see ci.md for execution scope. | implementation run | 2026-09-29 |
| AC-012 | identity settings compatibility | `uv run pytest tests/unit/test_identity_bundles.py tests/unit/test_phase_0_3.py -q` | `qualification.md#ac-012` | PASS | Local Python 3.12.13, macOS arm64; see ci.md for execution scope. | implementation run | 2026-09-29 |
| AC-013 | production identity preflight | `uv run pytest tests/unit/test_identity.py::test_production_api_requires_adapter_before_router_materialization tests/integration/test_identity_dependencies.py::test_mount_rechecks_production_guard_before_mutating_the_host -q` | `qualification.md#ac-013` | PASS | Local Python 3.12.13, macOS arm64; see ci.md for execution scope. | implementation run | 2026-09-29 |
| AC-014 | provider object and lifecycle ownership | `uv run pytest tests/unit/test_identity_bundles.py tests/review/test_phase_0_4_contract.py::test_sol_014_cancelled_construction_disposes_engine_once -q` | `qualification.md#ac-014` | PASS | Local Python 3.12.13, macOS arm64; see ci.md for execution scope. | implementation run | 2026-09-29 |
| AC-015 | dependency overrides and OpenAPI security | `uv run pytest tests/integration/test_identity_dependencies.py::test_nested_security_keyword_only_and_yield_dependencies_remain_native -q` | `qualification.md#ac-015` | PASS | Local Python 3.12.13, macOS arm64; see ci.md for execution scope. | implementation run | 2026-09-29 |
| AC-016 | mutation route security inventory | `uv run pytest tests/security/test_mutation_authorization.py -q` | `qualification.md#ac-016` | PASS | Local Python 3.12.13, macOS arm64; see ci.md for execution scope. | implementation run | 2026-09-29 |
| AC-017 | cross-scope denial probes | `uv run pytest tests/security/test_scope_and_outages.py::test_collection_and_item_denials_do_not_disclose_cross_scope_data tests/security/test_scope_and_outages.py::test_protected_optional_reads_deny_before_unavailable_provider_lookup tests/security/test_scope_and_outages.py::test_existing_foreign_registry_and_schedule_records_are_denied_before_lookup -q` | `qualification.md#ac-017` | PASS | Local Python 3.12.13, macOS arm64; 14 passed, including direct and mounted configured-provider denial checks. Added after initial hosted baseline run 36654931532; included in pre-tag run 36659423353 and release run 36659686930 for commit `d846c3d`. | implementation run | 2026-09-29 |
| AC-018 | concrete list denial | `uv run pytest tests/security/test_scope_and_outages.py::test_collection_and_item_denials_do_not_disclose_cross_scope_data tests/security/test_scope_and_outages.py::test_registry_workspace_list_filters_concrete_denials_and_denies_before_lookup -q` | `qualification.md#ac-018` | PASS | Local Python 3.12.13, macOS arm64; see ci.md for execution scope. | implementation run | 2026-09-29 |
| AC-019 | limited list filtering | `uv run pytest tests/security/test_scope_and_outages.py::test_limited_lists_expand_until_visible_items_fill_existing_limit -q` | `qualification.md#ac-019` | PASS | Local Python 3.12.13, macOS arm64; see ci.md for execution scope. | implementation run | 2026-09-29 |
| AC-020 | concurrent principal contexts | `uv run pytest tests/integration/test_identity_dependencies.py::test_concurrent_principals_keep_independent_scopes -q` | `qualification.md#ac-020` | PASS | Local Python 3.12.13, macOS arm64; see ci.md for execution scope. | implementation run | 2026-09-29 |
| AC-021 | SSE cursor ordering | `uv run pytest tests/security/test_stream_authorization.py -q` | `qualification.md#ac-021` | PASS | Local Python 3.12.13, macOS arm64; see ci.md for execution scope. | implementation run | 2026-09-29 |
| AC-022 | run artifact metadata protection | `uv run pytest tests/security/test_scope_and_outages.py::test_acceptance_receipt_metadata_authorizes_before_run_lookup -q` | `qualification.md#ac-022` | PASS | Local Python 3.12.13, macOS arm64; see ci.md for execution scope. | implementation run | 2026-09-29 |
| AC-023 | identity and provider outages | `uv run pytest tests/security/test_scope_and_outages.py tests/unit/test_identity.py::test_invalid_context_is_a_constant_503_without_exception_details -q` | `qualification.md#ac-023` | PASS | Local Python 3.12.13, macOS arm64; see ci.md for execution scope. | implementation run | 2026-09-29 |
| AC-024 | trigger identity persistence | `uv run pytest tests/security/test_triggering_identity_and_execution_boundary.py::test_durable_submission_persists_only_trigger_identity_and_no_credentials tests/integration/test_postgresql.py::test_triggering_identity_is_persisted_without_host_credentials -q` | `qualification.md#ac-024` | PASS | Local PostgreSQL 18.6 plus synthetic-memory credential sentinel; see ci.md. | implementation run | 2026-09-29 |
| AC-025 | secret resolution and execution boundary | `uv run pytest tests/security/test_triggering_identity_and_execution_boundary.py::test_validate_plan_and_submit_never_resolve_secrets_or_execute -q` | `qualification.md#ac-025` | PASS | Local Python 3.12.13, macOS arm64; see ci.md for execution scope. | implementation run | 2026-09-29 |
| AC-026 | validation and credential redaction | `uv run pytest tests/integration/test_identity_dependencies.py::test_upstream_validation_errors_are_redacted_without_changing_host_routes -q` | `qualification.md#ac-026` | PASS | Local Python 3.12.13, macOS arm64; see ci.md for execution scope. | implementation run | 2026-09-29 |
| AC-027 | doctor identity facts | `uv run pytest tests/unit/test_identity_bundles.py::test_doctor_reports_configured_and_inspected_identity_without_authenticating -q` | `qualification.md#ac-027` | PASS | Local Python 3.12.13, macOS arm64; see ci.md for execution scope. | implementation run | 2026-09-29 |
| AC-028 | host OIDC and session recipes | `uv run python scripts/check_clean_wheel.py` | `qualification.md#ac-028` | PASS | Local Python 3.12.13, macOS arm64; see ci.md for execution scope. | implementation run | 2026-09-29 |
| AC-029 | 0.4 compatibility regressions | `uv run pytest -q` | `qualification.md#ac-029` | PASS | Local Python matrix and PostgreSQL 18.6; hosted quality jobs passed on Python 3.11–3.13 for baseline commit `6e69b57` in [CI run 36654931532](https://github.com/eddiethedean/shuetl/actions/runs/36654931532), and the final commit `d846c3d` passed in [pre-tag CI run 36659423353](https://github.com/eddiethedean/shuetl/actions/runs/36659423353) and [release run 36659686930](https://github.com/eddiethedean/shuetl/actions/runs/36659686930). | implementation run | 2026-09-29 |
| AC-030 | clean wheel imports | `uv run python scripts/check_clean_wheel.py` | `qualification.md#ac-030` | PASS | Clean wheel environments use the local Python 3.12.13 interpreter. | implementation run | 2026-09-29 |
| AC-031 | local release gate matrix | `uv run python scripts/check_release.py` | `qualification.md#ac-031` | PASS | Local release gate and hosted quality, PostgreSQL, and release-gate jobs passed on Python 3.11–3.13 for baseline commit `6e69b57` in [CI run 36654931532](https://github.com/eddiethedean/shuetl/actions/runs/36654931532); the final release commit `d846c3d` passed the same matrix in [pre-tag CI run 36659423353](https://github.com/eddiethedean/shuetl/actions/runs/36659423353) and [release run 36659686930](https://github.com/eddiethedean/shuetl/actions/runs/36659686930). | implementation run | 2026-09-29 |
| AC-032 | evidence proof integrity | `uv run pytest tests/unit/test_evidence_proofs.py tests/review/test_phase_0_4_evidence_contract.py tests/review/test_phase_0_4_evidence_semantics.py -q` | `qualification.md#ac-032` | PASS | Local Python 3.12.13, macOS arm64; see ci.md for execution scope. | implementation run | 2026-09-29 |
| AC-033 | ETLantic 0.55 list-denial correction | `uv run pytest tests/security/test_scope_and_outages.py::test_collection_and_item_denials_do_not_disclose_cross_scope_data tests/security/test_scope_and_outages.py::test_limited_lists_expand_until_visible_items_fill_existing_limit -q` | `qualification.md#ac-033` | PASS | Published 0.55.0 installed artifacts; no ETLantic source is copied into ShuETL. | implementation run | 2026-09-29 |
| AC-034 | ETLantic 0.55 validation redaction | `uv run pytest tests/integration/test_identity_dependencies.py::test_upstream_validation_errors_are_redacted_without_changing_host_routes -q` | `qualification.md#ac-034` | PASS | Published 0.55.0 installed artifacts; unrelated host routes keep ordinary FastAPI errors. | implementation run | 2026-09-29 |

## Boundary review and gap register

The integration burden remains in ShuETL's composition layer, public composition hooks remain injected, and no copied route or pipeline model is introduced. ShuETL remains materially easier to maintain than a parallel control-plane implementation; no behavior is contributed to `etlantic-fastapi`.

Boundary outcome: **proceed-to-0.5** for the implementation baseline at commit `6e69b57`; hosted CI passed in [run 36654931532](https://github.com/eddiethedean/shuetl/actions/runs/36654931532). The follow-up AC-017 configured-provider proof passed locally and was included in hosted CI for final commit `d846c3d`. The exact 0.55.0 upstream artifacts satisfy PB-001 and PB-002; their issue tracker entries remain open. ShuETL 0.5.0 was published to PyPI on 2026-09-30 UTC from tag `v0.5.0`; the [release workflow](https://github.com/eddiethedean/shuetl/actions/runs/36659686930) passed.
