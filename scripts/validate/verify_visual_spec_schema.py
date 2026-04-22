"""verify_visual_spec_schema — output/<episode>/visual_spec.json 이중 검증 CLI.

Phase 16-04 — REQ-PROD-INT-04.

1. JSON Schema Draft-07 (.planning/phases/16-.../schemas/visual-spec.v1.schema.json)
2. Pydantic VisualSpec (scripts.orchestrator.api.models.VisualSpec)

Exit code:
  0 = PASS (양쪽 모두 통과)
  1 = FAIL (한쪽 이상 실패 or 파일 없음)
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = (
    REPO_ROOT
    / ".planning"
    / "phases"
    / "16-production-integration-option-a"
    / "schemas"
    / "visual-spec.v1.schema.json"
)


def validate_json_schema(data: dict, schema_path: Path) -> tuple[bool, str]:
    """JSON Schema Draft-07 validate. 성공 = (True, '') / 실패 = (False, err)."""
    try:
        import jsonschema
    except ImportError as e:
        return False, f"jsonschema import 실패: {e} — pip install jsonschema"
    try:
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        return False, f"schema 로드 실패 {schema_path}: {e}"
    try:
        jsonschema.validate(data, schema)
    except jsonschema.ValidationError as e:
        return False, f"JSON Schema ValidationError: {e.message} (path: {list(e.path)})"
    return True, ""


def validate_pydantic(data: dict) -> tuple[bool, str]:
    """Pydantic VisualSpec model_validate. 성공 = (True, '') / 실패 = (False, err)."""
    if str(REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(REPO_ROOT))
    try:
        from scripts.orchestrator.api.models import VisualSpec  # type: ignore
    except ImportError as e:
        return False, f"VisualSpec import 실패: {e}"
    try:
        VisualSpec.model_validate(data)
    except Exception as e:  # pydantic.ValidationError 및 기타 모든 검증 실패
        return False, f"Pydantic VisualSpec FAIL: {e}"
    return True, ""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Phase 16-04 visual_spec.json dual validator "
        "(JSON Schema Draft-07 + Pydantic VisualSpec)"
    )
    parser.add_argument(
        "--spec",
        type=Path,
        required=True,
        help="visual_spec.json 경로",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="경고도 에러 취급 (현재 미사용, 향후 확장용)",
    )
    args = parser.parse_args(argv)

    if not args.spec.exists():
        print(
            f"[verify_visual_spec_schema] 파일 미존재: {args.spec}",
            file=sys.stderr,
        )
        return 1
    try:
        data = json.loads(args.spec.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(
            f"[verify_visual_spec_schema] JSON parse 실패: {e}",
            file=sys.stderr,
        )
        return 1

    # 1. JSON Schema
    ok, err = validate_json_schema(data, SCHEMA_PATH)
    if not ok:
        print(
            f"[verify_visual_spec_schema] JSON Schema FAIL: {err}",
            file=sys.stderr,
        )
        return 1
    print("[verify_visual_spec_schema] JSON Schema Draft-07 PASS")

    # 2. Pydantic
    ok, err = validate_pydantic(data)
    if not ok:
        print(
            f"[verify_visual_spec_schema] {err}",
            file=sys.stderr,
        )
        return 1
    print("[verify_visual_spec_schema] Pydantic VisualSpec PASS")

    return 0


if __name__ == "__main__":
    sys.exit(main())
