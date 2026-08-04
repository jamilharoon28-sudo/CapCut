"""Grouped factual review before publish (increment #3).

CLAUDE.md rule 14: Coach must not claim an edit is publish-ready before the owner
has reviewed it, and Claude outputs are untrusted suggestions. This module turns a
finished plan into a short, grouped checklist the beginner confirms *before* the
video is saved out:

* **Words on screen** — every caption line, to confirm it's true and not overstated
  (each requires acknowledgement; Coach never invents facts).
* **Shots to double-check** — low-confidence or explicitly flagged picks (advisory).
* **Music rights** — if a track was used, confirm it's owned/licensed (required).
* **Branded ending** — if a logo outro was added (advisory).

``required_ack_ids`` returns the items that must be ticked; the approve endpoint
refuses to save until all of them are acknowledged. Pure and deterministic.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from ..schemas.edit_plan import EditPlan

_LOW_CONFIDENCE = 0.35


class ReviewItem(BaseModel):
    id: str
    label: str
    detail: str = ""
    kind: str                       # claim | shot | music | branding
    requires_ack: bool = False


class ReviewGroup(BaseModel):
    key: str
    title: str
    note: str = ""
    items: list[ReviewItem] = Field(default_factory=list)


def build_review_groups(
    plan: EditPlan,
    *,
    music_present: bool = False,
    music_name: str | None = None,
    logo_present: bool = False,
) -> list[ReviewGroup]:
    groups: list[ReviewGroup] = []

    claims = [
        ReviewItem(
            id=f"claim-{i}", label=c.text, kind="claim", requires_ack=True,
            detail="On-screen text — confirm it's accurate and not overstated.",
        )
        for i, c in enumerate(sorted(plan.captions, key=lambda c: c.start_us))
        if c.text.strip()
    ]
    if claims:
        groups.append(ReviewGroup(
            key="claims", title="Words on screen",
            note="Coach never invents facts. Confirm each line is true before saving.",
            items=claims))

    shots = [
        ReviewItem(
            id=f"shot-{s.id}", label=f"Shot {i + 1} · {s.role}", kind="shot",
            detail="A less-confident pick — check it represents you well.",
        )
        for i, s in enumerate(sorted(plan.segments, key=lambda s: s.timeline_start_us))
        if s.must_review or s.confidence < _LOW_CONFIDENCE
    ]
    if shots:
        groups.append(ReviewGroup(
            key="shots", title="Shots to double-check",
            note="Optional — swap any of these on the previous screen if you prefer.",
            items=shots))

    if music_present:
        groups.append(ReviewGroup(
            key="music", title="Music rights",
            note="Coach only reads local files and never downloads music.",
            items=[ReviewItem(
                id="music-rights", label=music_name or "Selected track", kind="music",
                requires_ack=True,
                detail="Confirm you own this track or are licensed to use it.")]))

    if logo_present:
        groups.append(ReviewGroup(
            key="branding", title="Branded ending",
            items=[ReviewItem(
                id="branding-logo", label="Logo outro", kind="branding",
                detail="Your logo appears on the closing card.")]))

    return groups


def required_ack_ids(groups: list[ReviewGroup]) -> set[str]:
    """Item ids that must be acknowledged before the video can be saved."""
    return {it.id for g in groups for it in g.items if it.requires_ack}
