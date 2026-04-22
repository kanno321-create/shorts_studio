---
name: create-video
description: "⚠️ DEPRECATED — 롱폼은 longform/PIPELINE.md 가 진실 원천. 이 스킬은 v5 이전 구조. Phase 43 Wave 4 (세션 64) deprecated."
disable-model-invocation: true
argument-hint: "DEPRECATED — use longform/PIPELINE.md instead"
skills:
  - shorts-safety
---

# ⚠️ DEPRECATED — Create Video Pipeline

> **이 스킬은 사용하지 마라.** 롱폼 영상 제작은 `longform/PIPELINE.md` (13-18분, 4막 구조) 가 유일한 진실 원천.
> 이 파일의 Stage 1-8 절차는 v5 이전 구조이며 현행 `longform/agents/` 에이전트와 불일치.
> Phase 43 Wave 4 (세션 64, 2026-04-16) deprecated.

Execute the YouTube general video creation pipeline for topic: $ARGUMENTS

Pipeline type: **video** (16:9, 5-15 minutes, multi-chapter)

## Step 0: Parse Arguments

1. Parse $ARGUMENTS for flags:
   - `--channel [name]` flag: channel-specific tone and style
   - `--duration [N]` flag: target duration in minutes (default: 10)
   - Topic = everything before the first `--` flag (or all of $ARGUMENTS if no flags)

2. Validate duration:
   - Parse --duration value as integer (default: 10)
   - If < 5: warn "Minimum duration is 5 minutes" and clamp to 5
   - If > 15: warn "Maximum duration is 15 minutes" and clamp to 15
   - Set TARGET_DURATION_SECONDS = duration * 60

3. Set PIPELINE_TYPE = "video" (hardcoded -- this is the video director)

4. If `--channel` is present:
   - Validate channel name by checking: `.claude/skills/channel-[name]/SKILL.md`
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

5. If `--channel` is absent:
   - Set CHANNEL_CONTEXT = null
   - Set CHANNEL_NAME = "neutral"

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
3. Step 4 (Safety + Approval): Run on BOTH scripts
   - Safety check each variant's script
   - Show both hooks to user for approval: "Variant A hook: [hook_A] | Variant B hook: [hook_B]"
4. Steps 5-9 (Voice, Subtitle, Scene Design, Assembly, QA): Run for EACH variant sequentially
   - First: variant-A full pipeline
   - Then: variant-B full pipeline
5. Upload: Upload EACH variant as separate videos
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

