"""FAIL-03 unit tests for backup_skill_before_write (D-12).

In-process import of the Hook helper; verifies:
    - Backup file is created for existing SKILL.md
    - Backup filename matches v<YYYYMMDD_HHMMSS>.md.bak format
    - Backup content is byte-identical to the original
    - First-time create (SKILL.md does not yet exist) is silently skipped
    - Non-SKILL.md files are silently skipped (no false-positive backup dir)
    - SKILL_HISTORY/<skill>/ parent directory is created automatically
    - Empty / missing file_path is a no-op (no exception)
    - Unicode content (Korean) is preserved byte-for-byte
"""
from __future__ import annotations

import importlib
import re
import sys
from pathlib import Path


# tests/phase06/test_skill_history_backup.py -> parents[2] = studios/shorts/
_REPO = Path(__file__).resolve().parents[2]
_HOOK_PATH = _REPO / ".claude" / "hooks"
if str(_HOOK_PATH) not in sys.path:
    sys.path.insert(0, str(_HOOK_PATH))

pre_tool_use = importlib.import_module("pre_tool_use")
backup_skill_before_write = pre_tool_use.backup_skill_before_write


def test_backup_created_for_existing_skill(
    tmp_path: Path, monkeypatch
):
    """Existing SKILL.md under .claude/skills/<name>/ -> backup file created."""
    monkeypatch.chdir(tmp_path)
    skill_dir = tmp_path / ".claude" / "skills" / "my-skill"
    skill_dir.mkdir(parents=True)
    skill_file = skill_dir / "SKILL.md"
    skill_file.write_text("original skill content", encoding="utf-8")

    backup_skill_before_write({"file_path": str(skill_file)})

    history = tmp_path / "SKILL_HISTORY" / "my-skill"
    backups = sorted(history.glob("v*.md.bak"))
    assert len(backups) == 1
    assert backups[0].read_text(encoding="utf-8") == "original skill content"


def test_backup_filename_format_matches_timestamp(
    tmp_path: Path, monkeypatch
):
    """Filename must match v<YYYYMMDD_HHMMSS>.md.bak (exactly 8+6 digits)."""
    monkeypatch.chdir(tmp_path)
    skill_dir = tmp_path / ".claude" / "skills" / "foo"
    skill_dir.mkdir(parents=True)
    skill_file = skill_dir / "SKILL.md"
    skill_file.write_text("content", encoding="utf-8")

    backup_skill_before_write({"file_path": str(skill_file)})

    history = tmp_path / "SKILL_HISTORY" / "foo"
    backups = sorted(history.glob("v*.md.bak"))
    assert len(backups) == 1
    assert re.match(r"^v\d{8}_\d{6}\.md\.bak$", backups[0].name), (
        f"Unexpected backup filename: {backups[0].name}"
    )


def test_backup_skipped_on_first_time_create(
    tmp_path: Path, monkeypatch
):
    """SKILL.md does not yet exist -> backup silently skipped (no dir created)."""
    monkeypatch.chdir(tmp_path)
    skill_dir = tmp_path / ".claude" / "skills" / "new-skill"
    skill_dir.mkdir(parents=True)
    skill_file = skill_dir / "SKILL.md"  # does not exist
    assert not skill_file.exists()

    backup_skill_before_write({"file_path": str(skill_file)})

    history = tmp_path / "SKILL_HISTORY" / "new-skill"
    # Either the history dir doesn't exist, or it exists with zero backups
    assert not history.exists() or not list(history.glob("v*.md.bak"))


def test_backup_skipped_for_non_skill_files(
    tmp_path: Path, monkeypatch
):
    """File with basename other than SKILL.md -> no backup attempted."""
    monkeypatch.chdir(tmp_path)
    other_file = tmp_path / "other.md"
    other_file.write_text("content", encoding="utf-8")

    backup_skill_before_write({"file_path": str(other_file)})

    assert not (tmp_path / "SKILL_HISTORY").exists(), (
        "Backup dir must not be created for non-SKILL.md files"
    )


