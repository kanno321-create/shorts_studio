"""Phase 10 Plan 10-06 — scripts.research_loop.monthly_update tests.

13 tests covering:
    Test 1  : template 4 placeholders exist
    Test 2  : query_notebook subprocess argv shape
    Test 3  : query_notebook returncode != 0 → (stderr, False)
    Test 4  : query_notebook TimeoutExpired → graceful tuple (no raise)
    Test 5  : render_context with fixture videos + NLM answer
    Test 6  : top_n_by_composite sort ordering (desc)
    Test 7  : T1 fallback — previous month context reuse
    Test 8  : T2 fallback — empty context + FAILURES.md F-KPI append
    Test 9  : T3 fallback — both fail → exit 1 + stderr
    Test 10 : CLI --dry-run → no file output
    Test 11 : CLI idempotent — existing target → skipped + exit 0
    Test 12 : NOTEBOOK_ID env vs --notebook-id flag + missing → exit 2
    Test 13 : Reminder contains 대표님 + 수동 업로드 wording

All tests are hermetic — no real NotebookLM subprocess call is issued; the
``subprocess.run`` name inside the module under test is monkeypatched so that
the test suite remains runnable on any developer machine (offline, no OAuth).

Plan 10-03 Rule 1 deviation rationale: the plan frontmatter still references
``wiki/shorts/kpi/`` but the real kpi_log.md shipped at ``wiki/kpi/`` in
Phase 9 Plan 09-02. This test file follows the module's ``DEFAULT_WIKI_DIR =
wiki/kpi`` (matches disk truth + Plan 10-03 precedent).
"""
from __future__ import annotations

import io
import json
import subprocess
import sys
from contextlib import redirect_stderr, redirect_stdout
from datetime import datetime
from pathlib import Path

import pytest

import scripts.research_loop.monthly_update as mu

_KST = mu.KST


# ---------------------------------------------------------------- helpers


def _make_fixture_videos() -> dict[str, dict]:
    """Five videos with deterministic composite scores (desc: v1 > v2 > v3 > v4 > v5)."""
    raw = {
        "vid_top_1": {"retention_3s": 0.70, "completion_rate": 0.45, "avg_view_sec": 28.0},
        "vid_top_2": {"retention_3s": 0.65, "completion_rate": 0.42, "avg_view_sec": 26.0},
        "vid_top_3": {"retention_3s": 0.62, "completion_rate": 0.40, "avg_view_sec": 25.0},
        "vid_bot_1": {"retention_3s": 0.48, "completion_rate": 0.27, "avg_view_sec": 18.0},
        "vid_bot_2": {"retention_3s": 0.42, "completion_rate": 0.24, "avg_view_sec": 15.0},
    }
    for m in raw.values():
        m["composite"] = mu.composite_score(m)
    return raw


def _write_template(tmp_path: Path) -> Path:
    """Copy the real template to a tmp dir so tests stay disk-isolated."""
    real_tpl = (
        Path(__file__).resolve().parents[2]
        / "wiki"
        / "kpi"
        / "monthly_context_template.md"
    )
    assert real_tpl.exists(), f"template missing: {real_tpl}"
    tpl_copy = tmp_path / "monthly_context_template.md"
    tpl_copy.write_text(real_tpl.read_text(encoding="utf-8"), encoding="utf-8")
    return tpl_copy


def _seed_failures(tmp_path: Path) -> Path:
    failures = tmp_path / "FAILURES.md"
    failures.write_text(
        "# FAILURES.md — fixture\n\n"
        "> seeded for phase10 test_research_loop\n\n"
        "## F-CTX-01 — placeholder (seed)\n\n"
        "**증상**: test fixture only.\n",
        encoding="utf-8",
    )
    return failures


# ---------------------------------------------------------------- Test 1


