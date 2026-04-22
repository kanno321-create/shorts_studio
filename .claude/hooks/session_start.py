#!/usr/bin/env python3
"""
session_start.py — 공용 SessionStart Hook (Layer 1 naberal_harness)

목적: 세션 시작 시 스튜디오 **자동 감사** 실행.
     - SKILL.md 500줄 초과 경고 (Progressive Disclosure 위반)
     - deprecated 패턴 잔존 검사
     - CONFLICT_MAP.md 존재 여부 + 미해결 A급 카운트
     - 결과를 세션 시작 메시지에 컨텍스트로 주입

각 스튜디오가 자기 `.claude/hooks/`에 복사해 사용.
"""
from __future__ import annotations
import json
import sys
import re
from pathlib import Path


def find_studio_root(start: Path) -> Path | None:
    cur = start.resolve()
    for _ in range(10):
        if (cur / ".claude").is_dir():
            return cur
        if cur.parent == cur:
            return None
        cur = cur.parent
    return None


def count_long_skills(studio_root: Path, threshold: int = 500) -> list[tuple[str, int]]:
    """SKILL.md 중 threshold 줄 초과 파일 목록."""
    skills_dir = studio_root / ".claude" / "skills"
    if not skills_dir.exists():
        return []
    long_files = []
    for skill_md in skills_dir.rglob("SKILL.md"):
        try:
            line_count = sum(1 for _ in skill_md.open("r", encoding="utf-8", errors="ignore"))
            if line_count > threshold:
                rel = skill_md.relative_to(studio_root)
                long_files.append((str(rel), line_count))
        except Exception:
            pass
    return long_files


def check_conflict_map(studio_root: Path) -> dict:
    """CONFLICT_MAP.md 존재 여부 + A급 미해결 카운트."""
    cm = studio_root / ".planning" / "codebase" / "CONFLICT_MAP.md"
    if not cm.exists():
        return {"exists": False, "a_grade_open": 0}

    try:
        content = cm.read_text(encoding="utf-8", errors="ignore")
        # 간단 휴리스틱: "A-\d+" 패턴 카운트 (A급 충돌 번호)
        a_matches = re.findall(r"A-\d+", content)
        # 🚫 또는 "정답 확정:" 뒤가 비어있으면 미해결로 간주 (단순화)
        return {
            "exists": True,
            "a_grade_total": len(set(a_matches)),
            # 실제 "미해결" 판정은 복잡 — 여기선 총계만
        }
    except Exception:
        return {"exists": True, "a_grade_total": -1}


def summarize_work_handoff(studio_root: Path, max_lines: int = 30) -> str | None:
    """WORK_HANDOFF.md 첫 N줄 요약 (현재 세션 상태 + 박제된 결정사항).

    F-CTX-01 재발 방지 — 세션 시작 시 이전 세션 핸드오프를 자동 주입.
    """
    wh = studio_root / "WORK_HANDOFF.md"
    if not wh.exists():
        return None
    try:
        lines = wh.read_text(encoding="utf-8", errors="ignore").splitlines()[:max_lines]
        return "\n".join(lines)
    except Exception:
        return None


def list_env_keys(studio_root: Path) -> list[str]:
    """`.env` 에 저장된 key 이름 목록 (값은 마스킹, 이름만 노출).

    F-CTX-01 재발 방지: API key 재질문 절대 금지 근거 자료.
    """
    env = studio_root / ".env"
    if not env.exists():
        return []
    try:
        keys = []
        for line in env.read_text(encoding="utf-8", errors="ignore").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue
            key_name = line.split("=", 1)[0].strip()
            if key_name:
                keys.append(key_name)
        return keys
    except Exception:
        return []


def load_memory_index(studio_root: Path) -> str | None:
    """`.claude/memory/MEMORY.md` 인덱스 전체 로드.

    auto memory 규약: MEMORY.md 는 200줄 이내 index 전용.
    """
    idx = studio_root / ".claude" / "memory" / "MEMORY.md"
    if not idx.exists():
        return None
    try:
        return idx.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return None


