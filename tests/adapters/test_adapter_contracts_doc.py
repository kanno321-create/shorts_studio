"""Phase 14 ADAPT-05 structural validator — adapter_contracts.md 문서 계약.

본 모듈은 `wiki/render/adapter_contracts.md` 의 **구조적 무결성** 만 검증합니다.
문서 내용의 의미론적 정확성 (실제 adapter signature 와의 일치) 은 Wave 2
contract 테스트 (tests/adapters/test_*_contract.py) 가 담당하며, 본 테스트는
다음 축만 다룹니다:

1. 파일 존재.
2. frontmatter 필수 키 (category: render, status: ready, updated: YYYY-MM-DD).
3. Adapter Registry 섹션에 7 adapter (kling_i2v, runway_i2v, veo_i2v, typecast,
   elevenlabs, shotstack, whisperx) 전부 행 존재.
4. 최소 4 개 섹션 헤더 (Adapter Registry, Mock↔Real Deltas, Retry/Fallback,
   Production-Safe Defaults).
5. whisperx 행에 'NOT YET IMPLEMENTED' 명시 (Phase 15+ stub — 14-RESEARCH Open
   Q2 Option A).
6. Contract 테스트 cross-reference 섹션 존재 (3 Wave 2 파일 경로 인용).
7. CLAUDE.md 금기사항 cross-reference (금기 #3/#4 준수 명시).

금기 #2 준수: 미완성 표식 없음 (전수 구현 완료).
금기 #3 준수: 모든 검증 실패는 pytest assert 로 명시.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

pytestmark = pytest.mark.adapter_contract


ADAPTER_NAMES = (
    "kling_i2v",
    "runway_i2v",
    "veo_i2v",
    "typecast",
    "elevenlabs",
    "shotstack",
    "whisperx",
)


@pytest.fixture(scope="module")
def doc_text(repo_root: Path) -> str:
    path = repo_root / "wiki" / "render" / "adapter_contracts.md"
    assert path.exists(), f"ADAPT-05 문서 부재: {path}"
    return path.read_text(encoding="utf-8")


def test_frontmatter_required_keys(doc_text: str):
    """frontmatter 필수 키 (category: render, status: ready, updated: YYYY-MM-DD)
    모두 존재."""
    head = doc_text.split("---", 2)
    assert len(head) >= 3, "frontmatter 구분자 `---` 부재 또는 비정상."
    fm = head[1]
    assert re.search(r"^category:\s*render\b", fm, re.MULTILINE), (
        "frontmatter 'category: render' 누락 — ADAPT-05 doc schema 위반."
    )
    assert re.search(r"^status:\s*ready\b", fm, re.MULTILINE), (
        "frontmatter 'status: ready' 누락 — adapter_contracts.md 는 leaf "
        "contract 문서이므로 MOC-like scaffold/partial 허용되지 않음."
    )
    assert re.search(r"^updated:\s*\d{4}-\d{2}-\d{2}", fm, re.MULTILINE), (
        "frontmatter 'updated: YYYY-MM-DD' 형식 누락."
    )


def test_all_seven_adapters_listed(doc_text: str):
    """7 adapter 이름 (ADAPTER_NAMES) 이 모두 문서에 등장."""
    for name in ADAPTER_NAMES:
        assert name in doc_text, (
            f"adapter '{name}' 누락 — ADAPT-05 spec (14-RESEARCH §D-3) 위반."
        )


def test_min_four_section_headers(doc_text: str):
    """최소 4 개 주요 섹션 헤더 존재 — substring 매칭 허용."""
    required_headers = (
        "Adapter Registry",
        "Mock",              # "Mock ↔ Real Contract Deltas"
        "Retry",             # "Retry / Fallback Rails"
        "Production-Safe Defaults",
    )
    for header in required_headers:
        assert re.search(
            rf"^##\s+.*{re.escape(header)}", doc_text, re.MULTILINE
        ), f"필수 섹션 '{header}' 부재 — ADAPT-05 구조 미충족."


def test_whisperx_stub_labeled(doc_text: str):
    """whisperx 행에 'NOT YET IMPLEMENTED' 라벨 명시 — Phase 15+ 경계."""
    assert "NOT YET IMPLEMENTED" in doc_text, (
        "whisperx stub 라벨 'NOT YET IMPLEMENTED' 부재 — "
        "14-RESEARCH Open Q2 Option A (Phase 15+ stub 유지) 위반."
    )


def test_contract_cross_reference_present(doc_text: str):
    """3 개 Wave 2 contract 테스트 파일 경로가 문서 내 참조됨."""
    expected = (
        "tests/adapters/test_veo_i2v_contract.py",
        "tests/adapters/test_elevenlabs_contract.py",
        "tests/adapters/test_shotstack_contract.py",
    )
    for f in expected:
        assert f in doc_text, (
            f"contract 테스트 교차 참조 누락: {f} — "
            "Phase 14 Plan 03 산출물과의 링크 단절 방지."
        )


def test_forbid_reference_present(doc_text: str):
    """CLAUDE.md 금기사항 (#3 침묵 폴백 / #4 T2V) 준수 명시."""
    assert "금기" in doc_text or "forbid" in doc_text.lower(), (
        "CLAUDE.md 금기사항 cross-reference 부재 — "
        "adapter 가 금기사항을 어떻게 지키는지 문서화 요구."
    )


def test_fault_injection_invariant_documented(doc_text: str):
    """D-3 Phase 7 invariant (allow_fault_injection=False default) 문서화."""
    assert "allow_fault_injection" in doc_text, (
        "D-3 Phase 7 production-safe default invariant "
        "('allow_fault_injection=False') 문서화 누락."
    )
