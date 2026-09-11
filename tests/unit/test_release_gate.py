from __future__ import annotations

from scripts import check_release


def test_release_gate_bootstraps_locked_test_environment(monkeypatch) -> None:
    calls: list[tuple[str, list[str]]] = []
    uv = "/usr/local/bin/uv"

    monkeypatch.setattr(check_release.shutil, "which", lambda executable: uv)
    monkeypatch.setattr(
        check_release,
        "run_step",
        lambda label, command: calls.append((label, command)),
    )

    assert check_release.main([]) == 0
    assert [label for label, _ in calls[:3]] == ["lock", "sync", "format"]
    assert calls[1] == (
        "sync",
        [uv, "sync", "--locked", "--all-groups", "--extra", "test"],
    )
