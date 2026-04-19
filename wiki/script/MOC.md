---
category: script
type: MOC
status: ready
tags: [script, moc, wiki-root]
updated: 2026-04-20
---

# Script — Map of Content

shorts_studio SCRIPT gate 관련 wiki 노드 인덱스. NLM 2-step 프롬프트 + 품질 패턴 + 4막 구조 + 대화 패턴 집약.

## 핵심 원칙

1. **NLM 2-노트북 2-step 분리** — 발굴(Step 1) + 제조(Step 2). 1-노트북 금지 (세션 70 확정).
2. **컷 단위 JSON 출력** — 통짜 대본 금지. 묘사 4요소(인상/움직임/감정/분위기) 각 컷에 강제.
3. **롱폼 우선** — 13-18분 롱폼이 원본, 30-60초 쇼츠는 파생물.
4. **외주 역할 분리** — NLM=시나리오 / Typecast=TTS / Runway Gen-4.5=I2V / 나베랄=기획·프롬프트·검수.

## Nodes

### Prompt Templates
- [[NLM_2STEP_TEMPLATE]] — Step 1 사건 발굴 + Step 2 시나리오 제조 프롬프트 skeleton (세션 70·77 박제)

### Quality Reviewer Rubric
- [[QUALITY_PATTERNS]] — Patterns A-D: 씬 플로우 공식 / 문장 길이 리듬 / 이음쇠 분포 / 감정=사실배치

### 작성 예정
- `4ACT_STRUCTURE.md` — 4막 시간/글자수 할당 (180s/300s/240s/180s, 1400/2400/1900/1400자), 대화 패턴 5종 배치 규칙
- `DUO_DIALOGUE_PATTERNS.md` — 탐정/조수 대화 5 패턴 (대리질문/교정/공포/감정앵커/강조)
- `EMOTION_TTS_MAPPING.md` — 탐정 Sullock Hong + 조수 voice preset × emotion matrix

## Related

- [[../continuity_bible/MOC]] — 채널 바이블 prefix (assembler 자동 주입)
- [[../render/runway_gen4_5]] — Runway Gen-4.5 어댑터 스펙 (작성 예정)
- [[../kpi/retention_3second_hook]] — 3초 retention hook 패턴 (이미 존재)

## 원본 참조 (read-only)

아래 문서는 `.preserved/harvested/` 또는 `/c/Users/PC/Desktop/shorts_naberal/longform/` 에 있는 원본. shorts_studio 는 **패턴 추출만** 수행 (코드 흡수 금지, 세션 #24 대표님 방침).

- `shorts_naberal/longform/PIPELINE.md` — 8-stage longform 파이프라인
- `shorts_naberal/longform/SCRIPT_SKILL.md` — 롱폼 스크립트 skill (4막 / 듀오 / 스키마)
- `shorts_naberal/longform/claudedocs/SCRIPT_QUALITY_GATE_CONTRACT.md` — Patterns A-D 원본
- `shorts_naberal/longform/claudedocs/CRIME_STORYTELLING_GUIDE.md` — 범죄 스토리텔링 가이드

---

*Created 2026-04-20 session #24 by 나베랄 감마, Phase 10 영상 품질 테스트 선행 작업.*
