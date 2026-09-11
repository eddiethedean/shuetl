"""Enforce the import and ownership boundary for importable ShuETL code."""

from __future__ import annotations

import argparse
import ast
import json
import sys
from dataclasses import dataclass
from pathlib import Path

PROHIBITED_IMPORT_ROOTS = {
    "alembic",
    "apscheduler",
    "celery",
    "dramatiq",
    "sqlmodel",
    "tenacity",
}
DOMAIN_CLASS_NAMES = {
    "Artifact",
    "Attempt",
    "Authorizer",
    "Event",
    "Executor",
    "Firing",
    "Pipeline",
    "Plan",
    "Report",
    "Run",
    "Schedule",
}
ROUTE_DECORATOR_NAMES = {"delete", "get", "patch", "post", "put", "websocket"}
MIGRATION_DIRECTORY_NAMES = {"alembic", "migrations"}


@dataclass(frozen=True)
class Violation:
    """One actionable boundary violation."""

    rule_id: str
    path: Path
    line: int
    message: str
    remediation: str

    def format(self, root: Path) -> str:
        try:
            display_path = self.path.relative_to(root)
        except ValueError:
            display_path = self.path
        return (
            f"{display_path}:{self.line}: {self.rule_id}: {self.message} "
            f"Remediation: {self.remediation}"
        )


def _module_from_import(node: ast.AST) -> str | None:
    if isinstance(node, ast.Import):
        return node.names[0].name if node.names else None
    if isinstance(node, ast.ImportFrom):
        return node.module
    return None


def _scan_file(path: Path) -> list[Violation]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except SyntaxError as exc:
        return [
            Violation(
                "BOUNDARY-SYNTAX",
                path,
                exc.lineno or 1,
                f"source cannot be parsed: {exc.msg}",
                "fix the syntax error before importing the package",
            )
        ]

    violations: list[Violation] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            module = _module_from_import(node)
            if not module:
                continue
            root = module.split(".", 1)[0]
            if root in PROHIBITED_IMPORT_ROOTS:
                violations.append(
                    Violation(
                        "BOUNDARY-IMPORT",
                        path,
                        node.lineno,
                        f"prohibited implementation dependency: {module}",
                        (
                            "use an ETLantic public contract or move the capability "
                            "upstream"
                        ),
                    )
                )
            if root in {"etlantic", "etlantic_fastapi"} and any(
                segment.startswith("_") for segment in module.split(".")[1:]
            ):
                violations.append(
                    Violation(
                        "BOUNDARY-PRIVATE",
                        path,
                        node.lineno,
                        f"private upstream import: {module}",
                        "import only documented public ETLantic package surfaces",
                    )
                )
        elif isinstance(node, ast.ClassDef) and node.name in DOMAIN_CLASS_NAMES:
            violations.append(
                Violation(
                    "BOUNDARY-DOMAIN",
                    path,
                    node.lineno,
                    f"ShuETL cannot define ETLantic domain class {node.name!r}",
                    "reuse the upstream model or protocol",
                )
            )
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for decorator in node.decorator_list:
                target = (
                    decorator.func if isinstance(decorator, ast.Call) else decorator
                )
                if (
                    isinstance(target, ast.Attribute)
                    and target.attr in ROUTE_DECORATOR_NAMES
                ):
                    violations.append(
                        Violation(
                            "BOUNDARY-ROUTE",
                            path,
                            decorator.lineno,
                            (
                                f"ShuETL route decorator {target.attr!r} duplicates "
                                "upstream HTTP ownership"
                            ),
                            (
                                "mount the etlantic-fastapi router instead of defining "
                                "a route"
                            ),
                        )
                    )
    return violations


def check_tree(root: Path) -> list[Violation]:
    """Return violations found below a source tree."""

    root = root.resolve()
    if not root.exists():
        return [
            Violation(
                "BOUNDARY-SOURCE",
                root,
                1,
                "source tree does not exist",
                "create the importable package before running boundary checks",
            )
        ]
    violations = [
        violation
        for path in sorted(root.rglob("*.py"))
        for violation in _scan_file(path)
    ]
    directories = [root, *[path for path in root.rglob("*") if path.is_dir()]]
    for directory in sorted(directories):
        if directory.name in MIGRATION_DIRECTORY_NAMES:
            violations.append(
                Violation(
                    "BOUNDARY-MIGRATION",
                    directory,
                    1,
                    f"production migration directory is forbidden: {directory.name}",
                    "use provider-owned ETLantic migrations outside ShuETL core",
                )
            )
    return violations


def check_openapi(path: Path) -> list[Violation]:
    """Check operation-ID uniqueness in an OpenAPI document."""

    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [
            Violation(
                "BOUNDARY-OPENAPI",
                path,
                1,
                f"cannot read OpenAPI evidence: {exc}",
                "generate a valid normalized OpenAPI document",
            )
        ]
    operations: list[tuple[str, str, str]] = []
    for route, item in document.get("paths", {}).items():
        if not isinstance(item, dict):
            continue
        for method, operation in item.items():
            if method.startswith("x-") or not isinstance(operation, dict):
                continue
            operation_id = operation.get("operationId")
            if isinstance(operation_id, str):
                operations.append((operation_id, method, route))
    seen: dict[str, tuple[str, str]] = {}
    violations: list[Violation] = []
    for operation_id, method, route in operations:
        prior = seen.get(operation_id)
        if prior is not None:
            violations.append(
                Violation(
                    "BOUNDARY-OPERATION-ID",
                    path,
                    1,
                    (
                        f"duplicate operationId {operation_id!r} at {method.upper()} "
                        f"{route}; "
                        f"first seen at {prior[0].upper()} {prior[1]}"
                    ),
                    "preserve the unique upstream operation IDs",
                )
            )
        else:
            seen[operation_id] = (method, route)
    return violations


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=Path("src/shuetl"))
    parser.add_argument("--openapi", type=Path)
    args = parser.parse_args(argv)
    violations = check_tree(args.source)
    if args.openapi is not None:
        violations.extend(check_openapi(args.openapi))
    if violations:
        root = args.source.resolve()
        for violation in violations:
            print(violation.format(root), file=sys.stderr)
        return 1
    print("boundary checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
