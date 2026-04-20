---
name: reference_api_keys_location
description: .env 위치 + 각 key 이름/용도 매핑. 대표님께 API key 재질문 절대 금지 (F-CTX-01 재발 방지)
type: reference
---

# API Keys Location Registry

**⚠️ 절대 규칙**: 대표님께 API key 를 재질문하지 말 것. 전부 `.env` 에 존재한다. F-CTX-01 참조.

## 파일 경로

- **로컬 작동본**: `C:/Users/PC/Desktop/naberal_group/studios/shorts/.env` (gitignore, 실 key 값 포함)
- **원본 레지스트리**: `C:/Users/PC/Desktop/shorts_naberal/.env` (shorts_naberal 의 검증된 key, 세션 #26 포팅 완료)
- **템플릿**: `.env.example` (구조 + 금지 항목 명시, git 추적)

## Key 매핑

### TTS (Stage 3)
| Key | 용도 | Tier |
|-----|------|------|
| `TYPECAST_API_KEY` | 한국 채널 primary TTS | Primary |
| `ELEVENLABS_API_KEY` | 영어 채널 primary + 한국 fallback | Fallback |
| `ELEVENLABS_DEFAULT_VOICE_ID` | voice_discovery auto-resolve 실패 시 override | Optional |

### Image (Stage 2)
| Key | 용도 |
|-----|------|
| `GOOGLE_API_KEY` | Nano Banana Pro (Gemini 3 Pro Image) 앵커 프레임 |

### Video (Stage 4)
| Key | 용도 | 우선순위 |
|-----|------|---------|
| `FAL_KEY` | fal.ai 공용 (Kling + Veo 양쪽 호출, 권장) | Primary |
| `KLING_ACCESS_KEY` + `KLING_SECRET_KEY` | Kling 직접 호출 (fal.ai 우회) | Alternative |
| `RUNWAY_API_KEY` | Runway hold adapter (production 미호출, 코드만 유지) | Hold |

### YouTube (Phase 8)
- **API key 방식 사용 안 함**. OAuth2 경로:
  - `config/client_secret.json` (Google Cloud OAuth 클라이언트)
  - `config/youtube_token.json` (refresh token)

## 🚫 금지 항목

- **`ANTHROPIC_API_KEY` 등록 절대 금지** ([project_claude_code_max_no_api_key](project_claude_code_max_no_api_key.md))
- 이유: Claude Code Max 구독 = 월정액. SDK 호출은 별도 usage billing 발생.

## 확인 명령어

```bash
# key 이름만 확인 (값 노출 금지)
grep -E '^[A-Z_]+=' .env | cut -d= -f1
```

## Related

- F-CTX-01 (FAILURES.md) — API key 재질문 패턴 재발 방지
- `.env.example:3` — shorts_naberal 원본 레지스트리 경로 주석
- [project_claude_code_max_no_api_key](project_claude_code_max_no_api_key.md) — ANTHROPIC 금지 근거
