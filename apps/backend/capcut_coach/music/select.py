"""Deterministic, reproducible music selection (pack doc 20 §3 selection).

Scores only rights-eligible tracks and returns the best plus two alternatives,
with a plain-language reason. No network, no ripping — it can only rank tracks
already indexed from approved folders.
"""

from __future__ import annotations

from .schemas import MusicAsset, MusicSelection


def _score(asset: MusicAsset, *, target_s: float, want_energy: float,
           avoid_vocals: bool, prefer_bpm: float | None) -> float:
    score = 0.0
    # Duration: must comfortably cover the target; long enough > too short.
    if asset.duration_s >= target_s:
        score += 0.35
    elif asset.duration_s > 0:
        score += 0.35 * (asset.duration_s / target_s)
    # Energy match (closer to desired = better).
    if asset.energy > 0:
        score += 0.25 * (1.0 - min(1.0, abs(asset.energy - want_energy)))
    # Tempo preference (e.g. campaign ~120 BPM) when known.
    if prefer_bpm and asset.bpm > 0:
        score += 0.20 * (1.0 - min(1.0, abs(asset.bpm - prefer_bpm) / 60.0))
    else:
        score += 0.10
    # Vocals conflict with dialogue-led edits.
    if avoid_vocals and asset.vocals:
        score -= 0.30
    else:
        score += 0.10
    return round(score, 4)


def select_music(
    assets: list[MusicAsset],
    *,
    target_seconds: float,
    want_energy: float = 0.6,
    avoid_vocals: bool = False,
    prefer_bpm: float | None = 120.0,
) -> MusicSelection:
    """Pick the best eligible track + two alternatives. Reproducible from scores."""
    eligible = [a for a in assets if a.eligible]
    if not eligible:
        return MusicSelection(chosen=None, alternatives=[], considered=len(assets),
                              reason="No rights-approved music available.")
    ranked = sorted(
        eligible,
        key=lambda a: _score(a, target_s=target_seconds, want_energy=want_energy,
                             avoid_vocals=avoid_vocals, prefer_bpm=prefer_bpm),
        reverse=True,
    )
    chosen = ranked[0]
    bits = []
    if chosen.bpm:
        bits.append(f"~{chosen.bpm:.0f} BPM")
    if chosen.duration_s:
        bits.append(f"{chosen.duration_s:.0f}s long")
    if avoid_vocals and not chosen.vocals:
        bits.append("instrumental (keeps speech clear)")
    reason = f"“{chosen.title}” — {', '.join(bits) or 'best rights-approved match'}."
    return MusicSelection(chosen=chosen, alternatives=ranked[1:3], reason=reason,
                          considered=len(eligible))
