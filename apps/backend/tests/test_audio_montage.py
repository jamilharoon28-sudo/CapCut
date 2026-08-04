"""Beat-synced montage: audio DNA phrase grid, montage plan, music/outro render."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from capcut_coach.analysis.audio import AudioDNA
from capcut_coach.autocreate import CatalogAsset
from capcut_coach.montage import build_music_montage
from capcut_coach.render.graph import ENHANCED, Outro, RenderClip, RenderGraph
from capcut_coach.render.renderer import build_command
from capcut_coach.schemas.edit_plan import Canvas


def test_phrase_cuts_snap_to_beats():
    beats = [round(0.5 * i, 3) for i in range(33)]  # 120 BPM over 16 s
    dna = AudioDNA(duration_s=16.0, tempo_bpm=120.0, beat_times_s=beats)
    cuts = dna.phrase_cuts_s(2.0, 16.0)  # 2s ≈ every 4th beat
    gaps = [round(cuts[i + 1] - cuts[i], 2) for i in range(len(cuts) - 1)]
    assert all(abs(g - 2.0) < 0.01 for g in gaps)


def test_phrase_cuts_fixed_grid_without_beats():
    dna = AudioDNA(duration_s=10.0, tempo_bpm=0.0, beat_times_s=[])
    cuts = dna.phrase_cuts_s(2.0, 10.0)
    assert cuts[0] == 0.0 and len(cuts) >= 5


def test_montage_rotates_clips_and_is_contiguous():
    catalog = [CatalogAsset(id=f"a{i}", path=Path(f"/x/{i}.mp4"),
                            duration_us=8_000_000, has_audio=True) for i in range(3)]
    beats = [round(0.5 * i, 3) for i in range(25)]
    dna = AudioDNA(duration_s=12.0, tempo_bpm=120.0, beat_times_s=beats)
    plan = build_music_montage(catalog, dna, project_id="p", target_us=12_000_000,
                               captions=["one", "two", "three", "four"])
    # No accidental adjacent duplicate shots.
    for a, b in zip(plan.segments, plan.segments[1:]):
        assert a.asset_id != b.asset_id
    # Contiguous timeline (each starts where the previous ended).
    cursor = 0
    for seg in plan.segments:
        assert seg.timeline_start_us == cursor
        cursor += seg.timeline_duration_us


def test_render_command_music_bed_and_outro(tmp_path):
    clips = [RenderClip(asset_path=tmp_path / f"{i}.mp4", source_start_us=0,
                        source_duration_us=2_000_000, timeline_start_us=i * 2_000_000)
             for i in range(2)]
    graph = RenderGraph(schema_version=1, canvas=Canvas(), clips=clips, style=ENHANCED,
                        music_path=tmp_path / "music.mp3",
                        outro=Outro(logo_path=tmp_path / "logo.png", duration_us=4_500_000))
    joined = " ".join(build_command(graph, tmp_path / "o.mp4", ass_path=None))
    # Music bed normalised to the campaign target and faded out.
    assert "loudnorm=I=-14" in joined and "afade=t=out" in joined
    # Branded outro: colour background + logo overlay, concatenated after the clips.
    assert "color=c=" in joined and "overlay=(W-w)/2:(H-h)/2" in joined
    assert "concat=n=3:v=1:a=0" in joined  # 2 clips + outro


@pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="ffmpeg not installed")
def test_analyse_audio_detects_tempo(tmp_path):
    from capcut_coach.analysis.audio import analyse_audio, librosa_available
    if not librosa_available():
        pytest.skip("librosa not installed")
    import numpy as np
    import soundfile as sf

    sr, bpm, dur = 22050, 120, 12
    click = np.zeros(int(sr * dur))
    for b in np.arange(0, dur, 60 / bpm):
        i = int(b * sr)
        click[i:i + int(0.02 * sr)] += np.sin(2 * np.pi * 1200 * np.arange(int(0.02 * sr)) / sr)
    wav = tmp_path / "click.wav"
    sf.write(str(wav), click * 0.8, sr)
    dna = analyse_audio(wav, shutil.which("ffmpeg"))
    assert dna is not None
    assert 108 <= dna.tempo_bpm <= 132  # detected near 120
    assert len(dna.beat_times_s) > 10
