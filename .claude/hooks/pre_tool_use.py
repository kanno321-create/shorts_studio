#!/usr/bin/env python3
"""
pre_tool_use.py — 공용 PreToolUse Hook (Layer 1 naberal_harness)

목적: Write/Edit 도구 호출 직전에 **deprecated 패턴 검출** → 차단 or 경고.
각 스튜디오가 이 Hook을 자신의 `.claude/hooks/`에 복사해 사용.

Claude Code PreToolUse hook spec:
- stdin으로 JSON input 받음: {"tool_name": "...", "input": {...}}
- stdout으로 JSON response: {"decision": "allow"|"deny", "reason": "..."}
- exit 0 = 결정 반영, exit != 0 = 에러
"""
from __future__ import annotations
import json
import shutil
import sys
import re
from datetime import datetime
from pathlib import Path

# ============================================================================
# 스튜디오별 금지 패턴 로드
# ============================================================================
#
# 각 스튜디오는 `.claude/deprecated_patterns.json` 파일로 자신의 금지 패턴을 정의.
# 예시 (shorts_studio/.claude/deprecated_patterns.json):
# {
#   "patterns": [
#     {"regex": "skip_gates\\s*=\\s*True", "reason": "CONFLICT_MAP A-6: skip_gates deprecated"},
#     {"regex": "subtitle_generate\\.py --pipeline shorts", "reason": "CONFLICT_MAP A-7: 구형 경로"}
#   ]
# }


def load_patterns(studio_root: Path) -> list[dict]:
    """스튜디오의 deprecated 패턴 로드. 없으면 빈 리스트."""
    config = studio_root / ".claude" / "deprecated_patterns.json"
    if not config.exists():
        return []
    try:
        data = json.loads(config.read_text(encoding="utf-8"))
        return data.get("patterns", [])
    except Exception as e:
        # 설정 파일 오류는 경고만, Hook 자체 실패로 이어지지 않게
        sys.stderr.write(f"[pre_tool_use] pattern config error: {e}\n")
        return []


def find_studio_root(start: Path) -> Path | None:
    """현재 위치에서 위로 올라가며 `.claude/` 디렉토리 찾음."""
    cur = start.resolve()
    for _ in range(10):  # 최대 10단계 상위
        if (cur / ".claude").is_dir():
            return cur
        if cur.parent == cur:
            return None
        cur = cur.parent
    return None


# ============================================================================
# Hook 본체
# ============================================================================

def check_content(content: str, patterns: list[dict]) -> list[str]:
    """content 내에서 deprecated 패턴 감지. 매칭된 reason 목록 반환."""
    violations = []
    for p in patterns:
        regex = p.get("regex", "")
        reason = p.get("reason", "deprecated pattern")
        if not regex:
            continue
        try:
            if re.search(regex, content, re.MULTILINE):
                violations.append(reason)
        except re.error as e:
            sys.stderr.write(f"[pre_tool_use] invalid regex '{regex}': {e}\n")
    return violations


def check_structure_allowed(file_path: Path, studio_root: Path) -> tuple[bool, str]:
    """
    파일 생성 경로가 STRUCTURE.md Whitelist에 허용된 폴더인지 검사.

    Returns:
        (허용 여부, 차단 시 이유)
    """
    structure_md = studio_root / "STRUCTURE.md"
    if not structure_md.exists():
        # STRUCTURE.md 없으면 검사 안 함 (하위 호환)
        return True, ""

    try:
        rel = file_path.resolve().relative_to(studio_root.resolve())
    except ValueError:
        # 스튜디오 밖 경로
        return True, ""

    # 최상위 1레벨 폴더만 검사 (깊은 경로는 *OPTIONAL 허용)
    parts = rel.parts
    if len(parts) == 0:
        return True, ""

    top = parts[0]
    # 파일이면 파일명, 폴더면 폴더/
    if len(parts) == 1:
        # 루트 바로 아래 파일
        top_key = top
    else:
        top_key = top + "/"

    # STRUCTURE.md에서 허용 최상위 추출
    try:
        content = structure_md.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return True, ""

    allowed_top = set()
    in_code = False
    for line in content.splitlines():
        if line.strip().startswith("```"):
            in_code = not in_code
            continue
        if not in_code:
            continue
        cleaned = re.sub(r'^[│├└─\s]+', '', line)
        cleaned = re.sub(r'\s*\[.*?\].*$', '', cleaned)
        cleaned = re.sub(r'\s*#.*$', '', cleaned)
        cleaned = cleaned.strip()
        if not cleaned or "/" in cleaned[:-1]:  # 최상위 1레벨만
            continue
        allowed_top.add(cleaned)

    if not allowed_top:
        # 파서 실패 — 안전하게 허용
        return True, ""

    if top_key in allowed_top:
        return True, ""

    # 허용 안 됨
    reason = (
        f"❌ STRUCTURE.md Whitelist 위반:\n"
        f"   - 시도한 경로: {rel}\n"
        f"   - 최상위 '{top_key}'가 STRUCTURE.md에 등록되지 않음.\n"
        f"\n"
        f"해결:\n"
        f"   1) 기존 허용 폴더로 경로 변경, 또는\n"
        f"   2) STRUCTURE.md 수정 절차 따라 새 폴더 등록 후 재시도\n"
        f"      (백업: STRUCTURE_HISTORY/STRUCTURE_v<n>.md.bak)\n"
    )
    return False, reason


