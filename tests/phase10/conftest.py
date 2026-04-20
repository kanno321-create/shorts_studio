"""Phase 10 shared pytest fixtures.

D-2 Lock (FAIL-04) skill_patch_counter 테스트용 공통 fixture.
Phase 5/6 conftest 패턴 (`_REPO_ROOT` import-time resolve + sys.path insert) 을
따르되, D-2 Lock 검증은 **synthetic git repo (tmp_path)** 에서만 수행한다 — 실
studio repo 를 건드리지 않는다.

Fixtures provided:
    - repo_root             : absolute Path to studios/shorts/ repo root
    - tmp_git_repo          : tmp_path 에 빈 git repo 초기화 + initial commit
    - make_commit           : (repo, files_dict, msg) -> commit_hash helper
    - freeze_kst_now        : autouse, datetime.now(KST) 를 2026-04-30T09:00 으로 고정
"""
from __future__ import annotations

import subprocess
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

# Windows cp949 stdout 가드 — 한국어 commit message round-trip.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# tests/phase10/conftest.py -> parents[2] = studios/shorts/
_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

_KST = ZoneInfo("Asia/Seoul")
_FROZEN_NOW = datetime(2026, 4, 30, 9, 0, 0, tzinfo=_KST)


@pytest.fixture
def repo_root() -> Path:
    """Absolute Path to studios/shorts/ repo root."""
    return _REPO_ROOT


@pytest.fixture
def tmp_git_repo(tmp_path: Path) -> Path:
    """Initialize an empty git repo at tmp_path with a seed commit.

    Returns the repo root. Commits a single `.gitkeep` so `git log` has at
    least one entry to walk. Configures deterministic user.name / user.email
    to keep commits reproducible across test runs.
    """
    subprocess.run(
        ["git", "init", "-q", "-b", "main", str(tmp_path)],
        check=True,
    )
    subprocess.run(
        ["git", "-C", str(tmp_path), "config", "user.email", "phase10-test@naberal.local"],
        check=True,
    )
    subprocess.run(
        ["git", "-C", str(tmp_path), "config", "user.name", "phase10-test"],
        check=True,
    )
    subprocess.run(
        ["git", "-C", str(tmp_path), "config", "commit.gpgsign", "false"],
        check=True,
    )
    seed = tmp_path / ".gitkeep"
    seed.write_text("", encoding="utf-8")
    subprocess.run(
        ["git", "-C", str(tmp_path), "add", ".gitkeep"],
        check=True,
    )
    subprocess.run(
        ["git", "-C", str(tmp_path), "commit", "-q", "--no-verify",
         "--date", "2026-04-20T10:00:00+09:00",
         "-m", "chore: seed repo"],
        check=True,
        env={**_subprocess_env(), "GIT_COMMITTER_DATE": "2026-04-20T10:00:00+09:00"},
    )
    return tmp_path


@pytest.fixture
def make_commit(tmp_git_repo: Path):
    """Return a callable that writes files + commits, returning short hash.

    Signature: make_commit(files: dict[str, str], msg: str,
                           when: str = "2026-05-01T12:00:00+09:00") -> str
    """
    def _make(files: dict[str, str], msg: str,
              when: str = "2026-05-01T12:00:00+09:00") -> str:
        for rel, content in files.items():
            p = tmp_git_repo / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(content, encoding="utf-8")
            subprocess.run(
                ["git", "-C", str(tmp_git_repo), "add", rel.replace("\\", "/")],
                check=True,
            )
        subprocess.run(
            ["git", "-C", str(tmp_git_repo), "commit", "-q", "--no-verify",
             "--date", when, "-m", msg],
            check=True,
            env={**_subprocess_env(), "GIT_COMMITTER_DATE": when},
        )
        out = subprocess.run(
            ["git", "-C", str(tmp_git_repo), "rev-parse", "HEAD"],
            check=True, capture_output=True, text=True, encoding="utf-8",
        )
        return out.stdout.strip()
    return _make


@pytest.fixture(autouse=True)
def freeze_kst_now(monkeypatch: pytest.MonkeyPatch) -> datetime:
    """Freeze datetime.now(KST) in skill_patch_counter module to 2026-04-30T09:00.

    Only applied if the module is importable (won't fail Task 1 fixture-only tests).
    """
    try:
        import scripts.audit.skill_patch_counter as spc  # noqa: WPS433
    except ImportError:
        return _FROZEN_NOW

    class _FrozenDatetime(datetime):
        @classmethod
        def now(cls, tz=None):  # type: ignore[override]
            if tz is None:
                return _FROZEN_NOW.replace(tzinfo=None)
            return _FROZEN_NOW.astimezone(tz)

    monkeypatch.setattr(spc, "datetime", _FrozenDatetime)
    return _FROZEN_NOW


def _subprocess_env() -> dict[str, str]:
    """Minimal env for git subprocess — Windows-agnostic, deterministic.

    Returns current os.environ merged with git committer overrides. Avoids
    empty-env surprises on Windows where git needs PATH / HOME.
    """
    import os
    env = dict(os.environ)
    env.setdefault("GIT_AUTHOR_NAME", "phase10-test")
    env.setdefault("GIT_AUTHOR_EMAIL", "phase10-test@naberal.local")
    env.setdefault("GIT_COMMITTER_NAME", "phase10-test")
    env.setdefault("GIT_COMMITTER_EMAIL", "phase10-test@naberal.local")
    return env
