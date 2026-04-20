# FAILURES.md — shorts_studio

> **규율 (D-11)**: 이 파일은 **append-only**. 기존 엔트리 수정/삭제 금지. `pre_tool_use.py:160 check_failures_append_only()` 가 강제.
>
> **목적**: 과거 실패를 박제해 재발 방지. 각 엔트리는 증상 + 근본 원인 + 재발 방지 조치를 기록.

---

## F-CTX-01 — 세션 간 컨텍스트 단절 (2026-04-20, 대표님 지적)

**증상**:
- 이미 `.env`에 저장된 API key를 Claude가 세션마다 다시 질문
- `WORK_HANDOFF.md` / `SESSION_LOG.md` / 메모리에 박제된 결정사항을 Claude가 무시하고 엉뚱한 작업 수행
- 대표님 인용 (세션 #26, 세션 #27): "이미 어딘가에 입력되어있는거 자꾸 빠트린다고", "맨날 그거 안읽고 그런거 모른다는둥 대화가 가끔 단절되는데", "분명 줬는데도 불구하고 api key달라고그러고"

**발생 세션**: #24, #25, #26, #27 (반복 패턴)

**근본 원인 3중**:
1. `.claude/hooks/session_start.py:166-167` — SessionStart hook이 감사 메시지(SKILL 500줄/CONFLICT_MAP/deprecated 패턴)만 system context로 주입하고 **메모리·핸드오프·API key 존재 고지는 일절 안 함**.
2. `.claude/settings.json:1-37` — `additionalDirectories` / 자동 컨텍스트 로드 설정 **부재**. Session Init 4개 파일 지시가 CLAUDE.md에 **텍스트로만** 존재, Hook 강제 로드 없음.
3. `C:/Users/PC/.claude/projects/c--Users-PC-Desktop-naberal-group-studios-shorts/memory/` **빈 디렉토리**. WORK_HANDOFF.md에 "메모리 N개 갱신" 기록만 있고 실제 파일 0개. Claude가 읽을 메모리 실체가 없음.

**재발 방지 조치** (2026-04-20 commit `fix(context)`):
- **A1**: `session_start.py` Step 4-6 추가 — `WORK_HANDOFF.md` 첫 30줄 요약 + `.env` key 이름 목록 + `.claude/memory/MEMORY.md` 인덱스를 매 세션 system context로 강제 주입.
- **A2**: `.claude/memory/` 로컬 메모리 저장소 신설. 9개 메모리 파일 (project/feedback/reference) + MEMORY.md 인덱스. 스튜디오 로컬 격리(전역 메모리 노이즈 회피).
- **A3**: 본 `FAILURES.md` 생성 + F-CTX-01 등록 (이 엔트리).
- **A4**: `CLAUDE.md` Session Init 섹션에 `.claude/memory/` + `.env` 항목 명시 추가.

**검증 방법**:
- 신규 세션 시작 시 system message에 "API keys available: TYPECAST_API_KEY, KLING_ACCESS_KEY, FAL_KEY, GOOGLE_API_KEY, ELEVENLABS_API_KEY, RUNWAY_API_KEY" 문구 노출 확인
- `ls .claude/memory/` → 10개 파일 (1 인덱스 + 9 메모리) 존재 확인
- 동일 유형 질문 재발 시 본 F-CTX-01 참조 후 Step 4-6 로직 실패 여부 진단

**관련 메모리**: `feedback_session_evidence_first` (UAT evidence-first 원칙과 동일 맥락 — 박제된 것을 먼저 읽어라)