# ============================================================================
# Phase 6 Plan 08: FAILURES 저수지 규율 (D-11, D-12, D-14)
# ============================================================================


def check_failures_append_only(tool_name: str, tool_input: dict) -> str | None:
    """D-11 append-only + D-A3-01 500줄 cap + D-A3-04 env whitelist (Phase 12 FAIL-PROTO-01).

    Applies only to files whose basename is exactly 'FAILURES.md'. EXPLICITLY
    excludes '_imported_from_shorts_naberal.md' (Phase 3 D-14 immutable, sha256-locked,
    handled by separate immutability check — basename mismatch filters it here).

    Returns:
        Deny reason string if the operation would:
          (a) modify existing FAILURES.md content (D-11 append-only), OR
          (b) push line count over 500 (D-A3-01 rotation cap).
        None if the operation is allowed.

    Contract:
        - FAILURES_ROTATE_CTX=1 env var -> return None (D-A3-04 whitelist for rotation CLI)
        - Edit with non-empty old_string -> deny (modifies existing line)
        - Write with new content that does NOT preserve existing content as
          strict prefix -> deny (not an append)
        - Write when file does not yet exist -> allow (first-time create)
        - MultiEdit with any non-empty old_string -> deny
        - Write/Edit that would produce > 500 lines -> deny with rotation guidance
        - Any tool on files whose basename is not exactly 'FAILURES.md' -> allow
          (HARD-EXCLUDE: '_imported_from_shorts_naberal.md' passes through here)
    """
    # --- D-A3-04 env whitelist (Phase 12 FAIL-PROTO-01) ---
    # rotation script sets FAILURES_ROTATE_CTX=1 before its direct file I/O;
    # all other callers fall through to normal checks.
    import os as _os
    if _os.environ.get("FAILURES_ROTATE_CTX") == "1":
        return None
    # ---------------------------------------------------------

    fp = tool_input.get("file_path", "")
    if not fp:
        return None
    # Path separator agnostic: only match literal filename 'FAILURES.md' at end
    name = fp.replace("\\", "/").rsplit("/", 1)[-1]
    if name != "FAILURES.md":
        return None

    # --- D-A3-01 500줄 cap (Phase 12 FAIL-PROTO-01) ---
    # Write/Edit only — MultiEdit cap is OOS (Phase 13 candidate per plan 12-05).
    if tool_name in ("Write", "Edit"):
        p = Path(fp)
        existing = p.read_text(encoding="utf-8") if p.exists() else ""
        if tool_name == "Write":
            candidate = tool_input.get("content", "")
        else:  # Edit
            old_s = tool_input.get("old_string", "")
            new_s = tool_input.get("new_string", "")
            if old_s and old_s in existing:
                candidate = existing.replace(old_s, new_s, 1)
            elif old_s:
                # old_string not found — existing append-only check will deny below
                candidate = existing
            else:
                # Edit with empty old_string = prepend insertion
                candidate = new_s + existing
        if len(candidate.splitlines()) > 500:
            return (
                "FAILURES.md 500줄 cap 초과 — "
                "`python scripts/audit/failures_rotate.py` 실행 후 재시도. "
                "(Phase 12 FAIL-PROTO-01, 500줄 cap 는 에이전트 <mandatory_reads> 전수 읽기 전제)"
            )
    # ----------------------------------------------------

    if tool_name == "Edit":
        old = tool_input.get("old_string", "")
        if old.strip():
            return (
                "FAILURES.md is append-only (D-11). "
                "Use Write to append new content, or add a new entry at EOF."
            )
    if tool_name == "Write":
        p = Path(fp)
        existing = p.read_text(encoding="utf-8") if p.exists() else ""
        new = tool_input.get("content", "")
        if existing and not new.startswith(existing):
            return (
                "FAILURES.md Write must preserve entire existing content "
                "as prefix (append-only per D-11)."
            )
    if tool_name == "MultiEdit":
        for e in tool_input.get("edits", []):
            if e.get("old_string", "").strip():
                return (
                    "FAILURES.md is append-only (D-11). "
                    "MultiEdit with non-empty old_string is denied."
                )
    return None


