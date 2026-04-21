"""shorts_pipeline.py — Phase 5 Orchestrator v2 (ORCH-01 keystone).

Single-file 500~800 line state machine that integrates every Wave 0-3
primitive into a 13-GATE DAG executor. Physical invariants
(CONTEXT D-1 / D-8 / D-9 / D-13) are enforced by this file's size and
blacklist grep acceptance checks run in the test suite — see
``.planning/phases/05-orchestrator-v2-write/05-CONTEXT.md`` for the
exact forbidden-token list (acceptance is 0 matches for each).

Public API::

    pipeline = ShortsPipeline(session_id="20260419-1430-wildlife-mantis")
    result = pipeline.run()
    # -> {"session_id": ..., "final_gate": "COMPLETE",
    #     "dispatched_count": 13, "fallback_count": 0}

Requirements fulfilled:
    - ORCH-01 : this file (500~800 line single-file state machine)
    - ORCH-02 : 13 operational GATE IntEnum transition sequencing
    - ORCH-03 : GateGuard.dispatch single enforcement point
    - ORCH-04 : verify_all_dispatched at COMPLETE (IncompleteDispatch raise)
    - ORCH-05 : Checkpointer resume + per-gate save
    - ORCH-06 : 5 CircuitBreaker instances (kling/runway/typecast/elevenlabs/shotstack)
    - ORCH-07 : GATE_DEPS runtime check via ensure_dependencies
    - ORCH-08 : D-8 blacklist (no forbidden kwarg) enforced by test grep
    - ORCH-09 : D-9 blacklist (no forbidden comments) enforced by test grep
    - ORCH-10 : VoiceFirstTimeline ASSEMBLY (audio-first alignment)
    - ORCH-11 : Low-Res First — Shotstack.render(resolution="hd") before upscale
    - ORCH-12 : _producer_loop 3-retry regeneration + FAILURES append +
               ken-burns Fallback for ASSETS / THUMBNAIL

See ``.planning/phases/05-orchestrator-v2-write/05-CONTEXT.md`` for the full
D-1..D-20 decision register.
"""
from __future__ import annotations

import argparse
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

from .checkpointer import Checkpoint, Checkpointer, make_timestamp
from .circuit_breaker import CircuitBreaker, CircuitBreakerOpenError
from .fallback import append_failures, insert_fallback_shot
from .gate_guard import GateGuard, Verdict
from .gates import (
    GATE_DEPS,
    GateName,
    IncompleteDispatch,
    RegenerationExhausted,
)
from .voice_first_timeline import (
    AudioSegment,
    VideoCut,
    VoiceFirstTimeline,
)

from .api.elevenlabs import ElevenLabsAdapter
from .api.ken_burns import KenBurnsLocalAdapter, KenBurnsUnavailable
from .api.kling_i2v import KlingI2VAdapter
from .api.nanobanana import NanoBananaAdapter
from .api.runway_i2v import RunwayI2VAdapter
from .api.shotstack import ShotstackAdapter
from .api.typecast import TypecastAdapter
from .character_registry import CharacterRegistry
from .invokers import (
    make_default_asset_sourcer,
    make_default_producer_invoker,
    make_default_supervisor_invoker,
)


logger = logging.getLogger(__name__)


# ===========================================================================
# GATE_INSPECTORS — per-gate Inspector mapping
# ===========================================================================
# Consumed by ``scripts/hc_checks/hc_checks.check_hc_10_inspector_coverage``
# (RESEARCH §hc_checks rewrite line 965). Each key is the string name of
# an operational GATE; each value is the list of ``.claude/agents/inspectors/``
# directory names that must report for the gate's supervisor fan-out.
GATE_INSPECTORS: dict[str, list[str]] = {
    "TREND":        ["ins-readability"],
    "NICHE":        ["ins-blueprint-compliance"],
    "RESEARCH_NLM": ["ins-factcheck"],
    "BLUEPRINT":    ["ins-blueprint-compliance", "ins-timing-consistency"],
    "SCRIPT":       [
        "ins-narrative-quality",
        "ins-korean-naturalness",
        "ins-tone-brand",
        "ins-readability",
    ],
    "POLISH":       [
        "ins-korean-naturalness",
        "ins-tone-brand",
        "ins-schema-integrity",
    ],
    "VOICE":        ["ins-audio-quality", "ins-subtitle-alignment"],
    "ASSETS":       ["ins-mosaic", "ins-gore", "ins-license"],
    "ASSEMBLY":     [
        "ins-render-integrity",
        "ins-subtitle-alignment",
        "ins-timing-consistency",
    ],
    "THUMBNAIL":    ["ins-thumbnail-hook", "ins-safety"],
    "METADATA":     ["ins-platform-policy", "ins-safety"],
    "UPLOAD":       ["ins-platform-policy"],
    "MONITOR":      ["ins-schema-integrity"],
}


