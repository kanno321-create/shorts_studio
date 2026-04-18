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

    context_text = "\n".join(lines)

    # Claude Code SessionStart hook은 context를 반환하여 시스템 메시지로 주입
    print(json.dumps({"context": context_text}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
