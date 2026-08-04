"""Per-beat clip alternatives and the "Change this clip" swap (increment #2).

A finished montage places one clip in each timeline *slot*. Beginners often think
"that shot's fine, but swap the third one." This module answers two questions
without re-analysing anything:

* ``build_slots`` — for each slot, which *other* clips could fill it just as well?
  Alternatives must be able to cover the slot's exact duration (so a swap never
  changes timing) and are ranked by their analysed quality score. Clips already
  used in the neighbouring slots are excluded to preserve visual variety.
* ``replace_slot`` — produce a new EditPlan with one slot rebuilt from the chosen
  clip: start on that clip's best moment, reframe on its subject, keep the slot's
  timeline position and length identical. Everything else is untouched.

Pure and deterministic: no FFmpeg, no disk, no mutation of the input plan.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass

from pydantic import BaseModel, Field

from ..schemas.edit_plan import EditPlan, Transform

SECOND_US = 1_000_000
_DEFAULT_MAX_ALTERNATIVES = 4


@dataclass(frozen=True)
class AssetRef:
    """A catalog clip as slots need it — id, display name, duration."""

    id: str
    name: str
    duration_us: int


class SlotAlternative(BaseModel):
    asset_id: str
    label: str
    score: float
    reason: str = ""


class Slot(BaseModel):
    index: int
    segment_id: str
    asset_id: str
    label: str
    timeline_start_us: int
    duration_us: int
    role: str
    caption: str | None = None
    alternatives: list[SlotAlternative] = Field(default_factory=list)


def _an(analyses: dict | None, asset_id: str, attr: str, default):
    """Read an analysis attribute whether analyses holds objects or plain dicts."""
    a = (analyses or {}).get(asset_id)
    if a is None:
        return default
    if isinstance(a, dict):
        return a.get(attr, default)
    return getattr(a, attr, default)


def _label(name: str) -> str:
    """Trim a filename into a short, friendly shot label."""
    stem = name.rsplit("/", 1)[-1]
    for ext in (".mov", ".mp4", ".m4v", ".avi", ".mkv"):
        if stem.lower().endswith(ext):
            stem = stem[: -len(ext)]
            break
    return stem.replace("_", " ").replace("-", " ").strip() or name


def build_slots(
    plan: EditPlan,
    assets: list[AssetRef],
    analyses: dict | None = None,
    *,
    max_alternatives: int = _DEFAULT_MAX_ALTERNATIVES,
) -> list[Slot]:
    """List timeline slots, each with ranked alternative clips that fit exactly."""
    by_id = {a.id: a for a in assets}
    cap_by_start = {c.start_us: c.text for c in plan.captions}
    seg_order = sorted(plan.segments, key=lambda s: s.timeline_start_us)

    slots: list[Slot] = []
    for i, seg in enumerate(seg_order):
        dur = seg.timeline_duration_us
        prev_id = seg_order[i - 1].asset_id if i > 0 else None
        nxt_id = seg_order[i + 1].asset_id if i + 1 < len(seg_order) else None

        alts: list[SlotAlternative] = []
        for a in assets:
            if a.id == seg.asset_id or a.id in (prev_id, nxt_id):
                continue
            if a.duration_us < dur:  # must cover the slot exactly — no timing drift
                continue
            score = float(_an(analyses, a.id, "score", 0.0))
            alts.append(SlotAlternative(
                asset_id=a.id, label=_label(a.name), score=round(score, 3),
                reason="sharper, well-exposed shot" if score >= 0.6 else "another usable take",
            ))
        # Highest quality first; stable by asset id for determinism on ties.
        alts.sort(key=lambda x: (-x.score, x.asset_id))

        cur = by_id.get(seg.asset_id)
        slots.append(Slot(
            index=i, segment_id=seg.id, asset_id=seg.asset_id,
            label=_label(cur.name) if cur else seg.asset_id,
            timeline_start_us=seg.timeline_start_us, duration_us=dur, role=seg.role,
            caption=cap_by_start.get(seg.timeline_start_us),
            alternatives=alts[:max_alternatives],
        ))
    return slots


def replace_slot(
    plan: EditPlan,
    assets: list[AssetRef],
    analyses: dict | None,
    slot_index: int,
    new_asset_id: str,
) -> EditPlan:
    """Return a new plan with slot ``slot_index`` rebuilt from ``new_asset_id``.

    Timing is preserved exactly: the new clip must be at least as long as the slot
    (enforced by ``build_slots``); it starts on its best moment and is reframed on
    its subject. Raises ``KeyError``/``IndexError`` on bad input.
    """
    by_id = {a.id: a for a in assets}
    if new_asset_id not in by_id:
        raise KeyError(new_asset_id)
    p = copy.deepcopy(plan)
    seg_order = sorted(p.segments, key=lambda s: s.timeline_start_us)
    if not 0 <= slot_index < len(seg_order):
        raise IndexError(slot_index)

    seg = seg_order[slot_index]
    asset = by_id[new_asset_id]
    dur = seg.timeline_duration_us
    default_best = min(int(0.3 * SECOND_US), asset.duration_us // 10)
    best = int(_an(analyses, new_asset_id, "best_start_us", default_best))
    src_start = max(0, min(best, max(0, asset.duration_us - dur)))
    src_dur = min(dur, asset.duration_us - src_start)
    if src_dur <= 0:  # defensive: clip unexpectedly short, use it whole from 0
        src_start, src_dur = 0, min(dur, asset.duration_us)

    seg.asset_id = new_asset_id
    seg.source_start_us = src_start
    seg.source_duration_us = src_dur
    seg.timeline_duration_us = src_dur
    seg.reason = "user_swapped_clip"
    seg.confidence = float(_an(analyses, new_asset_id, "score", seg.confidence))
    seg.transform = Transform(
        scale=1.0, x=float(_an(analyses, new_asset_id, "crop_x_norm", 0.0)), y=0.0)
    return p
