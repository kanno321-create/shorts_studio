"""Phase 42 — Audio-event-driven highlight extractor.

Scans an input video's audio track with YAMNet (tensorflow-hub) for impactful
events (Screaming / Gunshot / Siren / Fire alarm / etc.), then cuts ±window_s
seconds around each detected event. Adjacent windows within MERGE_GAP_S
are merged into a single clip.

CLI:
  python scripts/video-pipeline/auto_highlight.py \\
    --input  sources/real/raw/<id>.mp4 \\
    --output sources/real/<clip_id>.highlight.mp4 \\
    --window 8.0 \\
    --threshold 0.4

Key constants (tunable):
  YAMNET_EVENT_INDICES — whitelist of interesting yamnet class indices
  SCORE_THRESHOLD      — minimum softmax score to trigger an event (default 0.4)
  MERGE_GAP_S          — adjacent windows within this gap collapse (default 2.0)
  DEFAULT_WINDOW_S     — ± seconds around each event center (default 8.0)

Windows safety:
  - All subprocess calls use shell=(sys.platform == 'win32').
  - All paths written with forward slashes.
  - YAMNet runs on CPU (RESEARCH.md §Concurrency) via
    tf.config.set_visible_devices([], 'GPU') + CUDA_VISIBLE_DEVICES="".
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

# Force yamnet onto CPU — avoids torch/TF GPU memory conflict (RESEARCH.md Library Deep-Dive 3).
os.environ.setdefault("CUDA_VISIBLE_DEVICES", "")

# --------------------------------------------------------------------------
# Event class map
# Indices sourced from yamnet_class_map.csv (RESEARCH.md §Library Deep-Dive 3).
# --------------------------------------------------------------------------
YAMNET_EVENT_INDICES: dict[int, str] = {
    14: "Screaming",
    390: "Siren",
    391: "Civil defense siren",
    392: "Buzzer",
    393: "Fire alarm",
    427: "Gunshot",
    428: "Machine gun",
    429: "Fusillade",
    430: "Artillery fire",
    431: "Cap gun",
}

SCORE_THRESHOLD = 0.4
MERGE_GAP_S = 2.0
DEFAULT_WINDOW_S = 8.0


@dataclass
class Window:
    start_s: float
    end_s: float
    label: str
    score: float


# --------------------------------------------------------------------------
# Audio I/O
# --------------------------------------------------------------------------
def _load_audio_16k_mono(path: Path):
    """Load audio resampled to 16 kHz mono float32 via librosa."""
    import librosa

    y, sr = librosa.load(str(path), sr=16000, mono=True)
    return y, sr


# --------------------------------------------------------------------------
# Event detection
# --------------------------------------------------------------------------
def detect_events(
    audio_path: Path,
    window_s: float = DEFAULT_WINDOW_S,
    threshold: float = SCORE_THRESHOLD,
    _hub_load=None,
) -> list[Window]:
    """Detect highlight windows centered on YAMNet events.

    Parameters
    ----------
    audio_path : Path
        Path to audio or video file (librosa handles ffmpeg-backed decode).
    window_s : float
        ±seconds around each event center.
    threshold : float
        Minimum YAMNet softmax score to trigger an event.
    _hub_load : callable | None
        Optional test seam. If provided, called with the YAMNet URL and must
        return a yamnet-compatible callable (scores, embeddings, spectrogram).

    Returns
    -------
    list[Window]
        Sorted, merged windows.
    """
    import numpy as np

    y, _sr = _load_audio_16k_mono(audio_path)

    if _hub_load is None:
        import tensorflow as tf  # type: ignore
        import tensorflow_hub as hub  # type: ignore

        tf.config.set_visible_devices([], "GPU")
        model = hub.load("https://tfhub.dev/google/yamnet/1")
    else:
        model = _hub_load("https://tfhub.dev/google/yamnet/1")

    scores, _embeddings, _spectrogram = model(y)
    scores_np = scores.numpy() if hasattr(scores, "numpy") else np.asarray(scores)

    hop_s = 0.48  # YAMNet frame hop (RESEARCH.md §Library Deep-Dive 3)
    windows: list[Window] = []
    for frame_idx, row in enumerate(scores_np):
        for cls_idx, label in YAMNET_EVENT_INDICES.items():
            if row[cls_idx] >= threshold:
                center = frame_idx * hop_s
                windows.append(
                    Window(
                        start_s=max(0.0, center - window_s),
                        end_s=center + window_s,
                        label=label,
                        score=float(row[cls_idx]),
                    )
                )
                break
    return _merge(windows)


def _merge(ws: list[Window]) -> list[Window]:
    """Collapse adjacent windows within MERGE_GAP_S into one."""
    if not ws:
        return []
    ws = sorted(ws, key=lambda w: w.start_s)
    out: list[Window] = [ws[0]]
    for w in ws[1:]:
        last = out[-1]
        if w.start_s - last.end_s <= MERGE_GAP_S:
            out[-1] = Window(
                start_s=last.start_s,
                end_s=max(last.end_s, w.end_s),
                label=(
                    f"{last.label}+{w.label}"
                    if last.label != w.label
                    else last.label
                ),
                score=max(last.score, w.score),
            )
        else:
            out.append(w)
    return out


# --------------------------------------------------------------------------
# ffmpeg cut + concat
# --------------------------------------------------------------------------
def cut_clip(input_path: Path, windows: list[Window], output_path: Path) -> None:
    """Extract each window via ffmpeg -ss/-to, then concat into output_path."""
    if not windows:
        raise RuntimeError(
            "No highlight windows detected — YAMNet score below threshold"
        )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    parts: list[Path] = []
    for i, w in enumerate(windows):
        part = output_path.parent / f"_part_{i}.mp4"
        cmd = [
            "ffmpeg",
            "-y",
            "-loglevel",
            "error",
            "-ss",
            f"{w.start_s:.3f}",
            "-to",
            f"{w.end_s:.3f}",
            "-i",
            str(input_path).replace("\\", "/"),
            "-c",
            "copy",
            str(part).replace("\\", "/"),
        ]
        subprocess.run(cmd, check=True, shell=(sys.platform == "win32"))
        parts.append(part)

    list_file = output_path.parent / "_concat.txt"
    list_file.write_text(
        "\n".join(f"file '{p.name}'" for p in parts), encoding="utf-8"
    )
    cmd = [
        "ffmpeg",
        "-y",
        "-loglevel",
        "error",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        str(list_file).replace("\\", "/"),
        "-c",
        "copy",
        str(output_path).replace("\\", "/"),
    ]
    subprocess.run(
        cmd,
        check=True,
        cwd=str(output_path.parent),
        shell=(sys.platform == "win32"),
    )
    for p in parts:
        p.unlink(missing_ok=True)
    list_file.unlink(missing_ok=True)


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------
def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Phase 42 yamnet highlight extractor")
    ap.add_argument("--input", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--window", type=float, default=DEFAULT_WINDOW_S)
    ap.add_argument("--threshold", type=float, default=SCORE_THRESHOLD)
    args = ap.parse_args(argv)

    windows = detect_events(
        args.input, window_s=args.window, threshold=args.threshold
    )
    print(f"[info] {len(windows)} highlight windows detected")
    cut_clip(args.input, windows, args.output)
    print(f"[ok] -> {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
