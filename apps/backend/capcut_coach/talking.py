"""Speech-driven editing for talking-head footage (pack docs 15 §6, 16).

For each clip with speech: extract audio, transcribe locally with whisper.cpp,
segment into phrases, drop fillers / silence / restarts / repeated takes (the
tested deterministic rough-cut engine), and keep the good spoken lines. Captions
come from the **real transcribed words** — never invented. Returns None when
there is not enough speech, so the caller falls back to the visual montage.

Requires a whisper.cpp model (``scripts/setup-whisper.sh``). When absent,
``resolve_transcriber`` returns None and this mode is simply unavailable.
"""

from __future__ import annotations

import os
import tempfile
import uuid
from pathlib import Path

from .media.transcription import WhisperCppTranscriber, WhisperModel
from .roughcut.detect import DetectionSettings, segment_transcript
from .schemas.edit_plan import Caption, EditPlan, Segment, Transform

SECOND_US = 1_000_000


def resolve_transcriber() -> WhisperCppTranscriber | None:
    """Locate a whisper.cpp binary + verified model, or return None.

    The binary is found from (in order): COACH_WHISPER, PATH/Homebrew, or —
    most reliably — *derived from the model path* (…/whisper.cpp/models/*.bin ->
    …/whisper.cpp/build/bin/whisper-cli). The derivation means talking-head mode
    works even when the models dir isn't on the app's PATH.
    """
    from .toolpaths import resolve

    model_path = os.environ.get("COACH_WHISPER_MODEL")
    if not model_path:
        return None
    model_file = Path(model_path)
    if not model_file.exists():
        return None

    candidates: list[str] = []
    if os.environ.get("COACH_WHISPER"):
        candidates.append(os.environ["COACH_WHISPER"])
    for name in ("whisper-cli", "whisper.cpp", "main"):
        found = resolve(name)
        if found:
            candidates.append(found)
    # Derive from the whisper.cpp checkout that holds the model.
    for ancestor in model_file.parents:
        if ancestor.name == "whisper.cpp":
            for rel in ("build/bin/whisper-cli", "build/bin/main", "whisper-cli", "main"):
                candidates.append(str(ancestor / rel))
            break

    binary = next((c for c in candidates if c and Path(c).exists()), None)
    if not binary:
        return None
    t = WhisperCppTranscriber(binary=binary, model=WhisperModel(name=model_file.stem,
                                                                path=model_file))
    return t if t.available() else None


def build_talking_plan(
    catalog,  # list[CatalogAsset]
    *,
    transcriber: WhisperCppTranscriber,
    project_id: str,
    target_us: int = 45 * SECOND_US,
    ffmpeg: str | None = None,
    settings: DetectionSettings | None = None,
    analyses: dict | None = None,
    min_kept_words: int = 8,
) -> EditPlan | None:
    """Cut the good spoken lines across clips. None if too little speech."""
    from .media import ffmpeg as ffmpeg_mod

    settings = settings or DetectionSettings()
    analyses = analyses or {}
    segments: list[Segment] = []
    captions: list[Caption] = []
    cursor = 0
    kept_words = 0

    for asset in catalog:
        if not asset.has_audio or cursor >= target_us:
            continue
        with tempfile.TemporaryDirectory() as td:
            wav = Path(td) / "audio16k.wav"
            try:
                ffmpeg_mod.extract_audio_16k_mono(asset.path, wav)
                transcript = transcriber.transcribe(wav, asset.id)
            except Exception:
                continue  # unreadable audio / transcription failure → skip clip
        if not transcript.words:
            continue
        units = segment_transcript(transcript, settings)
        crop_x = float(getattr(analyses.get(asset.id), "crop_x_norm", 0.0))
        for unit in units:
            if not unit.keep or unit.kind != "speech" or unit.duration_us <= 0:
                continue
            lead = settings.lead_margin_us
            tail = settings.tail_margin_us
            src_start = max(0, unit.start_us - lead)
            src_end = min(asset.duration_us, unit.end_us + tail)
            dur = src_end - src_start
            if dur <= 0:
                continue
            segments.append(Segment(
                id=f"seg_{uuid.uuid4().hex[:12]}",
                asset_id=asset.id,
                source_start_us=src_start,
                source_duration_us=dur,
                timeline_start_us=cursor,
                timeline_duration_us=dur,
                role="hook" if not segments else "point",
                reason=f"kept_speech:{unit.reason or 'clear_line'}",
                confidence=round(unit.mean_confidence, 3),
                transform=Transform(scale=1.0, x=crop_x, y=0.0),
                source_unit_ids=[unit.id],
            ))
            captions.append(Caption(id=f"cap_{uuid.uuid4().hex[:12]}", text=unit.text,
                                    start_us=cursor, duration_us=dur))
            kept_words += len(unit.words)
            cursor += dur
            if cursor >= target_us:
                break

    if len(segments) < 1 or kept_words < min_kept_words:
        return None
    return EditPlan(id=f"edit_{uuid.uuid4().hex}", project_id=project_id,
                    segments=segments, captions=captions)
