"""Phase 42 — English bodycam audio → Whisper transcription → Claude detective translation.

Pipeline position:
    sources/real/<clip>.clean.mp4
        -> [faster-whisper small.en word_timestamps]
        -> [Claude Opus detective-tone batch translate ko+ja]
        -> sources/real/<clip>.en_ko.json   (Remotion word-highlight subtitle)
           sources/real/<clip>.en_ja.json   (ditto)
           sources/real/<clip>.bracket.json (optional, from scripter bracket_caption)

CLI:
    python scripts/audio-pipeline/en_caption_translate.py \
        --input output/<slug>/sources/real/<clip>.clean.mp4 \
        --script output/<slug>/script.json \
        --output-dir output/<slug>/sources/real \
        --clip-id <clip_id> \
        --langs ko,ja \
        --channel incidents

Environment:
    Uses Claude Code CLI (``claude -p``) via subprocess. Requires a Claude Code
    login with an active Max plan — **no ANTHROPIC_API_KEY is used**
    (memory rule: feedback_no_claude_api + feedback_env_keys_sacred). The
    subprocess unsets ``CLAUDECODE`` before invocation (Phase 39 pattern) so
    that nested ``claude -p`` calls do not reject as recursive.

Design:
    - faster-whisper small.en, CUDA -> CPU fallback (same pattern as word_subtitle.py).
    - Single Claude batch call per target language (scene granularity = full clip),
      inline retry x3 (tenacity not pulled).
    - ``ClaudeCliClient`` adapter exposes the anthropic SDK shape
      (``client.messages.create(...) -> msg.content[0].text``) over a
      ``subprocess.run(["claude","-p", ..., "--system-prompt", ...,
      "--output-format","json","--model",<alias>])`` call. Envelope
      ``{"type":"result","result":"..."}`` is unwrapped before returning.
    - JSON output schema matches word_subtitle.py Remotion schema
      (startMs/endMs/text/words[{text,startMs,endMs}]) + `color: "yellow"` hint.
    - bracket_caption is a one-shot static caption for the whole clip — not
      word-timed.  Extracted from scripter section matching clip_id.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

try:  # load .env if python-dotenv is available (memory env_keys_sacred)
    from dotenv import load_dotenv  # type: ignore
    load_dotenv(override=True)
except Exception:
    pass

REPO_ROOT = Path(__file__).resolve().parents[2]
PROMPT_PATH = REPO_ROOT / "config" / "prompts" / "en_translate_detective.md"
DEFAULT_MODEL = "small.en"
MAX_CHARS_PER_GROUP = 18
DEFAULT_CLAUDE_MODEL = "claude-opus-4-20250514"
CLAUDE_CLI_TIMEOUT = int(os.environ.get("CLAUDE_CLI_TIMEOUT", "300"))


_CLAUDE_MODEL_ALIASES = {
    "opus": "opus",
    "sonnet": "sonnet",
    "haiku": "haiku",
}


def _map_claude_model_to_cli(model: str) -> str:
    """Map anthropic SDK model id (``claude-opus-4-20250514``) to CLI alias."""
    if not model:
        return "opus"
    if model.startswith("claude-opus"):
        return "opus"
    if model.startswith("claude-sonnet"):
        return "sonnet"
    if model.startswith("claude-haiku"):
        return "haiku"
    return _CLAUDE_MODEL_ALIASES.get(model, "opus")


class _ClaudeBlock:
    """anthropic-SDK-compatible content block — ``block.text`` holds the text."""

    __slots__ = ("text",)

    def __init__(self, text: str):
        self.text = text


class _ClaudeResponse:
    """anthropic-SDK-compatible message — ``msg.content[0].text`` shape."""

    __slots__ = ("content",)

    def __init__(self, text: str):
        self.content = [_ClaudeBlock(text)]


class _ClaudeCliMessages:
    """``client.messages.create(...)`` sub-namespace, SDK-compatible."""

    def __init__(self, parent: "ClaudeCliClient"):
        self._parent = parent

    def create(self, *, model: str, max_tokens: int, system: str, messages: list) -> _ClaudeResponse:
        user_content = ""
        if messages:
            first = messages[0]
            content = first.get("content") if isinstance(first, dict) else None
            if isinstance(content, str):
                user_content = content
            elif isinstance(content, list):
                # SDK supports content blocks; flatten text blocks for CLI.
                parts: list[str] = []
                for b in content:
                    if isinstance(b, dict) and b.get("type") == "text":
                        parts.append(str(b.get("text", "")))
                user_content = "\n".join(parts)
        return self._parent._invoke(
            model=model,
            max_tokens=max_tokens,
            system=system,
            user_content=user_content,
        )


class ClaudeCliClient:
    """Max-plan ``claude -p`` subprocess adapter with anthropic-SDK shape.

    Exposes ``client.messages.create(...)`` returning an object whose
    ``content[0].text`` carries the response — the exact contract that
    :meth:`EnCaptionTranslator._call_claude_with_retry` relies on. Tests
    inject ``MagicMock`` through the ``_claude_client`` DI seam and never
    invoke this adapter, so unit coverage is unaffected.

    Implementation follows Phase 39 ``orchestrate.py`` patterns:
      - ``CLAUDECODE`` env var unset (nested-invocation guard)
      - bytes mode + UTF-8 decode (Windows CP949 avoidance)
      - ``--output-format json`` + envelope unwrap (``{"result": "..."}``)
      - explicit ``--system-prompt`` flag to preserve detective-tone prompt
    """

    def __init__(
        self,
        claude_bin: str = "claude",
        timeout: int = CLAUDE_CLI_TIMEOUT,
    ):
        self._claude_bin = claude_bin
        self._timeout = timeout
        self.messages = _ClaudeCliMessages(self)

    def _invoke(
        self,
        *,
        model: str,
        max_tokens: int,  # CLI does not accept; kept for SDK signature parity
        system: str,
        user_content: str,
    ) -> _ClaudeResponse:
        del max_tokens  # CLI max-tokens is controlled by session settings.
        cli_model = _map_claude_model_to_cli(model)
        cmd = [
            self._claude_bin,
            "-p",
            user_content,
            "--system-prompt",
            system,
            "--output-format",
            "json",
            "--model",
            cli_model,
        ]
        env = os.environ.copy()
        env.pop("CLAUDECODE", None)  # Phase 39 nested-call guard
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=False,  # bytes mode — Windows CP949 safety
                timeout=self._timeout,
                env=env,
            )
        except FileNotFoundError as exc:
            raise RuntimeError(
                "claude CLI not found on PATH; install Claude Code or set "
                "an explicit path via ClaudeCliClient(claude_bin=...)"
            ) from exc
        except subprocess.TimeoutExpired as exc:
            raise RuntimeError(
                f"claude CLI timed out after {self._timeout}s"
            ) from exc

        if result.returncode != 0:
            stderr = (result.stderr or b"").decode("utf-8", errors="replace")
            raise RuntimeError(
                f"claude CLI exit {result.returncode}: {stderr[:500]}"
            )

        stdout_str = (result.stdout or b"").decode("utf-8", errors="replace")
        # Phase 39 envelope unwrap: {"type":"result","result":"...","is_error":false}
        try:
            envelope = json.loads(stdout_str.strip())
            if isinstance(envelope, dict) and "result" in envelope:
                stdout_str = envelope["result"]
        except (json.JSONDecodeError, TypeError):
            pass  # Already raw text
        return _ClaudeResponse(stdout_str)


@dataclass
class WordTs:
    start_ms: int
    end_ms: int
    text: str


@dataclass
class CaptionGroup:
    start_ms: int
    end_ms: int
    text: str
    words: list[WordTs] = field(default_factory=list)


class EnCaptionTranslator:
    """faster-whisper en transcription + Claude Opus detective-tone translation.

    Dependency injection seams:
        _whisper_loader(model_size) -> whisper_model_like
        _claude_client                -> anthropic.Anthropic-like client

    Both seams exist so tests can run without GPU / network / API keys.
    """

    def __init__(
        self,
        model_size: str = DEFAULT_MODEL,
        channel: str = "incidents",
        claude_model: str = DEFAULT_CLAUDE_MODEL,
        _whisper_loader=None,
        _claude_client=None,
    ):
        self._model_size = model_size
        self._channel = channel
        self._claude_model = claude_model
        self._whisper_loader = _whisper_loader
        self._claude_client = _claude_client

    # ------------------------------------------------------------------
    # Whisper
    # ------------------------------------------------------------------
    def _load_whisper(self):
        if self._whisper_loader is not None:
            return self._whisper_loader(self._model_size)
        from faster_whisper import WhisperModel  # type: ignore
        # CUDA/CPU 선택은 opt-in env var 로 제어한다. 기본은 CPU.
        # ctranslate2 4.x + faster-whisper 1.2.x 조합은 ``device="cuda"`` 로
        # 초기화가 예외 없이 성공해도 transcribe() 실제 호출 시 cublas DLL
        # 로드를 지연 요구 → cublas64_12.dll 미설치 환경에서 RuntimeError.
        # 또한 ``ctranslate2.get_cuda_device_count()`` 는 GPU 가 보이면 1 을
        # 반환하지만 cublas/cuDNN 존재 여부는 검증하지 않는다. 따라서 감지
        # 로직만으로는 "init 통과-transcribe 실패" 함정을 회피할 수 없다.
        # GPU 환경은 ``FASTER_WHISPER_DEVICE=cuda`` 를 명시적으로 설정하게
        # 강제한다.
        device_pref = os.environ.get("FASTER_WHISPER_DEVICE", "cpu").lower()
        if device_pref == "cuda":
            try:
                import ctypes
                ctypes.CDLL("cublas64_12")  # Phase 43 W5: cublas DLL 실존 probe
                return WhisperModel(self._model_size, device="cuda", compute_type="float16")
            except (OSError, Exception):
                pass  # cublas 미설치 또는 CUDA init 실패 → CPU fallback
        return WhisperModel(self._model_size, device="cpu", compute_type="int8")

    def transcribe_en(self, audio_path: Path) -> list[WordTs]:
        """Run faster-whisper small.en with word_timestamps + vad_filter."""
        model = self._load_whisper()
        segments, _info = model.transcribe(
            str(audio_path),
            language="en",
            word_timestamps=True,
            vad_filter=True,
        )
        out: list[WordTs] = []
        for seg in segments:
            seg_words = getattr(seg, "words", None)
            if not seg_words:
                continue
            for w in seg_words:
                text = (getattr(w, "word", "") or "").strip()
                if not text:
                    continue
                out.append(WordTs(
                    start_ms=int(round(float(w.start) * 1000)),
                    end_ms=int(round(float(w.end) * 1000)),
                    text=text,
                ))
        return out

    # ------------------------------------------------------------------
    # Grouping
    # ------------------------------------------------------------------
    def _group_words(self, words: list[WordTs]) -> list[CaptionGroup]:
        """Collapse word stream into short caption groups (~MAX_CHARS_PER_GROUP)."""
        groups: list[CaptionGroup] = []
        cur: list[WordTs] = []
        cur_chars = 0
        for w in words:
            break_on_gap = bool(cur) and (w.start_ms - cur[-1].end_ms > 800)
            break_on_len = bool(cur) and (cur_chars + len(w.text) + 1 > MAX_CHARS_PER_GROUP)
            if break_on_gap or break_on_len:
                groups.append(CaptionGroup(
                    start_ms=cur[0].start_ms,
                    end_ms=cur[-1].end_ms,
                    text=" ".join(x.text for x in cur),
                    words=list(cur),
                ))
                cur = []
                cur_chars = 0
            cur.append(w)
            cur_chars += len(w.text) + 1
        if cur:
            groups.append(CaptionGroup(
                start_ms=cur[0].start_ms,
                end_ms=cur[-1].end_ms,
                text=" ".join(x.text for x in cur),
                words=list(cur),
            ))
        return groups

    # ------------------------------------------------------------------
    # Claude translation
    # ------------------------------------------------------------------
    def translate_batch(self, groups: list[CaptionGroup], target_lang: str) -> list[CaptionGroup]:
        """Single Claude Opus call translating all groups; returns groups with text replaced."""
        if not groups:
            return []
        prompt_template = PROMPT_PATH.read_text(encoding="utf-8")
        lang_full = {"ko": "Korean", "ja": "Japanese"}.get(target_lang, target_lang)
        channel_full = {
            "incidents": "사건기록부",
            "incidents_jp": "冴木の手帳",
        }.get(self._channel, self._channel)
        system_prompt = (
            prompt_template
            .replace("{target_lang}", lang_full)
            .replace("{channel_name}", channel_full)
        )
        payload = [
            {"startMs": g.start_ms, "endMs": g.end_ms, "text": g.text}
            for g in groups
        ]
        client = self._claude_client or self._make_anthropic_client()
        translated_text = self._call_claude_with_retry(
            client, system_prompt, json.dumps(payload, ensure_ascii=False)
        )
        translated = self._parse_json_array(translated_text)
        if len(translated) != len(groups):
            raise RuntimeError(
                f"Translation length mismatch: {len(translated)} vs {len(groups)}"
            )
        out: list[CaptionGroup] = []
        for orig, t in zip(groups, translated):
            out.append(CaptionGroup(
                start_ms=int(t["startMs"]),
                end_ms=int(t["endMs"]),
                text=str(t["text"]),
                words=orig.words,  # preserve original word-timing
            ))
        return out

    @staticmethod
    def _parse_json_array(text: str) -> list[dict]:
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # Claude occasionally wraps response in markdown / commentary
            m = re.search(r"\[\s*\{.*\}\s*\]", text, re.DOTALL)
            if not m:
                raise RuntimeError(f"Claude returned non-JSON: {text[:200]}")
            return json.loads(m.group(0))

    def _make_anthropic_client(self):
        """Return a Claude CLI adapter shaped like the anthropic SDK.

        Memory rule ``feedback_no_claude_api`` forbids paid API usage; this
        project uses Claude Code Max plan via ``claude -p`` subprocess. The
        historical name is preserved for DI-seam compatibility; the actual
        client is :class:`ClaudeCliClient`.
        """
        return ClaudeCliClient()

    def _call_claude_with_retry(
        self,
        client,
        system_prompt: str,
        user_payload: str,
        max_attempts: int = 3,
    ) -> str:
        last_err: Exception | None = None
        for _attempt in range(max_attempts):
            try:
                msg = client.messages.create(
                    model=self._claude_model,
                    max_tokens=4096,
                    system=system_prompt,
                    messages=[{"role": "user", "content": user_payload}],
                )
                return msg.content[0].text
            except Exception as e:  # retry on any failure
                last_err = e
        raise RuntimeError(f"Claude call failed after {max_attempts}: {last_err}")

    # ------------------------------------------------------------------
    # Output
    # ------------------------------------------------------------------
    def write_remotion_json(self, groups: list[CaptionGroup], output_path: Path) -> None:
        """Write Remotion-compatible subtitle JSON (word_subtitle.py schema + color hint)."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        data = []
        for g in groups:
            data.append({
                "startMs": g.start_ms,
                "endMs": g.end_ms,
                "text": g.text,
                "words": [
                    {"text": w.text, "startMs": w.start_ms, "endMs": w.end_ms}
                    for w in g.words
                ],
                "color": "yellow",
            })
        output_path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )


