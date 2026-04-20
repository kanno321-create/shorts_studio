"""PIPELINE-03 adapter graceful-degrade tests (5 cases, D-05/D-06).

These tests lock the contract that missing env for ANY single adapter
must NOT block ``ShortsPipeline.__init__``. Each missing adapter must be
logged as a warning + the slot set to the injected arg (``None`` by default
in these tests) so mock-based test harnesses construct cleanly. Adapter
internals (``scripts/orchestrator/api/*.py``) remain eager (D-06 regression
protection) — the pipeline site wraps the instantiation uniformly via the
``_try_adapter`` helper.

Contract seam: these tests intentionally instantiate ``ShortsPipeline``
without injecting the target adapter, then clear its env keys. The
``_try_adapter`` helper should catch ``ValueError``/``KenBurnsUnavailable``
from the adapter ``__init__`` and emit a Korean-first warning containing
the adapter name + "대표님".
"""
from __future__ import annotations

import logging
from unittest.mock import MagicMock


_ADAPTER_ENV_KEYS = {
    "kling":      ("KLING_API_KEY", "FAL_KEY"),
    "runway":     ("RUNWAY_API_KEY",),
    "typecast":   ("TYPECAST_API_KEY",),
    "elevenlabs": ("ELEVENLABS_API_KEY",),
    "shotstack":  ("SHOTSTACK_API_KEY",),
    "nanobanana": ("GOOGLE_API_KEY",),
}


def _build_pipeline_skipping_adapter(adapter_name, monkeypatch, tmp_path, caplog):
    """Clear env keys for ``adapter_name``; construct pipeline.

    Returns ``(pipeline, warnings_for_adapter)``.
    """
    from scripts.orchestrator import ShortsPipeline

    # Clear env keys for the target adapter.
    for key in _ADAPTER_ENV_KEYS.get(adapter_name, ()):
        monkeypatch.delenv(key, raising=False)

    caplog.set_level(logging.WARNING, logger="scripts.orchestrator.shorts_pipeline")
    pipeline = ShortsPipeline(
        session_id="test_graceful",
        state_root=tmp_path,
        producer_invoker=MagicMock(),
        supervisor_invoker=MagicMock(),
    )
    # Adapter whose env we cleared should be None — helper returned the
    # injected value (None in this constructor call path).
    assert getattr(pipeline, adapter_name) is None, (
        f"pipeline.{adapter_name} must be None when env missing"
    )
    adapter_warnings = [
        r for r in caplog.records
        if r.levelname == "WARNING" and adapter_name in r.getMessage()
    ]
    return pipeline, adapter_warnings


def test_pipeline_constructs_when_kling_env_missing(monkeypatch, tmp_path, caplog):
    pipeline, warnings = _build_pipeline_skipping_adapter(
        "kling", monkeypatch, tmp_path, caplog,
    )
    assert pipeline is not None
    assert len(warnings) >= 1
    assert "대표님" in warnings[0].getMessage()


def test_pipeline_constructs_when_runway_env_missing(monkeypatch, tmp_path, caplog):
    pipeline, warnings = _build_pipeline_skipping_adapter(
        "runway", monkeypatch, tmp_path, caplog,
    )
    assert pipeline is not None
    assert len(warnings) >= 1
    assert "대표님" in warnings[0].getMessage()


def test_pipeline_constructs_when_typecast_env_missing(monkeypatch, tmp_path, caplog):
    pipeline, warnings = _build_pipeline_skipping_adapter(
        "typecast", monkeypatch, tmp_path, caplog,
    )
    assert pipeline is not None
    assert len(warnings) >= 1
    assert "대표님" in warnings[0].getMessage()


def test_pipeline_constructs_when_elevenlabs_env_missing(monkeypatch, tmp_path, caplog):
    pipeline, warnings = _build_pipeline_skipping_adapter(
        "elevenlabs", monkeypatch, tmp_path, caplog,
    )
    assert pipeline is not None
    assert len(warnings) >= 1
    assert "대표님" in warnings[0].getMessage()


def test_pipeline_all_adapters_missing_still_constructs(monkeypatch, tmp_path, caplog):
    """All network adapters missing env → pipeline constructs; warnings logged."""
    from scripts.orchestrator import ShortsPipeline

    # Clear env for every network adapter.
    for keys in _ADAPTER_ENV_KEYS.values():
        for k in keys:
            monkeypatch.delenv(k, raising=False)

    caplog.set_level(logging.WARNING, logger="scripts.orchestrator.shorts_pipeline")
    pipeline = ShortsPipeline(
        session_id="test_all_missing",
        state_root=tmp_path,
        producer_invoker=MagicMock(),
        supervisor_invoker=MagicMock(),
    )

    # All 6 network adapter slots must be None (ken_burns is ffmpeg-dependent
    # and not asserted here — env-agnostic).
    assert pipeline.kling is None
    assert pipeline.runway is None
    assert pipeline.typecast is None
    assert pipeline.elevenlabs is None
    assert pipeline.shotstack is None
    assert pipeline.nanobanana is None

    # At least one warning per adapter that was missing.
    warn_msgs = [r.getMessage() for r in caplog.records if r.levelname == "WARNING"]
    for adapter in ("kling", "runway", "typecast", "elevenlabs", "shotstack", "nanobanana"):
        assert any(adapter in m for m in warn_msgs), (
            f"Expected a warning mentioning {adapter!r}; got: {warn_msgs}"
        )
