"""Phase 5 Orchestrator v2 — Checkpointer (ORCH-05 per CONTEXT D-5).

Atomic JSON-per-GATE persistence at ``state/{session_id}/gate_{n:02d}.json``.

Purpose
-------
Durable state across process restart + observability for post-mortem debugging
+ sha256 artifact fingerprinting for integrity audit.

Used by
-------
- Plan 04 GateGuard.dispatch() — saves a checkpoint on every successful PASS
- Plan 07 shorts_pipeline.py — resume(session_id) on start-up to pick up
  from the next gate after the highest persisted gate_index
- Plan 02 CircuitBreaker — breaker state may embed into each checkpoint via
  the ``artifacts`` / ``verdict`` dicts (RESEARCH §Checkpointer Design
  circuit_breakers extension)

Design constraints (locked by plan + RESEARCH)
----------------------------------------------
- Atomic cross-platform write via ``os.replace(tmp, target)`` — NOT the
  shutil rename helper (not atomic on Windows, RESEARCH §4 lines 664-665).
- Filenames zero-padded: ``gate_{gate_index:02d}.json`` for lexicographic
  sort (Plan 04 resume iteration depends on sort order).
- ``ensure_ascii=False`` so Korean evidence survives round-trip (grep-based
  debugging would break with ``\\uXXXX`` escapes).
- Schema version field ``_schema: 1`` embedded for forward compatibility.
- Idempotent re-writes: same (session_id, gate_index) overwrites silently.
- Stdlib-only: ``json``, ``os``, ``hashlib``, ``dataclasses``, ``pathlib``,
  ``datetime``. Python 3.11+ (per D-19).
"""
from __future__ import annotations

import hashlib
import json
import os
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path


# ============================================================================
# Schema version (forward-compatibility marker embedded in every JSON)
# ============================================================================

SCHEMA_VERSION: int = 1


# ============================================================================
# Checkpoint dataclass (D-5 canonical record)
# ============================================================================


@dataclass
class Checkpoint:
    """ORCH-05 per-GATE persistence record (CONTEXT D-5).

    Fields match the D-5 JSON schema byte-for-byte (minus the ``_schema``
    version field which is injected by :class:`Checkpointer.save`).

    Attributes
    ----------
    session_id : str
        Opaque session identifier (D-5 path namespace). Example:
        ``"20260419-143022-wildlife-mantis"``.
    gate : str
        :class:`scripts.orchestrator.GateName` ``.name`` string, e.g.
        ``"NICHE"``. Used by :meth:`Checkpointer.dispatched_gates` to
        reconstruct the dispatched set after resume.
    gate_index : int
        :class:`scripts.orchestrator.GateName` ``.value`` (0-14). Drives the
        on-disk filename ``gate_{gate_index:02d}.json``.
    timestamp : str
        ISO 8601 UTC with microseconds, e.g.
        ``"2026-04-19T14:35:40.123456+00:00"``.
    verdict : dict
        Rubric-schema draft-07 Verdict shape:
        ``{result, score, evidence, semantic_feedback, inspector_name}``.
    artifacts : dict
        Either ``{"path": str, "sha256": str}`` or ``{}`` when no artifact
        file exists (e.g. IDLE / bookkeeping checkpoints).
    """

    session_id: str
    gate: str
    gate_index: int
    timestamp: str
    verdict: dict
    artifacts: dict


# ============================================================================
# Checkpointer (atomic filesystem persistence)
# ============================================================================


