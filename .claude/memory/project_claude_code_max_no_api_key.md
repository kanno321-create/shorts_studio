---
name: project_claude_code_max_no_api_key
description: Claude Code Max 구독 활용, anthropic Python SDK 직접 호출 영구 금지, Claude CLI subprocess 경로 강제
type: project
---

# Claude Code Max 구독 — ANTHROPIC_API_KEY 영구 금지

**결정**: 세션 #24 (2026-04-20), architecture correction commit `8af5063`.

## 핵심 원칙

- **`.env` 에 `ANTHROPIC_API_KEY` 등록 금지**
- **`anthropic.Anthropic().messages.create()` 직접 호출 금지** (별도 usage billing 발생 — Max 구독 중복 결제)
- **모든 Claude 호출 = Claude CLI subprocess 경로**:
  ```python
  subprocess.run(["claude", "--print", "--append-system-prompt", system_prompt, user_msg])
  ```

## 근거

- Claude Code Max 구독 = 월정액. SDK 직접 호출은 **추가 API key billing** 으로 Max subscription 과 별개 요금 발생
- Max 구독 경로 = `claude --print` CLI → subprocess → 자동으로 Max billing 적용

## 구현 파일

- `scripts/orchestrator/invokers.py` — Claude CLI subprocess wrapper (세션 #24 commit `8af5063` 에서 SDK → CLI 전환)

## 적용 scope

- Producer (script/blueprint/metadata) — Claude Sonnet 4.6
- Reviewer (critical gate) — Claude Opus 4.6
- 둘 다 CLI subprocess 경로. SDK import 금지.

## 금지 코드 패턴

```python
# ❌ 금지
from anthropic import Anthropic
client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

# ✅ 허용
subprocess.run(["claude", "--print", ...], capture_output=True)
```

## Related

- [reference_api_keys_location](reference_api_keys_location.md) — .env 금지 항목 명시
- `.env.example:44-46` — "금지 항목" 섹션 주석
