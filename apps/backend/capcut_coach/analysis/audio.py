"""Audio DNA: tempo, beats, and onsets for beat-synced cutting (pack doc 18 §4).

Local only. Extracts audio with FFmpeg, then uses librosa (pinned, open-source)
to derive tempo, a beat grid, and onset times so the montage can place cuts
within a small window of a real musical onset — never clipping a word or action
just to hit a beat. librosa is optional; without it, beat-sync degrades to a
fixed phrase grid.
"""

from __future__ import annotations

import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path


def librosa_available() -> bool:
    try:
        import librosa  # noqa: F401
        return True
    except ImportError:
        return False


@dataclass
class AudioDNA:
    duration_s: float
    tempo_bpm: float
    beat_times_s: list[float] = field(default_factory=list)
    onset_times_s: list[float] = field(default_factory=list)
    energy: float = 0.0        # 0..1 overall loudness/energy (RMS-derived)
    has_vocals_hint: bool = False  # coarse hint; not a guarantee

    def phrase_cuts_s(self, phrase_seconds: float, until_s: float) -> list[float]:
        """Cut points on a musical phrase grid (~every N beats), snapped to beats.

        Falls back to a fixed grid when there is no beat information.
        """
        if not self.beat_times_s:
            n = max(1, int(until_s // phrase_seconds))
            return [round(i * phrase_seconds, 3) for i in range(n + 1)]
        beats = self.beat_times_s
        # Beats per phrase from the detected tempo (e.g. 120 BPM → 4 beats ≈ 2 s).
        beat_period = 60.0 / self.tempo_bpm if self.tempo_bpm > 0 else 0.5
        per_phrase = max(1, round(phrase_seconds / beat_period))
        cuts = [b for b in beats[::per_phrase] if b <= until_s]
        if not cuts or cuts[0] > 0.05:
            cuts = [0.0, *cuts]
        return cuts


def _extract_wav(src: Path, dst: Path, ffmpeg: str, *, sr: int = 22050) -> bool:
    cmd = [ffmpeg, "-y", "-hide_banner", "-loglevel", "error", "-i", str(src),
           "-vn", "-ac", "1", "-ar", str(sr), str(dst)]
    return subprocess.run(cmd, capture_output=True, check=False).returncode == 0 and dst.exists()


def analyse_audio(path: Path, ffmpeg: str) -> AudioDNA | None:
    """Return AudioDNA for a track, or None if librosa/audio is unavailable."""
    if not librosa_available():
        return None
    import librosa
    import numpy as np

    with tempfile.TemporaryDirectory() as td:
        wav = Path(td) / "a.wav"
        if not _extract_wav(path, wav, ffmpeg):
            return None
        try:
            y, sr = librosa.load(str(wav), sr=22050, mono=True)
        except Exception:
            return None
    if y.size == 0:
        return None
    duration = float(librosa.get_duration(y=y, sr=sr))
    tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
    beat_times = librosa.frames_to_time(beat_frames, sr=sr)
    onset_frames = librosa.onset.onset_detect(y=y, sr=sr, backtrack=True)
    onset_times = librosa.frames_to_time(onset_frames, sr=sr)
    tempo_val = float(np.atleast_1d(tempo)[0])
    # Energy: mean RMS mapped to ~0..1 (‑40 dBFS→0, 0 dBFS→1).
    rms = float(np.sqrt(np.mean(np.square(y)))) if y.size else 0.0
    db = 20.0 * np.log10(rms + 1e-9)
    energy = float(min(1.0, max(0.0, (db + 40.0) / 40.0)))
    return AudioDNA(
        duration_s=duration,
        tempo_bpm=round(tempo_val, 1),
        beat_times_s=[round(float(t), 3) for t in beat_times],
        onset_times_s=[round(float(t), 3) for t in onset_times],
        energy=round(energy, 3),
    )


def snap_to_onset(t_s: float, onsets: list[float], tolerance_ms: int = 200) -> float:
    """Snap a time to the nearest onset within tolerance; else return it unchanged."""
    if not onsets:
        return t_s
    nearest = min(onsets, key=lambda o: abs(o - t_s))
    return nearest if abs(nearest - t_s) * 1000 <= tolerance_ms else t_s