class Checkpointer:
    """Atomic JSON-per-GATE persistence for Phase 5 orchestrator (ORCH-05).

    Path layout
    -----------
    ``{state_root}/{session_id}/gate_{gate_index:02d}.json``

    Write protocol (atomic, Windows + POSIX safe)
    ---------------------------------------------
    1. Serialize payload to ``{target}.tmp`` via ``Path.write_text``
       (``ensure_ascii=False, indent=2``).
    2. ``os.replace(tmp, target)`` — atomic rename per Python docs
       (https://docs.python.org/3/library/os.html#os.replace).

    If step 1 crashes, only the ``.tmp`` file is orphaned; the real target
    is untouched. If step 2 raises, the caller aborts the gate — never a
    half-written checkpoint.

    Resume protocol
    ---------------
    :meth:`resume` returns the highest ``gate_index`` in the session dir,
    or ``-1`` when the session directory does not exist. Plan 07 pipeline
    advances to ``GateName(last + 1)`` to continue from the next gate.
    """

    SCHEMA_VERSION: int = SCHEMA_VERSION

    def __init__(self, state_root: Path = Path("state")) -> None:
        self.root = Path(state_root)

    def save(self, cp: Checkpoint) -> Path:
        """Persist one checkpoint atomically. Returns the final target path.

        Idempotent: same ``(session_id, gate_index)`` overwrites silently
        (``os.replace`` is defined to replace an existing destination).
        """
        target_dir = self.root / cp.session_id
        target_dir.mkdir(parents=True, exist_ok=True)
        target = target_dir / f"gate_{cp.gate_index:02d}.json"
        tmp = target.with_suffix(target.suffix + ".tmp")
        payload = {"_schema": self.SCHEMA_VERSION, **asdict(cp)}
        tmp.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        # os.replace: atomic on Windows + POSIX (Python 3.3+ guarantee).
        # Do NOT use the shutil rename helper — not atomic on Windows per
        # stdlib docs; same-filesystem case does copy+delete internally.
        os.replace(tmp, target)
        return target

    def resume(self, session_id: str) -> int:
        """Highest ``gate_index`` saved for ``session_id``, or ``-1`` if none.

        Returns ``-1`` when the session directory does not exist OR exists
        but contains no valid ``gate_NN.json`` files. Junk files (non-int
        indices, unrelated extensions) are silently ignored.
        """
        d = self.root / session_id
        if not d.exists():
            return -1
        indices: list[int] = []
        for p in d.glob("gate_*.json"):
            stem_parts = p.stem.split("_")
            if len(stem_parts) < 2:
                continue
            try:
                indices.append(int(stem_parts[1]))
            except ValueError:
                # e.g. "gate_NOT_INT.json" — ignore, keep scanning
                continue
        return max(indices) if indices else -1

    def dispatched_gates(self, session_id: str) -> set[str]:
        """Set of :class:`GateName` ``.name`` strings persisted for ``session_id``.

        Reconstructs Plan 04 GateGuard's ``dispatched`` set from disk so a
        restarted pipeline can honor ``verify_all_dispatched()`` semantics.
        Missing session dir → empty set. Corrupt JSON / missing ``gate`` key
        → silently skipped (we trust the filesystem as source-of-truth and
        do not want a single bad file to brick resume).
        """
        d = self.root / session_id
        if not d.exists():
            return set()
        out: set[str] = set()
        for p in sorted(d.glob("gate_*.json")):
            try:
                data = json.loads(p.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                continue
            gate = data.get("gate")
            if isinstance(gate, str):
                out.add(gate)
        return out

    def load(self, session_id: str, gate_index: int) -> dict | None:
        """Read one gate checkpoint back as a dict. ``None`` if file absent.

        Returned dict contains the ``_schema`` field plus every
        :class:`Checkpoint` attribute. Plan 07 uses this to rehydrate
        circuit-breaker state from the most recent gate file.
        """
        target = self.root / session_id / f"gate_{gate_index:02d}.json"
        if not target.exists():
            return None
        return json.loads(target.read_text(encoding="utf-8"))


# ============================================================================
# Helpers
# ============================================================================


def sha256_file(path: Path, chunk_size: int = 65536) -> str:
    """Streaming SHA256 hex digest for arbitrarily large files.

    Streams in 64 KiB chunks so memory stays bounded regardless of file
    size (artifacts like assembled 4K MP4s can exceed several GiB).

    Source pattern: ``.preserved/harvested/hc_checks_raw/hc_checks.py``
    lines 438-450 (RESEARCH §Code Examples lines 1142-1154).
    """
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            h.update(chunk)
    return h.hexdigest()


def make_timestamp() -> str:
    """ISO 8601 UTC with microseconds — D-5 canonical timestamp format.

    Example output: ``"2026-04-19T14:35:40.123456+00:00"``. Timezone-aware
    so downstream parsers can distinguish from naive local times.
    """
    return datetime.now(timezone.utc).isoformat()
