"""Increment #2: per-slot alternatives and the clip swap are pure + deterministic."""

from __future__ import annotations

from capcut_coach.editing import AssetRef, build_slots, replace_slot
from capcut_coach.schemas.edit_plan import Caption, EditPlan, Segment

US = 1_000_000


def _plan() -> EditPlan:
    segs = [
        Segment(id=f"seg{i}", asset_id=f"a{i}", source_start_us=0,
                source_duration_us=2 * US, timeline_start_us=i * 2 * US,
                timeline_duration_us=2 * US, confidence=0.5)
        for i in range(3)
    ]
    caps = [Caption(id=f"c{i}", text=f"line {i}", start_us=i * 2 * US, duration_us=2 * US)
            for i in range(3)]
    return EditPlan(id="edit1", project_id="p1", segments=segs, captions=caps)


def _assets() -> list[AssetRef]:
    # a0..a2 are used; a3 and a4 are spare footage long enough to swap in.
    return [AssetRef(id=f"a{i}", name=f"beach_clip_{i}.mp4", duration_us=5 * US)
            for i in range(5)]


def test_slots_list_current_clip_caption_and_alternatives():
    slots = build_slots(_plan(), _assets(), analyses=None)
    assert [s.index for s in slots] == [0, 1, 2]
    mid = slots[1]
    assert mid.asset_id == "a1"
    assert mid.caption == "line 1"
    alt_ids = {a.asset_id for a in mid.alternatives}
    # Current clip and both neighbours are excluded to keep visual variety.
    assert "a1" not in alt_ids and "a0" not in alt_ids and "a2" not in alt_ids
    assert {"a3", "a4"} <= alt_ids


def test_alternatives_ranked_by_quality_score():
    analyses = {"a3": {"score": 0.9}, "a4": {"score": 0.2}}
    slots = build_slots(_plan(), _assets(), analyses=analyses)
    ranked = [a.asset_id for a in slots[1].alternatives]
    assert ranked.index("a3") < ranked.index("a4")


def test_too_short_clips_are_not_offered():
    assets = _assets() + [AssetRef(id="short", name="tiny.mp4", duration_us=US // 2)]
    slots = build_slots(_plan(), assets)
    assert all("short" not in {a.asset_id for a in s.alternatives} for s in slots)


def test_replace_slot_swaps_clip_and_preserves_timing():
    plan = _plan()
    analyses = {"a4": {"score": 0.8, "best_start_us": 1 * US, "crop_x_norm": 0.25}}
    new_plan = replace_slot(plan, _assets(), analyses, slot_index=1, new_asset_id="a4")

    # Original plan is untouched (pure function).
    assert plan.segments[1].asset_id == "a1"

    swapped = sorted(new_plan.segments, key=lambda s: s.timeline_start_us)[1]
    assert swapped.asset_id == "a4"
    assert swapped.source_start_us == 1 * US       # started on its best moment
    assert swapped.timeline_start_us == 2 * US     # slot position unchanged
    assert swapped.timeline_duration_us == 2 * US  # slot length unchanged
    assert swapped.transform.x == 0.25             # reframed on subject
    assert swapped.reason == "user_swapped_clip"

    # Timeline stays contiguous and non-overlapping.
    ordered = sorted(new_plan.segments, key=lambda s: s.timeline_start_us)
    for prev, cur in zip(ordered, ordered[1:]):
        assert cur.timeline_start_us == prev.timeline_start_us + prev.timeline_duration_us


def test_replace_slot_rejects_unknown_clip_and_bad_index():
    import pytest

    plan = _plan()
    with pytest.raises(KeyError):
        replace_slot(plan, _assets(), None, 0, "nope")
    with pytest.raises(IndexError):
        replace_slot(plan, _assets(), None, 9, "a3")
