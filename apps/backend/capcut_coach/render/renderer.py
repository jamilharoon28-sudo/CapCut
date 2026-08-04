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

import re
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

# Lines that carry FFmpeg's actual reason for failing (as opposed to the echoed
# filter graph). We surface these so a failure is diagnosable, not a wall of graph.
_ERROR_SIGNALS = re.compile(
    r"(error|invalid|unable|failed|no such|matches no streams|does not|cannot|"
    r"not found|conversion failed|permission denied|moov atom|decoder)", re.IGNORECASE)


def _compress(line: str, limit: int = 220) -> str:
    """Collapse a mega-line (FFmpeg embeds the whole filter graph in some errors)
    to its readable head and tail so the actual message survives."""
    if len(line) <= limit:
        return line
    head, tail = limit * 2 // 3, limit // 3
    return f"{line[:head]} …[graph elided]… {line[-tail:]}"


def _summarise_error(stderr: str) -> str:
    """Pull the meaningful error lines out of FFmpeg stderr for the user/logs."""
    lines = [ln.strip() for ln in stderr.splitlines() if ln.strip()]
    signal = [ln for ln in lines if _ERROR_SIGNALS.search(ln)]
    # Prefer the specific error lines; fall back to the final lines of output.
    chosen = signal[-6:] if signal else lines[-6:]
    text = "\n".join(_compress(ln) for ln in chosen)
    return text[-900:]

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
    notes: str = ""


def _resolve_ffmpeg(ffmpeg: str | None) -> str:
    from ..toolpaths import ffmpeg_path

    found = ffmpeg or ffmpeg_path()
    if not found:
        raise RenderUnavailable("ffmpeg not found (install with: brew install ffmpeg)")
    return found


def _transpose_chain(rotation: int) -> str:
    """FFmpeg transpose steps to bake in a clockwise display rotation (trailing ',')."""
    r = int(rotation) % 360
    if r == 90:
        return "transpose=1,"
    if r == 270:
        return "transpose=2,"
    if r == 180:
        return "transpose=1,transpose=1,"
    return ""


def _esc_filter_path(p: str) -> str:
    """Escape a filesystem path for use inside an FFmpeg filter option."""
    return p.replace("\\", "\\\\").replace(":", "\\:").replace("'", "\\'")


