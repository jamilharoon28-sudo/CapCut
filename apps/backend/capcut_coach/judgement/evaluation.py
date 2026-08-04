"""Private evaluation manifest + human rating rubric (add-on §17).

Real editorial quality can only be judged against real paired footage, which must
never be committed. This module defines the *format* of a local, git-ignored
manifest that points at the owner's raw/finished examples plus a small gold
annotation set, and the 1–5 rating rubric used for blind A/B comparisons
(add-on §17–§19). The loader refuses any media path that escapes the approved
roots (path-traversal / symlink guard, add-on §5/§18).

Only the schema and synthetic fixtures are committed; the manifest and media stay
on the owner's Mac. This is the harness Phases 1–8 are scored against — no
capability may be claimed until it passes here on real footage.
"""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field

# The seven dimensions rated 1–5 in blind comparisons (add-on §17).
RUBRIC_DIMENSIONS = (
    "shot_choice", "story", "pacing", "framing", "captions", "audio", "overall",
)


class RubricRating(BaseModel):
    shot_choice: int = Field(ge=1, le=5)
    story: int = Field(ge=1, le=5)
    pacing: int = Field(ge=1, le=5)
    framing: int = Field(ge=1, le=5)
    captions: int = Field(ge=1, le=5)
    audio: int = Field(ge=1, le=5)
    overall: int = Field(ge=1, le=5)


class GoldShotMatch(BaseModel):
    """A hand-annotated mapping of one finished shot back to its raw source (§17)."""

    finished_start_us: int = Field(ge=0)
    finished_end_us: int = Field(ge=0)
    raw_asset: str
    raw_start_us: int = Field(ge=0)
    raw_end_us: int = Field(ge=0)
    beat: str | None = None


class GoldAnnotation(BaseModel):
    shot_matches: list[GoldShotMatch] = Field(default_factory=list)
    unusable_windows: list[str] = Field(default_factory=list)
    preferred_opening: str | None = None
    preferred_ending: str | None = None
    captions: list[str] = Field(default_factory=list)
    cta: str | None = None
    rating: RubricRating | None = None


class EvaluationExample(BaseModel):
    id: str
    style: str = "unknown"            # talking_head | montage | campaign | …
    script: str | None = None
    raw_root: str                     # folder of raw clips (local, approved root)
    finished_video: str | None = None  # approved reference final, if any
    baseline_video: str | None = None  # current-engine output for A/B, if any
    gold: GoldAnnotation | None = None


class EvaluationManifest(BaseModel):
    version: int = 1
    examples: list[EvaluationExample] = Field(default_factory=list)


class ManifestError(ValueError):
    pass


def _is_within(child: Path, roots: list[Path]) -> bool:
    child = child.resolve(strict=False)
    for root in roots:
        root = root.resolve(strict=False)
        if child == root or root in child.parents:
            return True
    return False


def load_manifest(
    path: Path,
    *,
    approved_roots: list[Path],
    require_exists: bool = False,
) -> EvaluationManifest:
    """Load and validate a local evaluation manifest.

    Every media path must resolve *inside* an approved root — a manifest can never
    point Coach at arbitrary files (add-on §5/§18). Existence is only checked when
    ``require_exists`` is set (off for schema tests / CI without media).
    """
    if not path.exists():
        raise ManifestError(f"manifest not found: {path}")
    try:
        manifest = EvaluationManifest.model_validate_json(path.read_text("utf-8"))
    except Exception as e:
        raise ManifestError(f"invalid manifest: {e}") from e

    if not approved_roots:
        raise ManifestError("no approved roots given; refusing to resolve media paths")

    for ex in manifest.examples:
        media = [ex.raw_root, ex.finished_video, ex.baseline_video]
        for m in media:
            if not m:
                continue
            p = Path(m).expanduser()
            if not _is_within(p, approved_roots):
                raise ManifestError(f"path escapes approved roots: {m!r}")
            if require_exists and not p.exists():
                raise ManifestError(f"missing media: {m!r}")
    return manifest
