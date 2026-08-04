"""Speech-driven talking-head mode: keep good lines, cut fillers, real captions."""

from __future__ import annotations

from pathlib import Path

from capcut_coach.autocreate import CatalogAsset
from capcut_coach.talking import build_talking_plan
from capcut_coach.transcript import Transcript, Word


class FakeTranscriber:
    """Returns a canned transcript regardless of the audio file."""

    def __init__(self, words):
        self._words = words

    def available(self):
        return True

    def transcribe(self, wav, asset_id, **_):
        return Transcript(asset_id=asset_id, words=[Word(*w) for w in self._words])


def test_talking_plan_keeps_speech_and_drops_fillers(monkeypatch, tmp_path):
    # Stub audio extraction so no real ffmpeg/audio is needed.
    import capcut_coach.media.ffmpeg as ffmpeg_mod
    monkeypatch.setattr(ffmpeg_mod, "extract_audio_16k_mono",
                        lambda src, dst, **_: Path(dst).write_bytes(b"RIFF") or Path(dst))

    # "So <um> here is the point" — the isolated "um" must be dropped.
    words = [
        ("So", 0, 300_000, 0.9),
        ("um", 700_000, 1_000_000, 0.9),          # standalone filler unit
        ("here", 1_400_000, 1_700_000, 0.95),
        ("is", 1_750_000, 1_900_000, 0.95),
        ("the", 1_950_000, 2_100_000, 0.95),
        ("point", 2_150_000, 2_600_000, 0.95),
    ]
    asset = CatalogAsset(id="a1", path=tmp_path / "clip.mp4", duration_us=3_000_000,
                         has_audio=True)
    plan = build_talking_plan([asset], transcriber=FakeTranscriber(words),
                              project_id="p1", target_us=45_000_000, min_kept_words=2)
    assert plan is not None
    joined = " ".join(c.text for c in plan.captions).lower()
    assert "point" in joined
    assert "um" not in joined.split()  # filler dropped, not just hidden
    # Captions come from real words and align 1:1 with kept segments.
    assert len(plan.captions) == len(plan.segments)


def test_talking_plan_returns_none_without_enough_speech(monkeypatch, tmp_path):
    import capcut_coach.media.ffmpeg as ffmpeg_mod
    monkeypatch.setattr(ffmpeg_mod, "extract_audio_16k_mono",
                        lambda src, dst, **_: Path(dst).write_bytes(b"x") or Path(dst))
    asset = CatalogAsset(id="a1", path=tmp_path / "c.mp4", duration_us=2_000_000, has_audio=True)
    plan = build_talking_plan([asset], transcriber=FakeTranscriber([("hi", 0, 200_000, 0.9)]),
                              project_id="p", target_us=45_000_000, min_kept_words=8)
    assert plan is None  # too little speech → caller falls back to montage
