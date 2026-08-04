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
    video_labels: list[str] = []      # video segments to concat (clips + outro)
    clip_audio_indexes: list[int] = []

    idx = 0
    for clip in graph.clips:
        # Input-level trim (fast seek) for each segment.
        inputs += ["-ss", f"{clip.source_start_s:.3f}", "-t", f"{clip.duration_s:.3f}",
                   "-i", str(clip.asset_path)]
        vlabel = f"v{idx}"
        # Subject reframe: shift the crop window horizontally by crop_x_norm.
        k = max(-1.0, min(1.0, clip.crop_x_norm))
        crop_x = f"(in_w-{cw})/2*(1+{k:.3f})" if abs(k) > 1e-3 else f"(in_w-{cw})/2"
        vchain = (
            f"[{idx}:v]scale={cw}:{ch}:force_original_aspect_ratio=increase,"
            f"crop={cw}:{ch}:{crop_x}:(in_h-{ch})/2,setsar=1,fps={fps}"
        )
        if (style.contrast, style.brightness, style.saturation) != (1.0, 0.0, 1.0):
            vchain += (
                f",eq=contrast={style.contrast}:brightness={style.brightness}"
                f":saturation={style.saturation}"
            )
        vchain += f",format=yuv420p[{vlabel}]"
        filters.append(vchain)
        video_labels.append(f"[{vlabel}]")
        clip_audio_indexes.append(idx)
        idx += 1

    # Branded outro: a logo over a solid background (pack doc 18).
    outro_secs = 0.0
    if graph.outro is not None:
        outro_secs = graph.outro.duration_us / 1_000_000
        inputs += ["-f", "lavfi", "-t", f"{outro_secs:.3f}",
                   "-i", f"color=c={graph.outro.bg_color}:s={cw}x{ch}:r={fps}"]
        color_idx = idx
        idx += 1
        if graph.outro.logo_path is not None:
            inputs += ["-i", str(graph.outro.logo_path)]
            logo_idx = idx
            idx += 1
            filters.append(f"[{color_idx}:v]setsar=1[obg]")
            filters.append(f"[{logo_idx}:v]scale={int(cw * 0.55)}:-1[olg]")
            filters.append(
                "[obg][olg]overlay=(W-w)/2:(H-h)/2,fade=t=in:st=0:d=0.4,"
                "format=yuv420p,setsar=1[voutro]")
        else:
            filters.append(f"[{color_idx}:v]format=yuv420p,setsar=1[voutro]")
        video_labels.append("[voutro]")

    # Video: concat all segments (video only), then burn captions.
    nvid = len(video_labels)
    filters.append(f"{''.join(video_labels)}concat=n={nvid}:v=1:a=0[vc]")
    if ass_path is not None and graph.captions:
        escaped = str(ass_path).replace("\\", "\\\\").replace(":", "\\:").replace("'", "\\'")
        filters.append(f"[vc]ass='{escaped}'[vout]")
    else:
        filters.append("[vc]null[vout]")

    total_s = graph.clips_total_us / 1_000_000 + outro_secs

    # Audio: a music bed (montage) replaces clip audio; otherwise concat clip audio.
    if graph.music_path is not None:
        inputs += ["-i", str(graph.music_path)]
        music_idx = idx
        idx += 1
        fade_start = max(0.0, total_s - 0.8)
        filters.append(
            f"[{music_idx}:a]aformat=sample_rates=48000:channel_layouts=stereo,"
            f"atrim=0:{total_s:.3f},afade=t=out:st={fade_start:.3f}:d=0.8,"
            f"apad=whole_dur={total_s:.3f},"
            f"loudnorm=I=-14:TP=-1.0:LRA=11[aout]")
    else:
        # Silence source for clips without audio and for the outro tail.
        need_silence = any(not c.has_audio for c in graph.clips) or graph.outro is not None
        silence_idx: int | None = None
        if need_silence:
            inputs += ["-f", "lavfi", "-t", f"{total_s:.3f}",
                       "-i", "anullsrc=r=48000:cl=stereo"]
            silence_idx = idx
            idx += 1
        audio_labels: list[str] = []
        for ci, clip in enumerate(graph.clips):
            alabel = f"a{ci}"
            src = f"[{clip_audio_indexes[ci]}:a]" if clip.has_audio else f"[{silence_idx}:a]"
            filters.append(
                f"{src}aformat=sample_rates=48000:channel_layouts=stereo,"
                f"atrim=0:{clip.duration_s:.3f},asetpts=PTS-STARTPTS[{alabel}]")
            audio_labels.append(f"[{alabel}]")
        if graph.outro is not None:
            filters.append(
                f"[{silence_idx}:a]atrim=0:{outro_secs:.3f},asetpts=PTS-STARTPTS[aoutro]")
            audio_labels.append("[aoutro]")
        na = len(audio_labels)
        filters.append(f"{''.join(audio_labels)}concat=n={na}:v=0:a=1[ac]")
        norm = "loudnorm=I=-14:TP=-1.0:LRA=11" if style.loudnorm else "anull"
        filters.append(f"[ac]{norm}[aout]")

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
