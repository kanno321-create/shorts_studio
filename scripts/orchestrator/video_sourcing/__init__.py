"""Multi-source video/image footage sourcing prototype (v3).

Session #34 new module per feedback_multi_source_video_search_required.
대표님 지시: "여러 매체를 검색해서 찾아와야지... 한 군데만 하면 안 되고 몇몇
매체를 검색하고 거기에서 관련된 정확한 영상을 가져와야 하는 거야".

Sources:
- YouTube Data API v3 (search_youtube.py) — uses .env YOUTUBE_API_KEY
- Wikimedia Commons REST (search_wikimedia.py) — no key, PD/CC-BY only
- Web HTML scrape (search_web.py) — stub for now, future work

Each candidate dict carries ``license_flag ∈
{"public-domain", "cc-by", "fair-use-educational", "unknown"}``.

Download (download.py) dispatches to yt-dlp (YouTube) or requests (direct
URL). Rank (rank_relevance.py) scores candidates against section
visual_directing via keyword overlap.

Prototype scope: no retry / rate-limit / cache — single-shot use for
Ryan Waller v3 + future episodes as MVP.
"""
from .search_youtube import search_youtube  # noqa: F401
from .search_wikimedia import search_wikimedia  # noqa: F401
from .rank_relevance import rank_candidates  # noqa: F401
from .download import download_candidate  # noqa: F401

__all__ = [
    "search_youtube",
    "search_wikimedia",
    "rank_candidates",
    "download_candidate",
]
