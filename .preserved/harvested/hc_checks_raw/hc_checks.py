"""Automated HC-1~7 + HC-12 checks for the hardcoded critical verification layer.

Source of truth: CLAUDE.md §하드코딩 치명적 검증 — the orchestrator MUST NOT
declare a video "complete" without all seven of these passing.

Each check parses canonical artifacts under `output/{slug}/` and returns an
`HCResult` with structured evidence so QA logs can be audited after the fact.

HC-12 (text-screenshot detection) is per-image and called separately from
`run_all_hc_checks`, which covers HC-1~7 only. See D-41-04: OpenCV primary,
pytesseract optional 2nd-pass boundary override.
"""
from __future__ import annotations

import hashlib
import json
import logging
import re
import subprocess
from collections import Counter
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Literal

try:  # D-41-04 graceful degrade
    import cv2  # type: ignore
    _CV2_AVAILABLE = True
except Exception:  # pragma: no cover - exercised in environments without opencv
    cv2 = None  # type: ignore
    _CV2_AVAILABLE = False

try:
    import pytesseract  # type: ignore
    _PYTESSERACT_AVAILABLE = True
except Exception:
    pytesseract = None  # type: ignore
    _PYTESSERACT_AVAILABLE = False

logger = logging.getLogger(__name__)

_PUNCT_RE = re.compile(r"[,\.!\?\"'…「」『』\(\)·:;~\[\]<>／/]+")
_WHITESPACE_RE = re.compile(r"\s+")
_GATE_ID_RE = re.compile(r"^GATE-[1-5]$")

_COVERAGE_THRESHOLD = 0.95
_TITLE_LINE1_MAX = 12
_TITLE_LINE2_MAX = 10
_NARRATION_CHARS_PER_SECOND = 8.5
_NARRATION_DELTA_MAX_S = 10.0
_UNIQUE_IMAGES_MIN = 6
_TEXT_RATIO_THRESHOLD = 0.30
_TEXT_RATIO_BOUNDARY_LOW = 0.20
_TEXT_RATIO_BOUNDARY_HIGH = 0.40
_OCR_CHAR_OVERRIDE = 50


@dataclass
class HCResult:
    """Result of a single HC-* check.

    Attributes:
        hc_id: "HC-1" .. "HC-7" or "HC-12".
        verdict: PASS / FAIL / SKIP.
        detail: Human-readable explanation.
        evidence: Measured values (coverage_pct, line1_len, unique_count, ...).
    """

    hc_id: str
    verdict: Literal["PASS", "FAIL", "SKIP"]
    detail: str
    evidence: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# ---------- helpers ----------


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _tokenize(text: str) -> list[str]:
    text = text.lower()
    text = _PUNCT_RE.sub(" ", text)
    return [t for t in _WHITESPACE_RE.split(text) if t]


def _script_narration(script: dict) -> str:
    sections = script.get("sections")
    if isinstance(sections, list) and sections:
        parts: list[str] = []
        for sec in sections:
            if isinstance(sec, dict) and isinstance(sec.get("narration"), str):
                parts.append(sec["narration"])
        if parts:
            return " ".join(parts)
    # legacy fallback
    legacy = script.get("narration")
    if isinstance(legacy, str):
        return legacy
    return ""


def _subtitle_tokens(subs: Any) -> list[str]:
    tokens: list[str] = []
    if isinstance(subs, list):
        for cue in subs:
            if not isinstance(cue, dict):
                continue
            words = cue.get("words")
            if isinstance(words, list):
                for w in words:
                    if isinstance(w, str):
                        tokens.extend(_tokenize(w))
                    elif isinstance(w, dict) and isinstance(w.get("word"), str):
                        tokens.extend(_tokenize(w["word"]))
            elif isinstance(cue.get("text"), str):
                tokens.extend(_tokenize(cue["text"]))
    return tokens


# ---------- HC-1 ----------


