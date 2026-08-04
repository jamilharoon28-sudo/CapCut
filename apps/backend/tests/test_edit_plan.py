"""Phase 3 exit gate + F6: edit-plan validity."""

from __future__ import annotations

from capcut_coach.schemas.edit_plan import Caption, EditPlan, Segment, validate_edit_plan


def _seg(sid, start, dur, tl_start):
    return Segment(id=sid, asset_id="a1", source_start_us=start, source_duration_us=dur,
                   timeline_start_us=tl_start, timeline_duration_us=dur)


def test_valid_plan_has_no_errors():
    plan = EditPlan(id="e1", project_id="p1", segments=[
        _seg("s1", 0, 1_000_000, 0),
        _seg("s2", 2_000_000, 1_000_000, 1_000_000),
    ])
    assert validate_edit_plan(plan, {"a1": 5_000_000}) == []


def test_source_range_beyond_media_is_rejected():
    plan = EditPlan(id="e1", project_id="p1", segments=[_seg("s1", 4_500_000, 1_000_000, 0)])
    errors = validate_edit_plan(plan, {"a1": 5_000_000})
    assert any("exceeds media duration" in e for e in errors)


def test_unknown_asset_is_rejected():
    plan = EditPlan(id="e1", project_id="p1", segments=[_seg("s1", 0, 1000, 0)])
    errors = validate_edit_plan(plan, {"other": 5_000_000})
    assert any("unknown asset" in e for e in errors)


def test_timeline_overlap_is_rejected():
    plan = EditPlan(id="e1", project_id="p1", segments=[
        _seg("s1", 0, 2_000_000, 0),
        _seg("s2", 0, 2_000_000, 1_000_000),  # overlaps s1
    ])
    errors = validate_edit_plan(plan, {"a1": 5_000_000})
    assert any("overlap" in e for e in errors)


def test_caption_overlap_is_rejected():
    plan = EditPlan(id="e1", project_id="p1",
                    segments=[_seg("s1", 0, 3_000_000, 0)],
                    captions=[
                        Caption(id="c1", text="a", start_us=0, duration_us=2_000_000),
                        Caption(id="c2", text="b", start_us=1_000_000, duration_us=1_000_000),
                    ])
    errors = validate_edit_plan(plan, {"a1": 5_000_000})
    assert any("caption overlap" in e for e in errors)
