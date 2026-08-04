"""EBU R128 loudness / true-peak QC on a rendered file (pack docs 18, 20).

Runs FFmpeg's ``ebur128`` filter on the final MP4 and reports integrated loudness
and true peak, then flags anything outside the social target band (~-14 LUFS,
true peak <= -1 dBTP). Local, deterministic; degrades to "unmeasured" when FFmpeg
is missing.
"""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

from ..qc import QcFinding

TARGET_LUFS = -14.0
LUFS_TOLERANCE = 2.0        # acceptable band ±2 LU
MAX_TRUE_PEAK_DBTP = -1.0

_I_RE = re.compile(r"I:\s*(-?\d+(?:\.\d+)?)\s*LUFS")
_PEAK_RE = re.compile(r"Peak:\s*(-?\d+(?:\.\d+)?)\s*dBFS")


@dataclass
class LoudnessMeasure:
    integrated_lufs: float | None
    true_peak_dbtp: float | None

    @property
    def measured(self) -> bool:
        return self.integrated_lufs is not None


def measure_loudness(path: Path, ffmpeg: str, *, timeout: float = 300.0) -> LoudnessMeasure:
    cmd = [ffmpeg, "-hide_banner", "-nostats", "-i", str(path),
           "-af", "ebur128=peak=true", "-f", "null", "-"]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, check=False)
    except (OSError, subprocess.SubprocessError):
        return LoudnessMeasure(None, None)
    err = proc.stderr
    i_matches = _I_RE.findall(err)
    peak_matches = _PEAK_RE.findall(err)
    integrated = float(i_matches[-1]) if i_matches else None
    true_peak = max((float(p) for p in peak_matches), default=None) if peak_matches else None
    return LoudnessMeasure(integrated, true_peak)


def loudness_findings(m: LoudnessMeasure) -> list[QcFinding]:
    findings: list[QcFinding] = []
    if not m.measured:
        return findings
    if abs(m.integrated_lufs - TARGET_LUFS) > LUFS_TOLERANCE:
        sev = "major" if abs(m.integrated_lufs - TARGET_LUFS) > 2 * LUFS_TOLERANCE else "minor"
        findings.append(QcFinding(
            0, sev, "loudness",
            f"Overall loudness is {m.integrated_lufs:.1f} LUFS (target ~{TARGET_LUFS:.0f}).",
            "Coach re-normalises to the social target; re-render if this persists."))
    if m.true_peak_dbtp is not None and m.true_peak_dbtp > MAX_TRUE_PEAK_DBTP:
        findings.append(QcFinding(
            0, "major", "true_peak",
            f"True peak is {m.true_peak_dbtp:.1f} dBTP (should be ≤ {MAX_TRUE_PEAK_DBTP:.0f}).",
            "Lower the ceiling to avoid clipping on phones."))
    return findings
