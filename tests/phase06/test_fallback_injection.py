"""Phase 6 Plan 05 — D-5 Fault Injection acceptance.

Forces the real RAG subprocess to rc=1 (simulating Google outage / auth expiry /
notebook missing) and asserts the chain activates Tier 1 (grep) or Tier 2
(hardcoded). This is the canonical D-5 acceptance criterion from ROADMAP SC #3.
"""
from __future__ import annotations

from pathlib import Path

from scripts.notebooklm.fallback import (
    GrepWikiBackend,
    HardcodedDefaultsBackend,
    NotebookLMFallbackChain,
    RAGBackend,
)


def test_real_rag_backend_falls_through_on_auth_failure(
    tmp_path: Path, mock_notebooklm_skill_env: Path
):
    """D-5 acceptance: subprocess rc=1 forces chain to activate tier>=1."""
    # Rewrite the fake skill's run.py to emit auth error + rc=1
    run_py = mock_notebooklm_skill_env / "scripts" / "run.py"
    run_py.write_text(
        "import sys\nsys.stderr.write('not authenticated')\nsys.exit(1)\n",
        encoding="utf-8",
    )
    # Seed a wiki dir so Tier 1 grep can match
    wiki_dir = tmp_path / "wiki"
    (wiki_dir / "continuity_bible").mkdir(parents=True)
    (wiki_dir / "continuity_bible" / "channel_identity.md").write_text(
        "---\ncategory: continuity_bible\nstatus: ready\n"
        "tags: [x]\nupdated: 2026-04-19\n"
        "source_notebook: naberal-shorts-channel-bible\n---\n"
        "# Channel Identity\n색상 팔레트 navy + gold. 한국 시니어 타겟.",
        encoding="utf-8",
    )
    chain = NotebookLMFallbackChain(
        backends=[
            RAGBackend(),
            GrepWikiBackend(wiki_root=wiki_dir),
            HardcodedDefaultsBackend(),
        ]
    )
    answer, tier = chain.query("색상 팔레트 한국", "naberal-shorts-channel-bible")
    assert tier in (1, 2), f"expected fall-through (tier >= 1), got tier={tier}"
    assert answer, "non-empty answer expected from fallback"


def test_real_rag_backend_falls_through_to_defaults_when_wiki_empty(
    tmp_path: Path, mock_notebooklm_skill_env: Path
):
    """RAG fails + grep finds nothing -> Tier 2 hardcoded returns known default."""
    (mock_notebooklm_skill_env / "scripts" / "run.py").write_text(
        "import sys\nsys.exit(1)\n", encoding="utf-8"
    )
    empty_wiki = tmp_path / "empty_wiki"
    empty_wiki.mkdir()
    chain = NotebookLMFallbackChain(
        backends=[
            RAGBackend(),
            GrepWikiBackend(wiki_root=empty_wiki),
            HardcodedDefaultsBackend(),
        ]
    )
    answer, tier = chain.query(
        "어떤 색 팔레트가 적절한가", "naberal-shorts-channel-bible"
    )
    assert tier == 2
    assert "navy" in answer or "cinematic" in answer


def test_rag_success_returns_tier_0(
    tmp_path: Path, mock_notebooklm_skill_env: Path
):
    """When subprocess rc=0, tier=0 short-circuits the chain."""
    run_py = mock_notebooklm_skill_env / "scripts" / "run.py"
    # Child must reconfigure stdout to utf-8 so Korean/em-dash survive Windows cp949.
    # (Mirrors the Plan 03 test_notebooklm_subprocess fixture discipline.)
    run_py.write_text(
        "import sys\n"
        "sys.stdout.reconfigure(encoding='utf-8')\n"
        "sys.stdout.write('real RAG answer')\n"
        "sys.exit(0)\n",
        encoding="utf-8",
    )
    wiki_dir = tmp_path / "wiki"
    wiki_dir.mkdir()
    chain = NotebookLMFallbackChain(
        backends=[
            RAGBackend(),
            GrepWikiBackend(wiki_root=wiki_dir),
            HardcodedDefaultsBackend(),
        ]
    )
    answer, tier = chain.query("test question", "naberal-shorts-channel-bible")
    assert tier == 0
    assert "real RAG answer" in answer
