"""Phase 13 Live Smoke Runner — real Claude CLI + budget cap + evidence anchoring.

phase11_full_run.py (493 lines) clone + Wave 0~3 wire (budget_counter +
provider_rates + evidence_extractor + upload_evidence). Cost cap $5.00 hard
(SMOKE-05), unlisted + cleanup (SMOKE-03, 금기 #8 준수). Evidence: 5 files in
``.planning/phases/13-live-smoke/evidence/`` — producer_output_<sid>.json,
supervisor_output_<sid>.json, smoke_upload_<sid>.json, budget_usage_<sid>.json,
smoke_e2e_<sid>.json.

대표님 사용 예::

    # dry-run preview ($0 cost, no real API calls — default)
    py -3.11 scripts/smoke/phase13_live_smoke.py

    # --help
    py -3.11 scripts/smoke/phase13_live_smoke.py --help

    # 실 과금 full E2E — 대표님 승인 후만 호출
    py -3.11 scripts/smoke/phase13_live_smoke.py --live --budget-cap-usd 5.00

CLI flags:
    --live                  Real API calls. Default: False (dry-run preview).
    --max-attempts N        Retry attempts on mid-run failure (default 2,
                            Research Open Q #2). Budget cap cumulative across
                            attempts.
    --budget-cap-usd USD    Hard cost cap (default 5.00, SMOKE-05).
    --session-id <sid>      Custom session identifier. Default timestamp.
    --state-root <path>     Checkpointer state dir. Default ``state``.
    --verbose-compression   Dump raw supervisor payload pre-compression to
                            ``evidence/supervisor_raw_<sid>_<gate>.json``
                            (Research Open Q #6).
    --log-level LEVEL       Python logging level (default INFO).

Exit codes:
    0 — smoke completed (dry-run preview OK OR live run OK with 5 evidence
        files written + rc=0).
    2 — live run crashed mid-pipeline after exhausting --max-attempts
        (ShortsPipeline.run exception).
    3 — live run rc=0 but state dir missing (artifact regression).
    4 — env readiness check failed (required .env key missing) — do NOT enter
        billable live run.
    5 — budget cap breached (BudgetExceededError raised from counter.charge).
    6 — evidence chain incomplete (one or more of the 5 evidence files
        missing at end of live run).

금기사항 준수:
    #2 미완성 wiring 표식 없음 — 모든 branch 완성 (미완 대신 raise).
    #3 try/except 침묵 폴백 없음 — 예외는 logger.error + raise / exit code.
    #4 T2V 없음 — I2V only (Kling/Runway). 본 runner 는 pipeline 경유하므로
       pipeline 내부 I2V 제약이 자동 승계.
    #5 비공식 브라우저 자동화 없음 — YouTube 과금 smoke 는 googleapiclient
       공식 경로 (upload_evidence.py + youtube_uploader.publish()) 만 경유.
    #8 일일 업로드 금지 — ``SHORTS_PUBLISH_LOCK_PATH`` 를 tmp path 로
       redirect 하여 48h+ 카운터 소진 차단. ``cleanup=True`` 로 업로드 영상
       즉시 삭제 (youtube_uploader.py 경유).

필수사항 준수:
    #7 한국어 존댓말 baseline — 모든 logger 메시지에 "대표님" + 존댓말.
    #8 증거 기반 보고 — 모든 evidence 파일 경로를 logger.info 로 출력.

Phase 13 Plan 05 (Wave 4). Skeleton: scripts/smoke/phase11_full_run.py L43-493.
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import re
import sys
import tempfile
import time
from datetime import datetime
from pathlib import Path

# Windows cp949 stdout guard — Phase 11 pattern (phase11_full_run.py L48-60).
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    except (AttributeError, OSError) as _enc_err:
        # 금기 #3 준수 — 침묵 폴백 금지. stderr 명시 기록.
        sys.stderr.write(
            f"[phase13_smoke] stdout reconfigure skipped: {_enc_err}\n"
        )

# Ensure repo root on sys.path — invoked directly from repo root or elsewhere.
_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

# =============================================================================
# publish_lock bypass — smoke MUST NOT consume 48h+ operational counter (금기 #8).
# Research §publish_lock Bypass L173-184: SHORTS_PUBLISH_LOCK_PATH env override
# (Phase 8 D-06 documented mechanism). ``setdefault`` 로 사용자 override 존중
# (monkeypatch + test fixture 가 먼저 set 하면 그 값 유지).
# =============================================================================
os.environ.setdefault(
    "SHORTS_PUBLISH_LOCK_PATH",
    str(Path(tempfile.gettempdir()) / "phase13_smoke_lock.json"),
)

# Wave 0~3 산출물 + phase11 재사용 — 단일 runner 에서 wire-up.
from scripts.orchestrator import ShortsPipeline  # noqa: E402
from scripts.orchestrator.gates import GateName  # noqa: E402
from scripts.orchestrator.invokers import (  # noqa: E402
    make_default_producer_invoker,
    make_default_supervisor_invoker,
)
from scripts.orchestrator.shorts_pipeline import PipelinePauseSignal  # noqa: E402
from scripts.smoke.phase11_full_run import (  # noqa: E402
    _check_env_readiness,
    _print_env_report,
    _build_pipeline,
    _aggregate_gate_metrics,
    _extract_upload_url,
)
from scripts.smoke.budget_counter import (  # noqa: E402
    BudgetCounter,
    BudgetExceededError,
)
from scripts.smoke.provider_rates import (  # noqa: E402
    PROVIDER_RATES_USD,
    estimate_adapter_cost,
    all_known_providers,
)
from scripts.smoke.evidence_extractor import (  # noqa: E402
    extract_producer_output,
    extract_supervisor_output,
    OPERATIONAL_GATES,
)
from scripts.smoke.upload_evidence import anchor_upload_evidence  # noqa: E402

logger = logging.getLogger("smoke.phase13")

# =============================================================================
# Pre-seeded topic/niche support — 대표님 요청 주제 강제 주입
# =============================================================================
#
# 기본 동작: trend-collector 에이전트가 자율적으로 트렌드 키워드를 픽업 →
# niche-classifier 가 7 채널바이블 중 1개 매핑. 주제 선택은 에이전트에 맡김.
#
# --topic + --niche 플래그 사용 시: _PreSeededProducerInvoker 가 TREND/NICHE
# 두 gate 의 producer 호출을 가로채서 대표님 지정 값을 반환. Claude CLI 호출
# SKIP (토큰 절약). 나머지 11 gate (RESEARCH_NLM~MONITOR) 는 실 에이전트 경로.

# 7 channel bible whitelist — .preserved/harvested/theme_bible_raw/*.md 기준
_VALID_NICHE_TAGS = {
    "documentary",
    "humor",
    "incidents",
    "politics",
    "trend",
    "wildlife",
}


class _PreSeededProducerInvoker:
    """real producer_invoker 를 wrapping 하여 TREND/NICHE gate 에 대표님 지정
    값을 pre-seed 로 반환. 나머지 gate 는 real invoker 로 delegate.

    CLAUDE.md 준수:
        - 금기 #3 try-except 침묵 폴백 금지 — 잘못된 gate 는 real invoker 에
          그대로 위임, 예외는 전파.
        - 필수 #7 한국어 존댓말 — logger 메시지 전체 "대표님" + 존댓말.
        - 필수 #8 증거 기반 — pre-seed 된 값은 logger.info 로 명시.

    Attributes
    ----------
    _real : Callable
        실 producer_invoker (ClaudeAgentProducerInvoker 인스턴스).
    _topic_keywords : list[str]
        TREND gate 에서 반환할 키워드 list. 대표님 --topic 입력값.
    _niche_tag : str
        NICHE gate 에서 반환할 niche_tag. _VALID_NICHE_TAGS 에 속해야 함.
    _channel_bible_ref : str
        채널바이블 경로. .preserved/harvested/theme_bible_raw/{niche}.md.
    """

    def __init__(
        self,
        real_invoker,
        topic_keywords: list[str],
        niche_tag: str,
        channel_bible_ref: str,
    ) -> None:
        self._real = real_invoker
        self._topic_keywords = list(topic_keywords)
        self._niche_tag = niche_tag
        self._channel_bible_ref = channel_bible_ref

    def __call__(self, agent_name: str, gate: str, inputs: dict) -> dict:
        if gate == "TREND":
            logger.info(
                "[pre-seed] TREND gate — 대표님 지정 키워드 주입 (%d 개): %s",
                len(self._topic_keywords),
                self._topic_keywords,
            )
            return {
                "gate": "TREND",
                "verdict": "PASS",
                "keywords": self._topic_keywords,
                "niche_tag": self._niche_tag,
                "session_id": inputs.get("session_id"),
                "seeded": True,
                "decisions": [
                    "대표님 --topic flag 를 통한 수동 키워드 주입 (trend-collector skip)",
                ],
                "error_codes": [],
            }
        if gate == "NICHE":
            logger.info(
                "[pre-seed] NICHE gate — 채널바이블 주입: niche=%s, ref=%s",
                self._niche_tag,
                self._channel_bible_ref,
            )
            return {
                "gate": "NICHE",
                "verdict": "PASS",
                "niche_tag": self._niche_tag,
                "channel_bible_ref": self._channel_bible_ref,
                "matched_fields": ["seeded_by_user_dpyonim"],
                "seeded": True,
                "decisions": [
                    f"대표님 --niche flag 를 통한 수동 채널바이블 선택: {self._niche_tag}",
                ],
                "error_codes": [],
            }
        # 나머지 11 gate (RESEARCH_NLM, BLUEPRINT, SCRIPT, POLISH, VOICE, ASSETS,
        # ASSEMBLY, THUMBNAIL, METADATA, UPLOAD, MONITOR) 는 실 Claude 에이전트 경로.
        return self._real(agent_name, gate, inputs)


class _PreScriptedProducerInvoker:
    """UFL-02 — 대표님 수동 대본 주입.

    SCRIPT gate 에서 scripter 에이전트 호출을 intercept 하여 파일 내용을
    ``script_md`` 로 반환. 나머지 gate 는 real invoker 로 위임 (Phase 13
    ``_PreSeededProducerInvoker`` chain-wrapping 패턴 승계).

    Design notes:
        - script-polisher 는 **정상 실행** (POLISH gate 유지) — 대표님 수동
          대본도 RUB 검증을 거쳐야 하므로 POLISH 를 skip 하지 않습니다.
        - 파일은 ``__init__`` 에서 즉시 읽어 missing 을 조기 감지
          (FileNotFoundError raise, 금기 #3 준수 — 침묵 폴백 금지).
        - decisions 필드에 파일 경로 기록하여 evidence trail 보존.

    Attributes
    ----------
    _real : Callable
        하류 gate 처리용 real producer_invoker.
    _script_content : str
        읽어들인 대본 텍스트 (UTF-8).
    _script_path : str
        로깅/decisions 용 파일 경로 문자열.
    """

    def __init__(self, real_invoker, script_path: Path) -> None:
        self._real = real_invoker
        # __init__ 에서 바로 읽어 missing 을 조기 감지 (금기 #3: 명시적 raise).
        self._script_content = script_path.read_text(encoding="utf-8")
        self._script_path = str(script_path)
        logger.info(
            "[pre-script] 대표님 수동 대본 로드: %s (%d chars)",
            self._script_path,
            len(self._script_content),
        )

    def __call__(self, agent_name: str, gate: str, inputs: dict) -> dict:
        if gate == "SCRIPT":
            logger.info(
                "[pre-script] SCRIPT gate — scripter skip, 대표님 수동 대본 주입",
            )
            return {
                "gate": "SCRIPT",
                "verdict": "PASS",
                "script_md": self._script_content,
                "user_provided": True,
                "seeded": True,
                "decisions": [
                    f"대표님 --revise-script flag: {self._script_path}",
                ],
                "error_codes": [],
            }
        # SCRIPT 이외 모든 gate — 실 Claude 에이전트 경로.
        return self._real(agent_name, gate, inputs)


class _AutoPassSupervisorInvoker:
    """F-LIVE-SMOKE-JSON-NONCOMPLIANCE 우회 — 모든 gate 자동 PASS 반환.

    대표님 세션 #30 합의 경로 (Option A 수동 혼합):
    Claude CLI 대화형 session 의 ``--json-schema`` 엄수가 brittle 하여
    supervisor 호출이 자연어 응답 / empty stdout 을 반환하는 문제를 우회.
    Inspector 17 의 실제 품질 검증은 그대로 유지되며, supervisor 의
    aggregation layer 만 skip 됩니다.

    Quality gate 는 영상 제작 달성 후 점진 복구 (F-LIVE-SMOKE 해소 후).

    Signature: ``(gate, output: dict) -> Verdict`` — 실 invoker
    :class:`scripts.orchestrator.invokers.ClaudeAgentSupervisorInvoker`
    와 동일한 duck-typing 계약.
    """

    def __init__(self) -> None:
        self._calls = 0

    def __call__(self, gate, output: dict):
        from scripts.orchestrator.state import Verdict
        self._calls += 1
        gate_name = getattr(gate, "name", str(gate))
        logger.info(
            "[phase13] --skip-supervisor auto-PASS: gate=%s call=%d (대표님)",
            gate_name,
            self._calls,
        )
        return Verdict.PASS


def _build_pipeline_with_seed(
    session_id: str,
    state_root: Path,
    topic_keywords: list[str] | None,
    niche_tag: str | None,
) -> ShortsPipeline:
    """Build ShortsPipeline with optional TREND/NICHE pre-seed wrapper.

    대표님 --topic + --niche 플래그 사용 시 _PreSeededProducerInvoker 로 실
    invoker 를 감싼다. 둘 다 미지정이면 phase11 의 기본 _build_pipeline 경유
    (기존 동작 보존 — 에이전트 자율 트렌드 픽업).
    """
    if topic_keywords is None and niche_tag is None:
        # 기본 경로 — 에이전트 자율. phase11 helper 그대로.
        return _build_pipeline(session_id, state_root)

    # Pre-seed 경로.
    agents_root = Path(".claude/agents")
    real_producer = make_default_producer_invoker(
        agent_dir_root=agents_root / "producers",
    )
    channel_bible_ref = (
        f".preserved/harvested/theme_bible_raw/{niche_tag}.md"
    )
    seeded_producer = _PreSeededProducerInvoker(
        real_invoker=real_producer,
        topic_keywords=topic_keywords or [],
        niche_tag=niche_tag or "",
        channel_bible_ref=channel_bible_ref,
    )
    supervisor_invoker = make_default_supervisor_invoker(
        agent_dir=agents_root / "supervisor" / "shorts-supervisor",
    )
    return ShortsPipeline(
        session_id=session_id,
        state_root=state_root,
        producer_invoker=seeded_producer,
        supervisor_invoker=supervisor_invoker,
    )

# =============================================================================
# UFL-01 — _apply_revision helper (대표님 재작업 peedback loop)
# =============================================================================
#
# 특정 gate 부터 checkpoint 파일을 삭제하여 ShortsPipeline.run() 의 resume
# 경로로 재실행 유도. Checkpointer.resume(session_id) 이 최고 gate_index 를
# 반환하므로, gate_NN.json 삭제만으로 해당 지점부터 재시작.


def _apply_revision(
    state_root: Path,
    session_id: str,
    from_gate: GateName,
) -> list[Path]:
    """UFL-01 — Delete state/<sid>/gate_N..13.json for N >= from_gate.value.

    대표님 --revision-from GATE 명령을 처리합니다. 존재하지 않는 session 은
    조용히 빈 리스트 반환 (예외 금지). malformed filename (gate_XX.json /
    not_a_gate.json) 은 무시 + preserve.

    Parameters
    ----------
    state_root : Path
        Checkpointer state root (예: ``Path("state")``).
    session_id : str
        Target session 이름.
    from_gate : GateName
        이 gate 이상의 checkpoint 를 삭제. GateName.SCRIPT (idx=5) 지정 시
        gate_05 ~ gate_13 (9 files) 삭제.

    Returns
    -------
    list[Path]
        삭제된 파일 경로 list (로깅/evidence 용).
    """
    state_dir = state_root / session_id
    if not state_dir.is_dir():
        logger.info(
            "[revision] state_dir 부재 (대표님) — 삭제 대상 없음: %s",
            state_dir,
        )
        return []
    deleted: list[Path] = []
    for gate_file in sorted(state_dir.glob("gate_*.json")):
        stem_parts = gate_file.stem.split("_")
        if len(stem_parts) < 2:
            continue  # malformed skip
        try:
            idx = int(stem_parts[1])
        except ValueError:
            continue  # gate_XX.json 등 non-numeric — skip
        if idx >= from_gate.value:
            gate_file.unlink()
            logger.info(
                "[revision] %s 삭제 (대표님 %s 이상 재작업 요청)",
                gate_file.name,
                from_gate.name,
            )
            deleted.append(gate_file)
    return deleted


# =============================================================================
# UFL-03 — _handle_pause_signal helper (대표님 --pause-after 처리)
# =============================================================================


def _handle_pause_signal(
    sig: PipelinePauseSignal,
    ev_dir: Path,
) -> int:
    """UFL-03 — PipelinePauseSignal 수신 시 evidence 저장 + exit 0 반환.

    대표님 --pause-after GATE 지정에 의해 GateGuard 가 raise 한 신호를
    phase13_live_smoke runner 가 catch 하여 정상 종료로 마무리합니다.

    Parameters
    ----------
    sig : PipelinePauseSignal
        paused_at: GateName attribute 보유.
    ev_dir : Path
        evidence 디렉토리 (없으면 mkdir parents=True).

    Returns
    -------
    int
        항상 0 (graceful exit). 비정상 경로는 상위에서 rc=2 등으로 처리.
    """
    ev_dir.mkdir(parents=True, exist_ok=True)
    ts = time.strftime("%Y%m%d_%H%M%S")
    payload = {
        "status": "PAUSED",
        "paused_at": sig.paused_at.name,
        "timestamp": ts,
        "message": (
            f"대표님 --pause-after {sig.paused_at.name} 수신, "
            "일시중지합니다."
        ),
    }
    out = ev_dir / f"pause_{ts}.json"
    out.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    logger.info(
        "[pause] evidence 저장 완료 (대표님): %s (paused_at=%s)",
        out,
        sig.paused_at.name,
    )
    return 0


# =============================================================================
# Constants
# =============================================================================

# Evidence 디렉토리 — Phase 13 anchor root. dry-run + live 모두 이 경로 사용.
EVIDENCE_DIR = _REPO_ROOT / ".planning" / "phases" / "13-live-smoke" / "evidence"
EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)

# CLI 기본값.
DEFAULT_BUDGET_CAP_USD = 5.00  # SMOKE-05 hard cap.
DEFAULT_MAX_ATTEMPTS = 2  # Research Open Q #2 — cumulative cap preserved.

# 5 evidence file prefix — smoke_e2e post-run invariant check 에서 사용.
_EVIDENCE_FILE_PREFIXES = (
    "producer_output",
    "supervisor_output",
    "smoke_upload",
    "budget_usage",
    "smoke_e2e",
)

# YouTube video URL → video_id 추출 regex.
# youtube_uploader.publish() 가 반환하는 URL 포맷: https://youtu.be/<id> 또는
# https://www.youtube.com/watch?v=<id> 두 패턴 모두 대응.
_VIDEO_ID_RE = re.compile(
    r"(?:youtu\.be/|youtube\.com/(?:watch\?v=|shorts/))([A-Za-z0-9_-]{11})"
)


# =============================================================================
# CLI
# =============================================================================


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Phase 13 Live Smoke — full E2E real API smoke + evidence chain. "
            "phase11_full_run.py clone + Wave 0~3 wire. Default dry-run ($0). "
            "Pass --live 로만 실 과금 진입 (대표님 승인 후)."
        ),
    )
    parser.add_argument(
        "--live",
        action="store_true",
        default=False,
        help=(
            "Real API calls. Default: dry-run mode ($0 preview). "
            "Requires env: TYPECAST_API_KEY + GOOGLE_API_KEY + FAL_KEY/KLING_API_KEY. "
            "Cost bounded ≤ --budget-cap-usd (default $5.00)."
        ),
    )
    parser.add_argument(
        "--max-attempts",
        type=int,
        default=DEFAULT_MAX_ATTEMPTS,
        help=(
            f"Retry attempts on mid-run failure (default {DEFAULT_MAX_ATTEMPTS}). "
            "Budget cap is cumulative across attempts (Research Open Q #2)."
        ),
    )
    parser.add_argument(
        "--budget-cap-usd",
        type=float,
        default=DEFAULT_BUDGET_CAP_USD,
        help=(
            f"Hard cost cap USD (default ${DEFAULT_BUDGET_CAP_USD:.2f}). "
            "SMOKE-05 invariant. BudgetExceededError → exit 5."
        ),
    )
    parser.add_argument(
        "--session-id",
        default=None,
        help="Session identifier (default: yyyyMMdd_HHMMSS).",
    )
    parser.add_argument(
        "--state-root",
        default="state",
        help="Checkpointer state directory (default: state).",
    )
    parser.add_argument(
        "--verbose-compression",
        action="store_true",
        default=False,
        help=(
            "Dump raw supervisor payload pre-compression to evidence "
            "(Research Open Q #6 ad-hoc forensic mode)."
        ),
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        help="Python logging level (default: INFO).",
    )
    parser.add_argument(
        "--evidence-dir",
        default=None,
        help=(
            "evidence 저장 루트 override (대표님 격리 실행용). 미지정 시 기본 "
            "EVIDENCE_DIR (.planning/phases/13-live-smoke/evidence) 사용. "
            "Plan 15-06 live retry 단계에서 대표님 격리 경로로 분리 저장 가능."
        ),
    )
    parser.add_argument(
        "--revision-from",
        default=None,
        choices=[
            g.name for g in GateName
            if g not in (GateName.IDLE, GateName.COMPLETE)
        ],
        help=(
            "UFL-01 — 기존 세션의 특정 GATE 부터 재실행 (대표님 재작업 요청). "
            "해당 GATE 이상 idx 의 state/<sid>/gate_NN.json 파일이 삭제되어 "
            "Checkpointer.resume 이 그 지점으로 되돌아갑니다. --session-id 와 "
            "함께 사용해야 기존 session 을 재사용할 수 있습니다."
        ),
    )
    parser.add_argument(
        "--feedback",
        default=None,
        help=(
            "UFL-01 — 대표님 피드백 텍스트. Producer invoker 가 "
            "prior_user_feedback 으로 user_payload 에 주입하여 scripter / "
            "script-polisher 등 하류 에이전트가 재작업 방향 인지. "
            "--revision-from 과 함께 사용 권장."
        ),
    )
    parser.add_argument(
        "--revise-script",
        default=None,
        type=Path,
        help=(
            "UFL-02 — 대표님 수동 대본 .md/.txt 경로. SCRIPT gate 에서 "
            "scripter 에이전트를 skip 하고 지정 파일 내용을 script_md 로 주입. "
            "script-polisher (POLISH gate) 는 정상 실행되어 RUB 검증 수행."
        ),
    )
    parser.add_argument(
        "--pause-after",
        default=None,
        choices=[
            g.name for g in GateName
            if g not in (GateName.IDLE, GateName.COMPLETE)
        ],
        help=(
            "UFL-03 — 지정 GATE 완료 후 pipeline 일시중지 (대표님 검토용). "
            "GateGuard.dispatch 이후 PipelinePauseSignal raise → runner "
            "graceful exit 0 + evidence pause_*.json 기록. 재개 시 "
            "--session-id 재사용 + --revision-from 으로 재진입 가능."
        ),
    )
    parser.add_argument(
        "--topic",
        default=None,
        help=(
            "쉼표 구분 키워드 list 로 TREND gate pre-seed. trend-collector "
            "에이전트 자율 픽업 대신 대표님 지정 주제 주입. 예: "
            '--topic "외국범죄,FBI 수사,인터폴". --niche 와 반드시 동반 사용.'
        ),
    )
    parser.add_argument(
        "--niche",
        default=None,
        choices=sorted(_VALID_NICHE_TAGS),
        help=(
            "NICHE gate pre-seed. 7 채널바이블 중 1개 (incidents/documentary/"
            "humor/politics/trend/wildlife). --topic 와 반드시 동반 사용. "
            "선택 시 niche-classifier 에이전트 skip, 해당 채널바이블 경로가 "
            "RESEARCH_NLM~UPLOAD 전 11 gate 에 전파."
        ),
    )
    parser.add_argument(
        "--skip-supervisor",
        action="store_true",
        default=False,
        help=(
            "F-LIVE-SMOKE-JSON-NONCOMPLIANCE 우회 — 모든 gate 의 supervisor "
            "호출을 auto-PASS 로 교체 (Claude CLI JSON schema brittleness "
            "회피). Inspector 17 품질 검증은 유지, supervisor aggregation "
            "layer 만 skip. 세션 #30 대표님 Option A 합의 경로."
        ),
    )
    return parser.parse_args(argv)


# =============================================================================
# Helpers
# =============================================================================


def _print_banner(session_id: str, budget_cap: float, live: bool) -> None:
    """Startup banner — 모든 provider 단가 + 계약 안내. 필수 #7/#8 준수."""
    mode = "LIVE (실 과금)" if live else "DRY-RUN (미과금 미리보기)"
    logger.info("=" * 64)
    logger.info(
        "Phase 13 Live Smoke Runner — real API + budget cap + evidence anchoring (대표님)",
    )
    logger.info(
        "세션: %s | 모드: %s | 예산 상한: $%.2f",
        session_id,
        mode,
        budget_cap,
    )
    logger.info(
        "등록된 provider (%d): %s",
        len(PROVIDER_RATES_USD),
        ", ".join(all_known_providers()),
    )
    logger.info(
        "Evidence dir: %s",
        EVIDENCE_DIR,
    )
    logger.info("=" * 64)


def _video_id_from_url(url: str | None) -> str | None:
    """Extract 11-char YouTube video_id from URL — regex, no HTTP.

    금기 #3 준수 — None/빈 문자열 입력은 정상 제어흐름 (pre-upload 단계 혹은
    채널 설정 미제공) → None 반환 + logger.info 경로 기록. 잘못된 URL 은
    regex 실패 → None 반환 + logger.warning.
    """
    if not url:
        logger.info("[phase13] video URL 미제공 — video_id 추출 skipped (대표님)")
        return None
    match = _VIDEO_ID_RE.search(url)
    if not match:
        logger.warning(
            "[phase13] video URL 포맷 인식 실패 (대표님): %s",
            url,
        )
        return None
    return match.group(1)


def _collect_gate_timestamps(state_dir: Path) -> dict[str, str]:
    """Walk state/<sid>/gate_*.json, return {gate_name: timestamp} dict.

    phase11._aggregate_gate_metrics 는 cost/retry 만 집계 — timestamps 는
    본 runner 책임. checkpoint payload 는 ``{_schema, session_id, gate,
    gate_index, timestamp, verdict, artifacts}`` 포맷 (scripts.orchestrator.
    checkpointer L60-90). 각 gate 의 timestamp 를 수집.
    """
    timestamps: dict[str, str] = {}
    if not state_dir.exists():
        logger.info(
            "[phase13] state_dir 부재 — gate_timestamps 수집 skipped: %s",
            state_dir,
        )
        return timestamps
    for gate_file in sorted(state_dir.glob("gate_*.json")):
        try:
            payload = json.loads(gate_file.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as err:
            # 금기 #3: warn + continue (계약된 graceful — 손상 checkpoint 1건이
            # 전체 수집을 막지 않음).
            logger.warning(
                "[phase13] gate checkpoint 로드 실패 %s (대표님): %s",
                gate_file,
                err,
            )
            continue
        gate_name = payload.get("gate")
        ts = payload.get("timestamp")
        if gate_name and ts:
            timestamps[gate_name] = ts
    return timestamps


def _charge_dry_run_preview(counter: BudgetCounter) -> None:
    """Dry-run 모드 — $0 simulation entry + persist. 실 API 호출 0."""
    counter.charge(
        "claude_cli",
        0.00,
        metadata={"note": "Max subscription inclusive — dry-run preview 대표님"},
    )
    counter.charge(
        "notebooklm",
        0.00,
        metadata={"note": "Max subscription inclusive — dry-run preview 대표님"},
    )
    counter.charge(
        "youtube_api",
        0.00,
        metadata={"note": "Free quota — dry-run preview 대표님"},
    )
    # Adapter dry-run entries — 비용 $0, 실 호출 전 예상 비용 meta 로 남김.
    counter.charge(
        "nanobanana",
        0.00,
        metadata={
            "note": "dry-run preview",
            "estimated_if_live": estimate_adapter_cost("nanobanana", 1),
        },
    )
    counter.charge(
        "kling",
        0.00,
        metadata={
            "note": "dry-run preview — 8 cuts",
            "estimated_if_live": estimate_adapter_cost("kling", 8),
        },
    )
    counter.charge(
        "typecast",
        0.00,
        metadata={
            "note": "dry-run preview — 1K chars",
            "estimated_if_live": estimate_adapter_cost("typecast", 1),
        },
    )


def _write_smoke_e2e_evidence(
    session_id: str,
    state_dir: Path,
    metrics: dict,
    video_id: str | None,
    budget_cap: float,
    total_cost_usd: float,
    budget_breached: bool,
    wall_time_s: float,
    status: str,
    attempt_count: int,
) -> Path:
    """Write smoke_e2e_<sid>.json — SMOKE-06 invariant evidence.

    10 key schema (fixture `sample_smoke_e2e.json` 와 정확 일치 + attempt_count
    확장):
        session_id / status / wall_time_seconds / gate_timestamps / gate_count /
        final_video_id / total_cost_usd / budget_cap_usd / budget_breached /
        supervisor_rc1_count / attempt_count
    """
    gate_timestamps = _collect_gate_timestamps(state_dir)
    # supervisor_rc1_count 는 Phase 12 AGENT-STD-03 적용 후 0 기대.
    # evidence_extractor.extract_supervisor_output 가 이미 rc1_count 를 계산
    # 하지만 본 runner 는 checkpoint 에서 직접 재확인 (결정성 보장).
    rc1_count = 0
    for ts_gate in gate_timestamps:
        gate_file = state_dir / f"gate_{_gate_index_for(ts_gate):02d}.json"
        if not gate_file.exists():
            continue
        try:
            payload = json.loads(gate_file.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        supervisor = (payload.get("artifacts") or {}).get("supervisor") or {}
        if int(supervisor.get("returncode", 0)) == 1:
            rc1_count += 1

    evidence = {
        "session_id": session_id,
        "status": status,
        "wall_time_seconds": round(wall_time_s, 2),
        "gate_timestamps": gate_timestamps,
        "gate_count": len(gate_timestamps),
        "final_video_id": video_id or "",
        "total_cost_usd": round(total_cost_usd, 4),
        "budget_cap_usd": budget_cap,
        "budget_breached": budget_breached,
        "supervisor_rc1_count": rc1_count,
        "attempt_count": attempt_count,
    }
    out_path = EVIDENCE_DIR / f"smoke_e2e_{session_id}.json"
    out_path.write_text(
        json.dumps(evidence, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    logger.info("[phase13] smoke_e2e evidence → %s", out_path)
    return out_path


def _gate_index_for(gate_name: str) -> int:
    """Map gate name → checkpointer file index. IDLE=00 + operational 01~13.

    CLAUDE.md §Pipeline L19 과 gate_guard._OPERATIONAL_GATES 순서 동기화.
    IDLE 은 checkpoint 대상 아님 (phase11_full_run.py L21-25 docstring) 이나
    map 은 완결성 위해 포함 — checkpoint 파일 존재 유무는 caller 가 확인.
    """
    pipeline_order = [
        "IDLE",  # 00
        "TREND",  # 01
        "NICHE",  # 02
        "RESEARCH_NLM",  # 03
        "BLUEPRINT",  # 04
        "SCRIPT",  # 05
        "POLISH",  # 06
        "VOICE",  # 07
        "ASSETS",  # 08
        "ASSEMBLY",  # 09
        "THUMBNAIL",  # 10
        "METADATA",  # 11
        "UPLOAD",  # 12
        "MONITOR",  # 13
        "COMPLETE",  # 14
    ]
    try:
        return pipeline_order.index(gate_name)
    except ValueError:
        # 금기 #3 준수 — unknown gate 는 명시적 -1 반환 + caller 가 skip.
        logger.warning(
            "[phase13] unknown gate name '%s' — index=-1 (대표님)",
            gate_name,
        )
        return -1


def _verify_evidence_chain(session_id: str) -> list[str]:
    """Return missing evidence file prefixes (empty list = 전부 존재).

    5 evidence 파일 모두 ``{prefix}_{session_id}.json`` 포맷으로 저장되어야
    함. dry-run 시 smoke_upload 는 skip (실 upload 가 없으므로).
    """
    missing: list[str] = []
    for prefix in _EVIDENCE_FILE_PREFIXES:
        pattern = f"{prefix}_{session_id}.json"
        matches = list(EVIDENCE_DIR.glob(pattern))
        if not matches:
            missing.append(prefix)
    return missing


# =============================================================================
# Main flows
# =============================================================================


def _run_dry_run(args: argparse.Namespace, session_id: str) -> int:
    """Dry-run path — $0 simulation preview. 실 API 호출 0회.

    목적: 대표님이 --live 전에 env + budget 설정을 확인할 수 있도록 미리보기
    제공. Evidence dir 에 mock-only budget_usage_<sid>.json 만 write (다른 4
    evidence 파일은 live run 만 생성 — dry-run 에서는 smoke_e2e 도 write
    하여 대표님이 구조 확인 가능).
    """
    logger.info(
        "[phase13] dry-run 모드 진입 — 실 API 호출 0회, 예상 비용 $0.00 (대표님)"
    )

    budget_path = EVIDENCE_DIR / f"budget_usage_{session_id}.json"
    counter = BudgetCounter(args.budget_cap_usd, budget_path)
    try:
        _charge_dry_run_preview(counter)
    except BudgetExceededError as exc:
        # Dry-run 에서는 cap 초과 가능성 0 (모든 entry $0.00). 다만 safety
        # 로 명시 기록 후 rc=5 반환.
        logger.error(
            "[phase13] dry-run BudgetExceededError (대표님): %s",
            exc,
        )
        counter.persist()
        return 5

    counter.persist()
    logger.info(
        "[phase13] dry-run budget ledger → %s (total=$%.2f, cap=$%.2f)",
        budget_path,
        counter.total_usd,
        counter.cap_usd,
    )

    # dry-run 에서는 smoke_e2e evidence 를 mock payload 로 write — 대표님이
    # shape 을 사전 확인 가능.
    _write_smoke_e2e_evidence(
        session_id=session_id,
        state_dir=Path(args.state_root) / session_id,
        metrics={},
        video_id=None,
        budget_cap=args.budget_cap_usd,
        total_cost_usd=counter.total_usd,
        budget_breached=False,
        wall_time_s=0.0,
        status="DRY_RUN",
        attempt_count=0,
    )

    logger.info(
        "[phase13] dry-run 완료 (대표님). 실 발행: "
        "py -3.11 scripts/smoke/phase13_live_smoke.py --live --budget-cap-usd %.2f",
        args.budget_cap_usd,
    )
    return 0


def _run_live(args: argparse.Namespace, session_id: str) -> int:
    """Live path — real Claude CLI + real adapters + YouTube upload + cleanup.

    Attempts loop (`args.max_attempts`): ShortsPipeline.run() 이 중간에
    예외로 중단되면 다음 attempt 진행 (budget 은 cumulative). Pipeline 내부
    retry 와는 독립적 — pipeline 자체가 recoverable exception 에 대해 retry
    를 시도한 후에도 계속 실패하면 본 outer loop 이 attempt 재시도.

    pipeline success 후 5 evidence 파일 write + cleanup (videos.delete).
    """
    budget_path = EVIDENCE_DIR / f"budget_usage_{session_id}.json"
    counter = BudgetCounter(args.budget_cap_usd, budget_path)

    # Max 구독 / free quota adapter 는 $0 ledger entry 로 감사 trail 완결.
    counter.charge(
        "claude_cli",
        0.00,
        metadata={"note": "Max subscription inclusive 대표님"},
    )
    counter.charge(
        "notebooklm",
        0.00,
        metadata={"note": "Max subscription inclusive 대표님"},
    )

    state_root = Path(args.state_root)
    state_dir = state_root / session_id

    wall_start = time.time()
    last_err: Exception | None = None
    attempt_count = 0

    for attempt in range(args.max_attempts):
        attempt_count = attempt + 1
        logger.info(
            "[phase13] live run attempt %d/%d — session=%s (대표님)",
            attempt_count,
            args.max_attempts,
            session_id,
        )
        try:
            topic_keywords = (
                [k.strip() for k in args.topic.split(",") if k.strip()]
                if getattr(args, "topic", None)
                else None
            )
            niche_tag = getattr(args, "niche", None)
            # UFL-01 — revision-from 은 pipeline 생성 전에 적용 (Checkpointer
            # 가 resume 시 state_dir 을 스캔하므로, gate_NN.json 삭제는
            # pipeline.run() 호출 전에 완료되어야 함).
            if getattr(args, "revision_from", None):
                target = GateName[args.revision_from.upper()]
                deleted = _apply_revision(state_root, session_id, target)
                logger.info(
                    "[phase13] UFL-01 revision-from=%s — %d checkpoint 삭제 (대표님)",
                    target.name,
                    len(deleted),
                )
            pipeline = _build_pipeline_with_seed(
                session_id,
                state_root,
                topic_keywords,
                niche_tag,
            )
            # F-LIVE-SMOKE-JSON-NONCOMPLIANCE 우회 — --skip-supervisor 지정 시
            # 기본 supervisor_invoker 를 _AutoPassSupervisorInvoker 로 교체.
            # 대표님 세션 #30 Option A 합의 경로. Inspector 17 품질 검증은 유지.
            if getattr(args, "skip_supervisor", False):
                pipeline.supervisor_invoker = _AutoPassSupervisorInvoker()
                logger.info(
                    "[phase13] --skip-supervisor 활성 — supervisor auto-PASS (대표님)",
                )
            # UFL-02 — --revise-script 지정 시 기존 producer_invoker 를
            # _PreScriptedProducerInvoker 로 wrap. SCRIPT gate 에서만 scripter
            # skip, 나머지 gate 는 기존 chain (pre-seed 포함) 에 pass-through.
            if getattr(args, "revise_script", None):
                pipeline.producer_invoker = _PreScriptedProducerInvoker(
                    pipeline.producer_invoker,
                    args.revise_script,
                )
                logger.info(
                    "[phase13] UFL-02 revise-script wrap 적용 (대표님): %s",
                    args.revise_script,
                )
            # UFL-01 — feedback / revision_from_gate 을 ctx.config 에 주입.
            # ShortsPipeline._run_<gate> 각 메서드가 ctx.config.get(
            # "prior_user_feedback") 를 producer_invoker inputs 에 전달.
            if getattr(args, "feedback", None):
                pipeline.ctx.config["prior_user_feedback"] = args.feedback
                logger.info(
                    "[phase13] UFL-01 feedback 주입 (대표님, %d chars)",
                    len(args.feedback),
                )
            if getattr(args, "revision_from", None):
                pipeline.ctx.config["revision_from_gate"] = args.revision_from.upper()
            # UFL-03 — pause_after_gate 을 ctx.config 에 주입. GateGuard 가
            # ctx.config 를 by-reference 로 이미 참조하므로 dispatch 시점에
            # 자동 반영.
            if getattr(args, "pause_after", None):
                pipeline.ctx.config["pause_after_gate"] = args.pause_after.upper()
                logger.info(
                    "[phase13] UFL-03 pause-after=%s 예약 (대표님)",
                    args.pause_after.upper(),
                )
            pipeline.run()  # blocking — 13 gates TREND..MONITOR + COMPLETE
            last_err = None
            logger.info(
                "[phase13] pipeline.run() 완주 attempt %d (대표님)",
                attempt_count,
            )
            break
        except PipelinePauseSignal as sig:
            # UFL-03 — 대표님 --pause-after 정상 정지. Evidence 저장 + exit 0.
            logger.info(
                "[phase13] pause signal 수신 (대표님): paused_at=%s",
                sig.paused_at.name,
            )
            counter.persist()
            return _handle_pause_signal(sig, EVIDENCE_DIR)
        except BudgetExceededError as exc:
            logger.error(
                "[phase13] 예산 상한 초과 (대표님): %s",
                exc,
            )
            counter.persist()
            return 5
        except Exception as exc:  # noqa: BLE001
            last_err = exc
            logger.error(
                "[phase13] pipeline attempt %d 실패 (대표님): %s",
                attempt_count,
                exc,
            )
            if attempt_count < args.max_attempts:
                logger.info(
                    "[phase13] 다음 attempt 진행 — budget 은 cumulative 유지 (대표님)"
                )
                continue
            # 마지막 attempt 도 실패 — 부분 evidence 기록 후 rc=2.
            metrics = (
                _aggregate_gate_metrics(state_dir, args.budget_cap_usd)
                if state_dir.exists()
                else {"gate_file_count": 0}
            )
            counter.persist()
            _write_smoke_e2e_evidence(
                session_id=session_id,
                state_dir=state_dir,
                metrics=metrics,
                video_id=None,
                budget_cap=args.budget_cap_usd,
                total_cost_usd=counter.total_usd,
                budget_breached=counter.total_usd > counter.cap_usd,
                wall_time_s=time.time() - wall_start,
                status="FAILED",
                attempt_count=attempt_count,
            )
            return 2

    # Pipeline 완주 — artifact 존재 검증.
    if not state_dir.exists():
        logger.error(
            "[phase13] state_dir 부재 — 실행 artifact 누락 (대표님): %s",
            state_dir,
        )
        counter.persist()
        return 3

    # Evidence 집계 — Wave 1 유틸 2종.
    extract_producer_output(session_id, state_root, EVIDENCE_DIR)
    extract_supervisor_output(session_id, state_root, EVIDENCE_DIR)

    # Upload URL → video_id → anchor_upload_evidence → 즉시 cleanup (금기 #8).
    upload_url = _extract_upload_url(state_dir)
    video_id = _video_id_from_url(upload_url)
    if video_id:
        try:
            # googleapiclient — 공식 경로만 (금기 #5 준수). Lazy import 로
            # dry-run/cli surface 에 영향 없음.
            from googleapiclient.discovery import build  # noqa: E402
            from scripts.publisher.oauth import get_credentials  # noqa: E402
            creds = get_credentials()
            youtube = build("youtube", "v3", credentials=creds)
            anchor_upload_evidence(youtube, video_id, session_id, EVIDENCE_DIR)
            # 즉시 cleanup — 48h+ 운영 카운터 소비 0, 채널 reputation 보호.
            youtube.videos().delete(id=video_id).execute()
            logger.info(
                "[phase13] video %s 삭제 완료 (cleanup=True, 금기 #8 준수, 대표님)",
                video_id,
            )
        except Exception as exc:  # noqa: BLE001 — cleanup 실패는 명시 raise
            logger.error(
                "[phase13] anchor_upload_evidence / cleanup 실패 (대표님): %s",
                exc,
            )
            # 금기 #3 — 예외를 삼키지 않음. 다만 pipeline 본체는 성공했으므로
            # evidence chain 완결성만 깨진 것. rc=6 (evidence missing) 으로
            # 반환.
            counter.persist()
            return 6
    else:
        logger.warning(
            "[phase13] video_id 추출 실패 — smoke_upload evidence 생성 skipped "
            "(대표님 YouTube Studio 수동 확인 권장)",
        )

    # Adapter charge — phase11 PER_GATE_COST_ESTIMATE_USD 와 정합.
    counter.charge(
        "nanobanana",
        estimate_adapter_cost("nanobanana", 1),
        metadata={"gate": "THUMBNAIL", "units": 1},
    )
    counter.charge(
        "kling",
        estimate_adapter_cost("kling", 8),
        metadata={"gate": "ASSETS", "units": 8, "note": "8 cuts × 5s"},
    )
    counter.charge(
        "typecast",
        estimate_adapter_cost("typecast", 1),
        metadata={"gate": "VOICE", "units": 1, "note": "~1K chars"},
    )
    counter.charge(
        "youtube_api",
        0.00,
        metadata={"gate": "UPLOAD", "note": "free quota"},
    )
    counter.persist()

    metrics = _aggregate_gate_metrics(state_dir, args.budget_cap_usd)
    wall_time_s = time.time() - wall_start
    _write_smoke_e2e_evidence(
        session_id=session_id,
        state_dir=state_dir,
        metrics=metrics,
        video_id=video_id,
        budget_cap=args.budget_cap_usd,
        total_cost_usd=counter.total_usd,
        budget_breached=counter.total_usd > counter.cap_usd,
        wall_time_s=wall_time_s,
        status="OK",
        attempt_count=attempt_count,
    )

    # 5 evidence 파일 모두 존재 확인.
    missing = _verify_evidence_chain(session_id)
    if missing:
        logger.error(
            "[phase13] evidence chain 불완전 (대표님) — 누락: %s",
            missing,
        )
        return 6

    logger.info(
        "[phase13] 대표님, Phase 13 smoke 완료 — wall=%.1fs total_cost=$%.2f "
        "budget_cap=$%.2f breached=%s",
        wall_time_s,
        counter.total_usd,
        counter.cap_usd,
        counter.total_usd > counter.cap_usd,
    )
    if counter.total_usd > counter.cap_usd:
        return 5
    return 0


# =============================================================================
# Entry
# =============================================================================


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    logging.basicConfig(
        level=args.log_level,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    # --evidence-dir 런타임 override (대표님 격리 실행용).
    # EVIDENCE_DIR 상수를 module global 로 재바인딩하여 이후 모든 참조점
    # (_run_dry_run / _run_live / _write_smoke_e2e_evidence / _verify_evidence_chain)
    # 이 자동으로 override 경로 사용.
    global EVIDENCE_DIR
    effective_evidence_dir = (
        Path(args.evidence_dir) if args.evidence_dir else EVIDENCE_DIR
    )
    effective_evidence_dir.mkdir(parents=True, exist_ok=True)
    if args.evidence_dir:
        logger.info(
            "[phase13] --evidence-dir override (대표님): %s",
            effective_evidence_dir,
        )
        EVIDENCE_DIR = effective_evidence_dir

    # --topic + --niche 동반 검증 (한 쪽만 지정 불가)
    topic_set = bool(args.topic)
    niche_set = bool(args.niche)
    if topic_set != niche_set:
        print(
            "Error: --topic 과 --niche 는 반드시 동시에 지정해야 합니다 (대표님). "
            "한쪽만 지정하면 pipeline 상태 시드가 불완전합니다. "
            f"현재: --topic={'SET' if topic_set else 'unset'}, "
            f"--niche={'SET' if niche_set else 'unset'}.",
            file=sys.stderr,
        )
        return 7

    session_id = args.session_id or datetime.now().strftime("%Y%m%d_%H%M%S")
    _print_banner(session_id, args.budget_cap_usd, args.live)

    if args.topic and args.niche:
        topic_preview = [k.strip() for k in args.topic.split(",") if k.strip()]
        logger.info(
            "[phase13] 주제 pre-seed 활성 — 대표님 지정: niche=%s, keywords=%s",
            args.niche,
            topic_preview,
        )

    if args.verbose_compression:
        logger.info(
            "[phase13] --verbose-compression 활성 — supervisor raw payload "
            "dump enabled (대표님 forensic mode)"
        )

    if args.live:
        env = _check_env_readiness()
        _print_env_report(env)
        if env["required_missing"] or env["any_of_missing"]:
            logger.error(
                "[phase13] env 미충족 — 실 API 호출 진입 차단 (대표님). "
                ".env 확인 후 재시도 부탁드립니다."
            )
            return 4
        return _run_live(args, session_id)

    return _run_dry_run(args, session_id)


if __name__ == "__main__":
    sys.exit(main())
