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
import sys
import re
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
