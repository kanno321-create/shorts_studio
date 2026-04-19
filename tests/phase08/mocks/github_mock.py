"""Deterministic GitHub REST + subprocess git double for Phase 8.

Mirrors the surface used by scripts/publisher/github_remote.py (Wave 1):

* post_user_repos(name, private, token)   POST /user/repos (201 | 422 idempotent)
* git_push(remote_url, branch, env)       subprocess.run(["git","push",...]).returncode
* git_submodule_add(url, path, commit_sha) subprocess.run(["git","submodule","add",...]).returncode

Per CONTEXT D-10 + Phase 7 Correction 2 default safety inheritance:
``allow_fault_injection`` defaults to **False**.

Fault-injection opt-ins modelled here:
- post_user_repos duplicate-name on same instance → 422 (Research Example B)
- git_push without GIT_ASKPASS in env → 128 (no credential helper)
- git_submodule_add with colliding path → 128 (Pitfall 10 path collision)
"""
from __future__ import annotations

from typing import Any


class MockGitHub:
    """Mock for the GitHub REST + subprocess git surface consumed by Wave 1.

    Happy-path returns always succeed regardless of fault injection setting —
    fault injection only activates when both ``allow_fault_injection=True`` AND
    the per-method trigger condition is met (duplicate name, missing askpass,
    colliding submodule path).
    """

    def __init__(self, *, allow_fault_injection: bool = False) -> None:
        self._allow_fault_injection = allow_fault_injection
        self._counter: int = 0
        self._repos_created: list[str] = []
        self._pushes: list[tuple[str, str]] = []
        self._submodules: list[tuple[str, str, str]] = []

    # REST ------------------------------------------------------------------
    def post_user_repos(self, name: str, private: bool, token: str) -> dict[str, Any]:
        """Simulate POST https://api.github.com/user/repos.

        Happy path: returns 201 body; appends name to _repos_created.
        Fault: if allow_fault_injection is True AND name already created on this
        instance, returns a 422 body (repo-already-exists) matching the Research
        Example B idempotent contract.
        """
        if not token:
            # Missing token is a programming error regardless of fault flag —
            # surface immediately so callers catch auth misconfiguration in tests.
            raise ValueError("token is required for post_user_repos")

        if self._allow_fault_injection and name in self._repos_created:
            return {
                "message": f"Repository creation failed: name '{name}' already exists on this account",
                "status": 422,
                "errors": [
                    {
                        "resource": "Repository",
                        "code": "custom",
                        "field": "name",
                        "message": "name already exists on this account",
                    }
                ],
            }

        self._counter += 1
        self._repos_created.append(name)
        return {
            "id": self._counter,
            "name": name,
            "full_name": f"kanno321-create/{name}",
            "private": private,
            "html_url": f"https://github.com/kanno321-create/{name}",
            "clone_url": f"https://github.com/kanno321-create/{name}.git",
            "default_branch": "main",
        }

    # subprocess git --------------------------------------------------------
    def git_push(self, remote_url: str, branch: str, env: dict[str, str]) -> int:
        """Simulate subprocess.run(["git", "push", "-u", remote_url, branch], env=env).

        Happy path: returns 0 + appends (remote_url, branch) to _pushes.
        Fault: when allow_fault_injection=True AND env.get("GIT_ASKPASS") is None,
        returns 128 (no credential helper → git prompts and fails in non-tty env).
        """
        if self._allow_fault_injection and env.get("GIT_ASKPASS") is None:
            return 128
        self._pushes.append((remote_url, branch))
        return 0

    def git_submodule_add(self, url: str, path: str, commit_sha: str) -> int:
        """Simulate subprocess.run(["git", "submodule", "add", url, path]).

        Happy path: returns 0 + appends (url, path, commit_sha) to _submodules.
        Fault: when allow_fault_injection=True AND path already registered on
        this instance, returns 128 (Pitfall 10 — path collision).
        """
        if self._allow_fault_injection and any(
            existing_path == path for (_url, existing_path, _sha) in self._submodules
        ):
            return 128
        self._submodules.append((url, path, commit_sha))
        return 0


__all__ = ["MockGitHub"]