def test_template_has_four_placeholders():
    """Template must expose 4 primary + 3 metadata placeholders."""
    real_tpl = (
        Path(__file__).resolve().parents[2]
        / "wiki"
        / "kpi"
        / "monthly_context_template.md"
    )
    text = real_tpl.read_text(encoding="utf-8")
    for ph in ("{YEAR_MONTH}", "{TOP_3_TABLE}", "{SUCCESS_PATTERNS}", "{AVOIDANCE}"):
        assert ph in text, f"missing placeholder {ph}"
    for meta in ("{SOURCE_VIDEO_IDS}", "{NOTEBOOK_ID}", "{FALLBACK_TIER}"):
        assert meta in text, f"missing metadata placeholder {meta}"


# ---------------------------------------------------------------- Test 2


def test_query_notebook_subprocess_called_with_correct_argv(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
):
    """argv must carry run.py + ask_question.py + --question + --notebook-id."""
    skill = tmp_path / "nlm_skill"
    (skill / "scripts").mkdir(parents=True)
    (skill / "scripts" / "run.py").write_text("# fake", encoding="utf-8")

    captured: dict = {}

    def _fake_run(argv, *, cwd, capture_output, text, encoding, errors, timeout):
        captured["argv"] = list(argv)
        captured["cwd"] = cwd
        captured["timeout"] = timeout
        return subprocess.CompletedProcess(argv, 0, stdout="ok", stderr="")

    monkeypatch.setattr(mu.subprocess, "run", _fake_run)

    answer, ok = mu.query_notebook("질문", "nb-42", nlm_skill=skill, timeout=30)

    assert ok is True
    assert answer == "ok"
    assert captured["argv"][0] == sys.executable
    assert captured["argv"][1].endswith("run.py")
    assert "ask_question.py" in captured["argv"]
    assert "--question" in captured["argv"]
    q_idx = captured["argv"].index("--question")
    assert captured["argv"][q_idx + 1] == "질문"
    assert "--notebook-id" in captured["argv"]
    nid_idx = captured["argv"].index("--notebook-id")
    assert captured["argv"][nid_idx + 1] == "nb-42"
    assert captured["cwd"] == str(skill)
    assert captured["timeout"] == 30


# ---------------------------------------------------------------- Test 3


def test_query_notebook_returncode_nonzero_returns_false(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
):
    skill = tmp_path / "nlm"
    (skill / "scripts").mkdir(parents=True)
    (skill / "scripts" / "run.py").write_text("# fake", encoding="utf-8")

    def _fake_run(argv, **kw):
        return subprocess.CompletedProcess(argv, 1, stdout="", stderr="auth expired")

    monkeypatch.setattr(mu.subprocess, "run", _fake_run)

    answer, ok = mu.query_notebook("q", "nb", nlm_skill=skill)
    assert ok is False
    assert "auth expired" in answer


# ---------------------------------------------------------------- Test 4


def test_query_notebook_timeout_graceful(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
):
    """TimeoutExpired must not propagate — must degrade to (msg, False)."""
    skill = tmp_path / "nlm"
    (skill / "scripts").mkdir(parents=True)
    (skill / "scripts" / "run.py").write_text("# fake", encoding="utf-8")

    def _fake_run(argv, **kw):
        raise subprocess.TimeoutExpired(cmd=argv, timeout=1)

    monkeypatch.setattr(mu.subprocess, "run", _fake_run)

    answer, ok = mu.query_notebook("q", "nb", nlm_skill=skill, timeout=1)
    assert ok is False
    assert "timed out" in answer.lower()


def test_query_notebook_missing_runpy_returns_false(tmp_path: Path):
    """No run.py on disk → immediate graceful fail (no subprocess attempt)."""
    skill = tmp_path / "absent_skill"
    answer, ok = mu.query_notebook("q", "nb", nlm_skill=skill)
    assert ok is False
    assert "not found" in answer


# ---------------------------------------------------------------- Test 5


