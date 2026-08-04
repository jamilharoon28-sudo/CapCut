"""Phase 3 / F5: deterministic detection + candidate building."""

from __future__ import annotations

from capcut_coach.roughcut.detect import DetectionSettings, segment_transcript
from capcut_coach.roughcut.plan import build_candidates
from capcut_coach.schemas.edit_plan import validate_edit_plan
from capcut_coach.transcript import Transcript, Word

S = 1_000_000


def _t(*words):
    return Transcript(asset_id="a1", words=[Word(*w) for w in words])


def test_filler_unit_is_flagged_not_deleted():
    # Gaps >350ms isolate "um" into its own unit, which is then flagged filler.
    t = _t(("So", 0, 300_000, 0.9), ("um", 700_000, 1_000_000, 0.9),
           ("here", 1_400_000, 1_800_000, 0.95))
    units = segment_transcript(t)
    fillers = [u for u in units if u.kind == "filler"]
    assert fillers and all(not u.keep for u in fillers)
    # Nothing removed: the surrounding speech units remain.
    assert sum(len(u.words) for u in units if u.kind == "speech") >= 2


def test_long_silence_removed_but_dramatic_pause_kept():
    s = DetectionSettings()
    # >1.5s dead air -> removed long silence; 0.7-1.5s beat -> kept dramatic pause.
    t = _t(("one", 0, 300_000, 0.9), ("two", 2_000_000, 2_300_000, 0.9),
           ("three", 3_300_000, 3_600_000, 0.9))
    units = segment_transcript(t, s)
    silences = [u for u in units if u.kind == "silence"]
    assert any(u.reason == "long_silence" and not u.keep for u in silences)
    assert any(u.reason == "dramatic_pause" and u.keep for u in silences)


def test_false_restart_is_flagged():
    t = _t(("I think", 0, 400_000, 0.9), ("hmmmm", 500_000, 900_000, 0.4))
    # Build a clear restart: "let me" then "let me explain"
    t = Transcript(asset_id="a1", words=[
        Word("let", 0, 200_000, 0.9), Word("me", 250_000, 450_000, 0.9),
        Word("let", 1_000_000, 1_200_000, 0.9), Word("me", 1_250_000, 1_450_000, 0.9),
        Word("explain", 1_500_000, 1_900_000, 0.9),
    ])
    units = segment_transcript(t)
    assert any(u.kind in ("restart", "repeat") and not u.keep for u in units)


def test_candidates_are_valid_and_respect_target():
    words = []
    cursor = 0
    for i in range(20):
        # 400ms word + 400ms gap -> each word is its own phrase unit.
        words.append(Word(f"word{i}", cursor, cursor + 400_000, 0.95))
        cursor += 800_000
    t = Transcript(asset_id="a1", words=words)
    units = segment_transcript(t)
    media_us = cursor
    result = build_candidates(project_id="p1", asset_id="a1",
                              media_duration_us=media_us, units=units,
                              target_durations_us=(3 * S, 5 * S))
    assert result.candidates
    for cand in result.candidates:
        assert validate_edit_plan(cand.plan, {"a1": media_us}) == []
        assert cand.plan.total_timeline_us <= cand.target_us + 200_000
