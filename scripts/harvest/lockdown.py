"""Windows Tier 3 lockdown via `attrib +R /S /D`.

CRITICAL: Git Bash CANNOT invoke `attrib +R /S /D "path/*"` directly —
shell glob expansion mangles the Windows syntax and produces a silent
security hole (verified 2026-04-19, 03-RESEARCH.md §5).

Correct invocation: subprocess.run(["cmd.exe", "/c", ...]).
Verification: probe write must raise PermissionError.
"""
from __future__ import annotations

import subprocess
from pathlib import Path


def apply_lockdown(target: Path) -> None:
    """Apply `attrib +R /S /D` recursively to target.

    Raises:
        FileNotFoundError: target does not exist.
        RuntimeError: attrib command failed with non-zero return code.
    """
    if not target.exists():
        raise FileNotFoundError(f"lockdown target not found: {target}")
    if not target.is_dir():
        raise RuntimeError(
            f"lockdown target is not a directory: {target}"
        )

    win_path = str(target.resolve()).replace("/", "\\")
    cmd = ["cmd.exe", "/c", f"attrib +R /S /D {win_path}\\*"]
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"attrib failed: rc={result.returncode}, "
            f"stderr={result.stderr!r}, stdout={result.stdout!r}"
        )


def verify_lockdown(target: Path) -> None:
    """Prove lockdown applied by attempting a write.

    Picks the first *.md under target, tries to overwrite it with a
    tamper string, and expects PermissionError.

    Raises:
        RuntimeError: no probe file found (empty directory).
        AssertionError: write succeeded → lockdown FAILED.
    """
    probe = next(target.rglob("*.md"), None)
    if probe is None:
        raise RuntimeError(
            f"No probe file (*.md) found under {target} — "
            f"cannot verify lockdown on empty directory"
        )
    original_content = probe.read_bytes()
    try:
        probe.write_text("LOCKDOWN_VERIFY_TAMPER", encoding="utf-8")
    except PermissionError:
        return  # expected — lockdown is active
    # If write succeeded, restore original content before raising
    probe.write_bytes(original_content)
    raise AssertionError(
        f"LOCKDOWN FAILED — write to {probe} succeeded. "
        f"attrib +R did not apply correctly."
    )


def unlock(target: Path) -> None:
    """Emergency unlock — `attrib -R /S /D` recursively.

    Document-only in AGENT.md; normal workflow must not call this.

    Raises:
        RuntimeError: attrib command failed.
    """
    if not target.exists():
        raise FileNotFoundError(f"unlock target not found: {target}")
    win_path = str(target.resolve()).replace("/", "\\")
    cmd = ["cmd.exe", "/c", f"attrib -R /S /D {win_path}\\*"]
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"unlock attrib failed: rc={result.returncode}, "
            f"stderr={result.stderr!r}"
        )


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print(
            "usage: python lockdown.py <apply|verify|unlock> <target_dir>",
            file=sys.stderr,
        )
        sys.exit(2)
    action = sys.argv[1]
    target = Path(sys.argv[2]) if len(sys.argv) > 2 else Path(".preserved/harvested")
    if action == "apply":
        apply_lockdown(target)
        print(f"[OK] lockdown applied to {target}")
    elif action == "verify":
        verify_lockdown(target)
        print(f"[OK] lockdown verified on {target}")
    elif action == "unlock":
        unlock(target)
        print(f"[OK] unlocked {target}")
    else:
        print(f"[FAIL] unknown action: {action}", file=sys.stderr)
        sys.exit(2)
