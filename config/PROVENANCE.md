# config/ Provenance

이 디렉토리의 각 파일이 **어디에서 왔고, 수정 가능 여부**를 기록하는 single source of truth.

`feedback_clean_slate_rebuild` 원칙 상 레거시 자산 흡수는 기본 금지이나, 세션 #26 예외 확장으로 **declarative 설정값** 은 포팅 허용. 이 파일은 해당 예외 적용 대상의 감사 기록.

---

## Import 이력

| 파일 | 원본 경로 | Import 시점 | 수정 허용 | 비고 |
|------|----------|------------|----------|------|
| `voice-presets.json` | `shorts_naberal/config/voice-presets.json` | 2026-04-20 세션 #26 | ✅ 복사본 수정 OK, 원본 touch 금지 | 611 lines, 19KB. JSON 주석 미지원 → header 삽입 불가, 이력은 이 PROVENANCE.md 로 대체 |
| `channels.yaml` | `shorts_naberal/config/channels.yaml` | 2026-04-20 세션 #26 | ✅ 복사본 수정 OK, 원본 touch 금지 | 693 lines, 30KB. 상단 YAML 주석 header 삽입 완료 |

## 원본 touch 금지 이유

`shorts_naberal` 은 대표님의 **live production** workspace. 원본 편집 시:
- 실 운영 중인 11 채널 영상 생산 파이프라인 breakage 위험
- 세션 #24 박제 "백지 상태 새 구축 원칙" — shorts_studio 가 신 구축이고 shorts_naberal 은 parallel live
- 분기된 두 카피가 drift 하는 건 감당 가능, 한 쪽이 깨지는 건 감당 불가

## 비 이관 자산 (의도적 흡수 금지)

아래 파일들은 `shorts_naberal/config/` 에 존재하지만 **shorts_studio 로 이관하지 않음** (Phase 2 검토 대상, D091-DEF-02 참조):

- `api-budgets.yaml` — API 비용 상한. shorts_studio 는 Phase 10 Circuit Breaker + cost tracking 으로 독립 설계 예정.
- `avatar-config.json` — 아바타 TTS (HeyGen 계열). shorts_studio scope 외.
- `channel_registry.py` — imperative 코드 (YAML 로드 → class). shorts_studio 는 pydantic model 신 구축 예정.
- `dubbing-config.json` — 더빙 설정. shorts_studio 는 subtitle 중심 설계.
- `duo-repertoire.json` — 듀오 대화 패턴. Phase 10 실측 후 검토.
- `music-config.json` — BGM 설정. shorts_studio 는 continuity_bible 에서 신 설계.
- `niche-profiles/` (디렉토리) — 장르 프로파일. Phase 10 batch window 검토.
- `oblique_strategies.json` — divergent ideation 전략 카드. Phase 47 ideator 로직 내장 (shorts_studio scope 외).
- `platform-accounts.json` — 업로드 계정 (YouTube/TikTok/Instagram). Phase 8 `scripts/publisher/` 가 이미 별도 관리.
- `jp-*.md` (2 파일) — 일본 채널 가이드. incidents-jp 채널 진출 시 재검토.
- `benchmark-48h-playbook.md` — 업로드 후 48시간 벤치마크 관리. shorts_studio Phase 10 ops 로드맵 scope.
- `learning-config.json` — 학습 파라미터. shorts_studio 는 HITL + Taste Gate 로 대체 설계.
- `curation/` (디렉토리) — 큐레이션 룰. Phase 10 batch window 검토.
- `channel_upload_profile.json` — 채널별 업로드 프로파일. Phase 8 remote publishing 에서 신 설계 완료.

## shorts_studio 고유 자산 (포팅 아님, 신 구축)

- `client_secret.json` (Google OAuth2 — YouTube API) — shorts_studio 창업 시 신규 생성
- `youtube_token.json` (OAuth 토큰) — 위와 동일

## 포팅 절차 (향후 신규 항목 추가 시)

1. **판정 질문**: "외부 API 상수 / 실 튜닝 데이터인가 (= declarative) vs 로직 / 아이덴티티인가 (= imperative/identity)?"
   - declarative → 포팅 허용
   - imperative / identity → 포팅 금지 (신 구축)
2. **복사**: `cp shorts_naberal/config/<file> shorts_studio/config/<file>`
3. **Header 삽입** (가능한 경우):
   - YAML / Python: `# Imported from: ...`
   - JSON / binary: 이 PROVENANCE.md 테이블에 추가
4. **원본 touch 금지 원칙 재확인**
5. **SESSION_LOG 박제**: import 시점, 원본 hash (선택), rationale

## 관련 메모리

- `feedback_clean_slate_rebuild` §예외 확장 — 포팅 허용 근거
- `reference_api_keys_location` — shorts_naberal/.env 원본 레지스트리
- `project_tts_stack_typecast` — voice-presets.json 소비자
- `reference_shorts_naberal_voice_setup` — voice-presets.json 매트릭스 상세
