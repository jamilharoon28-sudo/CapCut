"""Beat-synced campaign montage (pack doc 18): cut on the music's phrase grid.

Given a music track's Audio DNA, place cuts on a ~2 s phrase grid snapped to
real beats, rotate through clips for visual variety (no accidental adjacent
duplicates), start each shot on its best moment, reframe on the subject, and lay
the narrative text beats across the shots. The music becomes the soundtrack; an
optional branded outro closes it.

A cut only snaps to a beat inside an allowed window — a shot is never trimmed so
short that it becomes a flicker.
"""

from __future__ import annotations

import uuid

from .analysis.audio import AudioDNA
from .schemas.edit_plan import Caption, EditPlan, Segment, Transform

SECOND_US = 1_000_000
MIN_PHRASE_US = int(1.2 * SECOND_US)


def build_music_montage(
    catalog,                       # list[CatalogAsset]
    audio_dna: AudioDNA,
    *,
    project_id: str,
    target_us: int,
    phrase_seconds: float = 2.0,
    captions: list[str] | None = None,
    analyses: dict | None = None,
) -> EditPlan:
    analyses = analyses or {}
    until_s = min(target_us / SECOND_US, audio_dna.duration_s or target_us / SECOND_US)
    cuts = audio_dna.phrase_cuts_s(phrase_seconds, until_s)
    if len(cuts) < 2:
        cuts = [0.0, until_s]

    segments: list[Segment] = []
    caption_events: list[Caption] = []
    prev_asset_id: str | None = None
    ci = 0  # rotation cursor across the catalog
    n = len(catalog)

    for i in range(len(cuts) - 1):
        phrase_us = int(round((cuts[i + 1] - cuts[i]) * SECOND_US))
        if phrase_us < MIN_PHRASE_US:
            continue
        # Rotate to the next clip, skipping an immediate repeat for visual variety.
        asset = catalog[ci % n]
        if n > 1 and asset.id == prev_asset_id:
            ci += 1
            asset = catalog[ci % n]
        ci += 1
        prev_asset_id = asset.id

        an = analyses.get(asset.id)
        best = getattr(an, "best_start_us", min(int(0.3 * SECOND_US), asset.duration_us // 10))
        src_start = max(0, min(best, max(0, asset.duration_us - phrase_us)))
        dur = min(phrase_us, asset.duration_us - src_start)
        if dur <= 0:
            dur = min(phrase_us, asset.duration_us)
            src_start = 0
        crop_x = float(getattr(an, "crop_x_norm", 0.0))
        tl = int(round(cuts[i] * SECOND_US))
        segments.append(Segment(
            id=f"seg_{uuid.uuid4().hex[:12]}",
            asset_id=asset.id,
            source_start_us=src_start,
            source_duration_us=dur,
            timeline_start_us=tl,
            timeline_duration_us=dur,
            role="hook" if not segments else "point",
            reason="beat_synced_phrase",
            confidence=float(getattr(an, "score", 0.6)),
            transform=Transform(scale=1.0, x=crop_x, y=0.0),
        ))
        if captions and i < len(captions):
            caption_events.append(Caption(id=f"cap_{uuid.uuid4().hex[:12]}", text=captions[i],
                                          start_us=tl, duration_us=dur))

    # Re-base the timeline to be contiguous (segments render back-to-back).
    cursor = 0
    for seg, cap in zip(segments, caption_events + [None] * (len(segments) - len(caption_events))):
        seg.timeline_start_us = cursor
        if cap is not None:
            cap.start_us = cursor
            cap.duration_us = seg.timeline_duration_us
        cursor += seg.timeline_duration_us

    return EditPlan(id=f"edit_{uuid.uuid4().hex}", project_id=project_id,
                    segments=segments, captions=caption_events)
