"""Phase 8 Wave 1 REMOTE — GitHub REST + subprocess git CLI wrappers.

Satisfies REMOTE-01/02/03 per .planning/phases/08-remote-publishing-production-metadata/
08-CONTEXT.md (D-01 Fine-grained PAT + D-02 git submodule + D-03 main branch).

Three public functions:

* ``create_private_repo(name, token)`` — POST /user/repos (201 happy / 422
  idempotent / other → ``GitHubRemoteError``). REMOTE-01.
* ``push_to_remote(repo_url, token, branch="main")`` — ``git branch -M main`` +
  ``git remote add origin`` (idempotent) + ``git push -u origin main`` using a
  ``GIT_ASKPASS`` helper shell script. REMOTE-02.
* ``add_harness_submodule(harness_url, commit_sha, path="harness")`` — ``git
  submodule add`` + ``git checkout <sha>`` + ``git add .gitmodules <path>``.
  REMOTE-03.

Pitfall 2 avoidance (.planning/phases/08-remote-publishing-production-metadata/
08-RESEARCH.md §Pitfall 2): the PAT token is **never** embedded in the remote
URL. Instead ``GIT_ASKPASS`` + ``GITHUB_TOKEN`` env-var pair is passed to the
``git push`` subprocess so git invokes the helper script to retrieve credentials
without ever writing them to ``.git/config``.

Pitfall 10 (path collision) is surfaced by letting ``subprocess.CalledProcessError``
propagate out of ``add_harness_submodule`` so callers can apply CD-03 discretion
(sha256-compare existing ``harness/`` vs upstream → delete + retry, or ask the
user).
"""
from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Any

import requests

from scripts.publisher.exceptions import GitHubRemoteError

GITHUB_API = "https://api.github.com"
GITHUB_OWNER_DEFAULT = "kanno321-create"
ASKPASS_SCRIPT = Path(__file__).resolve().parent / "_git_askpass.sh"


def create_private_repo(
    name: str,
    token: str,
    *,
    session: Any | None = None,
) -> dict[str, Any]:
    """POST /user/repos to create a private repository.

    REMOTE-01. Idempotent on 422 (name-taken): falls through to GET
    /repos/{owner}/{name} and returns the existing repo body.

    Parameters
    ----------
    name : str
        Repository name (e.g. ``"shorts_studio"``).
    token : str
        Fine-grained Personal Access Token with ``contents:write`` +
        ``metadata:read`` scopes.
    session : optional
        Injectable REST client exposing ``.post(url, headers, json, timeout)``
        and ``.get(url, headers, timeout)`` — defaults to the ``requests``
        module for production, overridden by tests for deterministic fixtures.

    Returns
    -------
    dict
        The GitHub repo payload (201 happy) or the existing repo payload (422
        idempotent fall-through).

    Raises
    ------
    GitHubRemoteError
        On any non-2xx non-422 response, or on 422 fall-through returning
        non-200 from GET /repos/{owner}/{name}.
    """
    sess = session or requests
    resp = sess.post(
        f"{GITHUB_API}/user/repos",
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
        json={"name": name, "private": True, "auto_init": False},
        timeout=30,
    )
    if resp.status_code == 201:
        return resp.json()
    if resp.status_code == 422:
        owner = os.environ.get("GITHUB_USER", GITHUB_OWNER_DEFAULT)
        existing = sess.get(
            f"{GITHUB_API}/repos/{owner}/{name}",
            headers={"Authorization": f"Bearer {token}"},
            timeout=30,
        )
        if existing.status_code == 200:
            return existing.json()
        raise GitHubRemoteError(existing.status_code, existing.text)
    raise GitHubRemoteError(resp.status_code, resp.text)