def check_hc_1(output_dir: Path) -> HCResult:
    """Subtitle coverage ≥ 95% of script narration tokens."""
    sub_path = output_dir / "subtitles_remotion.json"
    script_path = output_dir / "script.json"
    if not sub_path.exists():
        return HCResult("HC-1", "FAIL", f"missing {sub_path.name}", {})
    if not script_path.exists():
        return HCResult("HC-1", "FAIL", f"missing {script_path.name}", {})

    try:
        subs = _load_json(sub_path)
        script = _load_json(script_path)
    except (OSError, json.JSONDecodeError) as exc:
        return HCResult("HC-1", "FAIL", f"parse error: {exc}", {})

    script_tokens = _tokenize(_script_narration(script))
    if not script_tokens:
        return HCResult("HC-1", "FAIL", "script narration empty", {"script_token_count": 0})
    sub_tokens = _subtitle_tokens(subs)

    # Multiset match: each subtitle occurrence consumes one script occurrence.
    sub_counter = Counter(sub_tokens)
    matched = 0
    missing: list[str] = []
    for tok in script_tokens:
        if sub_counter.get(tok, 0) > 0:
            sub_counter[tok] -= 1
            matched += 1
        else:
            missing.append(tok)

    coverage_pct = matched / len(script_tokens)
    verdict: Literal["PASS", "FAIL", "SKIP"] = (
        "PASS" if coverage_pct >= _COVERAGE_THRESHOLD else "FAIL"
    )
    return HCResult(
        "HC-1",
        verdict,
        f"coverage={coverage_pct:.3f} (threshold={_COVERAGE_THRESHOLD})",
        {
            "coverage_pct": round(coverage_pct, 4),
            "script_token_count": len(script_tokens),
            "matched_count": matched,
            "missing_samples": missing[:10],
        },
    )


# ---------- HC-2 ----------


def check_hc_2(output_dir: Path) -> HCResult:
    """Title line1 ≤ 12자, line2 ≤ 10자."""
    script_path = output_dir / "script.json"
    if not script_path.exists():
        return HCResult("HC-2", "FAIL", "missing script.json", {})

    try:
        script = _load_json(script_path)
    except (OSError, json.JSONDecodeError) as exc:
        return HCResult("HC-2", "FAIL", f"parse error: {exc}", {})

    title = script.get("title")
    if isinstance(title, str):
        return HCResult(
            "HC-2",
            "SKIP",
            "legacy flat title format (no line1/line2 split)",
            {"title": title},
        )
    if not isinstance(title, dict):
        return HCResult("HC-2", "FAIL", "title field missing or wrong type", {})

    line1 = str(title.get("line1", ""))
    line2 = str(title.get("line2", ""))
    line1_len = len(line1)
    line2_len = len(line2)
    ok = line1_len <= _TITLE_LINE1_MAX and line2_len <= _TITLE_LINE2_MAX
    return HCResult(
        "HC-2",
        "PASS" if ok else "FAIL",
        f"line1={line1_len}/{_TITLE_LINE1_MAX} line2={line2_len}/{_TITLE_LINE2_MAX}",
        {
            "line1": line1,
            "line2": line2,
            "line1_len": line1_len,
            "line2_len": line2_len,
        },
    )


# ---------- HC-3 ----------


def _ffprobe_duration(path: Path) -> float:
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(path),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    stdout = getattr(result, "stdout", "") or ""
    return float(stdout.strip())


def check_hc_3(output_dir: Path) -> HCResult:
    """narration.mp3 duration ≈ total chars / 8.5 within ±10s."""
    narration = output_dir / "narration.mp3"
    script_path = output_dir / "script.json"
    if not narration.exists():
        return HCResult("HC-3", "FAIL", "missing narration.mp3", {})
    if not script_path.exists():
        return HCResult("HC-3", "FAIL", "missing script.json", {})

    try:
        script = _load_json(script_path)
    except (OSError, json.JSONDecodeError) as exc:
        return HCResult("HC-3", "FAIL", f"script parse error: {exc}", {})

    text = _script_narration(script)
    char_count = len(text)
    if char_count == 0:
        return HCResult("HC-3", "FAIL", "script narration empty", {"char_count": 0})

    try:
        actual = _ffprobe_duration(narration)
    except FileNotFoundError:
        return HCResult("HC-3", "FAIL", "ffprobe not on PATH", {"char_count": char_count})
    except (ValueError, subprocess.SubprocessError) as exc:
        return HCResult("HC-3", "FAIL", f"ffprobe failed: {exc}", {"char_count": char_count})

    expected = char_count / _NARRATION_CHARS_PER_SECOND
    delta = actual - expected
    ok = abs(delta) <= _NARRATION_DELTA_MAX_S
    return HCResult(
        "HC-3",
        "PASS" if ok else "FAIL",
        f"actual={actual:.1f}s expected={expected:.1f}s delta={delta:+.1f}s (tol=±{_NARRATION_DELTA_MAX_S})",
        {
            "actual_duration": round(actual, 3),
            "expected_duration": round(expected, 3),
            "char_count": char_count,
            "delta": round(delta, 3),
        },
    )


# ---------- HC-4 ----------


_BANNED_GATE_VERDICTS = {
    "auto-approved",
    "auto_approved",
    "autoapproved",
    "deferred",
    "skip",
    "skipped",
    "pending",
    "na",
    "n/a",
    "tbd",
    "todo",
}


