# Harness Hooks — 공용 Claude Code 훅

Layer 1 naberal_harness가 제공하는 **공용 훅 3종**. 각 스튜디오는 자신의 `.claude/hooks/`에 이 파일들을 **복사**하여 사용.

## 훅 목록

| Hook | 이벤트 | 역할 |
|------|-------|------|
| `pre_tool_use.py` | PreToolUse | Write/Edit 전 **deprecated 패턴 검출 → 차단** |
| `post_tool_use.py` | PostToolUse | 모든 tool call 기록 (`.claude/hooks/post_tool_log.jsonl`) |
| `session_start.py` | SessionStart | 세션 시작 시 **자동 감사** 리포트 주입 |

## 설치

### 자동 (스캐폴드 CLI 사용)
```bash
python harness/scripts/new_domain.py my_studio
# → my_studio/.claude/hooks/ 에 3개 훅 자동 복사됨
```

### 수동 (기존 스튜디오에 추가)
```bash
cp harness/hooks/*.py my_studio/.claude/hooks/
cp harness/hooks/settings.sample.json my_studio/.claude/settings.json
```

## 설정 (`.claude/settings.json`)

Claude Code Hook 등록:
```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Write|Edit|MultiEdit",
        "hooks": [
          {
            "type": "command",
            "command": "python .claude/hooks/pre_tool_use.py"
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "*",
        "hooks": [
          {
            "type": "command",
            "command": "python .claude/hooks/post_tool_use.py"
          }
        ]
      }
    ],
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python .claude/hooks/session_start.py"
          }
        ]
      }
    ]
  }
}
```

## Deprecated 패턴 정의 (`.claude/deprecated_patterns.json`)

각 스튜디오가 자신의 금지 패턴을 명시. `pre_tool_use.py`와 `session_start.py`가 이 파일을 읽음:

```json
{
  "patterns": [
    {
      "regex": "skip_gates\\s*=\\s*True",
      "reason": "CONFLICT_MAP A-6: skip_gates deprecated"
    },
    {
      "regex": "subtitle_generate\\.py --pipeline shorts",
      "reason": "CONFLICT_MAP A-7: 구형 경로, word_subtitle.py 사용"
    },
    {
      "regex": "TODO\\(next-session\\)",
      "reason": "GATE dispatch 미연결 (CLAUDE.md M6 위반)"
    }
  ]
}
```

## 업데이트 (Layer 1 변경 반영)

```bash
cd my_studio/
cp ../../harness/hooks/*.py .claude/hooks/
git diff .claude/hooks/  # 변경 확인
git add .claude/hooks/ && git commit -m "chore: update harness hooks to v{version}"
```

## 원칙

- **Hook은 절대 파이프라인 멈추지 않음** — 내부 에러 시 조용히 `allow` 반환
- **민감 정보 마스킹** — post_tool_use가 token/password/cookie 키 자동 제거
- **성능 우선** — session_start 감사는 캐시 파일 있으면 재사용 고려 (향후 개선)

---

> 🧩 naberal_harness v1.0 — 스튜디오 독립성 유지하며 공통 안전망 제공.
