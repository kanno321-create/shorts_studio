"""Phase 16-03 W1-SUBTITLE-PRODUCER-AGENT + W1-SUBTITLE-WRAPPER 검증.

TestSubtitleProducerAgent: AGENT.md frontmatter + 5 섹션 + description 길이.
TestSubtitleProducerWrapper: SubtitleProducer Python wrapper API.
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
AGENT_MD = REPO_ROOT / ".claude" / "agents" / "producers" / "subtitle-producer" / "AGENT.md"


class TestSubtitleProducerAgent:
    """subtitle-producer AGENT.md v1.0 spec 준수 검증."""

    def test_agent_md_exists(self):
        assert AGENT_MD.exists(), f"AGENT.md missing: {AGENT_MD}"

    def test_agent_md_min_lines(self):
        lines = AGENT_MD.read_text(encoding="utf-8").splitlines()
        assert len(lines) >= 100, f"AGENT.md too short: {len(lines)} lines"

    def test_frontmatter_name(self):
        text = AGENT_MD.read_text(encoding="utf-8")
        assert re.search(r"^name: subtitle-producer$", text, re.MULTILINE)

    def test_frontmatter_version(self):
        text = AGENT_MD.read_text(encoding="utf-8")
        assert re.search(r"^version: 1\.0$", text, re.MULTILINE)

    def test_frontmatter_role_producer(self):
        text = AGENT_MD.read_text(encoding="utf-8")
        assert re.search(r"^role: producer$", text, re.MULTILINE)

    def test_frontmatter_max_turns(self):
        text = AGENT_MD.read_text(encoding="utf-8")
        assert re.search(r"^maxTurns: 3$", text, re.MULTILINE)

    def test_description_under_1024_chars(self):
        text = AGENT_MD.read_text(encoding="utf-8")
        m = re.search(r"^description:\s*(.+?)\nversion:", text, re.DOTALL | re.MULTILINE)
        assert m, "description field not found"
        desc = m.group(1).strip()
        assert len(desc) <= 1024, f"description too long: {len(desc)} chars"

    def test_description_mentions_faster_whisper(self):
        text = AGENT_MD.read_text(encoding="utf-8")
        m = re.search(r"^description:\s*(.+?)\nversion:", text, re.DOTALL | re.MULTILINE)
        desc = m.group(1).strip()
        assert "faster-whisper" in desc and "large-v3" in desc

    def test_description_mentions_3_outputs(self):
        text = AGENT_MD.read_text(encoding="utf-8")
        m = re.search(r"^description:\s*(.+?)\nversion:", text, re.DOTALL | re.MULTILINE)
        desc = m.group(1).strip()
        assert "srt" in desc.lower() or "SRT" in desc
        assert "ass" in desc.lower() or "ASS" in desc
        assert "json" in desc.lower() or "JSON" in desc

    @pytest.mark.parametrize("section", [
        "<role>",
        "<mandatory_reads>",
        "<output_format>",
        "<skills>",
        "<constraints>",
    ])
    def test_required_section_present(self, section):
        text = AGENT_MD.read_text(encoding="utf-8")
        assert section in text, f"section missing: {section}"

    def test_must_remember_section_present(self):
        text = AGENT_MD.read_text(encoding="utf-8")
        assert "MUST REMEMBER" in text

    def test_mentions_faster_whisper_at_least_thrice(self):
        text = AGENT_MD.read_text(encoding="utf-8")
        count = text.count("faster-whisper") + text.count("large-v3")
        assert count >= 3, f"faster-whisper / large-v3 references too few: {count}"

    def test_mentions_timestamp_repair(self):
        text = AGENT_MD.read_text(encoding="utf-8")
        assert "clamp" in text and "merge" in text and "fallback" in text


class TestSubtitleProducerWrapper:
    """scripts/orchestrator/api/subtitle_producer.py Python wrapper API."""

    def test_imports_work(self):
        from scripts.orchestrator.api.subtitle_producer import (
            SubtitleProducer,
            SubtitleProducerError,
            SubtitleTripleResult,
        )
        assert SubtitleProducer is not None
        assert SubtitleProducerError is not None
        assert SubtitleTripleResult is not None

    def test_producer_init_with_project_root(self, tmp_path):
        from scripts.orchestrator.api.subtitle_producer import SubtitleProducer, SubtitleProducerError
        # Using real project_root so word_subtitle.py exists
        p = SubtitleProducer(project_root=REPO_ROOT)
        assert p.project_root == REPO_ROOT.absolute()
        assert p.word_subtitle_script.exists()

    def test_producer_init_raises_when_word_subtitle_missing(self, tmp_path):
        from scripts.orchestrator.api.subtitle_producer import SubtitleProducer, SubtitleProducerError
        # Fake project_root without word_subtitle.py
        with pytest.raises(SubtitleProducerError):
            SubtitleProducer(project_root=tmp_path)

    def test_produce_raises_when_narration_missing(self, tmp_path):
        from scripts.orchestrator.api.subtitle_producer import SubtitleProducer, SubtitleProducerError
        p = SubtitleProducer(project_root=REPO_ROOT)
        missing_mp3 = tmp_path / "missing.mp3"
        script_json = tmp_path / "script.json"
        script_json.write_text('{"sections": []}', encoding="utf-8")
        with pytest.raises(SubtitleProducerError, match="narration_mp3"):
            p.produce(missing_mp3, script_json, tmp_path / "out")

    def test_produce_raises_when_script_missing(self, tmp_path):
        from scripts.orchestrator.api.subtitle_producer import SubtitleProducer, SubtitleProducerError
        p = SubtitleProducer(project_root=REPO_ROOT)
        narration = tmp_path / "narration.mp3"
        narration.write_bytes(b"fake")
        missing_json = tmp_path / "missing.json"
        with pytest.raises(SubtitleProducerError, match="script_json"):
            p.produce(narration, missing_json, tmp_path / "out")

    def test_subtitle_triple_result_dataclass(self):
        from scripts.orchestrator.api.subtitle_producer import SubtitleTripleResult
        r = SubtitleTripleResult(
            srt_path=Path("/tmp/a.srt"),
            ass_path=Path("/tmp/a.ass"),
            json_path=Path("/tmp/a.json"),
            phrase_count=10,
            word_count=30,
            coverage_percent=96.5,
            device="cuda",
            language="ko",
            model="large-v3",
        )
        assert r.phrase_count == 10
        assert r.coverage_percent == 96.5
        d = r.to_dict()
        assert d["coverage_percent"] == 96.5
        assert d["language"] == "ko"

    def test_produce_calls_subprocess_with_correct_args(self, tmp_path):
        """subprocess.run called with --audio/--output/--model/--script/--language."""
        from scripts.orchestrator.api.subtitle_producer import SubtitleProducer
        p = SubtitleProducer(project_root=REPO_ROOT)

        narration = tmp_path / "narration.mp3"
        narration.write_bytes(b"fake mp3")
        script_json = tmp_path / "script.json"
        script_json.write_text('{"sections": []}', encoding="utf-8")
        output_dir = tmp_path / "out"

        # Prepare mock: subprocess.run returns success but we also simulate the 3 output files
        def fake_run(cmd, **kwargs):
            # Simulate word_subtitle.py creating 3 files
            (output_dir / "subtitles_remotion.srt").write_text("1\n00:00:00,000 --> 00:00:01,000\nhello\n\n", encoding="utf-8")
            (output_dir / "subtitles_remotion.ass").write_text("[Script Info]\n", encoding="utf-8")
            (output_dir / "subtitles_remotion.json").write_text('[{"startMs":0,"endMs":1000,"words":["hello"]}]', encoding="utf-8")
            return MagicMock(returncode=0, stdout="Loaded faster-whisper model 'large-v3' on CPU\n", stderr="")

        with patch("scripts.orchestrator.api.subtitle_producer.subprocess.run", side_effect=fake_run) as mock_run:
            result = p.produce(narration, script_json, output_dir)

        # Verify subprocess called (first call is word_subtitle.py; subsequent may be ffprobe)
        assert mock_run.called
        # Find the word_subtitle.py call (has --audio arg)
        word_sub_call = None
        for call in mock_run.call_args_list:
            cmd = call.args[0] if call.args else call.kwargs.get("args", [])
            if isinstance(cmd, list) and "--audio" in cmd:
                word_sub_call = cmd
                break
        assert word_sub_call is not None, f"no word_subtitle.py call found; calls: {mock_run.call_args_list}"
        assert "--output" in word_sub_call
        assert "--model" in word_sub_call
        assert "large-v3" in word_sub_call
        assert "--language" in word_sub_call
        assert "ko" in word_sub_call

        # Verify result
        assert result.phrase_count == 1
        assert result.srt_path.exists()
        assert result.ass_path.exists()
        assert result.json_path.exists()
        assert result.device == "cpu"  # extracted from stdout
        assert result.model == "large-v3"

    def test_produce_raises_on_subprocess_failure(self, tmp_path):
        from scripts.orchestrator.api.subtitle_producer import SubtitleProducer, SubtitleProducerError
        p = SubtitleProducer(project_root=REPO_ROOT)
        narration = tmp_path / "narration.mp3"
        narration.write_bytes(b"fake")
        script_json = tmp_path / "script.json"
        script_json.write_text('{}', encoding="utf-8")

        with patch("scripts.orchestrator.api.subtitle_producer.subprocess.run",
                   return_value=MagicMock(returncode=2, stdout="", stderr="transcription failed")):
            with pytest.raises(SubtitleProducerError, match="exit 2"):
                p.produce(narration, script_json, tmp_path / "out")

    def test_produce_raises_when_output_files_missing(self, tmp_path):
        """subprocess success (returncode=0) but output files not created."""
        from scripts.orchestrator.api.subtitle_producer import SubtitleProducer, SubtitleProducerError
        p = SubtitleProducer(project_root=REPO_ROOT)
        narration = tmp_path / "narration.mp3"
        narration.write_bytes(b"fake")
        script_json = tmp_path / "script.json"
        script_json.write_text('{}', encoding="utf-8")
        output_dir = tmp_path / "out"

        with patch("scripts.orchestrator.api.subtitle_producer.subprocess.run",
                   return_value=MagicMock(returncode=0, stdout="", stderr="")):
            with pytest.raises(SubtitleProducerError, match="출력 파일 누락"):
                p.produce(narration, script_json, output_dir)

    def test_extract_device_from_stdout(self):
        from scripts.orchestrator.api.subtitle_producer import SubtitleProducer
        p = SubtitleProducer(project_root=REPO_ROOT)
        assert p._extract_device("Loaded faster-whisper model 'large-v3' on CUDA") == "cuda"
        assert p._extract_device("Loaded faster-whisper model 'large-v3' on CPU") == "cpu"
        assert p._extract_device("") == "cpu"
        assert p._extract_device("device=cuda") == "cuda"
