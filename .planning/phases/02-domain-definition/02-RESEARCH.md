# Phase 2: Domain Definition — Research

**Researched:** 2026-04-19
**Domain:** Structural / documentation (infra phase, no code)
**Confidence:** HIGH
**Researcher:** nabe-researcher (spawned by `/gsd:research-phase 2`)
**Consumer:** gsd-planner (next) → 02-PLAN.md

---

<user_constraints>
## User Constraints (from 02-CONTEXT.md)

### Locked Decisions

- **D2-A: Tier 1 Wiki = Minimal.** `naberal_harness/wiki/` 빈 폴더 + `README.md`만 생성. 실 노드(korean_honorifics_baseline 등)는 Phase 6 FAILURES Reservoir 패턴 발견 후. Phase 2에서 선제 시드 = 나중 갈아엎기 리스크.
- **D2-B: Tier 2 Wiki = Category + MOC Skeleton.** 5 카테고리 폴더(`algorithm/`, `ypp/`, `render/`, `kpi/`, `continuity_bible/`) + 각 `MOC.md` 스켈레톤. Phase 4 에이전트 프롬프트가 `@wiki/shorts/<category>/MOC.md`로 참조할 경로를 Phase 2에서 고정.
- **D2-C: Harvest Scope = A급 13건만 사전 판정.** `HARVEST_SCOPE.md`가 CONFLICT_MAP A급 13건만 "승계/폐기/통합-후-재작성" 3-way로 Phase 2에서 확정. B급 16건 + C급 10건은 Phase 3 harvest-importer 에이전트가 실제 Harvest 중 판정.
- **D2-D: CLAUDE.md 치환 = 중간 수준.** D-1~D-10 확정 사항만 구체적으로 반영. Phase 4~5 결정 수치(12 GATE 명칭, 17 inspector 카테고리 세부, 에이전트 수)는 `TBD (Phase X)` 명시.

### Claude's Discretion

- Tier 1 README.md 문체·구조 (표준 템플릿 결정)
- Tier 2 카테고리별 MOC.md 내부 placeholder 문구
- HARVEST_SCOPE.md 표 컬럼 순서/디자인
- CLAUDE.md 치환 문장의 세부 구조 (D-1~D-10 요지 유지 조건)
- `STRUCTURE_HISTORY/STRUCTURE_v1.0.0.md.bak` 백업 파일명 확정

### Deferred Ideas (OUT OF SCOPE)

- **Phase 3:** CONFLICT_MAP B급 16건 + C급 10건 전수 판정, 4 raw 디렉토리 실제 복사 + chmod -w, `_imported_from_shorts_naberal.md` 실제 생성
- **Phase 4:** 12 GATE 명칭 최종 확정, 17 inspector 6 카테고리 세부, 에이전트 총 12~20명 확정
- **Phase 6:** Tier 1 실제 노드(korean_honorifics_baseline, youtube_api_limits), Tier 2 5 카테고리 실제 내용 작성, NotebookLM 2-노트북 세팅, Continuity Bible Prefix 자동 주입 로직
- **미래 스튜디오 창립 시:** secondjob_naberal/wiki/의 도메인-독립 노드 추출 및 Tier 1 이관

</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| **INFRA-02** | 3-Tier 위키 디렉토리 물리 생성: Tier 1 `naberal_harness/wiki/` (STRUCTURE.md schema bump 필요), Tier 2 `studios/shorts/wiki/`, Tier 3 `studios/shorts/.preserved/harvested/` | § Schema Bump Procedure (Tier 1 선행 조건), § 3-Tier Wiki Creation Order (Hook 간섭 회피 DAG), § MOC.md Template (Tier 2 5 카테고리 실체) |

**Derived deliverables (from Success Criteria):**
1. 3 Tier 디렉토리 물리 존재 (INFRA-02 직접)
2. `naberal_harness/STRUCTURE.md` schema bump v1.0.0→v1.1.0 (INFRA-02 전제)
3. CLAUDE.md 5 TODO 치환 (도메인 scope 확정)
4. HARVEST_SCOPE.md 존재 (Phase 3 harvest-importer 입력)

</phase_requirements>

---

## § Overview

Phase 2는 **코드 변경 0줄**. 전부 구조·문서 작업이다. 그러나 **실행 순서 1번 틀리면 Hook이 모든 Write를 차단**한다. 핵심은 네 가지:

1. **Schema bump를 먼저, 폴더 생성은 그 다음** — `naberal_harness/hooks/pre_tool_use.py`가 STRUCTURE.md Whitelist 외 경로로의 Write 시도를 실시간 차단한다. `wiki/`가 Whitelist에 등재되기 전에 `wiki/README.md`를 쓰려 하면 Hook이 deny를 반환한다.
2. **3개 Tier는 서로 다른 레포** — Tier 1은 `naberal_group/harness/`(상위 레포), Tier 2는 `naberal_group/studios/shorts/`(이 레포), Tier 3은 동일 레포 `.preserved/harvested/`. 각각 다른 Whitelist가 적용된다.
3. **A급 13건은 이미 90% 답이 나와 있다** — SUMMARY.md §13 D-1~D-10 + §10 Build Order + 대표님의 2026-04-19 D-3 확정(3단 Producer) + D-7 확정(state machine)이 A-1/A-3/A-5/A-6/A-11/A-12를 이미 결정했다. 판정은 문서화 작업에 가깝다.
4. **CLAUDE.md 치환은 line-exact로 수술** — 5 지점만 교체, 98% 보존. `<!-- GSD:project-start -->` 블록(line 109~133)은 이미 올바르게 채워져 있으므로 **건드리지 않는다**.

**Primary recommendation:** Phase 2는 **4 웨이브**로 분해 — (W1) Schema bump 커밋, (W2) 3-Tier 폴더 + README + MOC 생성, (W3) CLAUDE.md 5 TODO 치환 + HARVEST_SCOPE.md 작성, (W4) 검증 (`structure_check.py` 재실행 + grep 확인). W1은 상위 레포에서, W2~W4는 studio 레포에서.

---

## § Schema Bump Procedure

### 7-Step Amendment Policy (STRUCTURE.md:93-111 기준, 실행 가능 형태로 정제)

**대상 파일:** `C:\Users\PC\Desktop\naberal_group\harness\STRUCTURE.md`
**대상 레포:** `naberal_group/` (상위, 이 studio 레포와 별도)
**변경 유형:** **Minor** (1.0.0 → 1.1.0) — STRUCTURE.md:103 "Minor: 새 폴더 추가" 기준 정확히 일치

#### Step 1: 정당성 검토 (pre-flight)
- **정말 필요한가?** → YES. Phase 1 상속 시 `naberal_harness/` 에는 `wiki/`가 없음. Tier 1 도메인-독립 RAG 저장소 필요 (D-4 NotebookLM Fallback Chain 2차 계층)
- **기존 폴더로 커버 가능?** → NO. `docs/`는 설계 문서, `skills/`는 공용 스킬. wiki는 노드 기반 Obsidian graph — 별도 폴더 필수
- **Confidence:** HIGH (D-1, D-4 직접 근거)

#### Step 2: 백업 생성
```bash
cd C:/Users/PC/Desktop/naberal_group/harness
cp STRUCTURE.md STRUCTURE_HISTORY/STRUCTURE_v1.0.0.md.bak
```

**주의:**
- `STRUCTURE_HISTORY/` 디렉토리는 이미 존재 (`.gitkeep`만 있음, 확인 완료)
- Windows `cp` 는 없음 — Git Bash (MINGW64) 또는 `Copy-Item` PowerShell. Bash에서는 그대로 작동
- 백업 파일 경로 확정: `naberal_group/harness/STRUCTURE_HISTORY/STRUCTURE_v1.0.0.md.bak`

#### Step 3: schema_version bump (YAML frontmatter 수정)

**현재 (STRUCTURE.md:1-5):**
```yaml
---
schema_version: 1.0.0
updated: 2026-04-18
authority: AUTHORITY
amendment_policy: "기존 백업 + 버전업 필수, PR 없이 절대 수정 금지"
---
```

**목표:**
```yaml
---
schema_version: 1.1.0
updated: 2026-04-19
authority: AUTHORITY
amendment_policy: "기존 백업 + 버전업 필수, PR 없이 절대 수정 금지"
---
```

단 2곳만 변경: `schema_version`, `updated`.

#### Step 4: Whitelist 수정 (STRUCTURE.md:65-67 블록 확장)

**현재 (line 65-67):**
```
└── STRUCTURE_HISTORY/             [NECESSARY] 설계 변경 이력
    └── .gitkeep
```

**목표 — 직전에 `wiki/` 블록 삽입:**
```
├── wiki/                          [NECESSARY] Tier 1 도메인-독립 지식 노드 (RAG Fallback Chain 2차 계층)
│   └── README.md                  [NECESSARY] Tier 1 정의 + 사용 규칙
│
└── STRUCTURE_HISTORY/             [NECESSARY] 설계 변경 이력
    └── .gitkeep
```

