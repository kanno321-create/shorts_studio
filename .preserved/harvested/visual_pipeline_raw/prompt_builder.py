"""Prompt builder for visual pipeline scene generation."""

REQUIRED_ELEMENTS = {
    "camera_type",
    "camera_angle",
    "subject_action",
    "environment",
    "dynamic_element",
}

SHOT_TYPES = ["WIDE SHOT", "MEDIUM SHOT", "CLOSE-UP"]

NEGATIVE_PROMPT = (
    "static character, frozen pose, only camera movement, "
    "camera-only motion, motionless character"
)

ACTION_VERBS = [
    "running", "snapping", "lunging", "dragging", "swimming",
    "hunting", "feeding", "striking", "charging", "diving",
    "walking", "crawling", "leaping", "attacking", "fleeing",
    "stalking", "pouncing", "grabbing", "chasing", "darting",
]


def build_scene_prompt(
    shot_type: str,
    camera_type: str,
    camera_angle: str,
    subject_action: str,
    environment: str,
    dynamic_element: str,
    reference_desc: str = "",
) -> str:
    """Build a structured scene prompt from visual elements.

    Args:
        shot_type: One of SHOT_TYPES.
        camera_type: Camera hardware description.
        camera_angle: Camera angle/perspective.
        subject_action: What the subject is doing (must contain action verb).
        environment: Scene environment description.
        dynamic_element: Dynamic visual element in the scene.
        reference_desc: Optional reference image description.

    Returns:
        Formatted scene prompt string.

    Raises:
        ValueError: If shot_type is invalid or any required element is empty.
    """
    if shot_type not in SHOT_TYPES:
        raise ValueError(
            f"Invalid shot_type '{shot_type}'. Must be one of {SHOT_TYPES}"
        )

    elements = {
        "camera_type": camera_type,
        "camera_angle": camera_angle,
        "subject_action": subject_action,
        "environment": environment,
        "dynamic_element": dynamic_element,
    }
    for name, value in elements.items():
        if not value or not value.strip():
            raise ValueError(f"Required element '{name}' cannot be empty")

    reference_clause = ""
    if reference_desc and reference_desc.strip():
        reference_clause = f" Same {reference_desc} from reference image."

    prompt = (
        f"{shot_type}: Shot on {camera_type}, {camera_angle}."
        f"{reference_clause}"
        f" {subject_action} {environment} {dynamic_element}"
    )

    word_count = len(prompt.split())
    assert word_count >= 15, (
        f"Prompt word count {word_count} is below minimum 15"
    )

    return prompt


def validate_prompt_has_action(prompt: str) -> bool:
    """Validate that the prompt contains at least one recognized action verb.

    Args:
        prompt: The scene prompt string to validate.

    Returns:
        True if at least one action verb is found.

    Raises:
        ValueError: If no action verb is found in the prompt.
    """
    prompt_lower = prompt.lower()
    for verb in ACTION_VERBS:
        if verb in prompt_lower:
            return True
    raise ValueError(
        f"Prompt lacks action verbs. Must contain at least one of: {ACTION_VERBS}"
    )