def check_hc_4(output_dir: Path) -> HCResult:
    """gates.json must contain one entry per GATE-1..GATE-5 with a final verdict.

    Two-part check (D-72-01 R2 extension):

    Part 1 — Coverage: gates.json list must include at least one entry whose
    ``gate_id`` matches each of GATE-1, GATE-2, GATE-3, GATE-4, GATE-5.

    Part 2 — Verdict sanity (R2 guard): every final-attempt gate entry must
    carry ``verdict`` == "PASS" or "FAIL". Strings like "Auto-approved" /
    "deferred" / "SKIP" / "pending" are banned because that is exactly the
    pattern Phase 47 47-E2E-RESULTS.md used to paper over unrun E2E (see
    c-inspector-wiring.md plan §R2).

    SKIP is allowed as an inspector-level verdict inside ``inspector_results``
    but NEVER as the top-level gate verdict.
    """
    gates_path = output_dir / "gates.json"
    if not gates_path.exists():
        return HCResult("HC-4", "FAIL", "gates.json missing", {})

    try:
        gates = _load_json(gates_path)
    except (OSError, json.JSONDecodeError) as exc:
        return HCResult("HC-4", "FAIL", f"parse error: {exc}", {})

    if not isinstance(gates, list):
        return HCResult("HC-4", "FAIL", "gates.json is not a list", {})

    found: set[str] = set()
    banned: list[dict[str, str]] = []
    for entry in gates:
        if not isinstance(entry, dict):
            continue
        gid = entry.get("gate_id")
        if isinstance(gid, str) and _GATE_ID_RE.match(gid):
            found.add(gid)
        verdict_str = entry.get("verdict", "")
        if isinstance(verdict_str, str):
            if verdict_str.lower().strip() in _BANNED_GATE_VERDICTS:
                banned.append(
                    {"gate_id": gid or "?", "verdict": verdict_str}
                )

    expected = {f"GATE-{i}" for i in range(1, 6)}
    missing = expected - found

    problems: list[str] = []
    if missing:
        problems.append(f"missing_gates={sorted(missing)}")
    if banned:
        problems.append(f"banned_verdicts={banned}")

    verdict: Literal["PASS", "FAIL", "SKIP"] = "PASS" if not problems else "FAIL"
    detail = (
        f"gates_found={sorted(found)} "
        f"missing={sorted(missing)} "
        f"banned_verdicts={len(banned)}"
    )
    return HCResult(
        "HC-4",
        verdict,
        detail,
        {
            "gates_found": sorted(found),
            "missing": sorted(missing),
            "banned_verdict_entries": banned,
            "rule": "D-72-01 R2 (no Auto-approved/deferred at gate level)",
        },
    )


# ---------- HC-5 ----------


def check_hc_5(output_dir: Path) -> HCResult:
    """orchestrator_actions.log has 0 VIOLATION lines (or file missing)."""
    log = output_dir / "orchestrator_actions.log"
    if not log.exists():
        return HCResult(
            "HC-5",
            "PASS",
            "no log (guard never triggered)",
            {"violations": 0},
        )

    try:
        content = log.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        return HCResult("HC-5", "FAIL", f"log unreadable: {exc}", {})

    violation_lines = [ln for ln in content.splitlines() if ln.startswith("VIOLATION:")]
    count = len(violation_lines)
    verdict: Literal["PASS", "FAIL", "SKIP"] = "PASS" if count == 0 else "FAIL"
    return HCResult(
        "HC-5",
        verdict,
        f"violations={count}",
        {"violations": count, "samples": violation_lines[:5]},
    )


# ---------- HC-6 ----------


def _scene_clip_entries(manifest: Any) -> list[dict]:
    """Flatten scene-manifest.json into a list of per-clip dicts.

    Supports:
      - {"scenes": [{"image": ..., "hash": ...}]}
      - {"scenes": [{"clips": [{"file_path": ...}]}]}  (real shape)
      - {"clips": [{"source": ..., "hash": ...}]}       (legacy)
    """
    entries: list[dict] = []
    if isinstance(manifest, dict):
        scenes = manifest.get("scenes")
        if isinstance(scenes, list):
            for sc in scenes:
                if not isinstance(sc, dict):
                    continue
                if "hash" in sc or "image" in sc:
                    entries.append(sc)
                clips = sc.get("clips")
                if isinstance(clips, list):
                    for cl in clips:
                        if isinstance(cl, dict):
                            entries.append(cl)
        clips_legacy = manifest.get("clips")
        if isinstance(clips_legacy, list):
            for cl in clips_legacy:
                if isinstance(cl, dict):
                    entries.append(cl)
    return entries