### Post-Upload Guidance for General Videos (per D-06, D-08)
After uploading variant A, print:
```
=== A/B Test Upload Complete ===
Variant A: https://youtu.be/{video_id_A} (hook: {hook_style_A})
Variant B: https://youtu.be/{video_id_B} (hook: {hook_style_B})
Experiment ID: {experiment_id}

For YouTube Test & Compare (thumbnails/titles):
  Visit: https://studio.youtube.com/video/{video_id_A}/edit
  Click "Test & Compare" to add thumbnail variants.
  Thumbnail candidates saved to: output/YYYYMMDD-topic/thumbnails/
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
  "topic": "[topic text]",
  "created_at": "[ISO timestamp]",
  "pipeline_type": "video",
  "channel": "[CHANNEL_NAME]",
  "target_duration_seconds": "[TARGET_DURATION_SECONDS]",
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
      "character_count": null,
      "chapter_count": null
    },
    "subtitle": {
      "status": "pending",
      "completed_at": null,
      "output": "subtitles.srt",
      "model": "large-v3",
      "segment_count": null,
      "language_detected": null,
      "style": "video-standard"
    },
    "scene_design": {
      "status": "pending",
      "completed_at": null,
      "output": "scene-manifest.json",
      "schema_version": "2.0",
      "clips_count": null
    },
    "video_assembly": {
      "status": "pending",
      "completed_at": null,
      "output": "final.mp4",
      "render_mode": null,
      "duration_seconds": null,
      "resolution": null,
      "file_size_mb": null,
      "clips_count": null,
      "chapters_count": null
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
    "qa": {
      "status": "pending",
      "completed_at": null,
      "passed": null,
      "score": null,
      "total": 23,
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
   - Provide: topic = "[topic text]", output_dir = "[full output directory path]"
   - Append to agent prompt:
     ---
     VIDEO RESEARCH MODE:
     This is for a 5-15 minute general video (pipeline_type: video).
     Research should gather enough material for 3-7 chapters.
     Find multiple angles, perspectives, and data points for chapter variety.
     Include more numerical data and expert quotes than a shorts research.
     Target: enough verified content for [TARGET_DURATION_SECONDS / 60] minutes of narration.
     ---
   - If CHANNEL_CONTEXT is not null, also append:
     ---
     CHANNEL RESEARCH DIRECTION:
     This content is for the [CHANNEL_NAME] channel.
     [CHARACTER_GUIDE's Tone subsection only]
     Research should find sources that fit this channel's tone and audience.
     ---
   - Wait for completion
2. Verify source.md was created in the output directory
3. Read source.md and confirm it has the required sections
4. If source.md is missing or incomplete, report error and stop
5. Update metadata.json: steps.research.status = "completed"

## Step 3: Script Writing

**Skip condition**: metadata.steps.script.status == "completed" AND script.json exists AND no new feedback pending

If not skipped:
1. Dispatch the script-writing sub-agent:
   - Agent: @shorts-scripter
   - Provide: source.md path, output_dir path
   - If AB_TEST_MODE is true: append `AB_TEST_MODE=true` to agent prompt
     - Scripter will generate script-A.json and script-B.json (dual variant output)
   - Append to agent prompt:
     ---
     VIDEO SCRIPT MODE:
     pipeline_type: "video"
     target_duration: [TARGET_DURATION_SECONDS] seconds
     Write a multi-chapter script with intro/chapter_N/conclusion structure.
     Each chapter must have a scenes array with visual descriptions and duration_target.
     Target 3-7 chapters based on topic complexity.
     ---
   - If feedback exists (from Step 4 loop): include feedback text
   - If CHANNEL_CONTEXT is not null, append:
     ---
     CHANNEL CHARACTER GUIDE:
     [Full CHARACTER_GUIDE section from channel skill]

     Apply the above character guide to ALL narration text.
     The script.json must include "channel": "[CHANNEL_NAME]" and "pipeline_type": "video" in the root object.
     Speech patterns, Do rules, and Don't rules are MANDATORY constraints.
     ---
   - Wait for completion
2. Verify script.json was created in the output directory
3. Read script.json and validate:
   - Has pipeline_type: "video"
   - Has chapters array with at least 3 items (intro + chapter(s) + conclusion)
   - Each chapter has scenes array with visual and duration_target fields
   - total estimated duration is within 20% of TARGET_DURATION_SECONDS
4. If validation fails, report the specific issue
5. Update metadata.json: steps.script.status = "completed"

## Step 4: Safety Check + Approval Gate

**Skip condition**: metadata.steps.approval.status == "approved"

Run the safety check in THIS context (main conversation), NOT in a sub-agent.

### Safety Check

1. Read script.json from the output directory
2. Concatenate all narration text from all chapters and scenes
3. **Layer 1 - Keyword Scan**: Follow the shorts-safety skill's Layer 1 rules
   - Read `.claude/skills/shorts-safety/references/political-keywords.json`
   - Check concatenated narration against all keyword categories
   - Record any matches in keyword_matches array
4. **Layer 2 - AI Contextual Judgment**: Follow the shorts-safety skill's Layer 2 rules
   - Evaluate the full script content for political content, real names, and defamation risk
   - Record judgment in context_judgment field
5. **Determine flags**: Follow the shorts-safety skill's Decision Rules
   - If is_political: add "POLITICAL" to flags
   - If has_real_names: add "REAL_NAMES" to flags
   - If defamation_risk: add "DEFAMATION_RISK" to flags
   - If ANY flag exists: set auto_publish_blocked = true
6. Update metadata.json with safety_check results

### Approval Gate

Present the script to the user for review. This step ALWAYS runs (never auto-skipped).

```
============================================================
VIDEO SCRIPT REVIEW
============================================================

