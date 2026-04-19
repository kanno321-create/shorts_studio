"""MockGitHub contract tests — Phase 7 Correction 2 default safety inheritance.

Exercises the REST + subprocess git double for Wave 1 (REMOTE-01..03):
- post_user_repos happy + 422 idempotent
- git_push happy + askpass-missing fault
- git_submodule_add happy + path-collision fault
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from mocks.github_mock import MockGitHub  # noqa: E402


def test_default_allow_fault_injection_is_false():
    m = MockGitHub()
    assert m._allow_fault_injection is False


def test_post_user_repos_happy_path():
    m = MockGitHub()
    r = m.post_user_repos(name="shorts_studio", private=True, token="ghp_x")
    assert r["private"] is True
    assert r["name"] == "shorts_studio"
    assert r["default_branch"] == "main"
    assert r["full_name"] == "kanno321-create/shorts_studio"
    assert "shorts_studio" in m._repos_created


def test_post_user_repos_requires_token():
    m = MockGitHub()
    with pytest.raises(ValueError):
        m.post_user_repos(name="x", private=True, token="")


def test_post_user_repos_422_on_duplicate_with_fault_injection():
    m = MockGitHub(allow_fault_injection=True)
    m.post_user_repos(name="shorts_studio", private=True, token="ghp_x")
    r2 = m.post_user_repos(name="shorts_studio", private=True, token="ghp_x")
    assert r2.get("status") == 422
    assert "already exists" in r2["message"]


def test_post_user_repos_duplicate_happy_path_without_fault_injection():
    # With fault injection off, second create still returns 201-shape (mock contract)
    m = MockGitHub()
    r1 = m.post_user_repos(name="shorts_studio", private=True, token="ghp_x")
    r2 = m.post_user_repos(name="shorts_studio", private=True, token="ghp_x")
    assert r1["default_branch"] == "main"
    assert r2["default_branch"] == "main"


def test_git_push_happy_path():
    m = MockGitHub()
    rc = m.git_push(
        "https://github.com/kanno321-create/shorts_studio.git",
        "main",
        env={"GIT_ASKPASS": "/tmp/ask.sh", "GITHUB_TOKEN": "ghp_x"},
    )
    assert rc == 0
    assert m._pushes == [("https://github.com/kanno321-create/shorts_studio.git", "main")]


def test_git_push_fault_on_missing_askpass():
    m = MockGitHub(allow_fault_injection=True)
    rc = m.git_push(
        "https://github.com/kanno321-create/shorts_studio.git", "main", env={}
    )
    assert rc == 128


def test_git_push_default_off_tolerates_missing_askpass():
    # With fault injection off, even without GIT_ASKPASS the push returns 0.
    m = MockGitHub()
    rc = m.git_push(
        "https://github.com/kanno321-create/shorts_studio.git", "main", env={}
    )
    assert rc == 0


def test_submodule_add_happy_path():
    m = MockGitHub()
    rc = m.git_submodule_add(
        "https://github.com/kanno321-create/naberal_harness", "harness", "abc123"
    )
    assert rc == 0
    assert m._submodules == [
        ("https://github.com/kanno321-create/naberal_harness", "harness", "abc123")
    ]


def test_submodule_add_path_collision_fault():
    m = MockGitHub(allow_fault_injection=True)
    m.git_submodule_add("https://github.com/x/y", "harness", "sha1")
    rc = m.git_submodule_add("https://github.com/x/z", "harness", "sha2")
    assert rc == 128
    # First entry still present; second was rejected.
    assert len(m._submodules) == 1
