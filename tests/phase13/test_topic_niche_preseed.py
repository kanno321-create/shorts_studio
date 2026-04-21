"""Phase 13 — --topic + --niche pre-seed flag tests.

대표님 요청 주제로 쇼츠 제작 시 phase13_live_smoke.py 에 추가된 2개 flag
(`--topic` + `--niche`) 의 wrapping 동작을 Tier 1 (mock, 실 Claude CLI 미호출)
로 검증한다.

검증 대상:
- _PreSeededProducerInvoker 가 TREND/NICHE gate 에서 pre-seed 반환
- 나머지 11 gate 는 real invoker 로 delegate (mock 확인)
- _build_pipeline_with_seed 가 올바르게 wrap
- CLI validation (--topic 단독 또는 --niche 단독 → exit 7)
- _VALID_NICHE_TAGS 7 채널바이블 화이트리스트

CLAUDE.md 준수:
- 금기 #3 try-except 침묵 폴백 금지 — delegate 실패는 raise
- 필수 #7 한국어 존댓말 — error message + log "대표님"
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
RUNNER_PATH = REPO_ROOT / "scripts" / "smoke" / "phase13_live_smoke.py"


def _run_runner(args: list[str], timeout: int = 30) -> subprocess.CompletedProcess:
    """phase13_live_smoke.py subprocess helper (Windows cp949 대응)."""
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    return subprocess.run(
        [sys.executable, str(RUNNER_PATH), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        cwd=str(REPO_ROOT),
        env=env,
        timeout=timeout,
    )


# ---------------------------------------------------------------------------
# CLI validation
# ---------------------------------------------------------------------------


def test_topic_without_niche_exits_7():
    """--topic 만 주어지고 --niche 없으면 exit 7 (대표님 검증)."""
    result = _run_runner(["--topic", "외국범죄"])
    assert result.returncode == 7, (
        f"Expected rc=7, got rc={result.returncode}\nstderr:{result.stderr[-500:]}"
    )
    assert "--topic" in result.stderr
    assert "--niche" in result.stderr


def test_niche_without_topic_exits_7():
    """--niche 만 주어지고 --topic 없으면 exit 7."""
    result = _run_runner(["--niche", "incidents"])
    assert result.returncode == 7, (
        f"Expected rc=7, got rc={result.returncode}\nstderr:{result.stderr[-500:]}"
    )
    assert "대표님" in result.stderr


def test_both_topic_and_niche_dry_run_succeeds():
    """--topic + --niche 동시 지정 + dry-run → exit 0 + pre-seed log."""
    result = _run_runner([
        "--topic", "외국범죄,FBI 수사,인터폴",
        "--niche", "incidents",
    ])
    assert result.returncode == 0, (
        f"Expected rc=0, got rc={result.returncode}\nstderr:{result.stderr[-500:]}"
    )
    assert "주제 pre-seed 활성" in result.stderr, (
        "Pre-seed log line missing from stderr output"
    )
    assert "niche=incidents" in result.stderr
    assert "외국범죄" in result.stderr


def test_niche_choices_enforced_argparse():
    """잘못된 --niche 값 (7 채널바이블 외) → argparse error exit 2."""
    result = _run_runner([
        "--topic", "test",
        "--niche", "unknown_niche_xyz",
    ])
    # argparse choice error → rc=2
    assert result.returncode == 2, (
        f"Expected argparse error rc=2, got {result.returncode}"
    )
    assert "invalid choice" in result.stderr.lower()


def test_help_mentions_topic_and_niche_flags():
    """--help 에 --topic 과 --niche 플래그 + 7 채널바이블 list 명시."""
    result = _run_runner(["--help"])
    assert result.returncode == 0
    combined = result.stdout + result.stderr
    assert "--topic" in combined
    assert "--niche" in combined
    # 7 채널바이블 화이트리스트 명시
    for niche in ["incidents", "documentary", "humor", "politics", "trend", "wildlife"]:
        assert niche in combined, f"Niche '{niche}' missing from --help"


# ---------------------------------------------------------------------------
# _PreSeededProducerInvoker unit tests
# ---------------------------------------------------------------------------


def test_pre_seeded_invoker_returns_trend_keywords():
    """TREND gate 호출 시 대표님 지정 키워드 list 반환 (real invoker 호출 안 함)."""
    sys.path.insert(0, str(REPO_ROOT))
    from scripts.smoke.phase13_live_smoke import _PreSeededProducerInvoker

    def _mock_real_invoker(agent_name, gate, inputs):
        raise AssertionError(
            f"Real invoker must NOT be called for TREND/NICHE. called with {gate}"
        )

    invoker = _PreSeededProducerInvoker(
        real_invoker=_mock_real_invoker,
        topic_keywords=["외국범죄", "FBI 수사"],
        niche_tag="incidents",
        channel_bible_ref=".preserved/harvested/theme_bible_raw/incidents.md",
    )
    result = invoker("trend-collector", "TREND", {"session_id": "test"})
    assert result["gate"] == "TREND"
    assert result["verdict"] == "PASS"
    assert result["keywords"] == ["외국범죄", "FBI 수사"]
    assert result["niche_tag"] == "incidents"
    assert result["seeded"] is True
    assert "대표님" in result["decisions"][0]


def test_pre_seeded_invoker_returns_niche_bible_ref():
    """NICHE gate 호출 시 대표님 지정 채널바이블 ref 반환."""
    sys.path.insert(0, str(REPO_ROOT))
    from scripts.smoke.phase13_live_smoke import _PreSeededProducerInvoker

    def _mock_real_invoker(agent_name, gate, inputs):
        raise AssertionError(
            f"Real invoker must NOT be called for TREND/NICHE. called with {gate}"
        )

    invoker = _PreSeededProducerInvoker(
        real_invoker=_mock_real_invoker,
        topic_keywords=["외국범죄"],
        niche_tag="incidents",
        channel_bible_ref=".preserved/harvested/theme_bible_raw/incidents.md",
    )
    result = invoker("niche-classifier", "NICHE", {"trend_artifact": "foo"})
    assert result["gate"] == "NICHE"
    assert result["verdict"] == "PASS"
    assert result["niche_tag"] == "incidents"
    assert result["channel_bible_ref"].endswith("incidents.md")
    assert result["seeded"] is True


def test_pre_seeded_invoker_delegates_non_trend_niche_gates():
    """TREND/NICHE 외 11 gate 는 real invoker 로 delegate."""
    sys.path.insert(0, str(REPO_ROOT))
    from scripts.smoke.phase13_live_smoke import _PreSeededProducerInvoker

    call_log: list[tuple[str, str]] = []

    def _mock_real_invoker(agent_name, gate, inputs):
        call_log.append((agent_name, gate))
        return {"gate": gate, "verdict": "PASS", "from_real_invoker": True}

    invoker = _PreSeededProducerInvoker(
        real_invoker=_mock_real_invoker,
        topic_keywords=["외국범죄"],
        niche_tag="incidents",
        channel_bible_ref=".preserved/harvested/theme_bible_raw/incidents.md",
    )
    for gate in [
        "RESEARCH_NLM", "BLUEPRINT", "SCRIPT", "POLISH", "VOICE",
        "ASSETS", "ASSEMBLY", "THUMBNAIL", "METADATA", "UPLOAD", "MONITOR",
    ]:
        result = invoker("any_agent", gate, {})
        assert result.get("from_real_invoker") is True, (
            f"Gate {gate} should delegate to real invoker, got {result}"
        )
    # 11 gate 전수 delegate 확인
    assert len(call_log) == 11
    gates_called = {g for _, g in call_log}
    assert "TREND" not in gates_called, "TREND must be intercepted, not delegated"
    assert "NICHE" not in gates_called, "NICHE must be intercepted, not delegated"


def test_valid_niche_tags_whitelist():
    """_VALID_NICHE_TAGS 가 정확히 6개 (7 bibles 중 README 제외) 채널바이블 포함."""
    sys.path.insert(0, str(REPO_ROOT))
    from scripts.smoke.phase13_live_smoke import _VALID_NICHE_TAGS

    expected = {"documentary", "humor", "incidents", "politics", "trend", "wildlife"}
    assert _VALID_NICHE_TAGS == expected


def test_build_pipeline_with_seed_bypass_mode():
    """--topic + --niche 미지정 시 기본 _build_pipeline 경로로 (에이전트 자율)."""
    sys.path.insert(0, str(REPO_ROOT))
    from scripts.smoke.phase13_live_smoke import _build_pipeline_with_seed

    # topic/niche 가 None 이면 wrap 없이 phase11 기본 builder 호출 — 이 호출은
    # 실제 Claude CLI 실행하지 않고 단순히 pipeline 객체 생성까지만 수행.
    pipeline = _build_pipeline_with_seed(
        session_id="test_no_seed",
        state_root=Path("state"),
        topic_keywords=None,
        niche_tag=None,
    )
    assert pipeline is not None
    # 기본 producer_invoker 는 ClaudeAgentProducerInvoker (wrap 아님)
    from scripts.smoke.phase13_live_smoke import _PreSeededProducerInvoker
    assert not isinstance(pipeline.producer_invoker, _PreSeededProducerInvoker)


def test_build_pipeline_with_seed_wraps_when_both_set():
    """--topic + --niche 동시 지정 시 _PreSeededProducerInvoker 로 wrap."""
    sys.path.insert(0, str(REPO_ROOT))
    from scripts.smoke.phase13_live_smoke import (
        _build_pipeline_with_seed,
        _PreSeededProducerInvoker,
    )

    pipeline = _build_pipeline_with_seed(
        session_id="test_with_seed",
        state_root=Path("state"),
        topic_keywords=["외국범죄", "FBI"],
        niche_tag="incidents",
    )
    assert pipeline is not None
    assert isinstance(pipeline.producer_invoker, _PreSeededProducerInvoker)
    # 내부 상태 확인
    assert pipeline.producer_invoker._niche_tag == "incidents"
    assert "외국범죄" in pipeline.producer_invoker._topic_keywords