def _extract_bracket_for_clip(script: dict, clip_id: str) -> dict | None:
    """Return {startMs,endMs,text} for the scripter section matching clip_id, or None."""
    for sec in script.get("sections", []):
        if sec.get("clip_id") == clip_id or sec.get("id") == clip_id:
            if "bracket_caption" in sec:
                return {
                    "startMs": int(sec.get("bracket_caption_start_ms", 0)),
                    "endMs": int(sec.get("bracket_caption_end_ms", 99999)),
                    "text": sec["bracket_caption"],
                }
    return None


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        description="Phase 42 EN bodycam -> Whisper -> Claude detective translation",
    )
    ap.add_argument("--input", type=Path, required=True, help="clean.mp4 (en audio)")
    ap.add_argument("--script", type=Path, required=True, help="scripter script.json")
    ap.add_argument("--output-dir", type=Path, required=True)
    ap.add_argument("--clip-id", required=True)
    ap.add_argument("--langs", default="ko,ja")
    ap.add_argument("--channel", default="incidents")
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--claude-model", default=DEFAULT_CLAUDE_MODEL)
    args = ap.parse_args(argv)

    translator = EnCaptionTranslator(
        model_size=args.model,
        channel=args.channel,
        claude_model=args.claude_model,
    )
    words = translator.transcribe_en(args.input)
    groups = translator._group_words(words)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    for lang in args.langs.split(","):
        lang = lang.strip()
        if not lang:
            continue
        translated = translator.translate_batch(groups, lang)
        out_path = args.output_dir / f"{args.clip_id}.en_{lang}.json"
        translator.write_remotion_json(translated, out_path)
        print(f"[ok] {lang} -> {out_path}")

    # bracket caption (optional)
    if args.script.exists():
        try:
            script = json.loads(args.script.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            print(f"[warn] script.json parse failed: {e}", file=sys.stderr)
            script = {}
        br = _extract_bracket_for_clip(script, args.clip_id)
        if br is not None:
            br_path = args.output_dir / f"{args.clip_id}.bracket.json"
            br_path.write_text(
                json.dumps(br, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            print(f"[ok] bracket -> {br_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
