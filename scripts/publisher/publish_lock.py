"""48h+ jitter filesystem lock — Phase 8 PUB-03 enforcement.

Per CONTEXT D-06: ``.planning/publish_lock.json`` is the canonical lock file
path (gitignored — upload history is sensitive). The ``SHORTS_PUBLISH_LOCK_PATH``
env var overrides the default so the ``tmp_publish_lock`` fixture from
``tests/phase08/conftest.py`` can redirect to ``tmp_path`` per-test.

Pattern inherited from Phase 5 ``scripts/orchestrator/checkpointer.py``:
atomic ``os.replace(tmp, target)`` — atomic on Windows + POSIX per Python 3.3+
guarantee. Do NOT use ``os.rename`` (fails on Windows when target exists).

Jitter contract (RESEARCH §Pattern 3 lines 258-306):
- ``MIN_ELAPSED_HOURS`` constant = 48  (base minimum between uploads)
- ``MAX_JITTER_MIN`` constant = 720    (0..12h extra applied on previous upload)
- Required gap on each call          = 48h + jitter_applied_min (from lock file)
  → effective 48..60h spacing, defeats bot-pattern detection (AF-1/AF-11).

Anti-patterns refused (RESEARCH Anti-Patterns):
- naive ``datetime.now()`` comparison against aware ISO strings → TypeError.
  Always use ``datetime.now(timezone.utc)`` here.
- committing the lock file → ``.planning/publish_lock.json`` is gitignored.
- silent try/except fallback → every error propagates (hook-enforced).

Stdlib-only: ``json``, ``os``, ``random``, ``sys``, ``datetime``, ``pathlib``.
"""
from __future__ import annotations

import json
import math
import os
import random
import sys
from datetime import datetime, timezone
from pathlib import Path

from scripts.publisher.exceptions import PublishLockViolation


# UTF-8 safeguard for Windows cp949 per Phase 6 STATE #28 + RESEARCH Pitfall 3.
# Never re-raise — reconfigure is best-effort on exotic streams (pytest capture,
# CI log pipes). Hook-forbidden silent-swallow applies to business logic only.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


DEFAULT_LOCK_PATH = Path(".planning/publish_lock.json")
MIN_ELAPSED_HOURS = 48
MAX_JITTER_MIN = 720   # 0~12h additional jitter -> effective 48~60h


def _lock_path() -> Path:
    """Resolve the lock file path, honouring the test override env var.

    Returns ``DEFAULT_LOCK_PATH`` unless ``SHORTS_PUBLISH_LOCK_PATH`` is set.
    The env var MUST be read at call time (not import time) so pytest's
    ``monkeypatch.setenv`` inside ``tmp_publish_lock`` takes effect per-test.
    """
    return Path(os.environ.get("SHORTS_PUBLISH_LOCK_PATH",
                               str(DEFAULT_LOCK_PATH)))


def assert_can_publish(*, now_utc: datetime | None = None) -> None:
    """Raise ``PublishLockViolation`` if 48h+jitter has not elapsed.

    Parameters
    ----------
    now_utc
        Inject a frozen clock for deterministic tests. Defaults to
        ``datetime.now(timezone.utc)`` in production.

    Raises
    ------
    PublishLockViolation
        With ``remaining_min`` = integer minutes still to wait.

    Semantics
    ---------
    If the lock file does not exist (first-ever upload) this is a no-op —
    record_upload() has never been called, so there is no prior upload to
    honour. The lock file is created by ``record_upload`` immediately after
    a successful ``videos.insert`` call.
    """
    path = _lock_path()
    if not path.exists():
        return   # first-ever upload — no lock
    data = json.loads(path.read_text(encoding="utf-8"))
    last = datetime.fromisoformat(data["last_upload_iso"])
    jitter = int(data.get("jitter_applied_min", 0))
    required_min = MIN_ELAPSED_HOURS * 60 + jitter
    now = now_utc or datetime.now(timezone.utc)
    elapsed_min = (now - last).total_seconds() / 60
    if elapsed_min < required_min:
        # math.ceil so any sub-minute shortfall reports as >=1 minute remaining
        # (user-facing message "0 min remaining" while still blocking would be
        # confusing). Matches RESEARCH §Pattern 3 intent.
        raise PublishLockViolation(math.ceil(required_min - elapsed_min))


def record_upload(*, now_utc: datetime | None = None,
                  jitter_min: int | None = None) -> None:
    """Persist a new upload timestamp + jitter atomically.

    Parameters
    ----------
    now_utc
        Inject a frozen clock for deterministic tests. Defaults to
        ``datetime.now(timezone.utc)`` in production.
    jitter_min
        Inject a deterministic jitter for tests. Defaults to
        ``random.randint(0, MAX_JITTER_MIN)`` in production. The value is
        saved into the lock and consumed by the NEXT ``assert_can_publish``
        call — i.e. jitter applies to the forward-looking gap.

    Atomicity
    ---------
    Writes to ``<path>.tmp`` first, then ``os.replace(tmp, path)``. On
    Windows + POSIX this is atomic — either the old file or the new file
    is visible, never a half-written one. If the write step crashes, only
    ``.tmp`` is orphaned; the caller can safely retry.
    """
    path = _lock_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    now = now_utc or datetime.now(timezone.utc)
    jitter = (
        jitter_min if jitter_min is not None
        else random.randint(0, MAX_JITTER_MIN)
    )
    payload = {
        "last_upload_iso": now.isoformat(),
        "jitter_applied_min": jitter,
        "_schema": 1,
    }
    tmp = path.with_suffix(".tmp")
    tmp.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    os.replace(tmp, path)   # atomic Windows + POSIX (Python 3.3+)


__all__ = [
    "DEFAULT_LOCK_PATH",
    "MIN_ELAPSED_HOURS",
    "MAX_JITTER_MIN",
    "assert_can_publish",
    "record_upload",
]
