"""Shot boundaries and candidate windows (add-on §7.1/§7.2, Phase 1).

A source clip is split into shots; each shot yields several overlapping 2–5 s
candidate *windows* (the unit later phases score). Window generation is pure and
deterministic and can snap cut points toward motion valleys so a window doesn't
begin or end mid-action. Shot detection prefers PySceneDetect when installed and
falls back to fixed-interval splitting so the pipeline still runs without it.
"""

from __future__ import annotations

from pathlib import Path

from .schemas import ShotWindow

SECOND_US = 1_000_000
DEFAULT_MIN_US = int(2.0 * SECOND_US)
DEFAULT_MAX_US = int(5.0 * SECOND_US)
DEFAULT_STRIDE_US = int(1.5 * SECOND_US)
_MIN_USABLE_US = int(1.0 * SECOND_US)   # shorter than this ⇒ not a usable window


def _snap_to_valley(start_us: int, valleys_us: list[int], tolerance_us: int) -> int:
    """Nudge a window start to the nearest motion valley within tolerance."""
    if not valleys_us:
        return start_us
    nearest = min(valleys_us, key=lambda v: abs(v - start_us))
    return nearest if abs(nearest - start_us) <= tolerance_us else start_us


def candidate_windows(
    asset_id: str,
    shot_start_us: int,
    shot_end_us: int,
    *,
    min_us: int = DEFAULT_MIN_US,
    max_us: int = DEFAULT_MAX_US,
    stride_us: int = DEFAULT_STRIDE_US,
    valleys_us: list[int] | None = None,
    keyframes: int = 5,
) -> list[ShotWindow]:
    """Overlapping candidate windows within one shot (add-on §7.2)."""
    shot_len = max(0, shot_end_us - shot_start_us)
    if shot_len < _MIN_USABLE_US:
        return []

    windows: list[ShotWindow] = []
    if shot_len <= max_us:
        starts = [shot_start_us]
        target = shot_len
    else:
        target = max_us
        last_start = shot_end_us - target
        starts = list(range(shot_start_us, last_start + 1, stride_us))
        if starts[-1] != last_start:
            starts.append(last_start)

    tol = stride_us // 2
    for k, raw_start in enumerate(starts):
        start = _snap_to_valley(raw_start, valleys_us or [], tol)
        start = max(shot_start_us, min(start, shot_end_us - min(target, shot_len)))
        end = min(shot_end_us, start + target)
        if end - start < min(min_us, shot_len):
            continue
        n = max(2, keyframes)
        step = (end - start) / (n - 1)
        kf = [int(start + round(i * step)) for i in range(n)]
        windows.append(ShotWindow(
            id=f"win_{asset_id}_{k}", asset_id=asset_id,
            shot_start_us=shot_start_us, shot_end_us=shot_end_us,
            window_start_us=start, window_end_us=end,
            keyframe_times_us=kf, extractor_version="p1", confidence=0.5))
    return windows


def detect_boundaries(
    path: Path,
    duration_us: int,
    *,
    fallback_shot_us: int = int(4.0 * SECOND_US),
) -> list[tuple[int, int]]:
    """Return shot [start_us, end_us] spans. Uses PySceneDetect when available;
    otherwise splits into fixed-length shots so the pipeline still runs.

    The PySceneDetect path is exercised on the Mac (dependency + real media);
    here the deterministic fallback keeps everything testable.
    """
    try:
        from scenedetect import detect
        from scenedetect.detectors import AdaptiveDetector

        scenes = detect(str(path), AdaptiveDetector())
        spans = [(int(s.get_seconds() * SECOND_US), int(e.get_seconds() * SECOND_US))
                 for s, e in scenes]
        if spans:
            return spans
    except Exception:
        pass
    return uniform_shots(duration_us, fallback_shot_us)


def uniform_shots(duration_us: int, shot_us: int) -> list[tuple[int, int]]:
    """Split a duration into fixed-length shots (deterministic fallback)."""
    if duration_us <= 0:
        return []
    spans: list[tuple[int, int]] = []
    t = 0
    while t < duration_us:
        spans.append((t, min(duration_us, t + shot_us)))
        t += shot_us
    return spans
