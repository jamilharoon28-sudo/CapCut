"""Phrase / silence / filler / repeat / restart detection (Phase 3, test F5).

Pure, deterministic, dependency-free. Given word-level timing it segments the
transcript into units and marks removable ones (long silence, filler words,
repeated phrases, false restarts) while preserving intentional dramatic pauses
via a configurable threshold. Nothing is deleted — units are flagged so the user
can restore any of them in one click.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from ..transcript import Transcript, TranscriptUnit, Word

MS = 1000
SECOND_US = 1_000_000

# Common English fillers. Kept short and explicit; extended via custom vocab.
DEFAULT_FILLERS = {
    "um", "umm", "uh", "uhh", "er", "erm", "ah", "hmm", "like", "you know",
    "i mean", "sort of", "kind of", "basically", "literally", "actually",
}


@dataclass
class DetectionSettings:
    # A gap longer than this between words starts a new unit boundary.
    phrase_gap_us: int = 350 * MS
    # Silence at least this long becomes a removable 'silence' unit...
    silence_remove_us: int = 700 * MS
    # ...unless it is below the dramatic-pause ceiling, then it is preserved.
    dramatic_pause_us: int = 1500 * MS
    # Natural-cut margins added around a kept unit so phonemes are not clipped.
    lead_margin_us: int = 60 * MS
    tail_margin_us: int = 90 * MS
    # Confidence under which a very short word is treated as a possible clip risk.
    low_confidence: float = 0.45
    fillers: frozenset[str] = frozenset(DEFAULT_FILLERS)
    remove_fillers: bool = True
    remove_repeats: bool = True
    remove_restarts: bool = True


_NORMALISE_RE = re.compile(r"[^a-z0-9']+")


def _norm(text: str) -> str:
    return _NORMALISE_RE.sub(" ", text.lower()).strip()


def _group_into_units(transcript: Transcript, settings: DetectionSettings) -> list[TranscriptUnit]:
    """Split words into speech units and insert silence units for large gaps."""
    units: list[TranscriptUnit] = []
    current: list[Word] = []
    idx = 0

    def flush() -> None:
        nonlocal current, idx
        if current:
            units.append(TranscriptUnit(id=f"u{idx}", words=list(current)))
            idx += 1
            current = []

    prev_end: int | None = None
    for w in transcript.words:
        if prev_end is not None:
            gap = w.start_us - prev_end
            if gap >= settings.phrase_gap_us:
                flush()
                if gap >= settings.silence_remove_us:
                    keep = gap < settings.dramatic_pause_us
                    silence = TranscriptUnit(
                        id=f"u{idx}",
                        words=[Word(text="", start_us=prev_end, end_us=w.start_us, confidence=1.0)],
                        kind="silence",
                        keep=keep,
                        reason="dramatic_pause" if keep else "long_silence",
                    )
                    units.append(silence)
                    idx += 1
        current.append(w)
        prev_end = w.end_us
    flush()
    return units


def _mark_fillers(unit: TranscriptUnit, settings: DetectionSettings) -> None:
    if unit.kind != "speech":
        return
    words_norm = _norm(unit.text)
    if not words_norm:
        return
    # Whole unit is just a filler ("um", "you know").
    if words_norm in settings.fillers:
        unit.kind = "filler"
        unit.keep = False
        unit.reason = "filler_phrase"


def _mark_repeats_and_restarts(units: list[TranscriptUnit], settings: DetectionSettings) -> None:
    speech = [u for u in units if u.kind == "speech"]
    for prev, cur in zip(speech, speech[1:]):
        pn, cn = _norm(prev.text), _norm(cur.text)
        if not pn or not cn:
            continue
        # Immediate repeated phrase → keep the later (usually cleaner) take.
        if settings.remove_repeats and pn == cn:
            prev.keep = False
            prev.kind = "repeat"
            prev.reason = "repeated_take"
            continue
        # False restart: the earlier unit is a strict prefix of the next attempt.
        if settings.remove_restarts and len(cn) > len(pn) and cn.startswith(pn + " "):
            prev.keep = False
            prev.kind = "restart"
            prev.reason = "false_restart"


def segment_transcript(
    transcript: Transcript, settings: DetectionSettings | None = None
) -> list[TranscriptUnit]:
    """Segment a transcript into units with removable ones flagged.

    Guarantees (F5): every unit stays inside the media, units are contiguous and
    ordered, and no unit is deleted — only ``keep`` is toggled.
    """
    settings = settings or DetectionSettings()
    if not transcript.words:
        return []
    units = _group_into_units(transcript, settings)
    for u in units:
        _mark_fillers(u, settings)
    if settings.remove_repeats or settings.remove_restarts:
        _mark_repeats_and_restarts(units, settings)
    return units


def clip_risk_units(units: list[TranscriptUnit], settings: DetectionSettings) -> list[str]:
    """Ids of kept speech units whose edges risk clipping a phoneme/breath."""
    at_risk: list[str] = []
    for u in units:
        if u.kind != "speech" or not u.keep or not u.words:
            continue
        first, last = u.words[0], u.words[-1]
        if first.confidence < settings.low_confidence or last.confidence < settings.low_confidence:
            at_risk.append(u.id)
    return at_risk
