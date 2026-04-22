"""NLM deep-dive — Ryan Waller 취조 사건 상세 facts for script production.

대표님 선택: (1) 라이언 월러 — 첫 production smoke 소재.
이 스크립트는 사건기록부 채널 대본 작성에 필요한 source-grounded facts 를
NotebookLM 에서 가져와 `outputs/nlm_queries/ryan_waller_facts_<ts>.md` 에 저장.

Validation:
- Answer length ≥ 1500 chars (짧으면 잘림 의심)
- 필수 키워드: ['Ryan Waller', 'Phoenix' OR '애리조나', '2006'] 전부 포함
- 'citation' / '출처' / '#' 인용 번호 패턴 최소 3개
- 실패 시 retry (최대 2회, paste-robust 준비는 별도 task)

Usage:
  python scripts/experiments/nlm_ryan_waller_facts.py

Outputs:
  outputs/nlm_queries/ryan_waller_facts_<ts>.md
"""
from __future__ import annotations

import argparse
import datetime as dt
import os
import re
import subprocess
import sys
from pathlib import Path

# Force UTF-8 stdout for Korean + em-dash output on Windows cp949 default
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        pass

SKILL_PATH = Path(r"C:/Users/PC/Desktop/secondjob_naberal/.claude/skills/notebooklm")
FOLLOW_UP_MARKER = "EXTREMELY IMPORTANT: Is that ALL you need"
NOTEBOOK_ID = "crime-stories-+-typecast-emotion"

QUESTION = (
    "라이언 월러 취조 사건 (The Interrogation of Ryan Waller, 2006, 미국 애리조나 Phoenix) "
    "에 대한 사건기록부 YouTube Shorts 대본 작성용 상세 source-grounded facts 를 제공하시오. "
    "사건기록부 채널은 탐정 1인칭 독백 + 왓슨(조수) 시청자 대리 질문 듀오, 60-120초, "
    "Hook(오늘의 기록) → Misdirection(단순 살인사건처럼 보임) → Build-up(이상 행동) → "
    "Reveal(총상 피해자였음) → Aftermath(사망, 유족 소송) 4단계 구조. "
    "요구 정보: "
    "1) 피해자 신원 (여자친구 이름, 나이) + 발견 경위 (시간, 장소, 사망 원인), "
    "2) 라이언 월러 프로필 (당시 나이, 관계, 체포 정황), "
    "3) 취조 경과 상세 — 취조 소요 시간, 경찰의 잘못된 가정, 라이언의 이상 행동 (횡설수설, 좌측 눈 부종, 어지러움 등) 구체적 묘사, "
    "4) 실제 범인 (강도, 총격 순간, 총격 부위 — 라이언이 어디에 총을 맞았는지), "
    "5) 진실 발각 경위 — 누가 언제 어떻게 총상을 인지, 병원 이송 시점, 응급치료 지연 시간, "
    "6) 라이언의 후일담 — 뇌손상 잔존 여부, 생존 기간, 사망 시점 (몇 년 후), 사망 원인, "
    "7) 유족 소송 결과 — Phoenix 경찰서 상대 소송 결과 / 합의금 / 정책 변경, "
    "8) 시각 자산 — 실제 취조실 CCTV 영상 / 사진 / 현장 사진 중 public domain 또는 fair use 가능한 것 목록, "
    "9) 관련 공식 문서 — 경찰 보고서 / 법원 판결 / 주요 뉴스 기사 citation 최소 3개, "
    "10) 한국 시청자 몰입 포인트 (경찰 과실 분노 / 무고한 사망 / 확증 편향 교훈 등). "
    "답변은 한국어, 각 항목 번호 매겨 구분. "
    "출처 인용 (citation 번호) 필수 — 사실 주장마다 출처 번호 첨부."
)


def _strip_follow_up(s: str) -> str:
    if FOLLOW_UP_MARKER in s:
        return s.split(FOLLOW_UP_MARKER)[0].rstrip()
    return s


