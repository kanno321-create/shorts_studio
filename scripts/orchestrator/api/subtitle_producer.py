"""SubtitleProducer — Python wrapper for word_subtitle.py.

subtitle-producer AGENT.md 가 호출하는 adapter. narration.mp3 + script.json 을 받아
subtitles_remotion.{srt,ass,json} 3종을 ASSETS phase 에 생성.

Phase 16-03 — REQ-PROD-INT-03.

Contract (from Plan 16-03):
    Input:  narration_mp3 (Path) + script_json (Path) + output_dir (Path)
    Output: SubtitleTripleResult dataclass (srt_path, ass_path, json_path + metrics)
    Fallback: CUDA → CPU 자동 (word_subtitle.py 내부 로직 보전)
    Error:  SubtitleProducerError (RuntimeError subclass)
"""
from __future__ import annotations

import json
import logging
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

__all__ = ["SubtitleProducer", "SubtitleProducerError", "SubtitleTripleResult"]

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT_S = 600  # faster-whisper CPU 는 60s 오디오에 3~5분
DEFAULT_MODEL = "large-v3"
DEFAULT_LANGUAGE = "ko"
DEFAULT_MAX_CHARS_PER_LINE = 8


class SubtitleProducerError(RuntimeError):
    """subtitle 생성 실패."""


@dataclass
class SubtitleTripleResult:
    """subtitles_remotion.{srt,ass,json} 3종 결과."""

    srt_path: Path
    ass_path: Path
    json_path: Path
    phrase_count: int
    word_count: int
    coverage_percent: float
    device: str  # "cuda" or "cpu"
    language: str
    model: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "srt_path": str(self.srt_path),
            "ass_path": str(self.ass_path),
            "json_path": str(self.json_path),
            "phrase_count": self.phrase_count,
            "word_count": self.word_count,
            "coverage_percent": self.coverage_percent,
            "device": self.device,
            "language": self.language,
            "model": self.model,
        }


