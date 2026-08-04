"""Caption-only mutation canary (P0.3, mandatory first gate; tests S2/S5/S6).

The canary is the ONLY way direct writes become enabled, and only after ten
consecutive passes on a **disposable duplicate** with exact-hash restore. This
module implements the *procedure and guards*; the actual mutation step is
deliberately inert unless a proven, matching adapter is registered, so it cannot
run on an untested version or against an original.
"""

from __future__ import annotations

import shutil
from dataclasses import dataclass, field
from pathlib import Path

from ..media.cache import hash_file
from .compatibility import CompatibilityRecord, CompatibilityStatus


class CanaryRefused(RuntimeError):
    """Raised when preconditions for a safe canary are not met."""


@dataclass
class CanaryPreconditions:
    capcut_closed: bool
    is_duplicate: bool
    backup_exists: bool
    version_supported: bool

    def check(self) -> None:
        if not self.capcut_closed:
            raise CanaryRefused("CapCut must be closed before the canary")
        if not self.is_duplicate:
            raise CanaryRefused("the canary must target a disposable duplicate, never an original")
        if not self.backup_exists:
            raise CanaryRefused("a hashed backup must exist before any mutation")
        if not self.version_supported:
            raise CanaryRefused("this CapCut version is write-guarded/unsupported")


@dataclass
class CanaryRunResult:
    run_index: int
    mutated: bool
    restored: bool
    pre_hashes_match: bool
    detail: str = ""


@dataclass
class CanaryReport:
    runs: list[CanaryRunResult] = field(default_factory=list)

    @property
    def passed_runs(self) -> int:
        return sum(1 for r in self.runs if r.restored and r.pre_hashes_match)

    @property
    def all_passed(self) -> bool:
        return len(self.runs) == 10 and self.passed_runs == 10


def hash_tree(root: Path) -> dict[str, str]:
    """Map of relative path -> sha256 for every file under ``root``."""
    out: dict[str, str] = {}
    for p in sorted(root.rglob("*")):
        if p.is_file():
            out[str(p.relative_to(root))] = hash_file(p)
    return out


def backup_project(project_dir: Path, backup_dir: Path) -> dict[str, str]:
    """Copy a project directory to a backup and return its pre-hashes."""
    if backup_dir.exists():
        shutil.rmtree(backup_dir)
    shutil.copytree(project_dir, backup_dir)
    return hash_tree(project_dir)


def restore_project(project_dir: Path, backup_dir: Path) -> None:
    """Restore a project directory exactly from its backup (test S6)."""
    if project_dir.exists():
        shutil.rmtree(project_dir)
    shutil.copytree(backup_dir, project_dir)


def run_canary_once(
    *,
    run_index: int,
    project_dir: Path,
    backup_dir: Path,
    pre: CanaryPreconditions,
    mutate: CaptionMutator | None,
) -> CanaryRunResult:
    """Backup → mutate (if a proven adapter exists) → restore → verify hashes.

    Without a registered, proven mutator the mutation step is skipped and the run
    records ``mutated=False`` — the guard rails still exercise backup/restore.
    """
    pre.check()
    pre_hashes = backup_project(project_dir, backup_dir)

    mutated = False
    detail = ""
    if mutate is not None:
        mutate.apply_caption_change(project_dir)
        mutated = True
        detail = "caption-only mutation applied to duplicate"
    else:
        detail = "no proven adapter; mutation step skipped (safe)"

    restore_project(project_dir, backup_dir)
    post_hashes = hash_tree(project_dir)
    return CanaryRunResult(
        run_index=run_index,
        mutated=mutated,
        restored=True,
        pre_hashes_match=(pre_hashes == post_hashes),
        detail=detail,
    )


class CaptionMutator:
    """Interface for a proven, version-specific caption-only mutator.

    A concrete implementation is registered ONLY for a CapCut version whose
    compatibility record allows direct writes. It must be atomic and reversible.
    This base refuses to run.
    """

    def __init__(self, record: CompatibilityRecord) -> None:
        if record.status not in (
            CompatibilityStatus.DIRECT_WRITE_CAPTION_ONLY,
            CompatibilityStatus.DIRECT_WRITE_TEMPLATE_CLONE,
        ):
            raise CanaryRefused("no proven caption mutator for this version")
        self.record = record

    def apply_caption_change(self, project_dir: Path) -> None:  # pragma: no cover
        raise CanaryRefused("caption mutator not implemented for this exact version")
