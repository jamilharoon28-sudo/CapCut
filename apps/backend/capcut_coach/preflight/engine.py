"""Deterministic preflight: script + footage + audio + assets → ReadinessReport.

Maps every story beat to footage evidence, then decides Ready / Ready-with-
suggestions / Needs-help. Blocks only for material problems (doc 19 §5); never
blocks when a safe honest fallback exists, and always states the fallback and the
quality impact. Missing-footage asks include plain recording directions.

Claude may later refine semantic matching, but this baseline is fully local and
deterministic so preflight always works and is testable.
"""

from __future__ import annotations

from .schemas import (
    EvidenceMatch,
    PreflightRequirement,
    ReadinessReport,
    ReadinessStatus,
    RequestCard,
)

SECOND_US = 1_000_000
MIN_USABLE_US = 1_000_000          # a clip shorter than ~1 s can't hold a beat
LOW_QUALITY_SCORE = 0.35           # below this (when analysed) a shot is weak


def _usable(asset, analyses: dict) -> bool:
    if asset.duration_us < MIN_USABLE_US:
        return False
    an = analyses.get(asset.id)
    return not (an is not None and getattr(an, "score", 1.0) < LOW_QUALITY_SCORE)


def run_preflight(
    catalog,                          # list[CatalogAsset-like]
    *,
    script_beats: list[str] | None = None,
    music_present: bool = False,
    logo_present: bool = False,
    analyses: dict | None = None,
    target_seconds: float = 20.0,
    music_requested: bool = False,    # script/owner asked for a music-led montage
) -> ReadinessReport:
    analyses = analyses or {}
    beats = [b for b in (script_beats or []) if b.strip()]
    usable = [a for a in catalog if _usable(a, analyses)]

    requirements: list[PreflightRequirement] = []
    matches: list[EvidenceMatch] = []
    blocking: list[RequestCard] = []
    suggestions: list[RequestCard] = []

    # --- Requirement 1 (mandatory): at least some usable footage ---
    requirements.append(PreflightRequirement(
        id="footage_present", kind="shot_role", mandatory=True,
        description="Usable raw footage to build the video from.",
        rule=">=1 clip >=1s and not-too-soft"))
    footage_ok = len(usable) >= 1
    matches.append(EvidenceMatch(requirement_id="footage_present", matched=footage_ok,
                                 evidence_ids=[a.id for a in usable[:20]],
                                 confidence=1.0 if footage_ok else 0.0))
    if not footage_ok:
        blocking.append(RequestCard(
            type="no_usable_footage",
            what_needed="Some usable video clips for this video.",
            why="Coach found no clips it can build from.",
            recommended_action="Add a folder (or a .zip) of your raw clips.",
            fallback="None — at least one clip is required.",
            quality_impact="Coach cannot create a video without footage.",
            blocking=True,
            recording_direction="Film 5–8 vertical clips, 3–5 seconds each, holding "
                                "the camera steady for a second before and after each action.",
        ))

    # --- Requirement 2 (mandatory when a script exists): cover each story beat ---
    if beats:
        for i, beat in enumerate(beats):
            rid = f"beat_{i}"
            covered = i < len(usable)
            requirements.append(PreflightRequirement(
                id=rid, kind="story_beat", mandatory=True,
                description=f"A shot for: “{beat}”", rule="one usable clip per beat"))
            matches.append(EvidenceMatch(
                requirement_id=rid, matched=covered,
                evidence_ids=[usable[i].id] if covered else [],
                confidence=0.7 if covered else 0.0,
                note="matched by order (deterministic baseline)"))
        shortfall = max(0, len(beats) - len(usable))
        if shortfall > 0 and footage_ok:
            # Not blocking — Coach can still render by reusing shots — but ask.
            suggestions.append(RequestCard(
                type="missing_shots",
                what_needed=f"{shortfall} more distinct shot{'s' if shortfall != 1 else ''} "
                            "so each line has its own visual.",
                why="Your story has more beats than distinct clips, so some shots repeat.",
                recommended_action="Film the missing shots (directions below).",
                fallback="Coach reuses your strongest clips for the extra beats.",
                quality_impact="Repeated shots read as less polished than the reference.",
                affected_story_beats=[f"beat_{i}" for i in range(len(usable), len(beats))],
                recording_direction="For each missing beat, film a steady 3–5 second vertical "
                                    "close-up of the relevant subject/action, subject centred, "
                                    "holding one second before and after.",
            ))
    else:
        # No script text — offer a story, don't block (montage is a valid fallback).
        suggestions.append(RequestCard(
            type="no_story_text",
            what_needed="A few lines of on-screen copy to tell a story.",
            why="Story-led text is what makes the reference feel like a campaign.",
            recommended_action="Add one short line per shot (your campaign copy).",
            fallback="Coach makes a clean montage with no on-screen text.",
            quality_impact="Without copy the result is a mood montage, not a message.",
        ))

    # --- Brand asset: logo (suggestion, never blocking) ---
    requirements.append(PreflightRequirement(
        id="brand_outro", kind="brand_asset", mandatory=False,
        description="A logo for a branded ending."))
    matches.append(EvidenceMatch(requirement_id="brand_outro", matched=logo_present,
                                 confidence=1.0 if logo_present else 0.0))
    if not logo_present:
        suggestions.append(RequestCard(
            type="missing_logo",
            what_needed="A transparent logo image.",
            why="A branded ending matches your reference style.",
            recommended_action="Add your logo (PNG with transparency is best).",
            fallback="Coach ends with a clean text end-card instead.",
            quality_impact="Without a logo the ending is generic.",
            affected_story_beats=["outro"],
        ))

    # --- Audio: soundtrack (suggestion) when a montage would benefit ---
    requirements.append(PreflightRequirement(
        id="soundtrack", kind="audio", mandatory=False,
        description="A licensed music track for a beat-synced montage."))
    matches.append(EvidenceMatch(requirement_id="soundtrack", matched=music_present,
                                 confidence=1.0 if music_present else 0.0))
    if not music_present and (music_requested or beats):
        suggestions.append(RequestCard(
            type="missing_music",
            what_needed="A music track you own or that's licensed.",
            why="With music, Coach cuts on the beat and the montage feels designed.",
            recommended_action="Add a licensed track (never a copyrighted reference song).",
            fallback="Coach makes a clean edit using your clips' own audio (or silent).",
            quality_impact="Without music, cuts aren't beat-synced.",
        ))

    # --- Quality suggestions from footage analysis ---
    weak = [a.id for a in catalog
            if (an := analyses.get(a.id)) is not None
            and getattr(an, "score", 1.0) < LOW_QUALITY_SCORE]
    if weak and footage_ok:
        suggestions.append(RequestCard(
            type="weak_clips",
            what_needed=f"Sharper replacements for {len(weak)} soft/dark clip"
                        f"{'s' if len(weak) != 1 else ''}.",
            why="Blurry or dark shots lower the finished quality.",
            recommended_action="Re-film those moments with more light and steady focus.",
            fallback="Coach avoids the worst frames and uses each clip's best moment.",
            quality_impact="Soft shots are noticeable next to sharp ones.",
        ))

    # --- Delivery: duration always has a safe default ---
    requirements.append(PreflightRequirement(
        id="delivery", kind="delivery", mandatory=True,
        description=f"Target length (~{int(target_seconds)}s, vertical 1080×1920)."))
    matches.append(EvidenceMatch(requirement_id="delivery", matched=True, confidence=1.0))

    required = [r for r in requirements if r.mandatory]
    resolved_ids = {m.requirement_id for m in matches if m.matched}
    required_resolved = sum(1 for r in required if r.id in resolved_ids)

    if blocking:
        status = ReadinessStatus.NEEDS_HELP
    elif suggestions:
        status = ReadinessStatus.READY_WITH_SUGGESTIONS
    else:
        status = ReadinessStatus.READY

    return ReadinessReport(
        status=status,
        required_resolved=required_resolved,
        required_total=len(required),
        blocking_requests=blocking,
        suggestions=suggestions,
        requirements=requirements,
        matches=matches,
    )
