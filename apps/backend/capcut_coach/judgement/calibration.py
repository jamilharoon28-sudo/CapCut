"""Project-relative calibration for technical evidence (add-on §7.3).

The current pipeline normalises focus/exposure *within a single clip*, so one bad
clip can still score itself well. This module instead calibrates each window
against the whole project's distribution using robust statistics (median + MAD),
then keeps a small set of absolute hard blockers for footage that is unusable no
matter the context (decode failure, near-black, severe clipping, extreme blur).

A dim-but-intentional campaign should not lose every clip to a universal
brightness threshold — hence relative z-scores — while a truly broken window is
still rejected outright. Pure NumPy/statistics; no media dependency.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .schemas import TechnicalEvidence

# Absolute blockers (add-on §6/§7.3): unusable regardless of the project baseline.
NEAR_BLACK_RATIO = 0.60
SEVERE_CLIP_RATIO = 0.50
FREEZE_RATIO = 0.90
_MAD_SCALE = 1.4826  # scales MAD to be a consistent estimator of std for normals


@dataclass(frozen=True)
class Baseline:
    """Robust centre/spread of a metric across the project's windows."""

    median: float
    mad: float

    def z(self, value: float) -> float:
        """Robust z-score; 0 when the project has no spread (all equal)."""
        if self.mad <= 1e-9:
            return 0.0
        return (value - self.median) / (self.mad * _MAD_SCALE)


def build_baseline(values: list[float]) -> Baseline:
    """Robust baseline from a metric's values across all project windows."""
    if not values:
        return Baseline(median=0.0, mad=0.0)
    arr = np.asarray(values, dtype=float)
    med = float(np.median(arr))
    mad = float(np.median(np.abs(arr - med)))
    return Baseline(median=med, mad=mad)


def hard_failures(tech: TechnicalEvidence) -> list[str]:
    """Absolute, context-independent reasons a window is unusable (add-on §7.3)."""
    reasons: list[str] = list(tech.hard_failures)
    if tech.black_frame_ratio >= NEAR_BLACK_RATIO:
        reasons.append("near_black")
    if tech.clipped_highlight_ratio >= SEVERE_CLIP_RATIO:
        reasons.append("blown_highlights")
    if tech.clipped_shadow_ratio >= SEVERE_CLIP_RATIO:
        reasons.append("crushed_shadows")
    if tech.freeze_ratio >= FREEZE_RATIO:
        reasons.append("frozen")
    return sorted(set(reasons))


def usability_score(
    tech: TechnicalEvidence,
    *,
    focus_baseline: Baseline,
    exposure_baseline: Baseline | None = None,
) -> float:
    """Relative technical usability in [0, 1] (add-on §7.3).

    0.0 if any absolute hard blocker fires. Otherwise a bounded score from the
    window's robust z-scores: focus above the project median is good; heavy
    clipping, flicker and camera jerk subtract. Deliberately gentle on exposure
    so an intentionally dark look isn't punished — only *clipping* is penalised.
    """
    if hard_failures(tech):
        return 0.0
    # Focus relative to the project — reward sharper-than-typical, don't over-reward.
    fz = focus_baseline.z(tech.focus_median)
    score = 0.5 + 0.15 * float(np.tanh(fz))
    # Penalise objective faults, not artistic darkness.
    score -= 0.25 * (tech.clipped_highlight_ratio + tech.clipped_shadow_ratio)
    score -= 0.20 * min(1.0, tech.flicker_score)
    score -= 0.15 * min(1.0, tech.camera_jerk)
    score -= 0.10 * tech.freeze_ratio
    return float(max(0.0, min(1.0, score)))