class SubtitleProducer:
    """Wrapper around scripts/orchestrator/subtitle/word_subtitle.py."""

    def __init__(
        self,
        project_root: Path | None = None,
        timeout_s: int = DEFAULT_TIMEOUT_S,
    ) -> None:
        self.project_root = (project_root or Path(__file__).resolve().parents[3]).absolute()
        self.word_subtitle_script = (
            self.project_root
            / "scripts"
            / "orchestrator"
            / "subtitle"
            / "word_subtitle.py"
        )
        if not self.word_subtitle_script.exists():
            raise SubtitleProducerError(
                f"word_subtitle.py 미존재: {self.word_subtitle_script}"
            )
        self.timeout_s = timeout_s

    def produce(
        self,
        narration_mp3: Path,
        script_json: Path,
        output_dir: Path,
        max_chars_per_line: int = DEFAULT_MAX_CHARS_PER_LINE,
        language: str = DEFAULT_LANGUAGE,
        model: str = DEFAULT_MODEL,
    ) -> SubtitleTripleResult:
        """3종 subtitle 동시 생성. output_dir/subtitles_remotion.{srt,ass,json} 산출.

        Args:
            narration_mp3: VOICE gate 산출 narration.mp3 절대경로
            script_json: scripter 산출 script.json 절대경로
            output_dir: 출력 디렉토리 (없으면 생성)
            max_chars_per_line: 자막 1줄 최대 글자 (incidents §6: 8 권장)
            language: faster-whisper 언어 코드 ("ko" 기본)
            model: faster-whisper 모델 ("large-v3" 고정)

        Returns:
            SubtitleTripleResult

        Raises:
            SubtitleProducerError: 입력 누락 / subprocess 실패 / 출력 파일 누락
        """
        if not narration_mp3.exists():
            raise SubtitleProducerError(f"narration_mp3 미존재: {narration_mp3}")
        if not script_json.exists():
            raise SubtitleProducerError(f"script_json 미존재: {script_json}")
        output_dir.mkdir(parents=True, exist_ok=True)

        srt_path = output_dir / "subtitles_remotion.srt"
        ass_path = output_dir / "subtitles_remotion.ass"
        json_path = output_dir / "subtitles_remotion.json"

        cmd = [
            sys.executable,
            str(self.word_subtitle_script),
            "--audio",
            str(narration_mp3),
            "--output",
            str(srt_path),
            "--max-chars",
            str(max_chars_per_line),
            "--model",
            model,
            "--script",
            str(script_json),
            "--language",
            language,
        ]
        logger.info(
            "[subtitle-producer] invoking word_subtitle.py: %s",
            " ".join(cmd),
        )
        t0 = time.time()
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=self.timeout_s,
        )
        elapsed = time.time() - t0
        if result.returncode != 0:
            stderr_tail = (result.stderr or "")[-600:]
            raise SubtitleProducerError(
                f"word_subtitle.py 실패 (exit {result.returncode}, {elapsed:.1f}s): {stderr_tail}"
            )

        # 3종 파일 전수 존재 확인
        for p in (srt_path, ass_path, json_path):
            if not p.exists():
                raise SubtitleProducerError(f"출력 파일 누락: {p}")

        # JSON 로드하여 metrics 추출
        try:
            cues = json.loads(json_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            raise SubtitleProducerError(f"{json_path}: 유효하지 않은 JSON ({e})") from e
        if not isinstance(cues, list):
            raise SubtitleProducerError(f"{json_path}: cues list 형식 아님")

        phrase_count = len(cues)
        word_count = sum(
            len(c.get("words", []))
            for c in cues
            if isinstance(c, dict) and isinstance(c.get("words"), list)
        )
        last_end_ms = max(
            (c.get("endMs", 0) for c in cues if isinstance(c, dict)),
            default=0,
        )

        # audio duration (ffprobe)
        audio_duration = self._get_audio_duration(narration_mp3)
        coverage = (
            (last_end_ms / 1000.0) / audio_duration * 100 if audio_duration > 0 else 0.0
        )

        # device 추출 — word_subtitle.py stdout 에서 "device=cuda" / "device=cpu" 검색
        device = self._extract_device(result.stdout)

        logger.info(
            "[subtitle-producer] produced triple: phrases=%d words=%d coverage=%.2f%% device=%s",
            phrase_count,
            word_count,
            coverage,
            device,
        )

        return SubtitleTripleResult(
            srt_path=srt_path,
            ass_path=ass_path,
            json_path=json_path,
            phrase_count=phrase_count,
            word_count=word_count,
            coverage_percent=round(coverage, 2),
            device=device,
            language=language,
            model=model,
        )

    def _get_audio_duration(self, mp3_path: Path) -> float:
        """ffprobe 로 오디오 duration (초) 조회. 실패 시 0.0."""
        if shutil.which("ffprobe") is None:
            logger.warning("[subtitle-producer] ffprobe 미검출 — coverage 계산 불가")
            return 0.0
        try:
            r = subprocess.run(
                [
                    "ffprobe",
                    "-v",
                    "error",
                    "-show_entries",
                    "format=duration",
                    "-of",
                    "default=noprint_wrappers=1:nokey=1",
                    str(mp3_path),
                ],
                capture_output=True,
                text=True,
                timeout=30,
            )
            return float((r.stdout or "0").strip())
        except (subprocess.TimeoutExpired, ValueError) as e:
            logger.warning("[subtitle-producer] ffprobe 실패: %s", e)
            return 0.0

    def _extract_device(self, stdout: str) -> str:
        """word_subtitle.py 로그에서 device=cuda|cpu 추출. 없으면 'cpu' 기본."""
        if not stdout:
            return "cpu"
        for line in stdout.splitlines():
            lowered = line.lower()
            if "device=" in lowered:
                # "device=cuda" or "device=cpu"
                try:
                    return lowered.split("device=", 1)[1].split()[0].strip().rstrip(",;")
                except (IndexError, AttributeError):
                    continue
            # faster-whisper 로그 패턴: "Loaded ... on CUDA" or "Loaded ... on CPU"
            if "loaded faster-whisper" in lowered:
                if "on cuda" in lowered:
                    return "cuda"
                if "on cpu" in lowered:
                    return "cpu"
        return "cpu"
