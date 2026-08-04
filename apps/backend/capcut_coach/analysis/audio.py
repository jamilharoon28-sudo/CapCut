"""Audio DNA: tempo, beats, and onsets for beat-synced cutting (pack doc 18 §4).

Local only, **numpy-only** — no librosa/numba, so it builds on any Python 3.12
without a compile step. Extracts audio with FFmpeg, then derives a spectral-flux
onset envelope, an autocorrelation tempo estimate, a phase-aligned beat grid and
onset peaks, so the montage can place cuts within a small window of a real
musical onset — never clipping a word or action just to hit a beat.
"""

from __future__ import annotations

import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path


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


SR = 22050
HOP = 512
WIN = 1024


def _extract_wav(src: Path, dst: Path, ffmpeg: str, *, sr: int = SR) -> bool:
    cmd = [ffmpeg, "-y", "-hide_banner", "-loglevel", "error", "-i", str(src),
           "-vn", "-ac", "1", "-ar", str(sr), "-c:a", "pcm_s16le", str(dst)]
    return subprocess.run(cmd, capture_output=True, check=False).returncode == 0 and dst.exists()


def _read_wav_mono(path: Path):
    """Read a mono 16-bit PCM WAV into a float32 numpy array in [-1, 1]."""
    import wave

    import numpy as np

    with wave.open(str(path), "rb") as w:
        n = w.getnframes()
        raw = w.readframes(n)
        sampwidth = w.getsampwidth()
    if sampwidth != 2:
        return np.zeros(0, dtype="float32")
    y = np.frombuffer(raw, dtype="<i2").astype("float32") / 32768.0
    return y


def analyse_audio(path: Path, ffmpeg: str) -> AudioDNA | None:
    """Return AudioDNA for a track using a numpy-only detector (no numba/librosa).

    Extracts a mono WAV with FFmpeg, then derives an onset envelope (spectral
    flux), a tempo estimate (autocorrelation), a phase-aligned beat grid, and
    onset peaks. Fully local and dependency-light so it builds on any Mac.
    """
    try:
        import numpy as np
    except ImportError:
        return None
    with tempfile.TemporaryDirectory() as td:
        wav = Path(td) / "a.wav"
        if not _extract_wav(path, wav, ffmpeg):
            return None
        try:
            y = _read_wav_mono(wav)
        except Exception:
            return None
    if y.size < WIN * 2:
        return None
    duration = y.size / SR
    energy_rms = float(np.sqrt(np.mean(np.square(y))))
    db = 20.0 * np.log10(energy_rms + 1e-9)
    energy = float(min(1.0, max(0.0, (db + 40.0) / 40.0)))

    # --- Onset envelope via spectral flux ---
    window = np.hanning(WIN).astype("float32")
    n_frames = 1 + (y.size - WIN) // HOP
    prev = np.zeros(WIN // 2 + 1, dtype="float32")
    env = np.empty(n_frames, dtype="float32")
    for i in range(n_frames):
        frame = y[i * HOP: i * HOP + WIN] * window
        mag = np.abs(np.fft.rfft(frame))
        flux = np.sum(np.maximum(0.0, mag - prev))
        env[i] = flux
        prev = mag
    if env.max() > 0:
        env = env / env.max()
    fps = SR / HOP  # onset-envelope frames per second

    # --- Tempo via autocorrelation of the onset envelope ---
    e = env - env.mean()
    ac = np.correlate(e, e, mode="full")[len(e) - 1:]
    lo = int(fps * 60.0 / 180.0)   # 180 BPM
    hi = int(fps * 60.0 / 60.0)    # 60 BPM
    hi = min(hi, len(ac) - 1)
    if hi <= lo:
        tempo_bpm = 120.0
        period = fps * 0.5
    else:
        lag = lo + int(np.argmax(ac[lo:hi]))
        period = float(lag) if lag > 0 else fps * 0.5
        tempo_bpm = 60.0 * fps / period

    # --- Phase-aligned beat grid ---
    first = int(np.argmax(env[: max(1, int(period))])) if env.size else 0
    beats = []
    t = float(first)
    while t < n_frames:
        beats.append(round(t / fps, 3))
        t += period

    # --- Onset peaks (above mean+std, locally maximal) ---
    thr = env.mean() + env.std()
    onsets = [round(i / fps, 3) for i in range(1, n_frames - 1)
              if env[i] > thr and env[i] >= env[i - 1] and env[i] >= env[i + 1]]

    return AudioDNA(
        duration_s=round(duration, 2),
        tempo_bpm=round(float(tempo_bpm), 1),
        beat_times_s=beats,
        onset_times_s=onsets,
        energy=round(energy, 3),
    )


def snap_to_onset(t_s: float, onsets: list[float], tolerance_ms: int = 200) -> float:
    """Snap a time to the nearest onset within tolerance; else return it unchanged."""
    if not onsets:
        return t_s
    nearest = min(onsets, key=lambda o: abs(o - t_s))
    return nearest if abs(nearest - t_s) * 1000 <= tolerance_ms else t_s
