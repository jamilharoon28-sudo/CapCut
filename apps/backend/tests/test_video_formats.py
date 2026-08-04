"""Broad video-format acceptance and rotation normalisation."""

from __future__ import annotations

from capcut_coach.autocreate import VIDEO_EXTS, _norm_rotation


def test_common_containers_are_recognised():
    expected = {".mov", ".mp4", ".m4v", ".mkv", ".avi", ".webm", ".mts", ".m2ts",
                ".3gp", ".wmv", ".flv", ".mpg", ".mpeg", ".ts"}
    assert expected <= VIDEO_EXTS


def test_rotation_normalises_to_quadrants():
    assert _norm_rotation(90) == 90
    assert _norm_rotation(-90) == 270
    assert _norm_rotation(270) == 270
    assert _norm_rotation(-270) == 90
    assert _norm_rotation(180) == 180
    assert _norm_rotation(360) == 0
    assert _norm_rotation(0) == 0
    # Odd angles snap to the nearest quadrant.
    assert _norm_rotation(89.9) == 90
