---
phase: 8
slug: remote-publishing-production-metadata
status: executing
nyquist_compliant: false
wave_0_complete: true
created: 2026-04-19
---

# Phase 8 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.
> Source: 08-RESEARCH.md §Validation Architecture + CONTEXT D-10/D-11 smoke-test gate.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x (stdlib-only helpers, unittest.mock for API stubs) |
| **Config file** | pytest.ini (existing from Phase 5) |
| **Quick run command** | `pytest tests/phase08 -q --no-cov` |
| **Full suite command** | `pytest tests/phase04 tests/phase05 tests/phase06 tests/phase07 tests/phase08 --no-cov` |
| **Estimated runtime** | ~50s (phase08 only) / ~10min (full regression 986 + phase08) |

---

## Sampling Rate

- **After every task commit:** `pytest tests/phase08 -q --no-cov` (mocked, deterministic, ~50s)
- **After every plan wave:** Full combined sweep `pytest tests/phase04..phase08 --no-cov`
- **Before SMOKE-GATE (Wave 5):** Full regression + phase08 unit tests must be green
- **Before `/gsd:verify-work 8`:** Full suite green + smoke test delete-cleanup verified + `scripts/validate/phase08_acceptance.py` exit 0
- **Max feedback latency:** 60 seconds per-task

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 8-01-01 | 01 | 0 | REQ-TEST-infra | unit (scaffold) | `pytest tests/phase08/test_scaffold.py -q` | ✅ | ✅ green |
| 8-01-02 | 01 | 0 | REQ-TEST-infra | unit (MockYouTube) | `pytest tests/phase08/mocks/test_youtube_mock.py -q` | ✅ | ✅ green |
| 8-01-03 | 01 | 0 | REQ-TEST-infra | unit (MockGitHub) | `pytest tests/phase08/mocks/test_github_mock.py -q` | ✅ | ✅ green |
| 8-02-01 | 02 | 1 | REMOTE-01 | subprocess (repo create idempotent) | `pytest tests/phase08/test_github_remote_create.py -q` | ✅ | ✅ green |
| 8-02-02 | 02 | 1 | REMOTE-02 | subprocess (main rename + push) | `pytest tests/phase08/test_github_push_main.py -q` | ✅ | ✅ green |
| 8-02-03 | 02 | 1 | REMOTE-03 | subprocess (submodule add + .gitmodules schema) | `pytest tests/phase08/test_submodule_add.py -q` | ✅ | ✅ green |
| 8-03-01 | 03 | 2 | PUB-02 | unit (OAuth flow mock) | `pytest tests/phase08/test_oauth_installed_flow.py -q` | ✅ | ✅ green |
| 8-03-02 | 03 | 2 | PUB-02 | unit (refresh token round-trip) | `pytest tests/phase08/test_token_refresh.py -q` | ✅ | ✅ green |
| 8-04-01 | 04 | 3 | PUB-03 | unit (48h lock violation) | `pytest tests/phase08/test_publish_lock_48h.py -q` | ❌ W0 | ⬜ pending |
| 8-04-02 | 04 | 3 | PUB-03 | unit (KST window weekday 20-23) | `pytest tests/phase08/test_kst_window_weekday.py -q` | ❌ W0 | ⬜ pending |
| 8-04-03 | 04 | 3 | PUB-03 | unit (KST window weekend 12-15) | `pytest tests/phase08/test_kst_window_weekend.py -q` | ❌ W0 | ⬜ pending |
| 8-04-04 | 04 | 3 | PUB-01 | **ANCHOR A** — AST `containsSyntheticMedia=True` + `False` 0 hits | `pytest tests/phase08/test_ai_disclosure_anchor.py -q` | ❌ W0 | ⬜ pending |
| 8-05-01 | 05 | 4 | PUB-04 | unit (production_metadata 4-field schema) | `pytest tests/phase08/test_production_metadata_schema.py -q` | ✅ | ✅ green |
| 8-05-02 | 05 | 4 | PUB-04 | unit (HTML comment embedding roundtrip) | `pytest tests/phase08/test_metadata_html_comment.py -q` | ✅ | ✅ green |
| 8-05-03 | 05 | 4 | PUB-05 | unit (commentThreads.insert payload) | `pytest tests/phase08/test_pinned_comment.py -q` | ✅ | ✅ green |
| 8-05-04 | 05 | 4 | PUB-05 | **ANCHOR B** — grep `captions.insert` + `endScreen` 0 hits | `pytest tests/phase08/test_endscreen_nonexistent_anchor.py -q` | ✅ | ✅ green |
| 8-05-05 | 05 | 4 | PUB-02 | **ANCHOR C** — grep selenium/webdriver/playwright 0 hits | `pytest tests/phase08/test_no_selenium_anchor.py -q` | ✅ | ✅ green |
| 8-05-06 | 05 | 4 | PUB-02 | unit (youtube_uploader.upload_shorts full flow mocked) | `pytest tests/phase08/test_uploader_mocked_e2e.py -q` | ✅ | ✅ green |
| 8-06-01 | 06 | 5 | PUB-01..05 | **SMOKE GATE — CODE SHIPPED; real exec deferred to orchestrator** | `python -m py_compile scripts/publisher/smoke_test.py` | ✅ | ✅ green (code) |
| 8-06-02 | 06 | 5 | PUB-01..05 | subprocess (videos.delete cleanup verified) | `pytest tests/phase08/test_smoke_cleanup.py -q` | ✅ | ✅ green |
| 8-07-01 | 07 | 6 | PUB-01..05 + REMOTE-01..03 | E2E acceptance mocked | `python scripts/validate/phase08_acceptance.py` | ❌ W0 | ⬜ pending |
| 8-07-02 | 07 | 6 | TEST-regression | full regression sweep | `pytest tests/phase04 tests/phase05 tests/phase06 tests/phase07 tests/phase08 --no-cov` | ❌ W0 | ⬜ pending |
| 8-08-01 | 08 | 7 | All Phase 8 | TRACEABILITY matrix orphan guard | `pytest tests/phase08/test_traceability_matrix.py -q` | ❌ W0 | ⬜ pending |
| 8-08-02 | 08 | 7 | All Phase 8 | VALIDATION frontmatter flip | `grep 'nyquist_compliant: true' .planning/phases/08-*/08-VALIDATION.md` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [x] `tests/phase08/__init__.py` — package init (parallel to phase07)
- [x] `tests/phase08/conftest.py` — 6+ fixtures (tmp_publish_lock, mock_client_secret, mock_youtube_credentials, sample_mp4_path, fake_env_github_token, kst_clock_freeze)
- [x] `tests/phase08/mocks/__init__.py` + `tests/phase08/mocks/youtube_mock.py` + `tests/phase08/mocks/github_mock.py` — Phase 7 MockShotstack D-3 pattern (default `allow_fault_injection=False`)
- [x] `tests/phase08/fixtures/sample_production_metadata.json` — 4-field canonical reference
- [x] `tests/phase08/fixtures/sample_shorts.mp4` — 1-byte placeholder (upload path tests only need path string)
- [x] `scripts/publisher/__init__.py` — namespace (empty placeholder)
- [x] `scripts/publisher/_placeholder.py` — W0 smoke import surface (removed at Wave 3)

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| `config/client_secret.json` exists (user download from Google Cloud Console) | PUB-02 | OAuth client_secret requires 대표님 Google Cloud project creation — cannot automate without prior cloud project | 대표님 Google Cloud Console → APIs & Services → Credentials → OAuth 2.0 Client IDs → Desktop → Create → Download → save to `config/client_secret.json` |
| `config/youtube_token.json` initial acquisition (OAuth consent screen 1회) | PUB-02 | First-run browser-based consent screen interactive approval required by Google OAuth | Run `python scripts/publisher/oauth_bootstrap.py` once, authorize in browser, token saved to `config/youtube_token.json` |
| `GITHUB_TOKEN` fine-grained PAT exported to env | REMOTE-01 | 대표님 manual GitHub settings action required (fine-grained PAT issuance + 90-day rotation) | Settings → Developer Settings → Personal access tokens (fine-grained) → Generate → scope `contents:write` + `metadata:read` for `shorts_studio` AND `naberal_harness` → `export GITHUB_TOKEN=...` |
| `naberal_harness v1.0.1` commit SHA resolution (remote `git ls-remote`) | REMOTE-03 | External git remote state query — cannot embed SHA in plan artifacts (risks drift) | `git ls-remote https://github.com/kanno321-create/naberal_harness refs/tags/v1.0.1` then `git submodule add --depth=1 <url> harness/` + `cd harness && git checkout <sha>` |
| **SMOKE TEST LIVE UPLOAD (Wave 5)** — 대표님 승인 gate | PUB-01..05 | Real YouTube channel history irreversible. User Option A explicit approval required per CONTEXT D-11 | orchestrator가 Wave 5 실행 직전 `대표님, 실 YouTube smoke upload 진행 확인 (privacyStatus=unlisted + 30s 후 delete cleanup)?` 출력 후 정지. "진행" 응답 후 `python scripts/publisher/smoke_test.py --privacy=unlisted --cleanup` 실행 |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies (24 tasks mapped)
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify (verified — smoke gate 8-06-01 is manual but 8-06-02 cleanup is automated)
- [ ] Wave 0 covers all MISSING references (tests/phase08/ scaffold + mocks + fixtures + scripts/publisher/ namespace)
- [ ] No watch-mode flags (all commands exit; no `--watch` / `pytest -f`)
- [ ] Feedback latency < 60s per task (phase08 isolated ~50s)
- [ ] `nyquist_compliant: true` set in frontmatter (pending Wave 7 flip)

**Approval:** pending