def test_render_context_tier_0_happy_path(tmp_path: Path):
    """T0 render must include Top 3 table rows + NLM answer verbatim."""
    tpl = _write_template(tmp_path).read_text(encoding="utf-8")
    videos = _make_fixture_videos()
    now = datetime(2026, 5, 1, 9, 0, tzinfo=_KST)
    rendered = mu.render_context(
        tpl,
        "2026-04",
        videos,
        "훅: 1.5초 고유명사 / 페르소나: 탐정↔조수 / 페이스: 2.3 syll/s",
        fallback_tier=0,
        notebook_id="nb-x",
        now=now,
    )
    # Top 3 by composite desc: vid_top_1, vid_top_2, vid_top_3
    assert "`vid_top_1`" in rendered
    assert "`vid_top_2`" in rendered
    assert "`vid_top_3`" in rendered
    # NLM answer injected as-is into SUCCESS_PATTERNS
    assert "탐정↔조수" in rendered
    # Metadata placeholders substituted
    assert "fallback_tier: 0" in rendered
    assert "notebook_id: nb-x" in rendered
    # Year-month header
    assert "2026-04" in rendered
    # Bottom 2 appear in avoidance block
    assert "vid_bot_1" in rendered
    assert "vid_bot_2" in rendered


# ---------------------------------------------------------------- Test 6


def test_top_n_by_composite_descending_order():
    videos = _make_fixture_videos()
    top = mu.top_n_by_composite(videos, n=3)
    assert [vid for vid, _ in top] == ["vid_top_1", "vid_top_2", "vid_top_3"]
    # composite must be non-increasing
    composites = [m["composite"] for _, m in top]
    assert composites == sorted(composites, reverse=True)


# ---------------------------------------------------------------- Test 7


def test_fallback_tier1_previous_month_reuse(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
):
    """T1: videos present + NLM failure → render tier=1 AND reuse prev context."""
    wiki = tmp_path / "wiki"
    wiki.mkdir()
    tpl = _write_template(tmp_path)
    # Place a prior monthly_context (2026-03) so find_previous_context hits.
    prev_md = wiki / "monthly_context_2026-03.md"
    prev_md.write_text("# prior context 2026-03\n\nkey insight: navy+gold thumbnails won.", encoding="utf-8")

    # Move the template into wiki/ so default path logic matches.
    target_tpl = wiki / "monthly_context_template.md"
    target_tpl.write_text(tpl.read_text(encoding="utf-8"), encoding="utf-8")

    failures = _seed_failures(tmp_path)

    # Daily CSV with one video — aggregate_month returns non-empty.
    daily_dir = tmp_path / "data" / "kpi_daily"
    daily_dir.mkdir(parents=True)
    (daily_dir / "kpi_2026-04-01.csv").write_text(
        "video_id,retention_3s,completion_rate,avg_view_sec,views\n"
        "vid_a,0.65,0.42,27,1000\n",
        encoding="utf-8",
    )

    # NLM subprocess: always rc=1 → tier 1 branch.
    def _fake_run(argv, **kw):
        return subprocess.CompletedProcess(argv, 1, stdout="", stderr="browser closed")

    # Need to simulate run.py existing for the skill path.
    skill = tmp_path / "nlm_skill"
    (skill / "scripts").mkdir(parents=True)
    (skill / "scripts" / "run.py").write_text("# fake", encoding="utf-8")
    monkeypatch.setattr(mu.subprocess, "run", _fake_run)

    rc = mu.main(
        [
            "--year-month", "2026-04",
            "--daily-dir", str(daily_dir),
            "--wiki-dir", str(wiki),
            "--template", str(target_tpl),
            "--nlm-skill", str(skill),
            "--notebook-id", "nb-t1",
            "--failures", str(failures),
        ]
    )
    assert rc == 0
    out_md = (wiki / "monthly_context_2026-04.md").read_text(encoding="utf-8")
    assert "T1 fallback" in out_md or "이전 달 monthly_context 재사용" in out_md
    # prior context reference flowed into SUCCESS_PATTERNS
    assert "navy+gold" in out_md
    assert "fallback_tier: 1" in out_md
    # latest copy also written
    latest = (wiki / "monthly_context_latest.md").read_text(encoding="utf-8")
    assert "vid_a" in latest


