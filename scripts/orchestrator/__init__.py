"""scripts.orchestrator — Phase 5 public API surface.

Downstream plans (08 hc_checks, 09 Hook extensions, 10 SC acceptance) and
all future callers import from this namespace, NOT from the individual
modules directly. The namespace collects every primitive produced by
Waves 0-4 plus the keystone :class:`ShortsPipeline` from Wave 5.

Phase 11 additions (PIPELINE-02 / D-13~D-16):
    `_load_dotenv_if_present()` runs at package import time so adapters
    constructed downstream see `.env` values automatically. Zero external
    dependency (pure stdlib). ``os.environ.setdefault`` preserves
    pre-existing env (matches ``override=False`` convention).
"""
from __future__ import annotations

import os
import re
from pathlib import Path


def _load_dotenv_if_present() -> None:
    """Zero-dep ``.env`` loader. Idempotent. override=False semantics.

    Reads ``./.env`` relative to the current working directory and populates
    :data:`os.environ` using :meth:`os.environ.setdefault` (pre-existing env
    wins — matches the ``override=False`` semantics used by the existing
    ``scripts/experimental/test_*.py`` convention).

    Parser contract (verified by ``tests/phase11/test_dotenv_loader.py``):
        - Comments (``#`` as first non-whitespace char) skipped
        - Empty / whitespace-only lines skipped
        - ``export KEY=VAL`` bash prefix stripped
        - Values may contain ``=`` (split on FIRST ``=`` only)
        - Surrounding matched ``"`` or ``'`` quotes stripped from value
        - UTF-8 BOM on first line tolerated (``utf-8-sig`` decode)
        - CRLF line endings tolerated (rstrip ``\\r``)

    Silent skip when ``.env`` is missing — tests / CI without the file
    continue with the pre-existing environment.

    PIPELINE-02 / Phase 11 D-13, D-14, D-15. Called at package import time
    so adapters constructed by :class:`ShortsPipeline` observe env values
    loaded from disk. See RESEARCH §Pitfall 2 for placement reasoning
    (must run BEFORE submodule imports trigger adapter module loads).
    """
    env_path = Path(".env")
    if not env_path.exists():
        return
    try:
        # ``utf-8-sig`` transparently strips a leading UTF-8 BOM if present;
        # otherwise behaves identically to ``utf-8``.
        raw = env_path.read_text(encoding="utf-8-sig")
    except OSError:
        return

    line_re = re.compile(
        r"^\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*?)\s*$"
    )
    for raw_line in raw.splitlines():
        line = raw_line.rstrip("\r")
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        match = line_re.match(line)
        if not match:
            continue
        key, value = match.group(1), match.group(2)
        # Strip surrounding matched quotes (single OR double) once.
        if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
            value = value[1:-1]
        os.environ.setdefault(key, value)


# Run at package import time — before any adapter ``__init__`` can look at
# ``os.environ``. See RESEARCH §Pitfall 2 for placement reasoning.
_load_dotenv_if_present()


from .checkpointer import Checkpoint, Checkpointer, sha256_file
from .circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerOpenError,
    CircuitState,
)
from .gate_guard import GateGuard, Verdict
from .gates import (
    GATE_DEPS,
    CircuitOpen,
    GateDependencyUnsatisfied,
    GateFailure,
    GateName,
    IncompleteDispatch,
    InvalidGateTransition,
    InvalidI2VRequest,
    MissingVerdict,
    OrchestratorError,
    RegenerationExhausted,
    T2VForbidden,
)
from .shorts_pipeline import GATE_INSPECTORS, GateContext, ShortsPipeline
from .voice_first_timeline import (
    AudioSegment,
    ClipDurationMismatch,
    IntegratedRenderForbidden,
    InvalidClipDuration,
    TimelineEntry,
    TimelineMismatch,
    TransitionEntry,
    VideoCut,
    VoiceFirstTimeline,
)

__all__ = [
    # gates.py
    "GateName",
    "GATE_DEPS",
    "OrchestratorError",
    "InvalidGateTransition",
    "GateFailure",
    "MissingVerdict",
    "IncompleteDispatch",
    "GateDependencyUnsatisfied",
    "CircuitOpen",
    "RegenerationExhausted",
    "T2VForbidden",
    "InvalidI2VRequest",
    # circuit_breaker.py
    "CircuitBreaker",
    "CircuitBreakerOpenError",
    "CircuitState",
    # checkpointer.py
    "Checkpointer",
    "Checkpoint",
    "sha256_file",
    # gate_guard.py
    "GateGuard",
    "Verdict",
    # voice_first_timeline.py
    "VoiceFirstTimeline",
    "AudioSegment",
    "VideoCut",
    "TimelineEntry",
    "TransitionEntry",
    "TimelineMismatch",
    "InvalidClipDuration",
    "ClipDurationMismatch",
    "IntegratedRenderForbidden",
    # shorts_pipeline.py (Wave 5 keystone)
    "ShortsPipeline",
    "GateContext",
    "GATE_INSPECTORS",
]
