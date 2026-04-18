"""RUB-04: rubric-schema.json stdlib validator tests (Phase 4 Wave 0)."""
from __future__ import annotations


def _valid_rubric():
    return {
        "verdict": "PASS",
        "score": 85,
        "evidence": [],
        "semantic_feedback": "",
    }


def test_valid_rubric_passes(rubric_schema, validate_rubric_fn):
    errs = validate_rubric_fn(_valid_rubric(), rubric_schema)
    assert errs == [], f"unexpected errors: {errs}"


def test_missing_required_field(rubric_schema, validate_rubric_fn):
    doc = _valid_rubric()
    del doc["verdict"]
    errs = validate_rubric_fn(doc, rubric_schema)
    assert any("missing required field: verdict" in e for e in errs), errs


def test_invalid_verdict_enum(rubric_schema, validate_rubric_fn):
    doc = _valid_rubric()
    doc["verdict"] = "MAYBE"
    errs = validate_rubric_fn(doc, rubric_schema)
    assert any("verdict" in e and "not in enum" in e for e in errs), errs


def test_score_above_max(rubric_schema, validate_rubric_fn):
    doc = _valid_rubric()
    doc["score"] = 150
    errs = validate_rubric_fn(doc, rubric_schema)
    assert any("above maximum" in e for e in errs), errs


def test_score_below_min(rubric_schema, validate_rubric_fn):
    doc = _valid_rubric()
    doc["score"] = -1
    errs = validate_rubric_fn(doc, rubric_schema)
    assert any("below minimum" in e for e in errs), errs


def test_evidence_wrong_type(rubric_schema, validate_rubric_fn):
    doc = _valid_rubric()
    doc["evidence"] = "oops-string-instead-of-array"
    errs = validate_rubric_fn(doc, rubric_schema)
    assert any("evidence" in e and "expected array" in e for e in errs), errs
