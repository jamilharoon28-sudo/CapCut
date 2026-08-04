"""The honest 'what Coach did vs skipped' summary written after a render."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from capcut_coach.autocreate import _write_pipeline_summary


@dataclass
class _R:
    detail: str = "ok"


def _summary(tmp_path: Path, **kw) -> dict:
    defaults = dict(results=[_R()], smart=True, cv2_ok=True, visual_used=True,
                    whisper_ok=False, voice_led=False, music=None, music_auto=False,
                    captions_requested=False, logo=None)
    defaults.update(kw)
    _write_pipeline_summary(tmp_path, **defaults)
    data = json.loads((tmp_path / "summary.json").read_text("utf-8"))
    return {f["key"]: f for f in data["features"]}


def test_plain_montage_reports_each_skip_with_a_fix(tmp_path: Path):
    feats = _summary(tmp_path, cv2_ok=False, visual_used=False)
    assert feats["music"]["applied"] is False and "never rips" in feats["music"]["detail"]
    assert feats["smart_framing"]["applied"] is False and "OpenCV" in feats["smart_framing"]["detail"]
    assert feats["captions"]["applied"] is False


def test_dropped_captions_point_at_ffmpeg(tmp_path: Path):
    feats = _summary(tmp_path, captions_requested=True,
                     results=[_R(detail="Captions couldn't be burned in (your FFmpeg lacks subtitle support).")])
    assert feats["captions"]["applied"] is False
    assert "brew reinstall ffmpeg" in feats["captions"]["detail"]


def test_full_features_all_applied(tmp_path: Path):
    feats = _summary(tmp_path, voice_led=True, music=Path("/m.mp3"), music_auto=True,
                     captions_requested=True, logo=Path("/l.png"))
    assert feats["edit_style"]["applied"] and feats["music"]["applied"]
    assert feats["captions"]["applied"] and feats["outro"]["applied"]
