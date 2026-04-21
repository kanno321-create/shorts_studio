"""UFL-04 — 대표님 영상 품질 subjective rating CLI (Phase 15 Plan 05).

사용 예::

    py -3.11 scripts/smoke/rate_video.py \\
        --video-id dQw4w9WgXcQ \\
        --rating 3 \\
        --feedback "조명이 어두움, 음성 톤이 단조로움" \\
        --session-id overseas_crime_sample_20260422 \\
        --niche incidents

저장: ``.claude/memory/feedback_video_quality.md`` — Markdown H2 append-only.

D-2 Lock 예외 (Phase 15-05 REQ-UFL-04) — 대표님 직접 입력. Phase 11
F-D2-EXCEPTION-01 trend-collector 선례 따름.

Format (H2 entry)::

    ## YYYY-MM-DD VIDEO_ID
    - session_id: <str or "(미지정)">
    - niche: <str or "(미지정)">
    - rating: <1-5>/5
    - feedback: <대표님 원문>
    - keywords: [top3 korean nouns]

Mandatory reads: researcher AGENT.md ``<mandatory_reads>`` 5번째 entry
(Task 15-05-03) 로 등록되어 매 호출마다 전수 로드됨.

CLAUDE.md 준수: 금기 #3 (try-except 침묵 금지 — 명시적 ValueError + raise)
+ 필수 #7 (대표님 한국어 존댓말).
"""
from __future__ import annotations

import argparse
import re
import sys
import time
from collections import Counter
from pathlib import Path

DEFAULT_MEMORY = Path(".claude/memory/feedback_video_quality.md")

SEED_FRONTMATTER = """---
d2_exception: true
reason: "대표님 직접 입력 — F-D2-EXCEPTION 패턴 (Phase 11 F-D2-EXCEPTION-01 trend-collector 선례 따름)"
phase_added: 15-system-prompt-compression-user-feedback-loop
created: {today}
purpose: 대표님 영상 품질 subjective rating 집계 → researcher 에 feedback 주입
---

# 영상 품질 피드백 로그

UFL-04 CLI `scripts/smoke/rate_video.py` 가 이 파일에 Markdown H2 entry 를 append 합니다.
Phase 15 researcher `<mandatory_reads>` 에 5번째 entry 로 등록됨 (Task 15-05-03).

---
"""

# 한국어 2글자 이상 명사/형태소 토큰 추출용 regex (stdlib only — 외부 dep 없음).
NOUN_REGEX = re.compile(r"[가-힣]{2,}")

# 간단한 stopword — 접속부사/감탄사/빈출 조사 파생어 중 일부.
STOPWORDS = {
    "그리고", "하지만", "그래서", "아주", "매우", "많이", "조금", "그러나",
    "때문에", "통해서", "대하여", "대해서",
}


def extract_keywords(text: str, top_n: int = 3) -> list[str]:
    """한국어 텍스트에서 빈도 기준 top-N 명사형 토큰 추출.

    외부 형태소 분석기 없이 stdlib regex 만 사용. 대표님 feedback 의 직관적
    키워드 파악 용도 — 정밀 NLP 가 아님.
    """
    if not text:
        return []
    tokens = [t for t in NOUN_REGEX.findall(text) if t not in STOPWORDS]
    freq = Counter(tokens)
    return [w for w, _ in freq.most_common(top_n)]


def format_entry(
    *,
    today: str,
    video_id: str,
    session_id: str | None,
    niche: str | None,
    rating: int,
    feedback: str,
) -> str:
    """Markdown H2 entry 1 개 생성 (trailing newline 포함)."""
    keywords = extract_keywords(feedback)
    lines = [
        f"## {today} {video_id}",
        f"- session_id: {session_id or '(미지정)'}",
        f"- niche: {niche or '(미지정)'}",
        f"- rating: {rating}/5",
        f"- feedback: {feedback}",
        f"- keywords: {keywords}",
        "",
    ]
    return "\n".join(lines) + "\n"


def ensure_seed(memory_path: Path, today: str) -> None:
    """Memory 파일 부재 시 d2_exception frontmatter + header 로 seed 생성.

    이미 존재하면 no-op (기존 entry 보존).
    """
    if not memory_path.exists():
        memory_path.parent.mkdir(parents=True, exist_ok=True)
        memory_path.write_text(
            SEED_FRONTMATTER.format(today=today),
            encoding="utf-8",
        )


def append_rating(
    *,
    memory_path: Path,
    video_id: str,
    rating: int,
    feedback: str,
    session_id: str | None = None,
    niche: str | None = None,
) -> None:
    """영상 품질 rating entry 를 memory 파일에 Markdown H2 로 append.

    Rating 범위 위반 / 필수 필드 누락 시 명시적 ValueError (CLAUDE.md 금기 #3
    try-except 침묵 금지 — 대표님 존댓말 에러 메시지).
    """
    # isinstance 순서: bool 은 int 의 subclass 이므로 별도 거부.
    if isinstance(rating, bool) or not isinstance(rating, int):
        raise ValueError(
            f"rating 은 정수여야 합니다 (대표님): {rating!r}"
        )
    if rating < 1 or rating > 5:
        raise ValueError(
            f"rating 은 1~5 사이 정수여야 합니다 (대표님): {rating!r}"
        )
    if not video_id:
        raise ValueError("video_id 는 필수입니다 (대표님).")
    if not feedback:
        raise ValueError("feedback 은 필수입니다 (대표님).")

    today = time.strftime("%Y-%m-%d")
    ensure_seed(memory_path, today)
    entry = format_entry(
        today=today,
        video_id=video_id,
        session_id=session_id,
        niche=niche,
        rating=rating,
        feedback=feedback,
    )
    with memory_path.open("a", encoding="utf-8") as fp:
        fp.write(entry)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="UFL-04 대표님 영상 품질 rating CLI (Phase 15 Plan 05)",
    )
    parser.add_argument("--video-id", required=True, help="YouTube video ID")
    parser.add_argument(
        "--rating",
        type=int,
        required=True,
        help="1~5 사이 정수 (대표님 주관 평점)",
    )
    parser.add_argument(
        "--feedback",
        required=True,
        help="한국어 자유 텍스트 피드백 (대표님)",
    )
    parser.add_argument("--session-id", default=None)
    parser.add_argument("--niche", default=None)
    parser.add_argument(
        "--memory-path",
        type=Path,
        default=DEFAULT_MEMORY,
        help="rating 저장 대상 Markdown 파일",
    )
    args = parser.parse_args(argv)

    # Windows cp949 stdout 대비 (D-22 precedent).
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError):
        # 이미 UTF-8 이거나 reconfigure 미지원 환경 — 명시적 체념 (로깅 불필요).
        pass

    append_rating(
        memory_path=args.memory_path,
        video_id=args.video_id,
        rating=args.rating,
        feedback=args.feedback,
        session_id=args.session_id,
        niche=args.niche,
    )
    print(
        f"[rate_video] 기록 완료 (대표님): {args.video_id} "
        f"rating={args.rating}/5 → {args.memory_path}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
