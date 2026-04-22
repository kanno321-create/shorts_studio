---
name: feedback_no_mockup_no_empty_files
description: 절대 금지 — 목업/스텁/placeholder/빈 파일 생성. 모든 산출물은 production-ready 실 콘텐츠여야 함. 2026-04-22 대표님 절대 규칙.
type: feedback
---

# 절대 금지: 목업·빈 파일

**규칙**: 어떤 상황에서도 **목업(mock/stub/placeholder/dummy)** 또는 **빈 파일**을 생성하지 않는다.

**Why**:
- 2026-04-22 대표님 직접 지시 ("앞으로 절대 목업, 빈파일은 절대금지사항이다")
- 과거 사례: 빈 placeholder 파일 + TODO 주석으로 "완료" 보고 → 실제 production 영상 퀄리티가 처참한 demo 수준 (assembled_1776844680770.mp4, 13초 720p) → 대표님 충격
- 본질: spec 게이트 통과만으로 "완료" 처리하는 패턴이 **production 콘텐츠 누락**을 은폐한다

**How to apply**:
1. **모든 신규 파일은 즉시 실 콘텐츠로 채운다.** `# TODO` / `pass` / 빈 dict/list / `raise NotImplementedError` 단독 함수 금지.
2. **테스트 픽스처도 production-ready** — 1×1 PNG 같은 최소 valid 데이터는 OK (이미 stdlib 로 생성하는 패턴 박제됨), 단순 placeholder text 금지.
3. **에이전트 출력 JSON 도 빈 배열·null 금지** — `{"i2v_clips": []}` 같은 빈 출력은 ASSETS 게이트 PASS 처리하지 말고 raise EmptyAssetsError.
4. **"미완은 명시적 raise" — CLAUDE.md 금기 #2 와 결합**. `TODO(next-session)` 표식 금지, 미완은 `raise NotImplementedError("이유: <왜 미완인지>")`.
5. **README.md 같은 메타 파일도 실 내용** — 한 줄짜리 placeholder README 금지. 실제 디렉토리 목적 + 사용법 + cross-reference 포함 필수.
6. **assembled mp4 는 production spec 충족 확인 후에만 OK 보고**. 720p / 13초 / 자막없음 / 자료없음 / 인트로아웃로 없음 같은 demo 수준 산출물을 "fix 됐다" 라 보고하지 않는다.

**Cross-reference**:
- CLAUDE.md 🔴 금기사항 #10 (이 규칙 메인 정의)
- CLAUDE.md 🟢 필수사항 추가 항목
- `.claude/agents/_shared/agent-template.md` MUST REMEMBER 절 추가
- `feedback_lenient_retry_over_strict_block` — 봐주면서 retry 는 OK, **빈 출력은 봐주기 대상 아님**
- `feedback_session_evidence_first` — UAT 작성 전 실제 산출물 전수 점검 의무

**검출 패턴 (sanity check)**:
- `grep -rE "TODO|FIXME|XXX|placeholder|mock|stub|pass$|^\s*\.\.\.\s*$" --include="*.py"` 신규 파일에 매치 시 경고
- 0 byte 파일 (`find . -size 0 -type f`) 생성 금지
- 한 줄 README.md (`wc -l README.md` < 5) 생성 금지
