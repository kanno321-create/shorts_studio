"""Scene Evaluator -- deterministic scene-manifest quality checks.

Validates scene-manifest.json against scene-sprint-contract.json criteria.
All checks are deterministic (no LLM needed).

Usage:
    python scene_evaluator.py --manifest PATH [--contract PATH] [--script PATH]

Returns JSON to stdout with pass/fail + per-check results.
Exit code: 0 = pass, 1 = fail.
"""
import argparse
import json
import sys
from pathlib import Path
from collections import Counter


# Default contract path (relative to project root)
DEFAULT_CONTRACT_PATH = Path(__file__).parent.parent.parent / "config" / "scene-sprint-contract.json"


def load_contract(contract_path: str = None) -> dict:
    """Load scene-sprint-contract.json for threshold values."""
    path = Path(contract_path) if contract_path else DEFAULT_CONTRACT_PATH
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _check_min_clips(clips: list, contract: dict) -> dict:
    """Check 1: Minimum clip count."""
    criteria = contract.get("deterministic", {}).get("criteria", {})
    threshold = criteria.get("min_clips", {}).get("threshold", 5)
    count = len(clips)
    passed = count >= threshold
    return {
        "name": "min_clips",
        "passed": passed,
        "detail": f"Clip count: {count} (threshold: >= {threshold})",
    }


def _check_avg_clip_duration(clips: list, contract: dict) -> dict:
    """Check 2: Average clip duration within 2.0-3.0s range."""
    criteria = contract.get("deterministic", {}).get("criteria", {})
    dur_cfg = criteria.get("avg_clip_duration", {})
    min_dur = dur_cfg.get("min", 2.0)
    max_dur = dur_cfg.get("max", 3.0)

    if not clips:
        return {
            "name": "avg_clip_duration",
            "passed": False,
            "detail": "No clips to evaluate",
        }

    total_duration = sum(clip.get("duration", 0) for clip in clips)
    avg_duration = total_duration / len(clips)
    passed = min_dur <= avg_duration <= max_dur
    return {
        "name": "avg_clip_duration",
        "passed": passed,
        "detail": f"Average duration: {avg_duration:.2f}s (range: {min_dur}-{max_dur}s)",
    }


def _check_no_duplicate_urls(clips: list, contract: dict) -> dict:
    """Check 3: All original_url values must be unique (non-null)."""
    urls = []
    for clip in clips:
        url = clip.get("source", {}).get("original_url")
        if url:  # Only check non-null, non-empty URLs
            urls.append(url)

    url_counts = Counter(urls)
    duplicates = {url: count for url, count in url_counts.items() if count > 1}
    passed = len(duplicates) == 0
    detail = "All URLs unique" if passed else f"Duplicate URLs found: {list(duplicates.keys())}"
    return {
        "name": "no_duplicate_urls",
        "passed": passed,
        "detail": detail,
    }


def _check_transition_diversity(clips: list, contract: dict) -> dict:
    """Check 4: At least 3 distinct transition types."""
    criteria = contract.get("deterministic", {}).get("criteria", {})
    threshold = criteria.get("transition_diversity", {}).get("threshold", 3)

    transition_types = set()
    for clip in clips:
        transition = clip.get("transition", {})
        t_type = transition.get("type")
        if t_type:
            transition_types.add(t_type)

    count = len(transition_types)
    passed = count >= threshold
    return {
        "name": "transition_diversity",
        "passed": passed,
        "detail": f"Distinct transition types: {count} ({sorted(transition_types)}) (threshold: >= {threshold})",
    }


def _check_all_clips_downloaded(clips: list, contract: dict) -> dict:
    """Check 5: Every clip has a non-empty local_path."""
    missing = []
    for clip in clips:
        local_path = clip.get("source", {}).get("local_path")
        if not local_path:  # None or empty string
            missing.append(clip.get("index", "?"))

    passed = len(missing) == 0
    detail = "All clips have local_path" if passed else f"Clips missing local_path: indices {missing}"
    return {
        "name": "all_clips_downloaded",
        "passed": passed,
        "detail": detail,
    }


