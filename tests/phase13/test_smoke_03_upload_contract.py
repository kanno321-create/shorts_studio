"""Phase 13 Wave 2 SMOKE-03 — YouTube unlisted 업로드 + cleanup + public ValueError 방어.

Tier 1 (always-run, no API)
---------------------------
1. ``run_smoke_test(privacy='public')`` → ``ValueError`` (D-11 HARDCODED invariant)
2. ``run_smoke_test(privacy='private')`` → ``ValueError`` (choices-locked 재확인)
3. ``inspect.signature(run_smoke_test)`` default = ``'unlisted'`` regression guard
4. ``scripts/publisher/smoke_test`` 모듈 import 안전 + ``SMOKE_VIDEO_PATH`` 계약 보존

Tier 2 (``@pytest.mark.live_smoke``, opt-in ``--run-live``)
-----------------------------------------------------------
5. 실 YouTube Data API v3 경로로 videos.insert → 30s polling → videos.delete
   cleanup 전 구간 round-trip + anchor_upload_evidence 와의 통합 증명.

금기 준수
=========
- 금기 #5 공식 API only — 비공식 자동화 문자열 grep 결과 0 이 본 파일 전체에서 보장되어야 함.
- 금기 #8 일일 업로드 금지 — ``cleanup=True`` HARDCODED + ``SHORTS_PUBLISH_LOCK_PATH``
  tmp override (conftest ``tmp_evidence_dir`` fixture) 경유로 48h+ 카운터 소진 차단.
"""
from __future__ import annotations

import inspect
from datetime import datetime

import pytest


# --- Tier 1 tests (always-run, no API) --------------------------------------


def test_smoke_03_privacy_public_raises_value_error():
    """D-11 HARDCODED invariant: privacy='public' 호출 시 network 도달 전 ValueError.

    smoke_test.py 는 argument validation 단계 (함수 진입 직후) 에서 raise 하므로
    googleapiclient 호출 0회, 과금 0 USD 보장. 대표님 비용 방어선의 일부.
    """
    from scripts.publisher.smoke_test import run_smoke_test

    with pytest.raises(ValueError) as exc_info:
        run_smoke_test(privacy="public", cleanup=True)
    assert "unlisted" in str(exc_info.value).lower(), (
        "SMOKE-03: ValueError 메시지에 'unlisted' 문구 누락 대표님"
    )


def test_smoke_03_privacy_private_raises_value_error():
    """D-11 choices-locked 재확인: privacy='private' 또한 ValueError 대상."""
    from scripts.publisher.smoke_test import run_smoke_test

    with pytest.raises(ValueError):
        run_smoke_test(privacy="private", cleanup=True)


def test_smoke_03_default_privacy_is_unlisted_hardcoded():
    """regression guard: run_smoke_test default privacy = 'unlisted' 불변."""
    from scripts.publisher.smoke_test import run_smoke_test

    sig = inspect.signature(run_smoke_test)
    privacy_param = sig.parameters.get("privacy")
    assert privacy_param is not None, (
        "SMOKE-03: run_smoke_test signature 에 'privacy' parameter 부재 대표님"
    )
    assert privacy_param.default == "unlisted", (
        f"SMOKE-03: default 가 'unlisted' 가 아님 대표님 ({privacy_param.default!r})"
    )
    # cleanup default 도 True — 금기 #8 (일일 업로드 금지) 사전 방어.
    cleanup_param = sig.parameters.get("cleanup")
    assert cleanup_param is not None, "SMOKE-03: 'cleanup' parameter 부재"
    assert cleanup_param.default is True, "SMOKE-03: cleanup default 가 True 가 아님"


