"""Fallback helpers for the Phase 5 orchestrator (ORCH-12 / D-12).

Two surface helpers:

* :func:`append_failures` — append-only write to
  ``.claude/failures/orchestrator.md`` per the FAIL-01 contract. Never
  truncates; tests in ``test_fallback_shot.py`` assert existing content
  survives concurrent appends.
* :func:`insert_fallback_shot` — ken-burns over a static image when the
  regeneration loop in ``ShortsPipeline._producer_loop`` has exhausted its
  three retries on an ASSETS or THUMBNAIL gate (RESEARCH §9 lines 836-847).
  Receives a :class:`ShotstackAdapter` via dependency injection so the
  unit tests can exercise it with ``unittest.mock.MagicMock``.

Kept small (≤140 lines) so the keystone ``shorts_pipeline.py`` can stay
well within the D-1 500~800 line budget by delegating both I/O patterns
here instead of inlining.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Callable


DEFAULT_FAILURES_PATH = Path(".claude/failures/orchestrator.md")


def append_failures(
    failures_path: Path,
    session_id: str,
    gate: str,
    evidence: list[dict],
    semantic_feedback: str,
) -> None:
    """Append one failure record to ``failures_path`` (FAIL-01 / D-12 contract).

    The file is opened in ``"a"`` (append) mode so existing content is
    preserved byte-for-byte; ``"w"`` is never used. Parent directories are
    materialised when missing (fresh clones may not have
    ``.claude/failures/`` yet).

    The emitted entry is deterministic markdown so downstream parsers and
    tests can grep for ``<!-- session:... gate:... ts:... -->`` markers
    and assert ordering.
    """

    failures_path.parent.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc).isoformat()
    evidence_summary = "; ".join(
        f"{e.get('rule', '?')}: {e.get('detail', '(no detail)')}"
        for e in (evidence or [])[:3]
    )
    entry = (
        f"\n<!-- session:{session_id} gate:{gate} ts:{now} -->\n"
        f"## {session_id} {gate} FAIL after regeneration exhausted\n\n"
        f"- **Timestamp:** {now}\n"
        f"- **Evidence (first 3):** {evidence_summary}\n"
        f"- **Semantic feedback:** {semantic_feedback}\n"
    )
    # open 'a' == append-only mode; no truncation, no seek(0).
    with failures_path.open("a", encoding="utf-8") as fh:
        fh.write(entry)


def insert_fallback_shot(
    shotstack_adapter,
    asset_sourcer_invoker: Callable[[str], Path],
    prompt: str,
    duration_s: float,
    scale_from: float = 1.0,
    scale_to: float = 1.15,
    pan_direction: str = "left_to_right",
) -> dict:
    """Build an ORCH-12 Fallback shot (ken-burns over a static image).

    Parameters
    ----------
    shotstack_adapter:
        Instance exposing ``create_ken_burns_clip(image_path, duration_s,
        scale_from, scale_to, pan_direction) -> Path``. Real code injects
        :class:`scripts.orchestrator.api.shotstack.ShotstackAdapter`;
        tests inject ``MagicMock``.
    asset_sourcer_invoker:
        Callable that takes a prompt string and returns a :class:`Path` to
        a stock still image (typically calling Phase 4's asset-sourcer
        Producer harness).
    prompt:
        Scene prompt the failed Producer was trying to satisfy. Passed to
        ``asset_sourcer_invoker`` so the still image matches the scene.
    duration_s:
        Clip duration to hit — matches the failed cut's intended duration
        so the Shotstack timeline does not need re-alignment.

    Returns
    -------
    dict
        ``{"path": Path, "is_fallback": True, "prompt": str, "duration_s":
        float, "source_image": Path}``. The ``is_fallback`` flag is
        consumed by ``VoiceFirstTimeline.align`` diagnostics and by the
        Checkpointer ``fallback_indices`` tracking.
    """

    still_image = asset_sourcer_invoker(prompt)
    if not isinstance(still_image, Path):
        still_image = Path(still_image)

    fallback_clip = shotstack_adapter.create_ken_burns_clip(
        image_path=still_image,
        duration_s=duration_s,
        scale_from=scale_from,
        scale_to=scale_to,
        pan_direction=pan_direction,
    )
    return {
        "path": fallback_clip,
        "is_fallback": True,
        "prompt": prompt,
        "duration_s": duration_s,
        "source_image": still_image,
    }


def dedupe_fallback_key(session_id: str, gate: str, cut_index: int) -> str:
    """Build the dedup key for ``GateContext.fallback_indices``.

    RESEARCH §9 line 862 specifies per-session + per-gate + per-cut
    deduplication so a resume after partial failure does not double-insert
    the same ken-burns shot.
    """

    return f"{session_id}:{gate}:{cut_index}"


__all__ = [
    "DEFAULT_FAILURES_PATH",
    "append_failures",
    "insert_fallback_shot",
    "dedupe_fallback_key",
]
