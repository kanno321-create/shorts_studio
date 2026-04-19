"""D-15 + Pitfall 10: NotebookLMFallbackChain tier-2-only offline configuration.

Proves Phase 7 E2E pipeline can run with **zero** RAG/grep calls by
constructing a reduced ``NotebookLMFallbackChain`` that contains **only**
:class:`HardcodedDefaultsBackend`. Pitfall 10 (RESEARCH §Pitfall 10
lines 694-702) warns that if the default 3-tier chain is used and
``wiki/`` has markdown hits, GrepWikiBackend (tier 1) may succeed before
Tier 2 — breaking the D-15 offline guarantee. The fix is the reduced
chain used here.

**Nomenclature note.** In the reduced chain
``[HardcodedDefaultsBackend()]`` the backend is at list position 0, so
``query()`` returns ``tier_used == 0``. That index 0 **semantically
corresponds to tier 2** in the full D-5 taxonomy (RAG=0, grep=1,
hardcoded=2). This file pins both facts: the raw index (0) and the
semantic tier (2).
"""
from __future__ import annotations

from scripts.notebooklm.fallback import (
    GrepWikiBackend,
    HardcodedDefaultsBackend,
    NotebookLMFallbackChain,
    RAGBackend,
)


def test_reduced_chain_tier_used_is_zero_semantic_tier_2():
    """Pitfall 10: ``tier_used`` is relative to the backends list.

    For the reduced chain ``[HardcodedDefaultsBackend()]`` the single
    backend is at index 0 so ``tier_used == 0`` — which is **semantic
    tier 2** per D-5 nomenclature (RAG=0 / grep=1 / hardcoded=2 in the
    full chain). We assert tier == 0 here and document the semantic
    tier 2 mapping in the docstring + comment.
    """
    chain = NotebookLMFallbackChain(backends=[HardcodedDefaultsBackend()])
    answer, tier = chain.query("any question", "naberal-shorts-channel-bible")
    # Raw index — reduced chain has 1 backend at position 0.
    # Semantic tier 2 per D-15 (hardcoded defaults).
    assert tier == 0, (
        "Reduced chain with [HardcodedDefaultsBackend()] only MUST yield "
        f"tier_used=0 (which is semantic tier 2 per D-15); got tier={tier}"
    )
    assert isinstance(answer, str)
    assert len(answer) > 0


def test_channel_bible_returns_canonical_d10_markers():
    """D-10 canonical markers must be present in HardcodedDefaultsBackend
    response for ``naberal-shorts-channel-bible`` notebook id.

    Checks the 5 D-10 components seeded in fallback.py:165-169
    (navy + gold / 35mm lens / cinematic / Korean senior audience /
    ambient BGM) so a future refactor of HardcodedDefaultsBackend.DEFAULTS
    is caught by this test.
    """
    chain = NotebookLMFallbackChain(backends=[HardcodedDefaultsBackend()])
    answer, tier = chain.query("channel DNA", "naberal-shorts-channel-bible")
    assert tier == 0
    # D-10 canonical markers from fallback.py:165-169
    for marker in ("navy", "gold", "35mm", "cinematic", "한국 시니어", "ambient"):
        assert marker in answer, (
            f"D-10 canonical marker {marker!r} missing from hardcoded "
            f"defaults answer: {answer!r}"
        )


def test_unknown_notebook_id_returns_sentinel_no_raise():
    """HardcodedDefaultsBackend MUST NOT raise for unknown ids (tier 2
    contract: always returns a string). For unknown ids returns the
    deterministic sentinel ``fallback defaults unavailable for
    notebook_id=<id>`` (fallback.py:176-178).
    """
    chain = NotebookLMFallbackChain(backends=[HardcodedDefaultsBackend()])
    # Must not raise.
    answer, tier = chain.query("any", "unknown-notebook-id-phase07")
    assert tier == 0
    assert isinstance(answer, str)
    assert "fallback defaults unavailable" in answer
    assert "unknown-notebook-id-phase07" in answer


def test_rag_backend_not_used_in_reduced_chain():
    """D-15: tier 0 (RAGBackend = subprocess to NotebookLM) never activated.

    Proof is structural: the reduced chain has only HardcodedDefaults
    so there is no RAG path at all — no subprocess can be spawned.
    """
    chain = NotebookLMFallbackChain(backends=[HardcodedDefaultsBackend()])
    assert len(chain.backends) == 1
    assert type(chain.backends[0]) is HardcodedDefaultsBackend
    # Sanity: no RAGBackend instance exists in the chain.
    assert not any(isinstance(b, RAGBackend) for b in chain.backends)


def test_grep_wiki_backend_not_used_in_reduced_chain():
    """D-15: tier 1 (GrepWikiBackend) never activated.

    Proof is structural: reduced chain has 1 backend only — no tier 1
    traversal possible. Prevents Pitfall 10 where wiki/ hits would
    pre-empt the semantic tier 2 guarantee.
    """
    chain = NotebookLMFallbackChain(backends=[HardcodedDefaultsBackend()])
    assert len(chain.backends) == 1
    # Sanity: no GrepWikiBackend instance exists in the chain.
    assert not any(isinstance(b, GrepWikiBackend) for b in chain.backends)


def test_multiple_queries_all_semantic_tier_2():
    """D-15 batched assertion: every query across diverse keys still
    resolves via semantic tier 2 in the reduced chain.

    Uses 3+ queries with topically diverse keys from the wider
    NotebookLM canon (color_palette / focal_length / YPP gate / RPM /
    BGM mood) to exercise determinism and confirm tier == 0 (semantic
    tier 2) for every call.
    """
    chain = NotebookLMFallbackChain(backends=[HardcodedDefaultsBackend()])
    questions = [
        ("color_palette query", "naberal-shorts-channel-bible"),
        ("focal_length_mm query", "naberal-shorts-channel-bible"),
        ("YPP_entry query", "shorts-production-pipeline-bible"),
        ("RPM query", "shorts-production-pipeline-bible"),
        ("bgm_mood query", "naberal-shorts-channel-bible"),
    ]
    for question, notebook_id in questions:
        _answer, tier = chain.query(question, notebook_id)
        # Every query in the reduced chain MUST return tier == 0
        # (semantic tier 2 per D-15).
        assert tier == 0, (
            f"Query {question!r} on {notebook_id!r} returned tier={tier}; "
            "reduced chain MUST always yield tier 0 (semantic tier 2)"
        )
