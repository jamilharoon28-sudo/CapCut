"""Human Judgement Engine (add-on) — layered, local, fallback-safe editorial judgement.

Built and validated phase by phase behind acceptance gates (add-on §19–§20). This
package holds the durable, media-independent foundations that later phases extend:

* ``schemas``     — versioned evidence & decision models with provenance (§6)
* ``calibration`` — project-relative robust scoring + absolute hard blockers (§7.3)
* ``story``       — script → story beats with immutable facts (§8)
* ``confidence``  — automate / recommend / ask-user policy (§11)
* ``evaluation``  — private paired-video manifest + 1–5 rating rubric (§17)

Nothing here is wired into the live render path yet: the current FFmpeg pipeline
is preserved unchanged, and no capability is claimed until it passes its gate on
real footage on the owner's Mac. Level A (deterministic) is always the fallback;
Levels B (local VLM) and C (learned preferences) are additive and gated.
"""

from __future__ import annotations

from .calibration import Baseline, build_baseline, hard_failures, usability_score
from .confidence import Action, Confidence, Decision, decide
from .evaluation import (
    RUBRIC_DIMENSIONS,
    EvaluationManifest,
    ManifestError,
    RubricRating,
    load_manifest,
)
from .schemas import (
    EVIDENCE_SCHEMA_VERSION,
    SemanticEvidence,
    ShotWindow,
    StoryBeat,
    SubjectEvidence,
    TechnicalEvidence,
    WindowEvidence,
    parse_semantic,
)
from .story import extract_immutable_facts, facts_preserved, parse_beats

__all__ = [
    "EVIDENCE_SCHEMA_VERSION",
    "RUBRIC_DIMENSIONS",
    "Action",
    "Baseline",
    "Confidence",
    "Decision",
    "EvaluationManifest",
    "ManifestError",
    "RubricRating",
    "SemanticEvidence",
    "ShotWindow",
    "StoryBeat",
    "SubjectEvidence",
    "TechnicalEvidence",
    "WindowEvidence",
    "build_baseline",
    "decide",
    "extract_immutable_facts",
    "facts_preserved",
    "hard_failures",
    "load_manifest",
    "parse_beats",
    "parse_semantic",
    "usability_score",
]