def test_backup_skipped_for_skill_md_sibling_basenames(
    tmp_path: Path, monkeypatch
):
    """SKILLS.md, SKILL.md.bak, mySKILL.md -> NOT backed up (basename != 'SKILL.md')."""
    monkeypatch.chdir(tmp_path)
    for name in ("SKILLS.md", "SKILL.md.bak", "mySKILL.md"):
        f = tmp_path / name
        f.write_text("x", encoding="utf-8")
        backup_skill_before_write({"file_path": str(f)})
    assert not (tmp_path / "SKILL_HISTORY").exists()


def test_backup_with_empty_file_path_no_raise(
    tmp_path: Path, monkeypatch
):
    """Empty / missing file_path must be a silent no-op (no exception)."""
    monkeypatch.chdir(tmp_path)
    backup_skill_before_write({"file_path": ""})
    backup_skill_before_write({})  # no file_path key at all
    backup_skill_before_write({"file_path": None})  # type: ignore[arg-type]
    # Should not have created any backup dir
    assert not (tmp_path / "SKILL_HISTORY").exists()


def test_backup_directory_created_automatically(
    tmp_path: Path, monkeypatch
):
    """SKILL_HISTORY/<skill>/ parent must be created when missing (mkdir parents=True)."""
    monkeypatch.chdir(tmp_path)
    skill_dir = tmp_path / ".claude" / "skills" / "fresh-skill"
    skill_dir.mkdir(parents=True)
    skill_file = skill_dir / "SKILL.md"
    skill_file.write_text("x", encoding="utf-8")

    assert not (tmp_path / "SKILL_HISTORY").exists()
    backup_skill_before_write({"file_path": str(skill_file)})
    assert (tmp_path / "SKILL_HISTORY" / "fresh-skill").is_dir()


def test_backup_content_is_byte_identical_korean(
    tmp_path: Path, monkeypatch
):
    """Korean / special chars must be preserved byte-for-byte (encoding-safe copy)."""
    monkeypatch.chdir(tmp_path)
    skill_dir = tmp_path / ".claude" / "skills" / "korean-skill"
    skill_dir.mkdir(parents=True)
    skill_file = skill_dir / "SKILL.md"
    original = "한국어 내용 with em-dash — and special chars\n# Header\n"
    skill_file.write_text(original, encoding="utf-8")

    backup_skill_before_write({"file_path": str(skill_file)})

    bak_files = list((tmp_path / "SKILL_HISTORY" / "korean-skill").glob("v*.md.bak"))
    assert len(bak_files) == 1
    assert bak_files[0].read_text(encoding="utf-8") == original


def test_multiple_backups_same_skill_accumulate(
    tmp_path: Path, monkeypatch
):
    """Calling backup twice on the same SKILL.md must NOT overwrite — each must
    produce a new .bak file (timestamp-based name provides uniqueness)."""
    import time

    monkeypatch.chdir(tmp_path)
    skill_dir = tmp_path / ".claude" / "skills" / "multi"
    skill_dir.mkdir(parents=True)
    skill_file = skill_dir / "SKILL.md"
    skill_file.write_text("v1 content", encoding="utf-8")

    backup_skill_before_write({"file_path": str(skill_file)})
    # Sleep >= 1 second so YYYYMMDD_HHMMSS timestamp differs
    time.sleep(1.1)
    skill_file.write_text("v2 content", encoding="utf-8")
    backup_skill_before_write({"file_path": str(skill_file)})

    backups = sorted((tmp_path / "SKILL_HISTORY" / "multi").glob("v*.md.bak"))
    assert len(backups) == 2
    contents = [b.read_text(encoding="utf-8") for b in backups]
    assert "v1 content" in contents
    assert "v2 content" in contents
