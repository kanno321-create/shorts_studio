"""Rank candidates by relevance to a section's visual_directing + keywords.

Simple keyword-overlap score (Jaccard-ish, no embeddings) — sufficient for
v3 prototype where section visual_directing already contains distinct proper
nouns (Ryan Waller, Phoenix, Carver, Dalton).
"""
from __future__ import annotations

import re
from typing import Any


_TOKEN_RE = re.compile(r"[\w가-힣]+", re.UNICODE)
_STOPWORDS = frozenset([
    "a", "an", "the", "of", "to", "and", "or", "in", "on", "at", "for", "with",
    "이", "그", "저", "은", "는", "이", "가", "을", "를", "의", "에", "에서", "로", "으로",
    "와", "과", "도", "만", "부터", "까지", "하지만", "그리고",
])


def _tokenize(text: str) -> set[str]:
    return {
        t.lower() for t in _TOKEN_RE.findall(text or "")
        if t.lower() not in _STOPWORDS and len(t) > 1
    }


def score_candidate(candidate: dict[str, Any], query_terms: set[str]) -> float:
    """Return 0..1 overlap score against candidate title+description+channel."""
    corpus = " ".join([
        candidate.get("title", ""),
        candidate.get("description", ""),
        candidate.get("channel", ""),
    ])
    cand_terms = _tokenize(corpus)
    if not cand_terms or not query_terms:
        return 0.0
    overlap = cand_terms & query_terms
    # Precision-weighted: reward candidates that have most of the query terms
    return len(overlap) / max(1, len(query_terms))


def rank_candidates(
    candidates: list[dict[str, Any]],
    query_text: str,
    extra_terms: list[str] | None = None,
) -> list[dict[str, Any]]:
    """Score each candidate and return sorted desc by score.

    Each returned dict gets an added ``_score`` field.
    """
    terms = _tokenize(query_text)
    if extra_terms:
        for t in extra_terms:
            terms.update(_tokenize(t))
    scored = []
    for c in candidates:
        s = score_candidate(c, terms)
        # License preference: PD/CC-BY preferred over fair-use
        lic_bonus = {"public-domain": 0.15, "cc-by": 0.10,
                     "fair-use-educational": 0.0, "unknown": -0.20}.get(
            c.get("license_flag", "unknown"), 0.0
        )
        c_copy = dict(c)
        c_copy["_score"] = round(s + lic_bonus, 4)
        c_copy["_matched_terms"] = sorted(_tokenize(
            " ".join([c.get("title", ""), c.get("description", "")])
        ) & terms)
        scored.append(c_copy)
    scored.sort(key=lambda c: c["_score"], reverse=True)
    return scored