def load_recent_failures(studio_root: Path, max_entries: int = 5) -> str | None:
    """`.claude/failures/FAILURES.md` 최근 N 개 entry + 전체 open 상태 entry 주입.

    대표님 원칙 (2026-04-22): "실패하면 실패리스트에 올려서 교훈까지 제공하고
    그걸 참조한뒤 작업시작" — 세션 시작 시 최근 실패 사례와 교훈을 자동 주입하여
    같은 실수 반복 차단.

    전략:
    - 전체 읽어서 `### F...` 헤더 기준 entry split
    - 최근 max_entries 개 + 상태 "open" 인 entry 전수 주입
    - 각 entry 의 "무엇/왜/정답/상태/Lessons" 핵심 요약 보존
    """
    fail_file = studio_root / ".claude" / "failures" / "FAILURES.md"
    if not fail_file.exists():
        return None
    try:
        content = fail_file.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return None

    # entry 경계: `### FAIL-` 또는 `### F-` 헤더 기준 분리
    entry_pattern = re.compile(r"^### (F[A-Z-]+-?[A-Z0-9-]+|FAIL-[A-Z0-9-]+).*$", re.MULTILINE)
    matches = list(entry_pattern.finditer(content))
    if not matches:
        return None

    entries = []
    for i, m in enumerate(matches):
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(content)
        block = content[start:end].strip()
        # 상태 필드 추출
        state_match = re.search(r"\*\*상태\*\*:\s*(\w+)", block)
        state = state_match.group(1) if state_match else "unknown"
        # 헤더 한 줄 추출
        header_line = block.split("\n", 1)[0]
        entries.append({"header": header_line, "body": block, "state": state})

    # 선택 규칙: open 상태 전부 + 최근 max_entries (중복 제거, 최신 순)
    open_entries = [e for e in entries if e["state"].lower() == "open"]
    recent_entries = entries[-max_entries:] if len(entries) >= max_entries else entries
    # 중복 제거 (header 기준)
    seen_headers = set()
    merged = []
    for e in open_entries + list(reversed(recent_entries)):
        if e["header"] not in seen_headers:
            seen_headers.add(e["header"])
            merged.append(e)

    if not merged:
        return None

    lines = []
    lines.append(f"**총 {len(entries)} 실패 등재. 아래는 open {len(open_entries)}건 + 최근 {min(max_entries, len(entries))}건 (중복 제거 {len(merged)}건):**")
    lines.append("")
    for e in merged:
        # 각 entry 의 body 는 길이 제한 (1500자) + 상태 필드는 항상 보존
        body = e["body"]
        if len(body) > 1500:
            # 상태 필드 라인을 찾아 preserve
            state_line_match = re.search(r"(\*\*상태\*\*:.*?)$", body, re.MULTILINE)
            state_line = state_line_match.group(1) if state_line_match else ""
            body = body[:1500] + "\n... (truncated — 전체는 FAILURES.md 참조)"
            if state_line and state_line not in body:
                body += f"\n{state_line}"
        lines.append(body)
        lines.append("")
    return "\n".join(lines)


def check_navigator_coverage(studio_root: Path) -> dict:
    """Navigator coverage 검증 — scripts/validate/navigator_coverage.py 호출.

    CLAUDE.md Navigator 매트릭스가 .claude/agents/ + .claude/skills/ 전수를
    커버하는지 확인. 누락 자산이 있으면 warning (block 아님, 파이프라인 중단 금지).
    """
    script = studio_root / "scripts" / "validate" / "navigator_coverage.py"
    if not script.exists():
        return {"available": False}
    try:
        import subprocess
        result = subprocess.run(
            [sys.executable, str(script), "--warn-only"],
            cwd=str(studio_root),
            capture_output=True,
            text=True,
            timeout=15,
            encoding="utf-8",
            errors="ignore",
        )
        return {
            "available": True,
            "stdout": (result.stdout or "").strip(),
            "stderr": (result.stderr or "").strip(),
            "returncode": result.returncode,
        }
    except Exception as e:
        return {"available": True, "error": str(e)}


