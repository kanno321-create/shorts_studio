---
d2_exception: true
reason: "대표님 직접 입력 — F-D2-EXCEPTION 패턴 (Phase 11 F-D2-EXCEPTION-01 trend-collector 선례 따름)"
phase_added: 15-system-prompt-compression-user-feedback-loop
created: 2026-04-22
purpose: 대표님 영상 품질 subjective rating 집계 → researcher 에 feedback 주입
---

# 영상 품질 피드백 로그

UFL-04 CLI `scripts/smoke/rate_video.py` 가 이 파일에 Markdown H2 entry 를 append 합니다.
Phase 15 researcher `<mandatory_reads>` 에 5번째 entry 로 등록됨 (Task 15-05-03).

매 entry 포맷::

    ## YYYY-MM-DD VIDEO_ID
    - session_id: <overseas_crime_sample_20260422 형식 또는 "(미지정)">
    - niche: <incidents/mystery/... 또는 "(미지정)">
    - rating: <1-5>/5
    - feedback: <대표님 자유 텍스트>
    - keywords: [상위 3 키워드]

검증 CLI: `py -3.11 scripts/validate/verify_feedback_format.py` (Task 15-05-02).

---
