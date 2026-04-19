"""Positive control tests: normal Phase 5 code is ALLOWED by pre_tool_use.py.

Regression guard against over-blocking: if someone tightens the
`.claude/deprecated_patterns.json` regexes too aggressively (e.g. case-
insensitive `t2v` without lookbehind, or `segments` without the `\\[\\s*\\]`
suffix, or `todo` without the `(next-session` qualifier), these tests fail
and reveal the false-positive.

Exercises the happy path for every canonical Phase 5 identifier:
    - image_to_video (D-13 allowed I2V function)
    - anchor_frame (D-13 kwarg)
    - Korean prose (non-ASCII codepoints must not trip any regex)
    - Kling I2V endpoint string
    - CircuitBreaker / VoiceFirstTimeline / AudioSegment (D-10, D-6 classes)
    - audio_segments / video_cuts (identifiers, NOT `segments[]` bracket form)

Payload shape per Claude Code PreToolUse spec:
    - Write     -> input.content
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

STUDIO_ROOT = Path(__file__).resolve().parents[2]
HOOK = STUDIO_ROOT / ".claude" / "hooks" / "pre_tool_use.py"


def _hook_check(
    tool_name: str,
    content: str,
    file_path: str = "scripts/orchestrator/shorts_pipeline.py",
) -> dict:
    tool_input: dict = {"file_path": file_path}
    if tool_name == "Write":
        tool_input["content"] = content
    elif tool_name == "Edit":
        tool_input["old_string"] = ""
        tool_input["new_string"] = content
    elif tool_name == "MultiEdit":
        tool_input["edits"] = [{"old_string": "", "new_string": content}]
    else:
        tool_input["content"] = content
    payload = {"tool_name": tool_name, "input": tool_input}
    proc = subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(payload),
        text=True,
        encoding="utf-8",
        capture_output=True,
        timeout=10,
        cwd=str(STUDIO_ROOT),
    )
    assert proc.returncode == 0, (
        f"Hook exited {proc.returncode}: stderr={proc.stderr!r}"
    )
    return json.loads(proc.stdout)


def test_image_to_video_allowed():
    """D-13: canonical I2V function name — must pass untouched."""
    res = _hook_check(
        "Write",
        "def image_to_video(anchor_frame, prompt: str):\n    pass\n",
    )
    assert res["decision"] == "allow", (
        f"D-13 I2V function must pass: {res}"
    )


def test_anchor_frame_kwarg_allowed():
    """D-13: `anchor_frame=Path('a.png')` kwarg call — canonical Phase 5 usage."""
    res = _hook_check(
        "Write",
        "adapter.image_to_video(prompt='x', anchor_frame=Path('a.png'))\n",
    )
    assert res["decision"] == "allow", (
        f"anchor_frame kwarg call must be allowed: {res}"
    )


def test_korean_prose_allowed():
    """Korean prose in docstrings (non-ASCII codepoints) must not trip any regex."""
    res = _hook_check(
        "Write",
        '"""탐정님의 대사가 흥미롭게 전개됩니다."""\n',
    )
    assert res["decision"] == "allow", (
        f"Korean docstring must be allowed: {res}"
    )


def test_kling_fal_endpoint_allowed():
    """Kling I2V endpoint URL is allowed — has `video` and `image-to-video`, no `t2v`."""
    res = _hook_check(
        "Write",
        'FAL_ENDPOINT = "fal-ai/kling-video/v2.5-turbo/pro/image-to-video"\n',
    )
    assert res["decision"] == "allow", (
        f"Kling I2V endpoint URL must be allowed: {res}"
    )


def test_circuit_breaker_code_allowed():
    """D-6 CircuitBreaker class — normal Phase 5 orchestrator code."""
    res = _hook_check(
        "Write",
        "class CircuitBreaker:\n    def call(self, fn):\n        return fn()\n",
    )
    assert res["decision"] == "allow", (
        f"CircuitBreaker class must be allowed: {res}"
    )


def test_voice_first_timeline_allowed():
    """D-10 VoiceFirstTimeline — `audio_segments` identifier must NOT trip `segments[]`."""
    res = _hook_check(
        "Write",
        (
            "class VoiceFirstTimeline:\n"
            "    def align(self, audio_segments, video_cuts):\n"
            "        return self\n"
        ),
    )
    assert res["decision"] == "allow", (
        f"VoiceFirstTimeline (identifiers only, no bracket form) must be allowed: {res}"
    )


def test_empty_content_allowed():
    """Empty content must not crash the Hook nor trigger any regex."""
    res = _hook_check("Write", "")
    assert res["decision"] == "allow", (
        f"Empty content must be allowed: {res}"
    )


def test_audio_segment_dataclass_allowed():
    """D-10 AudioSegment dataclass — `AudioSegment` class name must not trip `segments[]`."""
    res = _hook_check(
        "Write",
        (
            "from dataclasses import dataclass\n"
            "@dataclass\n"
            "class AudioSegment:\n"
            "    index: int\n"
            "    start: float\n"
        ),
    )
    assert res["decision"] == "allow", (
        f"AudioSegment dataclass must be allowed: {res}"
    )


def test_i2v_in_edit_allowed():
    """Edit tool with I2V function body — must pass (no T2V, no skip_gates)."""
    res = _hook_check(
        "Edit",
        "result = adapter.image_to_video(anchor_frame=frame, duration=6)\n",
    )
    assert res["decision"] == "allow", (
        f"I2V call via Edit tool must be allowed: {res}"
    )
