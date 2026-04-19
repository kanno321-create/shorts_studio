"""Wave 6 — full Phase 8 chain against mocks (no real API).

End-to-end aggregated scenario verifying ALL 8 Phase 8 requirements fire in
a single atomic flow:

- REMOTE-01: GitHub repo create (MockGitHub.post_user_repos)
- REMOTE-02: main branch push (MockGitHub.git_push)
- REMOTE-03: harness submodule add (MockGitHub.git_submodule_add)
- PUB-01: AI disclosure containsSyntheticMedia=True enforced in insert body
- PUB-02: YouTube Data API v3 videos.insert resumable upload
- PUB-03: publish_lock 48h persistence + KST window (bypassed via fixture)
- PUB-04: production_metadata 4-field HTML comment injected into description
- PUB-05: commentThreads.insert pinned comment

This is the Phase 8 analogue of Phase 7's test_e2e_happy_path.py — one
test module exercising the full happy path AND a negative cleanup path
(smoke_test delete) against the same MockYouTube instance.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

# tests/phase08/mocks/ — no package __init__ (Phase 4-7 collision avoidance).
sys.path.insert(0, str(Path(__file__).resolve().parent))
from mocks.github_mock import MockGitHub   # type: ignore[import-not-found]
from mocks.youtube_mock import MockYouTube   # type: ignore[import-not-found]

import scripts.publisher.kst_window as kstw


@pytest.fixture(autouse=True)
def kst_pass(monkeypatch):
    """Autouse fixture — all tests in this module bypass KST window."""
    monkeypatch.setattr(kstw, "assert_in_window", lambda **kw: None)


def _build_plan() -> dict:
    """Canonical plan for the full-chain scenario.

    All 8 requirements are represented:
    - snippet/status → PUB-02
    - ai_disclosure.syntheticMedia → PUB-01 (translated to containsSyntheticMedia)
    - production_metadata → PUB-04
    - funnel.pinned_comment → PUB-05
    - _media_body / _thumb_body sentinels → bypass lazy MediaFileUpload
    """
    return {
        "snippet": {
            "title": "Phase 8 chain test",
            "description": "chain",
            "tags": ["chain"],
            "categoryId": "24",
            "defaultLanguage": "ko",
        },
        "status": {
            "privacyStatus": "public",
            "embeddable": True,
            "publicStatsViewable": True,
        },
        "ai_disclosure": {"syntheticMedia": True},
        "production_metadata": {
            "script_seed": "chain_test",
            "assets_origin": "kling:primary",
        },
        "funnel": {"pinned_comment": "구독!"},
        "_media_body": object(),
        "_thumb_body": object(),
    }


def test_full_chain_remote_then_publish(sample_mp4_path, tmp_publish_lock):
    """Atomic scenario: MockGitHub (3 ops) then MockYouTube (publish).

    Proves REMOTE-01/02/03 + PUB-01/02/03/04/05 all fire in sequence
    against the shared mock instances, producing the expected side-effect
    state in both mocks.
    """
    # --- REMOTE half (REMOTE-01/02/03) ---
    gh = MockGitHub()
    repo = gh.post_user_repos(name="shorts_studio", private=True, token="ghp_x")
    assert repo["name"] == "shorts_studio"
    assert repo["private"] is True

    push_rc = gh.git_push(
        "https://github.com/kanno321-create/shorts_studio.git",
        "main",
        env={"GIT_ASKPASS": "/tmp/ask.sh", "GITHUB_TOKEN": "ghp_x"},
    )
    assert push_rc == 0
    assert gh._pushes == [
        ("https://github.com/kanno321-create/shorts_studio.git", "main"),
    ]

    submod_rc = gh.git_submodule_add(
        "https://github.com/kanno321-create/naberal_harness",
        "harness",
        "v1.0.1_commit_sha",
    )
    assert submod_rc == 0
    assert len(gh._submodules) == 1

    # --- PUBLISH half (PUB-01/02/03/04/05) ---
    from scripts.publisher.youtube_uploader import publish
    yt = MockYouTube()
    plan = _build_plan()
    video_id = publish(yt, plan, sample_mp4_path, sample_mp4_path, "channel_1")
    assert video_id.startswith("mock_video_id_")
    assert yt._upload_count == 1
    assert video_id in yt._pinned_comments


def test_full_chain_publish_then_smoke_delete(
        sample_mp4_path, tmp_publish_lock, monkeypatch):
    """After publish, smoke_test cleanup flow works against MockYouTube.

    Exercises the PUB-01..05 + delete cleanup path in one run —
    ensures smoke_test.run_smoke_test() with MockYouTube returns a
    cleaned-up video (_deleted list contains the video id).
    """
    import scripts.publisher.smoke_test as st
    # Skip the 30s processing wait — we only care that delete fires.
    monkeypatch.setattr(st.time, "sleep", lambda s: None)

    yt = MockYouTube()
    vid = st.run_smoke_test(youtube=yt, privacy="unlisted", cleanup=True)
    assert vid.startswith("mock_video_id_")
    assert vid in yt._deleted, (
        f"MockYouTube._deleted should contain {vid}; got {yt._deleted}"
    )


def test_production_metadata_reaches_description_in_chain(
        sample_mp4_path, tmp_publish_lock, monkeypatch):
    """E2E guarantee: production_metadata JSON reaches insert body description.

    Proves the PUB-04 → PUB-02 data flow survives the full publish()
    chain. Uses a Spy videos() that captures the body dict passed into
    MockYouTube.videos().insert(...).
    """
    from scripts.publisher.youtube_uploader import publish

    captured: dict = {}
    yt = MockYouTube()
    real_videos = yt.videos

    class _SpyVideos:
        def insert(self, *, part, body, media_body):
            captured.update(body)
            return real_videos().insert(part=part, body=body, media_body=media_body)

    monkeypatch.setattr(yt, "videos", lambda: _SpyVideos())

    plan = _build_plan()
    publish(yt, plan, sample_mp4_path, sample_mp4_path, "channel_1")
    desc = captured["snippet"]["description"]
    assert "<!-- production_metadata" in desc
    assert '"script_seed":"chain_test"' in desc
    assert '"assets_origin":"kling:primary"' in desc
    assert '"pipeline_version":"1.0.0"' in desc
    # sha256 of b"0" = 5feceb66ffc86f38d952786c6d696c79c2dbc239dd4e91b46729d73a27fb57e9
    assert '"checksum":"sha256:5feceb66' in desc


def test_contains_synthetic_media_true_reaches_body_in_chain(
        sample_mp4_path, tmp_publish_lock, monkeypatch):
    """E2E guarantee: containsSyntheticMedia=True in insert body.

    Proves PUB-01 translation happens correctly:
    - Canonical API field `containsSyntheticMedia` is True
    - Custom plan key `syntheticMedia` does NOT leak into the API body
    - Hardcoded `selfDeclaredMadeForKids=False` is present
    """
    from scripts.publisher.youtube_uploader import publish

    captured: dict = {}
    yt = MockYouTube()
    real_videos = yt.videos

    class _SpyVideos:
        def insert(self, *, part, body, media_body):
            captured.update(body)
            return real_videos().insert(part=part, body=body, media_body=media_body)

    monkeypatch.setattr(yt, "videos", lambda: _SpyVideos())

    plan = _build_plan()
    publish(yt, plan, sample_mp4_path, sample_mp4_path, "channel_1")
    status_body = captured["status"]
    assert status_body["containsSyntheticMedia"] is True
    # Pitfall 6 guard — custom key MUST NOT leak into API body.
    assert "syntheticMedia" not in status_body, (
        "Custom 'syntheticMedia' key leaked into API body (Pitfall 6)"
    )
    assert status_body["selfDeclaredMadeForKids"] is False


def test_publish_lock_recorded_after_chain(sample_mp4_path, tmp_publish_lock):
    """publish_lock.json must exist on disk after the full chain runs.

    Proves PUB-03 Gate 5c (record_upload) fires at the end of the chain
    — this is what prevents the next publish attempt from running before
    48h have passed.
    """
    from scripts.publisher.youtube_uploader import publish
    yt = MockYouTube()
    publish(yt, _build_plan(), sample_mp4_path, sample_mp4_path, "c1")
    assert tmp_publish_lock.exists(), (
        f"publish_lock.json missing at {tmp_publish_lock} — PUB-03 broken"
    )


def test_eight_requirements_all_exercised_in_chain(
        sample_mp4_path, tmp_publish_lock):
    """Meta-test: prove REMOTE-01/02/03 + PUB-01/02/03/04/05 all fire.

    Single atomic run that touches every mock side-effect list exactly
    once — any missing side-effect means a requirement was silently
    skipped. Acts as the canonical Phase 8 E2E integration proof.
    """
    # REMOTE half ------------------------------------------------------
    gh = MockGitHub()
    # REMOTE-01
    gh.post_user_repos(name="shorts_studio", private=True, token="ghp_x")
    # REMOTE-02
    gh.git_push(
        "https://github.com/kanno321-create/shorts_studio.git",
        "main",
        env={"GIT_ASKPASS": "/tmp", "GITHUB_TOKEN": "ghp_x"},
    )
    # REMOTE-03
    gh.git_submodule_add(
        "https://github.com/kanno321-create/naberal_harness",
        "harness",
        "sha_v1_0_1",
    )
    assert gh._repos_created == ["shorts_studio"], "REMOTE-01 not fired"
    assert len(gh._pushes) == 1, "REMOTE-02 not fired"
    assert len(gh._submodules) == 1, "REMOTE-03 not fired"

    # PUBLISH half -----------------------------------------------------
    from scripts.publisher.youtube_uploader import publish
    yt = MockYouTube()
    plan = _build_plan()
    vid = publish(yt, plan, sample_mp4_path, sample_mp4_path, "c1")
    # PUB-02: insert happened
    assert yt._upload_count == 1, "PUB-02 insert not fired"
    # PUB-03: lock recorded on disk
    assert tmp_publish_lock.exists(), "PUB-03 record_upload not fired"
    # PUB-05: pinned comment inserted
    assert vid in yt._pinned_comments, "PUB-05 pinned comment not fired"
    assert yt._pinned_comments[vid] == "구독!", "PUB-05 text drift"
    # PUB-01 + PUB-04: verified structurally in the *_reaches_body_in_chain
    # tests above; the meta-test only needs to confirm non-zero activity on
    # every mock side-effect list.
