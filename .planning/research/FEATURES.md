# FEATURES — naberal-shorts-studio

**Researched**: 2026-04-18 | **Mode**: Ecosystem (Features dimension)
**Confidence (overall)**: MEDIUM-HIGH (7 HIGH findings, 3 MEDIUM, 1 LOW)
**Scope**: AI-assisted YouTube Shorts production studio, Korean market, 3~4 videos/week, YPP-targeting

---

## Overview

### Context anchors (from PROJECT.md + shorts_naberal research)

- **Core value** = external YPP ad revenue on an **existing Korean channel**, not internal pipeline elegance.
- **Cadence** = 3~4 Shorts/week. The feature budget is small — anything that doesn't materially move retention / CTR / compliance is cut.
- **Inheritance** = `shorts_naberal`'s incidents niche (true-crime / detective-duo format), Morgan/조수 TTS pools, Runway Gen-4.5 primary video gen, WhisperX subtitle alignment. Confirmed in PROJECT.md REQ-02 and CONFLICT_MAP.
- **Critical 2026 regime change** = YouTube's July 2025 **"Inauthentic Content"** policy (rename of "repetitious content") explicitly targets AI-narration-over-stock-footage and template-replicable Shorts. This is the single biggest feature constraint for this project — **every feature below must either increase originality signal or reduce demonetization risk**. [HIGH confidence — YouTube Help + TechCrunch + Plagiarism Today + SEOSherpa all cross-validate]

### The 2026 reality for a 3~4/week Korean creator

1. **Retention ≥ volume.** Algorithm rewards viewed-to-swiped ratio and avg % viewed. 80% retention × 1 Short > 40% × 4 Shorts. [HIGH — vidiq, metricool, Epidemic Sound, TrueFuture Media cross-validate]
2. **74% of Shorts views come from non-subscribers** → every Short is a discovery attempt for the existing channel, not a follower-serve. Table stakes must assume cold audience. [HIGH — loopexdigital / pennep]
3. **AI use is not banned — AI-as-template is banned.** Creator's unique insight, editorial choices, voice-distinctness, and research originality are what keeps monetization safe. [HIGH — YouTube Help + Fliki + Knolli]
4. **Dual YPP tier from 2026**: 500 subs + 3 posts in 90 days gets Shopping/Fan Funding; **full ad-rev requires 1000 subs + 10M Shorts views/90d (or 4000 watch hours)**. PROJECT.md's YPP goal = full tier. [HIGH — vidiq, shopify, tubebuddy]

### Korean market realities (must-know)

- **87.1% of Korean short-form viewing happens on YouTube Shorts** (not TikTok/Reels). Shorts IS the Korean short-form market. [HIGH — opensurvey]
- **Voice-clone auto-detection launches 2026**: YouTube's "likeness" detection automatically flags synthesized voices of real people. Morgan/조수 TTS pools are fictional personas, but any celebrity/politician voice is demonetization-risk. [HIGH — supertone + viralpulse]
- **Emotional-satisfaction / 감성 content** and **health-intelligence (건강지능)** are rising 2026 Korean niches. True-crime (shorts_naberal incidents niche) overlaps with 감성 — confirmation that existing niche fits 2026 Korean trends. [MEDIUM — fikad/pikaclip + marieclaire]

---

## Table Stakes

**Definition**: Without these, algorithm de-ranks or YouTube demonetizes. Users expect them. Non-negotiable v1 scope.

