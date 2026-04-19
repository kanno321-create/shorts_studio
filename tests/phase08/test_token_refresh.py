"""Wave 2 PUB-02 — Credentials.refresh roundtrip + disk persistence."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

import scripts.publisher.oauth as oauth


class _RefreshableCreds:
    """Fake creds simulating expired refreshable state."""

    def __init__(self):
        self.valid = False
        self.expired = True
        self.refresh_token = "r_refreshable"
        self.refresh_called = False
        self._serialized = '{"refresh_token":"r_refreshable","valid":false}'

    def refresh(self, request):
        self.refresh_called = True
        self.valid = True
        self.expired = False
        self._serialized = '{"refresh_token":"r_refreshable","valid":true,"refreshed":true}'

    def to_json(self):
        return self._serialized


class _NoRefreshTokenCreds:
    valid = False
    expired = True
    refresh_token = None

    def to_json(self):
        return '{"refresh_token":null}'


class _FakeFlow:
    def __init__(self, creds):
        self._creds = creds
        self.called = False

    def run_local_server(self, port):
        self.called = True
        return self._creds


def test_expired_creds_triggers_refresh(tmp_path, mock_client_secret, monkeypatch):
    tk_path = tmp_path / "youtube_token.json"
    tk_path.write_text("{}", encoding="utf-8")  # presence matters, content replaced by mock
    refreshable = _RefreshableCreds()
    monkeypatch.setattr(oauth.Credentials, "from_authorized_user_file",
                        lambda p, s: refreshable)
    monkeypatch.setattr(oauth.InstalledAppFlow, "from_client_secrets_file",
                        lambda *a, **kw: pytest.fail("Flow must not run when refresh possible"))
    result = oauth.get_credentials(client_secret_path=mock_client_secret, token_path=tk_path)
    assert refreshable.refresh_called is True
    assert result is refreshable


def test_refresh_writes_new_token_to_disk(tmp_path, mock_client_secret, monkeypatch):
    tk_path = tmp_path / "youtube_token.json"
    tk_path.write_text("stale", encoding="utf-8")
    refreshable = _RefreshableCreds()
    monkeypatch.setattr(oauth.Credentials, "from_authorized_user_file",
                        lambda p, s: refreshable)
    oauth.get_credentials(client_secret_path=mock_client_secret, token_path=tk_path)
    persisted = json.loads(tk_path.read_text(encoding="utf-8"))
    assert persisted.get("refreshed") is True, (
        f"Expected new token on disk after refresh, got {persisted}"
    )


def test_no_refresh_token_falls_through_to_flow(tmp_path, mock_client_secret, monkeypatch):
    tk_path = tmp_path / "youtube_token.json"
    tk_path.write_text("{}", encoding="utf-8")
    no_rt = _NoRefreshTokenCreds()
    monkeypatch.setattr(oauth.Credentials, "from_authorized_user_file",
                        lambda p, s: no_rt)
    new_creds_from_flow = _RefreshableCreds()
    new_creds_from_flow.valid = True
    fake_flow = _FakeFlow(new_creds_from_flow)
    monkeypatch.setattr(oauth.InstalledAppFlow, "from_client_secrets_file",
                        lambda cs, scopes: fake_flow)
    result = oauth.get_credentials(client_secret_path=mock_client_secret, token_path=tk_path)
    assert fake_flow.called is True
    assert result is new_creds_from_flow


def test_valid_creds_short_circuits(tmp_path, mock_client_secret, monkeypatch):
    tk_path = tmp_path / "youtube_token.json"
    tk_path.write_text("{}", encoding="utf-8")

    class _Valid:
        valid = True
        expired = False
        refresh_token = "r"

        def to_json(self):
            return '{}'

        def refresh(self, r):
            pytest.fail("refresh MUST NOT be called on valid creds")

    monkeypatch.setattr(oauth.Credentials, "from_authorized_user_file",
                        lambda p, s: _Valid())
    monkeypatch.setattr(oauth.InstalledAppFlow, "from_client_secrets_file",
                        lambda *a, **kw: pytest.fail("Flow MUST NOT run"))
    result = oauth.get_credentials(client_secret_path=mock_client_secret, token_path=tk_path)
    assert result.valid is True


def test_run_console_never_used_in_source():
    source = Path("scripts/publisher/oauth.py").read_text(encoding="utf-8")
    assert "run_console" not in source, (
        "Pitfall 1 anti-pattern: the deprecated OOB console flow is forbidden (2022-10 deprecation)"
    )