def backup_skill_before_write(tool_input: dict) -> None:
    """D-12: pre-tool backup of SKILL.md to SKILL_HISTORY/<skill>/v<stamp>.md.bak.

    Skips silently when:
        - file_path is missing / empty
        - target basename is not exactly 'SKILL.md'
        - target SKILL.md does not yet exist (first-time create)

    Raises OSError on disk-full / permission — caller (main) should treat as deny.

    Side effect: creates `SKILL_HISTORY/<skill_name>/v<YYYYMMDD_HHMMSS>.md.bak`
    relative to current working directory (to keep the hook studio-agnostic; the
    backup lives beside the studio root where cwd is set by Claude Code).
    """
    fp_str = tool_input.get("file_path", "")
    if not fp_str:
        return
    fp = Path(fp_str)
    if fp.name != "SKILL.md":
        return
    if not fp.exists():
        return
    skill_name = fp.parent.name
    history_dir = Path("SKILL_HISTORY") / skill_name
    history_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    shutil.copy2(fp, history_dir / f"v{stamp}.md.bak")


def main() -> int:
    # Hook input 읽기
    try:
        payload = json.loads(sys.stdin.read())
    except Exception:
        # 입력 파싱 실패 시 안전하게 allow (Hook이 파이프라인 막으면 안 됨)
        print(json.dumps({"decision": "allow"}))
        return 0

    tool_name = payload.get("tool_name", "")
    tool_input = payload.get("input", {})

    # Write/Edit 외에는 검사 안 함
    if tool_name not in ("Write", "Edit", "MultiEdit"):
        print(json.dumps({"decision": "allow"}))
        return 0

    # 검사 대상 content 추출
    content_to_check = ""
    if tool_name == "Write":
        content_to_check = tool_input.get("content", "")
    elif tool_name == "Edit":
        content_to_check = tool_input.get("new_string", "")
    elif tool_name == "MultiEdit":
        edits = tool_input.get("edits", [])
        content_to_check = "\n".join(e.get("new_string", "") for e in edits)

    # ── Phase 6 Plan 08: D-11 FAILURES.md append-only 검사 (studio-agnostic) ──
    # 이 검사는 studio_root 탐색 전에 수행. FAILURES.md 수정은 경로가 어디든 차단.
    failures_reason = check_failures_append_only(tool_name, tool_input)
    if failures_reason is not None:
        print(json.dumps({"decision": "deny", "reason": failures_reason}))
        return 0

    # ── Phase 6 Plan 08: D-12 SKILL_HISTORY 백업 (pre-write side effect) ──
    # SKILL.md 수정 직전 기존 버전을 SKILL_HISTORY/<skill>/v<stamp>.md.bak로 복사.
    # 디스크 에러 발생 시 deny로 변환 (백업 실패 = 수정 차단).
    try:
        backup_skill_before_write(tool_input)
    except OSError as e:
        print(
            json.dumps(
                {
                    "decision": "deny",
                    "reason": f"SKILL_HISTORY backup failed (D-12): {e}",
                }
            )
        )
        return 0

    # 스튜디오 루트 탐색 + 패턴 로드
    file_path = tool_input.get("file_path", "")
    if file_path:
        studio_root = find_studio_root(Path(file_path))
    else:
        studio_root = find_studio_root(Path.cwd())

    if studio_root is None:
        # 스튜디오 밖 작업 — 검사 건너뜀
        print(json.dumps({"decision": "allow"}))
        return 0

    # (신규) STRUCTURE.md Whitelist 검사 — Write 도구만
    if tool_name == "Write" and file_path:
        allowed, reason = check_structure_allowed(Path(file_path), studio_root)
        if not allowed:
            print(json.dumps({"decision": "deny", "reason": reason}))
            return 0

    patterns = load_patterns(studio_root)
    if not patterns:
        print(json.dumps({"decision": "allow"}))
        return 0

    # 위반 검사
    violations = check_content(content_to_check, patterns)

    if violations:
        reason = (
            f"❌ Deprecated pattern detected ({len(violations)}건):\n"
            + "\n".join(f"  - {v}" for v in violations)
            + "\n\nCONFLICT_MAP.md 참조. 이 패턴 제거 후 다시 시도."
        )
        print(json.dumps({"decision": "deny", "reason": reason}))
        return 0

    print(json.dumps({"decision": "allow"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
