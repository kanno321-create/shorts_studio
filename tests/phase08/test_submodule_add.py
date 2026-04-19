"""Wave 1 REMOTE-03 — add_harness_submodule SHA-pinned submodule creation.

Validates scripts.publisher.github_remote.add_harness_submodule against the
CONTEXT D-02 contract (studios/shorts/harness/ submodule pinned to v1.0.1 SHA):

* test_submodule_add_three_commands_in_order    — exact 3-call argv sequence
* test_submodule_checkout_runs_in_harness_cwd   — checkout cwd ends at harness/
* test_submodule_default_path_is_harness        — default path arg is "harness"
* test_submodule_sha_is_passed_verbatim         — full SHA passes through unchanged
* test_submodule_path_collision_propagates_error — Pitfall 10 CalledProcessError
* test_git_add_includes_both_gitmodules_and_harness — final stage includes both
"""
from __future__ import annotations

import subprocess

import pytest

from scripts.publisher.github_remote import add_harness_submodule


@pytest.fixture
def capture_subprocess(monkeypatch):
    """Records every subprocess.run invocation (argv + cwd) and returns a
    _Completed(returncode=0) so all ``check=True`` calls succeed.
    """
    calls: list[dict] = []

    class _Completed:
        returncode = 0

    def _fake_run(argv, *, check=False, cwd=None, env=None, **kw):
        calls.append(
            {
                "argv": list(argv),
                "check": check,
                "cwd": str(cwd) if cwd else None,
            }
        )
        return _Completed()

    monkeypatch.setattr("subprocess.run", _fake_run)
    return calls


def test_submodule_add_three_commands_in_order(capture_subprocess):
    add_harness_submodule(
        "https://github.com/kanno321-create/naberal_harness",
        "abc1234567890",
        path="harness",
    )
    argvs = [c["argv"] for c in capture_subprocess]
    assert argvs == [
        [
            "git",
            "submodule",
            "add",
            "https://github.com/kanno321-create/naberal_harness",
            "harness",
        ],
        ["git", "checkout", "abc1234567890"],
        ["git", "add", ".gitmodules", "harness"],
    ]


def test_submodule_checkout_runs_in_harness_cwd(capture_subprocess):
    add_harness_submodule(
        "https://github.com/kanno321-create/naberal_harness",
        "abc1234567890",
    )
    checkout_call = capture_subprocess[1]
    assert checkout_call["argv"][:2] == ["git", "checkout"]
    assert "harness" in checkout_call["cwd"]


def test_submodule_default_path_is_harness(capture_subprocess):
    add_harness_submodule(
        "https://github.com/kanno321-create/naberal_harness",
        "abc1234567890",
    )
    add_call = capture_subprocess[0]
    assert add_call["argv"][-1] == "harness"


def test_submodule_sha_is_passed_verbatim(capture_subprocess):
    sha = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    add_harness_submodule(
        "https://github.com/kanno321-create/naberal_harness",
        sha,
    )
    checkout_call = capture_subprocess[1]
    assert checkout_call["argv"][2] == sha


def test_submodule_path_collision_propagates_error(monkeypatch):
    """Pitfall 10 anchor: pre-existing harness/ in index → CalledProcessError."""

    class _Completed:
        returncode = 128

    def _failing(argv, *, check=False, cwd=None, env=None, **kw):
        if check and argv[:3] == ["git", "submodule", "add"]:
            raise subprocess.CalledProcessError(
                128, argv, stderr="already exists in the index"
            )
        return _Completed()

    monkeypatch.setattr("subprocess.run", _failing)
    with pytest.raises(subprocess.CalledProcessError):
        add_harness_submodule(
            "https://github.com/kanno321-create/naberal_harness", "abc"
        )


def test_git_add_includes_both_gitmodules_and_harness(capture_subprocess):
    add_harness_submodule(
        "https://github.com/kanno321-create/naberal_harness", "abc"
    )
    add_call = capture_subprocess[2]
    assert add_call["argv"] == ["git", "add", ".gitmodules", "harness"]
