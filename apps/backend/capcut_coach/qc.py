"""Deterministic quality-control checks (Phase 9, test F12).

Runs without Claude. Each finding carries a timecode (microseconds), a severity,
and a suggested action. Editorial QC (via the Claude layer) layers on top of
this; these deterministic checks are always available.
"""

from __future__ import annotations

from dataclasses import dataclass

from .schemas.edit_plan import Canvas, EditPlan

# Reading-speed ceiling for captions (characters per second). Above this we warn.
MAX_CHARS_PER_SECOND = 22


@dataclass
class QcFinding:
    timecode_us: int
    severity: str  # info | minor | major | blocker
    code: str
    message: str
    suggested_action: str

    def to_public(self) -> dict:
        return {
            "timecode_us": self.timecode_us,
            "severity": self.severity,
            "code": self.code,
            "message": self.message,
            "suggested_action": self.suggested_action,
        }


def check_caption_overlaps(plan: EditPlan) -> list[QcFinding]:
    findings: list[QcFinding] = []
    ordered = sorted(plan.captions, key=lambda c: c.start_us)
    for prev, cur in zip(ordered, ordered[1:]):
        if cur.start_us < prev.end_us:
            findings.append(
                QcFinding(cur.start_us, "major", "caption_overlap",
                          "Two captions overlap in time.",
                          "Shorten the earlier caption or delay the later one.")
            )
    return findings


def check_reading_speed(plan: EditPlan) -> list[QcFinding]:
    findings: list[QcFinding] = []
    for cap in plan.captions:
        seconds = cap.duration_us / 1_000_000
        if seconds <= 0:
            continue
        cps = len(cap.text) / seconds
        if cps > MAX_CHARS_PER_SECOND:
            findings.append(
                QcFinding(cap.start_us, "minor", "reading_speed",
                          f"Caption is fast to read ({cps:.0f} chars/s).",
                          "Split the line or hold it slightly longer.")
            )
    return findings


def check_aspect_ratio(plan: EditPlan, expected: Canvas | None = None) -> list[QcFinding]:
    expected = expected or Canvas()
    c = plan.canvas
    if (c.width, c.height) != (expected.width, expected.height):
        return [QcFinding(0, "major", "aspect_ratio",
                          f"Canvas is {c.width}x{c.height}, expected "
                          f"{expected.width}x{expected.height}.",
                          "Set the project ratio to match the target format.")]
    return []


def check_timeline_gaps(plan: EditPlan) -> list[QcFinding]:
    findings: list[QcFinding] = []
    ordered = sorted(plan.segments, key=lambda s: s.timeline_start_us)
    for prev, cur in zip(ordered, ordered[1:]):
        gap = cur.timeline_start_us - prev.timeline_end_us
        if gap > 0:
            findings.append(
                QcFinding(prev.timeline_end_us, "minor", "timeline_gap",
                          "There is a blank gap between two clips.",
                          "Close the gap unless the pause is intentional.")
            )
    return findings


def check_missing_cta(plan: EditPlan) -> list[QcFinding]:
    if not any(s.role == "cta" for s in plan.segments) and not any(
        b.concept.lower().find("cta") >= 0 for b in plan.broll
    ):
        return [QcFinding(plan.total_timeline_us, "info", "missing_cta",
                          "No call-to-action was detected at the end.",
                          "Add an end card or CTA if this video needs one.")]
    return []


def run_deterministic_qc(plan: EditPlan, expected_canvas: Canvas | None = None) -> list[QcFinding]:
    findings: list[QcFinding] = []
    findings += check_caption_overlaps(plan)
    findings += check_reading_speed(plan)
    findings += check_aspect_ratio(plan, expected_canvas)
    findings += check_timeline_gaps(plan)
    findings += check_missing_cta(plan)
    severity_rank = {"blocker": 0, "major": 1, "minor": 2, "info": 3}
    findings.sort(key=lambda f: (severity_rank.get(f.severity, 9), f.timecode_us))
    return findings