Topic: [topic]
Pipeline: video (16:9, general)
Target Duration: [TARGET_DURATION_SECONDS / 60] minutes
Chapters: [N] chapters

------------------------------------------------------------
CHAPTER STRUCTURE
------------------------------------------------------------

[INTRO]
[intro narration summary, first 100 chars...]
Scenes: [N] scenes

[CHAPTER 1: title]
[chapter 1 narration summary, first 100 chars...]
Scenes: [N] scenes

[CHAPTER 2: title]
...

[CONCLUSION]
[conclusion narration summary, first 100 chars...]
Scenes: [N] scenes

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
```

If `has_real_names == true`:
```
REAL NAMES DETECTED: [list of names]
Defamation risk under Article 307 applies to named individuals.
```

If `defamation_risk == true`:
```
DEFAMATION RISK WARNING
[defamation_details]
법적 근거: 형법 제307조 ①항(사실 적시 명예훼손, 2년 이하 징역 또는 500만원 이하 벌금) 및 ②항(허위 사실 적시, 5년 이하 징역, 10년 이하 자격정지, 1천만원 이하 벌금)
```

### User Response Options:

```
Choose one:
1. APPROVE - Accept this script as-is (type "approve")
2. FEEDBACK - Request changes (type your feedback)
3. REJECT - Discard this script (type "reject")
```

- **APPROVE** ("approve", "ok"): Update approval status, continue to Step 5
- **FEEDBACK** (any other text): Save feedback, reset script status, return to Step 3
- **REJECT** ("reject"): Update status to "rejected", STOP pipeline

## Step 5: TTS Generation

**Skip condition**: metadata.steps.voice.status == "completed" AND narration.mp3 exists in output directory

If not skipped:
1. Dispatch the voice sub-agent:
   - Agent: @shorts-voice
   - Provide: output_dir = "[full output directory path]"
   - Append to agent prompt:
     ---
     VIDEO TTS MODE:
     pipeline_type: "video"
     Run tts_generate.py with --pipeline video flag.
     Command: python scripts/audio-pipeline/tts_generate.py --input [output_dir]/script.json --output [output_dir]/narration.mp3 --pipeline video --voice-preset [VOICE_PRESET or default] --config-dir config
     The script will auto-split by chapter, generate chapter_NN.mp3 files, and concat with 0.3s silence gaps.
     ElevenLabs previous_request_ids is used for prosody continuity across chapters (max 3).
     ---
   - If CHANNEL_CONTEXT is not null, append:
     ---
     CHANNEL VOICE PRESET:
     [VOICE_PRESET section from channel skill]

     Use the channel's ElevenLabs voice_id and parameters as INLINE CLI flags to tts_generate.py.
     Do NOT use --voice-preset flag. Pass --voice-id, --stability, --similarity-boost, --style, --edge-voice directly.
     If voice_id is PLACEHOLDER_PENDING_USER_APPROVAL, report to user and use EdgeTTS fallback voice.
     ---
   - Wait for completion
2. Verify narration.mp3 was created in the output directory
3. Display voice generation results:

```
============================================================
VOICE GENERATION COMPLETE
============================================================
Provider: [elevenlabs / edge-tts]
Duration: [X.X] seconds
Chapters: [N] chapters generated and merged
============================================================
```

4. Update metadata.json: steps.voice.status = "completed"

## Step 5.5: Background Music

**Skip condition**: MUSIC_ENABLED == false OR (metadata.steps.music.status == "completed" AND mixed_audio.mp3 exists in output directory)

If not skipped:
0. If MUSIC_ENABLED is false, skip this step entirely. Set metadata.steps.music.status = "skipped" and AUDIO_PATH = "[output_dir]/narration.mp3". Proceed to Step 6.

1. Run the music step directly (no sub-agent needed):
   ```
   python -c "
   import sys; sys.path.insert(0, '.')
   from scripts.music.music_generator import execute_music_step
   result = execute_music_step(
       narration_path='[output_dir]/narration.mp3',
       channel='[CHANNEL_NAME]',
       pipeline_type='video',
       config_path='config/music-config.json',
       output_dir='[output_dir]'
   )
   print(result)
   "
   ```
   - CHANNEL_NAME is the channel parsed in Step 0 (humor / politics / trend)
   - pipeline_type is always "video" for this skill
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
       "bgm_volume_db": -20,
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
Volume: -20 dB (video default)
Output: [AUDIO_PATH]
============================================================
```

