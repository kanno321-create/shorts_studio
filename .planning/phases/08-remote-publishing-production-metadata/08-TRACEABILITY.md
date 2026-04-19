---
phase: 8
slug: remote-publishing-production-metadata
gathered: 2026-04-19
requirements_count: 8
success_criteria_count: 6
---

# Phase 8 — Traceability Matrix

**Phase:** Remote + Publishing + Production Metadata
**Plans:** 8 (08-01 through 08-08)
**Requirements:** PUB-01..05 + REMOTE-01..03 (8 total)
**Success Criteria:** SC1..SC6 (6 total)
**Anchors:** 3 permanent (AI disclosure AST + endScreen grep 0 + selenium grep 0)
**Research Corrections:** 2 applied (Pitfall 6 + Pitfall 7)

Every REQ ID from the Phase 8 scope appears below with at least one
passing test file and at least one acceptance SC. No orphans.

---

## REQ × Source × Test × SC Matrix

| REQ ID | Spec (short) | Primary Source File(s) | Primary Test File(s) | SC |
|--------|--------------|-------------------------|----------------------|----|
| PUB-01 | AI disclosure 토글 자동 ON (hardcoded `containsSyntheticMedia=True`) | scripts/publisher/ai_disclosure.py `build_status_block` + `assert_synthetic_media_true` | tests/phase08/test_ai_disclosure_anchor.py (**ANCHOR A** — AST + grep 0 `False` hits) | SC3 |
| PUB-02 | YouTube Data API v3 공식 사용 (Selenium 영구 금지) | scripts/publisher/youtube_uploader.py + scripts/publisher/oauth.py | tests/phase08/test_uploader_mocked_e2e.py + test_oauth_installed_flow.py + test_token_refresh.py + test_no_selenium_anchor.py (**ANCHOR C**) | SC3, SC6 |
| PUB-03 | 48시간+ 랜덤 간격 + KST 피크 시간 enforcement | scripts/publisher/publish_lock.py + scripts/publisher/kst_window.py | tests/phase08/test_publish_lock_48h.py + test_kst_window_weekday.py + test_kst_window_weekend.py | SC4 |
| PUB-04 | production_metadata 4-field 첨부 (Reused Content 증명) | scripts/publisher/production_metadata.py `inject_into_description` | tests/phase08/test_production_metadata_schema.py + test_metadata_html_comment.py | SC5 |
| PUB-05 | 핀 댓글 + end-screen subscribe funnel (description CTA 대체) | scripts/publisher/youtube_uploader.py publish funnel block | tests/phase08/test_pinned_comment.py + test_endscreen_nonexistent_anchor.py (**ANCHOR B**) | SC6 |
| REMOTE-01 | GitHub Private 저장소 생성 `kanno321-create/shorts_studio` | scripts/publisher/github_remote.py `create_private_repo` | tests/phase08/test_github_remote_create.py | SC1 |
| REMOTE-02 | `git remote add origin` + `git push -u origin main` | scripts/publisher/github_remote.py `push_to_remote` | tests/phase08/test_github_push_main.py | SC1 |
| REMOTE-03 | naberal_harness v1.0.1 submodule 연결 | scripts/publisher/github_remote.py `add_harness_submodule` | tests/phase08/test_submodule_add.py | SC2 |

**Coverage check:** 8/8 REQs mapped, all 6 SC covered, no orphans.

---

## Success Criteria → Primary Tests

