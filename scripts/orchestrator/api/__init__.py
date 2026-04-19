"""scripts.orchestrator.api — namespace for external service adapters.

Phase 5 Plan 06 fills this package with:
    - kling_i2v.py       : KlingI2VAdapter (fal.ai endpoint, primary I2V)
    - runway_i2v.py      : RunwayI2VAdapter (Gen-3 Alpha Turbo, fallback I2V)
    - typecast.py        : TypecastAdapter (primary Korean TTS)
    - elevenlabs.py      : ElevenLabsAdapter (fallback TTS + word timestamps)
    - shotstack.py       : ShotstackAdapter (timeline render, ken-burns fallback)

Design constraint (VIDEO-01 / D-13):
    Text-driven video code paths are FORBIDDEN. Adapters expose
    image_to_video() only, using an anchor frame as the seed. Even if an
    upstream SDK exposes a text-only method, the adapter MUST NOT re-export
    it. The pre_tool_use Hook regex in .claude/deprecated_patterns.json
    blocks re-introduction of the banned identifiers (see ORCH-08 / AF-14).

No imports at this layer — each adapter is optional at runtime and the
pipeline injects them via constructor args.
"""
from __future__ import annotations
