"""Phase 13 Preflight — Wave 1~5 live run 진입 전 환경 sanity check.

4 체크를 수행하고 모두 OK 시 rc=0, 하나라도 실패 시 rc=1:

    1. Claude CLI reachable (``claude --version`` rc=0)
       — Max 구독 CLI 경로 확인. ANTHROPIC_API_KEY 미등록 정책 (금기 #5).
    2. YouTube OAuth token refresh OK
       — ``config/client_secret.json`` + ``config/youtube_token.json`` 존재 +
         refresh_token field presence (실 API 호출 없음; Wave 2 수행).
    3. ``.env`` 필수 키 보유 확인 (TYPECAST / GOOGLE / YOUTUBE_CLIENT_SECRETS_FILE
       + any_of FAL_KEY|KLING_API_KEY + optional ELEVENLABS/RUNWAY/SHOTSTACK).
    4. ``.planning/phases/13-live-smoke/evidence/`` write-access probe.

Windows cp949 guard + ANSI-safe log + exit code contract. 본 CLI 는 Wave
1~4 전에 대표님이 수동 실행하여 billable run 진입 전 사전 차단이 가능
하도록 한다 (13-RESEARCH.md §Pitfall 1-4).

Usage::

    py -3.11 scripts/smoke/phase13_preflight.py

Exit codes:
    0 — 4 체크 모두 OK (Wave 1~5 진입 허용)
    1 — 하나 이상 실패 (대표님 개입 필요)
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

# Windows cp949 guard (Phase 11 pattern — phase11_full_run.py L51-61 승계).
# 한국어 출력 + em-dash 가 기본 Windows 콘솔 cp949 에서 깨지므로 utf-8
# 재설정 (POSIX 에서는 no-op). 실패 시 명시적 stderr 기록 — 금기 #3 준수.
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    except (AttributeError, OSError) as _enc_err:
        sys.stderr.write(
            f"[preflight] stdout reconfigure skipped: {_enc_err}\n"
        )

# Ensure repo root on sys.path when invoked directly.
_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))


def check_claude_cli() -> dict:
    """1. Claude CLI reachable + rc=0 검증.

    Max 구독 CLI 경로 (``project_claude_code_max_no_api_key.md``) — Anthropic
    SDK 중복 결제 방지. ``claude --version`` 은 local binary probe 만 수행
    하며 실 Anthropic API 호출이 아니므로 $0.

    Returns:
        dict: {"ok": bool, "version": str, "path": str, "error": str}
    """
    bin_path = shutil.which("claude")
    if not bin_path:
        return {"ok": False, "error": "claude CLI not found in PATH"}
    try:
        result = subprocess.run(
            ["claude", "--version"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=30,
        )
    except (subprocess.TimeoutExpired, OSError) as err:
        return {"ok": False, "error": f"claude --version failed: {err}"}
    if result.returncode != 0:
        return {
            "ok": False,
            "error": f"rc={result.returncode} stderr={result.stderr[-200:]}",
        }
    return {"ok": True, "version": result.stdout.strip(), "path": bin_path}


def check_youtube_oauth() -> dict:
    """2. YouTube OAuth refresh token file sanity.

    Phase 8 Plan 06 ship 결과 on-disk 확인 — ``config/client_secret.json`` +
    ``config/youtube_token.json`` 존재 + refresh_token field presence.
    실제 API refresh 호출은 수행하지 않음 (Wave 2 가 수행); 본 체크는
    파일 integrity + 구조 sanity 로 한정 — Pitfall 1 (credential staleness)
    1차 방어선.

    Returns:
        dict: {"ok": bool, "has_refresh_token": bool, "token_path": str,
               "error": str}
    """
    token_path = _REPO_ROOT / "config" / "youtube_token.json"
    client_secret_path = _REPO_ROOT / "config" / "client_secret.json"
    if not token_path.exists():
        return {"ok": False, "error": f"missing {token_path}"}
    if not client_secret_path.exists():
        return {"ok": False, "error": f"missing {client_secret_path}"}
    try:
        payload = json.loads(token_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as err:
        return {"ok": False, "error": f"token parse failed: {err}"}
    if not payload.get("refresh_token"):
        return {"ok": False, "error": "refresh_token field missing"}
    return {
        "ok": True,
        "has_refresh_token": True,
        "token_path": str(token_path),
    }


def check_env_keys() -> dict:
    """3. ``.env`` 필수 키 + any_of + 선택 키 보유 확인.

    Phase 11 ``_check_env_readiness`` pattern 승계. ``scripts.orchestrator``
    import 가 ``_load_dotenv_if_present()`` 를 package-init 시점에 호출하므로
    본 함수 진입 전에 ``.env`` 가 프로세스 env 에 주입됨.

    Tiers:
        required — absence = hard block
        any_of   — 그룹 전체 absence = hard block
        optional — absence = warn only

    Returns:
        dict: {"ok": bool, "missing_required": list, "any_of_missing": list,
               "present_optional": list}
    """
    required = [
        "TYPECAST_API_KEY",
        "GOOGLE_API_KEY",
        "YOUTUBE_CLIENT_SECRETS_FILE",
    ]
    any_of = [
        ("FAL_KEY", "KLING_API_KEY", "KLING_ACCESS_KEY"),
    ]
    optional = [
        "ELEVENLABS_API_KEY",
        "RUNWAY_API_KEY",
        "SHOTSTACK_API_KEY",
        "ELEVENLABS_DEFAULT_VOICE_ID",
    ]
    # Ensure .env loaded via orchestrator package init (PIPELINE-02 / D-13).
    # ImportError 발생 시에도 check 진행 — env 가 이미 셸에서 주입된 경우
    # 동작 가능. 금기 #3: 침묵 폴백이 아닌 명시적 stderr 로 이유 기록.
    try:
        from scripts.orchestrator import _load_dotenv_if_present  # type: ignore
        _load_dotenv_if_present()
    except ImportError as err:
        sys.stderr.write(
            f"[preflight] orchestrator import skipped (fall back to shell env): {err}\n"
        )
    missing_required = [k for k in required if not os.environ.get(k)]
    satisfied_any_of = [
        pair for pair in any_of if any(os.environ.get(k) for k in pair)
    ]
    any_of_missing = [pair for pair in any_of if pair not in satisfied_any_of]
    present_optional = [k for k in optional if os.environ.get(k)]
    ok = not missing_required and not any_of_missing
    return {
        "ok": ok,
        "missing_required": missing_required,
        "any_of_missing": [list(p) for p in any_of_missing],
        "present_optional": present_optional,
    }


def check_evidence_dir_writable() -> dict:
    """4. ``.planning/phases/13-live-smoke/evidence/`` write probe.

    mkdir + write probe + unlink — Wave 1~5 evidence anchor 가능성 사전
    검증. 실패 시 Windows permission / disk-full 등 근본 문제 가능.

    Returns:
        dict: {"ok": bool, "path": str, "error": str}
    """
    evidence_dir = (
        _REPO_ROOT / ".planning" / "phases" / "13-live-smoke" / "evidence"
    )
    try:
        evidence_dir.mkdir(parents=True, exist_ok=True)
        probe = evidence_dir / ".preflight_probe"
        probe.write_text("OK", encoding="utf-8")
        probe.unlink()
    except OSError as err:
        return {"ok": False, "error": f"write probe failed: {err}"}
    return {"ok": True, "path": str(evidence_dir)}


def main() -> int:
    """Run all 4 checks + print plain-text report + return rc.

    Returns:
        0 if all checks pass, 1 otherwise.
    """
    checks = {
        "claude_cli": check_claude_cli(),
        "youtube_oauth": check_youtube_oauth(),
        "env_keys": check_env_keys(),
        "evidence_dir": check_evidence_dir_writable(),
    }
    all_ok = all(c.get("ok") for c in checks.values())
    print("=" * 60)
    print("Phase 13 Preflight Report (대표님)")
    print("=" * 60)
    for name, result in checks.items():
        status = "OK" if result.get("ok") else "FAIL"
        print(f"  [{status}] {name}: {result}")
    print("=" * 60)
    print(f"Overall: {'ALL_PASS' if all_ok else 'FAIL'}")
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
