"""Score candidate RenderGraphs and pick the best safe one (pack doc 20 §6).

Deterministic and reproducible: scores story/asset coverage, caption/text
presence, soundtrack + branded ending, source quality, and technical QC, then
returns the highest-scoring candidate. On a tie it prefers the conservative
default (Enhanced) — Coach "selects its best safe candidate."
"""

from __future__ import annotations

from ..qc import run_deterministic_qc
from ..render.candidates import Candidate
from .schemas import AutopilotDecision, CandidateScore

_QC_PENALTY = {"blocker": 0.5, "major": 0.15, "minor": 0.03, "info": 0.0}
_PREFERENCE_ORDER = {"enhanced": 2, "bold": 1, "clean": 0}


def _score_candidate(cand: Candidate) -> CandidateScore:
    g = cand.graph
    reasons: list[str] = []
    score = 0.0

    coverage = min(0.20, len(g.clips) * 0.03)
    score += coverage
    reasons.append(f"{len(g.clips)} shots")

    if g.captions:
        score += 0.20
        reasons.append("on-screen text")
    if g.music_path is not None:
        score += 0.20
        reasons.append("soundtrack")
    if g.outro is not None:
        score += 0.15
        reasons.append("branded ending")
    if g.style.saturation > 1.0:
        score += 0.10
        reasons.append("graded look")

    # Technical QC on the candidate's editorial content (captions/aspect/gaps).
    from ..schemas.edit_plan import Caption, EditPlan, Segment

    plan = EditPlan(
        id=g.edit_plan_id or "cand", project_id=g.project_id,
        segments=[Segment(id=f"s{i}", asset_id=str(i), source_start_us=c.source_start_us,
                          source_duration_us=c.source_duration_us,
                          timeline_start_us=c.timeline_start_us,
                          timeline_duration_us=c.source_duration_us)
                  for i, c in enumerate(g.clips)],
        captions=[Caption(id=f"c{i}", text=cap.text, start_us=cap.start_us,
                         duration_us=cap.duration_us) for i, cap in enumerate(g.captions)],
    )
    findings = run_deterministic_qc(plan, expected_canvas=g.canvas)
    penalty = sum(_QC_PENALTY.get(f.severity, 0.0) for f in findings)
    if penalty:
        score -= penalty
        reasons.append(f"−{penalty:.2f} QC")

    return CandidateScore(name=cand.name, score=round(score, 4), reasons=reasons)


def choose_best(candidates: list[Candidate]) -> AutopilotDecision:
    if not candidates:
        return AutopilotDecision(chosen=None, reason="No candidates to choose from.")
    scores = [_score_candidate(c) for c in candidates]
    # Highest score wins; ties break toward the conservative default (Enhanced).
    best = max(scores, key=lambda s: (s.score, _PREFERENCE_ORDER.get(s.name, 0)))
    reason = f"Chose “{best.name}” — {', '.join(best.reasons)}."
    return AutopilotDecision(chosen=best.name, scores=scores, reason=reason)
