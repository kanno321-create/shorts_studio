#!/usr/bin/env python3
"""
post_tool_use.py — 공용 PostToolUse Hook (Layer 1 naberal_harness)

목적: 모든 tool call을 **append-only 로그**로 기록.
     이후 drift 감지·감사·디버깅에 활용.

각 스튜디오가 자기 `.claude/hooks/`에 복사해서 사용.
"""
from __future__ import annotations
import json
import sys
import time
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


def main() -> int:
    try:
        payload = json.loads(sys.stdin.read())
    except Exception:
        return 0  # 실패해도 파이프라인 방해 금지

    studio_root = find_studio_root(Path.cwd())
    if studio_root is None:
        return 0

    log_dir = studio_root / ".claude" / "hooks"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "post_tool_log.jsonl"

    # 민감 정보 마스킹 (토큰·쿠키·패스워드 키 제외)
    tool_input = payload.get("input", {})
    SENSITIVE_KEYS = {"token", "password", "secret", "cookie", "api_key", "auth"}
    def mask(d):
        if isinstance(d, dict):
            return {
                k: ("***MASKED***" if any(s in k.lower() for s in SENSITIVE_KEYS) else mask(v))
                for k, v in d.items()
            }
        if isinstance(d, list):
            return [mask(x) for x in d]
        return d

    record = {
        "ts": time.time(),
        "ts_iso": time.strftime("%Y-%m-%dT%H:%M:%S%z", time.localtime()),
        "tool": payload.get("tool_name", ""),
        "input_summary": mask(tool_input) if tool_input else None,
        "result_type": type(payload.get("result")).__name__,
        "error": payload.get("error"),
    }

    # Append-only 기록
    try:
        with log_file.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    except Exception as e:
        sys.stderr.write(f"[post_tool_use] log write failed: {e}\n")

    # Hook은 통과만 — 반환값 무관
    return 0


if __name__ == "__main__":
    sys.exit(main())
