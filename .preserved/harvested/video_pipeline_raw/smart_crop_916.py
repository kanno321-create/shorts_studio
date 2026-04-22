"""Phase 42 — Smart 9:16 crop (1080x1920) following face/motion centroid.

⚠️ AUDIO 유실: OpenCV VideoWriter는 audio stream 미보존.
출력 파일에 audio가 필요하면 ffmpeg로 원본 audio를 재병합하라:
  ffmpeg -i output.mp4 -i input.mp4 -map 0:v:0 -map 1:a:0 -c:v copy -c:a aac -shortest merged.mp4

CLI:
  python scripts/video-pipeline/smart_crop_916.py \\
    --input sources/real/X.plates.mp4 \\
    --output sources/real/X.clean.mp4 \\
    --target-w 1080 --target-h 1920

Per-frame face centroids (YOLOv8-face) are smoothed with EMA, then used as
the crop center in scaled space. If face weights absent or YOLO not invoked,
falls back to frame-center (safe default).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

TARGET_W_DEFAULT = 1080
TARGET_H_DEFAULT = 1920
EMA_ALPHA = 0.2  # smoothing factor for center EMA


class SmartCrop916:
    def __init__(
        self,
        face_weights: "Path | None" = None,
        ema_alpha: float = EMA_ALPHA,
    ):
        self._face_weights = face_weights
        self._ema_alpha = ema_alpha
        self._yolo = None

    def _load_yolo(self):
        if self._yolo is None and self._face_weights is not None:
            from ultralytics import YOLO

            self._yolo = YOLO(str(self._face_weights))
        return self._yolo

    def _detect_centers(self, input_path: Path) -> list:
        """Return per-frame (cx, cy) in source pixels."""
        import cv2

        cap = cv2.VideoCapture(str(input_path))
        w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        cap.release()
        yolo = self._load_yolo()
        centers: list = []
        if yolo is None:
            return [(w / 2, h / 2)] * total
        results = yolo.predict(
            source=str(input_path), stream=True, conf=0.25, verbose=False
        )
        for res in results:
            if res.boxes is not None and len(res.boxes) > 0:
                boxes = res.boxes.xyxy.cpu().numpy()
                cxs = ((boxes[:, 0] + boxes[:, 2]) / 2).mean()
                cys = ((boxes[:, 1] + boxes[:, 3]) / 2).mean()
                centers.append((float(cxs), float(cys)))
            else:
                centers.append((w / 2, h / 2))
        return centers

    def _smooth(self, centers: list) -> list:
        """EMA-smooth a list of (cx, cy) centers."""
        if not centers:
            return centers
        out = [centers[0]]
        for cx, cy in centers[1:]:
            pcx, pcy = out[-1]
            out.append(
                (
                    self._ema_alpha * cx + (1 - self._ema_alpha) * pcx,
                    self._ema_alpha * cy + (1 - self._ema_alpha) * pcy,
                )
            )
        return out

    def process(
        self,
        input_path: Path,
        output_path: Path,
        target_w: int = TARGET_W_DEFAULT,
        target_h: int = TARGET_H_DEFAULT,
    ) -> dict:
        import cv2

        centers = self._smooth(self._detect_centers(input_path))
        cap = cv2.VideoCapture(str(input_path))
        sw = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        sh = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        # scale source to target_h while preserving aspect, then crop width = target_w
        scale = target_h / sh if sh else 1.0
        scaled_w = int(round(sw * scale))
        output_path.parent.mkdir(parents=True, exist_ok=True)
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer = cv2.VideoWriter(str(output_path), fourcc, fps, (target_w, target_h))
        frame_idx = 0
        face_in_crop_count = 0
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            # scale frame to target_h
            scaled = cv2.resize(
                frame, (scaled_w, target_h), interpolation=cv2.INTER_LINEAR
            )
            # crop center-x in scaled space
            if frame_idx < len(centers):
                cx_src = centers[frame_idx][0]
            else:
                cx_src = sw / 2
            cx_scaled = cx_src * scale
            x_start = int(
                max(0, min(scaled_w - target_w, cx_scaled - target_w / 2))
            )
            cropped = scaled[:, x_start:x_start + target_w]
            if cropped.shape[1] != target_w:
                pad = target_w - cropped.shape[1]
                cropped = cv2.copyMakeBorder(
                    cropped, 0, 0, 0, pad, cv2.BORDER_CONSTANT
                )
            # Ensure contiguous buffer for VideoWriter (slice may be a view)
            cropped = cropped.copy()
            writer.write(cropped)
            # face-in-crop check: ±200px tolerance from crop center
            if abs(cx_scaled - (x_start + target_w / 2)) <= 200:
                face_in_crop_count += 1
            frame_idx += 1
        writer.release()
        cap.release()
        return {
            "frames_processed": frame_idx,
            "target_w": target_w,
            "target_h": target_h,
            "face_in_crop_frames": face_in_crop_count,
            "output": str(output_path).replace("\\", "/"),
        }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--target-w", type=int, default=TARGET_W_DEFAULT)
    ap.add_argument("--target-h", type=int, default=TARGET_H_DEFAULT)
    ap.add_argument(
        "--face-weights", type=Path, default=Path("models/yolov8n-face.pt")
    )
    args = ap.parse_args(argv)
    face_w = args.face_weights if args.face_weights.exists() else None
    sc = SmartCrop916(face_weights=face_w)
    result = sc.process(
        args.input, args.output, target_w=args.target_w, target_h=args.target_h
    )
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
