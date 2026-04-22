"""Phase 16-03 — Character overlay injection flow 검증.

Plan 16-02 RemotionRenderer._inject_character_props 가 episode sources/
character_assistant.png + character_detective.png 를 remotion/public/<job_id>/ 로
복사하고 props 에 characterLeftSrc / characterRightSrc 를 주입하는지 검증.

CONTEXT.md Q4 locked mapping:
    좌 (characterLeftSrc) = character_assistant.png (왓슨/assistant)
    우 (characterRightSrc) = character_detective.png (탐정/detective)
"""
from __future__ import annotations

import shutil
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]


def _make_renderer(tmp_path: Path):
    """RemotionRenderer instance, bypassing node/ffprobe/remotion_dir checks."""
    from scripts.orchestrator.api.remotion_renderer import RemotionRenderer

    # Simulate remotion/ structure
    (tmp_path / "remotion").mkdir()
    (tmp_path / "remotion" / "package.json").write_text('{"name":"remotion"}', encoding="utf-8")

    # Monkeypatch shutil.which to return 'node' and 'ffprobe' during init
    import scripts.orchestrator.api.remotion_renderer as mod
    orig_which = mod.shutil.which
    mod.shutil.which = lambda b: "C:\\fake\\" + b
    try:
        r = RemotionRenderer(project_root=tmp_path)
    finally:
        mod.shutil.which = orig_which
    return r


class TestInjectCharacterProps:
    """_inject_character_props 단위 동작 검증."""

    def test_both_characters_present(self, tmp_path):
        """좌+우 둘 다 존재 → props 에 둘 다 주입."""
        r = _make_renderer(tmp_path)
        # Prepare episode with both character PNGs
        episode_dir = tmp_path / "episode-test"
        sources = episode_dir / "sources"
        sources.mkdir(parents=True)
        (sources / "character_assistant.png").write_bytes(b"fake_png_data_assistant")
        (sources / "character_detective.png").write_bytes(b"fake_png_data_detective")

        props: dict = {}
        r._inject_character_props(props, "job-xyz", episode_dir)

        assert "characterLeftSrc" in props
        assert "characterRightSrc" in props
        assert props["characterLeftSrc"] == "job-xyz/character_left.png"
        assert props["characterRightSrc"] == "job-xyz/character_right.png"

    def test_character_files_copied_to_public(self, tmp_path):
        """실제 파일이 remotion/public/<job_id>/ 에 복사됨."""
        r = _make_renderer(tmp_path)
        episode_dir = tmp_path / "ep"
        sources = episode_dir / "sources"
        sources.mkdir(parents=True)
        (sources / "character_assistant.png").write_bytes(b"ASSISTANT_BYTES")
        (sources / "character_detective.png").write_bytes(b"DETECTIVE_BYTES")

        props: dict = {}
        r._inject_character_props(props, "job-alpha", episode_dir)

        left_dst = tmp_path / "remotion" / "public" / "job-alpha" / "character_left.png"
        right_dst = tmp_path / "remotion" / "public" / "job-alpha" / "character_right.png"
        assert left_dst.exists()
        assert right_dst.exists()
        assert left_dst.read_bytes() == b"ASSISTANT_BYTES"
        assert right_dst.read_bytes() == b"DETECTIVE_BYTES"

    def test_q4_mapping_left_is_assistant(self, tmp_path):
        """CONTEXT.md Q4: 좌 = assistant (왓슨)."""
        r = _make_renderer(tmp_path)
        episode_dir = tmp_path / "ep"
        sources = episode_dir / "sources"
        sources.mkdir(parents=True)
        (sources / "character_assistant.png").write_bytes(b"WATSON_ASSISTANT")
        (sources / "character_detective.png").write_bytes(b"DETECTIVE")

        props: dict = {}
        r._inject_character_props(props, "job1", episode_dir)

        # 좌 는 assistant 복사본이어야 함
        left_dst = tmp_path / "remotion" / "public" / "job1" / "character_left.png"
        assert left_dst.read_bytes() == b"WATSON_ASSISTANT"

    def test_q4_mapping_right_is_detective(self, tmp_path):
        """CONTEXT.md Q4: 우 = detective (탐정)."""
        r = _make_renderer(tmp_path)
        episode_dir = tmp_path / "ep"
        sources = episode_dir / "sources"
        sources.mkdir(parents=True)
        (sources / "character_assistant.png").write_bytes(b"ASSIST")
        (sources / "character_detective.png").write_bytes(b"DETECTIVE_A")

        props: dict = {}
        r._inject_character_props(props, "job2", episode_dir)

        right_dst = tmp_path / "remotion" / "public" / "job2" / "character_right.png"
        assert right_dst.read_bytes() == b"DETECTIVE_A"

    def test_only_assistant_present(self, tmp_path):
        """assistant 만 존재 → left 만 주입, right 누락 허용."""
        r = _make_renderer(tmp_path)
        episode_dir = tmp_path / "ep"
        sources = episode_dir / "sources"
        sources.mkdir(parents=True)
        (sources / "character_assistant.png").write_bytes(b"A")

        props: dict = {}
        r._inject_character_props(props, "job3", episode_dir)

        assert "characterLeftSrc" in props
        assert "characterRightSrc" not in props

    def test_only_detective_present(self, tmp_path):
        """detective 만 존재 → right 만 주입."""
        r = _make_renderer(tmp_path)
        episode_dir = tmp_path / "ep"
        sources = episode_dir / "sources"
        sources.mkdir(parents=True)
        (sources / "character_detective.png").write_bytes(b"D")

        props: dict = {}
        r._inject_character_props(props, "job4", episode_dir)

        assert "characterRightSrc" in props
        assert "characterLeftSrc" not in props

    def test_no_characters_present(self, tmp_path):
        """둘 다 없음 → props 비어있음 (crash 하지 않음)."""
        r = _make_renderer(tmp_path)
        episode_dir = tmp_path / "ep"
        (episode_dir / "sources").mkdir(parents=True)

        props: dict = {}
        r._inject_character_props(props, "job5", episode_dir)

        assert "characterLeftSrc" not in props
        assert "characterRightSrc" not in props

    def test_public_dir_created_when_needed(self, tmp_path):
        """public/<job_id>/ 디렉토리가 없으면 자동 생성."""
        r = _make_renderer(tmp_path)
        episode_dir = tmp_path / "ep"
        sources = episode_dir / "sources"
        sources.mkdir(parents=True)
        (sources / "character_assistant.png").write_bytes(b"A")

        public_dir = tmp_path / "remotion" / "public" / "new-job-id"
        assert not public_dir.exists()

        props: dict = {}
        r._inject_character_props(props, "new-job-id", episode_dir)

        assert public_dir.exists()

    def test_props_dict_mutated_in_place(self, tmp_path):
        """props 딕셔너리가 호출 후 업데이트됨 (in-place mutation)."""
        r = _make_renderer(tmp_path)
        episode_dir = tmp_path / "ep"
        sources = episode_dir / "sources"
        sources.mkdir(parents=True)
        (sources / "character_assistant.png").write_bytes(b"A")

        props: dict = {"existing_key": "existing_value"}
        r._inject_character_props(props, "job6", episode_dir)

        # Existing keys preserved
        assert props["existing_key"] == "existing_value"
        # New keys added
        assert "characterLeftSrc" in props
