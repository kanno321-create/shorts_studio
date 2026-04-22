"""Pronunciation conversion module for Korean TTS.

Applies substitution rules from pronunciation-table.json to text
BEFORE sending to TTS API. Original script.json is never modified (D-04).

Usage:
    from pronunciation import load_pronunciation_table, apply_pronunciation
    rules = load_pronunciation_table("config/pronunciation-table.json")
    converted = apply_pronunciation("NASA가 AI칩 1조 투자", rules)
    # -> "나사가 에이아이칩 일조 투자"
"""
import json
import re
from pathlib import Path


def load_pronunciation_table(path: str) -> list[dict]:
    """Load pronunciation rules from JSON file.

    Args:
        path: Path to pronunciation-table.json

    Returns:
        List of rule dicts with 'pattern', 'replacement', 'category', optional 'regex' keys.

    Raises:
        FileNotFoundError: If path does not exist.
        json.JSONDecodeError: If file is not valid JSON.
    """
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data["rules"]


def apply_pronunciation(text: str, rules: list[dict]) -> str:
    """Apply pronunciation substitution rules to text.

    Rules are applied in order. Each rule is either a literal string
    replacement or a regex substitution (if rule has "regex": true).

    Args:
        text: Original narration text from script.json.
        rules: List of rule dicts from load_pronunciation_table().

    Returns:
        Text with pronunciation substitutions applied.
    """
    for rule in rules:
        pattern = rule["pattern"]
        replacement = rule["replacement"]
        if rule.get("regex", False):
            text = re.sub(pattern, replacement, text)
        else:
            text = text.replace(pattern, replacement)
    return text
