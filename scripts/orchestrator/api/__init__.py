"""scripts.orchestrator.api — namespace for external service adapters.

Phase 5 Plan 06 fills this package with:
    - kling_i2v.py       : KlingI2VAdapter (fal.ai endpoint, primary I2V)
    - runway_i2v.py      : RunwayI2VAdapter (Gen-3 Alpha Turbo, fallback I2V)
    - typecast.py        : TypecastAdapter (primary Korean TTS)
    - elevenlabs.py      : ElevenLabsAdapter (fallback TTS + word timestamps)
    - shotstack.py       : ShotstackAdapter (timeline render, ken-burns fallback)

Design constraint (VIDEO-01 / D-13):
    T2V code paths are FORBIDDEN. Adapters expose image_to_video() only.
    RunwayI2VAdapter MUST NOT expose text_to_video() even if upstream SDK has
    one. The pre_tool_use Hook regex in .claude/deprecated_patterns.json
    blocks re-introduction of t2v / text_to_video / text2video identifiers.

No imports at this layer — each adapter is optional at runtime and the
pipeline injects them via constructor args.
"""
from __future__ import annotations