def _entry_hash(entry: dict, output_dir: Path) -> str | None:
    """Return hash for one manifest entry (explicit field or computed from file bytes)."""
    for key in ("hash", "sha1", "sha256"):
        v = entry.get(key)
        if isinstance(v, str) and v:
            return v
    for key in ("image", "file_path", "source", "path"):
        v = entry.get(key)
        if isinstance(v, str) and v:
            p = output_dir / v if not Path(v).is_absolute() else Path(v)
            try:
                if p.exists():
                    return "sha1:" + hashlib.sha1(p.read_bytes()).hexdigest()
                return "path:" + v  # stable pseudo-hash when file missing
            except OSError:
                return "path:" + v
    return None


_SIGNATURE_FILENAME_TOKENS = (
    "signature",
    "intro",
    "outro",
    "_shared",
    "character_",  # channel-wide detective / assistant illustrations are
                   # intentionally shared across slugs (see video-sourcer
                   # AGENT.md "기존 시그니처 재사용" section).
)
_LANGUAGE_SLUG_SUFFIXES = ("-jp", "-kr", "-en", "-ja", "-ko", "-cn", "-zh")


def _is_language_variant(slug_a: str, slug_b: str) -> bool:
    """Return True when slug_a and slug_b are same-event different-language.

    Example: ``shipman-dr-death`` and ``shipman-dr-death-jp`` are the Korean
    and Japanese versions of the same incident story. They legitimately reuse
    the same evidence / crime-scene / perpetrator assets — this is NOT
    contamination.

    Detection: one slug is the other with a language suffix, OR both have
    language suffixes and the stems match.
    """
    if slug_a == slug_b:
        return False
    # slug_b = slug_a + suffix
    for suf in _LANGUAGE_SLUG_SUFFIXES:
        if slug_b == slug_a + suf or slug_a == slug_b + suf:
            return True
    # both have suffixes with matching stem
    stems: dict[str, str] = {}
    for slug in (slug_a, slug_b):
        for suf in _LANGUAGE_SLUG_SUFFIXES:
            if slug.endswith(suf):
                stems[slug] = slug[: -len(suf)]
                break
    if len(stems) == 2 and len(set(stems.values())) == 1:
        return True
    return False


def check_hc_6_5_cross_slug(output_dir: Path) -> HCResult:
    """Sources in this slug must not share md5 with other slugs (Phase 50-E).

    Session 75 failure: dyatlov-pass/sources/ contained character_detective.png
    and character_assistant.png with md5 completely identical to
    shipman-dr-death/sources/. Video-sourcer was copying from a previous slug's
    folder. HC-6.5 detects this cross-contamination.

    Exceptions: files whose name contains ``signature``, ``intro``, ``outro``,
    or ``_shared`` are allowed to share md5 across slugs (channel signatures
    are intentionally reused per video-sourcer AGENT.md).

    FAIL if any non-signature file in ``output_dir/sources`` has the same md5
    as a file in any sibling ``output/<other_slug>/sources/``.
    """
    sources_dir = output_dir / "sources"
    if not sources_dir.is_dir():
        return HCResult("HC-6.5", "SKIP", "sources/ missing (pre-sourcing step)", {})

    current_slug = output_dir.name
    output_root = output_dir.parent

    def _md5(p: Path) -> str | None:
        try:
            return hashlib.md5(p.read_bytes()).hexdigest()
        except OSError:
            return None

    def _is_signature(name: str) -> bool:
        n = name.lower()
        return any(tok in n for tok in _SIGNATURE_FILENAME_TOKENS)

    # Current slug: md5 -> filename
    current_hashes: dict[str, str] = {}
    for p in sources_dir.iterdir():
        if not p.is_file() or _is_signature(p.name):
            continue
        h = _md5(p)
        if h is not None:
            current_hashes[h] = p.name

    if not current_hashes:
        return HCResult("HC-6.5", "PASS", "no non-signature files to check", {})

    # Sibling slugs: md5 -> (slug, filename). Skip language variants of the
    # current slug (same event, different language) — they legitimately share
    # the same evidence assets.
    other_hashes: dict[str, tuple[str, str]] = {}
    for sibling in output_root.iterdir():
        if not sibling.is_dir() or sibling.name == current_slug:
            continue
        if sibling.name.startswith("_") or sibling.name.startswith("."):
            continue  # skip output/_shared, _research, etc.
        if _is_language_variant(current_slug, sibling.name):
            continue
        sib_sources = sibling / "sources"
        if not sib_sources.is_dir():
            continue
        for p in sib_sources.iterdir():
            if not p.is_file() or _is_signature(p.name):
                continue
            h = _md5(p)
            if h is not None and h not in other_hashes:
                other_hashes[h] = (sibling.name, p.name)

    collisions: list[dict[str, str]] = []
    for h, fname in current_hashes.items():
        if h in other_hashes:
            other_slug, other_name = other_hashes[h]
            collisions.append(
                {
                    "md5": h,
                    "current": fname,
                    "other_slug": other_slug,
                    "other_name": other_name,
                }
            )

    verdict: Literal["PASS", "FAIL", "SKIP"] = "PASS" if not collisions else "FAIL"
    msg = (
        f"cross-slug contamination: {len(collisions)} files"
        if collisions
        else f"checked {len(current_hashes)} non-signature files, no collisions"
    )
    return HCResult(
        "HC-6.5",
        verdict,
        msg,
        {
            "checked_count": len(current_hashes),
            "collision_count": len(collisions),
            "collisions": collisions[:10],
            "rule": "Phase 50-E (no cross-slug md5 match except signature files)",
        },
    )


