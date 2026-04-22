"""Shot type planner with interleaved allocation."""


def plan_shot_types(num_scenes: int) -> list:
    """Allocate shot types across scenes with ~30% WIDE, ~40% MEDIUM, ~30% CLOSE-UP.

    Uses interleaving to prevent consecutive same-type shots.

    Args:
        num_scenes: Number of scenes to plan shots for.

    Returns:
        List of shot type strings.
    """
    if num_scenes <= 0:
        return []
    if num_scenes == 1:
        return ["MEDIUM SHOT"]

    wide_count = max(1, round(num_scenes * 0.3))
    closeup_count = max(1, round(num_scenes * 0.3))
    medium_count = num_scenes - wide_count - closeup_count
    if medium_count < 1:
        medium_count = 1
        if wide_count + closeup_count + medium_count > num_scenes:
            if wide_count > closeup_count:
                wide_count = num_scenes - medium_count - closeup_count
            else:
                closeup_count = num_scenes - medium_count - wide_count

    pool = (
        ["WIDE SHOT"] * wide_count
        + ["MEDIUM SHOT"] * medium_count
        + ["CLOSE-UP"] * closeup_count
    )

    # Interleave to avoid consecutive duplicates
    result = []
    buckets = {
        "WIDE SHOT": wide_count,
        "MEDIUM SHOT": medium_count,
        "CLOSE-UP": closeup_count,
    }

    for _ in range(num_scenes):
        last = result[-1] if result else None
        # Pick the type with the most remaining that isn't the same as last
        candidates = sorted(
            buckets.items(), key=lambda x: -x[1]
        )
        chosen = None
        for shot_type, count in candidates:
            if count > 0 and shot_type != last:
                chosen = shot_type
                break
        if chosen is None:
            # Fallback: forced to pick same as last (shouldn't happen with valid input)
            for shot_type, count in candidates:
                if count > 0:
                    chosen = shot_type
                    break
        if chosen is None:
            break
        result.append(chosen)
        buckets[chosen] -= 1

    return result
