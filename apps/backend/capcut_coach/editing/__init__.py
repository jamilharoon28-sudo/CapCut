"""Post-render editorial controls: per-slot clip alternatives and the pre-publish
factual review (increments #2 and #3).

Both modules are pure and deterministic — they operate on a persisted EditPlan and
a lightweight asset catalog, with no FFmpeg or filesystem dependency — so they are
unit-testable anywhere and never touch the owner's originals.
"""

from __future__ import annotations

from .review import ReviewGroup, ReviewItem, build_review_groups, required_ack_ids
from .slots import AssetRef, Slot, SlotAlternative, build_slots, replace_slot

__all__ = [
    "AssetRef",
    "ReviewGroup",
    "ReviewItem",
    "Slot",
    "SlotAlternative",
    "build_review_groups",
    "build_slots",
    "replace_slot",
    "required_ack_ids",
]
