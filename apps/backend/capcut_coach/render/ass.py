"""Generate ASS subtitles for burned-in captions (pack doc 15 §4).

Captions are placed inside a phone-safe zone, readable at phone size, with a
strong outline. Times are timeline microseconds. libass renders these during the
FFmpeg pass.
"""

from __future__ import annotations

from ..schemas.edit_plan import Canvas
from .graph import RenderCaption, RenderStyle


def _ass_time(us: int) -> str:
    cs = us // 10_000  # centiseconds
    s = cs // 100
    cs %= 100
    h = s // 3600
    m = (s % 3600) // 60
    sec = s % 60
    return f"{h:d}:{m:02d}:{sec:02d}.{cs:02d}"


def _escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace("{", "(").replace("}", ")").replace("\n", "\\N")


def build_ass(captions: list[RenderCaption], canvas: Canvas, style: RenderStyle) -> str:
    """Return a complete ASS document for the given captions."""
    # Font size ~ 6% of height; bottom safe-zone margin ~ 14% of height.
    font_size = max(28, round(canvas.height * 0.055))
    margin_v = round(canvas.height * 0.14)
    margin_h = round(canvas.width * 0.08)
    header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {canvas.width}
PlayResY: {canvas.height}
ScaledBorderAndShadow: yes
WrapStyle: 2

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, OutlineColour, BackColour, Bold, Italic, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV
Style: Coach,Arial,{font_size},{style.caption_fill},{style.caption_outline},&H64000000,-1,0,1,{max(3, font_size // 12)},2,2,{margin_h},{margin_h},{margin_v}

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    lines = []
    for cap in captions:
        start = _ass_time(cap.start_us)
        end = _ass_time(cap.start_us + cap.duration_us)
        # Small fade for polish; kept subtle.
        text = "{\\fad(120,120)}" + _escape(cap.text)
        lines.append(f"Dialogue: 0,{start},{end},Coach,,0,0,0,,{text}")
    return header + "\n".join(lines) + "\n"
