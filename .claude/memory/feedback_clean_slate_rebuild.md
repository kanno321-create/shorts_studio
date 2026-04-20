---
name: feedback_clean_slate_rebuild
description: shorts_naberal 원본 수정 금지 원칙 + declarative config 포팅 예외 (세션 #26 확장)
type: feedback
---

# Clean Slate Rebuild 원칙

**원 박제**: 신규 스튜디오 창업 시 대표님 방침.
**확장**: 세션 #26 2차 batch — "imperative 코드는 신 구축 / declarative 설정값은 포팅 허용".

## 원칙

1. **`shorts_naberal/` 원본 수정 영구 금지** (도메인 절대 규칙 #6)
2. **Harvest는 `.preserved/harvested/` 에 읽기 전용 복사만** (Phase 3, chmod -w)
3. **신 구축이 기본** — 구 로직을 그대로 베끼지 않음

## §예외 확장 (세션 #26)

**3중 테스트 모두 통과 시 declarative config 포팅 허용**:

1. **재구현 비용 테스트**: 외부 API 상수 / 실 운영 튜닝 데이터라 새로 만들어도 동일한 값에 수렴
2. **원본 불변성 테스트**: shorts_naberal 원본은 건드리지 않고 복사만
3. **백지 설계 불가 테스트**: 로직이 아닌 **데이터** 이므로 "어떻게 구현할지" 가 아니라 "무엇을 값으로 쓸지" 의 문제

### 통과 사례 (세션 #26 2차)

- `config/voice-presets.json` (611줄, 11채널 × voice 매트릭스) — voice_id 는 외부 Typecast API 상수. 재설계하면 같은 값 도출.
- `config/channels.yaml` (693줄, 채널별 preset 매핑) — 동일 근거.
- `config/PROVENANCE.md` — import 이력 + 비 이관 13건 분류 박제.

### 통과 실패 사례

- 회계 공식 / hc_checks — 알고리즘 불변성은 로직이므로 신 구축.
- scripter agent 템플릿 — 아이덴티티 영역이므로 신 구축.

## 판정 질문

**"외부 상수/튜닝 데이터 vs 로직/아이덴티티?"**
- 전자 → 포팅 허용 (값만 복사)
- 후자 → 신 구축 (로직 재설계)

## Related

- [reference_shorts_naberal_voice_setup](reference_shorts_naberal_voice_setup.md) — 포팅된 voice 매트릭스 세부
- CLAUDE.md 도메인 절대 규칙 #6
