"""Enhanced visual rendering engine for reference-quality title overlays.

Produces professional-quality title overlays, watermarks, and FFmpeg filter
commands based on reference analysis of top-performing YouTube Shorts channels.

Design specifications (from output/analysis/refs/):
    - Titles: HUGE (48-64px), not the previous tiny 36-42px
    - Keywords highlighted in accent color (yellow/red per channel)
    - Thick black outline (4-5px) + drop shadow for contrast
    - Title persists for the entire video duration
    - 2-line layout: line1 smaller context, line2 BIGGER hook with accent
    - Channel watermark in top-right corner

ASS color format: #RRGGBB -> &H00BBGGRR& (BGR order, 00 = fully opaque alpha).

Exit codes:
    0 = success
    1 = error
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Channel design presets
# ---------------------------------------------------------------------------

# 채널 디자인 프리셋 — config/channels.yaml 싱글 소스
import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0, str(_Path(__file__).resolve().parent.parent.parent / "config"))
try:
    import channel_registry as _cr
    CHANNEL_DESIGNS: dict[str, dict] = _cr.design_presets()
except Exception:
    CHANNEL_DESIGNS: dict[str, dict] = {}

# Title styling constants
LINE1_FONT_SIZE = 48
LINE2_FONT_SIZE = 64
LINE1_OUTLINE = 4
LINE2_OUTLINE = 5
LINE1_SHADOW = 2
LINE2_SHADOW = 3
TITLE_ZONE_HEIGHT = 250  # Top zone reserved for title overlay
CANVAS_WIDTH = 1080
CANVAS_HEIGHT = 1920


# ---------------------------------------------------------------------------
# Color Conversion
# ---------------------------------------------------------------------------

def rgb_to_ass_color(hex_rgb: str) -> str:
    """Convert #RRGGBB to ASS &H00BBGGRR& format.

    ASS subtitle format uses BGR byte order with 00 alpha prefix
    (fully opaque).

    Args:
        hex_rgb: Hex color string, e.g., "#FFC947" or "FFC947".

    Returns:
        ASS-formatted color string, e.g., "&H0047C9FF&".

    Examples:
        >>> rgb_to_ass_color("#FFC947")
        '&H0047C9FF&'
        >>> rgb_to_ass_color("#E63946")
        '&H004639E6&'
        >>> rgb_to_ass_color("#00F5D4")
        '&H00D4F500&'
    """
    hex_rgb = hex_rgb.lstrip("#")
    r = hex_rgb[0:2]
    g = hex_rgb[2:4]
    b = hex_rgb[4:6]
    return f"&H00{b}{g}{r}&"


def rgb_to_ass_color_with_alpha(hex_rgb: str, alpha_hex: str = "00") -> str:
    """Convert #RRGGBB to ASS &HAA_BBGGRR& format with alpha.

    Args:
        hex_rgb: Hex color string, e.g., "#000000".
        alpha_hex: Alpha as hex string, "00" = opaque, "FF" = transparent.

    Returns:
        ASS-formatted color string with alpha, e.g., "&H80000000&".
    """
    hex_rgb = hex_rgb.lstrip("#")
    r = hex_rgb[0:2]
    g = hex_rgb[2:4]
    b = hex_rgb[4:6]
    return f"&H{alpha_hex}{b}{g}{r}&"


# ---------------------------------------------------------------------------
# Channel Design Lookup
# ---------------------------------------------------------------------------

def get_channel_design(channel: str) -> dict:
    """Return channel-specific design parameters.

    Falls back to "humor" preset if channel is unknown.

    Args:
        channel: Channel name ("humor", "politics", "trend").

    Returns:
        Dict with keys: accent, title_bg, font, watermark_text.
    """
    design = CHANNEL_DESIGNS.get(channel, CHANNEL_DESIGNS["humor"])
    if channel not in CHANNEL_DESIGNS:
        logger.warning("Unknown channel '%s', falling back to 'humor' design", channel)
    return dict(design)


# ---------------------------------------------------------------------------
# ASS Title Overlay Generation
# ---------------------------------------------------------------------------

def _apply_accent_to_text(text: str, accent_words: list[str], accent_ass_color: str) -> str:
    """Apply inline ASS color tags to accent words in text.

    Wraps each accent word with ASS inline color override tags:
    {\\c&H00BBGGRR&}word{\\c&H00FFFFFF&}

    Args:
        text: Original text string.
        accent_words: List of keywords to highlight.
        accent_ass_color: ASS-formatted accent color string.

    Returns:
        Text with ASS inline color tags applied.
    """
    styled = text
    for word in accent_words:
        if word in styled:
            colored = f"{{\\c{accent_ass_color}}}{word}{{\\c&H00FFFFFF&}}"
            styled = styled.replace(word, colored)
    return styled


def generate_title_overlay(
    title_config: dict,
    duration: float,
    output_path: str,
) -> str:
    """Generate an ASS subtitle file for professional-quality title overlay.

    Creates a 2-line title with reference-quality styling:
        - Line1 (context/category): 48px, white, bold, outline 4px, shadow 2px
        - Line2 (main hook): 64px, white with accent keywords, extra-bold,
          outline 5px, shadow 3px
    Both lines are centered horizontally in the top 250px zone.

    Args:
        title_config: Dict with keys:
            - line1 (str): Top line text (topic/context).
            - line2 (str): Bottom line text (main title/hook).
            - accent_words (list[str]): Keywords to highlight in accent color.
            - accent_color (str): Hex color for accent, e.g., "#FFC947".
            - channel (str): Channel name for design lookup.
        duration: Video duration in seconds (title persists entire video).
        output_path: Path to write the generated ASS file.

    Returns:
        Path to the generated ASS file (same as output_path).
    """
    line1 = title_config.get("line1", "")
    line2 = title_config.get("line2", "")
    accent_words = title_config.get("accent_words", [])
    accent_color = title_config.get("accent_color", "#FFC947")
    channel = title_config.get("channel", "humor")

    # Get channel design for font
    design = get_channel_design(channel)
    font_name = design["font"]

    # Convert accent color to ASS format
    accent_ass = rgb_to_ass_color(accent_color)

    # Apply accent color to line2 keywords
    styled_line2 = _apply_accent_to_text(line2, accent_words, accent_ass)

    # Calculate vertical positioning for 2-line title in top zone
    # Line1 sits above center, line2 sits below center of the title zone
    # Total text height: LINE1_FONT_SIZE + gap + LINE2_FONT_SIZE
    line_gap = 16
    total_text_height = LINE1_FONT_SIZE + line_gap + LINE2_FONT_SIZE
    top_margin = (TITLE_ZONE_HEIGHT - total_text_height) // 2

    # MarginV for Line1 style (Alignment 8 = top-center)
    line1_margin_v = max(top_margin, 10)
    # MarginV for Line2 style: positioned below line1
    line2_margin_v = line1_margin_v + LINE1_FONT_SIZE + line_gap

    # Format duration as ASS timestamp
    dur_h = int(duration // 3600)
    dur_m = int((duration % 3600) // 60)
    dur_s = duration % 60
    dur_whole = int(dur_s)
    dur_cs = int(round((dur_s - dur_whole) * 100))
    end_ts = f"{dur_h}:{dur_m:02d}:{dur_whole:02d}.{dur_cs:02d}"

    # Shadow color: black with 80% opacity -> alpha = 0x33 (ASS: 00=opaque, FF=transparent)
    # 80% opaque = 20% transparent = 0x33
    shadow_color = "&H33000000&"

    # Build ASS content
    lines = [
        "[Script Info]",
        "Title: Title Overlay",
        "ScriptType: v4.00+",
        f"PlayResX: {CANVAS_WIDTH}",
        f"PlayResY: {CANVAS_HEIGHT}",
        "WrapStyle: 0",
        "ScaledBorderAndShadow: yes",
        "",
        "[V4+ Styles]",
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, "
        "OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, "
        "ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, "
        "Alignment, MarginL, MarginR, MarginV, Encoding",
        # Line1 style: 48px, white, bold, thick outline + shadow
        f"Style: TitleLine1,{font_name},{LINE1_FONT_SIZE},"
        f"&H00FFFFFF&,&H00FFFFFF&,"
        f"&H00000000&,{shadow_color},"
        f"-1,0,0,0,100,100,0,0,1,{LINE1_OUTLINE},{LINE1_SHADOW},"
        f"8,20,20,{line1_margin_v},1",
        # Line2 style: 64px, white, extra-bold, thicker outline + shadow
        f"Style: TitleLine2,{font_name},{LINE2_FONT_SIZE},"
        f"&H00FFFFFF&,&H00FFFFFF&,"
        f"&H00000000&,{shadow_color},"
        f"-1,0,0,0,100,100,0,0,1,{LINE2_OUTLINE},{LINE2_SHADOW},"
        f"8,20,20,{line2_margin_v},1",
        "",
        "[Events]",
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
    ]

    # Add line1 dialogue (context/category)
    if line1:
        lines.append(
            f"Dialogue: 0,0:00:00.00,{end_ts},TitleLine1,,0,0,0,,{line1}"
        )

    # Add line2 dialogue (main hook with accent colors)
    if styled_line2:
        lines.append(
            f"Dialogue: 0,0:00:00.00,{end_ts},TitleLine2,,0,0,0,,{styled_line2}"
        )

    ass_content = "\n".join(lines)

    # Write ASS file
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(ass_content, encoding="utf-8")

    logger.info(
        "Title overlay ASS generated: %s (line1='%s', line2='%s', accent=%s)",
        output_path, line1, line2, accent_color,
    )

    return str(output)


# ---------------------------------------------------------------------------
# Watermark Filter
# ---------------------------------------------------------------------------

def generate_watermark_filter(
    channel: str,
    logo_path: str | None = None,
    fontsize: int = 22,
    opacity: float = 0.4,
    font_path: str = "",
) -> str:
    """Generate FFmpeg filter string for channel watermark overlay.

    If logo_path is provided, uses an image overlay. Otherwise generates
    a text-based watermark using the channel's watermark_text.

    Position: top-right corner, semi-transparent.

    Args:
        channel: Channel name for watermark text lookup.
        logo_path: Optional path to logo image file (PNG with alpha).
        fontsize: Watermark font size (default 22).
        opacity: Watermark opacity 0.0-1.0 (default 0.4).
        font_path: Path to font file for text watermark. If empty,
            uses system default.

    Returns:
        FFmpeg filter string fragment (without label wiring -- caller
        handles [input] and [output] labels).
    """
    if logo_path and Path(logo_path).exists():
        # Image-based watermark: overlay in top-right with opacity
        logo_safe = str(logo_path).replace("\\", "/").replace(":", "\\:")
        return (
            f"movie='{logo_safe}'[wm];"
            f"[wm]format=rgba,colorchannelmixer=aa={opacity}[wm_alpha];"
            f"overlay=W-w-30:30"
        )

    # Text-based watermark
    design = get_channel_design(channel)
    watermark_text = design["watermark_text"]

    filter_parts = [
        f"drawtext=text='{watermark_text}'",
        f":fontsize={fontsize}",
        f":fontcolor=white@{opacity}",
        ":x=w-text_w-30",
        ":y=30",
    ]

    if font_path:
        safe_font = str(font_path).replace("\\", "/").replace(":", "\\:")
        filter_parts.append(f":fontfile='{safe_font}'")

    return "".join(filter_parts)


# ---------------------------------------------------------------------------
# FFmpeg Design Filter Composition
# ---------------------------------------------------------------------------

def build_ffmpeg_design_filters(
    title_ass: str,
    watermark_filter: str | None = None,
    subtitle_srt: str | None = None,
    fonts_dir: str = "assets/fonts",
) -> str:
    """Combine all visual overlays into a single FFmpeg filtergraph.

    Layering order:
        1. Input video [0:v]
        2. Title overlay (ASS burn-in)
        3. Watermark (drawtext or image overlay)
        4. Subtitle overlay (SRT or ASS burn-in)

    The output label is [designed].

    Args:
        title_ass: Path to the title ASS file.
        watermark_filter: FFmpeg filter string for watermark (or None to skip).
        subtitle_srt: Path to subtitle file (.srt or .ass), or None to skip.
        fonts_dir: Directory containing font files.

    Returns:
        Complete FFmpeg -filter_complex string.
    """
    # Escape paths for FFmpeg (Windows backslash + colon handling)
    title_safe = str(title_ass).replace("\\", "/").replace(":", "\\:")
    fonts_safe = str(fonts_dir).replace("\\", "/").replace(":", "\\:")

    parts = []
    current_label = "[0:v]"
    label_counter = 0

    def next_label() -> str:
        nonlocal label_counter
        label_counter += 1
        return f"[d{label_counter}]"

    # 1. Title overlay
    out = next_label()
    parts.append(
        f"{current_label}ass='{title_safe}':fontsdir='{fonts_safe}'{out}"
    )
    current_label = out

    # 2. Watermark
    if watermark_filter:
        out = next_label()
        parts.append(f"{current_label}{watermark_filter}{out}")
        current_label = out

    # 3. Subtitle overlay
    if subtitle_srt and Path(subtitle_srt).exists():
        sub_safe = str(subtitle_srt).replace("\\", "/").replace(":", "\\:")
        out = "[designed]"
        if str(subtitle_srt).lower().endswith(".ass"):
            parts.append(
                f"{current_label}ass='{sub_safe}':fontsdir='{fonts_safe}'{out}"
            )
        else:
            parts.append(
                f"{current_label}subtitles='{sub_safe}':fontsdir='{fonts_safe}'{out}"
            )
        current_label = out
    else:
        # Rename last label to [designed]
        parts[-1] = parts[-1].replace(current_label.replace("[", "").replace("]", ""),
                                       "designed") if parts else ""
        # Simpler approach: just replace the output label
        if parts:
            last = parts[-1]
            # Find the last [...] and replace with [designed]
            bracket_start = last.rfind("[")
            bracket_end = last.rfind("]")
            if bracket_start >= 0 and bracket_end > bracket_start:
                parts[-1] = last[:bracket_start] + "[designed]" + last[bracket_end + 1:]

    return ";".join(parts)


# ---------------------------------------------------------------------------
# CLI Entry Point
# ---------------------------------------------------------------------------

def main():
    """CLI entry point for design_engine.py."""
    parser = argparse.ArgumentParser(
        description="Generate reference-quality title overlays and FFmpeg design filters",
    )
    subparsers = parser.add_subparsers(dest="command", help="Sub-commands")

    # --- title sub-command ---
    title_parser = subparsers.add_parser("title", help="Generate title overlay ASS file")
    title_parser.add_argument("--line1", required=True, help="Top line text (context/category)")
    title_parser.add_argument("--line2", required=True, help="Bottom line text (main hook)")
    title_parser.add_argument(
        "--accent-words", nargs="*", default=[],
        help="Keywords to highlight in accent color",
    )
    title_parser.add_argument(
        "--accent-color", default=None,
        help="Accent color hex (default: channel-specific)",
    )
    title_parser.add_argument("--channel", default="humor", help="Channel name (humor/politics/trend)")
    title_parser.add_argument("--duration", type=float, default=60.0, help="Video duration in seconds")
    title_parser.add_argument("--output", required=True, help="Output ASS file path")

    # --- watermark sub-command ---
    wm_parser = subparsers.add_parser("watermark", help="Generate watermark FFmpeg filter")
    wm_parser.add_argument("--channel", required=True, help="Channel name")
    wm_parser.add_argument("--logo", default=None, help="Path to logo PNG (optional)")
    wm_parser.add_argument("--font-path", default="", help="Path to font file")

    # --- filters sub-command ---
    filt_parser = subparsers.add_parser("filters", help="Build combined FFmpeg filtergraph")
    filt_parser.add_argument("--title-ass", required=True, help="Path to title ASS file")
    filt_parser.add_argument("--subtitle", default=None, help="Path to subtitle file")
    filt_parser.add_argument("--channel", default="humor", help="Channel name for watermark")
    filt_parser.add_argument("--fonts-dir", default="assets/fonts", help="Font directory")
    filt_parser.add_argument("--no-watermark", action="store_true", help="Skip watermark")

    # --- design sub-command (show channel design) ---
    design_parser = subparsers.add_parser("design", help="Show channel design parameters")
    design_parser.add_argument("--channel", required=True, help="Channel name")

    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose logging")

    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    if args.command == "title":
        accent_color = args.accent_color
        if accent_color is None:
            design = get_channel_design(args.channel)
            accent_color = design["accent"]

        config = {
            "line1": args.line1,
            "line2": args.line2,
            "accent_words": args.accent_words,
            "accent_color": accent_color,
            "channel": args.channel,
        }
        result_path = generate_title_overlay(config, args.duration, args.output)
        print(json.dumps({"output_path": result_path}, ensure_ascii=False))
        sys.exit(0)

    elif args.command == "watermark":
        wm_filter = generate_watermark_filter(
            channel=args.channel,
            logo_path=args.logo,
            font_path=args.font_path,
        )
        print(json.dumps({"filter": wm_filter}, ensure_ascii=False))
        sys.exit(0)

    elif args.command == "filters":
        wm_filter = None
        if not args.no_watermark:
            wm_filter = generate_watermark_filter(channel=args.channel)
        filtergraph = build_ffmpeg_design_filters(
            title_ass=args.title_ass,
            watermark_filter=wm_filter,
            subtitle_srt=args.subtitle,
            fonts_dir=args.fonts_dir,
        )
        print(json.dumps({"filter_complex": filtergraph}, ensure_ascii=False))
        sys.exit(0)

    elif args.command == "design":
        design = get_channel_design(args.channel)
        print(json.dumps(design, ensure_ascii=False))
        sys.exit(0)

    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
