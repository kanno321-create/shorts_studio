"""verify_baseline_parity — ffprobe 기반 우리 final.mp4 의 production baseline 정량 비교.

Phase 16-04 — REQ-PROD-INT-13. "spec pass != production pass" 재발 방지.

shorts_naberal/output/{zodiac-killer, mary-celeste, db-cooper, elisa-lam, kitakyushu-matsunaga}/final.mp4
를 baseline 으로 잡고 우리 산출 final.mp4 의 다음을 비교:
  - 해상도 (절대: 1080x1920 strict)
  - duration (절대: MIN_DURATION_S=60.0 ~ MAX=125.0)
  - video codec (h264 or hevc)
  - audio channels (stereo 2 strict — SC#5)
  - audio sample_rate (>=44100 Hz)
  - video bitrate (>=5000 kbps — session #32 519kbps shock 재발 방지)
  - subtitle track (>=1)
  - baseline 상대 bitrate ±10%
  - baseline 상대 fps ±10%

gate_guard.ASSEMBLY 최종 체크 또는 CLI 로 실행.

Exit code:
  0 = PASS (모든 criterion 통과)
  1 = FAIL (1개 이상 criterion 미달)
  2 = baseline 접근 불가 (--dry-run 없이, shorts_naberal 경로 없음)
"""
from __future__ import annotations

import argparse
import json
import logging
import shutil
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

BASELINE_CANDIDATE_PATHS = [
    "C:/Users/PC/Desktop/shorts_naberal/output/zodiac-killer/final.mp4",
    "C:/Users/PC/Desktop/shorts_naberal/output/mary-celeste/final.mp4",
    "C:/Users/PC/Desktop/shorts_naberal/output/db-cooper/final.mp4",
    "C:/Users/PC/Desktop/shorts_naberal/output/elisa-lam/final.mp4",
    "C:/Users/PC/Desktop/shorts_naberal/output/kitakyushu-matsunaga/final.mp4",
]

TARGET_W = 1080
TARGET_H = 1920
MIN_DURATION_S = 60.0  # ROADMAP Phase 16 SC#4 absolute floor
MAX_DURATION_S = 125.0
TOLERANCE = 0.10  # ±10% for baseline-relative metrics

# SC#5 absolute thresholds (session #32 shock event defence)
REQUIRED_AUDIO_CHANNELS = 2  # stereo
MIN_AUDIO_SAMPLE_RATE = 44100  # Hz
MIN_VIDEO_BITRATE_KBPS = 5000  # absolute floor — 519kbps shock 재발 방지
MIN_SUBTITLE_TRACKS = 1

logger = logging.getLogger(__name__)


@dataclass
class VideoMeta:
    """ffprobe 단일 mp4 meta."""

    path: str
    width: int
    height: int
    duration_s: float
    codec: str
    fps: float
    bitrate_kbps: int
    file_size_mb: float
    subtitle_tracks: int
    audio_channels: int
    audio_sample_rate: int


def ffprobe(path: Path) -> VideoMeta | None:
    """ffprobe 실행 — 실패 시 None.

    Windows 환경 UTF-8 safeguard 포함.
    """
    if shutil.which("ffprobe") is None:
        logger.warning("ffprobe 미설치 — baseline parity skip")
        return None
    try:
        r = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_format",
                "-show_streams",
                "-of",
                "json",
                str(path),
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=30,
        )
    except (subprocess.TimeoutExpired, OSError) as e:
        logger.warning("ffprobe 실행 실패 path=%s err=%s", path, e)
        return None
    if r.returncode != 0:
        logger.warning("ffprobe returncode=%d stderr=%s", r.returncode, r.stderr[:200])
        return None
    try:
        info = json.loads(r.stdout)
    except json.JSONDecodeError as e:
        logger.warning("ffprobe json parse 실패: %s", e)
        return None

    streams = info.get("streams", [])
    v_streams = [s for s in streams if s.get("codec_type") == "video"]
    s_streams = [s for s in streams if s.get("codec_type") == "subtitle"]
    a_streams = [s for s in streams if s.get("codec_type") == "audio"]
    if not v_streams:
        return None
    v = v_streams[0]
    a = a_streams[0] if a_streams else {}
    fmt = info.get("format", {})

    fps_str = v.get("r_frame_rate", "30/1")
    try:
        num, den = fps_str.split("/")
        fps = float(num) / float(den or "1")
    except (ValueError, ZeroDivisionError):
        fps = 30.0

    bitrate_kbps = 0
    if fmt.get("bit_rate"):
        try:
            bitrate_kbps = int(fmt["bit_rate"]) // 1000
        except (TypeError, ValueError):
            bitrate_kbps = 0

    file_size_mb = 0.0
    if fmt.get("size"):
        try:
            file_size_mb = round(int(fmt["size"]) / 1024 / 1024, 2)
        except (TypeError, ValueError):
            file_size_mb = 0.0

    return VideoMeta(
        path=str(path),
        width=int(v.get("width", 0)),
        height=int(v.get("height", 0)),
        duration_s=float(fmt.get("duration", 0.0) or 0.0),
        codec=str(v.get("codec_name", "")),
        fps=fps,
        bitrate_kbps=bitrate_kbps,
        file_size_mb=file_size_mb,
        subtitle_tracks=len(s_streams),
        audio_channels=int(a.get("channels", 0) or 0),
        audio_sample_rate=int(a.get("sample_rate", 0) or 0),
    )


