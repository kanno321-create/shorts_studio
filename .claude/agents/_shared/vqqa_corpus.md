# VQQA Semantic-Feedback Corpus (RUB-03)

본 파일은 Inspector가 Producer에 주입할 `semantic_feedback` 자연어 피드백의 **예시 코퍼스**다.
Phase 4 표준 형식 = `[문제 설명]([위치 or 시간 스탬프]) — [교정 힌트 1 문장]`.

## Format Rules

- **언어:** 한국어 (Producer 컨텍스트와 일치, code-switching cost 차단).
- **구조:** `[문제](위치) — [교정 힌트]`.
- **금지:** 대안 창작 (Inspector는 평가만, RUB-02).
- **위치 표기:** `scene:N`, `line:N`, `t:3.2s`, `frame:45` 중 하나.
- **길이:** 한 예시당 ≤ 300자 권장.

## 5 Reference Examples

### Example 1 — CONTENT-01 (3초 hook 약함)

> 3초 hook이 약하다 (질문형 없음, 숫자 없음)(line:1) — 예: '1997년 서울 23세 여대생은 왜 사라졌을까?'처럼 연도/나이/인명 중 2개 이상을 질문형 문장에 주입하도록 교정 필요.

### Example 2 — CONTENT-02 (존댓말/반말 혼용)

> 4번째 scene에서 탐정이 '알아요'(해요체) 사용(scene:4, line:7) — 탐정 speaker는 하오체 종결어미('알고 있소', '알겠소')로 교정 필요.

### Example 3 — CONTENT-02 (호칭 누출)

> 탐정 발화에 '탐정님' 호칭 누출(t:3.15s) — 자기 자신을 3인칭 '탐정님'으로 지칭 금지, '소생' 또는 생략 대명사로 교정 필요.

### Example 4 — AGENT-02 (Shot 1 Move Rule 위반)

> 7번째 scene이 1 Move Rule 위반(scene:7) — 카메라 팬 + 피사체 이동 동시 요청됨, 둘 중 하나만 선택하여 anchor frame 재정의 필요.

### Example 5 — AUDIO-04 / AF-13 (K-pop 감지)

> audio track에 BTS 'Dynamite' snippet 감지됨(t:12.4s-15.8s) — KOMCA strike 위험, royalty-free whitelist(Epidemic Sound / Artlist / YouTube Audio Library / Free Music Archive) 내 대체 트랙으로 교체 필요.

## Extension Policy

- Phase 4 Wave 0은 5 예시만 고정. Wave 3~5에서 각 Inspector AGENT.md가 본 파일을 `@.claude/agents/_shared/vqqa_corpus.md`로 참조.
- Phase 7 Integration Test 실측 후 **추가 예시 10건 보강**. Phase 4 타임라인 내에서는 보강 금지(scope out).
- 새 예시 추가 시 반드시 기존 형식 `[문제](위치) — [교정 힌트]`를 준수할 것.
