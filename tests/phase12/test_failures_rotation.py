"""FAIL-PROTO-01 — 500줄 cap Hook + rotation idempotency + immutable _imported file.

Plan 12-05 Task 1 (TDD RED) — assertions here fail until Task 2 (Hook 확장) +
Task 3 (failures_rotate.py 신규) 완료 시 GREEN 전환.

Test coverage (5 cases):
    test_env_whitelist_bypasses_cap
    test_hook_denies_over_500_lines
    test_rotate_idempotent
    test_imported_file_sha256_unchanged
    test_archive_month_tag
"""

from __future__ import annotations

import hashlib
import importlib
import sys
from pathlib import Path

# tests/phase12/test_failures_rotation.py -> parents[2] = studios/shorts/
REPO_ROOT = Path(__file__).resolve().parents[2]
_HOOK_PATH = REPO_ROOT / ".claude" / "hooks"
if str(_HOOK_PATH) not in sys.path:
    sys.path.insert(0, str(_HOOK_PATH))
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

pre_tool_use = importlib.import_module("pre_tool_use")
check_failures_append_only = pre_tool_use.check_failures_append_only


def _sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def test_env_whitelist_bypasses_cap(tmp_path, monkeypatch):
    """FAILURES_ROTATE_CTX=1 → cap check 우회 (D-A3-04 whitelist)."""
    f = tmp_path / "FAILURES.md"
    f.write_text("\n".join(f"line {i}" for i in range(100)) + "\n", encoding="utf-8")
    monkeypatch.setenv("FAILURES_ROTATE_CTX", "1")
    # 600-line content would normally deny, but env whitelist bypasses all checks.
    result = check_failures_append_only(
        "Write",
        {
            "file_path": str(f),
            "content": "\n".join(f"line {i}" for i in range(600)) + "\n",
        },
    )
    assert result is None, f"env whitelist failed to bypass cap: {result!r}"


def test_hook_denies_over_500_lines(tmp_path, monkeypatch):
    """501 줄 content Write 시도 시 deny + 한국어 안내 (D-A3-01 cap)."""
    monkeypatch.delenv("FAILURES_ROTATE_CTX", raising=False)
    f = tmp_path / "FAILURES.md"
    f.write_text("existing\n", encoding="utf-8")
    new_content = "\n".join(f"line {i}" for i in range(501)) + "\n"
    result = check_failures_append_only(
        "Write",
        {"file_path": str(f), "content": new_content},
    )
    assert result is not None, "expected deny for 501-line Write, got None"
    assert "500줄" in result, f"no 500줄 cap message: {result!r}"
    assert "failures_rotate.py" in result, f"no rotation guidance: {result!r}"


def test_rotate_idempotent(tmp_path, monkeypatch):
    """rotate() 2회 연속 실행 시 2회차는 no-op (idempotent)."""
    from scripts.audit import failures_rotate

    # Seed 501-line FAILURES.md (31 head + 470 body)
    f_dir = tmp_path / ".claude" / "failures"
    f_dir.mkdir(parents=True)
    head = ["# FAILURES.md"] + [f"> line {i}" for i in range(30)]  # 31 lines
    body = [f"### FAIL-{i:03d}" for i in range(470)]
    (f_dir / "FAILURES.md").write_text("\n".join(head + body) + "\n", encoding="utf-8")

    monkeypatch.setattr(failures_rotate, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(failures_rotate, "FAILURES_FILE", f_dir / "FAILURES.md")
    monkeypatch.setattr(failures_rotate, "ARCHIVE_DIR", f_dir / "_archive")

    r1 = failures_rotate.rotate()
    sha_after_first = _sha256(f_dir / "FAILURES.md")
    r2 = failures_rotate.rotate()
    sha_after_second = _sha256(f_dir / "FAILURES.md")
    assert r1 == 1, f"first rotate expected 1 (rotated), got {r1}"
    assert r2 == 0, f"second rotate expected 0 (idempotent no-op), got {r2}"
    assert sha_after_first == sha_after_second, (
        "FAILURES.md changed between identical rotations — not idempotent"
    )


def test_imported_file_sha256_unchanged(tmp_path, monkeypatch):
    """_imported_from_shorts_naberal.md sha256 은 rotation 전후 불변 (Phase 3 D-14 lock)."""
    from scripts.audit import failures_rotate

    # Seed emulated _imported_from_shorts_naberal.md (500-line at-cap file)
    f_dir = tmp_path / ".claude" / "failures"
    f_dir.mkdir(parents=True)
    imported = f_dir / "_imported_from_shorts_naberal.md"
    imported.write_text(
        "\n".join(f"imported line {i}" for i in range(500)) + "\n",
        encoding="utf-8",
    )
    sha_before = _sha256(imported)

    # Seed oversized FAILURES.md (501 lines) to trigger rotation
    head = ["# FAILURES.md"] + [f"> line {i}" for i in range(30)]
    body = [f"### FAIL-{i:03d}" for i in range(470)]
    (f_dir / "FAILURES.md").write_text(
        "\n".join(head + body) + "\n", encoding="utf-8"
    )

    monkeypatch.setattr(failures_rotate, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(failures_rotate, "FAILURES_FILE", f_dir / "FAILURES.md")
    monkeypatch.setattr(failures_rotate, "ARCHIVE_DIR", f_dir / "_archive")

    result = failures_rotate.rotate()
    assert result == 1, "rotation should have triggered on 501-line FAILURES.md"
    sha_after = _sha256(imported)
    assert sha_before == sha_after, (
        "_imported_from_shorts_naberal.md sha256 changed — Phase 3 D-14 lock broken"
    )


def test_archive_month_tag(tmp_path, monkeypatch):
    """rotation 후 _archive/{YYYY-MM}.md 생성 + 이관된 line count 검증."""
    from datetime import datetime
    from zoneinfo import ZoneInfo

    from scripts.audit import failures_rotate

    f_dir = tmp_path / ".claude" / "failures"
    f_dir.mkdir(parents=True)
    head = ["# FAILURES.md"] + [f"> line {i}" for i in range(30)]
    body = [f"### FAIL-{i:03d}" for i in range(470)]
    (f_dir / "FAILURES.md").write_text(
        "\n".join(head + body) + "\n", encoding="utf-8"
    )

    monkeypatch.setattr(failures_rotate, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(failures_rotate, "FAILURES_FILE", f_dir / "FAILURES.md")
    monkeypatch.setattr(failures_rotate, "ARCHIVE_DIR", f_dir / "_archive")

    result = failures_rotate.rotate()
    assert result == 1, "rotation expected on 501-line FAILURES.md"
    now = datetime.now(ZoneInfo("Asia/Seoul"))
    tag = now.strftime("%Y-%m")
    archive = f_dir / "_archive" / f"{tag}.md"
    assert archive.exists(), f"archive file not created: {archive}"
    # Archived content = lines[HEAD_PRESERVE_LINES:CAP_LINES] = 500 - 31 = 469 entries
    archive_text = archive.read_text(encoding="utf-8")
    archive_lines = archive_text.strip().splitlines()
    # Allow range 460-475 to accommodate any timestamp/notice header overhead in archive
    assert 460 <= len(archive_lines) <= 475, (
        f"archive lines count {len(archive_lines)} out of expected 460-475"
    )