def _validate_answer(answer: str) -> tuple[bool, list[str]]:
    """Return (ok, issues). Answer validation to detect typing-truncation."""
    issues: list[str] = []
    if len(answer) < 1500:
        issues.append(f"Answer too short ({len(answer)} < 1500) — typing-truncation suspect")
    must_have = ["Ryan Waller"]
    for kw in must_have:
        if kw.lower() not in answer.lower():
            issues.append(f"Missing required keyword: '{kw}'")
    cites_in_text = len(re.findall(r"\[?\d+\]?", answer))
    if cites_in_text < 3:
        issues.append(f"Too few citation markers ({cites_in_text} < 3)")
    return (len(issues) == 0, issues)


def _run_query(timeout_seconds: int) -> tuple[str, float]:
    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    run_py = SKILL_PATH / "scripts" / "run.py"
    cmd = [
        sys.executable, str(run_py),
        "ask_question.py",
        "--question", QUESTION,
        "--notebook-id", NOTEBOOK_ID,
    ]
    start = dt.datetime.now()
    result = subprocess.run(
        cmd,
        capture_output=True, text=True,
        encoding="utf-8", errors="replace",
        timeout=timeout_seconds + 30, env=env,
    )
    elapsed = (dt.datetime.now() - start).total_seconds()
    if result.returncode != 0:
        raise RuntimeError(
            f"NLM rc={result.returncode} stderr={result.stderr[:400]}"
        )
    return _strip_follow_up(result.stdout), elapsed


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--timeout-seconds", type=int, default=600)
    p.add_argument("--max-retries", type=int, default=2)
    args = p.parse_args()

    if not SKILL_PATH.exists():
        raise FileNotFoundError(f"NotebookLM skill not found at {SKILL_PATH}")

    timestamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = Path(__file__).resolve().parents[2] / "outputs" / "nlm_queries"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"ryan_waller_facts_{timestamp}.md"

    print(f"[NLM] Query Ryan Waller facts — notebook={NOTEBOOK_ID}")
    print(f"[NLM] Question length={len(QUESTION)} chars")
    print(f"[NLM] Max retries={args.max_retries} (validation: len>=1500 + keyword + citations>=3)")

    attempt = 0
    answer = None
    last_issues: list[str] = []
    last_elapsed = 0.0
    while attempt <= args.max_retries:
        attempt += 1
        print(f"[NLM] Attempt {attempt}/{args.max_retries + 1}...")
        try:
            answer, last_elapsed = _run_query(args.timeout_seconds)
        except Exception as e:  # noqa: BLE001 — log + retry per paste-truncation defence
            print(f"[NLM] Attempt {attempt} exception: {type(e).__name__}: {e}", file=sys.stderr)
            if attempt > args.max_retries:
                raise
            continue
        ok, last_issues = _validate_answer(answer)
        print(f"[NLM] Attempt {attempt}: elapsed={last_elapsed:.1f}s chars={len(answer)} ok={ok}")
        if ok:
            break
        print(f"[NLM] Validation issues: {last_issues}", file=sys.stderr)
        if attempt > args.max_retries:
            print("[NLM] Max retries exhausted — saving last answer despite validation failure", file=sys.stderr)
            break

    if answer is None:
        raise RuntimeError("NLM query failed on all attempts")

    content = [
        "---",
        f"query_type: ryan_waller_facts",
        f"notebook_id: {NOTEBOOK_ID}",
        f"timestamp: {timestamp}",
        f"elapsed_seconds: {last_elapsed:.1f}",
        f"answer_length_chars: {len(answer)}",
        f"attempts: {attempt}",
        f"validation_issues: {last_issues}",
        f"session: '#33'",
        f"purpose: 'Phase 16 post-completion first production smoke — Ryan Waller'",
        "---",
        "",
        "# NLM Query — Ryan Waller Interrogation Facts",
        "",
        "## Question",
        "",
        "```",
        QUESTION,
        "```",
        "",
        "## Answer",
        "",
        answer,
        "",
    ]
    out_path.write_text("\n".join(content), encoding="utf-8")
    print(f"[NLM] Saved → {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
