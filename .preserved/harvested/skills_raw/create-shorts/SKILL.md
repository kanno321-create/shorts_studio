---
name: create-shorts
description: Generate a YouTube Shorts from a topic. Orchestrates research, scriptwriting, safety, voice, subtitle, video assembly, and QA agents with approval gate. Supports --channel for channel-specific content and --ab-test for A/B variant generation.
disable-model-invocation: true
argument-hint: "[topic] --channel [channel_name] --nlm-source [file_path] --ab-test - Enter topic, optional channel, optional NLM source, optional A/B test mode"
skills:
  - shorts-safety
---

# Create Shorts Pipeline

Execute the YouTube Shorts creation pipeline for topic: $ARGUMENTS

## Step 0: Parse Channel Argument

1. Parse $ARGUMENTS for `--channel [name]` flag:
   - Split $ARGUMENTS to extract topic text and --channel flag
   - Topic = everything before `--channel` (or all of $ARGUMENTS if no --channel)
   - Channel name = value after `--channel` (if present)

2. If `--channel` is present:
   - Validate channel name is one of the available channels by checking file existence:
     `.claude/skills/channel-[name]/SKILL.md`
   - If skill file NOT found: report error:
     "Unknown channel: [name]. Available channels: humor, politics, trend.
      To add a new channel, create .claude/skills/channel-[name]/SKILL.md"
     Then STOP.
   - If skill file found: Read the entire SKILL.md content
   - Extract these sections from the channel skill:
     - CHARACTER_GUIDE = everything under "## Character Guide" heading
     - VOICE_PRESET = everything under "## Voice Preset" heading
     - SUBTITLE_STYLE = everything under "## Subtitle Style" heading
     - VISUAL_IDENTITY = everything under "## Visual Identity" heading
   - Store these as CHANNEL_CONTEXT for injection into sub-agents
   - Set CHANNEL_NAME = [name]

3. If `--channel` is absent:
   - Set CHANNEL_CONTEXT = null
   - Set CHANNEL_NAME = "neutral"
   - Continue with existing behavior (backward compatible per D-07)

4. In Step 1 (Setup Output Directory), add channel field to metadata.json:
   ```json
   { "channel": "[CHANNEL_NAME]" }
   ```

5. **Parse --nlm-source flag:**
   - Extract `--nlm-source [file_path]` from $ARGUMENTS (optional)
   - If present: Set NLM_SOURCE = [file_path]
   - If absent: Set NLM_SOURCE = null

6. **Parse --ab-test flag:**
   - Extract `--ab-test` from $ARGUMENTS (boolean flag, no value)
   - If present: Set AB_TEST_MODE = true
   - If absent: Set AB_TEST_MODE = false

7. **Parse --music flag:**
   - Extract `--music` from $ARGUMENTS (boolean flag, no value)
   - If present: Set MUSIC_ENABLED = true
   - If absent: Set MUSIC_ENABLED = false

8. **Parse --avatar flag:**
   - Extract `--avatar` from $ARGUMENTS (boolean flag, no value)
   - If present: Set AVATAR_ENABLED = true
   - If absent: Set AVATAR_ENABLED = false

## A/B Test Orchestration (when AB_TEST_MODE=true)

When AB_TEST_MODE is true, the pipeline runs as a 2-variant loop:

### Directory Setup
- Create `output/YYYYMMDD-topic/variant-A/` and `output/YYYYMMDD-topic/variant-B/`
- Each variant gets its own full pipeline execution
- Shared: source.md (research is done once, shared between variants)

### Modified Step Flow
1. Step 0-2: Run ONCE (setup, research are shared)
2. Step 3 (Script): Dispatch shorts-scripter with `AB_TEST_MODE=true`
   - Scripter generates script-A.json and script-B.json
   - Move script-A.json to variant-A/, script-B.json to variant-B/
3. Step 4-5 (Safety + Approval): Run on BOTH scripts
   - Safety check each variant's script
   - Show both hooks to user for approval: "Variant A hook: [hook_A] | Variant B hook: [hook_B]"
