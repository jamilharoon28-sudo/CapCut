"""whisper.cpp transcription wrapper + model manager (Phase 2, test F4).

Transcription is local (ADR-0002). This module resolves a whisper.cpp binary and
a checksum-pinned model, runs it, and parses word-level output into our
``Transcript``. When neither the binary nor a model is present (CI scaffold), the
provider reports itself unavailable so the caller can mark the stage BLOCKED
rather than fabricate a transcript.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from ..transcript import Transcript, Word


@dataclass
class WhisperModel:
    name: str
    path: Path
    sha256: str | None = None

    def verify(self) -> bool:
        if not self.path.exists():
            return False
        if self.sha256 is None:
            return True
        h = hashlib.sha256()
        with open(self.path, "rb") as f:
            for block in iter(lambda: f.read(1024 * 1024), b""):
                h.update(block)
        return h.hexdigest() == self.sha256


class TranscriptionUnavailable(RuntimeError):
    pass


class WhisperCppTranscriber:
    """Adapter around a whisper.cpp CLI producing word timestamps."""

    def __init__(self, binary: str | None = None, model: WhisperModel | None = None) -> None:
        self.binary = binary or shutil.which("whisper-cli") or shutil.which("whisper.cpp") \
            or shutil.which("main")
        self.model = model

    def available(self) -> bool:
        return bool(self.binary) and self.model is not None and self.model.verify()

    def transcribe(self, audio_16k_wav: Path, asset_id: str, *, language: str = "en",
                   timeout: float = 3600.0) -> Transcript:
        if not self.available():
            raise TranscriptionUnavailable(
                "whisper.cpp binary or verified model is not available on this host"
            )
        assert self.binary and self.model  # for type-checkers
        out_json = audio_16k_wav.with_suffix(".words.json")
        cmd = [
            self.binary, "-m", str(self.model.path), "-f", str(audio_16k_wav),
            "-l", language, "-oj", "-ml", "1", "-of", str(out_json.with_suffix("")),
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, check=False)
        if proc.returncode != 0:
            raise RuntimeError(f"whisper.cpp failed: {proc.stderr.strip()[:200]}")
        return parse_whisper_json(out_json, asset_id, language)


def parse_whisper_json(path: Path, asset_id: str, language: str = "en") -> Transcript:
    """Parse whisper.cpp JSON (token-level) into a word Transcript in microseconds."""
    data = json.loads(Path(path).read_text("utf-8"))
    words: list[Word] = []
    for seg in data.get("transcription", []):
        offsets = seg.get("offsets", {})
        text = (seg.get("text") or "").strip()
        if not text:
            continue
        start_ms = int(offsets.get("from", 0))
        end_ms = int(offsets.get("to", start_ms))
        conf = float(seg.get("p", seg.get("confidence", 1.0)) or 1.0)
        words.append(
            Word(text=text, start_us=start_ms * 1000, end_us=max(end_ms, start_ms) * 1000,
                 confidence=min(max(conf, 0.0), 1.0))
        )
    return Transcript(asset_id=asset_id, words=words, language=language)


def apply_custom_vocabulary(transcript: Transcript, corrections: dict[str, str]) -> Transcript:
    """Case-insensitive whole-word corrections retaining timing/provenance (F4)."""
    lut = {k.lower(): v for k, v in corrections.items()}
    for w in transcript.words:
        replacement = lut.get(w.text.lower())
        if replacement is not None:
            w.text = replacement
    return transcript
