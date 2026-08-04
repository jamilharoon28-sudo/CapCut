"""Compile a RenderGraph into a deterministic FFmpeg command and run it.

Zero-additional-cost renderer (pack doc 15 §4): FFmpeg with libx264 + aac, ASS
captions via libass, loudnorm audio, scale/crop to the vertical canvas. The
command is built as an argument array (never a shell string). ``build_command``
is pure and unit-tested; ``render_graph`` executes it.

Robust-by-design (doc 15 §10): a clip without an audio stream gets a silent
track so concatenation never fails; if a fancy step is unavailable the clean cut
still renders.
"""

from __future__ import annotations

import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

from .ass import build_ass
from .graph import RenderGraph


class RenderUnavailable(RuntimeError):
    pass


@dataclass
class RenderResult:
    output_path: Path
    command: list[str]
    duration_us: int
    returncode: int
    stderr_tail: str = ""


def _resolve_ffmpeg(ffmpeg: str | None) -> str:
    from ..toolpaths import ffmpeg_path

    found = ffmpeg or ffmpeg_path()
    if not found:
        raise RenderUnavailable("ffmpeg not found (install with: brew install ffmpeg)")
    return found


def build_command(
    graph: RenderGraph,
    output_path: Path,
    *,
    ass_path: Path | None,
    ffmpeg: str = "ffmpeg",
    fps: int = 30,
) -> list[str]:
    """Build the FFmpeg argv for a graph. Pure — does not run anything."""
    if not graph.clips:
        raise ValueError("cannot render an empty graph")
    cw, ch = graph.canvas.width, graph.canvas.height
    style = graph.style

    inputs: list[str] = []
    filters: list[str] = []
    concat_labels: list[str] = []
    audio_input_indexes: list[int] = []

    idx = 0
    for clip in graph.clips:
        # Input-level trim (fast seek) for each segment.
        inputs += ["-ss", f"{clip.source_start_s:.3f}", "-t", f"{clip.duration_s:.3f}",
                   "-i", str(clip.asset_path)]
        vlabel = f"v{idx}"
        vchain = (
            f"[{idx}:v]scale={cw}:{ch}:force_original_aspect_ratio=increase,"
            f"crop={cw}:{ch},setsar=1,fps={fps}"
        )
        if (style.contrast, style.brightness, style.saturation) != (1.0, 0.0, 1.0):
            vchain += (
                f",eq=contrast={style.contrast}:brightness={style.brightness}"
                f":saturation={style.saturation}"
            )
        vchain += f"[{vlabel}]"
        filters.append(vchain)
        concat_labels.append(f"[{vlabel}]")
        audio_input_indexes.append(idx)
        idx += 1

    # Provide silence for clips that have no audio, so concat a=1 stays valid.
    total_s = graph.total_us / 1_000_000
    silence_idx: int | None = None
    if any(not c.has_audio for c in graph.clips):
        inputs += ["-f", "lavfi", "-t", f"{total_s:.3f}",
                   "-i", "anullsrc=r=48000:cl=stereo"]
        silence_idx = idx
        idx += 1

    audio_labels: list[str] = []
    for k, clip in enumerate(graph.clips):
        alabel = f"a{k}"
        if clip.has_audio:
            src = f"[{audio_input_indexes[k]}:a]"
        else:
            # Take a slice of the shared silence input for this clip's duration.
            src = f"[{silence_idx}:a]"
        filters.append(
            f"{src}aformat=sample_rates=48000:channel_layouts=stereo,"
            f"atrim=0:{clip.duration_s:.3f},asetpts=PTS-STARTPTS[{alabel}]"
        )
        audio_labels.append(f"[{alabel}]")

    n = len(graph.clips)
    interleaved = "".join(f"{concat_labels[i]}{audio_labels[i]}" for i in range(n))
    filters.append(f"{interleaved}concat=n={n}:v=1:a=1[vc][ac]")

    # Captions (burned via ASS) then audio loudness normalisation.
    if ass_path is not None and graph.captions:
        escaped = str(ass_path).replace("\\", "\\\\").replace(":", "\\:").replace("'", "\\'")
        filters.append(f"[vc]ass='{escaped}'[vout]")
    else:
        filters.append("[vc]null[vout]")
    if style.loudnorm:
        filters.append("[ac]loudnorm=I=-16:TP=-1.5:LRA=11[aout]")
    else:
        filters.append("[ac]anull[aout]")

    filter_complex = ";".join(filters)
    return [
        ffmpeg, "-y", "-hide_banner", *inputs,
        "-filter_complex", filter_complex,
        "-map", "[vout]", "-map", "[aout]",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart",
        str(output_path),
    ]


def render_graph(
    graph: RenderGraph,
    output_path: Path,
    *,
    ffmpeg: str | None = None,
    timeout: float = 1800.0,
) -> RenderResult:
    """Render a graph to an MP4. Writes ASS captions to a temp file if present."""
    ff = _resolve_ffmpeg(ffmpeg)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    ass_path: Path | None = None
    tmpdir: tempfile.TemporaryDirectory | None = None
    if graph.captions and graph.style.captions:
        tmpdir = tempfile.TemporaryDirectory()
        ass_path = Path(tmpdir.name) / "captions.ass"
        ass_path.write_text(build_ass(graph.captions, graph.canvas, graph.style), "utf-8")

    cmd = build_command(graph, output_path, ass_path=ass_path, ffmpeg=ff)
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, check=False)
    finally:
        if tmpdir is not None:
            tmpdir.cleanup()
    return RenderResult(
        output_path=output_path,
        command=cmd,
        duration_us=graph.total_us,
        returncode=proc.returncode,
        stderr_tail=proc.stderr.strip()[-500:] if proc.returncode else "",
    )