4. Steps 6-9 (Voice, Subtitle, Assembly, QA): Run for EACH variant sequentially
   - First: variant-A full pipeline (voice -> subtitle -> assembly -> QA)
   - Then: variant-B full pipeline (voice -> subtitle -> assembly -> QA)
5. Step 10 (Upload): Upload EACH variant as separate videos
   - Each variant's metadata.json gets its own video_id
   - Both share the same experiment_id

### Metadata
Each variant's metadata.json includes:
```json
{
  "variant": "A",
  "experiment_id": "[YYYYMMDD]-[topic-slug]-exp",
  "ab_test": true
}
```

### Post-Upload Guidance (per D-06, D-07, D-08)
After uploading both variants, print:
```
=== A/B Test Upload Complete ===
Variant A: https://youtu.be/{video_id_A} (hook: {hook_style_A})
Variant B: https://youtu.be/{video_id_B} (hook: {hook_style_B})
Experiment ID: {experiment_id}

Note: Shorts do not support YouTube Test & Compare.
Both variants uploaded as separate videos.
Monitor performance in YouTube Studio or run:
  python scripts/analytics/analytics_collect.py --video-ids {vid_A},{vid_B}
```

## Step 1: Setup Output Directory

1. Get today's date in YYYYMMDD format
2. Sanitize the topic for use as a directory name:
   - If topic is Korean: create a short English slug (e.g., "AI 반도체 전쟁" -> "ai-semiconductor")
   - Replace spaces with hyphens, remove special characters, lowercase
3. Create directory: `output/[YYYYMMDD]-[sanitized-topic]/`
4. Check if `metadata.json` exists in that directory:
   - **If exists**: Read it. This is a pipeline RESUME. Skip any step with status "completed".
   - **If not exists**: Create initial metadata.json:

```json
{
  "topic": "$ARGUMENTS",
  "created_at": "[ISO timestamp]",
  "pipeline": "shorts",
  "channel": "[CHANNEL_NAME]",
  "output_dir": "output/[YYYYMMDD]-[sanitized-topic]/",
  "steps": {
    "research": {
      "status": "pending",
      "completed_at": null,
      "output": "source.md",
      "sources_count": 0
    },
    "script": {
      "status": "pending",
      "completed_at": null,
      "output": "script.json",
      "version": 0
    },
    "safety_check": {
      "status": "pending",
      "is_political": null,
      "has_real_names": null,
      "defamation_risk": null,
      "keyword_matches": [],
      "context_judgment": null,
      "real_names_found": [],
      "defamation_details": null,
      "auto_publish_blocked": false,
      "flags": []
    },
    "approval": {
      "status": "pending",
      "approved_at": null,
      "feedback_history": []
    },
    "voice": {
      "status": "pending",
      "completed_at": null,
      "output": "narration.mp3",
      "provider": null,
      "voice_id": null,
      "duration_seconds": null,
      "character_count": null
    },
    "subtitle": {
      "status": "pending",
      "completed_at": null,
      "output": "subtitles.srt",
      "model": "large-v3",
      "segment_count": null,
      "language_detected": null,
      "style": "shorts-standard"
    },
    "video_assembly": {
      "status": "pending",
      "completed_at": null,
      "output": "final.mp4",
      "render_mode": null,
      "duration_seconds": null,
      "resolution": null,
      "file_size_mb": null,
      "clips_count": null
    },
    "music": {
      "status": "pending",
      "provider": null,
      "track_name": null,
      "bgm_volume_db": null,
      "output": null
    },
    "avatar": {
      "status": "pending",
      "provider": null,
      "clips_generated": 0,
      "clips_fallback": 0,
      "total_cost": 0.0
    },
    "script_evaluation": {
      "status": "pending",
      "passed": null,
      "score": null,
      "attempts": 0,
      "last_feedback": null
    },
    "qa": {
      "status": "pending",
      "completed_at": null,
      "passed": null,
      "score": null,
      "total": 22,
      "failures": [],
      "warnings": [],
      "attempt_count": 0,
      "manual_review_required": false
    }
  }
}
```

## Step 2: Research

**Skip condition**: metadata.steps.research.status == "completed" AND source.md exists in output directory

