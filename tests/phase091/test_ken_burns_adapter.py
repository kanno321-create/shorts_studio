"""RED stub for REQ-091-04 — Wave 1 KenBurnsLocalAdapter target.

Frozen contract:
    KenBurnsUnavailable(RuntimeError)
    KenBurnsLocalAdapter(circuit_breaker, output_dir)
    .generate_clip(image, duration_seconds, resolution, fps, zoom_rate) -> Path
"""
from __future__ import annotations

import subprocess
from pathlib import Path
from unittest.mock import MagicMock

import pytest


def test_ken_burns_importable() -> None:
    """REQ-091-04: KenBurnsLocalAdapter + KenBurnsUnavailable importable."""
    from scripts.orchestrator.api.ken_burns import (  # noqa: F401
        KenBurnsLocalAdapter,
        KenBurnsUnavailable,
    )


def test_missing_ffmpeg_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    """REQ-091-04: missing ffmpeg raises KenBurnsUnavailable with Korean message."""
    import scripts.orchestrator.api.ken_burns as kb_mod
    from scripts.orchestrator.api.ken_burns import (
        KenBurnsLocalAdapter,
        KenBurnsUnavailable,
    )

    monkeypatch.setattr(kb_mod.shutil, "which", lambda _: None)
    with pytest.raises(KenBurnsUnavailable, match="ffmpeg"):
        KenBurnsLocalAdapter()


def test_cmd_construction_includes_scale_and_zoompan(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    fixture_png_bytes: bytes,
) -> None:
    """REQ-091-04: ffmpeg command includes scale=4000:-1 prefix and zoompan filter.

    Pitfall 3 (Research §3): low-res zoompan without prefix scale is jittery.
    """
    import scripts.orchestrator.api.ken_burns as kb_mod
    from scripts.orchestrator.api.ken_burns import KenBurnsLocalAdapter

    monkeypatch.setattr(kb_mod.shutil, "which", lambda _: "/usr/bin/ffmpeg")

    captured = {}

    def fake_run(cmd, **kwargs):
        captured["cmd"] = cmd
        out = Path(cmd[-1])
        out.write_bytes(b"\x00\x00\x00\x18ftypmp42")  # minimal mp4 header stub
        result = MagicMock()
        result.returncode = 0
        result.stderr = ""
        return result

    monkeypatch.setattr(kb_mod.subprocess, "run", fake_run)

    img = tmp_path / "input.png"
    img.write_bytes(fixture_png_bytes)
    adapter = KenBurnsLocalAdapter(output_dir=tmp_path)
    adapter.generate_clip(img)

    joined = " ".join(captured["cmd"])
    assert "scale=4000:-1" in joined, f"missing scale prefix; got: {joined[:300]}"
    assert "zoompan=" in joined, f"missing zoompan filter; got: {joined[:300]}"


def test_nonzero_rc_raises_korean(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    fixture_png_bytes: bytes,
) -> None:
    """REQ-091-04: ffmpeg rc != 0 raises RuntimeError containing 'ffmpeg 실패'."""
    import scripts.orchestrator.api.ken_burns as kb_mod
    from scripts.orchestrator.api.ken_burns import KenBurnsLocalAdapter

    monkeypatch.setattr(kb_mod.shutil, "which", lambda _: "/usr/bin/ffmpeg")

    def fake_run(cmd, **kwargs):
        result = MagicMock()
        result.returncode = 1
        result.stderr = "stream error"
        return result

    monkeypatch.setattr(kb_mod.subprocess, "run", fake_run)

    img = tmp_path / "input.png"
    img.write_bytes(fixture_png_bytes)
    adapter = KenBurnsLocalAdapter(output_dir=tmp_path)
    with pytest.raises(RuntimeError, match="ffmpeg 실패"):
        adapter.generate_clip(img)


# Silence unused import warning for subprocess (referenced symbolically in monkeypatches)
_ = subprocess
