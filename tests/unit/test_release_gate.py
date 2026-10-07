from __future__ import annotations

from scripts import check_release


def test_release_gate_bootstraps_locked_test_environment(monkeypatch) -> None:
    calls: list[tuple[str, list[str], tuple[str, ...]]] = []
    uv = "/usr/local/bin/uv"

    monkeypatch.setattr(check_release.shutil, "which", lambda executable: uv)
    monkeypatch.setattr(
        check_release,
        "run_step",
        lambda label, command, *, unset_env=(): calls.append(
            (label, command, unset_env)
        ),
    )

    assert check_release.main([]) == 0
    assert [label for label, _, _ in calls[:3]] == ["lock", "sync", "format"]
    assert calls[1] == (
        "sync",
        [
            uv,
            "sync",
            "--locked",
            "--all-groups",
            "--extra",
            "test",
            "--extra",
            "sqlite",
            "--extra",
            "postgresql",
            "--extra",
            "sql",
        ],
        (),
    )
    test_call = next(call for call in calls if call[0] == "tests")
    assert test_call[2] == (
        "SHUETL_PROFILE",
        "SHUETL_ROLE",
        "SHUETL_PROVIDER",
        "SHUETL_IDENTITY",
        "SHUETL_DATABASE_URL",
        "SHUETL_RUNTIME_DATABASE_URL",
        "SHUETL_POSTGRESQL_SSLMODE",
    )