def scan_deprecated_patterns(studio_root: Path) -> list[str]:
    """deprecated_patterns.json에 정의된 패턴이 스튜디오 내 어느 파일에 잔존하는지."""
    config = studio_root / ".claude" / "deprecated_patterns.json"
    if not config.exists():
        return []
    try:
        data = json.loads(config.read_text(encoding="utf-8"))
        patterns = data.get("patterns", [])
    except Exception:
        return []

    found = []
    # .claude, scripts, config, longform, src 스캔 (비용 고려)
    scan_dirs = [
        studio_root / ".claude",
        studio_root / "scripts",
        studio_root / "config",
    ]
    for p in patterns:
        regex = p.get("regex", "")
        reason = p.get("reason", "")
        if not regex:
            continue
        try:
            rx = re.compile(regex, re.MULTILINE)
        except re.error:
            continue
        for scan_dir in scan_dirs:
            if not scan_dir.exists():
                continue
            for f in scan_dir.rglob("*"):
                if not f.is_file():
                    continue
                if f.suffix in (".pyc", ".jsonl", ".log"):
                    continue
                try:
                    txt = f.read_text(encoding="utf-8", errors="ignore")
                    if rx.search(txt):
                        rel = f.relative_to(studio_root)
                        found.append(f"{rel}: {reason}")
                        break  # 한 파일당 한 번만 보고
                except Exception:
                    pass
    return found


