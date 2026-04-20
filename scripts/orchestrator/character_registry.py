"""Character reference registry (REQ-091-03, Phase 9.1).

Maps a script ``character_name`` to a reference image path used as Nano
Banana scene prompt anchor + Runway I2V anchor_frame. Hybrid design
(D-07): filesystem layout + JSON manifest. No DB.

Pitfall 5 (Relative path resolution): ``ref_path`` in manifest is relative
to ``registry.json``'s directory. This class records
``assets_root = registry_path.parent`` at init and composes absolute paths
via ``assets_root / entry.ref_path``. Absolute ``ref_path`` values are
kept unchanged.

나베랄 감마 · 대표님 전용 레지스트리 유틸.
"""
from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

__all__ = ["CharacterEntry", "CharacterRegistry"]


class CharacterEntry(BaseModel):
    """pydantic v2 row model for one character entry.

    ``extra='forbid'`` blocks schema drift. Unknown keys in the manifest
    raise ValidationError at load time rather than silently coasting.
    """

    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=64)
    ref_path: Path
    description: str = Field(default="", max_length=500)
    tags: list[str] = Field(default_factory=list)


class CharacterRegistry:
    """Load, query, and introspect the character manifest.

    Public API (frozen by Wave 0 RED tests):
        load() -> self (raises FileNotFoundError 한국어 if missing)
        get(name) -> CharacterEntry (raises KeyError 한국어 if absent)
        get_reference_path(name) -> Path (resolves relative to assets_root)
        list_all() -> list[str] (sorted names)
    """

    def __init__(
        self,
        registry_path: Path = Path("assets/characters/registry.json"),
    ) -> None:
        self.registry_path = Path(registry_path)
        self.assets_root = self.registry_path.parent
        self._entries: dict[str, CharacterEntry] = {}

    def load(self) -> "CharacterRegistry":
        """Parse manifest + validate each entry + confirm ref file exists."""
        if not self.registry_path.exists():
            raise FileNotFoundError(
                f"캐릭터 레지스트리 파일 없음: {self.registry_path} — "
                f"assets/characters/registry.json 을 먼저 생성하세요 (대표님)"
            )
        raw = json.loads(self.registry_path.read_text(encoding="utf-8"))
        entries_raw = raw.get("characters", [])
        if not isinstance(entries_raw, list):
            raise ValueError(
                f"registry.json 'characters' 필드가 list 가 아님 (대표님): "
                f"{type(entries_raw).__name__}"
            )
        for entry_dict in entries_raw:
            entry = CharacterEntry.model_validate(entry_dict)
            resolved = self._resolve(entry.ref_path)
            if not resolved.exists():
                raise FileNotFoundError(
                    f"캐릭터 '{entry.name}' 레퍼런스 파일 없음: {resolved} (대표님)"
                )
            self._entries[entry.name] = entry
        return self

    def get(self, name: str) -> CharacterEntry:
        if name not in self._entries:
            raise KeyError(
                f"캐릭터 '{name}' 을 레지스트리에서 찾을 수 없음 — "
                f"사용 가능: {self.list_all()}"
            )
        return self._entries[name]

    def get_reference_path(self, name: str) -> Path:
        return self._resolve(self.get(name).ref_path)

    def list_all(self) -> list[str]:
        return sorted(self._entries.keys())

    # ------------------------------------------------------------------

    def _resolve(self, ref_path: Path) -> Path:
        return ref_path if ref_path.is_absolute() else (self.assets_root / ref_path)
