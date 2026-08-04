"""Increment #3: the pre-publish factual review groups claims and gates saving."""

from __future__ import annotations

from capcut_coach.editing import build_review_groups, required_ack_ids
from capcut_coach.schemas.edit_plan import Caption, EditPlan, Segment

US = 1_000_000


def _plan(*, low_conf: bool = False) -> EditPlan:
    segs = [
        Segment(id="seg0", asset_id="a0", source_start_us=0, source_duration_us=2 * US,
                timeline_start_us=0, timeline_duration_us=2 * US, confidence=0.8),
        Segment(id="seg1", asset_id="a1", source_start_us=0, source_duration_us=2 * US,
                timeline_start_us=2 * US, timeline_duration_us=2 * US,
                confidence=0.1 if low_conf else 0.8),
    ]
    caps = [Caption(id="c0", text="50% off today", start_us=0, duration_us=2 * US)]
    return EditPlan(id="e", project_id="p", segments=segs, captions=caps)


def test_claims_group_requires_acknowledgement():
    groups = build_review_groups(_plan())
    claims = next(g for g in groups if g.key == "claims")
    assert claims.items[0].label == "50% off today"
    assert claims.items[0].requires_ack is True
    assert "claim-0" in required_ack_ids(groups)


def test_music_rights_is_required_when_music_present():
    groups = build_review_groups(_plan(), music_present=True, music_name="track.mp3")
    music = next(g for g in groups if g.key == "music")
    assert music.items[0].requires_ack is True
    assert "music-rights" in required_ack_ids(groups)


def test_low_confidence_shot_is_flagged_but_not_blocking():
    groups = build_review_groups(_plan(low_conf=True))
    shots = next(g for g in groups if g.key == "shots")
    assert shots.items and all(not it.requires_ack for it in shots.items)


def test_logo_and_no_music_do_not_add_required_acks():
    groups = build_review_groups(_plan(), logo_present=True)
    # Only the caption claim is required; branding is advisory, music absent.
    assert required_ack_ids(groups) == {"claim-0"}
    assert any(g.key == "branding" for g in groups)
