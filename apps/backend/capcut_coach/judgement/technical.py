"""Multi-frame technical metrics for a window (add-on §7.2, Phase 1).

The current pipeline judges a clip from ~6 isolated frames and normalises focus
within that one clip. This module instead computes *distributions* over the
frames of a candidate window — focus median and worst-decile, exposure
percentiles and clipping, flicker, camera motion and jerk, freeze and black —
returning a ``TechnicalEvidence`` row. Calibration against the whole project
happens separately in ``calibration.py`` (add-on §7.3).

Pure NumPy: input is a stack of grayscale frames (the Mac step decodes proxy
frames with FFmpeg and hands them here). OpenCV is used for dense optical flow
when available, with a frame-difference fallback so this runs anywhere.
"""

from __future__ import annotations

import numpy as np

from .schemas import TechnicalEvidence

# Pixel thresholds on an 8-bit luma scale.
_SHADOW_CLIP = 2
_HIGHLIGHT_CLIP = 253
_UNDER = 16
_OVER = 240
_BLACK_MEAN = 8.0
_FREEZE_EPS = 0.8   # mean abs frame delta below this ⇒ effectively frozen


def _laplacian_var(gray: np.ndarray) -> float:
    """Variance of the 4-neighbour Laplacian — a standard focus/sharpness measure."""
    g = gray.astype(np.float32)
    lap = (-4.0 * g[1:-1, 1:-1]
           + g[:-2, 1:-1] + g[2:, 1:-1] + g[1:-1, :-2] + g[1:-1, 2:])
    return float(lap.var()) if lap.size else 0.0


def _motion_signal(frames: list[np.ndarray]) -> np.ndarray:
    """Per-adjacent-pair global motion in [0,1]-ish units.

    Uses OpenCV dense optical flow when present (truer camera motion); otherwise a
    normalised mean absolute frame difference. Either way, higher = more motion.
    """
    if len(frames) < 2:
        return np.zeros(0, dtype=np.float32)
    try:  # optional: real optical flow
        import cv2

        mags = []
        for a, b in zip(frames, frames[1:]):
            flow = cv2.calcOpticalFlowFarneback(
                a.astype(np.uint8), b.astype(np.uint8), None,
                0.5, 3, 15, 3, 5, 1.2, 0)
            mags.append(float(np.mean(np.hypot(flow[..., 0], flow[..., 1]))))
        m = np.asarray(mags, dtype=np.float32)
        return np.tanh(m / 4.0)  # squash to a bounded, comparable range
    except Exception:
        diffs = [float(np.mean(np.abs(a.astype(np.float32) - b.astype(np.float32))))
                 for a, b in zip(frames, frames[1:])]
        return np.tanh(np.asarray(diffs, dtype=np.float32) / 24.0)


def analyse_window(
    frames: list[np.ndarray],
    *,
    audio_peak_dbfs: float | None = None,
    audio_lufs: float | None = None,
    extractor_version: str = "p1",
) -> TechnicalEvidence:
    """Compute a TechnicalEvidence distribution from a window's grayscale frames."""
    if not frames:
        return TechnicalEvidence(extractor_version=extractor_version,
                                 hard_failures=["no_frames"], confidence=0.0)

    foci = np.asarray([_laplacian_var(f) for f in frames], dtype=np.float32)
    means = np.asarray([float(f.mean()) for f in frames], dtype=np.float32)
    total_px = float(sum(f.size for f in frames))

    def _ratio(pred_counts: list[float]) -> float:
        return float(sum(pred_counts) / total_px) if total_px else 0.0

    under = _ratio([float((f < _UNDER).sum()) for f in frames])
    over = _ratio([float((f > _OVER).sum()) for f in frames])
    shadow = _ratio([float((f <= _SHADOW_CLIP).sum()) for f in frames])
    highlight = _ratio([float((f >= _HIGHLIGHT_CLIP).sum()) for f in frames])

    # Flicker: relative frame-to-frame brightness swing.
    if len(means) > 1 and means.mean() > 1e-6:
        flicker = float(np.mean(np.abs(np.diff(means))) / (means.mean() + 1e-6))
    else:
        flicker = 0.0

    motion = _motion_signal(frames)
    camera_motion = float(motion.mean()) if motion.size else 0.0
    camera_jerk = float(np.mean(np.abs(np.diff(motion)))) if motion.size > 1 else 0.0

    black_ratio = float(np.mean(means < _BLACK_MEAN))
    if len(frames) > 1:
        deltas = [float(np.mean(np.abs(a.astype(np.float32) - b.astype(np.float32))))
                  for a, b in zip(frames, frames[1:])]
        freeze_ratio = float(np.mean(np.asarray(deltas) < _FREEZE_EPS))
    else:
        freeze_ratio = 0.0

    # Confidence in the measurement itself: more frames + real motion signal.
    confidence = float(min(1.0, 0.4 + 0.1 * len(frames)))
    return TechnicalEvidence(
        extractor_version=extractor_version,
        focus_median=float(np.median(foci)),
        focus_floor=float(np.percentile(foci, 10)),
        underexposed_ratio=under,
        overexposed_ratio=over,
        clipped_shadow_ratio=shadow,
        clipped_highlight_ratio=highlight,
        flicker_score=min(1.0, flicker),
        camera_motion=camera_motion,
        camera_jerk=min(1.0, camera_jerk),
        freeze_ratio=freeze_ratio,
        black_frame_ratio=black_ratio,
        audio_peak_dbfs=audio_peak_dbfs,
        audio_lufs=audio_lufs,
        confidence=confidence,
    )
