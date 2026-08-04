"""Typed preflight schemas (pack doc 19 §6).

The normal UI shows only the plain-language outcome; confidence, evidence ids and
validation rules are stored but not surfaced in beginner mode.
"""

from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field

RequirementKind = Literal["story_beat", "shot_role", "brand_asset", "audio", "delivery"]


class ReadinessStatus(str, Enum):
    READY = "READY"
    READY_WITH_SUGGESTIONS = "READY_WITH_SUGGESTIONS"
    NEEDS_HELP = "NEEDS_HELP"


class PreflightRequirement(BaseModel):
    id: str
    kind: RequirementKind
    description: str
    mandatory: bool = False
    # Free-form validation notes kept internal (not shown in beginner mode).
    rule: str = ""


class EvidenceMatch(BaseModel):
    requirement_id: str
    matched: bool
    evidence_ids: list[str] = Field(default_factory=list)
    confidence: float = Field(0.0, ge=0.0, le=1.0)
    note: str = ""


class RequestCard(BaseModel):
    """A single plain-language ask (doc 19 §4)."""

    type: str
    what_needed: str            # what is needed, ordinary language
    why: str                    # one sentence
    recommended_action: str     # recommended option, shown first
    fallback: str               # a safe alternative
    quality_impact: str         # effect of proceeding without it
    blocking: bool = False
    affected_story_beats: list[str] = Field(default_factory=list)
    recording_direction: str | None = None  # for missing-footage asks
    quotation: str | None = None             # script line / thumbnail hint


class ReadinessReport(BaseModel):
    status: ReadinessStatus
    required_resolved: int
    required_total: int
    blocking_requests: list[RequestCard] = Field(default_factory=list)
    suggestions: list[RequestCard] = Field(default_factory=list)
    # Internal detail (Advanced only).
    requirements: list[PreflightRequirement] = Field(default_factory=list)
    matches: list[EvidenceMatch] = Field(default_factory=list)

    @property
    def headline(self) -> str:
        if self.status == ReadinessStatus.READY:
            return "Ready to create"
        if self.status == ReadinessStatus.READY_WITH_SUGGESTIONS:
            return "Ready — a couple of things would make it better"
        n = len(self.blocking_requests)
        return f"I need your help with {n} thing{'s' if n != 1 else ''}"
