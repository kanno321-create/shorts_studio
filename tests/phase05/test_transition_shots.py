"""Phase 5 Plan 05 — insert_transition_shots() cadence + template tests.

Covers:
    - VIDEO-03 / D-15: transition every Nth cut except last, 3 templates
    - RNG determinism with fixed seed (so tests are reproducible)
    - Edge cases: empty, 2-cut, 3-cut (last-is-last), 4-cut, 6-cut, 7-cut
"""
from __future__ import annotations

from pathlib import Path

from scripts.orchestrator.voice_first_timeline import (
    TimelineEntry,
    TransitionEntry,
    VoiceFirstTimeline,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _entry(i: int) -> TimelineEntry:
    """TimelineEntry placed contiguously on a 5s grid."""
    return TimelineEntry(
        start=i * 5.0,
        end=(i + 1) * 5.0,
        clip_path=Path(f"cut_{i}.mp4"),
        speed=1.0,
        audio_path=Path(f"aud_{i}.mp3"),
    )


# ---------------------------------------------------------------------------
# Cadence — correct transition count at each timeline length
# ---------------------------------------------------------------------------


def test_empty_timeline_returns_empty():
    t = VoiceFirstTimeline()
    assert t.insert_transition_shots([]) == []


def test_two_cuts_no_transitions():
    t = VoiceFirstTimeline(rng_seed=42)
    out = t.insert_transition_shots([_entry(0), _entry(1)])
    assert len(out) == 2
    assert all(isinstance(x, TimelineEntry) for x in out)


def test_three_cuts_no_transitions_because_third_is_last():
    # i=2 (3rd cut): (i+1) % 3 == 0 is True, but is_last is True -> skip.
    t = VoiceFirstTimeline(rng_seed=42)
    out = t.insert_transition_shots([_entry(0), _entry(1), _entry(2)])
    transitions = [x for x in out if isinstance(x, TransitionEntry)]
    assert len(transitions) == 0


def test_four_cuts_one_transition_after_index_2():
    # i=2: is_last=False, (i+1)%3==0 -> insert. i=3: (i+1)%3 != 0.
    t = VoiceFirstTimeline(rng_seed=42)
    out = t.insert_transition_shots([_entry(i) for i in range(4)])
    transitions = [x for x in out if isinstance(x, TransitionEntry)]
    assert len(transitions) == 1
    assert transitions[0].after_index == 2


def test_six_cuts_one_transition():
    # i=2: insert. i=5: (i+1)%3==0 but is_last=True -> skip.
    t = VoiceFirstTimeline(rng_seed=42)
    out = t.insert_transition_shots([_entry(i) for i in range(6)])
    transitions = [x for x in out if isinstance(x, TransitionEntry)]
    assert len(transitions) == 1


def test_seven_cuts_two_transitions():
    # i=2: insert. i=5: (i+1)%3==0 and is_last=False -> insert.
    t = VoiceFirstTimeline(rng_seed=42)
    out = t.insert_transition_shots([_entry(i) for i in range(7)])
    transitions = [x for x in out if isinstance(x, TransitionEntry)]
    assert len(transitions) == 2
    assert [tr.after_index for tr in transitions] == [2, 5]


def test_transitions_inserted_between_cuts_not_before_first():
    t = VoiceFirstTimeline(rng_seed=42)
    out = t.insert_transition_shots([_entry(i) for i in range(10)])
    # First item in the output must be a primary cut, never a transition.
    assert isinstance(out[0], TimelineEntry)


# ---------------------------------------------------------------------------
# Template + duration constraints (VIDEO-03)
# ---------------------------------------------------------------------------


def test_transition_templates_only_from_three():
    t = VoiceFirstTimeline(rng_seed=42)
    out = t.insert_transition_shots([_entry(i) for i in range(10)])
    allowed = {"prop_closeup", "silhouette", "background_wipe"}
    for x in out:
        if isinstance(x, TransitionEntry):
            assert x.template in allowed


def test_transition_duration_in_range():
    t = VoiceFirstTimeline(rng_seed=42)
    out = t.insert_transition_shots([_entry(i) for i in range(10)])
    for x in out:
        if isinstance(x, TransitionEntry):
            assert 0.5 <= x.duration <= 1.0


def test_transition_after_index_matches_insertion_point():
    t = VoiceFirstTimeline(rng_seed=42)
    # For a 7-cut timeline, transitions land after indices 2 and 5.
    out = t.insert_transition_shots([_entry(i) for i in range(7)])
    # Scan the flat output: every TransitionEntry must follow a TimelineEntry
    # whose index equals its after_index.
    for i, item in enumerate(out):
        if isinstance(item, TransitionEntry):
            prev = out[i - 1]
            assert isinstance(prev, TimelineEntry)
            # TimelineEntry has start = idx*5; recover idx from start.
            assert int(prev.start / 5.0) == item.after_index


# ---------------------------------------------------------------------------
# RNG determinism — same seed must produce the same template sequence
# ---------------------------------------------------------------------------


def test_determinism_with_same_seed():
    t1 = VoiceFirstTimeline(rng_seed=42)
    t2 = VoiceFirstTimeline(rng_seed=42)
    out1 = t1.insert_transition_shots([_entry(i) for i in range(10)])
    out2 = t2.insert_transition_shots([_entry(i) for i in range(10)])
    templates1 = [x.template for x in out1 if isinstance(x, TransitionEntry)]
    templates2 = [x.template for x in out2 if isinstance(x, TransitionEntry)]
    assert templates1 == templates2


def test_different_seeds_can_differ():
    t1 = VoiceFirstTimeline(rng_seed=1)
    t2 = VoiceFirstTimeline(rng_seed=2)
    # 50-cut timeline yields many transitions; divergence is overwhelmingly likely.
    out1 = t1.insert_transition_shots([_entry(i) for i in range(50)])
    out2 = t2.insert_transition_shots([_entry(i) for i in range(50)])
    templates1 = [x.template for x in out1 if isinstance(x, TransitionEntry)]
    templates2 = [x.template for x in out2 if isinstance(x, TransitionEntry)]
    # Either at least one divergence exists, or the sequences are too short
    # to meaningfully compare (fewer than 5 transitions). The latter only
    # happens when cadence is misconfigured.
    assert templates1 != templates2 or len(templates1) < 5


# ---------------------------------------------------------------------------
# Class constants — stability guard so downstream plans can rely on them
# ---------------------------------------------------------------------------


def test_transition_every_n_constant_is_three():
    assert VoiceFirstTimeline.TRANSITION_EVERY_N_CUTS == 3


def test_transition_templates_constant_has_three_members():
    assert len(VoiceFirstTimeline.TRANSITION_TEMPLATES) == 3
    assert set(VoiceFirstTimeline.TRANSITION_TEMPLATES) == {
        "prop_closeup",
        "silhouette",
        "background_wipe",
    }


def test_transition_duration_constants():
    assert VoiceFirstTimeline.MIN_TRANSITION_DURATION == 0.5
    assert VoiceFirstTimeline.MAX_TRANSITION_DURATION == 1.0