| SC | Focus | REQs | Representative Tests |
|----|-------|------|----------------------|
| SC1 | GitHub mirror + main pushed | REMOTE-01, REMOTE-02 | test_github_remote_create.py (idempotent repo create via `gh api`) + test_github_push_main.py (main rename + `git push -u origin main` subprocess argv + Pitfall 2 anchor) |
| SC2 | naberal_harness submodule | REMOTE-03 | test_submodule_add.py (`git submodule add --depth=1` + `.gitmodules` schema + Pitfall 10 depth-1 anchor) |
| SC3 | AI disclosure + Selenium zero | PUB-01, PUB-02 | test_ai_disclosure_anchor.py (**ANCHOR A** — AST-level `containsSyntheticMedia=True` hardcoded + `False` 0 hits) + test_no_selenium_anchor.py (**ANCHOR C** — grep `selenium`/`webdriver`/`playwright` = 0 in scripts/publisher/) |
| SC4 | 48h+ lock + KST window | PUB-03 | test_publish_lock_48h.py (filesystem lock + jitter) + test_kst_window_weekday.py (20-23 KST) + test_kst_window_weekend.py (12-15 KST) |
| SC5 | production_metadata 4-field | PUB-04 | test_production_metadata_schema.py (script_seed + assets_origin + pipeline_version + checksum sha256) + test_metadata_html_comment.py (`<!-- production_metadata` HTML comment roundtrip) |
| SC6 | Pinned comment + funnel | PUB-05 | test_pinned_comment.py (`commentThreads.insert` payload) + test_endscreen_nonexistent_anchor.py (**ANCHOR B** — grep `captions.insert`/`endScreen`/`end_screen_subscribe_cta` = 0) + test_uploader_mocked_e2e.py (publish 5-gate chain) |

All 6 SC green in `scripts/validate/phase08_acceptance.py` as of 2026-04-19
(`ALL_PASS` marker, exit 0).

---

## Plan → REQ → Commit Audit Trail

| Plan | Wave | Primary REQs Addressed | Key Commits |
|------|------|------------------------|-------------|
| 08-01 | W0 | REQ-TEST-infra (scaffold) + CD-02 exceptions | 5fb2d38, 501777d, b53d218, db6063d |
| 08-02 | W1 | REMOTE-01, REMOTE-02, REMOTE-03 | 763cbc1, 97a27b3, ad29325, 429791f |
| 08-03 | W2 | PUB-02 (OAuth 2.0 InstalledAppFlow + refresh) | 95022d4, 9d04c18, a6db395, 7f7beb8 |
| 08-04 | W3 | PUB-01 (ANCHOR A), PUB-03 | 8c2d9bf, dbe0f61, f48ade1, 6d06bee, b601e86, a3809ab, 7d32fcd |
| 08-05 | W4 | PUB-02, PUB-04, PUB-05 (ANCHOR B + ANCHOR C) | 98b4e46, 79e38c5, 51e5332, 8531475, 73c5eb3, 7cb1caa, a9e9ed7 |
| 08-06 | W5 | PUB-01..05 (SMOKE gate — USER APPROVAL) | 63464ca, d9509f8, 5a9a558, f8f378a |
| 08-07 | W6 | ALL (E2E acceptance + 986 regression guard + full-chain mock) | 8b9c790, 6656e07, feaa0f3 |
| 08-08 | W7 | ALL (TRACEABILITY + VALIDATION flip — PHASE GATE) | <this plan's hashes> |

---

## Research Corrections Applied

Phase 8 RESEARCH identified 2 critical falsifications in the original
08-CONTEXT.md Pitfalls 6 and 7. Each is anchored by a Phase 8 test such
that silent drift back to the incorrect form fails loudly.

| # | CONTEXT assertion | Actual API / code | Phase 8 test anchor | Commit |
|---|-------------------|-------------------|---------------------|--------|
| Pitfall 6 | `ai_disclosure.syntheticMedia=True` (custom key) | Canonical YouTube Data API v3 field is `status.containsSyntheticMedia` (2024-10-30). Applied at `scripts/publisher/ai_disclosure.py:build_status_block` → translated at `scripts/publisher/youtube_uploader.py:build_insert_body`. `syntheticMedia` custom key must NOT leak into API payload. | tests/phase08/test_ai_disclosure_anchor.py (**ANCHOR A** — AST-level `containsSyntheticMedia=True` hardcoded guard) + tests/phase08/test_full_publish_chain_mocked.py::test_contains_synthetic_media_true_reaches_body_in_chain (spy asserts `syntheticMedia NOT in status`) | studio@a3809ab + 7cb1caa |
| Pitfall 7 | `end_screen_subscribe_cta: true` + CONTEXT D-09 mentioned `captions.insert` | end-screen is NOT supported by Data API v3 (YouTube Studio UI only). Replaced with description CTA + pinned comment via `commentThreads.insert`. | tests/phase08/test_endscreen_nonexistent_anchor.py (**ANCHOR B** — grep `captions.insert`/`endScreen`/`end_screen_subscribe_cta` = 0 in scripts/publisher/) + tests/phase08/test_pinned_comment.py (`commentThreads.insert` payload) | studio@73c5eb3 + 51e5332 |

