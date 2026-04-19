"""Wave 2 PUB-02 — InstalledAppFlow bootstrap path.

Tests monkeypatch Credentials.from_authorized_user_file + InstalledAppFlow.from_client_secrets_file
to avoid any real Google library dependency at test time (still imports oauth.py successfully).
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

import scripts.publisher.oauth as oauth


class _FakeCreds:
    def __init__(self, *, valid=True, expired=False, refresh_token="r1",
                 token_json='{"refresh_token":"r1","valid":true}'):
        self.valid = valid
        self.expired = expired
        self.refresh_token = refresh_token
        self._token_json = token_json

    def to_json(self):
        return self._token_json

    def refresh(self, request):
        self.valid = True
        self.expired = False


class _FakeFlow:
    def __init__(self, creds: _FakeCreds):
        self._creds = creds
        self.run_local_server_called_with_port = None

    def run_local_server(self, port):
        self.run_local_server_called_with_port = port
        return self._creds


def test_bootstrap_when_token_missing(tmp_path, mock_client_secret, monkeypatch):
    tk_path = tmp_path / "youtube_token.json"
    assert not tk_path.exists()
    fake_creds = _FakeCreds()
    fake_flow = _FakeFlow(fake_creds)
    monkeypatch.setattr(oauth.InstalledAppFlow, "from_client_secrets_file",
                        lambda cs, scopes: fake_flow)
    result = oauth.get_credentials(client_secret_path=mock_client_secret, token_path=tk_path)
    assert result is fake_creds
    assert fake_flow.run_local_server_called_with_port == 0, (
        "Pitfall 1 anchor: port=0 MUST be passed (OS-assigned random port)"
    )
    assert tk_path.exists()
    assert json.loads(tk_path.read_text(encoding="utf-8"))["refresh_token"] == "r1"


def test_bootstrap_creates_parent_directory(tmp_path, mock_client_secret, monkeypatch):
    nested = tmp_path / "deep" / "nested" / "token.json"
    assert not nested.parent.exists()
    fake_flow = _FakeFlow(_FakeCreds())
    monkeypatch.setattr(oauth.InstalledAppFlow, "from_client_secrets_file",
                        lambda cs, scopes: fake_flow)
    oauth.get_credentials(client_secret_path=mock_client_secret, token_path=nested)
    assert nested.parent.is_dir()
    assert nested.exists()


def test_scopes_are_exactly_two_in_order():
    assert oauth.SCOPES == [
        "https://www.googleapis.com/auth/youtube.upload",
        "https://www.googleapis.com/auth/youtube.force-ssl",
    ]


def test_client_secret_path_default():
    assert oauth.CLIENT_SECRET_PATH == Path("config/client_secret.json")


def test_token_path_default():
    assert oauth.TOKEN_PATH == Path("config/youtube_token.json")


def test_load_existing_valid_token_skips_flow(tmp_path, mock_client_secret, monkeypatch):
    tk_path = tmp_path / "youtube_token.json"
    tk_path.write_text('{"refresh_token":"r1","valid":true}', encoding="utf-8")
    fake_valid_creds = _FakeCreds(valid=True, expired=False)
    monkeypatch.setattr(oauth.Credentials, "from_authorized_user_file",
                        lambda p, s: fake_valid_creds)
    # InstalledAppFlow must NOT be called — install a sentinel raising on call.
    monkeypatch.setattr(oauth.InstalledAppFlow, "from_client_secrets_file",
                        lambda *a, **kw: pytest.fail("Flow must not run for valid token"))
    result = oauth.get_credentials(client_secret_path=mock_client_secret, token_path=tk_path)
    assert result is fake_valid_creds