def check_hc_6(output_dir: Path) -> HCResult:
    """scene-manifest.json must contain ≥ 6 unique source hashes."""
    manifest_path = output_dir / "scene-manifest.json"
    if not manifest_path.exists():
        return HCResult("HC-6", "FAIL", "scene-manifest.json missing", {})

    try:
        manifest = _load_json(manifest_path)
    except (OSError, json.JSONDecodeError) as exc:
        return HCResult("HC-6", "FAIL", f"parse error: {exc}", {})

    entries = _scene_clip_entries(manifest)
    hashes: list[str] = []
    for e in entries:
        h = _entry_hash(e, output_dir)
        if h is not None:
            hashes.append(h)

    counter = Counter(hashes)
    unique_count = len(counter)
    duplicate_hashes = [h for h, c in counter.items() if c > 1]
    verdict: Literal["PASS", "FAIL", "SKIP"] = (
        "PASS" if unique_count >= _UNIQUE_IMAGES_MIN else "FAIL"
    )
    return HCResult(
        "HC-6",
        verdict,
        f"unique={unique_count} total={len(hashes)} min={_UNIQUE_IMAGES_MIN}",
        {
            "unique_count": unique_count,
            "total_scenes": len(hashes),
            "duplicate_hashes": duplicate_hashes,
        },
    )


# ---------- HC-7 ----------


_WATSON_TOKENS = ("watson", "조수", "왓슨")
_DETECTIVE_TOKENS = ("detective", "탐정", "홍", "셜록", "sherlock")


def _role_contains(role: str, needles: tuple[str, ...]) -> bool:
    r = role.lower()
    return any(n.lower() in r for n in needles)


def check_hc_7(output_dir: Path) -> HCResult:
    """Every Watson section must be followed by a detective response."""
    script_path = output_dir / "script.json"
    if not script_path.exists():
        return HCResult("HC-7", "FAIL", "missing script.json", {})

    try:
        script = _load_json(script_path)
    except (OSError, json.JSONDecodeError) as exc:
        return HCResult("HC-7", "FAIL", f"parse error: {exc}", {})

    sections = script.get("sections")
    if not isinstance(sections, list) or not sections:
        return HCResult("HC-7", "SKIP", "no sections array (not duo format)", {})

    has_role = any(isinstance(s, dict) and isinstance(s.get("role"), str) for s in sections)
    if not has_role:
        return HCResult("HC-7", "SKIP", "no role field on sections (not duo format)", {})

    watson_count = 0
    unanswered: list[int] = []
    for i, sec in enumerate(sections):
        if not isinstance(sec, dict):
            continue
        role = sec.get("role") or ""
        if not isinstance(role, str):
            continue
        if _role_contains(role, _WATSON_TOKENS):
            watson_count += 1
            nxt = sections[i + 1] if i + 1 < len(sections) else None
            next_role = nxt.get("role") if isinstance(nxt, dict) else None
            if not (isinstance(next_role, str) and _role_contains(next_role, _DETECTIVE_TOKENS)):
                unanswered.append(i)

    verdict: Literal["PASS", "FAIL", "SKIP"] = "PASS" if not unanswered else "FAIL"
    return HCResult(
        "HC-7",
        verdict,
        f"watson_count={watson_count} unanswered={len(unanswered)}",
        {"watson_count": watson_count, "unanswered_indices": unanswered},
    )


# ---------- HC-12 ----------