def _drawtext_chain(draw_captions: list[tuple[str, float, float]], cw: int, ch: int,
                    style) -> str:
    """A comma-joined drawtext chain that burns captions using freetype (no libass).

    Each caption reads from its own textfile (so arbitrary text needs no escaping)
    and is shown only during its time window. A font file may be supplied via
    COACH_CAPTION_FONT; otherwise a common macOS system font is used.
    """
    import os

    font = os.environ.get("COACH_CAPTION_FONT", "/System/Library/Fonts/Helvetica.ttc")
    fontsize = max(30, ch // 22)
    parts = []
    for tf, s, e in draw_captions:
        parts.append(
            f"drawtext=fontfile='{_esc_filter_path(font)}':textfile='{_esc_filter_path(tf)}'"
            f":fontcolor=white:fontsize={fontsize}:borderw=3:bordercolor=black@0.85"
            f":box=1:boxcolor=black@0.35:boxborderw={fontsize // 4}:line_spacing=6"
            f":x=(w-text_w)/2:y=h*0.74:enable='between(t,{s:.3f},{e:.3f})'")
    return ",".join(parts)


def build_command(
    graph: RenderGraph,
    output_path: Path,
    *,
    ass_path: Path | None,
    draw_captions: list[tuple[str, float, float]] | None = None,
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
        # Input-level trim (fast seek) for each segment. ``-noautorotate`` makes
        # rotation deterministic across FFmpeg versions: we bake in the display
        # rotation ourselves (below) so phone clips with a rotate flag come out
        # upright instead of sideways or double-rotated.
        inputs += ["-noautorotate",
                   "-ss", f"{clip.source_start_s:.3f}", "-t", f"{clip.duration_s:.3f}",
                   "-i", str(clip.asset_path)]
        vlabel = f"v{idx}"
        # Subject reframe: shift the crop window horizontally by crop_x_norm.
        k = max(-1.0, min(1.0, clip.crop_x_norm))
        crop_x = f"(in_w-{cw})/2*(1+{k:.3f})" if abs(k) > 1e-3 else f"(in_w-{cw})/2"
        # Bake in display rotation first so scale/crop see upright frames.
        rot = _transpose_chain(clip.rotation)
        vchain = (
            f"[{idx}:v]{rot}scale={cw}:{ch}:force_original_aspect_ratio=increase,"
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
        escaped = _esc_filter_path(str(ass_path))
        filters.append(f"[vc]ass='{escaped}'[vout]")
    elif draw_captions:
        filters.append(f"[vc]{_drawtext_chain(draw_captions, cw, ch, style)}[vout]")
    else:
        filters.append("[vc]null[vout]")

    total_s = graph.clips_total_us / 1_000_000 + outro_secs

    # Audio: music bed (montage), music ducked under voice (hybrid), or clip audio.
    fade_start = max(0.0, total_s - 0.8)
    if graph.music_path is not None and graph.duck_music and any(c.has_audio for c in graph.clips):
        # Hybrid: keep the spoken voice from the clips; duck the music beneath it
        # with a sidechain compressor keyed by the voice, then mix (dialogue leads).
        need_silence = any(not c.has_audio for c in graph.clips) or graph.outro is not None
        silence_idx: int | None = None
        if need_silence:
            inputs += ["-f", "lavfi", "-t", f"{total_s:.3f}",
                       "-i", "anullsrc=r=48000:cl=stereo"]
            silence_idx = idx
            idx += 1
        voice_parts: list[str] = []
        for ci, clip in enumerate(graph.clips):
            src = f"[{clip_audio_indexes[ci]}:a]" if clip.has_audio else f"[{silence_idx}:a]"
            filters.append(
                f"{src}aformat=sample_rates=48000:channel_layouts=stereo,"
                f"atrim=0:{clip.duration_s:.3f},asetpts=PTS-STARTPTS[dv{ci}]")
            voice_parts.append(f"[dv{ci}]")
        if graph.outro is not None:
            filters.append(
                f"[{silence_idx}:a]atrim=0:{outro_secs:.3f},asetpts=PTS-STARTPTS[dvo]")
            voice_parts.append("[dvo]")
        filters.append(f"{''.join(voice_parts)}concat=n={len(voice_parts)}:v=0:a=1[voice]")
        filters.append("[voice]asplit=2[voice_mix][voice_key]")
        inputs += ["-i", str(graph.music_path)]
        music_idx = idx
        idx += 1
        filters.append(
            f"[{music_idx}:a]aformat=sample_rates=48000:channel_layouts=stereo,"
            f"atrim=0:{total_s:.3f},apad=whole_dur={total_s:.3f},"
            f"afade=t=out:st={fade_start:.3f}:d=0.8,volume=0.6[musicbed]")
        # Sidechain: compress the music (main) using the voice as the key.
        filters.append(
            "[musicbed][voice_key]sidechaincompress=threshold=0.03:ratio=8:"
            "attack=15:release=350[ducked]")
        filters.append(
            "[voice_mix][ducked]amix=inputs=2:duration=first:dropout_transition=0,"
            "loudnorm=I=-14:TP=-1.0:LRA=11[aout]")
    elif graph.music_path is not None:
        inputs += ["-i", str(graph.music_path)]
        music_idx = idx
        idx += 1
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
        ffmpeg, "-y", "-hide_banner",
        # Regenerate presentation timestamps: odd/variable-frame-rate containers
        # (some phone .mov, .mts, .webm) can carry timestamps that break concat.
        "-fflags", "+genpts",
        *inputs,
        "-filter_complex", filter_complex,
        "-map", "[vout]", "-map", "[aout]",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart",
        "-max_muxing_queue_size", "1024",
        str(output_path),
    ]


def _run_once(graph: RenderGraph, output_path: Path, ff: str, timeout: float,
              caption_mode: str | None) -> tuple[int, str, list[str]]:
    """Build + execute one render attempt with a chosen caption renderer.

    ``caption_mode``: "ass" (libass), "drawtext" (freetype — works without libass),
    or None (no burned captions). Caption text/ASS files live in a temp dir that is
    cleaned up after the attempt.
    """
    ass_path: Path | None = None
    draw: list[tuple[str, float, float]] | None = None
    tmpdir: tempfile.TemporaryDirectory | None = None
    want_caps = bool(graph.captions) and graph.style.captions and caption_mode

    if want_caps:
        tmpdir = tempfile.TemporaryDirectory()
        base = Path(tmpdir.name)
        if caption_mode == "ass":
            ass_path = base / "captions.ass"
            ass_path.write_text(build_ass(graph.captions, graph.canvas, graph.style), "utf-8")
        elif caption_mode == "drawtext":
            draw = []
            for i, cap in enumerate(graph.captions):
                tf = base / f"cap_{i}.txt"
                tf.write_text(cap.text, "utf-8")
                s = cap.start_us / 1_000_000
                draw.append((str(tf), s, s + cap.duration_us / 1_000_000))

    cmd = build_command(graph, output_path, ass_path=ass_path, draw_captions=draw, ffmpeg=ff)
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, check=False)
    finally:
        if tmpdir is not None:
            tmpdir.cleanup()
    return proc.returncode, proc.stderr, cmd


def _attempts(graph: RenderGraph):
    """Ordered (graph, caption_mode, note) attempts, most-featureful first.

    Two independent failure axes: caption burn-in (libass may be missing → try
    drawtext/freetype next) and clip audio (an unmappable stream → silence). We
    prefer keeping captions, then audio; a finished video beats a perfect one.
    """
    import copy

    has_caps = bool(graph.captions) and graph.style.captions
    has_audio = graph.music_path is None and any(c.has_audio for c in graph.clips)

    silent = copy.deepcopy(graph)
    for c in silent.clips:
        c.has_audio = False

    if has_caps:
        yield graph, "ass", ""
        yield graph, "drawtext", "Captions rendered as plain text (your FFmpeg lacks libass)."
        if has_audio:
            yield silent, "ass", "Some clips had unreadable audio; rendered with silence."
            yield silent, "drawtext", ("Captions as plain text and some audio silenced "
                                       "(FFmpeg lacks libass; unreadable audio).")
        yield graph, None, "Captions couldn't be added."
        if has_audio:
            yield silent, None, "Captions dropped and some audio silenced."
    else:
        yield graph, None, ""
        if has_audio:
            yield silent, None, "Some clips had unreadable audio; rendered with silence."


def render_graph(
    graph: RenderGraph,
    output_path: Path,
    *,
    ffmpeg: str | None = None,
    timeout: float = 1800.0,
) -> RenderResult:
    """Render a graph to an MP4 with a graceful-degradation cascade.

    Tries full fidelity first, then — only for what's actually broken — a libass-
    free caption renderer (drawtext), then silence, then no captions. A finished
    video is produced whenever any variant can render; what changed is reported in
    ``notes`` and never hidden. Only the last error surfaces if every variant fails.
    """
    ff = _resolve_ffmpeg(ffmpeg)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    last_rc, last_stderr, last_cmd = 1, "", [ff]
    for variant, caption_mode, note in _attempts(graph):
        rc, stderr, cmd = _run_once(variant, output_path, ff, timeout, caption_mode)
        if rc == 0:
            return RenderResult(output_path, cmd, variant.total_us, rc, notes=note)
        last_rc, last_stderr, last_cmd = rc, stderr, cmd

    return RenderResult(output_path, last_cmd, graph.total_us, last_rc,
                        stderr_tail=_summarise_error(last_stderr))
