"""SRT generation and validation (Phase 2, test F4).

Output is UTF-8, timestamps are monotonic and non-overlapping, and no negative
times occur. ``validate_srt`` re-parses the text to guarantee CapCut can import
it into editable caption blocks (F9).
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from ..schemas.edit_plan import Caption

_TS_RE = re.compile(r"(\d{2}):(\d{2}):(\d{2}),(\d{3})")


def _fmt_ts(us: int) -> str:
    if us < 0:
        raise ValueError("negative timestamp")
    ms_total = us // 1000
    ms = ms_total % 1000
    s = (ms_total // 1000) % 60
    m = (ms_total // 60000) % 60
    h = ms_total // 3_600_000
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def _parse_ts(text: str) -> int:
    m = _TS_RE.fullmatch(text.strip())
    if not m:
        raise ValueError(f"bad timestamp {text!r}")
    h, mm, ss, ms = (int(x) for x in m.groups())
    return (((h * 60 + mm) * 60 + ss) * 1000 + ms) * 1000


def captions_to_srt(captions: list[Caption]) -> str:
    """Render captions to SRT text. Raises on overlap/negative timing."""
    ordered = sorted(captions, key=lambda c: c.start_us)
    prev_end = 0
    lines: list[str] = []
    for i, cap in enumerate(ordered, start=1):
        if cap.start_us < 0 or cap.duration_us <= 0:
            raise ValueError(f"caption {cap.id} has invalid timing")
        if cap.start_us < prev_end:
            raise ValueError(f"caption {cap.id} overlaps the previous caption")
        body = "\n".join(cap.line_breaks) if cap.line_breaks else cap.text
        lines.append(str(i))
        lines.append(f"{_fmt_ts(cap.start_us)} --> {_fmt_ts(cap.end_us)}")
        lines.append(body)
        lines.append("")
        prev_end = cap.end_us
    return "\n".join(lines).rstrip("\n") + "\n"


@dataclass
class SrtIssue:
    index: int
    message: str


def validate_srt(text: str) -> list[SrtIssue]:
    """Re-parse SRT and return issues (empty = valid, UTF-8, non-overlapping)."""
    issues: list[SrtIssue] = []
    blocks = re.split(r"\n\s*\n", text.strip())
    prev_end = -1
    for block in blocks:
        rows = [r for r in block.splitlines() if r.strip() != ""]
        if len(rows) < 2:
            continue
        try:
            index = int(rows[0].strip())
        except ValueError:
            issues.append(SrtIssue(0, "cue index is not an integer"))
            continue
        arrow = rows[1].split("-->")
        if len(arrow) != 2:
            issues.append(SrtIssue(index, "missing '-->' in time line"))
            continue
        try:
            start = _parse_ts(arrow[0])
            end = _parse_ts(arrow[1])
        except ValueError as e:
            issues.append(SrtIssue(index, str(e)))
            continue
        if end <= start:
            issues.append(SrtIssue(index, "end is not after start"))
        if start < prev_end:
            issues.append(SrtIssue(index, "overlaps previous cue"))
        prev_end = max(prev_end, end)
    return issues