def check_hc_12_text_screenshot(image_path: Path) -> HCResult:
    """Detect if an image is text-heavy (screenshot of document/paragraph).

    Primary: OpenCV Canny + findContours glyph-like rectangle area ratio.
    Secondary (optional): pytesseract OCR in the boundary band 0.20-0.40 ratio.
    """
    image_path = Path(image_path)
    if not _CV2_AVAILABLE:
        return HCResult(
            "HC-12",
            "SKIP",
            "cv2 not installed (install opencv-python)",
            {"image": str(image_path)},
        )
    if not image_path.exists():
        return HCResult("HC-12", "FAIL", f"image missing: {image_path}", {})

    img = cv2.imread(str(image_path))
    if img is None:
        return HCResult("HC-12", "FAIL", "image unreadable (cv2 returned None)", {})

    h, w = img.shape[:2]
    total_area = float(h * w) if h and w else 1.0
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 100, 200)
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    glyph_area = 0.0
    glyph_count = 0
    for cnt in contours:
        x, y, cw, ch = cv2.boundingRect(cnt)
        if ch <= 0 or cw <= 0:
            continue
        aspect = cw / float(ch)
        if 0.1 < aspect < 10.0 and 5 < ch < 80:
            glyph_area += cw * ch
            glyph_count += 1

    ratio = glyph_area / total_area
    used_ocr = False
    override = False
    if _TEXT_RATIO_BOUNDARY_LOW <= ratio <= _TEXT_RATIO_BOUNDARY_HIGH and _PYTESSERACT_AVAILABLE:
        try:
            text = pytesseract.image_to_string(img)  # type: ignore[arg-type]
            used_ocr = True
            non_ws = sum(1 for c in text if not c.isspace())
            if non_ws > _OCR_CHAR_OVERRIDE:
                override = True
        except Exception as exc:  # pragma: no cover - OCR optional
            logger.warning("pytesseract failed: %s", exc)

    fail_primary = ratio > _TEXT_RATIO_THRESHOLD
    verdict: Literal["PASS", "FAIL", "SKIP"] = "FAIL" if (fail_primary or override) else "PASS"
    return HCResult(
        "HC-12",
        verdict,
        f"text_area_ratio={ratio:.3f} threshold={_TEXT_RATIO_THRESHOLD} ocr_override={override}",
        {
            "text_area_ratio": round(ratio, 4),
            "contour_count": glyph_count,
            "used_ocr": used_ocr,
            "image": str(image_path),
        },
    )


# ---------- HC-13: compliance_result.json (product_review only) ----------

_URL_RE = re.compile(
    r"https?://[^\s\"'<>\)]+",
    re.IGNORECASE,
)


def _detect_channel(output_dir: Path) -> str | None:
    """Best-effort channel detection from script.json or blueprint.json."""
    for fname in ("script.json", "blueprint.json"):
        p = output_dir / fname
        if p.exists():
            try:
                data = _load_json(p)
                ch = data.get("channel")
                if isinstance(ch, str) and ch:
                    return ch
            except (OSError, json.JSONDecodeError):
                continue
    return None


def check_hc_13_compliance(output_dir: Path) -> HCResult:
    """compliance_result.json must exist and all items PASS (product_review only).

    SKIP for non-product_review channels.
    """
    channel = _detect_channel(output_dir)
    if channel != "product_review":
        return HCResult(
            "HC-13",
            "SKIP",
            f"channel={channel!r} (product_review only)",
            {"channel": channel},
        )

    cr_path = output_dir / "compliance_result.json"
    if not cr_path.exists():
        return HCResult("HC-13", "FAIL", "compliance_result.json missing", {})

    try:
        data = _load_json(cr_path)
    except (OSError, json.JSONDecodeError) as exc:
        return HCResult("HC-13", "FAIL", f"parse error: {exc}", {})

    # Support both flat ComplianceResult and wrapped shapes
    passed = data.get("passed")
    checks = data.get("checks", [])
    failed_checks = [c for c in checks if isinstance(c, dict) and not c.get("passed", True)]

    if passed is True and not failed_checks:
        return HCResult(
            "HC-13",
            "PASS",
            f"all {len(checks)} compliance checks passed",
            {"check_count": len(checks), "score": data.get("score")},
        )

    return HCResult(
        "HC-13",
        "FAIL",
        f"compliance failed: {len(failed_checks)} checks not passed",
        {
            "passed": passed,
            "failed_checks": failed_checks[:5],
            "score": data.get("score"),
        },
    )


# ---------- HC-14: no direct URL in CTA (product_review only) ----------


def check_hc_14_no_direct_link(output_dir: Path) -> HCResult:
    """script.json CTA section must NOT contain direct URLs (product_review only).

    SKIP for non-product_review channels.
    """
    channel = _detect_channel(output_dir)
    if channel != "product_review":
        return HCResult(
            "HC-14",
            "SKIP",
            f"channel={channel!r} (product_review only)",
            {"channel": channel},
        )

    script_path = output_dir / "script.json"
    if not script_path.exists():
        return HCResult("HC-14", "FAIL", "script.json missing", {})

    try:
        script = _load_json(script_path)
    except (OSError, json.JSONDecodeError) as exc:
        return HCResult("HC-14", "FAIL", f"parse error: {exc}", {})

    sections = script.get("sections", [])
    cta_urls: list[dict[str, str]] = []

    for sec in sections:
        if not isinstance(sec, dict):
            continue
        sec_type = sec.get("type", "") or sec.get("role", "")
        if not isinstance(sec_type, str):
            continue
        if sec_type.lower() not in ("cta", "summary"):
            continue
        narration = sec.get("narration", "")
        if not isinstance(narration, str):
            continue
        found = _URL_RE.findall(narration)
        for url in found:
            cta_urls.append({"section_type": sec_type, "url": url})

    if cta_urls:
        return HCResult(
            "HC-14",
            "FAIL",
            f"{len(cta_urls)} direct URL(s) found in CTA",
            {"urls_found": cta_urls},
        )

    return HCResult(
        "HC-14",
        "PASS",
        "no direct URLs in CTA sections",
        {"cta_sections_checked": sum(
            1 for s in sections
            if isinstance(s, dict) and (s.get("type", "") or s.get("role", "")).lower() in ("cta", "summary")
        )},
    )


