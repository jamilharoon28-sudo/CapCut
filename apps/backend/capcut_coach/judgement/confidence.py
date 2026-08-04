"""Calibrated confidence → automate / recommend / ask-user policy (add-on §11).

Confidence is not the VLM's self-reported number. It combines: is every required
story beat covered, is there a hard technical blocker, are the facts certain, and
does the top candidate clearly beat the runner-up. The policy then decides whether
Coach automates, recommends-with-alternatives, or asks the owner one meaningful
question. Pure and deterministic.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Confidence(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class Action(str, Enum):
    AUTOMATE = "automate"
    RECOMMEND = "recommend_with_alternatives"
    ASK_USER = "ask_user"


@dataclass(frozen=True)
class Decision:
    confidence: Confidence
    action: Action
    reasons: list[str]


# A clear win over the runner-up needs at least this normalised margin.
DEFAULT_MARGIN = 0.08


def decide(
    *,
    top_score: float,
    runner_up_score: float,
    required_coverage_complete: bool,
    has_blocker: bool,
    facts_uncertain: bool,
    margin_threshold: float = DEFAULT_MARGIN,
) -> Decision:
    """Map evidence to a confidence level and the action it licenses (§11)."""
    reasons: list[str] = []
    margin = top_score - runner_up_score

    # LOW: anything that makes the result unsafe or unclear.
    if has_blocker:
        reasons.append("a technical blocker is present")
    if not required_coverage_complete:
        reasons.append("a required story beat is uncovered")
    if facts_uncertain:
        reasons.append("a fact/offer is uncertain")
    if reasons:
        return Decision(Confidence.LOW, Action.ASK_USER, reasons)

    # HIGH: evidence agrees and the top choice clearly wins.
    if margin >= margin_threshold:
        return Decision(Confidence.HIGH, Action.AUTOMATE,
                        [f"clear margin over the alternative ({margin:.2f})"])

    # MEDIUM: safe, but alternatives score similarly — keep them for the owner.
    return Decision(Confidence.MEDIUM, Action.RECOMMEND,
                    [f"alternatives score similarly ({margin:.2f} margin)"])
