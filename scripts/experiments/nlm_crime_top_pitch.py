"""One-shot NLM query — top overseas crime stories for incidents shorts.

Session #33 post-Phase 16: first production smoke. Query crime-stories notebook
for TOP 5 overseas (non-Korean) unsolved/mysterious crime cases with highest
YouTube Shorts viral potential for 사건기록부 channel.

NOTE: Bypasses scripts/notebooklm/query.py which passes a --timeout flag not
supported by external ask_question.py (bug to be filed against query.py).
Directly invokes the skill's run.py with the correct argv shape.

Usage:
  python scripts/experiments/nlm_crime_top_pitch.py [--timeout-seconds 600]

Outputs:
  outputs/nlm_queries/crime_top_pitch_<timestamp>.md — raw NLM answer + metadata
"""
from __future__ import annotations

import argparse
import datetime as dt
import os
import subprocess
import sys
from pathlib import Path

SKILL_PATH = Path(r"C:/Users/PC/Desktop/secondjob_naberal/.claude/skills/notebooklm")
FOLLOW_UP_MARKER = "EXTREMELY IMPORTANT: Is that ALL you need"

QUESTION = (
    "해외 (한국 제외) 유명 범죄 · 미스터리 · 미제 사건 중, "
    "한국 YouTube Shorts '사건기록부' 채널 (60-120초 영상, 탐정 1인칭 독백 + 왓슨 질문 듀오, "
    "탐정 POV cinematic true crime documentary 스타일, 30-50대 남성 시청층) 에서 대박날 가능성이 "
    "가장 높은 TOP 5 사건을 추천하시오. "
    "선정 기준: (A) 미스터리 강도 — 미해결 or 충격적 반전 존재, "
    "(B) 시각적 hook — 단일 상징적 이미지 (범인 셔츠, 암호문, 현장 사진 등) 존재, "
    "(C) 감정적 여운 — 피해자 유족 비극 / 범인 동기의 기이함 / 무고한 희생 등 hook 1개 이상, "
    "(D) 60-120초 내 story arc 완결 — Hook → Misdirection → Build-up → Reveal → Aftermath 구조 수용, "
    "(E) 낯섦 + 호기심 — 한국 시청자에게 생소하되 즉시 호기심 자극 가능. "
    "각 사건에 대해: "
    "1) 사건명 (영문 + 한글), 2) 발생 연도 / 국가 / 지역, 3) 핵심 미스터리 1-2문장, "
    "4) 시각적 hook 1개 (존재하는 실 이미지 자산), 5) 감정적 여운 요소 1개, "
    "6) 예상 score (A-E 5개 기준 각 0-10, 총합 /50), 7) 특이사항 / 리스크. "
    "이미 대박난 재탕 (zodiac, jack the ripper, mary celeste, db cooper, elisa lam, dyatlov pass, "
    "세타가야, 기타큐슈) 은 제외하되, 덜 알려진 고급 사건 선호. "
    "답변은 한국어로 작성, 각 사건 섹션 구분. "
    "출처 (source citation) 가 있다면 반드시 포함."
)
NOTEBOOK_ID = "crime-stories-+-typecast-emotion"


def _strip_follow_up(s: str) -> str:
    if FOLLOW_UP_MARKER in s:
        return s.split(FOLLOW_UP_MARKER)[0].rstrip()
    return s


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--timeout-seconds", type=int, default=600)
    args = p.parse_args()

    timestamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = Path(__file__).resolve().parents[2] / "outputs" / "nlm_queries"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"crime_top_pitch_{timestamp}.md"

    if not SKILL_PATH.exists():
        raise FileNotFoundError(f"NotebookLM skill not found at {SKILL_PATH}")

    run_py = SKILL_PATH / "scripts" / "run.py"
    cmd = [
        sys.executable,
        str(run_py),
        "ask_question.py",
        "--question", QUESTION,
        "--notebook-id", NOTEBOOK_ID,
    ]
    print(f"[NLM] Invoking skill at {SKILL_PATH}")
    print(f"[NLM] Notebook: {NOTEBOOK_ID}")
    print(f"[NLM] Timeout: {args.timeout_seconds}s (subprocess cap {args.timeout_seconds + 30}s)")
    print(f"[NLM] Output → {out_path}")
    print()

    # Force Python UTF-8 mode — external skill's notebook_manager.py reads
    # library.json with default cp949 on Windows, which fails on Korean text.
    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"

    start = dt.datetime.now()
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=args.timeout_seconds + 30,
        env=env,
    )
    elapsed = (dt.datetime.now() - start).total_seconds()

    if result.returncode != 0:
        print(f"[NLM] ERROR rc={result.returncode} elapsed={elapsed:.1f}s", file=sys.stderr)
        print(f"[NLM] stderr: {result.stderr[:500]}", file=sys.stderr)
        raise RuntimeError(f"NotebookLM query failed rc={result.returncode}")

    answer = _strip_follow_up(result.stdout)
    content = [
        "---",
        f"query_type: crime_top_pitch",
        f"notebook_id: {NOTEBOOK_ID}",
        f"timestamp: {timestamp}",
        f"elapsed_seconds: {elapsed:.1f}",
        f"answer_length_chars: {len(answer)}",
        f"session: '#33'",
        f"purpose: 'Phase 16 post-completion first production smoke'",
        "---",
        "",
        "# NLM Query — Crime Top Pitch",
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
    print(f"[NLM] OK elapsed={elapsed:.1f}s chars={len(answer)}")
    print(f"[NLM] Saved → {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
