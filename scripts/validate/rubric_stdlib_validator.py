"""Stdlib-only JSON Schema draft-07 subset validator for rubric-schema.json.

Validates against the subset of draft-07 used by:
- .claude/agents/_shared/rubric-schema.json
- .claude/agents/_shared/supervisor-rubric-schema.json

Supported keywords: type (object/string/integer/array/boolean), required, properties,
additionalProperties=false, enum, minimum, maximum, minItems, maxItems, minLength,
maxLength, pattern (via `re`), items.

NO external jsonschema dependency. Live-tested on Python 3.11.9.

Deviation note [Rule 2 - critical functionality]: extended beyond RESEARCH.md §8.2
to also walk `properties.items` (for evidence[] items validation) and `additionalProperties=false`
(schema uses it). Rationale: without these the Task 3 <behavior> "evidence not array" would
pass vacuously, and additionalProperties would silently ignore typos. These are required for
the schema to actually enforce its contract.
"""
from __future__ import annotations

import re
from typing import Any


def _check_string_constraints(key: str, value: str, sub: dict) -> list[str]:
    errors: list[str] = []
    if "minLength" in sub and len(value) < sub["minLength"]:
        errors.append(f"{key}: string shorter than minLength {sub['minLength']}")
    if "maxLength" in sub and len(value) > sub["maxLength"]:
        errors.append(f"{key}: string longer than maxLength {sub['maxLength']}")
    if "pattern" in sub:
        try:
            if not re.search(sub["pattern"], value):
                errors.append(f"{key}: value {value!r} does not match pattern {sub['pattern']!r}")
        except re.error as e:
            errors.append(f"{key}: invalid regex pattern in schema ({e})")
    return errors


def _validate_value(key: str, value: Any, sub: dict) -> list[str]:
    """Validate a single value against a property sub-schema."""
    errors: list[str] = []
    sub_type = sub.get("type")

    # Enum check (applies regardless of type)
    if "enum" in sub and value not in sub["enum"]:
        errors.append(f"{key}: value {value!r} not in enum {sub['enum']}")

    if sub_type == "string":
        if not isinstance(value, str):
            errors.append(f"{key}: expected string")
        else:
            errors.extend(_check_string_constraints(key, value, sub))
    elif sub_type == "integer":
        # bool is subclass of int in Python; explicitly exclude
        if not isinstance(value, int) or isinstance(value, bool):
            errors.append(f"{key}: expected integer")
        else:
            if "minimum" in sub and value < sub["minimum"]:
                errors.append(f"{key}: below minimum")
            if "maximum" in sub and value > sub["maximum"]:
                errors.append(f"{key}: above maximum")
    elif sub_type == "array":
        if not isinstance(value, list):
            errors.append(f"{key}: expected array")
        else:
            if "minItems" in sub and len(value) < sub["minItems"]:
                errors.append(f"{key}: array has {len(value)} items < minItems {sub['minItems']}")
            if "maxItems" in sub and len(value) > sub["maxItems"]:
                errors.append(f"{key}: array has {len(value)} items > maxItems {sub['maxItems']}")
            items_schema = sub.get("items")
            if isinstance(items_schema, dict):
                for i, item in enumerate(value):
                    errors.extend(_validate_value(f"{key}[{i}]", item, items_schema))
    elif sub_type == "object":
        if not isinstance(value, dict):
            errors.append(f"{key}: expected object")
        else:
            # Nested object validation via recursive call
            nested_errors = validate_rubric(value, sub)
            errors.extend(f"{key}.{e}" for e in nested_errors)
    elif sub_type == "boolean":
        if not isinstance(value, bool):
            errors.append(f"{key}: expected boolean")
    # No sub-type -> permissive (e.g. $ref we don't resolve here)

    return errors


def validate_rubric(doc: Any, schema: dict) -> list[str]:
    """Validate a document against a draft-07 (subset) schema.

    Returns a list of error strings. Empty list == valid.
    """
    errors: list[str] = []
    s_type = schema.get("type")

    if s_type == "object":
        if not isinstance(doc, dict):
            return ["not an object"]

        # required
        for req in schema.get("required", []):
            if req not in doc:
                errors.append(f"missing required field: {req}")

        # additionalProperties=false
        if schema.get("additionalProperties") is False:
            allowed = set(schema.get("properties", {}).keys())
            for k in doc.keys():
                if k not in allowed:
                    errors.append(f"additional property not allowed: {k}")

        # each property
        for k, sub in schema.get("properties", {}).items():
            if k not in doc:
                continue
            errors.extend(_validate_value(k, doc[k], sub))

    elif s_type == "array":
        if not isinstance(doc, list):
            return ["not an array"]
        if "minItems" in schema and len(doc) < schema["minItems"]:
            errors.append(f"array has {len(doc)} items < minItems {schema['minItems']}")
        if "maxItems" in schema and len(doc) > schema["maxItems"]:
            errors.append(f"array has {len(doc)} items > maxItems {schema['maxItems']}")
        items_schema = schema.get("items")
        if isinstance(items_schema, dict):
            for i, item in enumerate(doc):
                errors.extend(_validate_value(f"[{i}]", item, items_schema))

    else:
        # Top-level primitive — delegate to value validator
        errors.extend(_validate_value("<root>", doc, schema))

    return errors
