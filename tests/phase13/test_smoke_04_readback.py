"""Phase 13 Wave 2 SMOKE-04 — production_metadata HTML comment readback 4 필드.

Tier 1 (always-run, no API)
---------------------------
1. ``PRODUCTION_METADATA_REGEX`` 가 valid HTML comment 매칭 + 4 필드 JSON 추출
2. regex flags 에 ``re.DOTALL`` 필수 (multi-line JSON payload)
3. HTML comment 부재 description → regex match is None
4. sample_smoke_upload.json golden fixture — 4 필드 all present + pipeline_version == "1.0.0"

Tier 2 (``@pytest.mark.live_smoke``, opt-in ``--run-live``)
-----------------------------------------------------------
5. 실 YouTube Data API v3 경유 videos.insert + videos.list readback + 4 필드
   검증 + evidence JSON anchor.

D-08 PIPELINE_VERSION invariant — production_metadata.py 의 ``PIPELINE_VERSION="1.0.0"``
constant 가 본 테스트의 regression guard. 변경 시 양쪽 반드시 동반 bump 대표님.
"""
from __future__ import annotations

import json
import re
from datetime import datetime

import pytest


# --- Tier 1 tests (always-run, no API) --------------------------------------


_GOLDEN_DESCRIPTION_WITH_META = (
    "샘플 설명\n\n"
    "<!-- production_metadata\n"
    "{"
    "\"script_seed\": \"s1\", "
    "\"assets_origin\": \"smoke:test\", "
    "\"pipeline_version\": \"1.0.0\", "
    "\"checksum\": \"sha256:abc123\""
    "}\n"
    "-->"
)


def test_smoke_04_regex_matches_valid_html_comment():
    """PRODUCTION_METADATA_REGEX 가 valid HTML comment 매칭 + JSON 4 필드 추출."""
    from scripts.smoke.upload_evidence import PRODUCTION_METADATA_REGEX

    match = PRODUCTION_METADATA_REGEX.search(_GOLDEN_DESCRIPTION_WITH_META)
    assert match is not None, (
        "SMOKE-04: regex 가 golden description 매칭 실패 대표님"
    )

    payload = json.loads(match.group(1))
    for field in ("script_seed", "assets_origin", "pipeline_version", "checksum"):
        assert payload.get(field), (
            f"SMOKE-04: regex 추출 payload 의 {field} 필드 비어있음 대표님"
        )
    assert payload["pipeline_version"] == "1.0.0", (
        "SMOKE-04 D-08 PIPELINE_VERSION invariant 위반 대표님"
    )


def test_smoke_04_regex_requires_dotall_flag():
    """regex flags 에 re.DOTALL 필수 — multi-line JSON payload 매칭 담보."""
    from scripts.smoke.upload_evidence import PRODUCTION_METADATA_REGEX

    assert PRODUCTION_METADATA_REGEX.flags & re.DOTALL, (
        "SMOKE-04: re.DOTALL flag 부재 대표님 — multi-line JSON payload 매칭 불가"
    )
    # 추가 sanity — dot-all 없이는 매칭 불가능한 케이스로 재확인.
    compact_multiline = "<!-- production_metadata\n{\"a\":\n1}\n-->"
    match = PRODUCTION_METADATA_REGEX.search(compact_multiline)
    assert match is not None, "SMOKE-04: DOTALL 가 적용된 multi-line 매칭 실패"


def test_smoke_04_regex_fails_on_missing_comment():
    """HTML comment 가 없는 plain description → regex match is None."""
    from scripts.smoke.upload_evidence import PRODUCTION_METADATA_REGEX

    plain_description = "그냥 평범한 유튜브 설명 — production_metadata 주입 없음"
    assert PRODUCTION_METADATA_REGEX.search(plain_description) is None, (
        "SMOKE-04: HTML comment 부재 description 에서 false-positive 매칭 대표님"
    )