def push_to_remote(
    repo_url: str,
    token: str,
    *,
    branch: str = "main",
    cwd: Path | str | None = None,
) -> None:
    """Rename the current branch, register the origin remote, and push.

    REMOTE-02. Sequence:

    1. ``git branch -M <branch>`` (master → main rename per CONTEXT D-03)
    2. ``git remote add origin <repo_url>`` — ``check=False`` for idempotence
       (``fatal: remote origin already exists`` is fine on re-runs).
    3. ``git push -u origin <branch>`` — ``GIT_ASKPASS`` + ``GITHUB_TOKEN``
       env-vars propagated so git calls the helper script for credentials
       WITHOUT embedding the token in the URL (Pitfall 2 avoidance).

    Parameters
    ----------
    repo_url : str
        HTTPS clone URL of the remote, e.g.
        ``https://github.com/kanno321-create/shorts_studio.git``.
        Must NOT contain embedded credentials (``user@host`` form); those are
        rejected with ``GitHubRemoteError`` before any subprocess runs.
    token : str
        Fine-grained PAT passed to the ``GIT_ASKPASS`` helper via the
        ``GITHUB_TOKEN`` env-var.
    branch : str, default ``"main"``
        Target branch name.
    cwd : optional
        Working directory for subprocess calls; ``None`` uses the current
        working directory.

    Raises
    ------
    GitHubRemoteError
        When ``repo_url`` embeds credentials (Pitfall 2 guard).
    subprocess.CalledProcessError
        When ``git branch`` or ``git push`` fail (propagates).
    """
    # Pitfall 2 guard: reject URLs where the host component contains '@'
    # (classic "https://<token>@github.com/..." anti-pattern).
    if "@" in repo_url.split("://", 1)[-1].split("/", 1)[0]:
        raise GitHubRemoteError(
            -1,
            f"repo_url must not embed credentials (Pitfall 2): {repo_url}",
        )
    env = os.environ.copy()
    env["GIT_ASKPASS"] = str(ASKPASS_SCRIPT.resolve())
    env["GITHUB_TOKEN"] = token
    subprocess.run(["git", "branch", "-M", branch], check=True, cwd=cwd, env=env)
    # git remote add may fail if origin already exists — idempotent on re-run.
    subprocess.run(
        ["git", "remote", "add", "origin", repo_url],
        check=False,
        cwd=cwd,
        env=env,
    )
    subprocess.run(
        ["git", "push", "-u", "origin", branch],
        check=True,
        cwd=cwd,
        env=env,
    )


def add_harness_submodule(
    harness_url: str,
    commit_sha: str,
    *,
    path: str = "harness",
    cwd: Path | str | None = None,
) -> None:
    """Add the naberal_harness repository as a SHA-pinned git submodule.

    REMOTE-03. Sequence:

    1. ``git submodule add <harness_url> <path>`` — creates ``.gitmodules``
       entry + registers the submodule in ``.git/config``.
    2. ``git checkout <commit_sha>`` executed inside ``<path>`` — pins the
       submodule to the exact SHA (CONTEXT D-02 v1.0.1 SHA lock rationale).
    3. ``git add .gitmodules <path>`` — stages both the metadata file and the
       submodule pointer so the parent commit captures the pin.

    Parameters
    ----------
    harness_url : str
        HTTPS clone URL of the harness repo.
    commit_sha : str
        Full commit SHA (40 chars) or short SHA (≥7 chars) to pin. Passed
        verbatim to ``git checkout``.
    path : str, default ``"harness"``
        Local path inside the parent repo where the submodule is cloned.
        Per CONTEXT D-02: ``studios/shorts/harness/`` (flat, not
        ``../../harness/`` — clone portability over symlink relative refs).
    cwd : optional
        Parent-repo working directory for the outer subprocess calls.

    Raises
    ------
    subprocess.CalledProcessError
        Propagated on any step failure. Pitfall 10 (pre-existing ``harness/``
        in index) surfaces as returncode 128 — callers apply CD-03 discretion.
    """
    subprocess.run(
        ["git", "submodule", "add", harness_url, path],
        check=True,
        cwd=cwd,
    )
    subprocess.run(
        ["git", "checkout", commit_sha],
        check=True,
        cwd=str(Path(cwd or ".") / path),
    )
    subprocess.run(
        ["git", "add", ".gitmodules", path],
        check=True,
        cwd=cwd,
    )


__all__ = [
    "GITHUB_API",
    "GITHUB_OWNER_DEFAULT",
    "ASKPASS_SCRIPT",
    "create_private_repo",
    "push_to_remote",
    "add_harness_submodule",
]
