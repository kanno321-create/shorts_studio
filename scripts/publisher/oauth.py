"""scripts.publisher.oauth — OAuth 2.0 Installed App flow for YouTube Data API v3.

Per CONTEXT D-04: Installed Application (desktop) + refresh token stored in
config/youtube_token.json. Service Account is unsupported for YouTube channel upload
(Google official policy). flask/web flow is over-engineered for single-user desktop.

Per RESEARCH Pitfall 1: run_local_server(port=0) uses OS-assigned random port;
Google Desktop OAuth 2.0 client auto-accepts localhost loopback at any port.
Do NOT register fixed redirect URI in Cloud Console — leave Authorized Redirect URIs
empty or set to exactly 'http://localhost'.

Scopes (exactly 3 as of Phase 10):
    - youtube.upload            → videos.insert + thumbnails.set
    - youtube.force-ssl         → commentThreads.insert (pin comment automation)
    - yt-analytics.readonly     → youtubeAnalytics.reports.query (Phase 10 KPI-01/02 daily fetch)

Test strategy: downstream tests monkeypatch Credentials.from_authorized_user_file
+ InstalledAppFlow.from_client_secrets_file to avoid any real network/browser call.
"""
from __future__ import annotations

from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow


SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",          # videos.insert + thumbnails.set
    "https://www.googleapis.com/auth/youtube.force-ssl",       # commentThreads.insert
    "https://www.googleapis.com/auth/yt-analytics.readonly",   # Phase 10 KPI-01/02 daily fetch (analytics v2)
]

CLIENT_SECRET_PATH = Path("config/client_secret.json")
TOKEN_PATH = Path("config/youtube_token.json")


def get_credentials(
    *,
    client_secret_path: Path | None = None,
    token_path: Path | None = None,
) -> Credentials:
    """Load refresh token from disk, refresh if expired, else bootstrap via InstalledAppFlow.

    Keyword-only path overrides enable test injection of mock_client_secret + tmp_path
    tokens without touching the module-level constants.

    Behavior:
        1. If ``token_path`` file exists → load via ``Credentials.from_authorized_user_file``.
        2. If the loaded creds are not valid:
            a. If expired + refresh_token present → ``creds.refresh(Request())``.
            b. Else → ``InstalledAppFlow.from_client_secrets_file(...).run_local_server(port=0)``.
            c. Ensure parent directory + persist ``creds.to_json()`` to ``token_path``.
        3. Return creds.

    Pitfall 1 (deprecated 2022-10): the legacy OOB console flow is NEVER called.
    Google deprecated the out-of-band flow in 2022-10; only ``run_local_server``
    remains for installed-app desktop authentication.
    """
    cs_path = client_secret_path or CLIENT_SECRET_PATH
    tk_path = token_path or TOKEN_PATH

    creds: Credentials | None = None
    if tk_path.exists():
        creds = Credentials.from_authorized_user_file(str(tk_path), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(str(cs_path), SCOPES)
            creds = flow.run_local_server(port=0)
        tk_path.parent.mkdir(parents=True, exist_ok=True)
        tk_path.write_text(creds.to_json(), encoding="utf-8")

    return creds


__all__ = [
    "SCOPES",
    "CLIENT_SECRET_PATH",
    "TOKEN_PATH",
    "get_credentials",
]