def main() -> int:
    try:
        _ = sys.stdin.read()  # SessionStart는 보통 input 없음
    except Exception:
        pass

    studio_root = find_studio_root(Path.cwd())
    if studio_root is None:
        # 스튜디오 밖 세션 — 감사 없이 통과
        print(json.dumps({"context": ""}))
        return 0

    lines = []
    lines.append(f"### 🧰 naberal_harness 세션 감사 — {studio_root.name}")
    lines.append("")

    # 1. CONFLICT_MAP 체크
    cm = check_conflict_map(studio_root)
    if cm["exists"]:
        total = cm.get("a_grade_total", 0)
        if total > 0:
            lines.append(f"⚠️ CONFLICT_MAP.md에 A급 충돌 {total}건 기록됨. 진행 전 확인.")
        else:
            lines.append("✅ CONFLICT_MAP.md 존재, A급 충돌 없음.")
    else:
        lines.append("ℹ️ CONFLICT_MAP.md 없음 (신규 스튜디오 정상).")

    # 2. SKILL.md 500줄 리밋
    long_skills = count_long_skills(studio_root, threshold=500)
    if long_skills:
        lines.append(f"⚠️ SKILL.md 500줄 초과 {len(long_skills)}건 (Lost-in-the-Middle 위험):")
        for path, n in long_skills[:5]:
            lines.append(f"   - {path}: {n}줄")
        if len(long_skills) > 5:
            lines.append(f"   ... 외 {len(long_skills) - 5}개")
        lines.append("   → references/ 분리 권장.")
    else:
        lines.append("✅ 모든 SKILL.md 500줄 이내.")

    # 3. Deprecated 패턴 스캔
    found = scan_deprecated_patterns(studio_root)
    if found:
        lines.append(f"🔴 Deprecated 패턴 잔존 {len(found)}곳:")
        for item in found[:5]:
            lines.append(f"   - {item}")
        if len(found) > 5:
            lines.append(f"   ... 외 {len(found) - 5}건")
    else:
        lines.append("✅ Deprecated 패턴 잔존 없음.")

    # 4. WORK_HANDOFF.md 첫 30줄 요약 (F-CTX-01 재발 방지)
    lines.append("")
    lines.append("### 📋 이전 세션 핸드오프 (WORK_HANDOFF.md 첫 30줄)")
    handoff_summary = summarize_work_handoff(studio_root, max_lines=30)
    if handoff_summary:
        lines.append("```")
        lines.append(handoff_summary)
        lines.append("```")
    else:
        lines.append("ℹ️ WORK_HANDOFF.md 없음 (신규 스튜디오 정상).")

    # 5. .env API key 이름 목록 (값 마스킹, F-CTX-01 재발 방지)
    lines.append("")
    lines.append("### 🔑 API Keys available in .env (값은 환경변수로만 접근, 재질문 금지)")
    env_keys = list_env_keys(studio_root)
    if env_keys:
        lines.append(f"**대표님께 API key 를 다시 묻지 말 것.** 다음 {len(env_keys)}개 key 가 이미 저장돼 있다:")
        for k in env_keys:
            lines.append(f"- `{k}`")
        lines.append("")
        lines.append("참조: `.claude/memory/reference_api_keys_location.md` (용도 매핑)")
    else:
        lines.append("⚠️ .env 파일 없음 또는 비어있음 — `.env.example` 을 복사해 값 채우기 필요.")

    # 6. 로컬 메모리 인덱스 전체 주입 (auto memory 규약)
    lines.append("")
    lines.append("### 🧠 Local Memory Index (.claude/memory/MEMORY.md)")
    memory_idx = load_memory_index(studio_root)
    if memory_idx:
        lines.append(memory_idx)
    else:
        lines.append("ℹ️ `.claude/memory/MEMORY.md` 없음 — 메모리 시스템 미초기화 (신규 스튜디오).")

    # 6a. 최근 실패 사례 + 교훈 자동 주입 (대표님 원칙 2026-04-22)
    # "실패하면 실패리스트에 올려서 교훈까지 제공하고 그걸 참조한뒤 작업시작"
    # → open 상태 entry 전부 + 최근 5건을 세션 시작 시 자동 노출하여 재발 차단
    lines.append("")
    lines.append("### 📛 최근 실패 사례 + 교훈 (.claude/failures/FAILURES.md)")
    lines.append("**작업 시작 전 반드시 확인 — 같은 실패 반복 금지.**")
    lines.append("")
    recent_fails = load_recent_failures(studio_root, max_entries=5)
    if recent_fails:
        lines.append(recent_fails)
    else:
        lines.append("ℹ️ `.claude/failures/FAILURES.md` 없음 또는 entry 미등재 (신규 스튜디오).")

    # 6b. Navigator coverage check — 구현된 자산이 CLAUDE.md 에 등록됐는지 확인
    # (warning only, 파이프라인 차단 금지 — 하네스 Hook 원칙 "Fail Loud, Not Silent" 의
    #  균형: 검증은 strict 하지만 Hook 자체는 파이프라인 중단 금지)
    lines.append("")
    lines.append("### 🗺️ Navigator Coverage (CLAUDE.md 네비게이터 ↔ 구현 자산 동기화)")
    nav = check_navigator_coverage(studio_root)
    if not nav.get("available"):
        lines.append("ℹ️ `scripts/validate/navigator_coverage.py` 미설치 — Navigator 검증 건너뜀.")
    elif nav.get("error"):
        lines.append(f"⚠️ Navigator 검증 실행 실패: {nav['error']}")
    else:
        stdout = nav.get("stdout") or ""
        stderr = nav.get("stderr") or ""
        if nav.get("returncode") == 0 and "OK" in stdout:
            # 마지막 'total: N/M covered' 줄만 표시
            summary = next(
                (line for line in stdout.splitlines() if "total:" in line),
                "✅ Navigator 전수 커버",
            )
            lines.append(f"✅ {summary.replace('[navigator-coverage] ', '')}")
        else:
            lines.append("⚠️ Navigator 커버리지 누락 자산 존재 (CLAUDE.md 매트릭스에 등록 필요):")
            for line in (stdout + "\n" + stderr).splitlines():
                if line.strip() and not line.startswith("[navigator-coverage]"):
                    lines.append(f"   {line}")

    context_text = "\n".join(lines)

    # Claude Code SessionStart hook은 context를 반환하여 시스템 메시지로 주입
    print(json.dumps({"context": context_text}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
