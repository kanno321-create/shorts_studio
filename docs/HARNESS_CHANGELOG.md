# Harness Changelog — naberal-shorts-studio

> 이 파일은 `studios/shorts` 가 상속한 **naberal_harness (Layer 1 인프라)** 의
> 업데이트 이력을 스튜디오 관점에서 기록한다.
>
> - **하네스 본체 이력 source of truth**: `../../harness/STRUCTURE.md` §변경 이력
> - **이 파일 역할**: studio 가 "언제 무엇을 pull 했는지" 기록 (append-only log)

## 업데이트 이력

| 날짜 | 하네스 버전 | 변경 내용 | 적용 대상 | 세션 |
|------|-----------|----------|----------|------|
| 2026-04-18 | v1.0.0 | 초기 스캐폴드 — 5 templates + 3 Hooks + 5 공용 스킬 + 3 CLI scripts | 전체 신규 스튜디오 생성 | 세션 #10 (Phase 1) |
| 2026-04-19 | v1.1.0 | `harness/wiki/` 추가 (Tier 1 도메인-독립 RAG 저장소) | Phase 6 NotebookLM Fallback Chain 2차 계층 | 세션 #19 (Phase 6) |

## 업데이트 절차

1. **Pull**: `python ../../harness/scripts/new_domain.py update shorts --only <skill>`
2. **Review**: 변경 내용 검토 (destructive change 여부, Major/Minor/Patch 구분)
3. **Record**: 이 파일 상단 표에 append (append-only, 기존 엔트리 수정 금지)
4. **Cross-ref**: Major/Minor bump 은 `SESSION_LOG.md` 에도 교차 참조
5. **Commit**: `chore(harness): pull v{version} — {summary}`

## 참고 문서

- **하네스 설계 원칙**: `../../harness/docs/ARCHITECTURE.md` (2-Layer 모델)
- **하네스 Whitelist + 변경 절차**: `../../harness/STRUCTURE.md`
- **공용 스킬 패턴**: `../../harness/docs/PATTERNS.md` (6 agent team patterns)
- **도메인 창업 체크리스트**: `../../harness/docs/DOMAIN_CHECKLIST.md`
- **하네스 운영 헌법**: `../../harness/CLAUDE.md`

---

*Created: 2026-04-20 — CLAUDE.md Navigator 재설계 시 "하네스 변경 이력" 섹션을 별도 파일로 분리.*
