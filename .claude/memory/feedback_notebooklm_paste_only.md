---
name: feedback_notebooklm_paste_only
description: NotebookLM 쿼리 입력은 반드시 clipboard paste 방식. typing 은 중간 enter 가 submit trigger 되어 쿼리 잘림 + 에러. 추가질문도 동일.
type: feedback
---

# NotebookLM 입력은 Paste 전용 (Typing 금지)

**Rule**: NotebookLM 의 query 입력 (`textarea.query-box-input`) 은 반드시 **clipboard paste** 방식으로 주입해야 한다. 브라우저 자동화가 직접 typing (문자 단위 입력) 으로 전달하면 중간에 포함된 자동 줄바꿈 / enter keystroke 가 채팅 submit trigger 로 인식되어 **쿼리가 잘린 채 전송되고 NLM 이 오답 반환 → rc=1 / 의미 없는 답**.

**Why**:
대표님 2026-04-22 세션 #33 직접 피드백:
> "nlm에게는 프롬프트를 미리 준비하고 붙혀넣기로 물어봐야된다. 직접 타이핑치면 쿼리 다날라가 엔터눌러버려서 채팅입력이 되어버리더라고 지난번보니까, 그래서 에러나는데 붙혀넣기로 하면 에러안남. 추가질문도 마찬가지."

NotebookLM UI 의 textarea 는 `Enter` 를 submit 으로 인식하는 설계 (Google Docs/Gmail chat 유사). 긴 prompt 를 문자 단위 타이핑 시 OS IME, 자동완성, 또는 input event 순서 어긋남으로 중간 Enter 가 발생할 수 있음.

**How to apply**:

### 1. 초기 질문 (ask_question 계열)
scripts/notebooklm/query.py + 외부 skill `secondjob_naberal/.claude/skills/notebooklm/scripts/ask_question.py` 는 현재 typing 방식. **수정 필요**:

```python
# AS-IS (잘못): page.fill(selector, question)  → typing with auto-enter risk
# TO-BE (정답): clipboard paste via JS
await page.evaluate(
    """([text]) => {
        const ta = document.querySelector('textarea.query-box-input');
        const setter = Object.getOwnPropertyDescriptor(
            window.HTMLTextAreaElement.prototype, 'value'
        ).set;
        setter.call(ta, text);
        ta.dispatchEvent(new Event('input', {bubbles: true}));
    }""",
    [question],
)
# Then click submit button explicitly (not press Enter)
await page.click('button[aria-label*="Submit"]')
```

Or use Playwright 의 `page.evaluate` 로 직접 `navigator.clipboard.writeText(text)` + `Cmd+V`/`Ctrl+V` 에뮬레이션.

### 2. 추가질문 (follow-up)
동일 원칙. NotebookLM 은 동일 textarea 를 재사용하므로 같은 paste 메커니즘.

### 3. 우리 scripts/notebooklm/query.py 대응
현재 구현은 외부 skill 호출 subprocess wrapper. 외부 skill 수정 없이 우회 방법 2개:
- **(A) 외부 skill patch**: `secondjob_naberal/.claude/skills/notebooklm/scripts/ask_question.py` 내 `page.fill` 호출을 clipboard paste 로 교체 (단 secondjob_naberal 수정은 shorts_naberal 금기 #6 와 대칭 원칙 — 외부 skill 보존 우선).
- **(B) 재시도 + 답변 validation**: 쿼리 후 답변 길이 / 핵심 키워드 포함 여부로 잘림 감지. 잘렸으면 재시도. — 임시방편, 근본 fix 아님.
- **(C) 직접 UI 제어**: scripts/notebooklm/ 에 새 `query_paste.py` 작성, Playwright 재구현. subprocess 우회 가능하나 D-7 "외부 skill reference, not copy" 원칙 위배 가능.

**현재 방침**: Option (B) 임시 + Option (A) 추적. 외부 skill 수정 권한 여부는 대표님 결정 대기.

### 4. 언제 잘림 발생하는가
- **Symptom 1**: `rc=1` + stderr "쿼리 응답 없음" / "타임아웃"
- **Symptom 2**: 답변이 질문의 첫 부분만 기반 (선정 기준이나 exclusion list 무시)
- **Symptom 3**: `answer_length_chars < 500` (정상은 3000+)
- **Validation**: 답변에 질문의 후반 키워드 (예: "출처 citation", "score 5개 기준") 가 포함되는지 grep

### 5. 박제 위치
- **이 메모리** (feedback_notebooklm_paste_only)
- **CLAUDE.md Navigator "NotebookLM 리서치" 라인** — 본 메모리 참조 추가
- **scripts/notebooklm/query.py docstring** — paste-only WARNING 추가
- **FAILURES.md** — NLM 잘림 이력 기록 항목 예약

## Related

- `.claude/memory/feedback_notebooklm_query.md` — (생성 예정, D-6 single-string discipline + 본 paste 규칙 통합)
- `scripts/notebooklm/query.py` — subprocess wrapper, --timeout argv 버그도 존재 (ask_question.py 미지원)
- `secondjob_naberal/.claude/skills/notebooklm/scripts/ask_question.py` — 외부 skill 본체
