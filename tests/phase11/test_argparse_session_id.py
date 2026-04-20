"""PIPELINE-04 tie-in — argparse session-id relax (3 cases, D-16).

Locks the contract that ``shorts_pipeline.main`` must:
  1. Accept invocation WITHOUT ``--session-id`` (required=False).
  2. Auto-generate a timestamp default matching ``YYYYMMDD_HHMMSS``.
  3. Preserve explicit ``--session-id`` override path for scheduler use.

Tests patch ``ShortsPipeline`` on the module to a recording double so we
never construct real adapters — this suite is argparse-surface only.
"""
from __future__ import annotations

import re


_TS_RE = re.compile(r"^\d{8}_\d{6}$")


def _run_main(monkeypatch, argv, tmp_path):
    """Patch ShortsPipeline to a recording double; call main(argv).

    Returns ``(rc, recorded)`` where ``recorded`` captures the ``session_id``
    and ``state_root`` kwargs the pipeline received.
    """
    from scripts.orchestrator import shorts_pipeline as sp

    recorded: dict = {}

    class RecordingPipeline:
        def __init__(self, session_id, state_root, **kwargs):
            recorded["session_id"] = session_id
            recorded["state_root"] = state_root

        def run(self):
            return {"status": "ok"}

    monkeypatch.setattr(sp, "ShortsPipeline", RecordingPipeline)
    full_argv = list(argv) + ["--state-root", str(tmp_path)]
    rc = sp.main(full_argv)
    return rc, recorded


def test_session_id_optional(monkeypatch, tmp_path):
    """main() without --session-id must NOT raise SystemExit."""
    rc, recorded = _run_main(monkeypatch, [], tmp_path)
    assert rc == 0
    assert "session_id" in recorded
    assert _TS_RE.match(recorded["session_id"]), (
        f"Expected auto-generated timestamp; got {recorded['session_id']!r}"
    )


def test_session_id_auto_default_generates_timestamp(monkeypatch, tmp_path):
    """Auto default must be ``datetime.now().strftime('%Y%m%d_%H%M%S')`` shape."""
    rc, recorded = _run_main(monkeypatch, [], tmp_path)
    assert rc == 0
    assert _TS_RE.match(recorded["session_id"])


def test_explicit_session_id_override(monkeypatch, tmp_path):
    """Explicit --session-id must win over auto-default."""
    rc, recorded = _run_main(
        monkeypatch, ["--session-id", "sess_test_override"], tmp_path,
    )
    assert rc == 0
    assert recorded["session_id"] == "sess_test_override"
