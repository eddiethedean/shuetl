"""Positive and negative tests for the Phase 0.1 boundary checker."""

from __future__ import annotations

import json
from pathlib import Path

from scripts.check_boundaries import check_openapi, check_tree

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "tests" / "boundary" / "fixtures"


def test_real_source_and_positive_fixture_pass() -> None:
    assert check_tree(ROOT / "src" / "shuetl") == []
    assert check_tree(FIXTURES / "pass") == []


def test_forbidden_import_is_rejected() -> None:
    violations = check_tree(FIXTURES / "forbidden_import")
    assert any(item.rule_id == "BOUNDARY-IMPORT" for item in violations)


def test_private_upstream_import_is_rejected() -> None:
    violations = check_tree(FIXTURES / "private_import")
    assert any(item.rule_id == "BOUNDARY-PRIVATE" for item in violations)


def test_route_decorator_is_rejected() -> None:
    violations = check_tree(FIXTURES / "route_decorator")
    assert any(item.rule_id == "BOUNDARY-ROUTE" for item in violations)


def test_shadow_domain_class_is_rejected() -> None:
    violations = check_tree(FIXTURES / "shadow_model")
    assert any(item.rule_id == "BOUNDARY-DOMAIN" for item in violations)


def test_migration_directory_is_rejected() -> None:
    violations = check_tree(FIXTURES / "migrations")
    assert any(item.rule_id == "BOUNDARY-MIGRATION" for item in violations)


def test_duplicate_operation_ids_are_rejected(tmp_path: Path) -> None:
    evidence = tmp_path / "openapi.json"
    evidence.write_text(
        json.dumps(
            {
                "paths": {
                    "/one": {"get": {"operationId": "same"}},
                    "/two": {"post": {"operationId": "same"}},
                }
            }
        ),
        encoding="utf-8",
    )
    violations = check_openapi(evidence)
    assert [item.rule_id for item in violations] == ["BOUNDARY-OPERATION-ID"]
