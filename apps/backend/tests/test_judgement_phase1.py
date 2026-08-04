"""Human Judgement Engine — Phase 1: technical metrics, windows, sampling argv.

Pure/media-independent parts are proven here with synthetic frames; the FFmpeg
decode + PySceneDetect paths run on the Mac against real footage (BLOCKED here)."""

from __future__ import annotations

import numpy as np

from capcut_coach.judgement.boundaries import (
    candidate_windows, uniform_shots,
)
from capcut_coach.judgement.calibration import hard_failures
from capcut_coach.judgement.sampling import window_frames_command
from capcut_coach.judgement.technical import analyse_window

US = 1_000_000
H, W = 72, 128


def _sharp_frame(seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    return (rng.integers(0, 256, size=(H, W))).astype(np.uint8)


def _flat_frame(value: int) -> np.ndarray:
    return np.full((H, W), value, dtype=np.uint8)


# ---------- technical metrics (§7.2) ----------

def test_sharp_beats_blurred_on_focus():
    sharp = analyse_window([_sharp_frame(i) for i in range(6)])
    # A smooth gradient has almost no high-frequency detail → low focus.
    grad = np.tile(np.linspace(0, 255, W, dtype=np.uint8), (H, 1))
    blurred = analyse_window([grad for _ in range(6)])
    assert sharp.focus_median > blurred.focus_median


def test_black_window_flagged_and_blocked():
    tech = analyse_window([_flat_frame(0) for _ in range(6)])
    assert tech.black_frame_ratio == 1.0
    assert tech.clipped_shadow_ratio > 0.9
    assert "near_black" in hard_failures(tech) or "crushed_shadows" in hard_failures(tech)


def test_frozen_window_has_high_freeze_ratio():
    frame = _sharp_frame(1)
    tech = analyse_window([frame.copy() for _ in range(6)])
    assert tech.freeze_ratio == 1.0


def test_flicker_is_detected():
    frames = [_flat_frame(40 if i % 2 == 0 else 200) for i in range(6)]
    tech = analyse_window(frames)
    assert tech.flicker_score > 0.3


def test_empty_frames_are_a_hard_failure():
    tech = analyse_window([])
    assert "no_frames" in tech.hard_failures


# ---------- candidate windows (§7.2) ----------

def test_short_shot_yields_one_window():
    wins = candidate_windows("a0", 0, 3 * US)
    assert len(wins) == 1
    assert wins[0].window_start_us == 0 and wins[0].window_end_us == 3 * US
    assert len(wins[0].keyframe_times_us) >= 2


def test_long_shot_yields_overlapping_windows_capped_at_max():
    wins = candidate_windows("a0", 0, 12 * US)
    assert len(wins) > 1
    assert all(w.duration_us <= 5 * US for w in wins)
    assert all(w.window_end_us <= 12 * US for w in wins)


def test_window_start_snaps_to_a_motion_valley():
    # A valley near the second window's raw start should pull the cut onto it.
    wins = candidate_windows("a0", 0, 12 * US, valleys_us=[int(1.4 * US)])
    starts = [w.window_start_us for w in wins]
    assert any(abs(s - int(1.4 * US)) < 100 for s in starts)


def test_tiny_shot_is_dropped():
    assert candidate_windows("a0", 0, US // 2) == []


def test_uniform_shots_partition_the_duration():
    spans = uniform_shots(10 * US, 4 * US)
    assert spans[0] == (0, 4 * US)
    assert spans[-1][1] == 10 * US


# ---------- sampling argv (§7.1/§16) ----------

def test_window_frames_command_is_pure_argv():
    cmd = window_frames_command(__import__("pathlib").Path("/x/a.mov"),
                                0, 3 * US, width=256, height=144, fps=8)
    joined = " ".join(cmd)
    assert "-noautorotate" in cmd            # geometry stays stable
    assert "scale=256:144,format=gray,fps=8" in joined
    assert cmd[-1] == "-"                     # raw frames to stdout
