"""Ryan Waller v5 Pexels fallback — fills Kling-failed shots with Pexels photo + Ken Burns.

INVARIANT Rule 1: reads script_v5.json first.
Context: Producer v5 Phase 2 Kling T2I returned HTTP 429 "balance not enough".
This fallback uses Pexels free stock photos + ffmpeg Ken Burns zoom for the 12
shots that had visual_mode=kling_t2i_i2v but no shot_final/.

INVARIANT Rule 2: Pexels query = shot.situation_markers[0].maps_to (first situation
marker english). Query built at runtime from script, not hardcoded.
"""
from __future__ import annotations
import builtins as _b
import json
import os
import subprocess
import sys
from pathlib import Path

import requests

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)
    except AttributeError:
        pass
os.environ.setdefault("PYTHONUNBUFFERED", "1")


def _p(*a, **k):
    k.setdefault("flush", True); _b.print(*a, **k)


SCRIPT_V5 = Path("output/ryan-waller/script_v5.json")
SHOT_FINAL = Path("output/ryan-waller/sources/shot_final")
PEXELS_ANCHORS = Path("output/ryan-waller/sources/pexels_v5")
MANIFEST = Path("output/ryan-waller/producer_v5_pexels_manifest.json")


def load_dotenv() -> None:
    env = Path(".env")
    if not env.exists():
        return
    for line in env.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line: continue
        k, v = line.split("=", 1)
        k = k.strip(); v = v.strip().strip('"').strip("'")
        if k and v and k not in os.environ:
            os.environ[k] = v


def probe_duration(p: Path) -> float:
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(p)],
        capture_output=True, text=True, check=True)
    return float(r.stdout.strip())


def build_pexels_query(shot: dict) -> str:
    """v5 query = runtime from shot.situation_markers.maps_to + motion hints."""
    sits = [m.get("maps_to", "") for m in shot.get("situation_markers", []) if m.get("maps_to")]
    motions = [m.get("maps_to", "") for m in shot.get("motion_markers", []) if m.get("maps_to")]
    # use first situation marker + motion hint as query
    parts = []
    if sits:
        parts.append(sits[0])
    if motions:
        parts.append(motions[0].split(",")[0])  # first word of motion
    return " ".join(parts).replace(",", "").strip()


# Manual query overrides for better Pexels results (more pictorial)
QUERY_OVERRIDES = {
    "hook_s01_date_christmas_eve": "christmas lights house night",
    "hook_s02_phoenix_arizona": "phoenix arizona desert night",
    "hook_s04_heather_body": "dark living room night",
    "body_scene_s01_heather_victim": "candle memorial dim",
    "body_scene_s02_phoenix_shooting": "desert home night exterior",
    "body_6hours_s01_clock_six_hours": "wall clock vintage",
    "body_6hours_s03_real_killer_fleeing_phoenix": "desert highway night",
    "watson_q2_s01_flee_shock": "car night road taillights",
    "reveal_s02_doorway_ambush": "dark doorway ajar night",
    "aftermath_det_s01_brain_eye_loss": "hospital room dim bed",
    "aftermath_det_s02_lawsuit_dismissed_cta": "court legal document gavel",
    "aftermath_watson_s01_cta": "detective desk case files dim",
}


def pexels_search(query: str, per_page: int = 5) -> list[dict]:
    api_key = os.environ.get("PEXELS_API_KEY")
    if not api_key:
        raise EnvironmentError("PEXELS_API_KEY missing")
    r = requests.get(
        "https://api.pexels.com/v1/search",
        headers={"Authorization": api_key},
        params={"query": query, "per_page": per_page, "orientation": "portrait"},
        timeout=30,
    )
    if r.status_code >= 400:
        raise RuntimeError(f"Pexels HTTP {r.status_code}: {r.text[:300]}")
    return r.json().get("photos", [])


def download_photo(url: str, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    with requests.get(url, stream=True, timeout=120) as r:
        r.raise_for_status()
        with dst.open("wb") as fh:
            for c in r.iter_content(131072):
                if c: fh.write(c)


def ken_burns(src: Path, dst: Path, duration: float) -> None:
    """ffmpeg Ken Burns zoom: slow zoom in, fps 30, 1080x1920."""
    dst.parent.mkdir(parents=True, exist_ok=True)
    frames = max(30, round(duration * 30))
    # scale source large, zoompan with slow zoom
    vf = (
        "scale=2160:3840:force_original_aspect_ratio=increase,"
        "crop=2160:3840,"
        f"zoompan=z='min(1+0.0005*on,1.12)':d={frames}:"
        "x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1080x1920,"
        "fade=t=in:st=0:d=0.2"
    )
    subprocess.run([
        "ffmpeg", "-y", "-loop", "1", "-i", str(src), "-t", f"{duration:.3f}",
        "-vf", vf,
        "-c:v", "libx264", "-crf", "20", "-pix_fmt", "yuv420p", "-r", "30", "-an",
        str(dst),
    ], check=True, capture_output=True)


def main() -> int:
    load_dotenv()
    if not os.environ.get("PEXELS_API_KEY"):
        raise EnvironmentError("PEXELS_API_KEY missing from .env")

    _p("[Pexels Fallback v5] reads script_v5.json (INVARIANT Rule 1)")
    script = json.loads(SCRIPT_V5.read_text(encoding="utf-8"))

    flat_shots = []
    for sec in script["sections"]:
        for s in sec["shots"]:
            flat_shots.append(s)

    # find shots with mode=kling_t2i_i2v AND no shot_final present
    targets = []
    for shot in flat_shots:
        if shot.get("visual_mode") != "kling_t2i_i2v":
            continue
        f = SHOT_FINAL / f"{shot['shot_id']}_final.mp4"
        if not f.exists():
            targets.append(shot)
    _p(f"[Pexels Fallback v5] {len(targets)} shots missing shot_final (Kling failed)")

    PEXELS_ANCHORS.mkdir(parents=True, exist_ok=True)
    results = []
    for shot in targets:
        sid = shot["shot_id"]
        query = QUERY_OVERRIDES.get(sid) or build_pexels_query(shot)
        _p(f"  [{sid:<45s}] query='{query}'")
        photos = pexels_search(query, 5)
        if not photos:
            _p(f"    FAIL no Pexels results for '{query}'")
            results.append({"shot_id": sid, "status": "no_pexels_result", "query": query})
            continue
        # pick first photo (Pexels relevance-sorted)
        top = photos[0]
        photo_url = top["src"].get("large") or top["src"].get("original")
        anchor = PEXELS_ANCHORS / f"{sid}_pexels.jpg"
        download_photo(photo_url, anchor)
        # Ken Burns clip
        dst = SHOT_FINAL / f"{sid}_final.mp4"
        duration = shot["duration_hint_s"]
        ken_burns(anchor, dst, duration)
        actual = probe_duration(dst)
        _p(f"    OK pexels_id={top.get('id')} → {dst.name} "
           f"dur={duration}s actual={actual:.3f}s photographer={top.get('photographer')}")
        results.append({
            "shot_id": sid, "status": "pexels_ken_burns_ok",
            "query": query, "pexels_id": top.get("id"),
            "pexels_url": top.get("url"), "photographer": top.get("photographer"),
            "anchor": str(anchor), "final": str(dst),
            "duration_s": duration, "actual_s": actual,
        })
    MANIFEST.write_text(json.dumps({"results": results}, ensure_ascii=False, indent=2), encoding="utf-8")
    _p(f"\nOK Pexels fallback manifest: {MANIFEST}")
    fails = [r for r in results if r.get("status") != "pexels_ken_burns_ok"]
    return 2 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
