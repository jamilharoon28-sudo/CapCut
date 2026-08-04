"""Dialogue ducking (hybrid) + EBU R128 loudness QC (pack docs 18, 20)."""

from __future__ import annotations

from pathlib import Path

from capcut_coach.media.audioqc import LoudnessMeasure, loudness_findings
from capcut_coach.render.graph import ENHANCED, RenderClip, RenderGraph
from capcut_coach.render.renderer import build_command
from capcut_coach.schemas.edit_plan import Canvas


def _graph(duck: bool):
    clips = [RenderClip(asset_path=Path(f"/x/{i}.mp4"), source_start_us=0,
                        source_duration_us=2_000_000, timeline_start_us=i * 2_000_000,
                        has_audio=True) for i in range(2)]
    return RenderGraph(schema_version=1, canvas=Canvas(), clips=clips, style=ENHANCED,
                       music_path=Path("/m/track.mp3"), duck_music=duck)


def test_ducking_uses_sidechain_and_keeps_voice(tmp_path):
    joined = " ".join(build_command(_graph(True), tmp_path / "o.mp4", ass_path=None))
    assert "sidechaincompress" in joined     # music ducked under the voice
    assert "amix=inputs=2" in joined         # voice + ducked music mixed
    assert "loudnorm=I=-14" in joined


def test_no_ducking_when_flag_off(tmp_path):
    joined = " ".join(build_command(_graph(False), tmp_path / "o.mp4", ass_path=None))
    assert "sidechaincompress" not in joined  # plain music bed replaces clip audio


def test_loudness_findings_flags_out_of_band_and_clipping():
    assert loudness_findings(LoudnessMeasure(-14.0, -1.5)) == []          # in band
    codes = {f.code for f in loudness_findings(LoudnessMeasure(-9.0, -0.2))}
    assert "loudness" in codes and "true_peak" in codes
    assert loudness_findings(LoudnessMeasure(None, None)) == []           # unmeasured