def test_smoke_04_fixture_readback_validates_all_four_fields(fixtures_dir):
    """sample_smoke_upload.json golden fixture 4 필드 readback + D-08 version lock."""
    from scripts.smoke.upload_evidence import REQUIRED_METADATA_FIELDS

    payload = json.loads(
        (fixtures_dir / "sample_smoke_upload.json").read_text(encoding="utf-8"),
    )

    assert payload["required_fields_present"] is True, (
        "SMOKE-04: golden fixture required_fields_present 플래그 False 대표님"
    )
    assert payload["missing_fields"] == [], (
        f"SMOKE-04: golden fixture missing_fields 비어있지 않음 {payload['missing_fields']}"
    )

    # REQUIRED_METADATA_FIELDS contract 와 정확 일치 — 누락 필드 즉시 식별 가능.
    assert len(REQUIRED_METADATA_FIELDS) == 4, (
        "SMOKE-04: REQUIRED_METADATA_FIELDS 개수 4 불변 대표님"
    )
    for field in REQUIRED_METADATA_FIELDS:
        assert payload["production_metadata"].get(field), (
            f"SMOKE-04: golden fixture 의 production_metadata.{field} 비어있음"
        )

    # D-08 PIPELINE_VERSION invariant — golden fixture 도 "1.0.0" 사용.
    assert payload["production_metadata"]["pipeline_version"] == "1.0.0", (
        "SMOKE-04 PIPELINE_VERSION lock 위반 — production_metadata.py bump 동반 필요"
    )

    # script_seed/assets_origin/checksum 도 non-empty 재확인 (acceptance grep 보조).
    assert payload["production_metadata"]["script_seed"], "script_seed empty"
    assert payload["production_metadata"]["assets_origin"], "assets_origin empty"
    assert payload["production_metadata"]["checksum"].startswith("sha256:"), (
        "checksum prefix sha256: 부재 대표님"
    )


# --- Tier 2 live tests (opt-in via --run-live) ------------------------------


@pytest.mark.live_smoke
def test_smoke_04_real_videos_list_readback_after_upload(tmp_evidence_dir):
    """실 videos.insert → videos.list readback + 4 필드 + evidence anchor 검증.

    Tier 2 test 13-03-02 와는 독립 업로드 — 과금은 배가되지만 SMOKE-03/04 격리성
    우선. Plan 13-05 Wave 4 Full E2E runner 는 1-shot 으로 두 SC 모두 충족.
    """
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
    from scripts.smoke.upload_evidence import (
        REQUIRED_METADATA_FIELDS,
        anchor_upload_evidence,
    )

    credentials = get_credentials()
    youtube = build("youtube", "v3", credentials=credentials)

    plan = _build_smoke_plan()
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
    assert video_id, "SMOKE-04 Tier 2: videos.insert 결과 video_id 비어있음"

    try:
        _wait_for_processing(youtube, video_id)
        sid = datetime.now().strftime("%Y%m%d_%H%M%S")
        evidence = anchor_upload_evidence(
            youtube,
            video_id,
            sid,
            evidence_dir=tmp_evidence_dir,
        )

        # 핵심 SMOKE-04 assertions.
        assert evidence["required_fields_present"] is True, (
            f"SMOKE-04: required_fields_present False 대표님 — missing={evidence['missing_fields']}"
        )
        assert evidence["missing_fields"] == [], (
            "SMOKE-04: missing_fields 비어있지 않음 대표님"
        )
        for field in REQUIRED_METADATA_FIELDS:
            assert evidence["production_metadata"].get(field), (
                f"SMOKE-04: readback 후 production_metadata.{field} 공란 대표님"
            )
        assert evidence["production_metadata"]["pipeline_version"] == "1.0.0", (
            "SMOKE-04 D-08 PIPELINE_VERSION 실 업로드 readback 불일치 대표님"
        )
        assert evidence["production_metadata"]["checksum"].startswith("sha256:"), (
            "SMOKE-04: checksum prefix 'sha256:' 부재 대표님"
        )

        # evidence JSON 파일이 실제로 write 되어 있고 readback 와 일치.
        evidence_path = tmp_evidence_dir / f"smoke_upload_{sid}.json"
        assert evidence_path.exists(), (
            "SMOKE-04: evidence JSON 파일 write 실패 대표님"
        )
        disk_payload = json.loads(evidence_path.read_text(encoding="utf-8"))
        assert disk_payload["video_id"] == video_id, (
            "SMOKE-04: evidence JSON 디스크 readback 의 video_id 불일치"
        )
        assert disk_payload["production_metadata"] == evidence["production_metadata"], (
            "SMOKE-04: evidence 디스크 vs 메모리 production_metadata 불일치"
        )
    finally:
        _delete_video(youtube, video_id)
