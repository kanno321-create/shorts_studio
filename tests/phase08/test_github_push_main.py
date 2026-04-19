"""Wave 1 REMOTE-02 — push_to_remote branch rename + GIT_ASKPASS + Pitfall 2 guard.

Validates scripts.publisher.github_remote.push_to_remote against the CONTEXT
D-03 (main branch rename) + Pitfall 2 (no URL-embedded credentials) contract:

* test_push_three_commands_in_order      — exactly 3 subprocess calls in order
* test_push_propagates_git_askpass       — env carries GIT_ASKPASS + GITHUB_TOKEN
* test_push_does_not_embed_token_in_remote_url — Pitfall 2 anchor on remote-add argv
* test_push_rejects_url_with_embedded_credentials — Pitfall 2 static guard raises
* test_push_master_to_main_rename        — first call is ``git branch -M main``

All tests monkeypatch subprocess.run, so no real git invocation occurs.
"""
from __future__ import annotations

import pytest

from scripts.publisher.exceptions import GitHubRemoteError
from scripts.publisher.github_remote import ASKPASS_SCRIPT, push_to_remote


@pytest.fixture
def capture_subprocess(monkeypatch):
    """Records every subprocess.run invocation (argv + cwd + env) and returns
    a benign _Completed(returncode=0) so callers don't trip ``check=True``.
    """
    calls: list[dict] = []

    class _Completed:
        returncode = 0

    def _fake_run(argv, *, check=False, cwd=None, env=None, **kw):
        calls.append(
            {
                "argv": list(argv),
                "check": check,
                "cwd": cwd,
                "env": dict(env) if env else None,
            }
        )
        return _Completed()

    monkeypatch.setattr("subprocess.run", _fake_run)
    return calls


def test_push_three_commands_in_order(capture_subprocess, fake_env_github_token):
    push_to_remote(
        "https://github.com/kanno321-create/shorts_studio.git",
        token="ghp_x",
        branch="main",
    )
    argvs = [c["argv"] for c in capture_subprocess]
    assert argvs == [
        ["git", "branch", "-M", "main"],
        [
            "git",
            "remote",
            "add",
            "origin",
            "https://github.com/kanno321-create/shorts_studio.git",
        ],
        ["git", "push", "-u", "origin", "main"],
    ]


def test_push_propagates_git_askpass(capture_subprocess):
    push_to_remote(
        "https://github.com/kanno321-create/shorts_studio.git",
        token="ghp_xyz",
        branch="main",
    )
    push_call = [c for c in capture_subprocess if c["argv"][:2] == ["git", "push"]][0]
    assert push_call["env"] is not None
    assert push_call["env"]["GIT_ASKPASS"] == str(ASKPASS_SCRIPT.resolve())
    assert push_call["env"]["GITHUB_TOKEN"] == "ghp_xyz"


def test_push_does_not_embed_token_in_remote_url(capture_subprocess):
    push_to_remote(
        "https://github.com/kanno321-create/shorts_studio.git",
        token="ghp_secret",
        branch="main",
    )
    remote_add_call = [
        c for c in capture_subprocess if c["argv"][:3] == ["git", "remote", "add"]
    ][0]
    # Pitfall 2 anchor: ghp_secret MUST NOT appear anywhere in remote add argv
    assert "ghp_secret" not in " ".join(remote_add_call["argv"])
    # Host component must not contain '@' (no user@host form in URL)
    url_arg = remote_add_call["argv"][-1]
    host = url_arg.split("://", 1)[-1].split("/", 1)[0]
    assert "@" not in host


def test_push_rejects_url_with_embedded_credentials():
    with pytest.raises(GitHubRemoteError) as exc_info:
        push_to_remote(
            "https://ghp_x@github.com/kanno321-create/shorts_studio.git",
            token="ghp_x",
            branch="main",
        )
    assert "Pitfall 2" in str(exc_info.value)


def test_push_master_to_main_rename(capture_subprocess):
    push_to_remote(
        "https://github.com/kanno321-create/shorts_studio.git",
        token="ghp_x",
        branch="main",
    )
    branch_call = capture_subprocess[0]
    assert branch_call["argv"] == ["git", "branch", "-M", "main"]