**주의:**
- 트리 마지막 항목(`STRUCTURE_HISTORY/`)은 `└──` prefix. `wiki/`를 그 위에 삽입하면 `├──`가 됨
- Whitelist 태그 `[NECESSARY]` 사용 (empty 허용 폴더 아님 — README.md는 반드시 존재)
- `structure_check.py:41-70` 파싱 로직은 들여쓰기 0~4 chars만 루트 인식 → 새 엔트리가 루트 레벨이어야 함

#### Step 5: 변경 이력 추가 (STRUCTURE.md:128-133 테이블 확장)

**현재:**
```
| 버전 | 날짜 | 변경 내용 | 사유 |
|-----|------|---------|------|
| 1.0.0 | 2026-04-18 | 초기 창립 | naberal_harness v1.0 스캐폴드 |
```

**목표:**
```
| 버전 | 날짜 | 변경 내용 | 사유 |
|-----|------|---------|------|
| 1.0.0 | 2026-04-18 | 초기 창립 | naberal_harness v1.0 스캐폴드 |
| 1.1.0 | 2026-04-19 | `wiki/` 추가 (Tier 1 도메인-독립 RAG 저장소) | naberal-shorts-studio Phase 2 INFRA-02 — 3-Tier 위키 시스템 구축, NotebookLM Fallback Chain 2차 계층 |
```

#### Step 6: 커밋 (harness 레포에서)
```bash
cd C:/Users/PC/Desktop/naberal_group/harness
git add STRUCTURE.md STRUCTURE_HISTORY/STRUCTURE_v1.0.0.md.bak
git commit -m "structure: v1.1.0 — add wiki/, reason: Tier 1 RAG for shorts studio Phase 2 INFRA-02"
```

**커밋 메시지 규약 (STRUCTURE.md:109-111 명시):**
```
structure: v{new} — add {folder}, reason: {why}
```

#### Step 7: 검증 재실행
```bash
cd C:/Users/PC/Desktop/naberal_group/harness
python scripts/structure_check.py
```
- 출력: 경고 0건 (wiki/가 Whitelist에 등재되었으므로 아직 파일이 없어도 통과)
- 만약 `--strict` 플래그 사용 시 wiki/가 없다고 경고할 수 있음 → 보통 모드로 실행

### ⚠️ Schema Bump 주의사항

| 위험 | 대응 |
|------|------|
| 상위 레포와 studio 레포 혼동 | **명확**: schema bump는 `naberal_group/harness/` 레포에서만. studio 레포에는 영향 없음 (submodule 아님, 형제 디렉토리) |
| 백업 누락 | Step 2가 누락되면 STRUCTURE.md:95 "기존 백업 + 버전업 필수" 위반 → 다음 harness-audit에서 감사 실패 |
| Whitelist 삽입 위치 오류 | `STRUCTURE_HISTORY/` 직전, 알파벳 순이 아닌 논리 순서(docs → STRUCTURE_HISTORY 흐름 중간에 wiki 삽입) |
| structure_check.py 미실행 | Step 7 생략 시 Phase 2 Success Criteria #2 "Whitelist 위반 없음" 검증 불가 |
| commit message 형식 | STRUCTURE.md:109-111 규약 엄수. `docs:` 나 `feat:` 접두어 금지, `structure:` 만 허용 |

**Confidence:** HIGH — 모든 단계가 STRUCTURE.md 본문 line 93~111에 명시됨.

---

## § 3-Tier Wiki Creation Order + Hook Interaction

### Hook 간섭 메커니즘 (실측)

`naberal_harness/hooks/pre_tool_use.py` 는 **두 층 검증**:

1. **deprecated 패턴 검사** (line 63-76): `deprecated_patterns.json` regex 매칭 → 차단
2. **구조 Whitelist 검사** (line 79+, `check_structure_allowed`): Write 대상 경로가 STRUCTURE.md Whitelist 외부면 차단

studio 레포는 자체 `STRUCTURE.md` 또는 `.claude/allowed_paths.json`를 가질 수 있으나 Phase 1 상속 직후 studios/shorts/에는 studio-level STRUCTURE.md가 **없다** (확인 필요 — 현재 공개 문서에선 미언급). Phase 1에서 harness 복사만 했으므로 studio 레포의 Hook은 harness copy의 로직을 쓰되, 레포 루트가 다름.

**결론:** Tier 1(`naberal_harness/wiki/`) 생성 시 harness STRUCTURE.md Whitelist 검사 발동. Tier 2/3(`studios/shorts/wiki/`, `studios/shorts/.preserved/harvested/`)는 studio 레포의 Hook이 적용되며, studio 레포의 Whitelist 구성에 따라 다름.

### 작업 DAG (실행 순서, strict)

```
W1 [harness repo]
  ├── Step 1-2: 정당성 검토 + 백업 생성
  ├── Step 3-5: STRUCTURE.md 수정 (frontmatter + Whitelist + 이력)
  ├── Step 6: git commit (harness/ 레포)
  └── Step 7: structure_check.py 검증 ✓
       │
       ▼ (W1 완료 선행)
W2a [harness repo]
  ├── mkdir naberal_harness/wiki/
  └── Write naberal_harness/wiki/README.md (Tier 1 정의)
       │
       ▼ (병렬 가능, 독립 레포)
W2b [studio repo]
  ├── mkdir studios/shorts/wiki/
  ├── mkdir studios/shorts/wiki/{algorithm,ypp,render,kpi,continuity_bible}
  ├── Write studios/shorts/wiki/README.md (Tier 2 정의)
  └── Write studios/shorts/wiki/<5 categories>/MOC.md (×5 files)
       │
       ▼ (병렬 가능)
W2c [studio repo]
  ├── mkdir studios/shorts/.preserved/
  └── mkdir studios/shorts/.preserved/harvested/
       (내부 파일은 Phase 3에서 채움. 지금은 빈 디렉토리 + .gitkeep)
       │
       ▼
W3 [studio repo]
  ├── Edit studios/shorts/CLAUDE.md (5 line-exact 수술)
  └── Write studios/shorts/.planning/phases/02-domain-definition/02-HARVEST_SCOPE.md
       │
       ▼
W4 [verification]
  ├── cd harness && python scripts/structure_check.py → 경고 0건
  ├── ls naberal_harness/wiki/ → README.md 존재
  ├── ls studios/shorts/wiki/ → 5 카테고리 + README.md 존재
  ├── ls studios/shorts/wiki/*/MOC.md → 5개 존재
  ├── ls studios/shorts/.preserved/harvested/ → 디렉토리 존재
  ├── grep -c "TODO" studios/shorts/CLAUDE.md → 0 (모든 TODO 치환)
  └── git log --oneline harness/ → v1.1.0 커밋 확인
```

### 왜 이 순서인가