### Additional Permanent Anchor (Hook-layer enforcement)

- **ANCHOR C** — Redundant Hook-layer guard beyond Phase 5 `deprecated_patterns.json`:
  zero `selenium` / `webdriver` / `playwright` imports in
  `scripts/publisher/**/*.py`. grep + AST verified by
  `tests/phase08/test_no_selenium_anchor.py` (PUB-02 SC3).
  Commit: studio@73c5eb3.

---

## Enforcement Tests

Automation that guards this matrix from silent drift:

- `tests/phase08/test_traceability_matrix.py` — asserts every REQ in
  `PHASE8_REQS` is referenced as a table row header in
  `08-TRACEABILITY.md`, every SC1..SC6 label is present, all 3 anchors
  (A/B/C) are documented, both Pitfall 6/7 corrections are acknowledged,
  all 8 plan rows appear in the audit trail, and no orphan plan numbers
  beyond 08-08 have crept in.
- `tests/phase08/test_phase08_acceptance.py` — asserts
  `scripts/validate/phase08_acceptance.py` exits 0 with all 6 SC labels
  PASS and final `Phase 8 acceptance: ALL_PASS` marker present.
- `tests/phase08/test_regression_986_green.py` — D-23 regression
  invariant: Phase 4 + 5 + 6 + 7 baseline (986) preserved end-to-end.

---

## Plan Summary

| Plan | Tasks | Artifacts | Gate |
|------|-------|-----------|------|
| 08-01 | 3 | tests/phase08/ scaffold + MockYouTube + MockGitHub + exceptions | Wave 0 |
| 08-02 | 3 | github_remote.py (create_private_repo + push_to_remote + add_harness_submodule) + Pitfall 2/10 anchors | Wave 1 |
| 08-03 | 2 | oauth.py InstalledAppFlow + refresh token roundtrip + disk persistence | Wave 2 |
| 08-04 | 4 | publish_lock.py + kst_window.py + ai_disclosure.py + ANCHOR A | Wave 3 |
| 08-05 | 6 | production_metadata.py + youtube_uploader.py + ANCHOR B + ANCHOR C + pinned comment | Wave 4 |
| 08-06 | 2 | smoke_test.py CLI + test_smoke_cleanup.py + real YouTube 2-upload evidence | Wave 5 (USER APPROVAL) |
| 08-07 | 2 | phase08_acceptance.py + test_phase08_acceptance wrapper + test_regression_986_green + test_full_publish_chain_mocked | Wave 6 |
| 08-08 | 2 | 08-TRACEABILITY.md + test_traceability_matrix.py + 08-VALIDATION.md flip | Wave 7 gate |

**Totals:** 8 plans, 24 tasks, 170+ Phase 8 tests, 3 anchors permanent
(A/B/C), 2 Research Corrections anchored (Pitfall 6 + 7), 986 regression
preserved.

Phase 8 status: shippable when all listed tests are green.

---

**Phase 8 shipped:** 2026-04-19 — 8/8 REQs complete · 6/6 SC PASS · 3 anchors permanent · 986 + Phase 8 regression green.

*Generated: 2026-04-19 (Plan 08-08 Wave 7 — Phase 8 final verification)*
