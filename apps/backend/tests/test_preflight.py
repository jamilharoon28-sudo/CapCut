"""Smart Preflight (doc 19): readiness decisions and honest fallbacks."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from capcut_coach.preflight import run_preflight
from capcut_coach.preflight.schemas import ReadinessStatus


@dataclass
class FakeAsset:
    id: str
    path: Path
    duration_us: int
    has_audio: bool = True


@dataclass
class FakeAnalysis:
    score: float
    best_start_us: int = 0
    crop_x_norm: float = 0.0


def _catalog(n, dur=4_000_000):
    return [FakeAsset(id=f"a{i}", path=Path(f"/x/{i}.mp4"), duration_us=dur) for i in range(n)]


def test_no_footage_blocks_with_recording_direction():
    r = run_preflight([], script_beats=["A", "B"])
    assert r.status == ReadinessStatus.NEEDS_HELP
    assert any(c.type == "no_usable_footage" and c.blocking for c in r.blocking_requests)
    assert r.blocking_requests[0].recording_direction  # tells them what to film


def test_enough_footage_and_story_is_ready_or_suggestions():
    # 4 clips, 4 beats, logo+music present → nothing missing → READY.
    r = run_preflight(_catalog(4), script_beats=["one", "two", "three", "four"],
                      music_present=True, logo_present=True)
    assert r.status == ReadinessStatus.READY
    assert r.required_resolved == r.required_total
    assert not r.blocking_requests


def test_missing_logo_and_music_are_suggestions_not_blocking():
    r = run_preflight(_catalog(3), script_beats=["a", "b", "c"])
    assert r.status == ReadinessStatus.READY_WITH_SUGGESTIONS
    types = {c.type for c in r.suggestions}
    assert "missing_logo" in types and "missing_music" in types
    for c in r.suggestions:
        assert c.fallback and c.quality_impact  # every ask states fallback + impact
    assert not r.blocking_requests  # honest fallbacks exist → never blocks


def test_more_beats_than_clips_suggests_shots_but_does_not_block():
    r = run_preflight(_catalog(2), script_beats=["a", "b", "c", "d", "e"])
    shots = [c for c in r.suggestions if c.type == "missing_shots"]
    assert shots and shots[0].recording_direction
    assert not shots[0].blocking
    assert r.status == ReadinessStatus.READY_WITH_SUGGESTIONS


def test_weak_clips_flagged_from_analysis():
    cat = _catalog(3)
    analyses = {"a0": FakeAnalysis(score=0.2), "a1": FakeAnalysis(score=0.9),
                "a2": FakeAnalysis(score=0.9)}
    r = run_preflight(cat, script_beats=["x", "y"], analyses=analyses,
                      music_present=True, logo_present=True)
    assert any(c.type == "weak_clips" for c in r.suggestions)


def test_never_ready_while_a_mandatory_beat_is_unresolved():
    # Zero footage but a script with beats → mandatory beats unresolved → not READY.
    r = run_preflight([], script_beats=["must include this fact"])
    assert r.status == ReadinessStatus.NEEDS_HELP
    assert r.required_resolved < r.required_total