5. If the music step used silence fallback, display notice:

```
[NOTICE] BGM was skipped (no tracks available or mixing failed).
         Using narration-only audio. Video quality is not affected.
```

## Step 6: Subtitle Generation

**Skip condition**: metadata.steps.subtitle.status == "completed" AND subtitles.srt exists in output directory

If not skipped:
1. Dispatch the subtitle sub-agent:
   - Agent: @shorts-subtitle
   - Provide: output_dir = "[full output directory path]"
   - Append to agent prompt:
     ---
     VIDEO SUBTITLE MODE:
     pipeline_type: "video"
     Run subtitle_generate.py with --pipeline video flag.
     Command: python scripts/audio-pipeline/subtitle_generate.py --input [output_dir]/narration.mp3 --output [output_dir]/subtitles.srt --pipeline video --chapter-dir [output_dir] --style video-standard --config-dir config
     Subtitles will be generated per-chapter and merged with time offsets based on actual chapter audio durations.
     ---
   - Wait for completion
2. Verify subtitles.srt was created in the output directory
3. Display subtitle generation results:

```
============================================================
SUBTITLE GENERATION COMPLETE
============================================================
Segments: [N]
Language: [detected language]
Style: video-standard
============================================================
```

4. Update metadata.json: steps.subtitle.status = "completed"

