"""Wave 1 REMOTE-01 — create_private_repo 201 + 422 + error paths.

Validates scripts.publisher.github_remote.create_private_repo against:

* 201 happy path — request payload + headers match the contract.
* 422 idempotent fall-through — GET /repos/{owner}/{name} succeeds.
* 422 fall-through failure — GET returns non-200 → GitHubRemoteError.
* Non-2xx non-422 response — raises GitHubRemoteError carrying status_code.

Dependency injection via the ``session=`` kwarg avoids any network I/O — no
MockGitHub needed at this layer (MockGitHub is reserved for higher-level
end-to-end wiring in Wave 5 smoke test).
"""
from __future__ import annotations

import pytest

from scripts.publisher.exceptions import GitHubRemoteError
from scripts.publisher.github_remote import GITHUB_API, create_private_repo


class _FakeResp:
    """Minimal stand-in for requests.Response used by _FakeSession."""

    def __init__(self, status_code: int, payload: dict | None = None, text: str = ""):
        self.status_code = status_code
        self._payload = payload or {}
        self.text = text

    def json(self) -> dict:
        return self._payload


class _FakeSession:
    """Records post/get calls + returns scripted _FakeResp objects."""

    def __init__(self) -> None:
        self.post_calls: list[dict] = []
        self.get_calls: list[dict] = []
        self.post_response: _FakeResp | None = None
        self.get_response: _FakeResp | None = None

    def post(self, url, headers, json, timeout):
        self.post_calls.append({"url": url, "headers": headers, "json": json})
        return self.post_response

    def get(self, url, headers, timeout):
        self.get_calls.append({"url": url, "headers": headers})
        return self.get_response


def test_create_repo_201_returns_payload():
    sess = _FakeSession()
    sess.post_response = _FakeResp(
        201,
        {
            "id": 1,
            "name": "shorts_studio",
            "private": True,
            "html_url": "https://github.com/kanno321-create/shorts_studio",
        },
    )
    result = create_private_repo("shorts_studio", "ghp_x", session=sess)
    assert result["name"] == "shorts_studio"
    assert result["private"] is True
    assert len(sess.post_calls) == 1
    call = sess.post_calls[0]
    assert call["url"] == f"{GITHUB_API}/user/repos"
    assert call["json"] == {
        "name": "shorts_studio",
        "private": True,
        "auto_init": False,
    }
    assert call["headers"]["Authorization"] == "Bearer ghp_x"
    assert call["headers"]["X-GitHub-Api-Version"] == "2022-11-28"


def test_create_repo_422_falls_through_to_get():
    sess = _FakeSession()
    sess.post_response = _FakeResp(422, text="name exists")
    sess.get_response = _FakeResp(200, {"id": 1, "name": "shorts_studio"})
    result = create_private_repo("shorts_studio", "ghp_x", session=sess)
    assert result["name"] == "shorts_studio"
    assert len(sess.get_calls) == 1
    assert sess.get_calls[0]["url"].endswith("/repos/kanno321-create/shorts_studio")


def test_create_repo_500_raises_github_remote_error():
    sess = _FakeSession()
    sess.post_response = _FakeResp(500, text="server error")
    with pytest.raises(GitHubRemoteError) as exc_info:
        create_private_repo("shorts_studio", "ghp_x", session=sess)
    assert exc_info.value.status_code == 500


def test_create_repo_422_then_404_raises():
    sess = _FakeSession()
    sess.post_response = _FakeResp(422)
    sess.get_response = _FakeResp(404, text="not found")
    with pytest.raises(GitHubRemoteError) as exc_info:
        create_private_repo("shorts_studio", "ghp_x", session=sess)
    assert exc_info.value.status_code == 404
