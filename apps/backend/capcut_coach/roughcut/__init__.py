"""Deterministic dialogue rough-cut engine (Phase 3). No Claude, no network."""

from .detect import DetectionSettings, segment_transcript
from .plan import CandidateSet, build_candidates

__all__ = ["CandidateSet", "DetectionSettings", "build_candidates", "segment_transcript"]