# ---------------------------------------------------------------- Test 8


def test_fallback_tier2_empty_context_failures_append(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
):
    """T2: no videos + NLM success → empty context + F-KPI-NN FAILURES append."""
    wiki = tmp_path / "wiki"
    wiki.mkdir()
    tpl = _write_template(tmp_path)
    target_tpl = wiki / "monthly_context_template.md"
    target_tpl.write_text(tpl.read_text(encoding="utf-8"), encoding="utf-8")

    failures = _seed_failures(tmp_path)

    # Empty daily_dir — aggregate_month returns {}.
    daily_dir = tmp_path / "data" / "kpi_daily"
    daily_dir.mkdir(parents=True)

    skill = tmp_path / "nlm_skill"
    (skill / "scripts").mkdir(parents=True)
    (skill / "scripts" / "run.py").write_text("# fake", encoding="utf-8")

    def _fake_run(argv, **kw):
        return subprocess.CompletedProcess(argv, 0, stdout="some retrospective", stderr="")

    monkeypatch.setattr(mu.subprocess, "run", _fake_run)

    rc = mu.main(
        [
            "--year-month", "2026-04",
            "--daily-dir", str(daily_dir),
            "--wiki-dir", str(wiki),
            "--template", str(target_tpl),
            "--nlm-skill", str(skill),
            "--notebook-id", "nb-t2",
            "--failures", str(failures),
        ]
    )
    assert rc == 0
    # Context file created (so next month T1 can reuse it).
    assert (wiki / "monthly_context_2026-04.md").exists()
    # FAILURES.md gained an F-KPI-NN heading.
    failures_text = failures.read_text(encoding="utf-8")
    assert "F-KPI-01" in failures_text
    # Empty state footer applied.
    out_md = (wiki / "monthly_context_2026-04.md").read_text(encoding="utf-8")
    assert "fallback_tier: 2" in out_md


# ---------------------------------------------------------------- Test 9


def test_fallback_tier3_both_fail_exit_1(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture,
):
    """T3: no videos + NLM failure → exit 1 + stderr alert + FAILURES append."""
    wiki = tmp_path / "wiki"
    wiki.mkdir()
    tpl = _write_template(tmp_path)
    target_tpl = wiki / "monthly_context_template.md"
    target_tpl.write_text(tpl.read_text(encoding="utf-8"), encoding="utf-8")

    failures = _seed_failures(tmp_path)

    daily_dir = tmp_path / "data" / "kpi_daily"
    daily_dir.mkdir(parents=True)

    skill = tmp_path / "nlm_skill"
    (skill / "scripts").mkdir(parents=True)
    (skill / "scripts" / "run.py").write_text("# fake", encoding="utf-8")

    def _fake_run(argv, **kw):
        return subprocess.CompletedProcess(argv, 1, stdout="", stderr="boom")

    monkeypatch.setattr(mu.subprocess, "run", _fake_run)

    rc = mu.main(
        [
            "--year-month", "2026-04",
            "--daily-dir", str(daily_dir),
            "--wiki-dir", str(wiki),
            "--template", str(target_tpl),
            "--nlm-skill", str(skill),
            "--notebook-id", "nb-t3",
            "--failures", str(failures),
        ]
    )
    assert rc == 1
    captured = capsys.readouterr()
    assert "[FAIL]" in captured.err or "FAIL" in captured.err
    # No wiki file produced in T3 — intentional, FAILURES carries the incident.
    assert not (wiki / "monthly_context_2026-04.md").exists()
    # FAILURES.md got the entry.
    assert "F-KPI-01" in failures.read_text(encoding="utf-8")


# ---------------------------------------------------------------- Test 10


