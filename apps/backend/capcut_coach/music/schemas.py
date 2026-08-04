"""Music library schemas (pack doc 20 §3)."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class RightsStatus(str, Enum):
    OWNER_APPROVED = "OWNER_APPROVED"   # placed by the owner in an approved folder
    SHIPPED_LICENSED = "SHIPPED_LICENSED"  # bundled with documented redistribution rights
    INELIGIBLE = "INELIGIBLE"           # anything else — never auto-selectable


class MusicAsset(BaseModel):
    id: str
    content_hash: str
    path: str
    title: str
    rights_status: RightsStatus
    rights_note: str = ""
    allowed_uses: list[str] = Field(default_factory=lambda: ["organic_social"])
    expires_at: str | None = None
    bpm: float = 0.0
    duration_s: float = 0.0
    energy: float = 0.0
    mood_tags: list[str] = Field(default_factory=list)
    vocals: bool = False
    analysis_version: str = "audio_dna_v1"

    @property
    def eligible(self) -> bool:
        """Only rights-cleared tracks may be auto-selected (doc 20 acceptance)."""
        return self.rights_status in (RightsStatus.OWNER_APPROVED, RightsStatus.SHIPPED_LICENSED)


class MusicSelection(BaseModel):
    chosen: MusicAsset | None
    alternatives: list[MusicAsset] = Field(default_factory=list)
    reason: str = ""              # shown under "Why Coach chose this"
    considered: int = 0
