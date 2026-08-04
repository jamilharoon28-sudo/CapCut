"""FFmpeg / ffprobe subprocess wrappers (Phase 2).

All arguments are passed as argument *arrays* (never a shell string) so paths
with spaces and metacharacters are safe (CLAUDE.md; runbook §4). When the
binaries are absent (e.g. this Linux CI scaffold without FFmpeg), calls raise a
clear ``FFmpegUnavailable`` and the caller degrades gracefully rather than
crashing the service.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path


class FFmpegUnavailable(RuntimeError):
    pass


def _resolve(binary: str) -> str:
    found = shutil.which(binary)
    if not found:
        raise FFmpegUnavailable(f"{binary} not found on PATH")
    return found


def available() -> bool:
    return shutil.which("ffmpeg") is not None and shutil.which("ffprobe") is not None


@dataclass
class MediaInfo:
    duration_us: int
    width: int
    height: int
    fps_num: int
    fps_den: int
    has_audio: bool
    is_vfr: bool
    rotation: int
    codec: str


def probe(path: Path, *, timeout: float = 60.0) -> MediaInfo:
    """Run ffprobe and return normalised media info. Detects VFR/rotation/audio."""
    ffprobe = _resolve("ffprobe")
    cmd = [
        ffprobe, "-v", "error", "-print_format", "json",
        "-show_streams", "-show_format", str(path),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, check=False)
    if proc.returncode != 0:
        raise RuntimeError(f"ffprobe failed: {proc.stderr.strip()[:200]}")
    data = json.loads(proc.stdout or "{}")
    streams = data.get("streams", [])
    video = next((s for s in streams if s.get("codec_type") == "video"), None)
    has_audio = any(s.get("codec_type") == "audio" for s in streams)
    if video is None:
        raise RuntimeError("no video stream")

    duration_s = float(data.get("format", {}).get("duration", 0.0) or 0.0)
    fps_num, fps_den = _parse_rational(video.get("avg_frame_rate", "0/1"))
    r_num, r_den = _parse_rational(video.get("r_frame_rate", "0/1"))
    is_vfr = (fps_num, fps_den) != (r_num, r_den) and fps_num != 0 and r_num != 0
    rotation = _rotation(video)
    return MediaInfo(
        duration_us=int(round(duration_s * 1_000_000)),
        width=int(video.get("width", 0)),
        height=int(video.get("height", 0)),
        fps_num=fps_num or 30,
        fps_den=fps_den or 1,
        has_audio=has_audio,
        is_vfr=is_vfr,
        rotation=rotation,
        codec=str(video.get("codec_name", "")),
    )


def _parse_rational(text: str) -> tuple[int, int]:
    try:
        num, den = text.split("/")
        return int(num), int(den) if int(den) != 0 else 1
    except (ValueError, ZeroDivisionError):
        return 0, 1


def _rotation(video: dict) -> int:
    tags = video.get("tags", {})
    if "rotate" in tags:
        try:
            return int(tags["rotate"]) % 360
        except ValueError:
            pass
    for sd in video.get("side_data_list", []) or []:
        if "rotation" in sd:
            try:
                return int(sd["rotation"]) % 360
            except (ValueError, TypeError):
                pass
    return 0


def extract_audio_16k_mono(src: Path, dst: Path, *, timeout: float = 600.0) -> Path:
    """Extract mono 16 kHz PCM WAV for transcription. Overwrites dst atomically."""
    ffmpeg = _resolve("ffmpeg")
    tmp = dst.with_suffix(".tmp.wav")
    cmd = [
        ffmpeg, "-y", "-i", str(src), "-vn", "-ac", "1", "-ar", "16000",
        "-f", "wav", str(tmp),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, check=False)
    if proc.returncode != 0:
        raise RuntimeError(f"audio extract failed: {proc.stderr.strip()[:200]}")
    tmp.replace(dst)
    return dst


def make_proxy_720p(src: Path, dst: Path, *, use_videotoolbox: bool = True,
                    timeout: float = 1800.0) -> Path:
    """Create a 720p proxy. Prefers VideoToolbox on macOS; falls back to x264."""
    ffmpeg = _resolve("ffmpeg")
    tmp = dst.with_suffix(".tmp.mp4")
    scale = ["-vf", "scale=-2:720"]
    if use_videotoolbox and shutil.which("ffmpeg"):
        encoder = ["-c:v", "h264_videotoolbox", "-b:v", "3M"]
    else:
        encoder = ["-c:v", "libx264", "-preset", "veryfast", "-crf", "23"]
    cmd = [ffmpeg, "-y", "-i", str(src), *scale, *encoder, "-c:a", "aac", str(tmp)]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, check=False)
    if proc.returncode != 0:
        # Retry once with the portable software encoder before giving up.
        cmd_sw = [ffmpeg, "-y", "-i", str(src), *scale,
                  "-c:v", "libx264", "-preset", "veryfast", "-crf", "23",
                  "-c:a", "aac", str(tmp)]
        proc = subprocess.run(cmd_sw, capture_output=True, text=True, timeout=timeout, check=False)
        if proc.returncode != 0:
            raise RuntimeError(f"proxy failed: {proc.stderr.strip()[:200]}")
    tmp.replace(dst)
    return dst
