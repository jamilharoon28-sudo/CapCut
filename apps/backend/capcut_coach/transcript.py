"""Transcript data model shared by transcription, rough-cut, and Claude layers.

Times are integer microseconds. A transcript is a list of words with timing and
confidence; the rough-cut engine groups words into *units* (phrases/sentences).
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Word:
    text: str
    start_us: int
    end_us: int
    confidence: float = 1.0

    @property
    def duration_us(self) -> int:
        return self.end_us - self.start_us


@dataclass
class TranscriptUnit:
    """A phrase/sentence: contiguous words plus derived metadata."""

    id: str
    words: list[Word]
    kind: str = "speech"  # speech | silence | filler | restart | repeat
    keep: bool = True
    reason: str = ""

    @property
    def start_us(self) -> int:
        return self.words[0].start_us if self.words else 0

    @property
    def end_us(self) -> int:
        return self.words[-1].end_us if self.words else 0

    @property
    def duration_us(self) -> int:
        return max(0, self.end_us - self.start_us)

    @property
    def text(self) -> str:
        return " ".join(w.text for w in self.words).strip()

    @property
    def mean_confidence(self) -> float:
        if not self.words:
            return 0.0
        return sum(w.confidence for w in self.words) / len(self.words)


@dataclass
class Transcript:
    asset_id: str
    words: list[Word] = field(default_factory=list)
    language: str = "en"

    @property
    def duration_us(self) -> int:
        return self.words[-1].end_us if self.words else 0

    def is_monotonic(self) -> bool:
        """Word timings must be non-decreasing and within [0, duration] (F4)."""
        prev_end = -1
        for w in self.words:
            if w.start_us < 0 or w.end_us < w.start_us:
                return False
            if w.start_us < prev_end:
                return False
            prev_end = w.end_us
        return True
