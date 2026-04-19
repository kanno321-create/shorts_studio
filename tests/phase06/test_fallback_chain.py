"""Phase 6 Plan 05 — Fallback Chain unit tests.

Covers D-5 3-tier regime: RAG > grep wiki > hardcoded defaults.

Scope:
- HardcodedDefaultsBackend never-raises contract + known-id seeded answers
- GrepWikiBackend keyword intersection logic + empty/no-hit raises
- NotebookLMFallbackChain sequencing with Fake backends
- Default constructor wires the 3 real backends in order
"""
from __future__ import annotations

from pathlib import Path

import pytest

from scripts.notebooklm.fallback import (
    GrepWikiBackend,
    HardcodedDefaultsBackend,
    NotebookLMFallbackChain,
    QueryBackend,
    RAGBackend,
)


class FakeFailing:
    """Backend double that always raises — used to force fall-through."""

    def __init__(self, label: str) -> None:
        self.label = label

    def query(self, q: str, nid: str) -> str:
        raise RuntimeError(f"simulated fail: {self.label}")


class FakeSucceeding:
    """Backend double that returns a canned answer — verifies tier short-circuit."""

    def __init__(self, answer: str) -> None:
        self.answer = answer

    def query(self, q: str, nid: str) -> str:
        return self.answer


# ---------------------------------------------------------------------------
# HardcodedDefaultsBackend
# ---------------------------------------------------------------------------


def test_hardcoded_known_id_channel_bible_returns_D10_canonical():
    h = HardcodedDefaultsBackend()
    answer = h.query("아무거나", "naberal-shorts-channel-bible")
    assert "색상" in answer
    assert "navy" in answer
    assert "cinematic" in answer
    assert "한국 시니어" in answer


def test_hardcoded_known_id_production_bible_returns_YPP_canonical():
    h = HardcodedDefaultsBackend()
    answer = h.query("question", "shorts-production-pipeline-bible")
    assert "YPP" in answer
    assert "T2V" in answer
    assert "I2V only" in answer


def test_hardcoded_unknown_id_returns_sentinel():
    h = HardcodedDefaultsBackend()
    answer = h.query("q", "unknown-notebook-xxx")
    assert answer == "fallback defaults unavailable for notebook_id=unknown-notebook-xxx"


def test_hardcoded_never_raises():
    """Tier 2 must be the safety net — no raise under any input."""
    h = HardcodedDefaultsBackend()
    for nid in ["", "xyz", "nonexistent-notebook", "naberal-shorts-channel-bible"]:
        h.query("query", nid)  # should not raise


# ---------------------------------------------------------------------------
# GrepWikiBackend
# ---------------------------------------------------------------------------


def test_grep_wiki_finds_keyword_intersection(tmp_wiki_dir: Path):
    (tmp_wiki_dir / "algorithm" / "note_a.md").write_text(
        "retention hook 완주율 signal 알고리즘", encoding="utf-8"
    )
    (tmp_wiki_dir / "kpi" / "note_b.md").write_text(
        "Different content entirely", encoding="utf-8"
    )
    grep = GrepWikiBackend(wiki_root=tmp_wiki_dir)
    answer = grep.query("retention 완주율", "whatever")
    assert "알고리즘" in answer or "retention" in answer


def test_grep_wiki_no_hits_raises(tmp_wiki_dir: Path):
    (tmp_wiki_dir / "algorithm" / "note.md").write_text("unrelated content", encoding="utf-8")
    grep = GrepWikiBackend(wiki_root=tmp_wiki_dir)
    with pytest.raises(RuntimeError, match="grep wiki: no hits"):
        grep.query("absolutely_different_keyword_xyz", "N")


def test_grep_wiki_empty_question_raises(tmp_wiki_dir: Path):
    """Question with no >=3 char tokens must raise, not silently return empty."""
    grep = GrepWikiBackend(wiki_root=tmp_wiki_dir)
    with pytest.raises(RuntimeError):
        grep.query("a b", "N")


def test_grep_wiki_requires_all_keywords(tmp_wiki_dir: Path):
    """Intersection semantics — partial match must NOT hit."""
    (tmp_wiki_dir / "algorithm" / "only_retention.md").write_text(
        "retention discussion only here — no other terms",
        encoding="utf-8",
    )
    grep = GrepWikiBackend(wiki_root=tmp_wiki_dir)
    # Question has two >=3 char tokens; file contains only one -> no hit
    with pytest.raises(RuntimeError, match="grep wiki: no hits"):
        grep.query("retention absent_word_xyzzy", "N")


# ---------------------------------------------------------------------------
# NotebookLMFallbackChain — default construction + sequencing
# ---------------------------------------------------------------------------


def test_chain_default_constructs_3_backends():
    chain = NotebookLMFallbackChain()
    assert len(chain.backends) == 3
    assert isinstance(chain.backends[0], RAGBackend)
    assert isinstance(chain.backends[1], GrepWikiBackend)
    assert isinstance(chain.backends[2], HardcodedDefaultsBackend)


def test_chain_tier_0_success_short_circuits():
    chain = NotebookLMFallbackChain(
        backends=[
            FakeSucceeding("rag answer"),
            FakeFailing("grep should-not-run"),
            FakeFailing("defaults should-not-run"),
        ]
    )
    answer, tier = chain.query("Q", "N")
    assert answer == "rag answer"
    assert tier == 0


def test_chain_falls_through_to_tier_1():
    chain = NotebookLMFallbackChain(
        backends=[
            FakeFailing("rag"),
            FakeSucceeding("grep answer"),
            FakeFailing("defaults should-not-run"),
        ]
    )
    answer, tier = chain.query("Q", "N")
    assert answer == "grep answer"
    assert tier == 1


def test_chain_falls_through_to_tier_2():
    chain = NotebookLMFallbackChain(
        backends=[
            FakeFailing("rag"),
            FakeFailing("grep"),
            HardcodedDefaultsBackend(),
        ]
    )
    answer, tier = chain.query("Q", "naberal-shorts-channel-bible")
    assert "색상" in answer
    assert tier == 2


def test_chain_all_fail_raises_exhausted():
    chain = NotebookLMFallbackChain(
        backends=[FakeFailing("a"), FakeFailing("b"), FakeFailing("c")]
    )
    with pytest.raises(RuntimeError, match="all NotebookLM fallback tiers exhausted"):
        chain.query("Q", "N")


def test_chain_empty_backends_raises_exhausted():
    chain = NotebookLMFallbackChain(backends=[])
    with pytest.raises(RuntimeError, match="exhausted"):
        chain.query("Q", "N")


def test_query_backend_protocol_runtime_checkable():
    """Protocol must be runtime-checkable so isinstance() works for validation."""
    assert isinstance(HardcodedDefaultsBackend(), QueryBackend)
    assert isinstance(FakeSucceeding("x"), QueryBackend)
