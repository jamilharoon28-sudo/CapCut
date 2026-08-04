"""Autopilot decision schemas (pack doc 20 §6)."""

from __future__ import annotations

from pydantic import BaseModel, Field


class CandidateScore(BaseModel):
    name: str                      # clean | enhanced | bold
    score: float
    reasons: list[str] = Field(default_factory=list)


class AutopilotDecision(BaseModel):
    chosen: str | None             # the candidate to render as the final
    scores: list[CandidateScore] = Field(default_factory=list)
    reason: str = ""

    def score_of(self, name: str) -> float:
        for s in self.scores:
            if s.name == name:
                return s.score
        return 0.0
