"""AI disclosure hardcoded True — Phase 8 PUB-01 + RESEARCH Pitfall 6 Correction.

Correction to Phase 4 publisher AGENT.md: the canonical YouTube Data API v3
field name is ``status.containsSyntheticMedia`` (added 2024-10-30). The agent
spec's custom ``syntheticMedia`` key is non-canonical and must be translated
to ``containsSyntheticMedia`` at the body-build boundary (this module).

Per CONTEXT D-05: ``containsSyntheticMedia`` is HARDCODED to literal True. No
code path exists that sets it otherwise — this matches Phase 5 D-07's
physical-removal principle (skip_gates elimination playbook). ANCHOR A test
``tests/phase08/test_ai_disclosure_anchor.py`` enforces this via AST parse +
publisher-dir-wide grep scan.

Two entry points:
- :func:`build_status_block` returns the ``status`` body block with the AI
  disclosure flag locked to True. Callers pick privacy / embed / stats flags;
  the disclosure bit is NOT parametrised.
- :func:`assert_synthetic_media_true` is the runtime last-line defense —
  raises :class:`AIDisclosureViolation` on anything other than literal True
  (strict ``is True`` identity check; truthy-1 / strings / missing all raise).

Why HARDCODED (not config toggle):
- Typecast + ElevenLabs synth voice is ALWAYS used.
- YouTube AI-content policy (2024-10) requires disclosure; mis-disclosure
  risks channel strikes + reduced reach.
- A toggle is a foot-gun; absence of a toggle IS the correctness proof.
"""
from __future__ import annotations

from typing import Any

from scripts.publisher.exceptions import AIDisclosureViolation


def build_status_block(
    *,
    privacy_status: str = "public",
    embeddable: bool = True,
    public_stats_viewable: bool = True,
) -> dict[str, Any]:
    """Build the YouTube Data API v3 ``status`` body block.

    The AI disclosure bit (``containsSyntheticMedia``) is HARDCODED to the
    literal ``True`` — do NOT parametrise it (D-05 physical-removal principle).
    ``selfDeclaredMadeForKids`` is similarly hardcoded to ``False`` because the
    channel niche (true crime / adult narrative) is not a kids property.

    Parameters
    ----------
    privacy_status
        ``"public"`` (default), ``"unlisted"`` (smoke tests — Wave 5), or
        ``"private"``. YouTube API validates this server-side.
    embeddable
        Whether the video can be embedded on external sites. Defaults to True
        (maximises reach).
    public_stats_viewable
        Whether view count / like count is public. Defaults to True.

    Returns
    -------
    dict
        Shape compatible with ``youtube.videos().insert(part="snippet,status",
        body={"snippet": {...}, "status": <this return>})``.
    """
    return {
        "privacyStatus": privacy_status,
        "selfDeclaredMadeForKids": False,
        "containsSyntheticMedia": True,    # <-- HARDCODED — do NOT parametrise
        "license": "youtube",
        "embeddable": embeddable,
        "publicStatsViewable": public_stats_viewable,
    }


def assert_synthetic_media_true(status_block: dict[str, Any]) -> None:
    """Runtime guard — raise :class:`AIDisclosureViolation` on anything but True.

    Uses strict ``is True`` identity check (not truthiness) so ``1``, ``"yes"``,
    non-empty strings, or missing keys ALL raise. Callers should invoke this
    on the dict they are about to pass to ``videos().insert(body=...)`` as the
    last line of defence — the AST anchor guards against static regression, this
    guards against dynamic corruption (e.g. dict.update overwriting the flag).

    Parameters
    ----------
    status_block
        The ``status`` dict from :func:`build_status_block` (or any equivalent).

    Raises
    ------
    AIDisclosureViolation
        When ``status_block["containsSyntheticMedia"]`` is not the literal True.
    """
    if status_block.get("containsSyntheticMedia") is not True:
        raise AIDisclosureViolation(
            "containsSyntheticMedia must be True "
            f"(got {status_block.get('containsSyntheticMedia')!r})"
        )


__all__ = ["build_status_block", "assert_synthetic_media_true"]