# ===========================================================================
# GateContext — per-run data carrier
# ===========================================================================


@dataclass
class GateContext:
    """Per-run context carrying state between GATEs.

    ``artifacts`` maps each dispatched gate to the Producer's output path
    (or ``None`` when the gate produced no filesystem artifact, e.g.
    MONITOR which only records metrics).

    ``retry_counts`` is tracked per-GATE so that post-mortem debugging can
    see which gates needed the most regeneration attempts.

    ``fallback_indices`` (RESEARCH §9 line 862) records the cut indices
    where the regeneration loop fell back to ken-burns; used both for
    diagnostics and to prevent double-insertion on resume.
    """

    session_id: str
    config: dict = field(default_factory=dict)
    channel_bible: dict = field(default_factory=dict)
    retry_counts: dict[GateName, int] = field(default_factory=dict)
    artifacts: dict[GateName, Any] = field(default_factory=dict)
    audio_segments: list[AudioSegment] = field(default_factory=list)
    video_cuts: list[VideoCut] = field(default_factory=list)
    fallback_indices: list[int] = field(default_factory=list)


# ===========================================================================
# ShortsPipeline — the 13-GATE state machine integrator
# ===========================================================================


class ShortsPipeline:
    """Phase 5 orchestrator — integrates all Wave 0-3 primitives.

    D-1 requires this class plus its 13 ``_run_<gate>`` methods to live in
    a single 500~800 line file. Supporting classes (CircuitBreaker,
    Checkpointer, GateGuard, VoiceFirstTimeline, the five API adapters)
    live in their own sibling modules so the keystone stays auditable.

    Dependency injection:

    * ``producer_invoker`` takes ``(agent_name, gate_name, inputs)`` and
      returns a Producer output dict. Production wires this to the Phase 4
      agent harness; tests pass ``MagicMock``.
    * ``supervisor_invoker`` takes ``(gate, output)`` and returns a
      :class:`Verdict`. Production wires this to ``shorts-supervisor``
      fan-out; tests pass ``MagicMock``.
    * ``asset_sourcer_invoker`` takes a prompt and returns a stock still
      :class:`Path`. Used by the ken-burns Fallback helper.
    """

    def __init__(
        self,
        session_id: str,
        state_root: Path = Path("state"),
        failures_path: Path = Path(".claude/failures/orchestrator.md"),
        max_retries_per_gate: int = 3,
        kling_adapter: KlingI2VAdapter | None = None,
        runway_adapter: RunwayI2VAdapter | None = None,
        typecast_adapter: TypecastAdapter | None = None,
        elevenlabs_adapter: ElevenLabsAdapter | None = None,
        shotstack_adapter: ShotstackAdapter | None = None,
        producer_invoker: Callable[[str, str, dict], dict] | None = None,
        supervisor_invoker: Callable[[GateName, dict], Verdict] | None = None,
        asset_sourcer_invoker: Callable[[str], Path] | None = None,
        nanobanana_adapter: NanoBananaAdapter | None = None,
        ken_burns_adapter: KenBurnsLocalAdapter | None = None,
    ) -> None:
        self.session_id = session_id
        self.state_root = Path(state_root)
        self.failures_path = Path(failures_path)
        self.max_retries = max_retries_per_gate

        # Checkpointer + GateGuard (Plan 03 + Plan 04).
        self.checkpointer = Checkpointer(self.state_root)
        self.gate_guard = GateGuard(self.checkpointer, session_id)

        # CircuitBreakers per external service (D-6 defaults 3 / 300).
        # 5 Phase-5 + 4 Phase-9.1 (REQ-091-01/02/04) = 9 breakers.
        _mk_breaker = lambda n: CircuitBreaker(n, max_failures=3, cooldown_seconds=300)  # noqa: E731
        self.kling_breaker = _mk_breaker("kling")
        self.runway_breaker = _mk_breaker("runway")
        self.typecast_breaker = _mk_breaker("typecast")
        self.elevenlabs_breaker = _mk_breaker("elevenlabs")
        self.shotstack_breaker = _mk_breaker("shotstack")
        self.nanobanana_breaker = _mk_breaker("nanobanana")
        self.ken_burns_breaker = _mk_breaker("ken_burns")
        self.claude_producer_breaker = _mk_breaker("claude_producer")
        self.claude_supervisor_breaker = _mk_breaker("claude_supervisor")

        # Adapters (injected for tests, constructed from env otherwise).
        # Missing env for an adapter is logged + slot = injected (usually None)
        # so mock-based test harnesses construct cleanly; real runs that
        # dispatch to a missing adapter raise at use-site (D-05 동일 패턴;
        # D-06 adapter internals untouched; §Line Budget: net -5 on block).
        def _try_adapter(name, build, injected, hint):
            try:
                return build()
            except (ValueError, KenBurnsUnavailable) as err:
                suffix = f" — {hint}" if hint else ""
                logger.warning("[pipeline] %s adapter 미초기화 (대표님%s): %s", name, suffix, err)
                return injected

        self.kling      = kling_adapter      or _try_adapter("kling",      lambda: KlingI2VAdapter(circuit_breaker=self.kling_breaker),           kling_adapter,      "KLING_API_KEY / FAL_KEY 없음")
        self.runway     = runway_adapter     or _try_adapter("runway",     lambda: RunwayI2VAdapter(circuit_breaker=self.runway_breaker),         runway_adapter,     "RUNWAY_API_KEY 없음")
        self.typecast   = typecast_adapter   or _try_adapter("typecast",   lambda: TypecastAdapter(circuit_breaker=self.typecast_breaker),       typecast_adapter,   "TYPECAST_API_KEY 없음")
        self.elevenlabs = elevenlabs_adapter or _try_adapter("elevenlabs", lambda: ElevenLabsAdapter(circuit_breaker=self.elevenlabs_breaker),   elevenlabs_adapter, "ELEVENLABS_API_KEY 없음")
        self.shotstack  = shotstack_adapter  or _try_adapter("shotstack",  lambda: ShotstackAdapter(circuit_breaker=self.shotstack_breaker),     shotstack_adapter,  "SHOTSTACK_API_KEY 없음, Phase 9.1 ken_burns 로컬 대체")
        self.nanobanana = nanobanana_adapter or _try_adapter("nanobanana", lambda: NanoBananaAdapter(circuit_breaker=self.nanobanana_breaker),   nanobanana_adapter, "GOOGLE_API_KEY 없음")
        self.ken_burns  = ken_burns_adapter  or _try_adapter("ken_burns",  lambda: KenBurnsLocalAdapter(circuit_breaker=self.ken_burns_breaker), ken_burns_adapter,  "ffmpeg 확인 필요")

        # Voice-first assembly primitive (Plan 05).
        self.timeline = VoiceFirstTimeline()

        # Invokers — 9.1 REQ-091-01 Claude Agent SDK wiring.
        # Tests pass MagicMock; production constructs SDK-backed defaults.
        _agents_root = Path(".claude/agents")
        self.producer_invoker = producer_invoker or make_default_producer_invoker(
            agent_dir_root=_agents_root / "producers",
            circuit_breaker=self.claude_producer_breaker,
        )
        self.supervisor_invoker = (
            supervisor_invoker
            or make_default_supervisor_invoker(
                agent_dir=_agents_root / "supervisor" / "shorts-supervisor",
                circuit_breaker=self.claude_supervisor_breaker,
            )
        )
        _registry_path = Path("assets/characters/registry.json")
        _registry = (
            CharacterRegistry(_registry_path).load()
            if _registry_path.exists()
            else None
        )
        self.asset_sourcer_invoker = (
            asset_sourcer_invoker
            or make_default_asset_sourcer(
                nanobanana_adapter=self.nanobanana,
                character_registry=_registry,
            )
        )

        # Per-run context.
        self.ctx = GateContext(session_id=session_id)

    # ===================================================================
    # Entry point
    # ===================================================================

    def run(self) -> dict:
        """Execute the pipeline from the current resume point to COMPLETE.

        Protocol:
            1. Consult Checkpointer for highest saved ``gate_index``.
            2. Rebuild ``GateGuard.dispatched`` from disk so already-done
               gates do not re-run (ORCH-05 resume semantics).
            3. Iterate operational gates in IntEnum order, calling each
               ``_run_<gate>`` method. Skip any gate already in the
               dispatched set.
            4. On the final operational gate (MONITOR) dispatch, run
               ``_transition_to_complete`` which raises
               :class:`IncompleteDispatch` if any operational gate is
               still missing.

        Returns a summary dict for the CLI / caller.
        """

        logger.info("[run] session=%s resume_check", self.session_id)
        last_idx = self.checkpointer.resume(self.session_id)
        if last_idx >= 0:
            # Rebuild the dispatched set from the filesystem so a restarted
            # pipeline does not redo GATEs that were already persisted.
            for name in self.checkpointer.dispatched_gates(self.session_id):
                try:
                    self.gate_guard._dispatched.add(GateName[name])
                except KeyError:
                    # Unknown gate name — skip defensively. The filesystem
                    # is a dev-facing artifact, not a hard contract.
                    logger.warning("[run] unknown gate name on disk: %s", name)
            logger.info("[run] resuming from gate_index=%d", last_idx)

        operational = [
            g for g in GateName if g not in (GateName.IDLE, GateName.COMPLETE)
        ]
        for gate in operational:
            if gate in self.gate_guard.dispatched:
                logger.info("[run] %s already dispatched — skip", gate.name)
                continue
            self.gate_guard.ensure_dependencies(gate)
            method = getattr(self, f"_run_{gate.name.lower()}")
            method(self.ctx)

        # COMPLETE transition (ORCH-04) — raises if any gate missing.
        self._transition_to_complete()
        return {
            "session_id": self.session_id,
            "final_gate": GateName.COMPLETE.name,
            "dispatched_count": len(self.gate_guard.dispatched),
            "fallback_count": len(self.ctx.fallback_indices),
        }

    # ===================================================================
    # 13 operational GATE methods — each follows the canonical pattern:
    #     Producer (via regen loop) -> Supervisor -> GateGuard.dispatch
    # ===================================================================

    def _run_trend(self, ctx: GateContext) -> None:
        """GATE 1 — trend-collector Producer, ins-readability Inspector."""

        output = self._producer_loop(
            GateName.TREND,
            lambda: self.producer_invoker(
                "trend-collector", "TREND", {
                    "session_id": self.session_id,
                    "prior_user_feedback": ctx.config.get("prior_user_feedback"),
                }
            ),
        )
        verdict = self.supervisor_invoker(GateName.TREND, output)
        self.gate_guard.dispatch(GateName.TREND, verdict)
        ctx.artifacts[GateName.TREND] = self._artifact_path(output)

    def _run_niche(self, ctx: GateContext) -> None:
        """GATE 2 — niche-classifier Producer, ins-blueprint-compliance."""

        output = self._producer_loop(
            GateName.NICHE,
            lambda: self.producer_invoker(
                "niche-classifier",
                "NICHE",
                {
                    "trend_artifact": ctx.artifacts.get(GateName.TREND),
                    "prior_user_feedback": ctx.config.get("prior_user_feedback"),
                },
            ),
        )
        verdict = self.supervisor_invoker(GateName.NICHE, output)
        self.gate_guard.dispatch(GateName.NICHE, verdict)
        ctx.artifacts[GateName.NICHE] = self._artifact_path(output)

    def _run_research_nlm(self, ctx: GateContext) -> None:
        """GATE 3 — researcher Producer (NotebookLM RAG wired in Phase 6)."""

        output = self._producer_loop(
            GateName.RESEARCH_NLM,
            lambda: self.producer_invoker(
                "researcher",
                "RESEARCH_NLM",
                {
                    "niche_artifact": ctx.artifacts.get(GateName.NICHE),
                    "prior_user_feedback": ctx.config.get("prior_user_feedback"),
                },
            ),
        )
        verdict = self.supervisor_invoker(GateName.RESEARCH_NLM, output)
        self.gate_guard.dispatch(GateName.RESEARCH_NLM, verdict)
        ctx.artifacts[GateName.RESEARCH_NLM] = self._artifact_path(output)

    def _run_blueprint(self, ctx: GateContext) -> None:
        """GATE 4 — director Producer, blueprint-compliance + timing."""

        output = self._producer_loop(
            GateName.BLUEPRINT,
            lambda: self.producer_invoker(
                "director",
                "BLUEPRINT",
                {
                    "research_artifact": ctx.artifacts.get(GateName.RESEARCH_NLM),
                    "prior_user_feedback": ctx.config.get("prior_user_feedback"),
                },
            ),
        )
        verdict = self.supervisor_invoker(GateName.BLUEPRINT, output)
        self.gate_guard.dispatch(GateName.BLUEPRINT, verdict)
        ctx.artifacts[GateName.BLUEPRINT] = self._artifact_path(output)

    def _run_script(self, ctx: GateContext) -> None:
        """GATE 5 — scripter Producer, narrative/Korean/tone/readability."""

        output = self._producer_loop(
            GateName.SCRIPT,
            lambda: self.producer_invoker(
                "scripter",
                "SCRIPT",
                {
                    "blueprint": ctx.artifacts.get(GateName.BLUEPRINT),
                    "prior_user_feedback": ctx.config.get("prior_user_feedback"),
                },
            ),
        )
        verdict = self.supervisor_invoker(GateName.SCRIPT, output)
        self.gate_guard.dispatch(GateName.SCRIPT, verdict)
        ctx.artifacts[GateName.SCRIPT] = self._artifact_path(output)

    def _run_polish(self, ctx: GateContext) -> None:
        """GATE 6 — script-polisher Producer."""

        output = self._producer_loop(
            GateName.POLISH,
            lambda: self.producer_invoker(
                "script-polisher",
                "POLISH",
                {
                    "script": ctx.artifacts.get(GateName.SCRIPT),
                    "prior_user_feedback": ctx.config.get("prior_user_feedback"),
                },
            ),
        )
        verdict = self.supervisor_invoker(GateName.POLISH, output)
        self.gate_guard.dispatch(GateName.POLISH, verdict)
        ctx.artifacts[GateName.POLISH] = self._artifact_path(output)

    def _run_voice(self, ctx: GateContext) -> None:
        """GATE 7 — Typecast primary, ElevenLabs fallback (AUDIO-01 / D-10)."""

        scenes = self._scenes_from_artifact(ctx.artifacts.get(GateName.POLISH))
        try:
            audio_segments = self.typecast_breaker.call(
                lambda: self.typecast.generate(scenes)
            )
        except CircuitBreakerOpenError:
            logger.warning("[_run_voice] typecast breaker OPEN — falling over to ElevenLabs")
            audio_segments = self.elevenlabs_breaker.call(
                lambda: self.elevenlabs.generate_with_timestamps(scenes)
            )
        ctx.audio_segments = list(audio_segments or [])

        output = {
            "audio_segments": [
                seg.path.as_posix() for seg in ctx.audio_segments
            ],
        }
        verdict = self.supervisor_invoker(GateName.VOICE, output)
        self.gate_guard.dispatch(GateName.VOICE, verdict)
        ctx.artifacts[GateName.VOICE] = output

    def _run_assets(self, ctx: GateContext) -> None:
        """GATE 8 — Kling primary, Runway backup (VIDEO-04 / D-16)."""

        scenes = self._scenes_from_artifact(ctx.artifacts.get(GateName.POLISH))
        video_cuts: list[VideoCut] = []
        for i, scene in enumerate(scenes):
            anchor = Path(
                scene.get("anchor_frame", f"assets/anchor_{i:03d}.png")
            )
            prompt = scene.get("prompt", "")
            duration = int(scene.get("duration_seconds", 5))
            try:
                clip_path = self.kling_breaker.call(
                    lambda p=prompt, a=anchor, d=duration: self.kling.image_to_video(
                        prompt=p, anchor_frame=a, duration_seconds=d
                    )
                )
            except CircuitBreakerOpenError:
                logger.warning(
                    "[_run_assets] kling breaker OPEN — falling over to Runway"
                )
                clip_path = self.runway_breaker.call(
                    lambda p=prompt, a=anchor, d=duration: self.runway.image_to_video(
                        prompt=p, anchor_frame=a, duration_seconds=d
                    )
                )
            video_cuts.append(
                VideoCut(
                    index=i,
                    path=Path(clip_path),
                    duration=float(duration),
                    prompt=prompt,
                    anchor_frame=anchor,
                )
            )
        ctx.video_cuts = video_cuts

        output = {"video_cuts": [c.path.as_posix() for c in video_cuts]}
        verdict = self.supervisor_invoker(GateName.ASSETS, output)
        self.gate_guard.dispatch(GateName.ASSETS, verdict)
        ctx.artifacts[GateName.ASSETS] = output

    def _run_assembly(self, ctx: GateContext) -> None:
        """GATE 9 — VoiceFirstTimeline + 720p Shotstack (ORCH-10 / ORCH-11)."""

        timeline = self.timeline.align(ctx.audio_segments, ctx.video_cuts)
        timeline = self.timeline.insert_transition_shots(timeline)

        # ORCH-11 / D-11: render at 720p BEFORE any upscale attempt.
        render_result = self.shotstack_breaker.call(
            lambda: self.shotstack.render(
                timeline, resolution="hd", aspect_ratio="9:16"
            )
        )
        render_url = (render_result or {}).get("url", "")
        ctx.artifacts[GateName.ASSEMBLY] = Path(render_url) if render_url else None

        # Upscale is a Phase 8 NOOP (ShotstackAdapter.upscale returns
        # {"status": "skipped", ...}). Called AFTER render so the order is
        # observable and enforced by test_low_res_first.test_upscale_after_render.
        self.shotstack.upscale(render_url)

        verdict = self.supervisor_invoker(GateName.ASSEMBLY, render_result)
        artifact = ctx.artifacts[GateName.ASSEMBLY]
        artifact_path = (
            artifact
            if isinstance(artifact, Path) and artifact.exists()
            else None
        )
        self.gate_guard.dispatch(
            GateName.ASSEMBLY, verdict, artifact_path=artifact_path
        )

    def _run_thumbnail(self, ctx: GateContext) -> None:
        """GATE 10 — thumbnail-designer Producer; eligible for Fallback."""

        output = self._producer_loop(
            GateName.THUMBNAIL,
            lambda: self.producer_invoker(
                "thumbnail-designer",
                "THUMBNAIL",
                {
                    "assembly": ctx.artifacts.get(GateName.ASSEMBLY),
                    "prior_user_feedback": ctx.config.get("prior_user_feedback"),
                },
            ),
        )
        verdict = self.supervisor_invoker(GateName.THUMBNAIL, output)
        self.gate_guard.dispatch(GateName.THUMBNAIL, verdict)
        ctx.artifacts[GateName.THUMBNAIL] = self._artifact_path(output)

    def _run_metadata(self, ctx: GateContext) -> None:
        """GATE 11 — metadata-seo Producer."""

        output = self._producer_loop(
            GateName.METADATA,
            lambda: self.producer_invoker(
                "metadata-seo",
                "METADATA",
                {
                    "script": ctx.artifacts.get(GateName.SCRIPT),
                    "prior_user_feedback": ctx.config.get("prior_user_feedback"),
                },
            ),
        )
        verdict = self.supervisor_invoker(GateName.METADATA, output)
        self.gate_guard.dispatch(GateName.METADATA, verdict)
        ctx.artifacts[GateName.METADATA] = self._artifact_path(output)

    def _run_upload(self, ctx: GateContext) -> None:
        """GATE 12 — publisher Producer (YouTube API wiring in Phase 8)."""

        output = self._producer_loop(
            GateName.UPLOAD,
            lambda: self.producer_invoker(
                "publisher",
                "UPLOAD",
                {
                    "assembly": ctx.artifacts.get(GateName.ASSEMBLY),
                    "thumbnail": ctx.artifacts.get(GateName.THUMBNAIL),
                    "metadata": ctx.artifacts.get(GateName.METADATA),
                    "prior_user_feedback": ctx.config.get("prior_user_feedback"),
                },
            ),
        )
        verdict = self.supervisor_invoker(GateName.UPLOAD, output)
        self.gate_guard.dispatch(GateName.UPLOAD, verdict)
        ctx.artifacts[GateName.UPLOAD] = self._artifact_path(output)

    def _run_monitor(self, ctx: GateContext) -> None:
        """GATE 13 — publisher Producer in MONITOR mode (post-upload KPI)."""

        output = self._producer_loop(
            GateName.MONITOR,
            lambda: self.producer_invoker(
                "publisher",
                "MONITOR",
                {
                    "upload_artifact": ctx.artifacts.get(GateName.UPLOAD),
                    "prior_user_feedback": ctx.config.get("prior_user_feedback"),
                },
            ),
        )
        verdict = self.supervisor_invoker(GateName.MONITOR, output)
        self.gate_guard.dispatch(GateName.MONITOR, verdict)
        ctx.artifacts[GateName.MONITOR] = self._artifact_path(output)

    # ===================================================================
    # Regeneration loop + Fallback (D-12 / ORCH-12)
    # ===================================================================

    def _producer_loop(
        self,
        gate: GateName,
        producer_fn: Callable[[], dict],
    ) -> dict:
        """Run the Producer up to ``max_retries`` times.

        On every attempt we call the Producer, then the Supervisor for the
        Inspector fan-out verdict. A ``PASS`` returns the output
        immediately. After ``max_retries`` failures we append to
        ``FAILURES.md`` and either insert a ken-burns Fallback
        (ASSETS / THUMBNAIL gates) or raise :class:`RegenerationExhausted`
        (every other gate). Raising is preferred for gates whose artifact
        is consumed structurally downstream — a silent substitution would
        poison later gates.
        """

        last_output: dict | None = None
        last_verdict: Verdict | None = None
        for retry in range(self.max_retries):
            output = producer_fn()
            last_output = output
            verdict = self.supervisor_invoker(gate, output)
            last_verdict = verdict
            if verdict.result == "PASS":
                return output
            self.ctx.retry_counts[gate] = retry + 1
            logger.warning(
                "[_producer_loop] %s retry %d/%d FAIL",
                gate.name,
                retry + 1,
                self.max_retries,
            )

        # Exhausted — append FAIL record and decide fallback vs raise.
        evidence = last_verdict.evidence if last_verdict else []
        feedback = last_verdict.semantic_feedback if last_verdict else ""
        append_failures(
            self.failures_path,
            self.session_id,
            gate.name,
            evidence,
            feedback,
        )

        if gate in (GateName.ASSETS, GateName.THUMBNAIL):
            return self._insert_fallback(gate, last_output or {})
        raise RegenerationExhausted(
            f"{gate.name} exhausted {self.max_retries} retries"
        )

    def _insert_fallback(
        self, gate: GateName, failed_output: dict
    ) -> dict:
        """ORCH-12 Fallback — ken-burns over static image (ASSETS/THUMBNAIL).

        The ``asset_sourcer_invoker`` callable returns a stock still, then
        :class:`ShotstackAdapter.create_ken_burns_clip` wraps it in a
        pan+scale effect matching the failed cut's duration.
        """

        prompt = failed_output.get("prompt") or "dark detective scene"
        duration_s = float(failed_output.get("duration_s", 5.0))
        fallback = insert_fallback_shot(
            shotstack_adapter=self.shotstack,
            asset_sourcer_invoker=self.asset_sourcer_invoker,
            prompt=prompt,
            duration_s=duration_s,
        )
        # Track fallback index per RESEARCH line 862 for dedup on resume.
        cut_index = failed_output.get(
            "cut_index", len(self.ctx.fallback_indices)
        )
        self.ctx.fallback_indices.append(int(cut_index))
        logger.info(
            "[_insert_fallback] %s ken-burns inserted at cut_index=%d",
            gate.name,
            cut_index,
        )
        return fallback

    # ===================================================================
    # COMPLETE transition (ORCH-04)
    # ===================================================================

    def _transition_to_complete(self) -> None:
        """Enforce verify_all_dispatched, then save the COMPLETE checkpoint.

        Raises :class:`IncompleteDispatch` if any operational gate is
        missing from the dispatched set. The diagnostic list is the
        output of :meth:`GateGuard.missing_for_complete`.
        """

        if not self.gate_guard.verify_all_dispatched():
            missing = self.gate_guard.missing_for_complete()
            raise IncompleteDispatch(
                f"COMPLETE blocked — missing: {[g.name for g in missing]}"
            )
        cp = Checkpoint(
            session_id=self.session_id,
            gate=GateName.COMPLETE.name,
            gate_index=int(GateName.COMPLETE),
            timestamp=make_timestamp(),
            verdict={
                "result": "PASS",
                "score": 100,
                "evidence": [],
                "semantic_feedback": "pipeline complete",
                "inspector_name": "shorts-supervisor",
            },
            artifacts={},
        )
        self.checkpointer.save(cp)

    # ===================================================================
    # Small helpers
    # ===================================================================

    @staticmethod
    def _artifact_path(output: dict | None) -> Path | None:
        """Extract ``artifact_path`` from a Producer output dict, if present."""

        if not output:
            return None
        raw = output.get("artifact_path")
        if raw in (None, ""):
            return None
        return Path(raw) if not isinstance(raw, Path) else raw

    @staticmethod
    def _scenes_from_artifact(artifact: Any) -> list[dict]:
        """Coerce a POLISH-gate artifact into a list of scene dicts.

        The artifact may be:
            - a list of dicts (direct scene list from polished script),
            - a dict with a ``"scenes"`` key,
            - ``None`` / any other shape → empty list.
        """

        if isinstance(artifact, list):
            return [s for s in artifact if isinstance(s, dict)]
        if isinstance(artifact, dict):
            scenes = artifact.get("scenes")
            if isinstance(scenes, list):
                return [s for s in scenes if isinstance(s, dict)]
        return []