## Step 6.5: Avatar Generation

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
       pipeline_type='video',
       avatar_config=config,
       avatar_enabled=True,
   )
   print(json.dumps(result))
   "
   ```
   Where:
   - [output_dir] is the project output directory from Step 0
   - [CHANNEL_NAME] is the channel parsed in Step 0
   - pipeline_type is always "video" for this skill
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
       record_video_cost(conn, '[TITLE]', '[CHANNEL]', 'video', 0.0, 0.0, 0.0, [avatar_total_cost])
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

## Step 7: Scene Design + Stock Footage

**Avatar clips**: If Step 6.5 ran, some scenes in scene-manifest.json now have source.type="avatar" and source.local_path pointing to HeyGen MP4 files. These are standard MP4 H.264 files and are handled identically to stock clips by build_filter_complex — no special treatment needed (per D-03, D-03b).

**Skip condition**: metadata.steps.scene_design.status == "completed" AND scene-manifest.json exists in output directory

If not skipped:

### Step 7a: Visual Design
1. Dispatch the designer sub-agent:
   - Agent: @shorts-designer
   - Provide: output_dir = "[full output directory path]"
   - Append to agent prompt:
     ---
     VIDEO DESIGN MODE:
     pipeline_type: "video"
     Create visual_spec.json with video-appropriate design parameters.
     ---
   - If CHANNEL_CONTEXT is not null, append:
     ---
     CHANNEL VISUAL IDENTITY:
     [VISUAL_IDENTITY section from channel skill]
     Use the channel's accent colors for titleKeywords.
     ---
   - Wait for completion
2. Verify visual_spec.json was created in the output directory
3. Update metadata.json: steps.scene_design.status = "completed"

### Step 7b: Stock Footage (handled by video-sourcer or existing stock_fetch)
Stock footage is fetched by the video sourcer agent or stock_fetch.py as part of the pipeline.

## Step 8: Video Assembly

**NOTE:** 일반 영상(16:9, 멀티챕터)은 FFmpeg `video_assemble.py`를 직접 사용한다. `@shorts-editor`(Remotion)는 쇼츠(9:16) 전용이므로 여기서는 사용하지 않는다. 쇼츠 파이프라인은 `create-shorts/SKILL.md` 참조.

**Audio input**: Uses AUDIO_PATH from Step 5.5 (mixed_audio.mp3 if BGM was applied, or narration.mp3 if BGM was skipped/failed).

**Skip condition**: metadata.steps.video_assembly.status == "completed" AND final.mp4 exists in output directory

If not skipped:
1. Run video_assemble.py directly with --pipeline video:
   ```
   python scripts/video-pipeline/video_assemble.py \
     --manifest [output_dir]/scene-manifest.json \
     --audio [AUDIO_PATH] \
     --subtitles [output_dir]/subtitles.srt \
     --output [output_dir]/final.mp4 \
     --fonts-dir "assets/fonts" \
     --config-dir config \
     --pipeline video
   ```
   - AUDIO_PATH was set in Step 5.5: [output_dir]/mixed_audio.mp3 if BGM was applied, or [output_dir]/narration.mp3 if BGM was skipped/failed
   - Video assembly uses chapter-based intermediate rendering for 16:9
   - Each chapter is rendered as an intermediate MP4, then concatenated
   - This avoids FFmpeg memory exhaustion with 50+ xfade transitions
2. Verify final.mp4 was created in the output directory
3. Display video assembly results:

```
============================================================
VIDEO ASSEMBLY COMPLETE
============================================================
Resolution: 1920x1080 (16:9)
Duration: [X.X] seconds
File Size: [X.X] MB
Clips: [N] clips assembled
Chapters: [N] intermediate renders merged
============================================================
```

4. Update metadata.json: steps.video_assembly.status = "completed"

## Step 9: QA Check

**Skip condition**: metadata.steps.qa.status == "completed" AND metadata.steps.qa.passed == true

If not skipped:
1. Dispatch the QA sub-agent:
   - Agent: @shorts-qa
   - Provide: output_dir = "[full output directory path]"
   - Append to agent prompt:
     ---
     VIDEO QA MODE:
     pipeline_type: "video"
     Run qa_check.py with --pipeline video:
     python scripts/video-pipeline/qa_check.py --video [output_dir]/final.mp4 --manifest [output_dir]/scene-manifest.json --audio [output_dir]/narration.mp3 --pipeline video
     Video QA validates: 1920x1080 resolution, 300-900s duration, 30+ clips, 8s max static, chapter transitions.
     ---
   - Wait for completion
2. Read metadata.json and check QA result

### QA Result Handling:

**If qa.passed == true:**

```
============================================================
VIDEO PIPELINE COMPLETE
============================================================
Topic: [topic]
Output: [output_dir]/final.mp4
Duration: [X.X] seconds ([N] minutes)
Resolution: 1920x1080 (16:9)
File Size: [X.X] MB
Chapters: [N]
QA Score: [N]/23 passed

Status: Ready for upload.
============================================================
```

**If qa.passed == false AND qa.attempt_count < 2 (auto-retry):**

```
============================================================
QA FAILED - AUTO-RETRY
============================================================
Score: [N]/23
Failed items: [list of QA IDs]
Attempt: [N] of 2

Retrying video assembly with feedback...
============================================================
```
- Return to Step 8 (video_assembly reset to "pending")

**If qa.passed == false AND qa.attempt_count >= 2 (manual review):**

```
============================================================
QA FAILED - MANUAL REVIEW REQUIRED
============================================================
Score: [N]/23
Failed items:
  - [QA-XX]: [failure description]
Attempts: 2 of 2
============================================================
```

- Present options:
  1. ACCEPT - Accept despite QA failures
  2. FEEDBACK - Provide guidance for re-assembly
  3. ABORT - Stop the pipeline

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
   Pipeline: video (16:9)
   Duration: [X.X] seconds ([N] minutes)
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
   VIDEO UPLOAD COMPLETE
   ============================================================
   Video ID: [VIDEO_ID]
   URL: https://youtu.be/[VIDEO_ID]
   Privacy: private
   Channel: [CHANNEL_NAME]
   Pipeline: video (16:9)
   Duration: [X.X] seconds ([N] minutes)

   Video uploaded as PRIVATE. Change visibility in YouTube Studio:
   https://studio.youtube.com/video/[VIDEO_ID]/edit
   ============================================================
   ```