def test_cli_dry_run_no_file_output(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
):
    wiki = tmp_path / "wiki"
    wiki.mkdir()
    tpl = _write_template(tmp_path)
    target_tpl = wiki / "monthly_context_template.md"
    target_tpl.write_text(tpl.read_text(encoding="utf-8"), encoding="utf-8")

    failures = _seed_failures(tmp_path)

    daily_dir = tmp_path / "data" / "kpi_daily"
    daily_dir.mkdir(parents=True)
    (daily_dir / "kpi_2026-04-01.csv").write_text(
        "video_id,retention_3s,completion_rate,avg_view_sec,views\n"
        "vid_a,0.61,0.40,25,500\n",
        encoding="utf-8",
    )

    skill = tmp_path / "nlm_skill"
    (skill / "scripts").mkdir(parents=True)
    (skill / "scripts" / "run.py").write_text("# fake", encoding="utf-8")

    def _fake_run(argv, **kw):
        return subprocess.CompletedProcess(argv, 0, stdout="patterns", stderr="")

    monkeypatch.setattr(mu.subprocess, "run", _fake_run)

    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = mu.main(
            [
                "--year-month", "2026-04",
                "--daily-dir", str(daily_dir),
                "--wiki-dir", str(wiki),
                "--template", str(target_tpl),
                "--nlm-skill", str(skill),
                "--notebook-id", "nb-dry",
                "--failures", str(failures),
                "--dry-run",
            ]
        )
    assert rc == 0
    # No artefacts on disk.
    assert not (wiki / "monthly_context_2026-04.md").exists()
    assert not (wiki / "monthly_context_latest.md").exists()
    # JSON stdout with dry_run: true.
    summary = json.loads(buf.getvalue())
    assert summary["dry_run"] is True
    assert summary["year_month"] == "2026-04"
    assert "rendered_preview" in summary


# ---------------------------------------------------------------- Test 11


def test_cli_idempotent_skip_existing(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
):
    wiki = tmp_path / "wiki"
    wiki.mkdir()
    tpl = _write_template(tmp_path)
    target_tpl = wiki / "monthly_context_template.md"
    target_tpl.write_text(tpl.read_text(encoding="utf-8"), encoding="utf-8")

    # Preexisting target.
    existing = wiki / "monthly_context_2026-04.md"
    existing.write_text("# already here — DO NOT OVERWRITE", encoding="utf-8")
    original_hash = existing.read_bytes()

    failures = _seed_failures(tmp_path)

    daily_dir = tmp_path / "data" / "kpi_daily"
    daily_dir.mkdir(parents=True)

    skill = tmp_path / "nlm_skill"
    (skill / "scripts").mkdir(parents=True)
    (skill / "scripts" / "run.py").write_text("# fake", encoding="utf-8")

    def _fake_run(argv, **kw):  # pragma: no cover — should not be invoked
        return subprocess.CompletedProcess(argv, 0, stdout="patterns", stderr="")

    monkeypatch.setattr(mu.subprocess, "run", _fake_run)

    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = mu.main(
            [
                "--year-month", "2026-04",
                "--daily-dir", str(daily_dir),
                "--wiki-dir", str(wiki),
                "--template", str(target_tpl),
                "--nlm-skill", str(skill),
                "--notebook-id", "nb-skip",
                "--failures", str(failures),
            ]
        )
    assert rc == 0
    # File untouched.
    assert existing.read_bytes() == original_hash
    summary = json.loads(buf.getvalue())
    assert summary["skipped"] is True


# ---------------------------------------------------------------- Test 12


def test_notebook_id_from_env_or_flag(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
):
    """--notebook-id absent AND NOTEBOOK_ID env unset → exit 2."""
    monkeypatch.delenv("NOTEBOOK_ID", raising=False)
    daily_dir = tmp_path / "data" / "kpi_daily"
    daily_dir.mkdir(parents=True)
    wiki = tmp_path / "wiki"
    wiki.mkdir()
    tpl = _write_template(tmp_path)
    (wiki / "monthly_context_template.md").write_text(
        tpl.read_text(encoding="utf-8"),
        encoding="utf-8",
    )

    buf_err = io.StringIO()
    with redirect_stderr(buf_err):
        rc = mu.main(
            [
                "--year-month", "2026-04",
                "--daily-dir", str(daily_dir),
                "--wiki-dir", str(wiki),
                "--template", str(wiki / "monthly_context_template.md"),
            ]
        )
    assert rc == 2
    assert "notebook-id" in buf_err.getvalue().lower() or "NOTEBOOK_ID" in buf_err.getvalue()


