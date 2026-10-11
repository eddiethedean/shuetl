"""Bind hosted Phase 0.6 qualification artifacts to the release candidate."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

PYTHON_VERSIONS = ("3.11", "3.12", "3.13")


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected a JSON object: {path}")
    return value


def _require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def _role_names(value: Any) -> set[str]:
    if not isinstance(value, list):
        return set()
    return {
        row["role"]
        for row in value
        if isinstance(row, dict) and isinstance(row.get("role"), str)
    }


def _has_roles(value: Any, expected: set[str]) -> bool:
    return (
        isinstance(value, list)
        and len(value) == len(expected)
        and (_role_names(value) == expected)
    )


def check_hosted_evidence(
    artifacts_dir: Path, evidence_dir: Path, source_commit: str
) -> list[str]:
    errors: list[str] = []
    if not re.fullmatch(r"[0-9a-f]{40}", source_commit):
        return ["hosted source commit must be a full lowercase Git SHA"]

    manifests = sorted(evidence_dir.glob("local-*/manifest.json"))
    if not manifests:
        return ["no Phase 0.6 candidate manifest is present"]
    try:
        manifest = _read_json(manifests[-1])
    except (OSError, ValueError) as exc:
        return [f"cannot read Phase 0.6 candidate manifest: {exc}"]
    expected = manifest.get("candidate_artifacts_sha256")
    if not isinstance(expected, dict):
        return ["candidate manifest has no artifact hashes"]
    expected_hashes = {
        "shuetl_wheel": expected.get("shuetl_wheel"),
        "gate0_reference_wheel": expected.get("gate0_reference_wheel"),
        "host_bindings_wheel": expected.get("host_bindings_wheel"),
    }
    for name, digest in expected_hashes.items():
        _require(
            isinstance(digest, str) and bool(re.fullmatch(r"[0-9a-f]{64}", digest)),
            f"candidate manifest has no valid {name} hash",
            errors,
        )
    if errors:
        return errors

    def read_record(relative: str) -> dict[str, Any] | None:
        path = artifacts_dir / relative
        try:
            return _read_json(path)
        except (OSError, ValueError) as exc:
            errors.append(f"cannot read hosted qualification record {relative}: {exc}")
            return None

    def candidate_record(
        record: dict[str, Any] | None,
        *,
        label: str,
        schema: str,
        reference_key: str,
    ) -> None:
        if record is None:
            return
        _require(record.get("schema") == schema, f"{label}: unexpected schema", errors)
        _require(record.get("result") == "PASS", f"{label}: result is not PASS", errors)
        _require(
            str(record.get("postgresql_version", "")).startswith("18.6"),
            f"{label}: PostgreSQL version is not 18.6",
            errors,
        )
        _require(
            record.get("source_commit") == source_commit,
            f"{label}: source commit differs from this hosted run",
            errors,
        )
        _require(
            record.get("shuetl_wheel_sha256") == expected_hashes["shuetl_wheel"],
            f"{label}: ShuETL wheel differs from the candidate manifest",
            errors,
        )
        _require(
            record.get("reference_wheel_sha256") == expected_hashes[reference_key],
            f"{label}: reference wheel differs from the candidate manifest",
            errors,
        )

    for python_version in PYTHON_VERSIONS:
        cli = read_record(
            f"phase06-cli-postgresql-python-{python_version}/"
            f"cli-postgresql-{python_version}.json"
        )
        candidate_record(
            cli,
            label=f"CLI Python {python_version}",
            schema="shuetl.phase06.cli-gate/1",
            reference_key="host_bindings_wheel",
        )
        if cli is not None:
            _require(
                str(cli.get("python", "")).startswith(python_version + "."),
                f"CLI Python {python_version}: interpreter version mismatch",
                errors,
            )
            _require(
                _has_roles(
                    cli.get("active_drain"),
                    {"gateway", "scheduler", "run_worker", "action_worker"},
                ),
                f"CLI Python {python_version}: active drain coverage is incomplete",
                errors,
            )
            _require(
                _has_roles(
                    cli.get("forced_termination"),
                    {"scheduler", "worker-actions", "worker-runs"},
                ),
                f"CLI Python {python_version}: force coverage is incomplete",
                errors,
            )

        container = read_record(
            f"phase06-container-postgresql-python-{python_version}/"
            f"container-postgresql-{python_version}.json"
        )
        candidate_record(
            container,
            label=f"Container Python {python_version}",
            schema="shuetl.phase06.container/1",
            reference_key="host_bindings_wheel",
        )
        if container is not None:
            _require(
                str(container.get("python", "")).startswith(python_version + "."),
                f"Container Python {python_version}: interpreter version mismatch",
                errors,
            )
            _require(
                container.get("platform") == "linux/amd64",
                f"Container Python {python_version}: platform is not linux/amd64",
                errors,
            )
            _require(
                _has_roles(
                    container.get("active_drain"),
                    {"gateway", "scheduler", "run_worker", "action_worker"},
                ),
                "Container Python "
                f"{python_version}: active drain coverage is incomplete",
                errors,
            )

        gate0 = read_record(
            f"phase06-gate0-postgresql-python-{python_version}/"
            f"postgresql-gate0-{python_version}.json"
        )
        candidate_record(
            gate0,
            label=f"Gate 0 Python {python_version}",
            schema="shuetl.phase06.gate0/1",
            reference_key="gate0_reference_wheel",
        )

        faults = read_record(
            f"phase06-faults-postgresql-python-{python_version}/"
            f"postgresql-faults-{python_version}.json"
        )
        candidate_record(
            faults,
            label=f"Crash recovery Python {python_version}",
            schema="shuetl.phase06.gate0/1",
            reference_key="gate0_reference_wheel",
        )
        if faults is not None:
            crashes = faults.get("crashes")
            _require(
                isinstance(crashes, dict)
                and crashes.get("schema") == "shuetl.phase06.crashes/1"
                and crashes.get("result") == "PASS"
                and isinstance(crashes.get("cases"), list)
                and len(crashes["cases"]) == 22
                and all(
                    isinstance(case, dict) and case.get("result") == "PASS"
                    for case in crashes["cases"]
                ),
                f"Crash recovery Python {python_version}: all 22 cases must pass",
                errors,
            )

        transition = read_record(
            f"phase06-cli-postgresql-python-{python_version}/"
            f"transition-{python_version}.json"
        )
        if transition is not None:
            _require(
                transition.get("schema") == "shuetl.phase06.transition/1"
                and transition.get("result") == "PASS"
                and transition.get("source_commit") == source_commit,
                f"Transition Python {python_version}: result or source commit mismatch",
                errors,
            )

    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifacts", required=True, type=Path)
    parser.add_argument("--evidence", required=True, type=Path)
    parser.add_argument("--source-commit", required=True)
    args = parser.parse_args(argv)
    errors = check_hosted_evidence(args.artifacts, args.evidence, args.source_commit)
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    print("hosted Phase 0.6 records match the frozen candidate")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
