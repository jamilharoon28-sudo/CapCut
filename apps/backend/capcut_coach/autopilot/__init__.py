"""Full Autopilot (pack doc 20): automatic best-candidate selection.

Scores the Clean/Enhanced/Bold RenderGraphs and picks the highest *safe*
candidate to render as the final, so the owner reviews rather than edits. Final
approval, publishing and cleanup remain separate explicit actions.
"""

from .schemas import AutopilotDecision, CandidateScore
from .select import choose_best

__all__ = ["AutopilotDecision", "CandidateScore", "choose_best"]
