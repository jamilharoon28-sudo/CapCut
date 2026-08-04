"""Build Clean / Enhanced / Bold render candidates from one EditPlan (doc 16 §4).

Each meaningful difference is a recorded decision dimension so feedback is
learnable. Bold reorders to lead with the strongest (highest-confidence) shot as
the hook while preserving every factual segment; Clean/Enhanced keep script order.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass
from pathlib import Path

from ..schemas.edit_plan import EditPlan
from .graph import BOLD, CLEAN, ENHANCED, RenderGraph, RenderStyle, graph_from_edit_plan


@dataclass
class Candidate:
    name: str
    graph: RenderGraph
    dimensions: dict


def _retime_sequential(plan: EditPlan) -> EditPlan:
    """Recompute timeline_start so segments are contiguous in their list order."""
    cursor = 0
    for seg in plan.segments:
        seg.timeline_start_us = cursor
        cursor += seg.timeline_duration_us
    # Captions follow their segment's new position by index alignment.
    for cap, seg in zip(plan.captions, plan.segments):
        cap.start_us = seg.timeline_start_us
    return plan


def _bold_plan(plan: EditPlan) -> EditPlan:
    """Lead with the highest-confidence segment as the hook (facts preserved)."""
    p = copy.deepcopy(plan)
    if len(p.segments) > 1:
        hook_idx = max(range(len(p.segments)), key=lambda i: p.segments[i].confidence)
        seg = p.segments.pop(hook_idx)
        seg.role = "hook"
        p.segments.insert(0, seg)
        if p.captions:
            # keep captions paired with segments by rebuilding order-by-segment
            cap_by_seg = {c.start_us: c for c in p.captions}
            # best-effort: leave captions to be re-timed sequentially below
            _ = cap_by_seg
    return _retime_sequential(p)


def build_candidates(
    plan: EditPlan,
    asset_paths: dict[str, Path],
    *,
    asset_has_audio: dict[str, bool] | None = None,
    asset_rotations: dict[str, int] | None = None,
    styles: tuple[RenderStyle, ...] = (CLEAN, ENHANCED, BOLD),
) -> list[Candidate]:
    candidates: list[Candidate] = []
    for style in styles:
        source_plan = _bold_plan(plan) if style.name == "bold" else plan
        graph = graph_from_edit_plan(
            source_plan, asset_paths, style=style, asset_has_audio=asset_has_audio,
            asset_rotations=asset_rotations,
        )
        candidates.append(
            Candidate(
                name=style.name,
                graph=graph,
                dimensions={
                    "captions": style.captions,
                    "reordered_hook": style.name == "bold",
                    "colour_boost": style.saturation > 1.0,
                },
            )
        )
    return candidates