def test_smoke_03_module_import_is_safe_and_contract_stable():
    """smoke_test.py 모듈 import 가 side-effect 없이 성공 + 주요 계약 보존.

    - ``SMOKE_VIDEO_PATH`` 공개 constant 존재.
    - ``PROCESSING_WAIT_SECONDS`` = 30 (Phase 8 ship 고정값 — 금기 #2 연장 금지).
    """
    from scripts.publisher import smoke_test as smoke_mod

    assert hasattr(smoke_mod, "SMOKE_VIDEO_PATH"), "SMOKE_VIDEO_PATH constant 부재"
    assert hasattr(smoke_mod, "PROCESSING_WAIT_SECONDS"), "PROCESSING_WAIT_SECONDS 부재"
    assert smoke_mod.PROCESSING_WAIT_SECONDS == 30, (
        "Phase 8 ship 계약 — 30s timeout 유지 대표님 (연장 시 금기 #2)"
    )
    assert hasattr(smoke_mod, "run_smoke_test"), "run_smoke_test export 부재"


# --- Tier 2 live tests (opt-in via --run-live) ------------------------------


@pytest.mark.live_smoke
def test_smoke_03_real_youtube_unlisted_upload_and_cleanup(tmp_evidence_dir):
    """실 YouTube Data API v3 1회 업로드 + readback + cleanup 통합 test.

    순서 재구성:
        1. get_credentials() + build('youtube', 'v3')
        2. _build_smoke_plan() — privacy=unlisted HARDCODED
        3. videos.insert(media_body=SMOKE_VIDEO_PATH) → video_id
        4. _wait_for_processing(30s budget)
        5. anchor_upload_evidence(...) — videos.list readback
        6. _delete_video(video_id) — cleanup (try/finally 보장)

    순서 이유: run_smoke_test 는 cleanup=True 시 videos.delete 수행 **후**
    반환 — 반환 후에는 anchor_upload_evidence 의 videos.list 가 empty 를
    받아 RuntimeError 를 발생시킴. 따라서 Tier 2 는 각 step 을 수동 조립
    대표님.
    """
    # Lazy imports — Tier 1 collection 시 googleapiclient 의존성 회피.
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload

    from scripts.publisher.oauth import get_credentials
    from scripts.publisher.production_metadata import (
        PIPELINE_VERSION,
        compute_checksum,
        inject_into_description,
    )
    from scripts.publisher.smoke_test import (
        SMOKE_VIDEO_PATH,
        _build_smoke_plan,
        _delete_video,
        _wait_for_processing,
    )
    from scripts.smoke.upload_evidence import anchor_upload_evidence

    credentials = get_credentials()
    youtube = build("youtube", "v3", credentials=credentials)
    plan = _build_smoke_plan()

    # description 에 production_metadata HTML comment 주입 (readback 검증 위해).
    meta = {
        "script_seed": plan["production_metadata"]["script_seed"],
        "assets_origin": plan["production_metadata"]["assets_origin"],
        "pipeline_version": PIPELINE_VERSION,
        "checksum": compute_checksum(SMOKE_VIDEO_PATH),
    }
    plan["snippet"]["description"] = inject_into_description(
        plan["snippet"]["description"],
        meta,
    )

    insert_body = {"snippet": plan["snippet"], "status": plan["status"]}
    media = MediaFileUpload(str(SMOKE_VIDEO_PATH), resumable=False)
    insert_resp = youtube.videos().insert(
        part="snippet,status",
        body=insert_body,
        media_body=media,
    ).execute()
    video_id = insert_resp["id"]
    assert video_id, "SMOKE-03 Tier 2: videos.insert 결과 video_id 비어있음"

    try:
        _wait_for_processing(youtube, video_id)
        sid = datetime.now().strftime("%Y%m%d_%H%M%S")
        evidence = anchor_upload_evidence(
            youtube,
            video_id,
            sid,
            evidence_dir=tmp_evidence_dir,
        )
        assert evidence["video_id"] == video_id, (
            "SMOKE-03 Tier 2: evidence.video_id != insert.video_id 대표님"
        )
        assert (tmp_evidence_dir / f"smoke_upload_{sid}.json").exists(), (
            "SMOKE-03 Tier 2: evidence JSON 파일 write 실패 대표님"
        )
    finally:
        # cleanup — try/finally 보장 (pytest framework 가 test 결과 관계없이 수행).
        # SmokeTestCleanupFailure 예외는 상위로 전파 — 대표님 Studio 수동 삭제 필요.
        _delete_video(youtube, video_id)
