"""Web news article + embedded video search — stub (v3 prototype).

Multi-source intent includes news media (ABC, Dateline, etc.) but scraping
arbitrary news sites with requests is unreliable and violates robots. Claude
Agent with WebSearch/WebFetch MCP is the production path; this stub holds
the contract so callers can swap in MCP/Tavily without refactoring.

For v3, actual coverage comes from YouTube (fair-use educational) and
Wikimedia Commons (PD/CC-BY). Web-news path returns [] so callers fall
back gracefully.
"""
from __future__ import annotations

from typing import Any


def search_web(query: str, max_results: int = 10) -> list[dict[str, Any]]:
    """Stub — returns empty list. Production: Tavily/Exa MCP + HTML scrape."""
    _ = query, max_results
    return []
