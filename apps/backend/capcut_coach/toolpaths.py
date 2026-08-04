"""Locate external binaries robustly, including for a GUI .app.

A macOS app launched from the Dock does NOT inherit the user's shell PATH, so
Homebrew's ffmpeg (/opt/homebrew/bin) is invisible to ``shutil.which``. This
resolver also checks the common Homebrew / MacPorts / local locations and honours
explicit COACH_FFMPEG / COACH_FFPROBE overrides written by the app build.
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path

_EXTRA_DIRS = (
    "/opt/homebrew/bin",   # Apple-silicon Homebrew
    "/usr/local/bin",      # Intel Homebrew / manual installs
    "/opt/local/bin",      # MacPorts
)


def resolve(binary: str, env_override: str | None = None) -> str | None:
    """Return an absolute path to ``binary`` or None."""
    if env_override:
        val = os.environ.get(env_override)
        if val and Path(val).exists():
            return val
    found = shutil.which(binary)
    if found:
        return found
    for d in _EXTRA_DIRS:
        candidate = Path(d) / binary
        if candidate.exists():
            return str(candidate)
    return None


def ffmpeg_path() -> str | None:
    return resolve("ffmpeg", env_override="COACH_FFMPEG")


def ffprobe_path() -> str | None:
    return resolve("ffprobe", env_override="COACH_FFPROBE")
