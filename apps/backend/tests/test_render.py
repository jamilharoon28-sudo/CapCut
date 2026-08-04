"""Automation-first render engine: command construction (pure) + real smoke test."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from capcut_coach.render.candidates import build_candidates
from capcut_coach.render.graph import BOLD, CLEAN, ENHANCED, graph_from_edit_plan
from capcut_coach.render.renderer import build_command
from capcut_coach.schemas.edit_plan import Caption, EditPlan, Segment


def _plan() -> EditPlan:
    segs = [
        Segment(id="s1", asset_id="a1", source_start_us=0, source_duration_us=3_000_000,
                timeline_start_us=0, timeline_duration_us=3_000_000, role="hook", confidence=0.9),
        Segment(id="s2", asset_id="a2", source_start_us=500_000, source_duration_us=2_000_000,
                timeline_start_us=3_000_000, timeline_duration_us=2_000_000, confidence=0.6),
    ]
    caps = [Caption(id="c1", text="Hello", start_us=0, duration_us=3_000_000)]
    return EditPlan(id="e1", project_id="p1", segments=segs, captions=caps)


def test_command_is_argv_and_scales_to_canvas(tmp_path):
    paths = {"a1": tmp_path / "a1.mp4", "a2": tmp_path / "a2.mp4"}
    graph = graph_from_edit_plan(_plan(), paths, style=CLEAN)
    cmd = build_command(graph, tmp_path / "out.mp4", ass_path=None, ffmpeg="ffmpeg")
    joined = " ".join(cmd)
    # No shell string; scales+crops to vertical; concatenates both segments.
    assert cmd[0] == "ffmpeg"
    assert "scale=1080:1920:force_original_aspect_ratio=increase" in joined
    assert "crop=1080:1920" in joined
    assert "concat=n=2:v=1:a=1" in joined
    assert "libx264" in cmd and "aac" in cmd


def test_missing_audio_gets_silence(tmp_path):
    paths = {"a1": tmp_path / "a1.mp4", "a2": tmp_path / "a2.mp4"}
    graph = graph_from_edit_plan(_plan(), paths, style=CLEAN,
                                 asset_has_audio={"a1": True, "a2": False})
    cmd = build_command(graph, tmp_path / "o.mp4", ass_path=None)
    assert "anullsrc=r=48000:cl=stereo" in " ".join(cmd)


def test_enhanced_adds_eq_and_captions(tmp_path):
    paths = {"a1": tmp_path / "a1.mp4", "a2": tmp_path / "a2.mp4"}
    graph = graph_from_edit_plan(_plan(), paths, style=ENHANCED)
    cmd = build_command(graph, tmp_path / "o.mp4", ass_path=tmp_path / "c.ass")
    joined = " ".join(cmd)
    assert "eq=contrast=1.06" in joined
    assert "ass=" in joined  # captions burned when style has captions


def test_bold_reorders_hook_to_front(tmp_path):
    paths = {"a1": tmp_path / "a1.mp4", "a2": tmp_path / "a2.mp4"}
    cands = build_candidates(_plan(), paths)
    bold = next(c for c in cands if c.name == "bold")
    # s1 has the higher confidence (0.9) so it leads; timeline starts at 0.
    assert bold.graph.clips[0].provenance["segment_id"] == "s1"
    assert bold.graph.clips[0].timeline_start_us == 0
    assert bold.dimensions["reordered_hook"] is True


def test_empty_graph_refused(tmp_path):
    graph = graph_from_edit_plan(EditPlan(id="e", project_id="p", segments=[]), {}, style=CLEAN)
    with pytest.raises(ValueError):
        build_command(graph, tmp_path / "o.mp4", ass_path=None)


@pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="ffmpeg not installed")
def test_autocreate_from_zip_with_nested_folder(tmp_path):
    """A .zip of clips (macOS-style: top folder + __MACOSX) renders 3 candidates."""
    import subprocess
    import zipfile

    from capcut_coach.autocreate import autocreate

    ff = shutil.which("ffmpeg")
    src = tmp_path / "raw videos"
    src.mkdir()
    for i in range(3):
        subprocess.run(
            [ff, "-y", "-hide_banner", "-loglevel", "error",
             "-f", "lavfi", "-i", "testsrc=size=640x360:rate=30:duration=3",
             "-f", "lavfi", "-i", "sine=frequency=440:duration=3",
             "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p",
             "-c:a", "aac", "-shortest", str(src / f"clip{i}.mp4")], check=True)
    zip_path = tmp_path / "raw videos.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        for p in src.iterdir():
            zf.write(p, f"raw videos/{p.name}")
        zf.writestr("__MACOSX/._junk", "x")  # AppleDouble noise must be ignored

    results = autocreate(zip_path, tmp_path / "out", target_seconds=9, max_clips=3)
    assert {r.candidate_name for r in results} == {"clean", "enhanced", "bold"}
    assert all(r.ok for r in results)


@pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="ffmpeg not installed")
def test_real_render_smoke(tmp_path):
    """End-to-end: synthesize two clips, render Clean, assert a playable file."""
    import subprocess

    ff = shutil.which("ffmpeg")
    clips = {}
    for name in ("a1", "a2"):
        p = tmp_path / f"{name}.mp4"
        subprocess.run(
            [ff, "-y", "-hide_banner", "-loglevel", "error",
             "-f", "lavfi", "-i", "testsrc=size=640x360:rate=30:duration=3",
             "-f", "lavfi", "-i", "sine=frequency=440:duration=3",
             "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p",
             "-c:a", "aac", "-shortest", str(p)], check=True)
        clips[name] = p
    from capcut_coach.render.renderer import render_graph

    graph = graph_from_edit_plan(_plan(), clips, style=BOLD)
    out = tmp_path / "final.mp4"
    result = render_graph(graph, out)
    assert result.returncode == 0, result.stderr_tail
    assert out.exists() and out.stat().st_size > 1000