# ---------- aggregator ----------


def check_hc_8_diagnostic_five(output_dir: Path) -> HCResult:
    """HC-8 — Phase 50-03 대표님 진단 5질문 (D-50-16, Plan 50-03 3e).

    Skeleton: production implementation dispatches a sonnet LLM judge with
    the fixed 5-question prompt and returns FAIL if 2+ NO.

    Q1: 시작 1초 스크롤 멈춤 문장?
    Q2: 10초 안 오해/갈등/반전?
    Q3: 숫자·비교·사례 1개+?
    Q4: 컷마다 화면 상상 가능?
    Q5: 마지막에 다음 편 궁금?

    Current surface: SKIP when LLM judge not wired. Real impl will mirror the
    Phase 47 CI-10 3-sample median pattern.
    """
    script_path = Path(output_dir) / "script.json"
    if not script_path.exists():
        return HCResult(
            "HC-8", "SKIP",
            "script.json not present — run step_3_script_nlm first",
            {},
        )
    # Phase 50-03 Wave 3e will wire the LLM judge here. Until then, this check
    # cooperates with the ins-fun inspector at GATE 2 which already covers the
    # same 5-axis prompt territory.
    return HCResult(
        "HC-8", "SKIP",
        "HC-8 diagnostic-five LLM judge not yet wired (Plan 50-03 Wave 3e)",
        {"plan": "50-03", "wave": "3e", "mirrors": "ins-fun GATE 2"},
    )


def check_hc_9_pipeline_order(output_dir: Path) -> HCResult:
    """HC-9 — Phase 50-03 Artifact chain integrity (D-50-15).

    Verifies nlm_meta.json → script_converted.json → script.json hash chain
    and mtime monotonicity. Mirrors ins-meta-chain inspector's checks but
    runs at QA time (post-pipeline) as a defense-in-depth layer.
    """
    output_dir = Path(output_dir)
    required = [
        "nlm_meta.json",
        "raw_script.md",
        "script_converted.json",
        "script.json",
    ]
    missing = [f for f in required if not (output_dir / f).exists()]
    if missing:
        # If this slug used the Phase 47 scripter path, HC-9 is N/A
        if not (output_dir / "nlm_meta.json").exists():
            return HCResult(
                "HC-9", "SKIP",
                "NLM pipeline artifacts absent — slug used Phase 47 scripter path",
                {"missing": missing},
            )
        return HCResult(
            "HC-9", "FAIL",
            f"artifact chain incomplete: {missing}",
            {"missing": missing, "rule": "D-50-15"},
        )

    # Hash verification
    raw_script_hash = hashlib.sha256(
        (output_dir / "raw_script.md").read_bytes()
    ).hexdigest()
    converted_hash = hashlib.sha256(
        (output_dir / "script_converted.json").read_bytes()
    ).hexdigest()

    try:
        nlm_meta = json.loads(
            (output_dir / "nlm_meta.json").read_text(encoding="utf-8")
        )
        script_converted = json.loads(
            (output_dir / "script_converted.json").read_text(encoding="utf-8")
        )
        script = json.loads(
            (output_dir / "script.json").read_text(encoding="utf-8")
        )
    except json.JSONDecodeError as e:
        return HCResult(
            "HC-9", "FAIL", f"JSON decode error: {e}", {},
        )

    mismatches: list[str] = []
    if nlm_meta.get("raw_script_hash") != raw_script_hash:
        mismatches.append(
            f"nlm_meta.raw_script_hash mismatch: got "
            f"{(nlm_meta.get('raw_script_hash') or '')[:8]}, "
            f"expected {raw_script_hash[:8]}"
        )
    if script_converted.get("nlm_source_hash") != raw_script_hash:
        mismatches.append(
            f"script_converted.nlm_source_hash mismatch vs raw_script.md"
        )
    if script.get("converted_hash") != converted_hash:
        mismatches.append(
            f"script.converted_hash mismatch vs script_converted.json"
        )

    # mtime monotonicity
    mtimes = {
        name: (output_dir / name).stat().st_mtime for name in required
    }
    monotonic_order = [
        mtimes["nlm_meta.json"] <= mtimes["script_converted.json"],
        mtimes["script_converted.json"] <= mtimes["script.json"],
    ]
    if not all(monotonic_order):
        mismatches.append(
            f"mtime not monotonic: {mtimes}"
        )

    if mismatches:
        return HCResult(
            "HC-9", "FAIL",
            f"artifact chain integrity violations: {len(mismatches)}",
            {"mismatches": mismatches, "rule": "D-50-15"},
        )
    return HCResult(
        "HC-9", "PASS",
        "artifact chain hashes + mtimes consistent",
        {"raw_script_hash": raw_script_hash[:8],
         "converted_hash": converted_hash[:8]},
    )


