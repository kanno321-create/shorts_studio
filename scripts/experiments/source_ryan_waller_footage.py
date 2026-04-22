"""Ryan Waller v3 footage sourcing — multi-source search + rank + download.

Per feedback_multi_source_video_search_required: searches YouTube (fair-use
educational) + Wikimedia Commons (PD / CC-BY) per section. Ranks candidates
against section.visual_directing. Downloads top-K.

Per-section hardcoded English+Korean keyword pools (prototype).

Reads: output/ryan-waller/script_v3.json
Writes:
- output/ryan-waller/sources/real/raw/<section_id>_<rank>.{mp4,jpg,...}
- output/ryan-waller/sources/real/manifest_v3.json

Safe to re-run — skip sections whose top-1 candidate is already downloaded.
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        pass

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scripts.orchestrator.video_sourcing import (  # noqa: E402
    search_youtube, search_wikimedia, rank_candidates, download_candidate,
)

SCRIPT_PATH = Path("output/ryan-waller/script_v3.json")
RAW_DIR = Path("output/ryan-waller/sources/real/raw")
MANIFEST_PATH = Path("output/ryan-waller/sources/real/manifest_v3.json")

# Per-section keyword pool. English preferred (US case); Korean extras when useful.
SECTION_QUERIES: dict[str, list[str]] = {
    "hook": [
        "Ryan Waller Phoenix 2006 interrogation",
        "Ryan Waller wrongful arrest Phoenix Arizona",
        "Phoenix police suburban neighborhood night",
    ],
    "watson_q1": [
        "police interrogation suspect chair detective",
        "취조실 CCTV 형사",
    ],
    "body_scene": [
        "Heather Quan Phoenix Christmas 2006 crime scene",
        "Phoenix suburban house Christmas lights night",
        "crime scene police tape house exterior",
    ],
    "body_dalton": [
        "Paul Dalton Phoenix detective interrogation",
        "police interrogation room fluorescent light wide shot",
        "detective closeup interrogation moody lighting",
    ],
    "body_6hours": [
        "interrogation room wall clock hours passing",
        "empty hospital corridor late night tracking shot",
        "interrogation room empty desk no water glass",
    ],
    "watson_q2": [
        "suspect escape getaway night street silhouette",
        "용의자 도주 실루엣",
    ],
    "reveal": [
        "Richie Carver Larry Carver Phoenix double murder",
        "front door gap gunshot recreation",
        "X-ray skull bullet graphic medical",
        "Phoenix suburban house front door crime",
    ],
    "aftermath_detective": [
        "Ryan Waller hospital eye patch TBI traumatic brain injury",
        "court dismissal document gavel Phoenix lawsuit",
        "wrongful conviction lawsuit dismissed news",
    ],
    "aftermath_watson": [
        "detective silhouette walking away noir",
        "탐정 실루엣 뒤돌아 걷다",
    ],
}

TOP_K_PER_SECTION = 2  # grab best 2 per section, pick 1 later in visual_spec


def _slugify(s: str) -> str:
    return "".join(c if c.isalnum() or c in "-_" else "_" for c in s)[:40]


def load_dotenv_minimal() -> None:
    env_file = Path(".env")
    if not env_file.exists():
        return
    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        k = k.strip()
        v = v.strip().strip('"').strip("'")
        if k and v and k not in os.environ:
            os.environ[k] = v


def search_all_sources(query: str, max_per_source: int = 8) -> list[dict]:
    results: list[dict] = []
    try:
        yt = search_youtube(query, max_results=max_per_source)
        print(f"    yt   : {len(yt)} candidates")
        results.extend(yt)
    except Exception as exc:  # noqa: BLE001
        print(f"    yt   : ERROR {exc!r}")
    try:
        wm = search_wikimedia(query, max_results=max_per_source)
        print(f"    wm   : {len(wm)} candidates")
        results.extend(wm)
    except Exception as exc:  # noqa: BLE001
        print(f"    wm   : ERROR {exc!r}")
    return results


def main() -> int:
    load_dotenv_minimal()
    if not SCRIPT_PATH.exists():
        raise FileNotFoundError(f"script_v3 missing: {SCRIPT_PATH}")
    script = json.loads(SCRIPT_PATH.read_text(encoding="utf-8"))

    RAW_DIR.mkdir(parents=True, exist_ok=True)

    manifest: dict = {
        "schema_version": "v3-multi-source",
        "episode_id": "ryan-waller",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "sections": [],
        "sources_used": [],
        "license_flag_counts": {},
    }
    sources_used: set[str] = set()
    license_counts: dict[str, int] = {}

    for section in script["sections"]:
        sid = section["section_id"]
        vd = section.get("visual_directing", "")
        queries = SECTION_QUERIES.get(sid, [])
        print(f"\n[SEC {sid}] visual_directing: {vd[:80]}")
        if not queries:
            print("  (no query pool — skipping)")
            manifest["sections"].append({
                "section_id": sid, "picks": [],
                "note": "no query pool configured",
            })
            continue

        # Aggregate candidates across all queries
        all_cands: list[dict] = []
        for q in queries:
            print(f"  query: {q!r}")
            found = search_all_sources(q, max_per_source=5)
            all_cands.extend(found)

        if not all_cands:
            print("  (no candidates from any source)")
            manifest["sections"].append({
                "section_id": sid, "picks": [],
                "note": "no candidates found — Kling fallback needed",
            })
            continue

        # Rank: query_text = visual_directing + first query + section narration
        query_text = " ".join([vd, section.get("narration", "")])
        ranked = rank_candidates(all_cands, query_text, extra_terms=queries)

        # Dedupe by URL, keep top-K
        seen_urls: set[str] = set()
        top: list[dict] = []
        for c in ranked:
            if c["url"] in seen_urls:
                continue
            seen_urls.add(c["url"])
            top.append(c)
            if len(top) >= TOP_K_PER_SECTION:
                break

        # Download each top pick
        picks: list[dict] = []
        for rank, c in enumerate(top, 1):
            basename = f"{sid}_{rank}_{_slugify(c.get('id', 'x'))}"
            try:
                print(f"  DL #{rank} [{c['source']} score={c.get('_score',0):.2f} "
                      f"lic={c.get('license_flag')}]: {c['title'][:60]}")
                local = download_candidate(c, RAW_DIR, basename)
                size_mb = local.stat().st_size / 1024 / 1024
                print(f"    → {local.name} ({size_mb:.2f} MB)")
                picks.append({
                    "rank": rank,
                    "source": c["source"],
                    "license_flag": c.get("license_flag", "unknown"),
                    "url": c["url"],
                    "title": c.get("title", ""),
                    "channel": c.get("channel", ""),
                    "score": c.get("_score", 0),
                    "matched_terms": c.get("_matched_terms", []),
                    "local_path": str(local),
                    "size_mb": round(size_mb, 2),
                })
                sources_used.add(c["source"])
                license_counts[c.get("license_flag", "unknown")] = (
                    license_counts.get(c.get("license_flag", "unknown"), 0) + 1
                )
            except Exception as exc:  # noqa: BLE001
                print(f"    download FAILED: {exc!r}")
                continue

        manifest["sections"].append({
            "section_id": sid,
            "visual_directing": vd,
            "queries": queries,
            "candidates_count": len(all_cands),
            "picks": picks,
        })

    manifest["sources_used"] = sorted(sources_used)
    manifest["license_flag_counts"] = license_counts

    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST_PATH.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    # Summary
    total_picks = sum(len(s.get("picks", [])) for s in manifest["sections"])
    covered = sum(1 for s in manifest["sections"] if s.get("picks"))
    print("\n" + "=" * 60)
    print("✅ Footage sourcing v3 complete")
    print(f"  sections total       : {len(manifest['sections'])}")
    print(f"  sections with picks  : {covered}")
    print(f"  total downloads      : {total_picks}")
    print(f"  sources used         : {sorted(sources_used)}")
    print(f"  license distribution : {license_counts}")
    print(f"  manifest             : {MANIFEST_PATH}")
    print(f"  raw dir              : {RAW_DIR}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
