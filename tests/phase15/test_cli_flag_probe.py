"""SPC-04 — Claude CLI ``--append-system-prompt-file`` flag 실측 확증.

대표님 Phase 13 live smoke 재진입의 근거 확립 목적. 실 CLI 바이너리를
호출하지만 존재하지 않는 파일 경로를 전달하여 **모델 호출 전 단계** 에서
error 반환 — 따라서 $0 (비과금).

Evidence:
    ``.planning/phases/15-system-prompt-compression-user-feedback-loop/``
    ``evidence/15-01-cli-probe.log`` — 실측 stdout/stderr/rc append-only 로그.
    Wave 1 Plan 15-02 이 ``--append-system-prompt-file`` 채택의 근거로
    영구 참조.

Design:
    Test 2 는 error 메시지에 "file not found" / "파일" / "ENOENT" 같은
    **file-level error** 가 포함됨을 확인 — CLI 가 flag 를 인식했고
    (unknown-option 이 아니고) file I/O 단계까지 진입했음을 증명.
"""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

# Evidence log 경로 — repo-root 기준 절대경로로 해석.
EVIDENCE = (
    Path(__file__).resolve().parents[2]
    / ".planning"
    / "phases"
    / "15-system-prompt-compression-user-feedback-loop"
    / "evidence"
    / "15-01-cli-probe.log"
)


@pytest.fixture(scope="module")
def claude_bin() -> str:
    """claude 바이너리 절대경로 — 미설치 시 skip (대표님 CI 공용)."""
    bin_path = shutil.which("claude")
    if not bin_path:
        pytest.skip("claude CLI 미설치 — Max 구독 환경 아님 (대표님)")
    return bin_path


def _append_evidence(tag: str, stdout: str, stderr: str, rc: int) -> None:
    """Append stdout/stderr/rc block to evidence log (UTF-8)."""
    EVIDENCE.parent.mkdir(parents=True, exist_ok=True)
    with EVIDENCE.open("a", encoding="utf-8") as fp:
        fp.write(
            f"\n## {tag}\n"
            f"rc={rc}\n"
            f"--- stdout ---\n{stdout}\n"
            f"--- stderr ---\n{stderr}\n"
        )


def test_claude_binary_resolvable(claude_bin: str) -> None:
    """shutil.which 가 claude 바이너리 절대경로를 반환합니다."""
    assert Path(claude_bin).exists(), (
        f"claude 바이너리 경로 미존재 (대표님): {claude_bin}"
    )


def test_append_system_prompt_file_flag_recognized(claude_bin: str) -> None:
    """``--append-system-prompt-file`` 이 CLI 에 인식됨을 실측.

    File-not-found error 반환 자체가 flag 인식의 empirical 증거.
    Flag 미인식 시 CLI 는 "unknown option" / "unrecognized" 반환.
    """
    result = subprocess.run(
        [
            claude_bin,
            "--print",
            "--append-system-prompt-file",
            "/tmp/nonexistent-15-01-probe",
        ],
        input="hi",
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=15,
    )
    _append_evidence(
        "test_append_system_prompt_file_flag",
        result.stdout,
        result.stderr,
        result.returncode,
    )
    # flag 인식 → nonexistent file 에 대해 비영 rc
    assert result.returncode != 0, (
        f"flag 인식 시 nonexistent file → 비영 rc 필수 "
        f"(대표님, rc={result.returncode})"
    )
    # file-level error 의 흔적이 있어야 함 (flag 가 파싱되어 I/O 단계 진입)
    stderr_lower = result.stderr.lower()
    file_error_found = (
        "not found" in stderr_lower
        or "파일" in result.stderr
        or "enoent" in stderr_lower
        or "no such file" in stderr_lower
    )
    assert file_error_found, (
        f"flag 인식 안 됨 — stderr 에 file error 없음 (대표님): "
        f"{result.stderr[:500]}"
    )
    # unknown-option error 는 반대 증거 — 절대 나와선 안 됨
    assert "unknown option" not in stderr_lower, (
        f"flag 미인식 증거 발견 (대표님): {result.stderr[:300]}"
    )
    assert "unrecognized" not in stderr_lower, (
        f"flag 미인식 증거 발견 (대표님): {result.stderr[:300]}"
    )


def test_system_prompt_file_flag_also_exists(claude_bin: str) -> None:
    """``--system-prompt-file`` (non-append variant) 도 인식 — SPC-04 Option B 문서화.

    Wave 1 Plan 15-02 가 Option A (append-semantics 승계) 를 채택할 예정이나,
    Option B 가 차선책으로 가용함을 evidence 로 기록하여 장래 reversion
    가능성을 보존합니다.
    """
    result = subprocess.run(
        [
            claude_bin,
            "--print",
            "--system-prompt-file",
            "/tmp/nonexistent-15-01-probe-sys",
        ],
        input="hi",
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=15,
    )
    _append_evidence(
        "test_system_prompt_file_flag",
        result.stdout,
        result.stderr,
        result.returncode,
    )
    assert result.returncode != 0, (
        f"flag 인식 시 nonexistent file → 비영 rc 필수 "
        f"(대표님, rc={result.returncode})"
    )
    stderr_lower = result.stderr.lower()
    assert "unknown option" not in stderr_lower, (
        f"--system-prompt-file flag 미인식 (대표님): {result.stderr[:300]}"
    )
    assert "unrecognized" not in stderr_lower, (
        f"--system-prompt-file flag 미인식 (대표님): {result.stderr[:300]}"
    )