If not skipped:
1. Dispatch the research sub-agent:
   - Agent: @shorts-researcher
   - Provide: topic = "$ARGUMENTS", output_dir = "[full output directory path]"
   - If CHANNEL_CONTEXT is not null, append to agent prompt:
     ---
     CHANNEL RESEARCH DIRECTION:
     This content is for the [CHANNEL_NAME] channel.
     [CHARACTER_GUIDE's Tone subsection only -- keep it concise]
     Research should find sources that fit this channel's tone and audience.
     ---
   - Wait for completion
2. Verify source.md was created in the output directory
3. Read source.md and confirm it has the required sections (Key Insights, Numerical Data, etc.)
4. If source.md is missing or incomplete, report error and stop

## Step 3: Script Generation

**Skip condition**: metadata.steps.script.status == "completed" AND script.json exists AND no new feedback pending

If not skipped:
1. Dispatch the script-writing sub-agent:
   - Agent: @shorts-scripter
   - Provide: source.md path, output_dir path
   - If feedback exists (from Step 5 loop): include feedback text
   - If AB_TEST_MODE is true: append `AB_TEST_MODE=true` to agent prompt
     - Scripter will generate script-A.json and script-B.json (dual variant output)
   - If CHANNEL_CONTEXT is not null, append to agent prompt:
     ---
     CHANNEL CHARACTER GUIDE:
     [Full CHARACTER_GUIDE section from channel skill]

     Apply the above character guide to ALL narration text.
     The script.json must include "channel": "[CHANNEL_NAME]" in the root object.
     Speech patterns, Do rules, and Don't rules are MANDATORY constraints.
     ---
   - Wait for completion
2. Verify script.json was created in the output directory
3. Read script.json and validate:
   - Has sections array with at least 3 items (hook + body + cta)
   - estimated_duration >= 50.0 and <= 120.0
   - total_characters >= 425 and <= 1020
   - Each section has narration_segments array with per-sentence emotions
   - Topic keywords appear in narration text (주제-내용 일치 검증)
   - No duplicate sentences across sections
4. If validation fails, report the specific issue

## Step 3.5: Script Evaluation

**Skip condition**: metadata.steps.script_evaluation.status == "completed" AND metadata.steps.script_evaluation.passed == true

**Purpose**: Automated quality gate between script generation and safety check. Per D-02 (HARN-01), evaluates script.json using deterministic + LLM-graded criteria.

If not skipped:
1. Initialize evaluation counter: eval_attempt = 0
2. **Evaluation Loop** (max 2 iterations per D-04):
   a. Dispatch the script evaluator sub-agent:
      - Agent: @shorts-script-evaluator
      - Provide: script.json path, output_dir path
      - If CHANNEL_CONTEXT is not null, append to agent prompt:
        ---
        CHANNEL CHARACTER GUIDE:
        [Full CHARACTER_GUIDE section from channel skill]
        Evaluate tone_matching against this guide.
        ---
      - Wait for completion
   b. Parse the JSON result from evaluator stdout
   c. If evaluator result.pass == true:
      - Update metadata.json: script_evaluation.status = "completed", script_evaluation.passed = true, script_evaluation.score = result.overall
      - Display:
        ```
        ============================================================
        SCRIPT EVALUATION PASSED
        ============================================================
        Deterministic: [result.deterministic_score]
        LLM Overall: [result.overall]/5.0
        ============================================================
        ```
      - Continue to Step 4
   d. If evaluator result.pass == false AND eval_attempt < 2:
      - eval_attempt += 1
      - Display:
        ```
        ============================================================
        SCRIPT EVALUATION FAILED - RETRY [eval_attempt]/2
        ============================================================
        Score: [result.overall]/5.0 (threshold: 3.5)
        Feedback: [result.feedback]
        ============================================================
        ```
      - Re-dispatch @shorts-scripter with evaluator feedback:
        - Pass result.feedback as the feedback parameter
        - Reset script step status to "pending"
        - Return to Step 3 to regenerate, then re-enter Step 3.5
   e. If evaluator result.pass == false AND eval_attempt >= 2:
      - Update metadata.json: script_evaluation.status = "failed", script_evaluation.passed = false, script_evaluation.attempts = eval_attempt, script_evaluation.last_feedback = result.feedback
      - Display:
        ```
        ============================================================
        SCRIPT EVALUATION FAILED - HUMAN REVIEW
        ============================================================
        Score: [result.overall]/5.0
        Attempts: 2/2
        Feedback: [result.feedback]

        Proceeding to approval gate for manual review.
        ============================================================
        ```
      - Continue to Step 5 (Approval Gate) — user can manually approve despite evaluation failure per D-04

## Step 4: Safety Check

**Skip condition**: metadata.steps.safety_check.status == "completed" AND script version hasn't changed

Run the safety check in THIS context (main conversation), NOT in a sub-agent. This is critical because the approval gate in Step 5 needs user interaction, which only works in the foreground.

Follow the detection methodology defined in the shorts-safety skill (preloaded via frontmatter):

1. Read script.json from the output directory
2. Concatenate all narration text from sections
3. **Layer 1 - Keyword Scan**: Follow the shorts-safety skill's Layer 1 rules
   - Read `.claude/skills/shorts-safety/references/political-keywords.json`
   - Check concatenated narration against all keyword categories
   - Record any matches in keyword_matches array
4. **Layer 2 - AI Contextual Judgment**: Follow the shorts-safety skill's Layer 2 rules
   - Evaluate the full script content for political content, real names, and defamation risk
   - Apply the contextual criteria from the safety skill (context matters, not just keyword presence)
   - Record judgment in context_judgment field
5. **Determine flags**: Follow the shorts-safety skill's Decision Rules
   - If is_political: add "POLITICAL" to flags
   - If has_real_names: add "REAL_NAMES" to flags
   - If defamation_risk: add "DEFAMATION_RISK" to flags
   - If ANY flag exists: set auto_publish_blocked = true
6. Update metadata.json with safety_check results (format per shorts-safety skill's Output Format)

## Step 5: Approval Gate

Present the script to the user for review. This step ALWAYS runs (never auto-skipped).

### Display Format:

```
============================================================
SHORTS SCRIPT REVIEW
============================================================

Topic: [topic]
Estimated Duration: [estimated_duration]s / 58s target
Total Characters: [total_characters] / 244 max

------------------------------------------------------------
NARRATION
------------------------------------------------------------

[HOOK - 3s]
[hook narration text]
Visual: [hook visual direction]

[BODY Scene 1 - Xs]
[body scene 1 narration]
Visual: [body scene 1 visual]

[BODY Scene 2 - Xs]
[body scene 2 narration]
Visual: [body scene 2 visual]

[CTA - 5s]
[cta narration text]
Visual: [cta visual direction]

------------------------------------------------------------
SOURCES USED
------------------------------------------------------------
1. [url1]
2. [url2]
```

### Safety Warnings (if any flags):

If `is_political == true`:
```
POLITICAL CONTENT DETECTED
Auto-publish is BLOCKED for this content.
Keywords matched: [list]
AI judgment: [context_judgment]

This content requires your explicit approval before ANY further processing.
Under Korean Criminal Code Article 307, political content carries defamation risk.
```

If `has_real_names == true`:
```
REAL NAMES DETECTED: [list of names]
Defamation risk under Article 307 applies to named individuals.
AI has NOT modified the content. You must decide whether to keep, modify, or remove references.
```

If `defamation_risk == true`:
```
DEFAMATION RISK WARNING
[defamation_details]
Korean Criminal Code Article 307(1): True facts damaging reputation = up to 2 years / 5M KRW
Korean Criminal Code Article 307(2): False facts damaging reputation = up to 5 years / 10M KRW
```

### User Response Options:

```
Choose one:
1. APPROVE - Accept this script as-is (type "승인" or "approve")
2. FEEDBACK - Request changes (type your feedback, e.g., "훅을 더 강렬하게", "톤을 더 부드럽게")
3. REJECT - Discard this script (type "거부" or "reject")
```

### Response Handling:

- **APPROVE** ("승인", "approve", "ok", "좋아", "확인"):
  - Update metadata.json: approval.status = "approved", approval.approved_at = [timestamp]
  - Display: "Script approved. Proceeding to voice generation..."
  - Continue to Step 6 (Voice Generation)

- **FEEDBACK** (any other text):
  - Save feedback to metadata.json: approval.feedback_history.push({"feedback": "[text]", "timestamp": "[ISO]", "version": [current version]})
  - Reset script step: metadata.steps.script.status = "pending"
  - Return to Step 3 with feedback text passed to the scripter agent
  - Note: This creates a loop until user approves or rejects

- **REJECT** ("거부", "reject", "취소"):
  - Update metadata.json: approval.status = "rejected"
  - Display: "Script rejected. Pipeline stopped. Re-run /create-shorts to start fresh."

## Step 6: Voice Generation

**Skip condition**: metadata.steps.voice.status == "completed" AND narration.mp3 exists in output directory

If not skipped:
1. Dispatch the voice sub-agent:
   - Agent: @shorts-voice
   - Provide: output_dir = "[full output directory path]"
   - If CHANNEL_CONTEXT is not null, append to agent prompt:
     ---
     CHANNEL VOICE PRESET:
     [VOICE_PRESET section from channel skill]

     Use the channel's ElevenLabs voice_id and parameters as INLINE CLI flags to tts_generate.py.
     Do NOT use --voice-preset flag. Pass --voice-id, --stability, --similarity-boost, --style, --edge-voice directly.
     If voice_id is PLACEHOLDER_PENDING_USER_APPROVAL, report to user and use EdgeTTS fallback voice from this channel's preset.
     ---
   - Wait for completion
2. Verify narration.mp3 was created in the output directory
3. Read metadata.json and confirm voice step is "completed"
4. Display voice generation results:

```
============================================================
VOICE GENERATION COMPLETE
============================================================
Provider: [elevenlabs / edge-tts]
Duration: [X.X] seconds
Characters: [N]
============================================================
```

5. If voice step failed, report error and stop
6. If provider is "edge-tts", display notice:

```
[NOTICE] EdgeTTS fallback was used. Audio quality may be lower than ElevenLabs.
To use ElevenLabs, ensure ELEVEN_API_KEY is set and credits are available.
```

## Step 6.5: Background Music

**Skip condition**: MUSIC_ENABLED == false OR (metadata.steps.music.status == "completed" AND mixed_audio.mp3 exists in output directory)

If not skipped:
0. If MUSIC_ENABLED is false, skip this step entirely. Set metadata.steps.music.status = "skipped" and AUDIO_PATH = "[output_dir]/narration.mp3". Proceed to Step 7.

1. Run the music step directly (no sub-agent needed):
   ```
   python -c "
   import sys, os; sys.path.insert(0, '.')
   from scripts.music.music_generator import execute_music_step
   srt_file = '[output_dir]/subtitles.srt'
   result = execute_music_step(
       narration_path='[output_dir]/narration.mp3',
       channel='[CHANNEL_NAME]',
       pipeline_type='shorts',
       config_path='config/music-config.json',
       output_dir='[output_dir]',
       srt_path=srt_file if os.path.exists(srt_file) else None,
   )
   print(result)
   "
   ```
   - CHANNEL_NAME is the channel parsed in Step 0 (humor / politics / trend)
   - pipeline_type is always "shorts" for this skill
   - srt_path enables BGM ducking (VFEX-11) when subtitles.srt exists
   - manifest_path is NOT passed here -- scene-manifest.json doesn't exist yet at Step 6.5
   - SFX pre-mix (VFEX-14) is handled by the editor after manifest creation
   - The function returns either the path to mixed_audio.mp3 (success) or narration.mp3 (fallback)
   - On ANY failure, the function returns narration.mp3 — the pipeline NEVER stops due to music errors (D-05b)

2. Determine the audio file for subsequent steps:
   - If mixed_audio.mp3 exists in output_dir: AUDIO_PATH = "[output_dir]/mixed_audio.mp3"
   - If mixed_audio.mp3 does NOT exist: AUDIO_PATH = "[output_dir]/narration.mp3" (silence fallback)

3. Update metadata.json:
   ```json
   "steps": {
     "music": {
       "status": "completed",
       "provider": "[pixabay_local or silence_fallback]",
       "track_name": "[selected track filename or null]",
       "bgm_volume_db": -15,
       "output": "[mixed_audio.mp3 or narration.mp3]"
     }
   }
   ```

4. Display music step results:

```
============================================================
BACKGROUND MUSIC COMPLETE
============================================================
Provider: [pixabay_local / silence_fallback]
Track: [track_name or "None (silence fallback)"]
Volume: -15 dB (shorts default)
Output: [AUDIO_PATH]
============================================================
```

5. If the music step used silence fallback, display notice:

```
[NOTICE] BGM was skipped (no tracks available or mixing failed).
         Using narration-only audio. Video quality is not affected.
```

## Step 7: Subtitle Generation

**Skip condition**: metadata.steps.subtitle.status == "completed" AND subtitles.srt exists in output directory

If not skipped:
1. Dispatch the subtitle sub-agent:
   - Agent: @shorts-subtitle
   - Provide: output_dir = "[full output directory path]"
   - Wait for completion
2. Verify subtitles.srt was created in the output directory
3. Read metadata.json and confirm subtitle step is "completed"
4. Display subtitle generation results:

```
============================================================
SUBTITLE GENERATION COMPLETE
============================================================
Segments: [N]
Language: [detected language]
Style: [style name]
============================================================
```

5. If subtitle step failed, report error and stop
6. Display: "Subtitles ready. Proceeding to video assembly..."

## Step 7.5: Avatar Generation

**Skip condition**: AVATAR_ENABLED == false OR metadata.steps.avatar.status == "completed"

If not skipped:
1. AVATAR_ENABLED was parsed in Step 0. If false, this step was already skipped by the skip condition above.

2. Run the avatar step directly (no sub-agent needed):
   ```
   python -c "
   import sys, json; sys.path.insert(0, '.')
   from scripts.avatar.avatar_generator import execute_avatar_step, load_avatar_config
   config = load_avatar_config('config/avatar-config.json')
   sections = json.load(open('[output_dir]/script.json'))['sections']
   result = execute_avatar_step(
       sections=sections,
       narration_path='[output_dir]/narration.mp3',
       subtitles_path='[output_dir]/subtitles.srt',
       output_dir='[output_dir]',
       channel='[CHANNEL_NAME]',
       pipeline_type='shorts',
       avatar_config=config,
       avatar_enabled=True,
   )
   print(json.dumps(result))
   "
   ```
   Where:
   - [output_dir] is the project output directory from Step 0
   - [CHANNEL_NAME] is the channel parsed in Step 0
   - pipeline_type is always "shorts" for this skill
   - The function returns a dict mapping section_index -> clip_path for avatar scenes
   - On ANY failure, the function returns {} — pipeline NEVER stops due to avatar errors (per D-04)

3. Update scene-manifest.json with avatar clips:
   For each section_index in the result dict:
   - Find the corresponding scene in scene-manifest.json
   - Replace `source.local_path` with the avatar clip path
   - Set `source.type` to `"avatar"`
   - Set `source.provider` to `"heygen"`
   Scenes NOT in the result dict remain unchanged (stock/B-Roll).

4. Update metadata.json:
   ```json
   "steps": {
     "avatar": {
       "status": "completed",
       "provider": "heygen",
       "clips_generated": [count of avatar clips],
       "clips_fallback": [count of avatar scenes that fell back to stock],
       "total_cost": [sum of costs from result]
     }
   }
   ```
   If avatar was skipped (no --avatar flag or avatar_enabled=False):
   ```json
   "avatar": {
     "status": "skipped",
     "provider": null,
     "clips_generated": 0,
     "clips_fallback": 0,
     "total_cost": 0.0
   }
   ```

5. If any avatar scenes fell back to stock, record in metadata.json:
   ```json
   "avatar_fallback": true,
   "avatar_fallback_reason": "[error message from execute_avatar_step logs]"
   ```
   Per D-04d: QA can check for avatar_fallback field.

6. Record avatar cost to costs.db (per D-04c):
   ```
   python -c "
   import sys; sys.path.insert(0, '.')
   from ui.components.costs import get_costs_rw_connection, ensure_costs_table, record_video_cost
   conn = get_costs_rw_connection()
   if conn:
       ensure_costs_table(conn)
       record_video_cost(conn, '[TITLE]', '[CHANNEL]', 'shorts', 0.0, 0.0, 0.0, [avatar_total_cost])
       conn.close()
   "
   ```
   Note: This records ONLY the avatar cost. Other costs (TTS, B-Roll, music) are recorded by their respective steps or by the final assembly step. If avatar cost is 0 (skipped/fallback), skip this recording.

7. Display avatar step results:
   ```
   ============================================================
   AVATAR STEP COMPLETE
   Provider: heygen (Avatar III)
   Clips generated: [N]
   Clips fallback to stock: [M]
   Total cost: $[X.XX]
   ============================================================
   ```

## Step 8: Video Assembly

**Avatar clips**: If Step 7.5 ran, some scenes in scene-manifest.json now have source.type="avatar" and source.local_path pointing to HeyGen MP4 files. These are standard MP4 H.264 files and are handled identically to stock clips by build_filter_complex — no special treatment needed (per D-03, D-03b).

**Audio input**: Uses AUDIO_PATH from Step 6.5 (mixed_audio.mp3 if BGM was applied, or narration.mp3 if BGM was skipped/failed). BGM ducking (VFEX-11) is applied via srt_path in Step 6.5.

**Remotion pipeline**: Video assembly uses Remotion (React) instead of FFmpeg. The designer creates visual_spec.json, and the editor calls render_shorts_video() to produce final.mp4.

**Skip condition**: metadata.steps.video_assembly.status == "completed" AND final.mp4 exists in output directory

If not skipped:

### Step 8a: Visual Design
1. Dispatch the designer sub-agent:
   - Agent: @shorts-designer
   - Provide: output_dir = "[full output directory path]"
   - If CHANNEL_CONTEXT is not null, append to agent prompt:
     ---
     CHANNEL VISUAL IDENTITY:
     [VISUAL_IDENTITY section from channel skill]
     Use the channel's accent colors for titleKeywords.
     ---
   - Wait for completion
2. Verify visual_spec.json was created in the output directory

### Step 8b: Final Render
3. Dispatch the editor sub-agent:
   - Agent: @shorts-editor
   - Provide: output_dir = "[full output directory path]"
   - Wait for completion
2. Read metadata.json and check video_assembly step result
3. If video_assembly status is "completed":
   - Verify final.mp4 exists in the output directory
   - Display video assembly results:

```
============================================================
VIDEO ASSEMBLY COMPLETE
============================================================
Render Mode: [stock / graphic]
Duration: [X.X] seconds
Resolution: [1080x1920]
File Size: [X.X] MB
Clips: [N] clips assembled
============================================================
```

4. If video_assembly status is "skipped" (render_mode was "graphic"):
   - Display notice:

```
============================================================
VIDEO ASSEMBLY SKIPPED
============================================================
Render mode "graphic" (Remotion) is not yet implemented.
The pipeline produced: script.json, narration.mp3, subtitles.srt
Video assembly will be available when Remotion support is added.
============================================================
```
   - Stop pipeline. Do not proceed to Step 9.

5. If video_assembly failed, report error and stop

## Step 9: QA Check

**Skip condition**: metadata.steps.qa.status == "completed" AND metadata.steps.qa.passed == true

If not skipped:
1. Dispatch the QA sub-agent:
   - Agent: @shorts-qa
   - Provide: output_dir = "[full output directory path]"
   - Wait for completion
2. Read metadata.json and check QA result

### QA Result Handling:

**If qa.passed == true (D-12 auto-complete):**
- Display pipeline success:

```
============================================================
SHORTS PIPELINE COMPLETE
============================================================
Topic: [topic]
Output: [output_dir]/final.mp4
Duration: [X.X] seconds
Resolution: 1080x1920
File Size: [X.X] MB
QA Score: [N]/22 passed

Status: Ready for upload.
============================================================
```

**If qa.passed == false AND qa.attempt_count < 2 (auto-retry):**
- Display retry message:

```
============================================================
QA FAILED - AUTO-RETRY
============================================================
Score: [N]/22
Failed items: [list of QA-XX IDs]
Attempt: [N] of 2

Retrying video assembly with feedback...
============================================================
```
- Return to Step 8 (video_assembly step has been reset to "pending" by the QA agent)

**If qa.passed == false AND qa.attempt_count >= 2 (D-11 manual review):**
- Display failure details:

```
============================================================
QA FAILED - MANUAL REVIEW REQUIRED
============================================================
Score: [N]/22
Failed items:
  - [QA-XX]: [failure description]
  - [QA-YY]: [failure description]
Attempts: 2 of 2

The video failed automated QA after 2 attempts.
============================================================
```

- Present options to user:

```
Choose one:
1. ACCEPT - Accept the video despite QA failures (type "accept")
2. FEEDBACK - Provide manual guidance for re-assembly (type your feedback)
3. ABORT - Stop the pipeline (type "abort")
```

- **ACCEPT**: Update qa status to "completed" with manual_override = true. Display "Video accepted with manual override. Ready for upload."
- **FEEDBACK**: Reset video_assembly to "pending", reset qa.attempt_count to 0. Return to Step 8 with feedback.
- **ABORT**: Update pipeline status to "aborted". Display "Pipeline aborted."

## Step 10: Upload to YouTube

**Skip condition**: metadata.steps.upload.status == "completed"

**Pre-condition**: metadata.steps.qa.passed == true (Step 9 must have passed or been manually accepted)

If not skipped:

### 10.1 Safety Gate Check
1. Read metadata.json from output directory
2. Check `metadata.steps.safety_check.auto_publish_blocked`:
   - If `true`: Display safety block message and STOP. Do NOT proceed to upload.
   ```
   ============================================================
   UPLOAD BLOCKED — SAFETY GATE
   ============================================================
   This content has been flagged by safety check.
   Flags: [list flags from metadata.steps.safety_check.flags]

   Upload is blocked. Review and resolve safety flags first.
   ============================================================
   ```
   - If `false` or absent: Continue to confirmation.

### 10.2 User Confirmation
1. Display upload preview:
   ```
   ============================================================
   UPLOAD PREVIEW
   ============================================================
   Title: [script.json title]
   Channel: [CHANNEL_NAME]
   Privacy: private (default)
   Video: [output_dir]/final.mp4
   Thumbnail: [output_dir]/thumbnail.jpg (if exists)

   Proceed with upload? (yes/no)
   ============================================================
   ```
2. Wait for user input:
   - "yes" → Continue to upload
   - "no" → Display "Upload cancelled." and STOP pipeline

### 10.3 Execute Upload
1. Run youtube_upload.py:
   ```bash
   python scripts/upload/youtube_upload.py \
     --video [output_dir]/final.mp4 \
     --metadata [output_dir]/metadata.json \
     --script [output_dir]/script.json \
     --channel [CHANNEL_NAME] \
     --thumbnail [output_dir]/thumbnail.jpg
   ```
   - Omit `--thumbnail` if thumbnail.jpg does not exist in output_dir
2. Parse JSON output: `{status, video_id, youtube_url}`
3. If upload fails: Display error and STOP

### 10.4 Post-Upload
1. metadata.json is automatically updated by youtube_upload.py with:
   ```json
   {
     "steps": {
       "upload": {
         "status": "completed",
         "video_id": "[VIDEO_ID]",
         "upload_time": "[ISO timestamp]",
         "privacy_status": "private",
         "youtube_url": "https://youtu.be/[VIDEO_ID]"
       }
     }
   }
   ```
2. Display success:
   ```
   ============================================================
   SHORTS UPLOAD COMPLETE
   ============================================================
   Video ID: [VIDEO_ID]
   URL: https://youtu.be/[VIDEO_ID]
   Privacy: private
   Channel: [CHANNEL_NAME]

   Video uploaded as PRIVATE. Change visibility in YouTube Studio:
   https://studio.youtube.com/video/[VIDEO_ID]/edit
   ============================================================
   ```
