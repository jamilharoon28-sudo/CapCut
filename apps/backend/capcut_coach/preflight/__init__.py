"""Smart Preflight (pack doc 19): inspect sources, then tell the owner what Coach
needs — Ready, Ready with suggestions, or a short list of blocking requests.
"""

from .engine import run_preflight
from .schemas import EvidenceMatch, PreflightRequirement, ReadinessReport, RequestCard

__all__ = [
    "EvidenceMatch",
    "PreflightRequirement",
    "ReadinessReport",
    "RequestCard",
    "run_preflight",
]
