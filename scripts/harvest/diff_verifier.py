"""Recursive filecmp.dircmp wrapper.

Default filecmp.dircmp only reports immediate children. This module
recurses through common_dirs and returns a flat mismatch list.

Empty list == perfect copy. CLI exits 0 iff mismatches == [].
"""
from __future__ import annotations

import argparse
import filecmp
import json
import sys
from pathlib import Path


def deep_diff(src: Path, dst: Path) -> list[str]:
    """Recursive directory comparison.

    Returns:
        list of mismatch strings prefixed with one of:
          - MISSING_IN_DEST: file exists in src but not dst
          - EXTRA_IN_DEST:   file exists in dst but not src
          - CONTENT_DIFF:    both exist but differ (shallow cmp)
          - COMPARE_ERROR:   dircmp.funny_files (unreadable, etc.)

    An empty list means every file matches.
    """
    mismatches: list[str] = []

    def _walk(a: Path, b: Path, prefix: str) -> None:
        cmp = filecmp.dircmp(str(a), str(b))
        for name in cmp.left_only:
            mismatches.append(f"MISSING_IN_DEST: {prefix}/{name}")
        for name in cmp.right_only:
            mismatches.append(f"EXTRA_IN_DEST: {prefix}/{name}")
        for name in cmp.diff_files:
            mismatches.append(f"CONTENT_DIFF: {prefix}/{name}")
        for name in cmp.funny_files:
            mismatches.append(f"COMPARE_ERROR: {prefix}/{name}")
        for name in cmp.common_dirs:
            _walk(a / name, b / name, f"{prefix}/{name}")

    if not src.is_dir():
        raise FileNotFoundError(f"source directory not found: {src}")
    if not dst.is_dir():
        raise FileNotFoundError(f"destination directory not found: {dst}")

    _walk(src, dst, "")
    return mismatches


def _cli() -> int:
    parser = argparse.ArgumentParser(
        description="Recursive directory diff for harvested raw dirs."
    )
    parser.add_argument(
        "raw_dir_name",
        help="logical name (e.g. theme_bible_raw). Looked up in path_manifest.json.",
    )
    parser.add_argument(
        "--manifest",
        default=".planning/phases/03-harvest/path_manifest.json",
        help="path_manifest.json path",
    )
    parser.add_argument(
        "--dest-root",
        default=".preserved/harvested",
        help="harvested destination root",
    )
    parser.add_argument(
        "--source-root",
        default="C:/Users/PC/Desktop/shorts_naberal",
        help="shorts_naberal source root",
    )
    args = parser.parse_args()

    manifest_path = Path(args.manifest)
    if not manifest_path.is_file():
        print(f"[FAIL] manifest not found: {manifest_path}", file=sys.stderr)
        return 2

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    entry = manifest.get(args.raw_dir_name)
    if not entry:
        print(
            f"[FAIL] raw_dir_name '{args.raw_dir_name}' not in manifest",
            file=sys.stderr,
        )
        return 2

    source_rel = entry.get("source")
    if not source_rel:
        print(
            f"[SKIP] {args.raw_dir_name} has no single source "
            f"(cherry_pick mode); deep_diff not applicable.",
            file=sys.stderr,
        )
        return 0

    src = Path(args.source_root) / source_rel
    dst = Path(args.dest_root) / args.raw_dir_name

    mismatches = deep_diff(src, dst)
    if not mismatches:
        print(f"[OK] {args.raw_dir_name}: 0 mismatches")
        return 0

    print(f"[FAIL] {args.raw_dir_name}: {len(mismatches)} mismatches")
    for m in mismatches:
        print(f"  {m}")
    return 1


if __name__ == "__main__":
    sys.exit(_cli())
