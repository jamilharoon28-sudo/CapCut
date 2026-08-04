"""Versioned evidence & decision schemas for the Human Judgement Engine (add-on §6).

Every AI/rule decision retains provenance: schema version, extractor version,
optional model id + source hash, an optional timestamp, and a calibrated
confidence. These schemas are the durable contract the later phases (window
analysis, subjects, semantics, story, sequencing, critique, learning) write into
and read from. They are pure data — no FFmpeg, no model, no I/O — so they are
unit-testable anywhere and stable across the phase gates.

Nothing here is wired into the live render path yet; the Human Judgement Engine
is built and validated phase by phase behind acceptance gates (add-on §19–§20).
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

# Bump when a schema's *meaning* changes; extractors record which version produced
# a row so re-analysis can supersede stale evidence (add-on §6, §14).
EVIDENCE_SCHEMA_VERSION = 1

StoryPurpose = Literal[
    "hook", "setup", "experience", "benefit", "proof", "payoff", "cta",
]
SHOT_TYPES = frozenset({
    "extreme_wide", "wide", "medium", "medium_close", "close_up", "extreme_close",
    "insert", "over_shoulder", "pov", "unknown",
})


class Provenance(BaseModel):
    """Common provenance carried by every piece of evidence."""

    schema_version: int = EVIDENCE_SCHEMA_VERSION
    extractor_version: str = "0"
    model_id: str | None = None
    source_hash: str | None = None
    created_at: float | None = None
    confidence: float = Field(0.0, ge=0.0, le=1.0)


class Box(BaseModel):
    """A normalised rectangle (0..1) in image space; origin top-left."""

    x: float = Field(ge=0.0, le=1.0)
    y: float = Field(ge=0.0, le=1.0)
    w: float = Field(ge=0.0, le=1.0)
    h: float = Field(ge=0.0, le=1.0)


class ShotWindow(Provenance):
    """A candidate 2–5 s usable window inside one shot of one source clip.

    One source clip can contain many shots; one shot can contain many windows.
    Later phases score *windows*, never whole files or isolated frames (§7).
    """

    id: str
    asset_id: str
    shot_start_us: int = Field(ge=0)
    shot_end_us: int = Field(ge=0)
    window_start_us: int = Field(ge=0)
    window_end_us: int = Field(ge=0)
    keyframe_times_us: list[int] = Field(default_factory=list)

    @property
    def duration_us(self) -> int:
        return max(0, self.window_end_us - self.window_start_us)


class TechnicalEvidence(Provenance):
    """Deterministic signal metrics for a window (§6/§7.2). Distributions, not
    single-frame values; calibrated against the project baseline elsewhere."""

    focus_median: float = 0.0
    focus_floor: float = 0.0            # worst-decile focus in the window
    underexposed_ratio: float = 0.0
    overexposed_ratio: float = 0.0
    clipped_shadow_ratio: float = 0.0
    clipped_highlight_ratio: float = 0.0
    flicker_score: float = 0.0
    camera_motion: float = 0.0
    camera_jerk: float = 0.0
    freeze_ratio: float = 0.0
    black_frame_ratio: float = 0.0
    audio_peak_dbfs: float | None = None
    audio_lufs: float | None = None
    hard_failures: list[str] = Field(default_factory=list)


class SubjectEvidence(Provenance):
    """Framing/subject signals (§6). Capture quality is photographic only — never
    a judgement of a person's appearance, age, ethnicity or worth."""

    face_count: int = 0
    primary_face_track: list[Box] = Field(default_factory=list)
    face_capture_quality: float | None = None   # capture signal, not attractiveness
    eyes_visible_ratio: float | None = None
    subject_stability: float = 0.0
    headroom_score: float | None = None
    edge_cut_risk: float = 0.0
    saliency_boxes: list[Box] = Field(default_factory=list)
    safe_caption_regions: list[Box] = Field(default_factory=list)


class SemanticEvidence(Provenance):
    """Optional VLM description of a shortlisted window (§6). Strict closed schema:
    unknown keys are rejected so a malformed/hallucinated payload falls back to
    Level A rather than corrupting the plan. Advisory only — it can nudge ranking
    but never overrides a technical blocker or invents advertising claims."""

    model_config = ConfigDict(extra="forbid")

    setting: str = "unknown"
    shot_type: str = "unknown"
    subjects: list[str] = Field(default_factory=list)
    actions: list[str] = Field(default_factory=list)
    visible_products: list[str] = Field(default_factory=list)
    emotion: list[str] = Field(default_factory=list)
    story_roles: list[str] = Field(default_factory=list)
    usable: bool = True
    risks: list[str] = Field(default_factory=list)


def parse_semantic(payload: dict) -> SemanticEvidence | None:
    """Validate a raw VLM payload against the closed schema. None on any failure
    (invalid JSON already parsed to dict, unknown keys, wrong types) so callers
    fall back to deterministic evidence (add-on adversarial checks §18)."""
    try:
        return SemanticEvidence.model_validate(payload)
    except Exception:
        return None


class StoryBeat(Provenance):
    """One ordered beat of the script's coverage contract (§6/§8). The script is
    authoritative: wording may be shortened but facts/offers/CTA are immutable."""

    id: str
    source_text: str
    purpose: StoryPurpose = "setup"
    required: bool = False
    desired_actions: list[str] = Field(default_factory=list)
    desired_emotions: list[str] = Field(default_factory=list)
    desired_shot_types: list[str] = Field(default_factory=list)
    caption_text: str | None = None
    immutable_facts: list[str] = Field(default_factory=list)
    min_duration_us: int = Field(default=1_500_000, ge=0)
    max_duration_us: int = Field(default=5_000_000, ge=0)


class WindowEvidence(Provenance):
    """Bundle of all evidence gathered for one window, with a content hash so a
    re-run with the same inputs+versions is a cache hit (§14)."""

    window: ShotWindow
    technical: TechnicalEvidence | None = None
    subject: SubjectEvidence | None = None
    semantic: SemanticEvidence | None = None
    evidence_hash: str | None = None
