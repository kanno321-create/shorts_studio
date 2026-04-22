"""Phase 42 — Face mosaic via YOLOv8-face + ByteTrack.

⚠️ AUDIO 유실: OpenCV VideoWriter는 audio stream 미보존.
출력 파일에 audio가 필요하면 ffmpeg로 원본 audio를 재병합하라:
  ffmpeg -i output.mp4 -i input.mp4 -map 0:v:0 -map 1:a:0 -c:v copy -c:a aac -shortest merged.mp4

CLI:
  python scripts/video-pipeline/face_mosaic.py \\
    --input sources/real/X.highlight.mp4 \\
    --output sources/real/X.faces.mp4 \\
    --weights models/yolov8n-face.pt

--mode note (CONTEXT.md deferred "수동/반자동 모자이크 옵션 금지" 스피릿 준수):
  --mode는 deployment-time system config (default "blur" 고정). 운영 수동 변경 금지.
  CLI 노출 이유는 개발 테스트용만 (pixelate 비교 검증 시). 프로덕션 파이프라인
  (video-sourcer 에이전트 호출)은 기본값 "blur"로만 실행하며 --mode pixelate 를
  명시적으로 호출하지 않는다.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Optional

BLUR_KSIZE = (51, 51)  # OpenCV requires odd
PIXELATE_FACTOR = 20


class FaceMosaic:
    def __init__(
        self,
        weights_path: Path,
        conf: float = 0.25,
        device: Optional[str] = None,
        mode: str = "blur",
    ):
        from ultralytics import YOLO

        self._yolo = YOLO(str(weights_path))
        self._conf = conf
        self._device = device  # None = auto
        self._mode = mode  # "blur" or "pixelate" (deployment-time only)

    def _apply_blur(self, frame, x1, y1, x2, y2):
        import cv2

        h, w = frame.shape[:2]
        x1 = max(0, int(x1))
        y1 = max(0, int(y1))
        x2 = min(w, int(x2))
        y2 = min(h, int(y2))
        if x2 <= x1 or y2 <= y1:
            return frame
        roi = frame[y1:y2, x1:x2]
        if self._mode == "pixelate":
            small = cv2.resize(
                roi,
                (
                    max(1, roi.shape[1] // PIXELATE_FACTOR),
                    max(1, roi.shape[0] // PIXELATE_FACTOR),
                ),
                interpolation=cv2.INTER_LINEAR,
            )
            roi = cv2.resize(
                small,
                (roi.shape[1], roi.shape[0]),
                interpolation=cv2.INTER_NEAREST,
            )
        else:
            roi = cv2.GaussianBlur(roi, BLUR_KSIZE, 0)
        frame[y1:y2, x1:x2] = roi
        return frame

    def process(self, input_path: Path, output_path: Path) -> dict:
        import cv2

        cap = cv2.VideoCapture(str(input_path))
        if not cap.isOpened():
            raise RuntimeError(f"Cannot open {input_path}")
        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        cap.release()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer = cv2.VideoWriter(str(output_path), fourcc, fps, (w, h))
        # Use ultralytics track() streaming with ByteTrack for persistent face IDs
        results = self._yolo.track(
            source=str(input_path),
            tracker="bytetrack.yaml",
            persist=True,
            stream=True,
            conf=self._conf,
            device=self._device,
            verbose=False,
        )
        frame_idx = 0
        total_faces = 0
        for res in results:
            frame = res.orig_img
            if res.boxes is not None and len(res.boxes) > 0:
                for box in res.boxes.xyxy.cpu().numpy():
                    x1, y1, x2, y2 = box[:4]
                    frame = self._apply_blur(frame, x1, y1, x2, y2)
                    total_faces += 1
            writer.write(frame)
            frame_idx += 1
        writer.release()
        return {
            "frames_processed": frame_idx,
            "expected_frames": total,
            "total_face_detections": total_faces,
            "output": str(output_path).replace("\\", "/"),
        }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--weights", type=Path, default=Path("models/yolov8n-face.pt"))
    ap.add_argument("--conf", type=float, default=0.25)
    ap.add_argument("--device", default=None)
    # --mode: deployment-time config; production pipeline must not pass "pixelate".
    ap.add_argument("--mode", choices=["blur", "pixelate"], default="blur")
    args = ap.parse_args(argv)
    if not args.weights.exists():
        print(
            f"[err] weights missing: {args.weights}. "
            f"Run scripts/video-pipeline/_download_face_weights.py",
            file=sys.stderr,
        )
        return 2
    fm = FaceMosaic(args.weights, conf=args.conf, device=args.device, mode=args.mode)
    result = fm.process(args.input, args.output)
    print(json.dumps(result, indent=2))
    # Coverage check: frames_processed must equal expected (zero missed)
    if result["frames_processed"] < result["expected_frames"]:
        print(
            f"[err] missed frames: "
            f"{result['expected_frames'] - result['frames_processed']}",
            file=sys.stderr,
        )
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main())