def test_notebook_id_env_var_accepted(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
):
    """NOTEBOOK_ID env var supplies the id when --notebook-id is omitted."""
    wiki = tmp_path / "wiki"
    wiki.mkdir()
    tpl = _write_template(tmp_path)
    target_tpl = wiki / "monthly_context_template.md"
    target_tpl.write_text(tpl.read_text(encoding="utf-8"), encoding="utf-8")

    daily_dir = tmp_path / "data" / "kpi_daily"
    daily_dir.mkdir(parents=True)
    (daily_dir / "kpi_2026-04-01.csv").write_text(
        "video_id,retention_3s,completion_rate,avg_view_sec,views\n"
        "vid_a,0.61,0.40,25,500\n",
        encoding="utf-8",
    )

    skill = tmp_path / "nlm_skill"
    (skill / "scripts").mkdir(parents=True)
    (skill / "scripts" / "run.py").write_text("# fake", encoding="utf-8")

    def _fake_run(argv, **kw):
        return subprocess.CompletedProcess(argv, 0, stdout="env-accepted", stderr="")

    monkeypatch.setattr(mu.subprocess, "run", _fake_run)
    monkeypatch.setenv("NOTEBOOK_ID", "nb-env-path")

    rc = mu.main(
        [
            "--year-month", "2026-04",
            "--daily-dir", str(daily_dir),
            "--wiki-dir", str(wiki),
            "--template", str(target_tpl),
            "--nlm-skill", str(skill),
            "--failures", str(_seed_failures(tmp_path)),
            "--dry-run",
        ]
    )
    assert rc == 0


# ---------------------------------------------------------------- Test 13


def test_reminder_mentions_manual_upload(tmp_path: Path):
    """Plan requirement: stdout reminder dispatch must include 대표님 + 수동 업로드."""
    target = tmp_path / "wiki" / "monthly_context_2026-04.md"
    reminder = mu._build_reminder("2026-04", target)
    assert "대표님" in reminder
    assert "수동" in reminder or "업로드" in reminder
    assert "Pitfall 6" in reminder


def test_cli_dry_run_emits_reminder(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
):
    """--dry-run JSON summary must carry the reminder field for automation."""
    wiki = tmp_path / "wiki"
    wiki.mkdir()
    tpl = _write_template(tmp_path)
    target_tpl = wiki / "monthly_context_template.md"
    target_tpl.write_text(tpl.read_text(encoding="utf-8"), encoding="utf-8")

    daily_dir = tmp_path / "data" / "kpi_daily"
    daily_dir.mkdir(parents=True)
    (daily_dir / "kpi_2026-04-01.csv").write_text(
        "video_id,retention_3s,completion_rate,avg_view_sec,views\n"
        "vid_a,0.61,0.40,25,500\n",
        encoding="utf-8",
    )

    skill = tmp_path / "nlm_skill"
    (skill / "scripts").mkdir(parents=True)
    (skill / "scripts" / "run.py").write_text("# fake", encoding="utf-8")

    def _fake_run(argv, **kw):
        return subprocess.CompletedProcess(argv, 0, stdout="patterns", stderr="")

    monkeypatch.setattr(mu.subprocess, "run", _fake_run)

    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = mu.main(
            [
                "--year-month", "2026-04",
                "--daily-dir", str(daily_dir),
                "--wiki-dir", str(wiki),
                "--template", str(target_tpl),
                "--nlm-skill", str(skill),
                "--notebook-id", "nb-reminder",
                "--failures", str(_seed_failures(tmp_path)),
                "--dry-run",
            ]
        )
    assert rc == 0
    summary = json.loads(buf.getvalue())
    assert "reminder" in summary
    assert "대표님" in summary["reminder"]