### TS-1 — 9:16 vertical, 1080×1920, ≤60s duration
- **Complexity**: XS
- **Dependencies**: None (shorts_naberal Remotion + FFmpeg pipeline already produces this)
- **shorts_naberal status**: ✅ WORKING — preserve via Harvest (REQ-02)
- **Korean note**: 60s+ Shorts are ranked differently — avoid drifting into >60s (shorts_naberal B-13 conflict: Morgan 140s exception is a landmine; kill in v1, stick to 120s hard cap per CLAUDE.md:111 but ideally ≤60s for pure shelf placement)
- **2026 fact**: The "59-second rule" — staying strictly ≤59s keeps the Short in all shelf placements with no ambiguity
- **Sources**: [socialync.io 59-second rule](https://www.socialync.io/blog/short-form-content-59-seconds-rule), [navigatevideo 2026 guide](https://www.navigatevideo.com/news/a-guide-to-youtube-shorts)

### TS-2 — Hook in first 1-3 seconds (Korean-optimized)
- **Complexity**: S (script-level; requires `ins-hook` inspector + scripter variant)
- **Dependencies**: TS-3 (captions must show hook line visibly from t=0)
- **shorts_naberal status**: ⚠️ PARTIAL — `ins-hook` exists in prior 32-inspector structure (RESEARCH_REPORT §2.4); retain under the 16-20 consolidated inspectors (REQ-03)
- **Korean note**: Korean true-crime hook pattern ≠ Western. Korean viewers respond to **질문형 hook** ("왜 [이 사람은] 사라졌을까?") + **숫자/고유명사 selector** ("1997년 서울", "23세 여대생"). Avoid Western "You won't believe..." translation — feels AI-generated to Korean ear.
- **2026 fact**: Algorithm tests every Short with a small seed audience first; low retention on those first ~100 views kills distribution. First 3s is the veto window.
- **Sources**: [vidiq algorithm](https://vidiq.com/blog/post/youtube-shorts-algorithm/), [metricool 2026](https://metricool.com/youtube-shorts-algorithm/)

### TS-3 — Burned-in Korean captions (not auto-generated)
- **Complexity**: S
- **Dependencies**: TS-1 (9:16 framing), WhisperX word-level alignment from shorts_naberal
- **shorts_naberal status**: ✅ WORKING — WhisperX pipeline confirmed "Keanu Reeves lip-sync grade" in prior research (RESEARCH_REPORT §6.3). Preserve.
- **Korean note**: YouTube auto-captions for Korean have improved in 2026 but still lose **존댓말/반말 nuance** and **homophone detective-jargon**. Burn-in (하드코딩) ≥ 24-32pt, short 1-4 word clusters, center-positioned (not bottom — bottom is covered by Shorts UI on mobile). [HIGH — opus.pro, air.io, reap.video cross-validate]
- **Design spec**: Avoid text in bottom 30% of frame — UI overlay region.
- **Sources**: [opus.pro caption best practices](https://www.opus.pro/blog/youtube-shorts-caption-subtitle-best-practices), [air.io subtitles](https://air.io/en/youtube-hacks/best-practices-for-writing-and-formatting-subtitles)

### TS-4 — Licensed/safe audio only (no copyright strikes)
- **Complexity**: S
- **Dependencies**: None
- **shorts_naberal status**: ⚠️ CONFLICT B-10 — Pexels banned (resolved), but music sourcing path still ambiguous. Must codify v1.
- **Korean note**: Use (in priority) — (1) YouTube Shorts Audio Library in-product, (2) YouTube Audio Library (Studio), (3) AI-generated tracks (Suno/Udio — commercial-safe), (4) project's own Morgan/조수 TTS as primary audio. **NEVER**: K-pop tracks even if "trending" — Content ID strike risk + music-publisher cut reduces creator share 20-40% of Shorts Fund pool.
- **2026 fact**: Original audio (= TTS narration + no music, or music only from Audio Library) keeps full 45% creator-pool share. Licensed music splits before the 45% cut.
- **Sources**: [YouTube music eligibility help](https://support.google.com/youtube/answer/13486873), [gyre.pro trending audio legally](https://gyre.pro/blog/using-trending-audio-legally-a-guide-for-youtube-creators), [postlinkapp copyright 2026](https://postlinkapp.com/blog/youtube-shorts-music-copyright)

### TS-5 — Custom thumbnail (for search/channel/embed surfaces)
- **Complexity**: XS
- **Dependencies**: TS-1 (1080×1920 vertical)
- **shorts_naberal status**: ❓ UNCLEAR — not surfaced in CONFLICT_MAP; may be missing
- **Korean note**: Not seen in the swipe feed (YouTube auto-picks a frame there) but IS seen on channel page, search results, and — critically — the January 2026 new Shorts search filter. On search, custom thumbnail does the click-through work. Korean CTR is thumbnail+title more than Western. [HIGH — miraflow, banana, vidiq]
- **Design rule**: No text in bottom 30% (UI overlay). 1-2 Korean characters max if text used — small fonts illegible in shelf.
- **Sources**: [miraflow thumbnail 2026](https://miraflow.ai/blog/youtube-shorts-thumbnail-strategy-2026), [bananathumbnail 2026](https://blog.bananathumbnail.com/youtube-shorts-thumbnail-upload-2026/)

### TS-6 — Metadata SEO (title, description, hashtags) Korean + searchable
- **Complexity**: S
- **Dependencies**: None
- **shorts_naberal status**: ⚠️ CONFLICT A-5 (TODO(next-session) for GATE 5 unwired) — metadata gate was never actually automated in orchestrator. Wiring is a REQ-04 v2 orchestrator task.
- **Korean note**: Korean search needs **both** Korean keywords and Romanization (e.g., "한강 사건 | Han River incident") for the ~15% of Shorts viewers using English UI. Hashtags: max 3-5 (more = spam signal). `#Shorts` hashtag was deprecated as a ranking factor but still useful for shelf clarity.
- **2026 fact**: Jan 2026 search filter lets users exclude/include Shorts — title/description keyword discipline matters more than in 2024.

### TS-7 — Upload cadence (non-spam, irregular human-like pattern)
- **Complexity**: XS (scheduler logic only)
- **Dependencies**: None
- **shorts_naberal status**: ✅ LESSON LEARNED — memory `feedback_publish_interval` explicitly bans "1 per hour" cadence, requires 60-180 min random. Inherit this rule.
- **Korean note**: Korean YouTube viewing peaks 20:00-23:00 KST weekdays, 12:00-15:00 weekends. Schedule 3-4 weekly posts into these windows. Don't post all 4 on Sunday — spread across 3 distinct days.
- **Algorithm note**: No per-video ranking boost from frequency. Frequency = sample-size for hits. Daily ≠ better; 3-4/week quality ≥ 7/week mediocre. [HIGH — air.io, ventress, shortimize cross-validate]
- **Sources**: [air.io cadence 2025](https://air.io/en/youtube-hacks/the-death-of-daily-uploads-what-cadence-actually-triggers-algorithm-love-in-2025), [ventress posting guide](https://ventress.app/blog/youtube-posting-frequency-guide-2025/)

### TS-8 — AI disclosure toggle (when synthetic voice depicts real events)
- **Complexity**: XS (metadata flag only)
- **Dependencies**: None
- **shorts_naberal status**: ❓ UNCLEAR — metadata generator unverified for this field
- **Korean note**: Our incidents/true-crime niche narrates **real historical cases**. Under 2026 YouTube rules, synthesized narration + realistic depiction of real events/people **requires disclosure**. The "Altered or synthetic content" toggle adds a banner in Shorts feed. **Not disclosing = YPP suspension risk**. Morgan/조수 voices are fictional personas → depends on whether content *depicts real people realistically*. If we narrate "실제 사건" with reenactment imagery, disclose.
- **2026 fact**: YouTube's own AI effects (dream screen, etc.) auto-disclose. Third-party TTS does not — creator must toggle.
- **Sources**: [YouTube blog AI disclosure](https://blog.youtube/news-and-events/disclosing-ai-generated-content/), [syncstudio policy guide](https://syncstudio.ai/blog/youtube-synthetic-content-disclosure), [onewrk 2025 guide](https://onewrk.com/youtubes-ai-disclosure-requirements-the-complete-2025-guide/)

### TS-9 — Monetization-safe content filter (DMCA, sensitive topics, likeness)
- **Complexity**: M (requires multiple inspectors working together)
- **Dependencies**: Existing shorts_naberal inspectors (`ins-license`, `ins-gore`, `ins-mosaic`, `ins-platform-policy`)
- **shorts_naberal status**: ✅ WORKING (at the inspector level) — 4 compliance inspectors identified in RESEARCH_REPORT §2.4. Preserve under consolidated 16-20 inspector structure.
- **Korean note**: True-crime Shorts have **three specific Korean landmines**: (a) 피의자 실명/사진 표시 (명예훼손), (b) 미성년 피해자 신원 노출 (아동복지법), (c) 현행 수사 사건 (공소제기 전 보도규제). Add `ins-korean-legal` or extend `ins-platform-policy` with these rules.
- **2026 fact**: The **voice-clone likeness detection** rolling out 2026 auto-removes videos with detected synthesized voice of real people. Morgan/조수 must remain demonstrably fictional (unique voice signatures documented).
- **Sources**: [viralpulse AI shorts policy](https://viralpulse.net/en/blog/ai-shorts-youtube-policy), [news1 유튜브 AI 저품질](https://www.news1.kr/it-science/general-it/6041850)

### TS-10 — Originality signal (avoid "Inauthentic Content" demonetization)
- **Complexity**: M (design-level, not a single feature)
- **Dependencies**: TS-8 disclosure, original research inputs, unique-voice TTS, human-editorial variance
- **shorts_naberal status**: ⚠️ RISK — 32 inspectors + template pipeline = *structurally* look like "easily replicable at scale". This is the project's single largest demonetization exposure.
- **Korean note**: YouTube has specifically called out "AI narration + stock footage" as prototypical inauthentic content. Our stack (TTS + Runway Gen-4.5 generated B-roll) is **exactly this pattern**. Mitigation: (a) per-episode original research manifest (NotebookLM outputs per REQ-07), (b) unique editorial commentary layer — not just narration-over-images, (c) visible variance between episodes (different pacing, different scene structures — not template), (d) channel-specific 바이블 enforcement with episode-specific deviation.
- **2026 fact**: "Videos with the same intro and outro, but where the bulk of the content is different" is explicitly allowed. Our template-ness must be confined to intro/outro + brand signature, never structure or content.
- **Sources**: [YouTube inauthentic policy help](https://support.google.com/youtube/answer/1311392), [plagiarismtoday inauthentic](https://www.plagiarismtoday.com/2025/07/08/youtube-targets-inauthentic-content/), [knolli AI compliance](https://www.knolli.ai/post/youtube-ai-monetization-policy-2025), [supertone Korean guide](https://www.supertone.ai/en/work/youtube-ai-monetization-policy-2025-eng)

### TS-11 — WhisperX word-level subtitle alignment
- **Complexity**: S
- **Dependencies**: TS-3
- **shorts_naberal status**: ✅ WORKING — sys.path.insert hack notwithstanding (CONFLICT B-16), the module functions. Harvest.
- **Korean note**: Korean phoneme alignment in WhisperX is significantly better than base Whisper — worth the dependency cost.
- **Sources**: RESEARCH_REPORT §6.3

### TS-12 — Duo-dialogue structure (탐정 + 조수) preserved
- **Complexity**: S (pipeline-level, scripter + inspector)
- **Dependencies**: TS-11 WhisperX timing, voice-presets.json Morgan/조수
- **shorts_naberal status**: ✅ WORKING but with ≥5 unresolved conflicts (A-8, A-9, A-10, B-5, A-7). Resolve during REQ-04 orchestrator rewrite — canonical rules: "조수 20-35%", "탐정님" 호명 금지, "놓지 않았습니다" Part1/마지막만 허용, Morgan tempo single value.
- **Korean note**: Duo format is a competitive differentiator (most Korean true-crime Shorts are monologue). Keep as table stake for **this project** — without it we lose identity. Generic duo would NOT be table stake.
- **Classification reasoning**: Listed as table stakes because it's the channel's existing identity (PROJECT.md REQ-08 "niche 승계"), not generic Shorts table stake.

---

## Differentiators

**Definition**: Competitive edge for a Korean quality-first creator targeting YPP. Builds retention, originality signal, or repeatable uniqueness. Optional in strict v1 — include only if they *directly* serve YPP velocity.

### DF-1 — Channel-bible-enforced theme consistency (v1 MUST-HAVE-anyway)
- **Complexity**: M
- **Dependencies**: NotebookLM RAG (REQ-07), `ins-tone-brand` inspector
- **shorts_naberal status**: ⚠️ PARTIAL — `.claude/channel_bibles/incidents.md` exists but A-8/A-9/A-10 conflicts show it drifts vs script rules
- **Why it's a differentiator**: Directly counters "Inauthentic Content" flag. A documented channel-bible with **explicit deviation per episode** creates paper-trail originality. Reviewers/YouTube trust signals increase.
- **Korean note**: Korean viewers are acutely sensitive to tone/register inconsistency — a detective slipping from 존댓말 to 반말 mid-episode tanks retention.
- **Decision**: Classify as differentiator but treat as v1-mandatory (= promote to table stake for this project specifically).

### DF-2 — NotebookLM-RAG-grounded research manifest (per episode)
- **Complexity**: L
- **Dependencies**: REQ-07 (NotebookLM integration), Tier 2 studio wiki
- **shorts_naberal status**: 🆕 NEW — session #77 introduced NLM as primary research/script entry (CLAUDE.md:105-131 + SKILL:23). Existed but not yet stabilized.
- **Why it's a differentiator**: Source-grounded outputs = original-research artifact per episode = anti-inauthentic evidence. Also cuts hallucination (Morgan narrating false facts = audience trust loss = retention tank = algorithmic demotion).
- **Korean note**: Korean true-crime audiences fact-check aggressively on community forums (DC/theqoo/FMKorea). One factual error trend-posted → channel reputation damage. Grounded research directly addresses memory `feedback_factcheck_agent` lesson.
- **Sources**: CONFLICT_MAP A-3 + PROJECT.md REQ-07

### DF-3 — Producer-Reviewer dual-pass with rubric-structured feedback
- **Complexity**: L
- **Dependencies**: REQ-05 (Producer-Reviewer pattern), consolidated 16-20 inspector set
- **shorts_naberal status**: ⚠️ OVER-ENGINEERED — 32 inspectors already implement this but without rubric-structured JSON output (RESEARCH_REPORT §2.3 — "rubric 없는 inspector는 'looks good 👍'만 반복").
- **Why it's a differentiator**: Quality gate before publish = retention-floor guarantee. At 3-4/week cadence, producer-reviewer overhead is affordable and prevents low-retention publishes that kill channel authority scores.
- **Korean note**: Doesn't have a Korean-specific twist — standard best practice.
- **Pattern**: Generator → structured-JSON critic (score + issues + suggested_fix) → regen or pass. Anthropic Evaluator-Optimizer.
- **Sources**: RESEARCH_REPORT §2.1-2.5

### DF-4 — Retention-analytics feedback loop (YouTube Analytics → next-episode input)
- **Complexity**: L
- **Dependencies**: REQ-09 (KPI-driven feedback loop), YouTube Analytics API
- **shorts_naberal status**: ❌ MISSING — memory/wiki shows no evidence of this loop
- **Why it's a differentiator**: At 3-4/week cadence over 90 days (YPP window), we publish ~40-50 Shorts. Without feedback, each is isolated. With retention curve per Short → identify the hook pattern/length/pacing that retains best → feed to next batch Producer. This directly accelerates YPP velocity.
- **Korean note**: Korean audiences have distinct retention curves (lower tolerance for slow openings, higher engagement on emotional-twist reveals). Local calibration impossible without data loop.
- **Priority**: Not v1, but v1.5 (once 10-15 Shorts published to have baseline).

### DF-5 — Twelve Labs Marengo semantic B-roll matching
- **Complexity**: L
- **Dependencies**: B-roll library indexing, scene-manifest semantic field
- **shorts_naberal status**: ❌ NOT INTEGRATED (RESEARCH_REPORT §6.5 flagged as "hidden gem")
- **Why it's a differentiator**: Generic stock B-roll signals "inauthentic" to both YouTube reviewers and Korean viewers. Marengo's multi-vector embeddings (visual/speech/text/audio) allow "scene-context-aware" B-roll — reduces template feel.
- **Korean note**: Korean incidents often reference specific locations/time periods (1990s Seoul, rural village). Marengo semantic search beats keyword search for this.
- **Priority**: v1.5 experiment. v1 uses Runway Gen-4.5 generated clips (already primary per A-1 resolution).

### DF-6 — Runway Gen-4.5 consistent-character B-roll (I2V, 6-8 clips per short)
- **Complexity**: M (already implemented in shorts_naberal)
- **Dependencies**: `config/stock-search-config.json` Runway primary (A-1 resolution), video-sourcer agent
- **shorts_naberal status**: ✅ RESOLVED as primary (A-1) per 2026-04-17 confirmation, but DESIGN_BIBLE + PIPELINE.md + channel_bibles not yet synced to Runway (CONFLICT_MAP A-1 "수정 범위").
- **Why it's a differentiator**: AI-generated original B-roll > licensed stock footage for originality signal. Kling-primary would have been Chinese-market-adapted; Runway Gen-4.5 I2V better for Korean detective aesthetics (noir tone, realistic lighting).
- **Korean note**: Stock-footage reliance was named in YouTube's 2025 policy update as prototypical inauthentic. Generated B-roll with channel-specific style = substantive originality.
- **Action**: Finalize A-1 and sync DESIGN_BIBLE + PIPELINE.md.

### DF-7 — Hook/CTA A/B variants (2-variant per Short, algorithm-seed-test)
- **Complexity**: M
- **Dependencies**: Variant publish scheduler, retention comparison
- **shorts_naberal status**: ❌ NOT EXISTING
- **Why it's a differentiator**: YouTube's seed-audience testing (first ~100-500 views) kills low-retention Shorts. Publishing 2 hook variants as separate Shorts spaced 24-48h gives us algorithm-tested hooks.
- **Korean note**: Expensive — 2× rendering + 2× compliance checks. At 3-4 total Shorts/week, A/B testing 2 of them halves our effective cadence.
- **Decision**: DE-PRIORITIZE for v1. Consider for v2 once KPI loop (DF-4) is stable.

### DF-8 — Korean-grammar + 존댓말 consistency inspector
- **Complexity**: S
- **Dependencies**: Consolidated inspector set
- **shorts_naberal status**: ✅ PROPOSED in RESEARCH_REPORT §7.5 but not confirmed implemented
- **Why it's a differentiator**: Korean viewer micro-signal detection. Morgan-to-조수 register consistency (Morgan 하오체, 조수 해요체) is channel identity; drift = AI-tell.
- **Korean note**: Specifically Korean — no Western equivalent need.

### DF-9 — End-screen / pinned-comment engagement prompt (subscribe funnel)
- **Complexity**: XS
- **Dependencies**: None
- **shorts_naberal status**: ❓ UNCLEAR — may exist in publisher but not surfaced in conflict map
- **Why it's a differentiator**: YPP target = 1000 subs. Shorts ad-rev requires subs. Pinned comment + next-episode-tease CTA converts retention-viewers to subs. 2026 best practice: "reply within 60min to boost early engagement signal"; pinned comment standard in top Korean true-crime channels.
- **Korean note**: Korean channels pin spoiler-prevention comments + "구독 눌러주세요" + next-episode question. High-converting pattern.
- **Sources**: [pennep 2026 vision](https://www.pennep.com/blogs/youtube-s-vision-for-2026-trends-updates-and-growth-strategies), [nigcworld small creator blueprint](https://www.nigcworld.com/youtube-channel-growth-blueprint-2026)

---

## Anti-Features (DO NOT BUILD)

**Definition**: Features that would harm YPP goal, trigger demonetization, or waste the small v1 budget.

### AF-1 — Mass spam generation (daily 5+, template-replicable)
- **Reasoning**: Directly violates July 2025 "Inauthentic Content" policy. PROJECT.md explicitly out-of-scope ("일 5편+ 양산 모델"). 3-4/week quality > 7/day template.
- **Alternative**: Quality cadence + Producer-Reviewer.
- **Ref**: PROJECT.md Out of Scope, TS-10

### AF-2 — Clickbait without substance
- **Reasoning**: Korean true-crime community forums (theqoo/FMKorea) publicly shame misleading thumbnails within hours. Demonetization via "Misleading Metadata" YouTube policy. Also tanks channel authority score → algorithm deprioritization.
- **Alternative**: Dramatic-but-truthful hooks (DF-2's grounded research enables this).

### AF-3 — Cross-posting to TikTok/Instagram without adaptation
- **Reasoning**: Explicitly out of v1 scope per PROJECT.md. Each platform has distinct algorithm + watermark-strip policy + audio-library differences. Cross-posting without adaptation degrades performance on both.
- **Alternative**: Focus YouTube-native in v1; revisit multi-platform in v2 with proper platform-adapters per shorts_naberal memory `platform-adaptation`.

### AF-4 — Voice cloning of real people (politicians, celebrities, victims)
- **Reasoning**: 2026 YouTube likeness auto-detection = instant removal. Korean 명예훼손/초상권 criminal liability. Morgan/조수 must remain documented-fictional.
- **Alternative**: Fictional narrator personas (current stack).
- **Ref**: TS-9, 2026 likeness detection rollout

### AF-5 — AI-generated faces of real historical victims (uncanny valley / ethical)
- **Reasoning**: Beyond legal — the incidents niche deals with real crime victims. AI reenactment of specific victim faces = trauma-exploitation = channel reputation death + likely demonetization under "harmful content." Korean audiences are especially sensitive to this after 박나래 deepfake discourse.
- **Alternative**: Symbolic / atmospheric / location-based B-roll, generic persona silhouettes, news-media-style blur.

### AF-6 — "AI narration over stock footage" template (the prototype YouTube named)
- **Reasoning**: This is the *exact* example YouTube gave for Inauthentic Content policy. Our current stack risks resembling this from the outside. Mitigation = DF-1 + DF-2 + DF-6 (original research, channel bible, generated-not-stock B-roll).
- **Alternative**: Generated B-roll + documented research + human-editorial variance (via Producer-Reviewer).
- **Ref**: TS-10 Korean note

### AF-7 — Template-based intro/outro that is the BULK of each Short
- **Reasoning**: YouTube explicitly allows "same intro/outro with different bulk." Inverting (same bulk + template variation) = violation.
- **Alternative**: 5-8s intro signature acceptable; remaining 45-55s must be unique per episode.

### AF-8 — Auto-upload via Selenium / unofficial APIs
- **Reasoning**: ToS violation → ban risk. RESEARCH_REPORT §7.4 explicit warning.
- **Alternative**: YouTube Data API v3 only (officially supported).

### AF-9 — Cross-channel content recycling (uploading others' Shorts with minor edits)
- **Reasoning**: Reused Content policy — demonetization. Also Korean audiences spot it fast and report.
- **Alternative**: Original research per DF-2.

### AF-10 — 32-inspector over-engineered review (legacy)
- **Reasoning**: Per RESEARCH_REPORT §2.3, 32 inspectors exceed Anthropic subagent sweet spot (3-5), cost-ineffective, duplicate checks, and worst-of-all don't improve output (Producer-Reviewer value is from *structured-rubric feedback*, not inspector count).
- **Alternative**: Consolidated 16-20 inspectors with Pydantic structured-output rubric (PROJECT.md REQ-03).

### AF-11 — Daily-upload cadence (4+ per day)
- **Reasoning**: PROJECT.md Out of Scope. Algorithm rewards retention, not volume. At infrastructure cost per Short (Runway API, TTS quota, inspector cycles), 4+/day breaks Constraint budget.
- **Alternative**: 3-4/week (PROJECT.md Decision D-10).

### AF-12 — Viewer-auto-translation to other markets (en-US, ja-JP)
- **Reasoning**: PROJECT.md v1 scope = single Korean channel. Translation = channel-fork (separate channel per language per YouTube best practice). Out of scope until Korean channel hits YPP.
- **Alternative**: Defer to v2+.

### AF-13 — Chasing viral/meme audio (K-pop/TikTok trend tracks)
- **Reasoning**: Music-publisher cut reduces creator share 20-40% of Shorts Fund. Content ID strike risk. Meme-tracks age fast (6-week shelf).
- **Alternative**: Original Morgan/조수 TTS narration as primary audio (full 45% creator share + zero copyright risk + channel-identity signal).
- **Ref**: TS-4 Sources

### AF-14 — "Skip gates / TODO(next-session)" debug bypass paths in prod
- **Reasoning**: Direct cause of shorts_naberal drift (CONFLICT_MAP A-5, A-6). PROJECT.md Code Quality constraint explicitly bans. Physical enforcement in REQ-04 state-machine orchestrator.
- **Alternative**: State-machine with physical GATE traversal.

### AF-15 — Community Tab dependency for YPP (as primary growth feature)
- **Reasoning**: Community Tab only unlocks at 500 subs (itself a YPP prerequisite) and its engagement contributes minimally to algorithm vs retention/CTR. Nice-to-have but not a v1 feature.
- **Alternative**: Focus engineering on retention (DF-4 loop) + pinned-comment (DF-9). Community tab is a 1-line channel-ops task, not a studio feature.

---

## 2026 Trends (informing feature priorities)

1. **Inauthentic Content enforcement is rising** — every feature must defend originality signal. [HIGH]
2. **Dual YPP tier (500/1000)** lowers entry bar but ad-rev still gated at 1000+10M — our goal remains the upper tier. [HIGH]
3. **Jan 2026 Shorts search filter** raises metadata+thumbnail importance. [HIGH]
4. **Voice-clone auto-detection** rolling out = synthetic-voice stack must be provably fictional. [HIGH]
5. **74% of Shorts views from non-subs** = every Short is cold-audience discovery; table-stake hooks matter disproportionately. [HIGH]
6. **Retention-over-volume officially stated by algorithm team** — vindicates 3-4/week quality cadence over 7/week mediocrity. [HIGH]
7. **59-second duration sweet spot** (avoid ≥60s to stay in all shelf placements). [MEDIUM]
8. **Shorts + long-form combination grows 41% faster** — NOT relevant for v1 (Shorts-only per PROJECT.md), but worth noting for v2. [MEDIUM]
9. **Creator Pool payout: $0.03-0.10 per 1000 views, creator takes 45%** — sets 10M view target for meaningful revenue (~$450 over 90d at median). [HIGH]
10. **"Emotional satisfaction" and "health intelligence" as rising Korean niches** — existing incidents niche overlaps with 감성. [MEDIUM]

---

## Korean Market Notes (mandatory specificity)

1. **87.1% Korean short-form consumption is on YouTube Shorts** — Korean market ≈ YouTube Shorts market. No multi-platform split in v1 needed to reach Korean audience. [HIGH]
2. **존댓말/반말 register drift is a retention killer** — Korean viewers detect instantly. `ins-korean-grammar` mandatory.
3. **Korean legal landmines for true-crime niche**: 명예훼손 / 아동복지법 / 공소제기 전 보도규제 — needs `ins-korean-legal` beyond generic `ins-platform-policy`.
4. **Korean true-crime hook patterns** diverge from Western — 질문형 + 숫자/고유명사 selector, avoid translated "You won't believe" patterns.
5. **Korean viewing peaks**: Weekday 20-23 KST, Weekend 12-15 KST. Schedule into these windows.
6. **Korean audiences fact-check on DC/theqoo/FMKorea** within hours of publish. DF-2 grounded research is not nice-to-have — it's reputation defense.
7. **Duo-narration (탐정/조수) format** is differentiator in Korean market (monologue is default). Worth preserving even at code-conflict cost.
8. **Morgan 하오체 + 조수 해요체** register pair is channel signature — bible enforcement mandatory per DF-8.
9. **Typecast (Korean firm) and Fish Audio** outperform ElevenLabs on Korean emotional prosody in 2026 benchmarks (RESEARCH_REPORT §7.3). But config/voice-presets.json has unresolved JP voice conflict (CONFLICT B-3) — only KR matters for v1.
10. **Korean Shorts Audio Library** has fewer track partnerships than US — more reason to lean on original TTS audio over licensed music.

---

## Feature Dependency Map (for roadmap ordering)

```
Foundation (MUST be first)
├── TS-1 (9:16 format) — existing, Harvest
├── TS-11 (WhisperX) — existing, Harvest
├── TS-12 (Duo structure) — existing w/ conflicts to resolve
└── AF-14 resolution (no skip_gates in prod) — REQ-04 v2 orchestrator

Research & Script layer
├── DF-1 (Channel bible) ← TS-10 originality
├── DF-2 (NotebookLM RAG) ← REQ-07
└── TS-2 (Korean hook) ← DF-1 + DF-2

Assembly layer
├── TS-3 (Burned captions) ← TS-11
├── DF-6 (Runway gen B-roll) ← A-1 resolution
├── TS-4 (Safe audio) ← independent
└── DF-8 (Korean-grammar ins) ← DF-1

Gate layer
├── DF-3 (Producer-Reviewer rubric) ← consolidated inspectors (REQ-03)
└── TS-9, TS-10 (compliance) ← DF-3

Publish layer
├── TS-5 (Thumbnail) ← independent
├── TS-6 (SEO metadata) ← independent
├── TS-7 (Cadence scheduler) ← independent
├── TS-8 (AI disclosure) ← TS-6
└── DF-9 (Pinned comment) ← TS-6

Feedback layer (v1.5)
└── DF-4 (Retention → next input) ← REQ-09
```

---

## Confidence Assessment

| Claim | Confidence | Source Tier |
|-------|-----------|-------------|
| Inauthentic content policy specifics | HIGH | YouTube Help + TechCrunch + Plagiarism Today |
| Dual YPP tier (500/1000) | HIGH | vidiq + tubebuddy + shopify + mediacube |
| Voice-clone detection 2026 | HIGH | supertone + viralpulse + news1 |
| Retention > volume | HIGH | metricool + vidiq + Epidemic Sound + TrueFuture Media |
| Captions best practices (1-4 words, 24-32pt, center) | HIGH | opus.pro + air.io + reap.video |
| Custom thumbnail visible in search but not swipe feed | HIGH | vidiq + miraflow + bananathumbnail |
| 87.1% Korean short-form on Shorts | HIGH | opensurvey |
| Jan 2026 Shorts search filter | MEDIUM | bananathumbnail cites it but single source |
| Korean emotional/health-intelligence niche rising | MEDIUM | fikad blog + marieclaire |
| 59-second hard threshold for shelf placement | MEDIUM | socialync.io single source |
| Twelve Labs Marengo as B-roll semantic layer | MEDIUM | Twelve Labs docs + RESEARCH_REPORT §6.5 |
| Shorts+long-form 41% faster growth | LOW | pennep + loopexdigital — not primary-source verified |

---

## Sources

- [vidiq Shorts monetization 2026](https://vidiq.com/blog/post/youtube-shorts-monetization/)
- [unkoa YPP tiers 2026](https://www.unkoa.com/youtube-shorts-monetization-requirements/)
- [tubebuddy monetization requirements](https://www.tubebuddy.com/blog/youtube-monetization-requirements/)
- [shopify Shorts monetization](https://www.shopify.com/blog/youtube-shorts-monetization)
- [mediacube 2026 requirements](https://mediacube.io/en-US/blog/youtube-monetization-requirements)
- [YouTube Shorts monetization policies (help)](https://support.google.com/youtube/answer/12504220)
- [YouTube channel monetization policies (help)](https://support.google.com/youtube/answer/1311392)
- [vidiq algorithm 2026](https://vidiq.com/blog/post/youtube-shorts-algorithm/)
- [metricool 2026 algorithm](https://metricool.com/youtube-shorts-algorithm/)
- [miraflow algorithm Jan 2026](https://miraflow.ai/blog/youtube-shorts-algorithm-update-january-2026)
- [shortimize retention 2026](https://www.shortimize.com/blog/youtube-shorts-retention-rate)
- [Epidemic Sound algorithm](https://www.epidemicsound.com/blog/youtube-shorts-algorithm/)
- [TrueFuture Media data-backed guide](https://www.truefuturemedia.com/articles/youtube-shorts-algorithm-data-backed-guide)
- [joinbrands 2026 best practices](https://joinbrands.com/blog/youtube-shorts-best-practices/)
- [navigatevideo 2026 guide](https://www.navigatevideo.com/news/a-guide-to-youtube-shorts)
- [opus.pro caption best practices 2026](https://www.opus.pro/blog/youtube-shorts-caption-subtitle-best-practices)
- [air.io subtitles 2026](https://air.io/en/youtube-hacks/best-practices-for-writing-and-formatting-subtitles)
- [reap.video captions guide](https://reap.video/blog/how-to-add-captions-to-youtube-shorts)
- [miraflow thumbnail strategy 2026](https://miraflow.ai/blog/youtube-shorts-thumbnail-strategy-2026)
- [bananathumbnail Shorts upload 2026](https://blog.bananathumbnail.com/youtube-shorts-thumbnail-upload-2026/)
- [vidiq custom thumbnails](https://vidiq.com/blog/post/youtube-shorts-custom-thumbnails/)
- [pennep 2026 vision](https://www.pennep.com/blogs/youtube-s-vision-for-2026-trends-updates-and-growth-strategies)
- [nigcworld small creator blueprint](https://www.nigcworld.com/youtube-channel-growth-blueprint-2026)
- [loopexdigital Shorts statistics](https://www.loopexdigital.com/blog/youtube-shorts-statistics)
- [air.io death of daily uploads](https://air.io/en/youtube-hacks/the-death-of-daily-uploads-what-cadence-actually-triggers-algorithm-love-in-2025)
- [ventress posting frequency 2025](https://ventress.app/blog/youtube-posting-frequency-guide-2025/)
- [socialync 59-second rule](https://www.socialync.io/blog/short-form-content-59-seconds-rule)
- [techcrunch inauthentic crackdown](https://techcrunch.com/2025/07/09/youtube-prepares-crackdown-on-mass-produced-and-repetitive-videos-as-concern-over-ai-slop-grows/)
- [plagiarismtoday inauthentic](https://www.plagiarismtoday.com/2025/07/08/youtube-targets-inauthentic-content/)
- [SEOSherpa policy update](https://seosherpa.com/youtube-changes-monetization-policy/)
- [Fliki monetization 2025](https://fliki.ai/blog/youtube-monetization-policy-2025)
- [Knolli AI compliance](https://www.knolli.ai/post/youtube-ai-monetization-policy-2025)
- [influencermarketinghub inauthentic standards](https://influencermarketinghub.com/youtube-inauthentic-content/)
- [blackenterprise AI crackdown](https://www.blackenterprise.com/youtube-inauthentic-ai-generated-content-demonetization/)
- [onewrk AI disclosure 2025 guide](https://onewrk.com/youtubes-ai-disclosure-requirements-the-complete-2025-guide/)
- [YouTube blog disclosing AI content](https://blog.youtube/news-and-events/disclosing-ai-generated-content/)
- [syncstudio synthetic content policy](https://syncstudio.ai/blog/youtube-synthetic-content-disclosure)
- [YouTube altered/synthetic disclosure help](https://support.google.com/youtube/answer/14328491)
- [influencermarketinghub AI disclosure platforms](https://influencermarketinghub.com/ai-disclosure-rules/)
- [supertone Korean AI policy 2025](https://www.supertone.ai/en/work/youtube-ai-monetization-policy-2025-eng)
- [viralpulse AI shorts policy](https://viralpulse.net/en/blog/ai-shorts-youtube-policy)
- [news1 유튜브 AI 저품질](https://www.news1.kr/it-science/general-it/6041850)
- [fikad/pikaclip 2026 Korean trends](https://blog.fikad.boo/2026%ED%8A%B8%EB%A0%8C%EB%93%9C-5%EA%B0%80%EC%A7%80-%ED%95%B5%EC%8B%AC-%ED%82%A4%EC%9B%8C%EB%93%9C%EB%A1%9C-%EC%95%8C%EC%95%84%EB%B3%B4%EB%8A%94-%EC%9C%A0%ED%8A%9C%EB%B8%8C-%EC%87%BC%EC%B8%A0-%EC%A0%84%EB%A7%9D%EC%9D%80-83386)
- [opensurvey Korean short-form study](https://blog.opensurvey.co.kr/article/socialmedia-2023-2/)
- [마리끌레르 2025 YouTube Korea](https://www.marieclairekorea.com/culture/lifestyle/2025/12/youtube-2/)
- [YouTube Shorts music eligibility help](https://support.google.com/youtube/answer/13486873)
- [gyre.pro trending audio legally](https://gyre.pro/blog/using-trending-audio-legally-a-guide-for-youtube-creators)
- [postlinkapp copyright 2026](https://postlinkapp.com/blog/youtube-shorts-music-copyright)
- [fluxnote copyright guide 2026](https://fluxnote.io/guides/youtube-shorts-music-copyright-guide)
- [trackclub free music 2026](https://www.trackclub.com/resources/free-non-copyrighted-music-for-youtube-where-to-find-it-2026-guide)

---

*FEATURES.md — 2026-04-18 — naberal-shorts-studio Phase 6 research*