def check_hc_10_inspector_coverage(output_dir: Path) -> HCResult:
    """HC-10 — Phase 50-03 Inspector army coverage (D-50-17).

    Verifies that all inspectors registered in GATE_INSPECTORS produced a
    result artifact during GATE 2 execution. Prevents silent skip of newly-
    added Phase 50 Script Gate inspectors (hook-strength / rhythm / fun etc.).

    Skeleton: looks for gate_results/ directory populated by harness during
    production runs. SKIPs if gate_results/ absent (pre-integration test).
    """
    output_dir = Path(output_dir)
    gate_results = output_dir / "gate_results"
    if not gate_results.exists():
        return HCResult(
            "HC-10", "SKIP",
            "gate_results/ absent — harness integration pending",
            {"plan": "50-03", "wave": "3d"},
        )

    # Import lazily to avoid circular dependency during module load
    from scripts.orchestrator.harness import GATE_INSPECTORS

    expected_script = set(GATE_INSPECTORS.get("script", []))
    executed = {
        p.stem for p in gate_results.glob("*.json")
    }
    missing = expected_script - executed
    if missing:
        return HCResult(
            "HC-10", "FAIL",
            f"{len(missing)} script inspectors did not run: {sorted(missing)}",
            {"expected": sorted(expected_script),
             "executed": sorted(executed),
             "missing": sorted(missing),
             "rule": "D-50-17"},
        )
    return HCResult(
        "HC-10", "PASS",
        f"all {len(expected_script)} script inspectors executed",
        {"count": len(expected_script)},
    )


_HC_FUNCS: list[tuple[str, Any]] = [
    ("HC-1", check_hc_1),
    ("HC-2", check_hc_2),
    ("HC-3", check_hc_3),
    ("HC-4", check_hc_4),
    ("HC-5", check_hc_5),
    ("HC-6", check_hc_6),
    ("HC-6.5", check_hc_6_5_cross_slug),
    ("HC-7", check_hc_7),
    # Phase 50-03 additions (D-50-17)
    ("HC-8", check_hc_8_diagnostic_five),
    ("HC-9", check_hc_9_pipeline_order),
    ("HC-10", check_hc_10_inspector_coverage),
]

# product_review-only checks — gated by channel in the check itself
_HC_PRODUCT_REVIEW_FUNCS: list[tuple[str, Any]] = [
    ("HC-13", check_hc_13_compliance),
    ("HC-14", check_hc_14_no_direct_link),
]


def run_all_hc_checks(output_dir: Path) -> list[HCResult]:
    """Run HC-1 through HC-7 + HC-13/14 and persist results to hc_checks.json.

    HC-13 and HC-14 are product_review-only: they SKIP for other channels.
    HC-12 is per-image and NOT executed here; it is called separately for each
    scene image by qa_checklist.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    results: list[HCResult] = []

    all_funcs = _HC_FUNCS + _HC_PRODUCT_REVIEW_FUNCS

    for hc_id, fn in all_funcs:
        try:
            results.append(fn(output_dir))
        except Exception as exc:  # defensive: per-check exception → FAIL HCResult
            logger.exception("%s raised; converting to FAIL", hc_id)
            results.append(
                HCResult(hc_id, "FAIL", f"unhandled exception: {exc}", {"exception": repr(exc)})
            )

    sink = output_dir / "hc_checks.json"
    try:
        sink.write_text(
            json.dumps([r.to_dict() for r in results], ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    except OSError as exc:
        logger.warning("failed to write hc_checks.json: %s", exc)
    return results


__all__ = [
    "HCResult",
    "check_hc_1",
    "check_hc_2",
    "check_hc_3",
    "check_hc_4",
    "check_hc_5",
    "check_hc_6",
    "check_hc_6_5_cross_slug",
    "check_hc_7",
    "check_hc_12_text_screenshot",
    "check_hc_13_compliance",
    "check_hc_14_no_direct_link",
    "run_all_hc_checks",
]