def _tokenize(text: str) -> set:
    """Simple word tokenizer: lowercase, split on whitespace, strip punctuation."""
    if not text:
        return set()
    import re
    words = re.findall(r"[a-zA-Z\uAC00-\uD7A3]{2,}", text.lower())
    return set(words)


def _check_keyword_overlap(clips: list, narration_sections: list, contract: dict) -> dict:
    """Check 6: search_query shares >= 1 word with narration text for each clip."""
    clips_with_no_overlap = []

    for i, clip in enumerate(clips):
        search_query = clip.get("source", {}).get("search_query", "")
        query_tokens = _tokenize(search_query)

        # Get corresponding narration text
        narration_text = ""
        if i < len(narration_sections):
            section = narration_sections[i]
            if isinstance(section, dict):
                narration_text = section.get("text", "")
            elif isinstance(section, str):
                narration_text = section

        narration_tokens = _tokenize(narration_text)

        if query_tokens and narration_tokens:
            overlap = query_tokens & narration_tokens
            if not overlap:
                clips_with_no_overlap.append(i)

    passed = len(clips_with_no_overlap) == 0
    detail = (
        "All clips have keyword overlap with narration"
        if passed
        else f"Clips with no keyword overlap: indices {clips_with_no_overlap}"
    )
    return {
        "name": "keyword_overlap",
        "passed": passed,
        "detail": detail,
    }


def evaluate_scene_manifest(
    manifest: dict,
    contract_path: str = None,
    narration_sections: list = None,
) -> dict:
    """Evaluate scene-manifest.json against scene-sprint-contract.json criteria.

    Args:
        manifest: Parsed scene-manifest.json dict.
        contract_path: Path to scene-sprint-contract.json (optional, defaults to config/).
        narration_sections: List of narration section dicts with 'text' key (optional).

    Returns:
        dict with keys:
            pass: bool -- True if all checks passed
            issues: list[str] -- list of issue descriptions for failed checks
            checks: list[dict] -- per-check results with name, passed, detail
    """
    contract = load_contract(contract_path)
    clips = manifest.get("clips", [])

    checks = [
        _check_min_clips(clips, contract),
        _check_avg_clip_duration(clips, contract),
        _check_no_duplicate_urls(clips, contract),
        _check_transition_diversity(clips, contract),
        _check_all_clips_downloaded(clips, contract),
    ]

    # Keyword overlap only when narration_sections provided
    if narration_sections is not None:
        checks.append(_check_keyword_overlap(clips, narration_sections, contract))

    issues = [check["detail"] for check in checks if not check["passed"]]
    all_passed = all(check["passed"] for check in checks)

    return {
        "pass": all_passed,
        "issues": issues,
        "checks": checks,
    }


def main():
    """CLI entry point: scene_evaluator.py --manifest PATH [--contract PATH] [--script PATH]"""
    parser = argparse.ArgumentParser(
        description="Deterministic scene-manifest quality evaluator"
    )
    parser.add_argument(
        "--manifest", required=True, help="Path to scene-manifest.json"
    )
    parser.add_argument(
        "--contract", default=None, help="Path to scene-sprint-contract.json"
    )
    parser.add_argument(
        "--script", default=None, help="Path to script.json (for narration text extraction)"
    )
    args = parser.parse_args()

    # Load manifest
    with open(args.manifest, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    # Load narration sections from script.json if provided
    narration_sections = None
    if args.script:
        with open(args.script, "r", encoding="utf-8") as f:
            script = json.load(f)
        # Extract narration text from script sections
        sections = script.get("sections", [])
        narration_sections = [{"text": s.get("narration", "")} for s in sections]

    result = evaluate_scene_manifest(
        manifest,
        contract_path=args.contract,
        narration_sections=narration_sections,
    )

    print(json.dumps(result, indent=2, ensure_ascii=False))
    sys.exit(0 if result["pass"] else 1)


if __name__ == "__main__":
    main()
