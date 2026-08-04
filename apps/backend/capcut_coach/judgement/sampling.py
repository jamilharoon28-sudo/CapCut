"""Proxy and frame sampling for window analysis (add-on §7.1, Phase 1).

Analysis runs on cheap proxies/frames, never full-resolution source (add-on §16).
The command builders here are pure argv (unit-testable); ``read_gray_frames``
executes FFmpeg on the Mac to decode a window into a stack of grayscale frames
for ``technical.analyse_window``. Sources are only ever read, never modified.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import numpy as np

SECOND_US = 1_000_000


def proxy_command(src: Path, dst: Path, *, ffmpeg: str = "ffmpeg", height: int = 540) -> list[str]:
    """Build an argv to make a small analysis proxy (keeps aspect; source timecode)."""
    return [
        ffmpeg, "-y", "-hide_banner", "-loglevel", "error", "-noautorotate",
        "-i", str(src),
        "-vf", f"scale=-2:{height}", "-c:v", "libx264", "-preset", "veryfast",
        "-crf", "28", "-an", "-movflags", "+faststart", str(dst),
    ]


def window_frames_command(
    src: Path, start_us: int, dur_us: int, *,
    ffmpeg: str = "ffmpeg", width: int = 256, height: int = 144, fps: int = 8,
) -> list[str]:
    """Build an argv that decodes a window to raw grayscale frames on stdout.

    ``-noautorotate`` keeps geometry stable; the caller reshapes the byte stream
    into ``height x width`` frames. Downscaled + low-fps so analysis stays cheap.
    """
    return [
        ffmpeg, "-hide_banner", "-loglevel", "error", "-noautorotate",
        "-ss", f"{start_us / SECOND_US:.3f}", "-t", f"{dur_us / SECOND_US:.3f}",
        "-i", str(src),
        "-vf", f"scale={width}:{height},format=gray,fps={fps}",
        "-f", "rawvideo", "-pix_fmt", "gray", "-",
    ]


def read_gray_frames(
    src: Path, start_us: int, dur_us: int, *,
    ffmpeg: str = "ffmpeg", width: int = 256, height: int = 144, fps: int = 8,
    timeout: float = 60.0,
) -> list[np.ndarray]:
    """Decode a window into grayscale frames (Mac step — needs FFmpeg + media)."""
    cmd = window_frames_command(src, start_us, dur_us, ffmpeg=ffmpeg,
                                width=width, height=height, fps=fps)
    proc = subprocess.run(cmd, capture_output=True, timeout=timeout, check=False)
    if proc.returncode != 0 or not proc.stdout:
        return []
    frame_bytes = width * height
    n = len(proc.stdout) // frame_bytes
    if n == 0:
        return []
    buf = np.frombuffer(proc.stdout[: n * frame_bytes], dtype=np.uint8)
    return [buf[i * frame_bytes:(i + 1) * frame_bytes].reshape(height, width)
            for i in range(n)]
