"""One-shot demo: re-assemble last 3 Kling clips with the fixed ffmpeg_assembler.

Proves the 720p→1080p + 419kbps→8Mbps fix works end-to-end without touching the
upstream Kling outputs (which are already 1080×1920).
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from scripts.orchestrator.api.ffmpeg_assembler import _run_ffmpeg, _transcode_clip


def main() -> int:
    src_clips = sorted(Path("outputs/kling").glob("kling_*.mp4"))[-3:]
    print(f"[repair] source clips: {[c.name for c in src_clips]}")

    tmp = Path("outputs/ffmpeg_assembly/_repair_demo")
    tmp.mkdir(exist_ok=True, parents=True)

    new_segs = []
    for i, src in enumerate(src_clips):
        dst = tmp / f"seg_{i:03d}.mp4"
        print(f"[repair] transcoding {src.name} → 1080×1920 + 8Mbps")
        _transcode_clip(src, dst, 1.0, 1080, 1920, 30, 600)
        new_segs.append(dst)

    concat_list = tmp / "concat.txt"
    concat_list.write_text(
        "\n".join(f"file '{p.resolve().as_posix()}'" for p in new_segs),
        encoding="utf-8",
    )
    video_concat = tmp / "video_concat.mp4"
    _run_ffmpeg(
        ["-f", "concat", "-safe", "0", "-i", str(concat_list),
         "-c:v", "copy", "-an", "-y", str(video_concat)],
        timeout_s=600,
    )

    audio_src = Path("outputs/ffmpeg_assembly/_tmp_1776844678983/audio_concat.aac")
    out = Path("outputs/ffmpeg_assembly/repaired_demo.mp4")
    _run_ffmpeg(
        ["-i", str(video_concat), "-i", str(audio_src),
         "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
         "-ac", "2", "-ar", "48000",
         "-shortest", "-movflags", "+faststart",
         "-y", str(out)],
        timeout_s=600,
    )

    print(f"\n[repair] OUTPUT: {out}  ({out.stat().st_size:,} bytes)")
    probe = subprocess.check_output(
        ["ffprobe", "-v", "error",
         "-show_entries", "stream=width,height,bit_rate,codec_name,channels,sample_rate",
         "-of", "default=nw=1", str(out)],
        encoding="utf-8",
    )
    print("\n=== ffprobe (REPAIRED) ===")
    print(probe)
    return 0


if __name__ == "__main__":
    sys.exit(main())
