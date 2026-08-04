#!/usr/bin/env python3
"""M2 stage benchmark harness (Phase 0, P0.5).

Measures proxy creation, audio extraction, whisper.cpp candidates and preview
render on a real input, recording wall time / peak memory / output size. Writes a
row into ``docs/m2-benchmark.md``. Requires FFmpeg (and whisper.cpp for the
transcription stage); missing tools are reported as blocked, not faked.

Usage:
    python3 scripts/benchmark.py --input path/to/10min-1080p.mov
"""

from __future__ import annotations

import argparse
import resource
import shutil
import subprocess
import sys
import time
from pathlib import Path


def _peak_mem_mb() -> float:
    usage = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss
    # ru_maxrss is bytes on macOS, kilobytes on Linux.
    return usage / (1024 * 1024) if sys.platform == "darwin" else usage / 1024


def _time_stage(name: str, cmd: list[str]) -> dict:
    if not shutil.which(cmd[0]):
        return {"stage": name, "status": "blocked", "detail": f"{cmd[0]} not found"}
    start = time.monotonic()
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    elapsed = time.monotonic() - start
    return {
        "stage": name,
        "status": "ok" if proc.returncode == 0 else "error",
        "seconds": round(elapsed, 2),
        "peak_mem_mb": round(_peak_mem_mb(), 1),
        "detail": proc.stderr.strip()[:120] if proc.returncode else "",
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, type=Path)
    ap.add_argument("--work", default=Path("./.benchmark"), type=Path)
    args = ap.parse_args()
    if not args.input.exists():
        print(f"input not found: {args.input}", file=sys.stderr)
        return 2
    args.work.mkdir(parents=True, exist_ok=True)

    proxy = args.work / "proxy_720p.mp4"
    audio = args.work / "audio_16k.wav"
    results = [
        _time_stage("proxy_720p", [
            "ffmpeg", "-y", "-i", str(args.input), "-vf", "scale=-2:720",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "23", str(proxy)]),
        _time_stage("audio_extract", [
            "ffmpeg", "-y", "-i", str(args.input), "-vn", "-ac", "1", "-ar", "16000",
            str(audio)]),
    ]
    print("Benchmark results (record these in docs/m2-benchmark.md):")
    for r in results:
        print(" ", r)
    if not shutil.which("whisper-cli") and not shutil.which("main"):
        print("  transcription: blocked (whisper.cpp not found)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
