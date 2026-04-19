"""Production metadata — Phase 8 PUB-04 D-08.

Per CONTEXT D-08: the ``production_metadata`` block is injected as a single
HTML comment at the END of the YouTube video description. Viewers never see
it (HTML comments in YT descriptions are stripped from rendered output), but
Phase 9 analytics can parse it back out with the exact regex::

    r'<!-- production_metadata\\n(\\{.*?\\})\\n-->'   (DOTALL)

4-field TypedDict per Phase 4 ``ins-platform-policy`` enforcement contract:

- ``script_seed``     — Phase 5 orchestrator deterministic seed
                        (episode-level reproducibility anchor).
- ``assets_origin``   — e.g. ``"kling:primary"`` / ``"runway:fallback"``.
                        Trace video-assets back to I2V source for E-P2
                        (Reused Content) rebuttals.
- ``pipeline_version``— Semver string. Bumps here flag Phase 9 schema
                        evolution boundaries.
- ``checksum``        — ``"sha256:<64-hex>"`` of the mp4 file. Byte-exact
                        proof that the uploaded artefact matches the
                        pipeline-produced file.

Why HTML comment (not tag field)::

- YouTube tag field has a 500 char hard cap; descriptions allow 5000 chars.
- Tag field value is public; HTML comments are private-ish (not rendered).
- Phase 9 analytics needs stable structured parsing — regex on a tagged
  comment block is simpler than parsing CSV-style tags.

Why streaming sha256 (not ``hashlib.sha256(p.read_bytes())``)::

- Shorts mp4s today are 10-30MB; future long-form could hit 500MB+.
- ``p.read_bytes()`` doubles peak RSS; streaming keeps it constant.
- 64KB chunk size matches the default IO block on modern filesystems.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import TypedDict


# UTF-8 safeguard for Windows cp949 per Phase 6 STATE #28 + RESEARCH Pitfall 3.
# Best-effort — never re-raise (exotic streams like pytest capture can refuse).
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


PIPELINE_VERSION = "1.0.0"   # Phase 8 shipping version — bump on schema drift

_CHUNK_SIZE = 65536   # 64 KB streaming window
_REQUIRED_FIELDS = frozenset({
    "script_seed",
    "assets_origin",
    "pipeline_version",
    "checksum",
})


class ProductionMetadata(TypedDict):
    """4-field schema — ALL fields required. Field names are frozen by Phase 4
    ins-platform-policy regex; renaming breaks Phase 9 analytics.
    """

    script_seed: str         # Phase 5 orchestrator deterministic seed
    assets_origin: str       # e.g. "kling:primary" / "runway:fallback"
    pipeline_version: str    # Semver matching PIPELINE_VERSION
    checksum: str            # "sha256:<64-hex>"


def compute_checksum(mp4_path: Path) -> str:
    """Stream-hash ``mp4_path`` in 64KB chunks and return ``"sha256:<hex>"``.

    Parameters
    ----------
    mp4_path
        Absolute or cwd-relative path to the mp4 artefact. Accepts str or
        Path; always coerced to ``Path`` before open.

    Returns
    -------
    str
        ``"sha256:"`` + 64-char lowercase hexdigest.

    Notes
    -----
    Memory footprint is bounded by ``_CHUNK_SIZE`` (64KB) regardless of file
    size. The hash is computed over the raw byte stream — no decompression,
    no metadata stripping.
    """
    h = hashlib.sha256()
    with Path(mp4_path).open("rb") as f:
        for chunk in iter(lambda: f.read(_CHUNK_SIZE), b""):
            h.update(chunk)
    return f"sha256:{h.hexdigest()}"


def inject_into_description(description: str, meta: ProductionMetadata) -> str:
    """Append the production_metadata HTML comment block to ``description``.

    Parameters
    ----------
    description
        Existing video description (may be empty string). Left byte-exact;
        the comment block is ONLY appended at tail.
    meta
        4-field ``ProductionMetadata``. All four keys MUST be present;
        missing keys raise ``ValueError`` with a message containing
        ``"PUB-04 schema violation"`` plus the list of missing fields.

    Returns
    -------
    str
        ``description + "\\n<!-- production_metadata\\n" + <compact JSON>
        + "\\n-->"``.

    Raises
    ------
    ValueError
        If ``meta`` is missing any of the 4 required fields. Phase 4
        ``ins-platform-policy`` would FAIL the upload anyway — raising
        early saves the network round-trip.

    Notes
    -----
    ``json.dumps(meta, ensure_ascii=False, separators=(",", ":"))``
    preserves Korean characters verbatim and uses compact delimiters so
    the 5000-char description ceiling stays maximally available.
    """
    missing = _REQUIRED_FIELDS - set(meta.keys())
    if missing:
        # Sorted for deterministic error messages (assertion-friendly).
        raise ValueError(
            f"PUB-04 schema violation: missing fields {sorted(missing)}"
        )
    block = (
        "\n<!-- production_metadata\n"
        + json.dumps(meta, ensure_ascii=False, separators=(",", ":"))
        + "\n-->"
    )
    return description + block


__all__ = [
    "PIPELINE_VERSION",
    "ProductionMetadata",
    "compute_checksum",
    "inject_into_description",
]
