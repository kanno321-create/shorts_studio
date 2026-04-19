"""NotebookLM 3-tier Fallback Chain per D-5 (WIKI-04).

Contract (RESEARCH Area 4, lines 619-690)
-----------------------------------------
``RAG query -> grep wiki/ -> hardcoded defaults``

A single RAG dependency (NotebookLM subprocess via ``query_notebook``) is a
Single Point of Failure for every agent-facing knowledge query. D-5 mandates
graceful degradation through two progressively-weaker tiers so the pipeline
never hard-fails on Google outage, auth expiry, or notebook-not-found.

Tier matrix (see RESEARCH Area 4 lines 634-642):

  Tier 0  RAGBackend               subprocess rc!=0 / timeout / auth -> raise
  Tier 1  GrepWikiBackend          no markdown hits                 -> raise
  Tier 2  HardcodedDefaultsBackend last-known-good canonical string -> never raises
  ---     all three raise          only if backends list empty or all fail
                                   -> RuntimeError("all NotebookLM fallback tiers exhausted")

D-5 acceptance (ROADMAP Phase 6 SC #3): intentional fault injection
(subprocess rc=1) forces tier>=1 activation without losing the caller's
answer-contract. See ``tests/phase06/test_fallback_injection.py``.

Design notes
------------
- ``QueryBackend`` is ``@runtime_checkable`` so downstream code can do
  ``isinstance(backend, QueryBackend)`` defensively without hitting
  PEP 544's structural-only default.
- Individual backends must raise on failure (no silent empty strings) per
  CLAUDE.md Project Rule 3 ("try-except silent fallback forbidden"). The
  chain orchestrator is the ONLY place that translates those raises into
  tier transitions.
- Tier 2 is the lone exception: it always returns a string, never raises.
  For unknown notebook ids it returns a deterministic sentinel so the
  caller can observe degraded mode explicitly.
- Backend order inside the chain is deterministic (``list``, not ``set``)
  and externally configurable via the ``backends`` kwarg for test doubles.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Protocol, runtime_checkable

from .query import query_notebook


# ---------------------------------------------------------------------------
# Protocol
# ---------------------------------------------------------------------------


@runtime_checkable
class QueryBackend(Protocol):
    """Structural interface for a single fallback tier.

    Implementations MUST raise on failure. The chain orchestrator interprets
    any exception as "this tier exhausted, try next" — silent empty returns
    would defeat the fall-through mechanism.
    """

    def query(self, question: str, notebook_id: str) -> str:  # pragma: no cover - protocol
        ...


# ---------------------------------------------------------------------------
# Tier 0 — RAGBackend
# ---------------------------------------------------------------------------


class RAGBackend:
    """Tier 0: NotebookLM RAG via the Plan 03 subprocess wrapper.

    Reuses ``scripts.notebooklm.query.query_notebook`` verbatim so there is
    exactly one subprocess boundary in the codebase (D-7 discipline). Any
    ``RuntimeError`` / ``FileNotFoundError`` / ``subprocess.TimeoutExpired``
    raised by ``query_notebook`` propagates unchanged — the chain
    orchestrator handles the fall-through.
    """

    def query(self, question: str, notebook_id: str) -> str:
        return query_notebook(question=question, notebook_id=notebook_id)


# ---------------------------------------------------------------------------
# Tier 1 — GrepWikiBackend
# ---------------------------------------------------------------------------


class GrepWikiBackend:
    """Tier 1: grep ``wiki/**/*.md`` for keyword intersection.

    Keyword extraction pulls tokens of length >= 3 (ASCII word chars or
    Korean) from the question. A file is considered a hit only if ALL
    extracted keywords appear (case-insensitive) in its text — intersection
    semantics prevent noisy single-keyword matches.

    Returns concatenated snippet blocks (first 500 chars of each hit file,
    prefixed with ``## <path>``). Raises when either the keyword set is
    empty or no file matches every keyword.
    """

    WIKI_ROOT_DEFAULT = Path("wiki")
    SNIPPET_CHARS = 500
    KEYWORD_LIMIT = 5
    MIN_KEYWORD_LEN = 3

    def __init__(self, wiki_root: Path | None = None) -> None:
        self.wiki_root = Path(wiki_root) if wiki_root is not None else self.WIKI_ROOT_DEFAULT

    def _extract_keywords(self, question: str) -> list[str]:
        # ASCII word chars OR Korean syllables, min 3 chars, first 5 tokens
        tokens = re.findall(
            rf"[\w가-힣]{{{self.MIN_KEYWORD_LEN},}}",
            question,
        )
        return tokens[: self.KEYWORD_LIMIT]

    def query(self, question: str, notebook_id: str) -> str:
        keywords = self._extract_keywords(question)
        if not keywords:
            raise RuntimeError("grep wiki: empty keyword set")

        lowered_keywords = [k.lower() for k in keywords]
        hits: list[str] = []

        if self.wiki_root.exists():
            for md_path in sorted(self.wiki_root.rglob("*.md")):
                try:
                    text = md_path.read_text(encoding="utf-8")
                except (UnicodeDecodeError, OSError):
                    continue
                lowered = text.lower()
                if all(kw in lowered for kw in lowered_keywords):
                    snippet = text[: self.SNIPPET_CHARS]
                    hits.append(f"## {md_path}\n{snippet}")

        if not hits:
            raise RuntimeError("grep wiki: no hits")
        return "\n\n".join(hits)


# ---------------------------------------------------------------------------
# Tier 2 — HardcodedDefaultsBackend
# ---------------------------------------------------------------------------


class HardcodedDefaultsBackend:
    """Tier 2: last-known-good canonical strings per notebook_id.

    MUST NOT raise under any input. For unknown notebook ids returns a
    deterministic sentinel (``fallback defaults unavailable for
    notebook_id=<id>``) so the caller can branch on explicit degradation.

    Seeded strings encode D-5 + D-10 + D-16 canonical truths so downstream
    agents still receive minimally-useful context even if both RAG and
    wiki grep fail:

    - ``naberal-shorts-channel-bible`` -> color palette + lens + style +
      Korean senior audience + BGM mood (D-10 five components)
    - ``shorts-production-pipeline-bible`` -> YPP gate + RPM + T2V ban
    """

    DEFAULTS: dict[str, str] = {
        "naberal-shorts-channel-bible": (
            "색상=navy+gold, lens=35mm, style=cinematic, "
            "audience=한국 시니어, bgm=ambient"
        ),
        "shorts-production-pipeline-bible": (
            "YPP=1000구독+10M views/yr, RPM=$0.20, T2V 금지 I2V only"
        ),
    }

    def query(self, question: str, notebook_id: str) -> str:
        return self.DEFAULTS.get(
            notebook_id,
            f"fallback defaults unavailable for notebook_id={notebook_id}",
        )


# ---------------------------------------------------------------------------
# Chain orchestrator
# ---------------------------------------------------------------------------


class NotebookLMFallbackChain:
    """D-5 canonical 3-tier chain orchestrator.

    Iterates backends in order; the first backend whose ``query`` returns
    a value short-circuits and its zero-based index becomes ``tier_used``.
    When every backend raises, a ``RuntimeError`` is emitted with the
    literal signature ``"all NotebookLM fallback tiers exhausted"`` — Plan
    05 fault-injection tests and downstream Phase 7 E2E asserts pin this
    string.
    """

    def __init__(self, backends: list[QueryBackend] | None = None) -> None:
        if backends is None:
            self.backends: list[QueryBackend] = [
                RAGBackend(),
                GrepWikiBackend(),
                HardcodedDefaultsBackend(),
            ]
        else:
            self.backends = list(backends)

    def query(self, question: str, notebook_id: str) -> tuple[str, int]:
        """Return ``(answer, tier_used)``.

        tier_used: 0 = RAG, 1 = grep wiki, 2 = hardcoded defaults.
        Raises ``RuntimeError`` only if every backend raised.
        """
        for tier_index, backend in enumerate(self.backends):
            try:
                return backend.query(question, notebook_id), tier_index
            except Exception:  # noqa: BLE001 — chain must swallow ONLY here
                # Intentional: tier fall-through. Individual backends already
                # raised a diagnostic; the chain's job is to translate that
                # into a tier transition. D-5 explicit non-silent design:
                # the final RuntimeError below still surfaces total failure.
                continue
        raise RuntimeError("all NotebookLM fallback tiers exhausted")


__all__ = [
    "QueryBackend",
    "RAGBackend",
    "GrepWikiBackend",
    "HardcodedDefaultsBackend",
    "NotebookLMFallbackChain",
]
