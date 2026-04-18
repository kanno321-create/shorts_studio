"""Shape regression for af_bank.json — COMPLY-04/05 + AUDIO-04 (Phase 4 Wave 0)."""
from __future__ import annotations

EXPECTED_KEYS = {"af4_voice_clone", "af5_real_face", "af13_kpop"}
CORE_KPOP_ARTISTS = {
    "BTS", "BLACKPINK", "NewJeans", "IVE", "aespa",
    "LE SSERAFIM", "Stray Kids", "SEVENTEEN", "NCT", "TWICE",
}


def test_af_bank_has_3_classes(af_bank):
    data_keys = {k for k in af_bank.keys() if not k.startswith("_")}
    assert data_keys == EXPECTED_KEYS, f"got keys: {data_keys}"


def test_each_class_has_10_plus(af_bank):
    for cls in EXPECTED_KEYS:
        entries = af_bank[cls]
        assert isinstance(entries, list), f"{cls} is not a list"
        assert len(entries) >= 10, f"{cls} has only {len(entries)} entries (need >= 10)"


def test_entries_have_required_fields(af_bank):
    for cls in EXPECTED_KEYS:
        for entry in af_bank[cls]:
            assert "id" in entry, f"{cls} missing 'id' in {entry}"
            assert "expected_verdict" in entry, f"{cls} missing 'expected_verdict' in {entry}"
            assert entry["expected_verdict"] in ("PASS", "FAIL"), (
                f"{cls} bad verdict in {entry}"
            )


def test_af13_includes_core_kpop(af_bank):
    artists = {e.get("artist", "") for e in af_bank["af13_kpop"]}
    hit = CORE_KPOP_ARTISTS & artists
    assert len(hit) >= 5, f"af13 core K-pop coverage only {len(hit)}: {hit}"
