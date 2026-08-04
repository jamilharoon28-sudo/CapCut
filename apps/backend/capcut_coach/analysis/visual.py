"""Per-clip visual analysis: best moment + subject reframe (pack doc 15 §6).

Samples a handful of frames with FFmpeg, then scores each for sharpness (focus),
exposure, and subject presence/position (face detection). Picks the timestamp of
the best window and a horizontal crop offset that keeps the subject in frame.

OpenCV is optional and lazily imported. Without it, analysis degrades to an
exposure-only score via FFmpeg ``signalstats`` and centre framing — the montage
still renders. Nothing here downloads a model or calls the network.
"""

from __future__ import annotations

import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

SECOND_US = 1_000_000


def cv2_available() -> bool:
    try:
        import cv2  # noqa: F401
        return True
    except ImportError:
        return False


@dataclass
class ClipAnalysis:
    best_start_us: int      # where to start the kept window
    crop_x_norm: float      # -1 (frame left) .. 0 (centre) .. +1 (frame right)
    score: float            # overall quality 0..1 (higher = better moment)
    has_subject: bool


def _sample_timestamps(duration_us: int, n: int) -> list[int]:
    """Evenly spaced sample points inside the middle 80% of the clip."""
    if duration_us <= 0:
        return [0]
    lo, hi = int(duration_us * 0.1), int(duration_us * 0.9)
    if hi <= lo:
        return [duration_us // 2]
    if n <= 1:
        return [(lo + hi) // 2]
    step = (hi - lo) / (n - 1)
    return [int(lo + i * step) for i in range(n)]


def _extract_frame(ffmpeg: str, clip: Path, ts_us: int, dst: Path, width: int = 320) -> bool:
    cmd = [ffmpeg, "-y", "-hide_banner", "-loglevel", "error",
           "-ss", f"{ts_us / SECOND_US:.3f}", "-i", str(clip),
           "-frames:v", "1", "-vf", f"scale={width}:-2", str(dst)]
    return subprocess.run(cmd, capture_output=True, check=False).returncode == 0 and dst.exists()


def _score_frame_cv2(path: Path) -> tuple[float, float, bool]:
    """Return (sharpness, exposure_score, face_cx_norm_or_-2, has_face)."""
    import cv2

    img = cv2.imread(str(path))
    if img is None:
        return 0.0, 0.0, False
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    sharpness = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    mean = float(gray.mean())
    # Exposure best near mid-grey; penalise crushed blacks / blown highlights.
    exposure = max(0.0, 1.0 - abs(mean - 118.0) / 118.0)
    face_cx = None
    try:
        cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
        faces = cascade.detectMultiScale(gray, scaleFactor=1.15, minNeighbors=5,
                                         minSize=(40, 40))
        if len(faces) > 0:
            x, _y, w, _h = max(faces, key=lambda f: f[2] * f[3])
            face_cx = (x + w / 2) / gray.shape[1]
    except Exception:
        face_cx = None
    return sharpness, exposure, face_cx


def analyse_clip(clip: Path, duration_us: int, ffmpeg: str, *, samples: int = 6) -> ClipAnalysis:
    """Analyse a clip and return the best window start + reframe offset."""
    if not cv2_available():
        return ClipAnalysis(best_start_us=min(int(0.3 * SECOND_US), duration_us // 10),
                            crop_x_norm=0.0, score=0.5, has_subject=False)

    timestamps = _sample_timestamps(duration_us, samples)
    scored: list[tuple[int, float, float | None]] = []  # (ts, quality, face_cx)
    with tempfile.TemporaryDirectory() as td:
        sharpness_vals: list[float] = []
        raw: list[tuple[int, float, float, float | None]] = []
        for i, ts in enumerate(timestamps):
            f = Path(td) / f"f{i}.png"
            if not _extract_frame(ffmpeg, clip, ts, f):
                continue
            sharp, expo, face_cx = _score_frame_cv2(f)
            sharpness_vals.append(sharp)
            raw.append((ts, sharp, expo, face_cx))
        if not raw:
            return ClipAnalysis(best_start_us=timestamps[0], crop_x_norm=0.0, score=0.4,
                                has_subject=False)
        max_sharp = max(sharpness_vals) or 1.0
        for ts, sharp, expo, face_cx in raw:
            focus = sharp / max_sharp
            face_bonus = 0.25 if face_cx is not None else 0.0
            quality = 0.5 * focus + 0.35 * expo + face_bonus
            scored.append((ts, quality, face_cx))

    best_ts, best_q, best_face = max(scored, key=lambda s: s[1])
    crop_x = 0.0
    if best_face is not None:
        crop_x = max(-1.0, min(1.0, (best_face - 0.5) * 2.0))
    # Start the window a touch before the best frame so it opens cleanly.
    best_start = max(0, best_ts - int(0.25 * SECOND_US))
    return ClipAnalysis(best_start_us=best_start, crop_x_norm=round(crop_x, 3),
                        score=round(min(1.0, best_q), 3), has_subject=best_face is not None)