# ===========================================================================
# CLI entry point
# ===========================================================================


def main(argv: list[str] | None = None) -> int:
    """Thin CLI wrapper for ops / ad-hoc runs.

    Production use wires Phase 4 harness invokers via constructor args;
    this CLI is primarily for smoke tests. ``--session-id`` is required
    so the Checkpointer can scope ``state/<session_id>/`` correctly.
    """

    parser = argparse.ArgumentParser(
        description="Phase 5 ShortsPipeline — 13 operational GATE orchestrator"
    )
    parser.add_argument(
        "--session-id", required=False, default=None,
        help="Session identifier (default: yyyyMMdd_HHMMSS auto-generated)",
    )
    parser.add_argument(
        "--state-root",
        default="state",
        help="Checkpointer state directory (default: state)",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        help="Python logging level (default: INFO)",
    )
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=args.log_level,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    session_id = args.session_id or datetime.now().strftime("%Y%m%d_%H%M%S")
    pipeline = ShortsPipeline(
        session_id=session_id,
        state_root=Path(args.state_root),
    )
    result = pipeline.run()
    logger.info("[main] result=%s", result)
    return 0


# Module-level assertion surface so downstream importers can see the
# operational gate count without instantiating the class (used by
# hc_checks HC-10 in Plan 08). 13 keys, one per operational GATE — exactly
# matches GATE_DEPS minus IDLE and COMPLETE.
assert len(GATE_INSPECTORS) == 13, (
    f"GATE_INSPECTORS must cover 13 operational gates, got {len(GATE_INSPECTORS)}"
)
assert set(GATE_INSPECTORS.keys()) == {
    g.name for g in GateName if g not in (GateName.IDLE, GateName.COMPLETE)
}, "GATE_INSPECTORS keys must equal operational GateName names"


__all__ = [
    "GATE_INSPECTORS",
    "GateContext",
    "ShortsPipeline",
    "main",
]


if __name__ == "__main__":
    raise SystemExit(main())
