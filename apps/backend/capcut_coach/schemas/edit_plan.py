"""Internal edit-plan contract (09_API_CONFIG_AND_STORAGE_CONTRACT.md §5).

The single editorial source of truth. All persisted time is **integer
microseconds** — never floating-point seconds (CLAUDE.md). Every adapter
(preview, SRT, CapCut handoff/clone) translates *from* this contract; CapCut ids
never leak in.

``validate_edit_plan`` enforces the Phase 3 exit gate and acceptance test F6:
every referenced asset/unit exists, no source or timeline interval is invalid or
out of media bounds, and captions/segments do not overlap illegally.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, NonNegativeInt, PositiveInt

SegmentRole = Literal["hook", "point", "evidence", "cta", "broll", "transition", "filler"]


class Canvas(BaseModel):
    width: PositiveInt = 1080
    height: PositiveInt = 1920
    fps_num: PositiveInt = 30
    fps_den: PositiveInt = 1


class Transform(BaseModel):
    scale: float = 1.0
    x: float = 0.0
    y: float = 0.0


class Segment(BaseModel):
    id: str
    asset_id: str
    source_start_us: NonNegativeInt
    source_duration_us: PositiveInt
    timeline_start_us: NonNegativeInt
    timeline_duration_us: PositiveInt
    role: SegmentRole = "point"
    reason: str = ""
    confidence: float = Field(0.0, ge=0.0, le=1.0)
    transform: Transform = Field(default_factory=Transform)
    must_review: bool = False
    # Provenance back to the transcript unit(s) this came from (Phase 3 restore).
    source_unit_ids: list[str] = Field(default_factory=list)

    @property
    def source_end_us(self) -> int:
        return self.source_start_us + self.source_duration_us

    @property
    def timeline_end_us(self) -> int:
        return self.timeline_start_us + self.timeline_duration_us


class Caption(BaseModel):
    id: str
    text: str
    start_us: NonNegativeInt
    duration_us: PositiveInt
    line_breaks: list[str] = Field(default_factory=list)

    @property
    def end_us(self) -> int:
        return self.start_us + self.duration_us


class AudioTrack(BaseModel):
    id: str
    kind: Literal["voice", "music", "sfx"] = "voice"
    asset_id: str | None = None
    gain_db: float = 0.0
    duck_to_db: float | None = None


class BrollItem(BaseModel):
    id: str
    concept: str
    asset_id: str | None = None  # None = placeholder, needs owned asset
    timeline_start_us: NonNegativeInt = 0
    timeline_duration_us: PositiveInt = 1


class EditPlan(BaseModel):
    schema_version: int = 1
    id: str
    project_id: str
    style_dna_version: str | None = None
    canvas: Canvas = Field(default_factory=Canvas)
    segments: list[Segment] = Field(default_factory=list)
    captions: list[Caption] = Field(default_factory=list)
    audio_tracks: list[AudioTrack] = Field(default_factory=list)
    broll: list[BrollItem] = Field(default_factory=list)
    graphics: list[dict] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)

    @property
    def total_timeline_us(self) -> int:
        return max((s.timeline_end_us for s in self.segments), default=0)


class EditPlanValidationError(ValueError):
    def __init__(self, errors: list[str]) -> None:
        self.errors = errors
        super().__init__("; ".join(errors))


def validate_edit_plan(plan: EditPlan, asset_durations_us: dict[str, int]) -> list[str]:
    """Return a list of errors (empty = valid). Raises nothing.

    ``asset_durations_us`` maps asset_id -> media duration in microseconds.
    """
    errors: list[str] = []

    seen_segment_ids: set[str] = set()
    for seg in plan.segments:
        if seg.id in seen_segment_ids:
            errors.append(f"duplicate segment id {seg.id}")
        seen_segment_ids.add(seg.id)

        if seg.asset_id not in asset_durations_us:
            errors.append(f"segment {seg.id} references unknown asset {seg.asset_id}")
            continue
        media_us = asset_durations_us[seg.asset_id]
        if seg.source_start_us >= media_us:
            errors.append(f"segment {seg.id} starts at/after media end")
        if seg.source_end_us > media_us:
            errors.append(f"segment {seg.id} source range exceeds media duration")

    # Timeline segments must not overlap (single video track model).
    ordered = sorted(plan.segments, key=lambda s: s.timeline_start_us)
    for prev, cur in zip(ordered, ordered[1:]):
        if cur.timeline_start_us < prev.timeline_end_us:
            errors.append(f"timeline overlap between {prev.id} and {cur.id}")

    # Captions must not overlap and must have positive duration (F7/QC).
    cap_ordered = sorted(plan.captions, key=lambda c: c.start_us)
    for prev, cur in zip(cap_ordered, cap_ordered[1:]):
        if cur.start_us < prev.end_us:
            errors.append(f"caption overlap between {prev.id} and {cur.id}")

    total = plan.total_timeline_us
    for cap in plan.captions:
        if total and cap.end_us > total:
            errors.append(f"caption {cap.id} extends beyond the timeline")

    return errors


def assert_valid(plan: EditPlan, asset_durations_us: dict[str, int]) -> None:
    errors = validate_edit_plan(plan, asset_durations_us)
    if errors:
        raise EditPlanValidationError(errors)
