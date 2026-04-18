"""Tests for scripts/orchestrator/hc_checks.py (Plan 41-02, D-41-04 + HC-1~7 + HC-12).

Fixtures in tmp_path mimic output/{slug}/ shape seen in real outputs (e.g. output/elisa-lam/).
HC-3 mocks ffprobe via monkeypatch on subprocess.run in hc_checks module namespace.
HC-12 generates synthetic PNGs via cv2 (skipped if cv2 unavailable).
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from scripts.orchestrator import hc_checks
from scripts.orchestrator.hc_checks import (
    HCResult,
    check_hc_1,
    check_hc_2,
    check_hc_3,
    check_hc_4,
    check_hc_5,
    check_hc_6,
    check_hc_7,
    check_hc_12_text_screenshot,
    run_all_hc_checks,
)


def _write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")


# ------------------------- HC-1: subtitle coverage -------------------------


def test_hc_1_pass_when_coverage_above_95(tmp_path: Path) -> None:
    script = {
        "sections": [
            {"narration": "elisa lam was found in cecil hotel"},
            {"narration": "the cctv footage was disturbing"},
        ]
    }
    # 10 unique script tokens; include 10 of them in subtitles = 100%
    subs = [
        {"startMs": 0, "endMs": 500, "words": ["elisa", "lam", "was", "found"]},
        {"startMs": 500, "endMs": 1000, "words": ["in", "cecil", "hotel"]},
        {"startMs": 1000, "endMs": 1500, "words": ["the", "cctv", "footage", "was", "disturbing"]},
    ]
    _write_json(tmp_path / "script.json", script)
    _write_json(tmp_path / "subtitles_remotion.json", subs)
    r = check_hc_1(tmp_path)
    assert r.verdict == "PASS"
    assert r.evidence["coverage_pct"] >= 0.95


def test_hc_1_fail_when_coverage_below_95(tmp_path: Path) -> None:
    script = {
        "sections": [
            {"narration": "alpha bravo charlie delta echo foxtrot golf hotel india juliet"}
        ]
    }
    # only 5 of 10 words covered → 50%
    subs = [{"startMs": 0, "endMs": 500, "words": ["alpha", "bravo", "charlie", "delta", "echo"]}]
    _write_json(tmp_path / "script.json", script)
    _write_json(tmp_path / "subtitles_remotion.json", subs)
    r = check_hc_1(tmp_path)
    assert r.verdict == "FAIL"
    assert r.evidence["coverage_pct"] < 0.95


def test_hc_1_fail_when_subtitles_missing(tmp_path: Path) -> None:
    _write_json(tmp_path / "script.json", {"sections": [{"narration": "x"}]})
    r = check_hc_1(tmp_path)
    assert r.verdict == "FAIL"
    assert "subtitles_remotion.json" in r.detail


def test_hc_1_supports_dict_words_shape(tmp_path: Path) -> None:
    """Real outputs may have words as list of {word,start,end} objects."""
    script = {"sections": [{"narration": "hello world test"}]}
    subs = [
        {
            "startMs": 0,
            "endMs": 500,
            "words": [
                {"word": "hello", "start": 0, "end": 100},
                {"word": "world", "start": 100, "end": 200},
                {"word": "test", "start": 200, "end": 300},
            ],
        }
    ]
    _write_json(tmp_path / "script.json", script)
    _write_json(tmp_path / "subtitles_remotion.json", subs)
    r = check_hc_1(tmp_path)
    assert r.verdict == "PASS"


def test_hc_1_legacy_flat_narration(tmp_path: Path) -> None:
    script = {"narration": "one two three"}
    subs = [{"startMs": 0, "endMs": 200, "words": ["one", "two", "three"]}]
    _write_json(tmp_path / "script.json", script)
    _write_json(tmp_path / "subtitles_remotion.json", subs)
    r = check_hc_1(tmp_path)
    assert r.verdict == "PASS"


# ------------------------- HC-2: title length -------------------------


def test_hc_2_pass_within_limits(tmp_path: Path) -> None:
    _write_json(
        tmp_path / "script.json",
        {"title": {"line1": "a" * 12, "line2": "b" * 10}},
    )
    r = check_hc_2(tmp_path)
    assert r.verdict == "PASS"
    assert r.evidence["line1_len"] == 12
    assert r.evidence["line2_len"] == 10


def test_hc_2_fail_line1_13_chars(tmp_path: Path) -> None:
    line1 = "a" * 13  # 13 chars — over 12 limit
    _write_json(tmp_path / "script.json", {"title": {"line1": line1, "line2": "ok"}})
    r = check_hc_2(tmp_path)
    assert r.verdict == "FAIL"
    assert r.evidence["line1_len"] == 13


def test_hc_2_fail_line2_11_chars(tmp_path: Path) -> None:
    line2 = "b" * 11  # 11 chars — over 10 limit
    _write_json(tmp_path / "script.json", {"title": {"line1": "ok", "line2": line2}})
    r = check_hc_2(tmp_path)
    assert r.verdict == "FAIL"
    assert r.evidence["line2_len"] == 11


def test_hc_2_skip_legacy_flat_title(tmp_path: Path) -> None:
    _write_json(tmp_path / "script.json", {"title": "flat string title"})
    r = check_hc_2(tmp_path)
    assert r.verdict == "SKIP"
    assert "legacy" in r.detail.lower()


# ------------------------- HC-3: narration duration -------------------------


def _make_ffprobe_patch(duration_seconds: float):
    """Return a fake subprocess.run callable that emits duration_seconds."""
    def fake_run(cmd, *args, **kwargs):
        result = subprocess.CompletedProcess(cmd, 0, stdout=f"{duration_seconds}\n", stderr="")
        return result
    return fake_run


def test_hc_3_pass_within_10s(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    script = {"sections": [{"narration": "a" * 850}]}  # 850 chars / 8.5 = 100s
    _write_json(tmp_path / "script.json", script)
    (tmp_path / "narration.mp3").write_bytes(b"fake-mp3")
    monkeypatch.setattr(hc_checks.subprocess, "run", _make_ffprobe_patch(95.0))
    r = check_hc_3(tmp_path)
    assert r.verdict == "PASS"
    assert abs(r.evidence["delta"]) <= 10


def test_hc_3_fail_off_by_15s(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    script = {"sections": [{"narration": "a" * 850}]}
    _write_json(tmp_path / "script.json", script)
    (tmp_path / "narration.mp3").write_bytes(b"fake-mp3")
    monkeypatch.setattr(hc_checks.subprocess, "run", _make_ffprobe_patch(85.0))
    r = check_hc_3(tmp_path)
    assert r.verdict == "FAIL"
    assert abs(r.evidence["delta"]) > 10


def test_hc_3_fail_narration_missing(tmp_path: Path) -> None:
    _write_json(tmp_path / "script.json", {"sections": [{"narration": "abc"}]})
    r = check_hc_3(tmp_path)
    assert r.verdict == "FAIL"
    assert "narration.mp3" in r.detail


def test_hc_3_fail_when_ffprobe_unavailable(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    script = {"sections": [{"narration": "abc"}]}
    _write_json(tmp_path / "script.json", script)
    (tmp_path / "narration.mp3").write_bytes(b"fake")

    def raise_fnf(*a, **k):
        raise FileNotFoundError("ffprobe not on PATH")

    monkeypatch.setattr(hc_checks.subprocess, "run", raise_fnf)
    r = check_hc_3(tmp_path)
    assert r.verdict == "FAIL"


# ------------------------- HC-4: GATE 1-5 present -------------------------


def test_hc_4_pass_with_5_gates(tmp_path: Path) -> None:
    gates = [
        {"gate_id": f"GATE-{i}", "inspector": f"ins-{i}", "verdict": "PASS"}
        for i in range(1, 6)
    ]
    _write_json(tmp_path / "gates.json", gates)
    r = check_hc_4(tmp_path)
    assert r.verdict == "PASS"


def test_hc_4_fail_with_4_gates(tmp_path: Path) -> None:
    gates = [{"gate_id": f"GATE-{i}", "verdict": "PASS"} for i in range(1, 5)]
    _write_json(tmp_path / "gates.json", gates)
    r = check_hc_4(tmp_path)
    assert r.verdict == "FAIL"
    assert "GATE-5" in r.evidence["missing"]


def test_hc_4_fail_missing_file(tmp_path: Path) -> None:
    r = check_hc_4(tmp_path)
    assert r.verdict == "FAIL"
    assert "gates.json" in r.detail


# ------------------------- HC-5: orchestrator violations -------------------------


def test_hc_5_pass_when_log_missing(tmp_path: Path) -> None:
    r = check_hc_5(tmp_path)
    assert r.verdict == "PASS"
    assert r.evidence["violations"] == 0


def test_hc_5_pass_when_log_has_no_violations(tmp_path: Path) -> None:
    (tmp_path / "orchestrator_actions.log").write_text(
        "INFO: install complete\n", encoding="utf-8"
    )
    r = check_hc_5(tmp_path)
    assert r.verdict == "PASS"


def test_hc_5_fail_when_violation_recorded(tmp_path: Path) -> None:
    (tmp_path / "orchestrator_actions.log").write_text(
        "VIOLATION: ts=... caller=scripts.orchestrator.orchestrate:foo:1 cmd=echo hi\n",
        encoding="utf-8",
    )
    r = check_hc_5(tmp_path)
    assert r.verdict == "FAIL"
    assert r.evidence["violations"] == 1


# ------------------------- HC-6: unique image hashes -------------------------


def test_hc_6_pass_with_6_uniques_from_scenes_field(tmp_path: Path) -> None:
    manifest = {
        "scenes": [
            {"image": f"img_{i}.jpg", "hash": f"sha1:{i:040d}"} for i in range(6)
        ]
    }
    _write_json(tmp_path / "scene-manifest.json", manifest)
    r = check_hc_6(tmp_path)
    assert r.verdict == "PASS"
    assert r.evidence["unique_count"] == 6


def test_hc_6_fail_with_5_uniques(tmp_path: Path) -> None:
    manifest = {
        "scenes": [{"image": f"i_{i}.jpg", "hash": f"sha1:{i:040d}"} for i in range(5)]
    }
    _write_json(tmp_path / "scene-manifest.json", manifest)
    r = check_hc_6(tmp_path)
    assert r.verdict == "FAIL"


def test_hc_6_fail_when_duplicates_reduce_unique_below_6(tmp_path: Path) -> None:
    # 7 entries but only 5 unique hashes
    manifest = {
        "scenes": [
            {"image": "a.jpg", "hash": "h1"},
            {"image": "b.jpg", "hash": "h2"},
            {"image": "c.jpg", "hash": "h3"},
            {"image": "d.jpg", "hash": "h4"},
            {"image": "e.jpg", "hash": "h5"},
            {"image": "f.jpg", "hash": "h1"},  # dup
            {"image": "g.jpg", "hash": "h2"},  # dup
        ]
    }
    _write_json(tmp_path / "scene-manifest.json", manifest)
    r = check_hc_6(tmp_path)
    assert r.verdict == "FAIL"
    assert r.evidence["unique_count"] == 5
    assert "h1" in r.evidence["duplicate_hashes"] or "h2" in r.evidence["duplicate_hashes"]


def test_hc_6_supports_nested_clips_shape(tmp_path: Path) -> None:
    """Real scene-manifest.json has scenes[].clips[] with file_path only."""
    # create 6 unique dummy files so sha1 of bytes differs
    srcs = tmp_path / "sources"
    srcs.mkdir()
    files = []
    for i in range(6):
        p = srcs / f"clip_{i}.bin"
        p.write_bytes(f"unique-content-{i}".encode())
        files.append(f"sources/clip_{i}.bin")
    manifest = {
        "scenes": [
            {"section_index": i, "clips": [{"file_path": f, "type": "image"}]}
            for i, f in enumerate(files)
        ]
    }
    _write_json(tmp_path / "scene-manifest.json", manifest)
    r = check_hc_6(tmp_path)
    assert r.verdict == "PASS"
    assert r.evidence["unique_count"] == 6


# ------------------------- HC-7: duo dialogue flow -------------------------


def test_hc_7_pass_when_watson_followed_by_detective(tmp_path: Path) -> None:
    script = {
        "sections": [
            {"role": "detective", "narration": "..."},
            {"role": "watson", "narration": "질문"},
            {"role": "detective", "narration": "답변"},
            {"role": "watson", "narration": "또 질문"},
            {"role": "detective", "narration": "또 답변"},
        ]
    }
    _write_json(tmp_path / "script.json", script)
    r = check_hc_7(tmp_path)
    assert r.verdict == "PASS"


def test_hc_7_fail_when_watson_last(tmp_path: Path) -> None:
    script = {
        "sections": [
            {"role": "detective", "narration": "a"},
            {"role": "watson", "narration": "b"},
        ]
    }
    _write_json(tmp_path / "script.json", script)
    r = check_hc_7(tmp_path)
    assert r.verdict == "FAIL"
    assert 1 in r.evidence["unanswered_indices"]


def test_hc_7_skip_when_not_duo(tmp_path: Path) -> None:
    script = {"sections": [{"section_type": "hook", "narration": "nope"}]}
    _write_json(tmp_path / "script.json", script)
    r = check_hc_7(tmp_path)
    assert r.verdict == "SKIP"


# ------------------------- HC-12: text screenshot detection -------------------------


cv2 = pytest.importorskip("cv2")
import numpy as np  # noqa: E402


def _make_text_image(path: Path) -> None:
    img = np.zeros((600, 600, 3), dtype=np.uint8) + 255
    for row in range(20, 580, 35):
        for col in range(20, 500, 100):
            cv2.putText(
                img,
                "TEXT",
                (col, row),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.9,
                (0, 0, 0),
                2,
            )
    cv2.imwrite(str(path), img)


def _make_plain_image(path: Path) -> None:
    img = np.zeros((600, 600, 3), dtype=np.uint8)
    img[:, :] = (30, 80, 200)  # solid red-ish
    cv2.imwrite(str(path), img)


def test_hc_12_pass_on_plain_image(tmp_path: Path) -> None:
    p = tmp_path / "plain.png"
    _make_plain_image(p)
    r = check_hc_12_text_screenshot(p)
    assert r.verdict == "PASS"
    assert r.evidence["text_area_ratio"] < 0.30


def test_hc_12_fail_on_text_heavy_image(tmp_path: Path) -> None:
    p = tmp_path / "text.png"
    _make_text_image(p)
    r = check_hc_12_text_screenshot(p)
    # text-heavy fixture should exceed 0.30 (or OCR override triggers on 0.20-0.40 band)
    assert r.verdict == "FAIL"


def test_hc_12_skip_when_cv2_unavailable(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    p = tmp_path / "any.png"
    _make_plain_image(p)
    monkeypatch.setattr(hc_checks, "_CV2_AVAILABLE", False)
    r = check_hc_12_text_screenshot(p)
    assert r.verdict == "SKIP"
    assert "cv2" in r.detail.lower()


def test_hc_12_fail_when_image_unreadable(tmp_path: Path) -> None:
    p = tmp_path / "bogus.png"
    p.write_bytes(b"not a real image")
    r = check_hc_12_text_screenshot(p)
    assert r.verdict == "FAIL"
    assert "unreadable" in r.detail.lower()


# ------------------------- run_all_hc_checks -------------------------


def test_run_all_hc_checks_returns_9_results(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # minimal valid-enough fixture so functions don't crash
    # HC-13/14 will SKIP because no channel field → _detect_channel returns None
    _write_json(tmp_path / "script.json", {"title": {"line1": "a", "line2": "b"}, "sections": [{"narration": "x"}]})
    _write_json(tmp_path / "subtitles_remotion.json", [{"startMs": 0, "endMs": 100, "words": ["x"]}])
    (tmp_path / "narration.mp3").write_bytes(b"fake")
    monkeypatch.setattr(hc_checks.subprocess, "run", _make_ffprobe_patch(0.1))
    _write_json(
        tmp_path / "gates.json",
        [{"gate_id": f"GATE-{i}", "verdict": "PASS"} for i in range(1, 6)],
    )
    _write_json(
        tmp_path / "scene-manifest.json",
        {"scenes": [{"image": f"i_{i}.jpg", "hash": f"h{i}"} for i in range(6)]},
    )
    results = run_all_hc_checks(tmp_path)
    # HC-1~7 + HC-6.5 (Phase 50-E cross-slug) + HC-8/9/10 (Phase 50-03) + HC-13 + HC-14
    assert len(results) == 13
    ids = [r.hc_id for r in results]
    assert ids == [
        "HC-1", "HC-2", "HC-3", "HC-4", "HC-5", "HC-6", "HC-6.5", "HC-7",
        "HC-8", "HC-9", "HC-10",
        "HC-13", "HC-14",
    ]
    # HC-8 (SKIP: LLM judge not wired)
    # HC-9 (SKIP: NLM pipeline artifacts absent)
    # HC-10 (SKIP: gate_results/ absent — pre-integration path)
    # HC-13/14 should SKIP (no channel detected)
    assert results[8].verdict == "SKIP"   # HC-8
    assert results[9].verdict == "SKIP"   # HC-9
    assert results[10].verdict == "SKIP"  # HC-10
    assert results[11].verdict == "SKIP"  # HC-13
    assert results[12].verdict == "SKIP"  # HC-14
    # hc_checks.json sink should be written
    assert (tmp_path / "hc_checks.json").exists()
    data = json.loads((tmp_path / "hc_checks.json").read_text(encoding="utf-8"))
    assert isinstance(data, list)
    assert len(data) == 13


def test_run_all_hc_checks_catches_per_check_exceptions(tmp_path: Path) -> None:
    # Empty directory — every check should FAIL or SKIP gracefully, not raise
    results = run_all_hc_checks(tmp_path)
    # HC-1~7 + HC-6.5 + HC-8/9/10 + HC-13 + HC-14
    assert len(results) == 13
    for r in results:
        assert isinstance(r, HCResult)
        assert r.verdict in {"PASS", "FAIL", "SKIP"}


def test_hcresult_to_dict() -> None:
    r = HCResult(hc_id="HC-1", verdict="PASS", detail="ok", evidence={"coverage_pct": 0.97})
    d = r.to_dict()
    assert d["hc_id"] == "HC-1"
    assert d["verdict"] == "PASS"
    assert d["evidence"]["coverage_pct"] == 0.97