def discover_baselines(max_count: int = 3) -> list[Path]:
    """shorts_naberal 5 candidate path 중 존재하는 것 최대 max_count 개 반환."""
    found: list[Path] = []
    for p in BASELINE_CANDIDATE_PATHS:
        if Path(p).exists():
            found.append(Path(p))
        if len(found) >= max_count:
            break
    return found


def within(value: float, target: float, tolerance: float = TOLERANCE) -> bool:
    """|value-target|/|target| <= tolerance."""
    if target == 0:
        return value == 0
    return abs(value - target) / abs(target) <= tolerance


def compare_to_baselines(
    ours: VideoMeta, baselines: list[VideoMeta]
) -> dict:
    """각 criterion 에 대해 pass/fail 판정 + 상세 metrics.

    반환 dict:
        {"ours": <asdict>, "baselines": [<asdict>...], "criteria": {...}, "summary": {...}}
    """
    report: dict = {
        "ours": asdict(ours),
        "baselines": [asdict(b) for b in baselines],
        "criteria": {},
    }

    # Absolute criteria
    report["criteria"]["resolution"] = {
        "value": f"{ours.width}x{ours.height}",
        "target": f"{TARGET_W}x{TARGET_H}",
        "pass": ours.width == TARGET_W and ours.height == TARGET_H,
    }
    report["criteria"]["duration"] = {
        "value": ours.duration_s,
        "target_min": MIN_DURATION_S,
        "target_max": MAX_DURATION_S,
        "pass": MIN_DURATION_S <= ours.duration_s <= MAX_DURATION_S,
    }
    report["criteria"]["codec"] = {
        "value": ours.codec,
        "expected_set": ["h264", "hevc"],
        "pass": ours.codec in {"h264", "hevc"},
    }
    # SC#5 absolute audio/bitrate/subtitle thresholds — session #32 shock defence
    report["criteria"]["audio_channels"] = {
        "value": ours.audio_channels,
        "expected": REQUIRED_AUDIO_CHANNELS,
        "pass": ours.audio_channels == REQUIRED_AUDIO_CHANNELS,
    }
    report["criteria"]["audio_sample_rate"] = {
        "value": ours.audio_sample_rate,
        "expected_min": MIN_AUDIO_SAMPLE_RATE,
        "pass": ours.audio_sample_rate >= MIN_AUDIO_SAMPLE_RATE,
    }
    report["criteria"]["min_video_bitrate"] = {
        "value": ours.bitrate_kbps,
        "threshold_kbps": MIN_VIDEO_BITRATE_KBPS,
        "pass": ours.bitrate_kbps >= MIN_VIDEO_BITRATE_KBPS,
    }
    report["criteria"]["subtitle_track_present"] = {
        "value": ours.subtitle_tracks,
        "expected_min": MIN_SUBTITLE_TRACKS,
        "pass": ours.subtitle_tracks >= MIN_SUBTITLE_TRACKS,
    }

    # Baseline-relative criteria
    if baselines:
        avg_br = sum(b.bitrate_kbps for b in baselines) / len(baselines)
        report["criteria"]["bitrate_vs_baseline"] = {
            "value": ours.bitrate_kbps,
            "baseline_avg": round(avg_br, 1),
            "tolerance": TOLERANCE,
            "pass": within(ours.bitrate_kbps, avg_br) if avg_br > 0 else True,
        }
        avg_fps = sum(b.fps for b in baselines) / len(baselines)
        report["criteria"]["fps_vs_baseline"] = {
            "value": round(ours.fps, 2),
            "baseline_avg": round(avg_fps, 2),
            "pass": within(ours.fps, avg_fps),
        }

    report["summary"] = {
        "all_pass": all(c.get("pass") for c in report["criteria"].values()),
        "fail_count": sum(
            1 for c in report["criteria"].values() if not c.get("pass")
        ),
        "criterion_count": len(report["criteria"]),
    }
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Phase 16-04 baseline parity verifier (ffprobe)",
        epilog="Compares our final.mp4 against shorts_naberal production baselines.",
    )
    parser.add_argument(
        "--our-mp4",
        type=Path,
        required=True,
        help="우리 산출 final.mp4 경로",
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=None,
        help="JSON report 저장 경로 (옵션)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="baseline 없어도 ours 절대 criterion 만 검증",
    )
    parser.add_argument(
        "--episode",
        default=None,
        help="에피소드명 라벨 (report 용)",
    )
    args = parser.parse_args(argv)

    if not args.our_mp4.exists():
        print(
            f"[verify_baseline_parity] our_mp4 미존재: {args.our_mp4}",
            file=sys.stderr,
        )
        return 1
    ours = ffprobe(args.our_mp4)
    if ours is None:
        print(
            "[verify_baseline_parity] ffprobe 실행 실패 — FFmpeg 설치 확인",
            file=sys.stderr,
        )
        return 1

    baselines: list[VideoMeta] = []
    for bp in discover_baselines():
        meta = ffprobe(bp)
        if meta:
            baselines.append(meta)
    if not baselines and not args.dry_run:
        print(
            "[verify_baseline_parity] baseline 3편 확보 불가 — shorts_naberal 경로 확인 "
            "or --dry-run 사용",
            file=sys.stderr,
        )
        return 2

    report = compare_to_baselines(ours, baselines)
    if args.episode:
        report["episode"] = args.episode
    report_text = json.dumps(report, indent=2, ensure_ascii=False, default=str)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(report_text, encoding="utf-8")
    print(report_text)
    return 0 if report["summary"]["all_pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
