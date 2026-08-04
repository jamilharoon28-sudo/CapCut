"""Turn detected units into validated EditPlan candidates (Phase 3, test F6).

Kept speech units become timeline segments with natural-cut margins clamped to
media bounds. Duration candidates (e.g. 30/45/60 s) select a prefix of the
strongest kept content. Every produced plan passes ``validate_edit_plan``.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from ..schemas.edit_plan import Caption, EditPlan, Segment, validate_edit_plan
from ..transcript import TranscriptUnit
from .detect import DetectionSettings

SECOND_US = 1_000_000
DEFAULT_TARGET_DURATIONS_US = (30 * SECOND_US, 45 * SECOND_US, 60 * SECOND_US)


@dataclass
class Candidate:
    target_us: int
    plan: EditPlan
    included_unit_ids: list[str]
    overflow: bool  # kept content exceeded the target and was trimmed


@dataclass
class CandidateSet:
    candidates: list[Candidate]
    removed_unit_ids: list[str]  # flagged-not-kept, restorable in the UI


def _clamped_source_window(
    unit: TranscriptUnit, media_us: int, settings: DetectionSettings
) -> tuple[int, int]:
    start = max(0, unit.start_us - settings.lead_margin_us)
    end = min(media_us, unit.end_us + settings.tail_margin_us)
    if end <= start:
        end = min(media_us, start + 1)
    return start, end


def build_candidates(
    *,
    project_id: str,
    asset_id: str,
    media_duration_us: int,
    units: list[TranscriptUnit],
    settings: DetectionSettings | None = None,
    target_durations_us: tuple[int, ...] = DEFAULT_TARGET_DURATIONS_US,
    style_dna_version: str | None = None,
) -> CandidateSet:
    settings = settings or DetectionSettings()
    kept = [u for u in units if u.keep and u.kind == "speech" and u.duration_us > 0]
    removed = [u.id for u in units if not u.keep]

    candidates: list[Candidate] = []
    for target_us in target_durations_us:
        segments: list[Segment] = []
        captions: list[Caption] = []
        included: list[str] = []
        timeline_cursor = 0
        overflow = False

        for unit in kept:
            src_start, src_end = _clamped_source_window(unit, media_duration_us, settings)
            seg_dur = src_end - src_start
            if seg_dur <= 0:
                continue
            if timeline_cursor + seg_dur > target_us and segments:
                # Respecting the target: stop rather than silently truncate meaning.
                overflow = True
                break
            seg = Segment(
                id=f"seg_{uuid.uuid4().hex[:12]}",
                asset_id=asset_id,
                source_start_us=src_start,
                source_duration_us=seg_dur,
                timeline_start_us=timeline_cursor,
                timeline_duration_us=seg_dur,
                role="hook" if not segments else "point",
                reason=unit.reason or "kept_dialogue",
                confidence=round(unit.mean_confidence, 3),
                source_unit_ids=[unit.id],
            )
            segments.append(seg)
            captions.append(
                Caption(
                    id=f"cap_{uuid.uuid4().hex[:12]}",
                    text=unit.text,
                    start_us=timeline_cursor,
                    duration_us=seg_dur,
                )
            )
            included.append(unit.id)
            timeline_cursor += seg_dur

        warnings: list[str] = []
        if overflow:
            warnings.append(
                f"Kept content is longer than {target_us // SECOND_US}s; "
                "later strong lines were left out rather than cutting mid-thought."
            )

        plan = EditPlan(
            id=f"edit_{uuid.uuid4().hex}",
            project_id=project_id,
            style_dna_version=style_dna_version,
            segments=segments,
            captions=captions,
            warnings=warnings,
        )
        errors = validate_edit_plan(plan, {asset_id: media_duration_us})
        if errors:
            # Never emit an invalid plan; record why and skip this target.
            plan.warnings.extend(errors)
            continue
        candidates.append(
            Candidate(
                target_us=target_us, plan=plan, included_unit_ids=included, overflow=overflow
            )
        )

    return CandidateSet(candidates=candidates, removed_unit_ids=removed)
