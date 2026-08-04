"""Deterministic fallbacks for every Claude-assisted decision (CLAUDE.md #13).

These run when Claude is disabled, unavailable, over allowance, or produces
invalid output. They never call the network. They are intentionally simple and
explainable so the app always produces a coherent result.
"""

from __future__ import annotations

from typing import Any


def fallback_hook_ranking(payload: dict[str, Any]) -> dict[str, Any]:
    """Rank candidates by descending local confidence, then original order."""
    candidates = payload.get("candidates", []) or []
    ordered = sorted(
        candidates,
        key=lambda c: (-float(c.get("confidence", 0.0)), candidates.index(c)),
    )
    return {
        "ranking": [
            {
                "candidate_id": str(c["id"]),
                "rank": i + 1,
                "reason": "highest local confidence (deterministic fallback)",
                "confidence": float(c.get("confidence", 0.0)),
            }
            for i, c in enumerate(ordered)
        ]
    }


def fallback_narrative_plan(payload: dict[str, Any]) -> dict[str, Any]:
    """Keep supplied units in their given order up to the target duration."""
    units = payload.get("units", []) or []
    target = int(payload.get("target_duration_us", 45_000_000))
    ordered_ids: list[str] = []
    total = 0
    for u in units:
        dur = int(u.get("duration_us", 0))
        if ordered_ids and total + dur > target:
            break
        ordered_ids.append(str(u["id"]))
        total += dur
    return {
        "ordered_unit_ids": ordered_ids,
        "roles": [{"unit_id": uid, "role": "point"} for uid in ordered_ids],
        "target_duration_us": target,
        "unresolved_questions": [],
        "confidence": 0.5,
    }


def fallback_beginner_explanation(payload: dict[str, Any]) -> dict[str, Any]:
    step = payload.get("step", {}) or {}
    return {
        "title": step.get("title", "Next step"),
        "action": step.get("action", "Follow the highlighted control in CapCut."),
        "reason": "Keeps your edit on track (deterministic fallback).",
        "expected_result": step.get("expected_result", "The control responds as described."),
        "common_mistake": step.get("common_mistake", "Skipping the confirmation step."),
        "needs_human_mapping": "knowledge_base_step_id" not in step,
    }


def fallback_editorial_qc(payload: dict[str, Any]) -> dict[str, Any]:
    return {"findings": []}


FALLBACKS = {
    "hook_ranking": fallback_hook_ranking,
    "narrative_plan": fallback_narrative_plan,
    "beginner_explanation": fallback_beginner_explanation,
    "editorial_qc": fallback_editorial_qc,
}