- **W1이 W2a 선행** — Schema bump 이전에 `naberal_harness/wiki/README.md` Write 시도하면 `pre_tool_use.py`의 Whitelist 검사가 wiki/를 "알 수 없는 경로"로 분류 → 차단
- **W2b는 W1과 병렬 가능** — studio 레포는 별도 Hook context. studio 레포가 `wiki/`를 자체 Whitelist에 이미 포함하는지 확인 필요 (Phase 1 new_domain.py가 studio용 STRUCTURE.md를 생성했는지 → Phase 1 세션 #10 확인 필요). **안전 가정:** studio 레포는 자체 STRUCTURE.md가 없거나 상속받은 느슨한 구성일 가능성. 만약 차단되면 studio-level schema bump도 필요 (추가 task)
- **W2c는 빈 디렉토리만** — `.preserved/harvested/`는 Phase 3에서 4 raw 디렉토리 + chmod -w 작업. Phase 2는 존재 증명만 (Success Criteria #1)
- **W3은 W2 완료 후** — CLAUDE.md에 `@wiki/shorts/<category>/MOC.md` 언급이 있으면 MOC 파일이 먼저 존재해야 참조 무결성 보장

### Studio-level Hook 상태 검증 (OPEN QUESTION — Planner 확인 필요)

**Planner 주의:** `studios/shorts/.claude/hooks/pre_tool_use.py` 가 Phase 1에 설치됐는지, 그리고 **studio-level Whitelist가 있는지** 확인 필요. 없다면 W2b/W2c는 Hook 간섭 없이 진행 가능. 있다면 studio-level STRUCTURE.md도 동일한 amendment 절차 필요 (OPEN ITEM).

`settings.json` 확인 명령: `cat studios/shorts/.claude/settings.json` — Hook 등록 여부 확인.

**Confidence:** HIGH (harness side) / MEDIUM (studio side — Phase 1 산출물 직접 검증 없이 추론)

---

## § MOC.md Template (Obsidian Standard)

### Frontmatter 표준 (secondjob_naberal/wiki/MOC.md 패턴 분석)

secondjob_naberal MOC.md는 frontmatter 없이 본문만 있으나, `wiki/README.md:1-3`은 YAML frontmatter 사용:
```yaml
---
tags: [readme, vault-home]
---
```

노드 파일들은 표준 4 필드: `tags / status / category / updated` (wiki/README.md:110-114 확인).

### Tier 2 MOC.md 표준 템플릿 (5 카테고리 공통)

```markdown
---
category: {algorithm|ypp|render|kpi|continuity_bible}
status: scaffold
tags: [moc, shorts, {category}]
updated: 2026-04-19
---

# {Category Display Name} — Map of Content

> Tier 2 도메인-특화 지식 노드 맵. naberal-shorts-studio 전용.
> 실제 노드 내용은 Phase 6 (Wiki + NotebookLM Integration) 에서 채워짐.

## Scope

{한 줄 스코프 — 이 카테고리가 다루는 주제 경계}

## Planned Nodes

> Phase 6에서 채워질 노드 placeholder. 현재는 scaffold.

- [ ] `{node_1}` — {한 줄 설명}
- [ ] `{node_2}` — {한 줄 설명}
- [ ] `{node_3}` — {한 줄 설명}

## Related

- **Tier 1** (도메인-독립, `../../../../harness/wiki/`): (Phase 6에서 링크)
- **Other Tier 2 categories**: (Phase 6에서 링크)
- **Root CLAUDE.md**: [[../../CLAUDE.md]] — domain scope 참조

## Source References

- **Research basis**: `.planning/research/SUMMARY.md` §14 (17 Novel Techniques)
- **Requirements**: `.planning/REQUIREMENTS.md` §WIKI
- **Agent consumer**: Phase 4 에이전트 prompts가 `@wiki/shorts/{category}/MOC.md` 형식으로 참조

---

*Scaffolded: 2026-04-19 (Phase 2 Domain Definition)*
*Next update: Phase 6 (NotebookLM integration + FAILURES Reservoir)*
```

### 왜 이 구조인가

- **Frontmatter** — secondjob_naberal 관행 준수 (wiki/README.md:112-116 "모든 노드는 frontmatter")
- **Scope 한 줄** — Phase 4 에이전트 prompt 작성 시 "이 카테고리가 뭘 다루는지" 1회 읽기로 파악 가능
- **Planned Nodes** — Phase 6 작업자가 "무엇을 채워야 하는지" 명확. `- [ ]` checkbox로 진행 추적 가능
- **Related** — Tier 1 경로(`../../../../harness/wiki/`)는 상대 경로. studio 레포에서 harness 레포로 가려면 `../../..`(studio→naberal_group→harness). 실제로는 **4단계** (studios/shorts/wiki/algorithm/ → studios/shorts/wiki → studios/shorts → studios → naberal_group → harness/wiki). **정확한 상대 경로: `../../../../harness/wiki/`**
- **Source References** — Phase 6 작업자가 "어느 research 노드에서 근거 가져올지" 즉시 확인 가능

### Tier 2 README.md 표준 템플릿 (루트)

```markdown
---
tags: [readme, wiki-home, tier-2, shorts]
---

# 📚 naberal-shorts-studio — Tier 2 Wiki

도메인-특화 지식 노드. naberal-shorts-studio 전용 RAG 소스.

## Tier 분류

- **Tier 1** (`../../../harness/wiki/`): 도메인-독립 공용 노드 (한국어 존댓말 baseline, YouTube API 한도 등)
- **Tier 2** (이 폴더): 쇼츠 도메인 전용 (알고리즘, YPP 기준, 렌더 스택, KPI, Continuity Bible)
- **Tier 3** (`../.preserved/harvested/`): 과거 shorts_naberal 자산 이관 — 읽기 전용 불변 (Phase 3 chmod -w)

## 카테고리 (5)

| 카테고리 | Scope | MOC |
|----------|-------|-----|
| `algorithm/` | YouTube Shorts 추천 알고리즘 + ranking 요소 | [[algorithm/MOC]] |
| `ypp/` | YouTube Partner Program 진입 조건 | [[ypp/MOC]] |
| `render/` | Remotion v4 + Kling 2.6 Pro / Runway Gen-3 Alpha Turbo 렌더 스택 | [[render/MOC]] |
| `kpi/` | 3초 hook retention / 완주율 / 평균 시청 지표 | [[kpi/MOC]] |
| `continuity_bible/` | 색상 팔레트 + 카메라 렌즈 + 시각 스타일 prefix (D-1) | [[continuity_bible/MOC]] |

## NotebookLM 연동 (Phase 6)

- **노트북 A: 일반** — shorts 도메인 일반 지식 (알고리즘, YPP, 렌더)
- **노트북 B: 채널바이블** — 채널 정체성 (Continuity Bible, 탐정/조수 페르소나, 색상 팔레트)
- Fallback Chain: NotebookLM RAG → grep wiki/ → hardcoded defaults (WIKI-04)

## 현재 상태

**Phase 2 (2026-04-19):** Scaffold — 5 카테고리 폴더 + MOC 스켈레톤만 존재. 실 노드는 Phase 6.

**추가 절차:**
1. Phase 6 실행 시 각 MOC.md의 `Planned Nodes` checkbox를 채우며 노드 파일 생성
2. 노드 생성 시 frontmatter `status: stub → ready` 승격
3. Tier 1 이관 대상 노드 발견 시 Phase 6 검토 후 batch 이관

---

*Scaffolded: 2026-04-19 (Phase 2 Domain Definition)*
```

### Tier 1 README.md 표준 템플릿 (harness/wiki/README.md)

```markdown
---
tags: [readme, wiki-home, tier-1, harness]
---

# 📚 naberal_harness — Tier 1 Wiki

도메인-독립 공용 지식 노드. 모든 Layer 2 스튜디오(shorts, blog, rocket, …)가 공유하는 **기반 정보 저장소**.

## Tier 1의 정의

- **범위**: 특정 도메인에 종속되지 않는 지식 — 예: 한국어 존댓말 baseline, YouTube API 한도 공통값, 저작권 일반 규칙
- **대조**: Tier 2 (`studios/<name>/wiki/`) = 도메인 전용 지식
- **Fallback Chain**: RAG 쿼리 실패 시 `studios/<name>/wiki/` (Tier 2) → `harness/wiki/` (이 폴더) → hardcoded defaults

## 현재 상태 (2026-04-19)

**빈 스캐폴드.** 실제 노드는 **첫 스튜디오(naberal-shorts-studio)의 Phase 6 이후** FAILURES Reservoir 패턴 발견 시점에 추가.

### 향후 추가 예정 노드 (예시)

- `korean_honorifics_baseline.md` — 한국어 존댓말/반말 구분 표준 (shorts_studio `ins-korean-naturalness`가 먼저 쓰고, 2번째 스튜디오가 쓰기 시작하면 Tier 1으로 이관)
- `youtube_api_limits.md` — YouTube Data API v3 quota 공통 (업로드 쿼터, analytics 쿼터)
- `copyright_korean_law.md` — 한국 저작권 기본 (shorts_studio와 blog_studio 공유 시 Tier 1 승격 대상)

## 노드 추가 절차

**⚠️ 이 폴더 신규 파일 생성은 STRUCTURE.md schema bump 필요** — `wiki/` 자체는 v1.1.0에서 등재됨. 하위 노드 추가는 Minor bump (Patch) 필요할 수 있음.

1. 스튜디오가 Tier 2에 노드를 먼저 작성
2. 2번째 스튜디오가 동일 노드 필요 시작
3. 대표님 승인 후 Tier 1 이관 (batch, 3+ 개 한번에)
4. STRUCTURE.md amendment 절차 준수 (버전업 + 백업 + 이력)

## Source 인용 원칙

Tier 1 노드는 **도메인-독립 기반 사실**만 기록. 의견·전략·최적화는 Tier 2로.

- ✅ "YouTube Data API v3 업로드 videos.insert = 1600 quota units"
- ❌ "한국 채널은 피크 시간 20-23 KST에 업로드해야 한다" (← 이건 Tier 2 shorts `algorithm/`)

---

*Created: 2026-04-19 (Phase 2 Domain Definition — naberal-shorts-studio)*
*First node addition: TBD (Phase 6 or later)*
```

### MOC 카테고리별 Planned Nodes 드래프트 (Phase 6 미리보기 / Planner 참고용)

Phase 2에서는 **placeholder만** 쓰고, 실제 채움은 Phase 6. 아래는 Planner가 MOC 스켈레톤 작성 시 "가장 그럴듯한 3-5개 노드 후보"로 참고:

**algorithm/MOC.md Planned Nodes:**
- `ranking_factors.md` — YouTube Shorts 추천 신호 (완주율, 리텐션, CTR, 재시청)
- `viewer_retention_curve.md` — 3초 hook 이후 retention 곡선 분석
- `cross_platform_penalties.md` — TikTok/IG 비-적응 cross-post 알고리즘 패널티 (AF-3 근거)
- `shorts_shelf_selection.md` — Shorts 추천 shelf 진입 조건

**ypp/MOC.md Planned Nodes:**
- `shorts_fund_history.md` — Shorts Fund 2023 종료 + 현 pool 45% (SUMMARY §11)
- `rpm_korean_benchmark.md` — KR RPM ~$0.20/1K views (SUMMARY §11, 보수값)
- `eligibility_path.md` — 1000 구독 + 10M views/년 or 1000 구독 + 4000 watch hours
- `reused_content_defense.md` — Production metadata 첨부 규칙 (PUB-04, E-P2 차단)

**render/MOC.md Planned Nodes:**
- `kling_api_spec.md` — Kling 2.6 Pro API (HMAC 서명, 가격, rate limits)
- `runway_fallback_policy.md` — Kling 실패 시 Runway Gen-3 Alpha Turbo 전환 조건
- `remotion_composition_schema.md` — Remotion v4 composition 표준 구조
- `shotstack_color_grading.md` — 일괄 색보정 API (T14)
- `low_res_first_pipeline.md` — 720p → AI 업스케일 2단계 (T4)

**kpi/MOC.md Planned Nodes:**
- `three_second_hook_target.md` — retention > 60% (SUMMARY §9 Korean specifics)
- `completion_rate_target.md` — 완주율 > 40%
- `avg_watch_duration_target.md` — > 25초
- `kpi_log_template.md` — 월 1회 `kpi_log.md` 자동 생성 포맷 (KPI-02)

**continuity_bible/MOC.md Planned Nodes:**
- `color_palette.md` — 채널 고정 색상 (hex codes)
- `camera_lens_spec.md` — 35mm/50mm 고정 설정 + shot type
- `visual_style_prefix.md` — 모든 이미지/영상 API 호출 prefix 템플릿 (T12)
- `duo_persona_bible.md` — 탐정(하오체) + 조수(해요체) 대화 양식
- `thumbnail_signature.md` — 1-2 한글 글자 / 하단 30% 회피 / Nano Banana Pro 프롬프트

**Confidence:** MEDIUM-HIGH — SUMMARY §14 + §9 + §2 직접 근거. 최종 리스트는 Phase 6 작업자 재량.

---

## § CLAUDE.md TODO 5 Replacement (Line-Exact Surgery)

### 현재 상태 (검증 완료, studios/shorts/CLAUDE.md 실측)

파일 전체 길이: **409 lines**. 5개 TODO 위치 line-exact:

| Position | Line | 현재 내용 | 치환 대상 |
|----------|------|-----------|-----------|
| **#1 DOMAIN_GOAL** | Line 3 | `TODO: 도메인 목표 1문장 작성` | D2-D 치환 문장 |
| **#2 PIPELINE_FLOW** | Line 41 | ` ``` ` (line 40)로 시작하는 코드블록 안에 `TODO: 파이프라인 다이어그램 작성` | 12 GATE 상태머신 다이어그램 (TBD 주석 포함) |
| **#3 DOMAIN_ABSOLUTE_RULES** | Line 45 | `- TODO: 도메인 절대 규칙 작성` | 8개 Hard Constraint bullet |
| **#4 hive 목표** | Line 66 | `**목표**: TODO: 하네스 목표 작성` | "주 3~4편 자동 제작 + YPP 궤도" |
| **#5 TRIGGER_PHRASES** | Line 68 | `**트리거**: "shorts 돌려", "shorts 시작"` (placeholder 수준) | 한국어 자연어 4-5개 |

**추가 발견 — Line 7 오타:**
```
Line 7: **Layer 1**: `naberal_harness` vv1.0
```
`vv1.0` → `v1.0.1` (이중 v 오타 + 실제 하네스는 v1.0.1). **Planner는 이것도 수정 대상에 포함 권장**.

**또한 Line 64 읽기 다시 확인:**
```
Line 64: ## 하네스: shorts-hive (e.g., shorts-hive)
```
`(e.g., shorts-hive)`는 템플릿 placeholder. 실제 studio는 "shorts-hive" 확정 사용 — `(e.g., shorts-hive)` 주석 제거 권장.

### 치환 명세 (Line-Exact Before/After)

#### Replacement #1: Line 3 DOMAIN_GOAL

**Before:**
```markdown
# shorts — AI 영상 제작

TODO: 도메인 목표 1문장 작성
```

**After:**
```markdown
# shorts — AI 영상 제작

AI 에이전트 팀이 자율 제작하는 주 3~4편 YouTube Shorts로 대표님의 기존 채널을 YPP 궤도에 올리는 스튜디오. **Core Value = 외부 수익 발생** (기술 성공 ≠ 비즈니스 성공).
```

#### Replacement #1b (추가): Line 7 오타 수정

**Before:**
```markdown
**Layer 1**: `naberal_harness` vv1.0
```

**After:**
```markdown
**Layer 1**: `naberal_harness` v1.0.1
```

#### Replacement #2: Line 38-42 PIPELINE_FLOW

**Before:**
```markdown
## Pipeline → 도메인 오케스트레이터 참조

```
TODO: 파이프라인 다이어그램 작성
```
```

**After:**
```markdown
## Pipeline → 도메인 오케스트레이터 참조

```
IDLE
  → TREND → NICHE → RESEARCH_NLM → BLUEPRINT
  → SCRIPT → POLISH → VOICE → ASSETS
  → ASSEMBLY → THUMBNAIL → METADATA
  → UPLOAD → MONITOR → COMPLETE
```

> 위 GATE 이름·개수는 **대표 후보, Phase 5 Orchestrator v2 작성 시 최종 확정** (D-7 state machine, 500~800줄 구현).
> 실 오케스트레이터 구현: `scripts/orchestrator/shorts_pipeline.py` (Phase 5)
```

#### Replacement #3: Line 44-45 DOMAIN_ABSOLUTE_RULES

**Before:**
```markdown
### 도메인 절대 규칙
- TODO: 도메인 절대 규칙 작성
```

**After:**
```markdown
### 도메인 절대 규칙

1. **`skip_gates=True` 금지** — `pre_tool_use.py` regex 차단 (CONFLICT_MAP A-6 재발 방지)
2. **`TODO(next-session)` 금지** — `pre_tool_use.py` regex 차단 (A-5 재발 방지)
3. **try-except 침묵 폴백 금지** — 명시적 `raise` + GATE 기록 필수
4. **T2V 금지 — I2V only** — Anchor Frame 강제 (NotebookLM T1)
5. **Selenium 업로드 영구 금지** — YouTube Data API v3 공식만 (AF-8)
6. **`shorts_naberal` 원본 수정 금지** — Harvest는 `.preserved/harvested/`에 읽기 전용 복사만 (Phase 3, chmod -w)
7. **K-pop 트렌드 음원 직접 사용 금지** — KOMCA + Content ID strike 위험 (AF-13). 하이브리드 오디오: 트렌딩 3~5초 → royalty-free crossfade (T11)
8. **주 3~4편 페이스 준수** — 일일 업로드 = 봇 패턴 + Inauthentic Content 직격 (AF-1, AF-11). 48시간+ 랜덤 간격 + 한국 피크 시간 (평일 20-23 / 주말 12-15 KST)
```

#### Replacement #4: Line 64-66 hive 목표

**Before:**
```markdown
## 하네스: shorts-hive (e.g., shorts-hive)

**목표**: TODO: 하네스 목표 작성

**트리거**: "shorts 돌려", "shorts 시작"
```

**After:**
```markdown
## 하네스: shorts-hive

**목표**: 주 3~4편 자동 영상 제작 + YPP 진입 궤도(1000구독 + 10M views/년) 확보. Core Value = 외부 YouTube 광고 수익 발생.

> **TBD (Phase 4 Agent Team Design)**: 에이전트 개수·이름 최종 확정 (현재 추정: Producer 11명 + Inspector 17명 + Supervisor 1명 = 29명, 범위 12~20 재조정 예정)
```

#### Replacement #5: Line 68 TRIGGER_PHRASES

**Before:**
```markdown
**트리거**: "shorts 돌려", "shorts 시작"
```

**After:**
```markdown
**트리거**: "쇼츠 돌려" / "영상 뽑아" / "shorts 파이프라인" / "YouTube 업로드" / "쇼츠 시작"
```

### 유지 영역 (절대 수정 금지)

| 영역 | Line | 이유 |
|------|------|------|
| Identity 섹션 | 16~27 | 나베랄 감마 정체성 + 대표님 호칭 — shorts 도메인 적합, 변경 불필요 |
| Session Init | 29~35 | 표준 프로토콜 — 변경 불필요 |
| Skill Routing 테이블 | 49~55 | TBD 상태지만 Phase 4에서 채움 — 지금 건드리면 drift |
| 공용 하네스 스킬 섹션 | 56~61 | Phase 1 상속 결과 — 정확함 |
| 하네스 변경 이력 | 74~78 | 2026-04-18 스캐폴드 이력 — 유지 |
| Context Tiers 테이블 | 82~93 | 표준 프로토콜 |
| 운영 원칙 | 97~104 | Lost-in-the-Middle 대응 — 모든 스튜디오 공통 |
| GSD 블록 | 109~133 | `<!-- GSD:project-start -->` ~ `<!-- GSD:project-end -->` — 이미 정확. PROJECT.md 소스 자동 관리 영역 |
| Stack 블록 | 135~377 | `<!-- GSD:stack-start -->` ~ `<!-- GSD:stack-end -->` — STACK.md 자동 합성 |
| Conventions/Architecture 블록 | 379~389 | 플레이스홀더, Phase 4+에서 채움 |
| Workflow / Profile 블록 | 391~409 | GSD 자동 관리 |

**치환 후 grep 검증:**
```bash
grep -c "TODO" studios/shorts/CLAUDE.md
# 예상 출력: 0  (모든 TODO 제거 확인)
```

단, `<!-- GSD:stack-end -->` 뒷부분(CONVENTIONS, ARCHITECTURE 섹션)은 "Conventions not yet established"라는 placeholder 문장이 있음. 이건 TODO 아니므로 grep 대상 제외됨 (그대로 유지).

**Confidence:** HIGH — CLAUDE.md 409줄 전수 확인 완료.

---

## § HARVEST_SCOPE.md Schema

### 파일 위치
`studios/shorts/.planning/phases/02-domain-definition/02-HARVEST_SCOPE.md`

**이유:** Phase 2 산출물이므로 phase 디렉토리 내부. Phase 3 harvest-importer 에이전트가 `@.planning/phases/02-domain-definition/02-HARVEST_SCOPE.md`로 참조.

**대안 위치 (Planner 판단):** `studios/shorts/.planning/HARVEST_SCOPE.md` — phase 독립 문서로 승격. ROADMAP Success Criteria #4에서 "HARVEST_SCOPE.md 존재"로만 언급되어 위치 자유. **권장: phase 디렉토리 내부 (첫 위치)** — Phase 2 세션 에셋으로 유지, Phase 3에서 `HARVEST_DECISIONS.md`로 승격 가능.

### Schema 구조

```markdown
# HARVEST_SCOPE — Phase 3 Harvest 범위 결정서

**Created:** 2026-04-19 (Phase 2 Domain Definition)
**Consumer:** Phase 3 harvest-importer 에이전트 (spawned by `/gsd:execute-phase 3`)
**Source:** `shorts_naberal/.planning/codebase/CONFLICT_MAP.md` (A:13 / B:16 / C:10 = 39)
**Purpose:** Phase 2가 A급 13건만 사전 판정. B/C급 26건은 Phase 3 위임.

---

## § A급 13건 사전 판정 (Phase 2 완결)

| ID | 드리프트 요약 | 판정 | 근거 | 실행 지시 |
|----|---------------|------|------|-----------|
| A-1 | Runway vs Kling primary | **통합-재작성** (Kling primary + Runway backup) | D-3 STACK §Visual, SUMMARY §2 | Phase 4 video-sourcer 에이전트가 Kling primary, Runway fallback 체인 구현. 원본 config/stock-search-config.json은 승계 금지 |
| A-2 | cuts[] vs segments[] 스키마 | **승계** (cuts[] canonical) | 세션 77 실측 사용 | Phase 4 scripter 에이전트가 cuts[]/narration 스키마만 출력. segments[]/text 역정규화 코드 제거 |
| A-3 | researcher vs NLM-fetcher 진입점 | **통합-재작성** (NLM-fetcher 승계, researcher 폐기) | D-4 NotebookLM RAG, 세션 77 CLAUDE.md | Phase 4 agent 팀에 nlm-fetcher + researcher(fallback only). create-shorts 스킬 전면 재작성 |
| A-4 | unique 60/80/100% 기준 | **통합-재작성** (ins-license 단일 ≥80% 기준) | SUMMARY §7 Reviewer 카테고리, NotebookLM T15 LogicQA | Phase 4 ins-license만 구현 (ins-matching의 unique 항목 + ins-duplicate 완전 폐기) |
| A-5 | TODO(next-session) 4곳 미연결 | **전수 폐기** | D-6 pre_tool_use regex 차단, AF-14 | Phase 3 harvest-importer는 orchestrate.py 자체를 `api_wrappers_raw/`에 복사하되, Phase 5에서 재작성 시 절대 import 금지. Hook이 문자열 자체 차단 |
| A-6 | skip_gates=True 디버그 경로 | **전수 폐기** | D-6, D-7, AF-14, SUMMARY §8 | orchestrate.py:1239-1291 블록은 harvest blacklist. Phase 5 state machine은 파라미터 자체 부재 |
| A-7 | Morgan tempo 0.93 vs 0.97 | **통합-재작성** (0.93 canonical) | DESIGN_BIBLE:179 기준점 | Phase 4 voice-producer 에이전트가 0.93 고정. config 승계 시 0.97 필드 제거 |
| A-8 | "놓지 않았습니다" 시그니처 | **통합-재작성** (조건부 허용 = ins-structure 규칙) | 세션 77 최종 확정본 | Phase 4 ins-structure 에이전트가 "Part1/마지막만 허용" 규칙 구현. scripter FAILURES deprecated 마킹 |
| A-9 | "탐정님" 호명 금지 | **승계** (호명 금지 규칙) | 17일 voice/AGENT.md, feedback_assistant_no_detective_honor | Phase 4 ins-korean-naturalness 또는 ins-duo가 "탐정님" regex 차단 |
| A-10 | "조수" vs "마스코트" 명칭 | **통합-재작성** ("조수" 통일, config key `assistant`) | 세션 77 CLAUDE.md | Phase 3 harvest 시 longform/ 경로는 이관 대상 아님 (쇼츠만). shorts 관련 channels.yaml만 참조하여 "assistant" key로 재작성 |
| A-11 | longform-scripter.md 2곳 충돌 | **전수 폐기** (shorts 스코프 외) | 본 스튜디오는 shorts 전용 | Phase 3 harvest에서 longform/ 디렉토리 전체 스킵 |
| A-12 | create-shorts vs create-video 진입점 | **통합-재작성** (create-shorts 승계, create-video 폐기) | A-3과 연결, shorts 전용 | Phase 4 에이전트 설계 시 create-shorts 스킬 재작성, create-video는 harvest blacklist |
| A-13 | 영상 소스 우선순위 (Veo 5개 vs Runway 6~8) | **통합-재작성** (Kling primary → Runway backup only, Veo 미사용) | SUMMARY §2 STACK 확정 | Phase 4 video-sourcer 프롬프트가 Kling 단일 primary + Runway fallback. Veo 완전 배제 (cost + I2V 일관성) |

### 판정 분포
- **승계**: 2건 (A-2, A-9) — 그대로 받아씀
- **폐기**: 3건 (A-5, A-6, A-11) — 참조 금지
- **통합-재작성**: 8건 (A-1, A-3, A-4, A-7, A-8, A-10, A-12, A-13) — 개념만 참조, Phase 4+에서 새로 구현

---

## § Harvest Blacklist (절대 import 금지)

Phase 3 harvest-importer 에이전트는 **이 목록을 read-lock**. 복사 시 skip.

```python
HARVEST_BLACKLIST = [
    # A-6: skip_gates 디버그 경로
    {"file": "scripts/orchestrator/orchestrate.py", "lines": "1239-1291", "reason": "A-6 skip_gates=True block"},

    # A-5: TODO(next-session) 미연결 4곳
    {"file": "scripts/orchestrator/orchestrate.py", "lines": "520", "reason": "A-5 TODO(next-session) wire ins-narration"},
    {"file": "scripts/orchestrator/orchestrate.py", "lines": "781", "reason": "A-5 TODO(next-session)"},
    {"file": "scripts/orchestrator/orchestrate.py", "lines": "1051", "reason": "A-5 TODO(next-session)"},
    {"file": "scripts/orchestrator/orchestrate.py", "lines": "1129", "reason": "A-5 TODO(next-session)"},

    # A-11/A-12: 스코프 외 진입점
    {"path": "longform/", "reason": "A-11 longform-scripter 2곳 충돌 + 본 스튜디오 shorts 전용"},
    {"file": ".claude/skills/create-video/", "reason": "A-12 롱폼 진입점, 폐기"},

    # A-3: 구 shorts-researcher 경로
    {"file": ".claude/skills/create-shorts/SKILL.md", "reason": "A-3 구 @shorts-researcher 직접 호출 — 재작성 대상"},

    # AF-8: Selenium 업로드
    {"pattern": "selenium", "reason": "AF-8 YouTube ToS 위반"},

    # Phase 2 D-C 지시: 구 orchestrator 전체 (5166줄)
    {"file": "scripts/orchestrator/orchestrate.py", "reason": "D-7 state machine 500~800줄 재작성 — 전량 폐기"},
]
```

## § 4개 raw 디렉토리 매핑 (Phase 3 실행 지침)

| 목적지 | 소스 | 필터 | 판정 근거 |
|--------|------|------|-----------|
| `.preserved/harvested/theme_bible_raw/` | `shorts_naberal/.claude/theme-bible/` (전체) | 무필터 복사 | HARVEST-01 |
| `.preserved/harvested/remotion_src_raw/` | `shorts_naberal/src/` (Remotion composition) | `node_modules/` 제외 | HARVEST-02 |
| `.preserved/harvested/hc_checks_raw/` | `shorts_naberal/scripts/*hc_checks*` 실측 작동 모듈만 | 블랙리스트 참조 | HARVEST-03 |
| `.preserved/harvested/api_wrappers_raw/` | `shorts_naberal/scripts/api/` (Runway/Kling/ElevenLabs/Typecast wrapper) | 블랙리스트 참조 | HARVEST-05 |

## § FAILURES 이관 경로

- **소스:** `shorts_naberal/.claude/failures/**/FAILURES.md` 및 루트 `FAILURES.md`
- **대상:** `studios/shorts/.claude/failures/_imported_from_shorts_naberal.md`
- **규칙:** append-only concat (HARVEST-04). 개별 agent FAILURES는 병합하되 출처 주석 유지

## § B/C급 26건 Phase 3 위임 지침

Phase 3 harvest-importer 에이전트는 다음 원칙으로 B급 16건 + C급 10건 자동 판정:

### 판정 알고리즘
```
for item in conflict_map[B:16] + conflict_map[C:10]:
    if item.path in HARVEST_BLACKLIST: → 폐기
    elif item.domain == "longform": → 폐기 (스코프 외)
    elif item.신형_위치 matches 세션 77 after: → 승계 신형
    elif item is pure cosmetic (.gitignore 누락, worktree 사본 등): → cleanup 커밋
    else: → 통합-재작성 (Phase 4 에이전트 prompt 설계 시 참조)
```

### B급 16건 사전 검토 결과 (Planner 참고)
- **스코프 외 (longform/duo/Japan/dev)**: B-1, B-3, B-5(롱폼 부분), B-6, B-8, B-16 → 폐기
- **이미 해결**: B-10 (Pexels 금지, 코멘트 정리만), B-12 (신형 유지, 하위 문서 동기화만) → 승계
- **규칙 문서화 필요**: B-7 (maxTurns 무분류) → Phase 4 RUB-05 규칙 적용 (maxTurns 3 표준 / 예외 10/5/1)
- **config 정리**: B-2 (pause_comma), B-4 (visual_mode), B-9 (paperclip orchestrate.py 호출), B-13 (길이 상한), B-14 (ins-duplicate/license 역할), B-15 (.tmp_nlm) → Phase 3 실측
- **합계**: 폐기 6 / 승계 2 / Phase 3 판정 8

### C급 10건 사전 검토 결과 (Planner 참고)
- **cleanup 일괄**: C-1, C-2, C-4, C-5 → `.gitignore` 추가 + 경로 정리 커밋
- **스코프 외 (longform/worktree/JP)**: C-6, C-7, C-8 → 폐기
- **config 리팩토링**: C-9, C-10 → Phase 3 실측 (낮은 우선순위)
- **해결 완료**: C-3 → 이관 불필요
- **합계**: cleanup 4 / 폐기 3 / Phase 3 판정 2 / 해결 1

---

## § Harvest 성공 기준 (Phase 3 Success Criteria 연동)

- [ ] `.preserved/harvested/` 하위 4 raw 디렉토리 존재 + diff 0 검증
- [ ] `chmod -w` 실제 발동 (수정 시도 거부 확인)
- [ ] `HARVEST_DECISIONS.md` 생성 (이 파일의 A급 13 판정 + B/C급 26 Phase 3 판정 병합)
- [ ] `_imported_from_shorts_naberal.md` 존재
- [ ] Harvest Blacklist 문서화 (이 파일 § Harvest Blacklist 섹션이 Phase 3 harvest-importer 입력)

---

*Phase 2 산출물 (2026-04-19). Phase 3에서 HARVEST_DECISIONS.md로 승격.*
```

### Schema 설계 근거

| 섹션 | 왜 이 구조 |
|------|-----------|
| A급 13건 판정 테이블 | 5 컬럼 (ID/요약/판정/근거/실행 지시) — Phase 3 harvest-importer가 표 그대로 파싱 가능. 판정 열은 enum (승계/폐기/통합-재작성) |
| Harvest Blacklist (Python 리스트) | Phase 3 harvest-importer가 Python dict로 로드 가능한 형식. regex + 경로 + 이유 3 필드 |
| 4 raw 매핑 테이블 | HARVEST-01~05 REQ와 1:1 매핑. 필터 컬럼으로 node_modules/ 같은 예외 명시 |
| B/C급 위임 지침 | 알고리즘 pseudocode → Phase 3 agent 프롬프트에 그대로 주입 가능. 사전 검토 결과는 힌트 (재작업 방지) |

**Confidence:** HIGH — CONFLICT_MAP.md A급 13건 전수 확인 + D-1~D-10 교차 참조 완료.

---

## § A급 13건 Draft Judgments (Planner Pre-approved)

위 HARVEST_SCOPE.md Schema 섹션에 이미 13건 판정 완료. 요약:

| 판정 | 개수 | ID |
|------|------|-----|
| **승계** | 2 | A-2 (cuts[] 스키마), A-9 (탐정님 호명 금지) |
| **폐기** | 3 | A-5 (TODO 미연결), A-6 (skip_gates), A-11 (longform-scripter) |
| **통합-재작성** | 8 | A-1, A-3, A-4, A-7, A-8, A-10, A-12, A-13 |

### 판정 근거 매트릭스

| A# | D# 연결 | SUMMARY 연결 | 세션 77 확정 | Research 근거 |
|----|---------|--------------|--------------|---------------|
| A-1 | D-8 Harvest | §2 STACK Kling primary | ✓ | SUMMARY §13 D-3 refined |
| A-2 | D-7 state machine | §7 rubric JSON | ✓ (세션 77 실측) | - |
| A-3 | D-4 NLM RAG | §7 researcher→nlm-fetcher | ✓ | CLAUDE.md:105-131 |
| A-4 | D-3 Producer-Reviewer | §7 17 inspector 통합 | - | AF-10 sweet spot |
| A-5 | D-6 3중 방어선 | §8 #1 pitfall | ✓ | AF-14 |
| A-6 | D-6 pre_tool_use | §8 #3 pitfall | ✓ | AF-14 |
| A-7 | - (tempo는 Phase 4 voice-producer) | - | - | DESIGN_BIBLE:179 기준 |
| A-8 | - (ins-structure Phase 4) | - | ✓ | channel_bibles:47 |
| A-9 | - (ins-duo Phase 4) | §9 duo dialogue | ✓ | feedback_assistant_no_detective_honor |
| A-10 | - (config key rename) | - | ✓ | PIPELINE.md:10,98 |
| A-11 | - (shorts 스코프 외) | - | ✓ | §3 longform 배제 |
| A-12 | D-4 진입점 통합 | - | ✓ | subtitle_generate.py 차단 |
| A-13 | D-8 Harvest + D-3 visual | §2 STACK | ✓ | AF-10 연결 |

**Confidence:** HIGH — 13/13 모두 이미 확정된 결정의 문서화 작업. 대표님의 추가 approval 필요 최소 (CONTEXT.md에서 D2-C 확정 완료).

---

## § Tier 2 MOC Planned Nodes — 5 카테고리 × 4-5 placeholder

**→ § MOC.md Template 섹션 참조 (이미 상세 기재됨)**

5 카테고리 placeholder 노드 총 **22개** 드래프트:
- algorithm/ → 4 nodes
- ypp/ → 4 nodes
- render/ → 5 nodes
- kpi/ → 4 nodes
- continuity_bible/ → 5 nodes

Phase 6 작업자는 이 placeholder 리스트를 출발점으로 활용. 최종 노드 세트는 NotebookLM Fallback Chain 실가동 시점에 정제.

---

## § Validation Architecture (Nyquist 적용)

**Trigger:** `.planning/config.json` workflow.nyquist_validation 체크 필요. 기본값 enabled 가정.

Phase 2는 **코드 변경 0줄**의 doc/infra phase. Validation은 **file existence + grep pattern + schema value check + git log**로 구성. Framework 설치 불필요.

### Test Framework

| Property | Value |
|----------|-------|
| Framework | Bash/PowerShell 내장 명령 + `python scripts/structure_check.py` (기존) |
| Config file | N/A (커맨드 기반) |
| Quick run command | `python C:/Users/PC/Desktop/naberal_group/harness/scripts/structure_check.py` |
| Full suite command | 아래 Phase Requirements → Test Map 섹션의 모든 command 순차 실행 |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| **INFRA-02 (Tier 1 exist)** | harness/wiki/ 디렉토리 + README.md 존재 | smoke | `test -d C:/Users/PC/Desktop/naberal_group/harness/wiki && test -f C:/Users/PC/Desktop/naberal_group/harness/wiki/README.md` | ✅ Phase 2 생성 |
| **INFRA-02 (Tier 2 exist)** | studios/shorts/wiki/ + 5 카테고리 + README | smoke | `for d in algorithm ypp render kpi continuity_bible; do test -d "studios/shorts/wiki/$d" && test -f "studios/shorts/wiki/$d/MOC.md"; done && test -f studios/shorts/wiki/README.md` | ✅ Phase 2 생성 |
| **INFRA-02 (Tier 3 exist)** | studios/shorts/.preserved/harvested/ 존재 | smoke | `test -d studios/shorts/.preserved/harvested` | ✅ Phase 2 생성 |
| **Success Criteria #2 (schema bump)** | harness/STRUCTURE.md schema_version: 1.1.0 | unit | `grep -c "schema_version: 1.1.0" C:/Users/PC/Desktop/naberal_group/harness/STRUCTURE.md` (expected: 1) | ✅ |
| **Success Criteria #2 (Whitelist valid)** | structure_check.py 경고 0건 | integration | `cd C:/Users/PC/Desktop/naberal_group/harness && python scripts/structure_check.py; echo $?` (expected: 0) | ✅ |
| **Success Criteria #2 (history)** | STRUCTURE_HISTORY/STRUCTURE_v1.0.0.md.bak 백업 | unit | `test -f C:/Users/PC/Desktop/naberal_group/harness/STRUCTURE_HISTORY/STRUCTURE_v1.0.0.md.bak` | ✅ |
| **Success Criteria #3 (CLAUDE.md TODO 치환)** | studios/shorts/CLAUDE.md 내 TODO 0건 | unit | `grep -c "TODO" studios/shorts/CLAUDE.md` (expected: 0, but check only TODO: patterns not GSD comments) | ⚠️ grep 필터 정밀화 — `grep -E "TODO:|TODO\(next-session\)" studios/shorts/CLAUDE.md` 가 0건이어야 |
| **Success Criteria #3 (line 7 오타)** | `vv1.0` → `v1.0.1` 수정 | unit | `grep -c "vv1.0" studios/shorts/CLAUDE.md` (expected: 0) + `grep -c "v1.0.1" studios/shorts/CLAUDE.md` (expected: ≥1) | ✅ |
| **Success Criteria #3 (domain rules)** | 8 absolute rules present | unit | `grep -c "skip_gates=True 금지" studios/shorts/CLAUDE.md` (expected: 1) + 동일 패턴 7개 더 | ✅ |
| **Success Criteria #4 (HARVEST_SCOPE)** | 파일 존재 + A급 13건 모두 언급 | unit | `test -f studios/shorts/.planning/phases/02-domain-definition/02-HARVEST_SCOPE.md && for i in 1 2 3 4 5 6 7 8 9 10 11 12 13; do grep -c "A-$i" studios/shorts/.planning/phases/02-domain-definition/02-HARVEST_SCOPE.md; done` (each: ≥1) | ✅ |
| **커밋 증빙 (harness)** | harness 레포 v1.1.0 커밋 존재 | smoke | `cd C:/Users/PC/Desktop/naberal_group/harness && git log --oneline -1 STRUCTURE.md \| grep "v1.1.0"` (expected: 1 match) | ✅ |
| **커밋 증빙 (studio)** | studio 레포 Phase 2 커밋 존재 | smoke | `cd studios/shorts && git log --oneline -5 \| grep -Ei "phase 2\|INFRA-02\|domain definition"` (expected: ≥1 match) | ✅ |

### Sampling Rate

- **Per task commit** (웨이브 단위): 해당 웨이브의 smoke 테스트만 (예: W1 완료 시 schema_version grep + structure_check.py)
- **Per wave merge**: 누적된 모든 smoke + unit (수초 내 완료, < 10s)
- **Phase gate** (`/gsd:verify-work 2`): 전체 12개 테스트 실행. 모두 PASS 시에만 Phase 3 진입 허용

### Wave 0 Gaps

**None — Phase 2는 인프라 검증이므로 테스트 파일 신규 생성 불필요.**

기존 `structure_check.py` + Bash/PowerShell 내장 명령으로 충분. Phase 2 산출물 자체가 검증 대상 파일들이므로, 별도 test fixture 불필요.

단, 다음 **선택적** 헬퍼 추가 가능 (Planner 판단):
- `studios/shorts/scripts/verify_phase2.sh` — 12개 테스트를 한 줄 명령으로 wrap (선택, 필수 아님). Phase 3 이후에도 회귀 감지에 사용 가능.

**Confidence:** HIGH — Nyquist sampling 원칙을 doc phase에 적용한 표준 패턴.

---

## § Project Constraints (from CLAUDE.md)

**Source:** `C:\Users\PC\Desktop\naberal_group\studios\shorts\CLAUDE.md` (studio 레포 루트)

### Hard Constraints (불변, STATE.md 재확인 + CLAUDE.md constraints 섹션)

1. **Whitelist 준수** — STRUCTURE.md 외 폴더 생성 금지 → Phase 2는 wiki/ 등재 후에만 폴더 생성
2. **SKILL.md ≤ 500줄** — Phase 2는 SKILL 수정 없음 (해당 없음)
3. **Hook 3종 필수 설치** — Phase 1에서 완료, Phase 2는 Hook 활용만
4. **에이전트 12~20명** — Phase 2 해당 없음 (Phase 4)
5. **오케스트레이터 500~800줄** — Phase 2 해당 없음 (Phase 5)
6. **`skip_gates=True` 금지 / `TODO(next-session)` 금지 / try-except 침묵 금지** — Phase 2 작업 중 문서에 이 패턴 포함 금지 (CLAUDE.md 치환 문장 안전 설계 필요)
7. **shorts_naberal 원본 수정 금지** — Harvest는 Phase 3. Phase 2는 CONFLICT_MAP.md 참조만 (읽기 전용)
8. **GSD 정식 워크플로우** — phase별 commit 필수. Phase 2 산출물 6개(STRUCTURE.md, backup, README×2, MOC×5, CLAUDE.md, HARVEST_SCOPE.md)는 2개 레포에 분산 커밋

### Session Protocol (세션마다 재확인)

세션 시작 시 진입점 문서 읽기 순서 (CLAUDE.md Session Init 섹션):
1. `CLAUDE.md` (이 파일)
2. `WORK_HANDOFF.md`
3. `docs/DESIGN_BIBLE.md` (없을 수 있음)
4. `../../harness/docs/ARCHITECTURE.md` (처음 세션만)

Phase 2 planner는 추가로:
5. `.planning/STATE.md`
6. `.planning/phases/02-domain-definition/02-CONTEXT.md`
7. 본 파일 `.planning/phases/02-domain-definition/02-RESEARCH.md`

---

## § Environment Availability

**Phase 2는 code/config 변경 없음 → 외부 dependency 없음.**

단, 아래 도구들은 Phase 2 실행에 필수:

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| `python` | `structure_check.py` 실행 | ✓ (가정) | 3.8+ | 없음 (필수) |
| `git` | 커밋 2개 레포 | ✓ (가정) | any | 없음 (필수) |
| `bash` 또는 `PowerShell` | 파일 생성, grep 검증 | ✓ | any | 상호 대체 |
| `grep` | 검증 command | ✓ (bash 기본) | any | PowerShell `Select-String` |

**Missing dependencies with no fallback:** 없음.
**Missing dependencies with fallback:** 없음.

Phase 2는 **runtime dependency zero** — 순수 파일 조작. OPEN QUESTION: Windows 환경에서 `chmod -w`는 `attrib +R`로 대체되나, Phase 2에서는 Tier 3 immutable lock이 **Phase 3에서 수행**되므로 Phase 2 스코프 밖 (RESEARCH 완료 시점에서 다루지 않음).

---

## § Runtime State Inventory

**Trigger 판단:** Phase 2는 **신규 도메인 scaffolding 확장**. Rename/refactor/migration 아님. 그러나 "기존 studio 레포에 wiki/ 폴더 추가" + "CLAUDE.md placeholder 치환" 작업은 일부 runtime state 관점 질문을 수반 → 포함.

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| **Stored data** | None — Phase 2는 데이터스토어 미사용. NotebookLM/ChromaDB/Mem0 연동은 Phase 6. | 없음 |
| **Live service config** | None — YouTube Data API / Kling / Typecast 등 외부 서비스 설정은 Phase 8 Publishing. Phase 2 무관. | 없음 |
| **OS-registered state** | None — Windows Task Scheduler / pm2 / systemd 미등록. Phase 10 Sustained Operations의 cron은 해당 시점에 등록. | 없음 |
| **Secrets/env vars** | None — Phase 2는 API key 사용 없음. `.env` 변경 없음. | 없음 |
| **Build artifacts / installed packages** | None — Phase 2는 npm/pip install 없음. `package.json` / `requirements.txt` 변경 없음. | 없음 |

**전 카테고리 "없음" 확인** — Phase 2는 순수 파일 구조/문서 작업으로, runtime state 측면에서 재등록/migration 불필요.

---

## § Open Questions (Planner 주의)

### OQ-1: studio 레포 Whitelist 상태

**질문:** `studios/shorts/` 레포에 자체 `STRUCTURE.md` 또는 `.claude/allowed_paths.json` 이 있는가? Phase 1 `new_domain.py`가 studio용 Whitelist를 생성했는가?

**Why matters:** 있다면 W2b/W2c(Tier 2/3 폴더 생성) 시 studio-level Hook이 `wiki/`나 `.preserved/`를 차단할 수 있음 → studio-level schema bump 추가 task 필요.

**How to resolve:**
```bash
ls studios/shorts/STRUCTURE.md 2>/dev/null
ls studios/shorts/.claude/allowed_paths.json 2>/dev/null
cat studios/shorts/.claude/settings.json
```

**Recommendation:** Planner가 Phase 2 Plan 작성 전 30초 투자하여 확인. 있으면 해당 파일도 Phase 2 수정 대상. 없으면 W2b/W2c 간섭 없이 진행.

**Confidence impact:** 현재 HIGH (harness side) / MEDIUM (studio side) → 확인 후 HIGH 수렴 가능.

---

### OQ-2: `.planning/config.json` Nyquist 설정

**질문:** `workflow.nyquist_validation` 플래그가 true인가 false인가 absent인가?

**Why matters:** Validation Architecture 섹션 포함/제외 결정. Default는 included.

**How to resolve:**
```bash
cat studios/shorts/.planning/config.json | grep -A1 nyquist
```

**Current assumption:** true (default). Validation Architecture 섹션 포함 완료.

---

### OQ-3: CLAUDE.md GSD 블록 안전 경계

**질문:** `<!-- GSD:project-start -->` 부터 `<!-- GSD:profile-end -->` 사이 블록(line 109~409)을 전혀 건드리지 않아야 하는가?

**Why matters:** 이 블록은 GSD 메타 명령이 자동 관리. Phase 2가 CLAUDE.md 수정 시 이 블록 외 영역만 수정.

**Current assumption:** YES — 치환 대상 5개 TODO는 모두 line 3~68 사이 (GSD 블록 이전). 안전.

**검증:**
- Replacement #1 (line 3): 안전 — 파일 최상단
- Replacement #2 (line 38-42): 안전 — Pipeline 섹션, GSD 블록 이전
- Replacement #3 (line 44-45): 안전 — 도메인 절대 규칙, GSD 블록 이전
- Replacement #4 (line 64-66): 안전 — hive 섹션, GSD 블록 이전 (line 107 "🧩 이 파일은 naberal_harness/templates/CLAUDE.md.template..." 바로 직전)
- Replacement #5 (line 68): 안전 — 동일 구역

**Confidence:** HIGH — 모든 치환이 line 3~68 범위, GSD 블록(line 109+) 무관.

---

### OQ-4: HARVEST_SCOPE.md 파일명 컨벤션

**질문:** `02-HARVEST_SCOPE.md`인가 `HARVEST_SCOPE.md`인가?

**Why matters:** phase 문서 네이밍 컨벤션 일치. 02-CONTEXT.md, 02-RESEARCH.md (본 파일), 02-PLAN.md 패턴.

**Current assumption:** `02-HARVEST_SCOPE.md` (phase prefix 유지) — 기존 파일(`02-CONTEXT.md`, `02-DISCUSSION-LOG.md`) 패턴 준수.

**Alt:** `HARVEST_SCOPE.md` 승격 (phase 독립 문서) — ROADMAP SC#4가 위치 미지정이므로 Phase 3 출력 `HARVEST_DECISIONS.md`와 병렬 위치(`.planning/HARVEST_SCOPE.md`) 도 가능.

**Recommendation:** Planner 재량. 두 옵션 모두 유효.

---

## § Sources

### Primary (HIGH confidence) — 직접 검증

- `C:\Users\PC\Desktop\naberal_group\studios\shorts\.planning\phases\02-domain-definition\02-CONTEXT.md` — Phase 2 user decisions (D2-A~D)
- `C:\Users\PC\Desktop\naberal_group\studios\shorts\.planning\REQUIREMENTS.md` — INFRA-02 정의 + Phase Traceability
- `C:\Users\PC\Desktop\naberal_group\studios\shorts\.planning\STATE.md` — D-1~D-10 확정 상태
- `C:\Users\PC\Desktop\naberal_group\studios\shorts\.planning\ROADMAP.md` — Phase 2 Success Criteria 4건
- `C:\Users\PC\Desktop\naberal_group\studios\shorts\.planning\research\SUMMARY.md` — 17 Novel Techniques + Build Order + D-1~D-10 refinement
- `C:\Users\PC\Desktop\naberal_group\studios\shorts\CLAUDE.md` — 409 line 전수 확인, TODO 5개 정확 위치
- `C:\Users\PC\Desktop\naberal_group\harness\STRUCTURE.md` — amendment_policy 7-step, Whitelist 구조, 변경 이력 테이블
- `C:\Users\PC\Desktop\naberal_group\harness\docs\DOMAIN_CHECKLIST.md` — Phase 2 체크리스트 원본
- `C:\Users\PC\Desktop\naberal_group\harness\hooks\pre_tool_use.py` (line 1-80 실측) — Whitelist 검사 메커니즘
- `C:\Users\PC\Desktop\naberal_group\harness\scripts\structure_check.py` (line 1-60 실측) — Whitelist 파싱 로직
- `C:\Users\PC\Desktop\shorts_naberal\.planning\codebase\CONFLICT_MAP.md` — A급 13건 + B급 16건 + C급 10건 전수

### Secondary (MEDIUM confidence) — 패턴 참조

- `C:\Users\PC\Desktop\secondjob_naberal\wiki\README.md` — Tier 2 wiki README 패턴
- `C:\Users\PC\Desktop\secondjob_naberal\wiki\MOC.md` — MOC 구조 (섹션 헤더 스타일)

### Tertiary — 없음

WebSearch/Context7 미사용 — Phase 2는 프로젝트 내부 문서 기반 충분.

---

## § Metadata

**Confidence breakdown:**

| Area | Level | Reason |
|------|-------|--------|
| Schema Bump Procedure | HIGH | STRUCTURE.md 본문 line 93-111 직접 근거 + structure_check.py 실측 |
| 3-Tier Creation Order | HIGH (harness) / MEDIUM (studio side) | OQ-1 해소 시 HIGH 수렴 |
| MOC.md Template | HIGH | secondjob_naberal 실측 패턴 + Obsidian 표준 |
| CLAUDE.md TODO Replacement | HIGH | 409-line 전수 실측, line-exact 확인 |
| HARVEST_SCOPE.md Schema | HIGH | CONFLICT_MAP 39건 + D-1~D-10 + SUMMARY §13 교차 참조 |
| A급 13건 판정 | HIGH | 10/13은 세션 77 확정본 / 3/13은 스코프 외(longform/JP) |
| Validation Architecture | HIGH | Nyquist sampling 표준 적용 |

**Research date:** 2026-04-19
**Valid until:** 2026-05-19 (30 days — stable research, doc/infra phase, 외부 의존성 없음)
**Supersedes:** 없음 (Phase 2 최초 research)

---

## § Ready for Planning

Phase 2 research 완료. Planner(gsd-planner)는 다음 순서로 02-PLAN.md 작성 가능:

1. **Wave 구조 결정** — W1(schema bump) → W2(3-Tier 생성) → W3(CLAUDE.md + HARVEST_SCOPE) → W4(검증). 각 웨이브 ≤ 3 task.
2. **Task 당 deliverable 명세** — 본 research의 line-exact 치환 + 템플릿 텍스트 그대로 활용 가능 (재작업 불필요)
3. **OPEN QUESTION OQ-1 해소** — Plan 작성 전 `ls studios/shorts/STRUCTURE.md` 1줄 확인 권장
4. **검증 command 12개** — § Validation Architecture 섹션 그대로 Plan의 Verification 섹션에 복붙 가능
5. **Harvest Blacklist Python dict** — HARVEST_SCOPE.md Schema 섹션의 블록을 Phase 3 task의 입력으로 그대로 채택 가능

**Estimated planning effort:** Light — 4 waves × ~3 tasks = 12 atomic tasks. 각 task는 본 research의 텍스트 블록을 실행으로 번역만 하면 됨.

*Phase 2 Research complete. Next: `/gsd:plan-phase 2` (spawns gsd-planner → 02-PLAN.md).*
