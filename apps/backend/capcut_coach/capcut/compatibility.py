"""CapCut compatibility registry + status state machine (runbook §9; test S3).

Direct writes are only ever enabled for an exact version/build/schema that passed
the ten-run canary. Any app update automatically drops the effective status to
``CANARY_REQUIRED`` or safer.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class CompatibilityStatus(str, Enum):
    READ_ONLY = "READ_ONLY"
    HANDOFF_ONLY = "HANDOFF_ONLY"
    CANARY_REQUIRED = "CANARY_REQUIRED"
    DIRECT_WRITE_CAPTION_ONLY = "DIRECT_WRITE_CAPTION_ONLY"
    DIRECT_WRITE_TEMPLATE_CLONE = "DIRECT_WRITE_TEMPLATE_CLONE"
    BLOCKED = "BLOCKED"


# Statuses that permit any direct mutation. Everything else is read-only/handoff.
DIRECT_WRITE_STATUSES = {
    CompatibilityStatus.DIRECT_WRITE_CAPTION_ONLY,
    CompatibilityStatus.DIRECT_WRITE_TEMPLATE_CLONE,
}


@dataclass
class CompatibilityRecord:
    capcut_semver: str
    build_number: str
    macos_version: str
    app_source: str  # "cc" = CapCut International; else JianYing
    schema_version: str
    timeline_filename: str
    status: CompatibilityStatus = CompatibilityStatus.CANARY_REQUIRED
    supported_operations: list[str] = field(default_factory=list)
    canary_date: str | None = None
    fixture_hash: str | None = None
    canary_runs_passed: int = 0

    @property
    def key(self) -> str:
        return f"{self.capcut_semver}+{self.build_number}/{self.schema_version}/{self.macos_version}"

    def allows_direct_write(self) -> bool:
        return self.status in DIRECT_WRITE_STATUSES and self.canary_runs_passed >= 10

    def to_public(self) -> dict:
        return {
            "key": self.key,
            "capcut_semver": self.capcut_semver,
            "build_number": self.build_number,
            "macos_version": self.macos_version,
            "app_source": self.app_source,
            "schema_version": self.schema_version,
            "status": self.status.value,
            "allows_direct_write": self.allows_direct_write(),
            "canary_runs_passed": self.canary_runs_passed,
            "canary_date": self.canary_date,
        }


def effective_status_after_update(
    previous: CompatibilityRecord, new_semver: str, new_build: str
) -> CompatibilityStatus:
    """A version/build change never keeps a direct-write status (runbook §9)."""
    if (new_semver, new_build) == (previous.capcut_semver, previous.build_number):
        return previous.status
    # Different build than the one that was proven → must re-canary.
    return CompatibilityStatus.CANARY_REQUIRED


def can_mutate(
    record: CompatibilityRecord,
    *,
    direct_write_enabled: bool,
    capcut_running: bool,
    target_is_duplicate: bool,
) -> tuple[bool, str]:
    """Gate every direct mutation against the non-negotiable safety rules.

    Returns (allowed, reason). Refuses if: the flag is off, the version is not
    proven, CapCut is running, or the target is not a Coach duplicate
    (acceptance tests S2, S3, S4).
    """
    if not direct_write_enabled:
        return False, "direct_capcut_write_enabled is off"
    if not record.allows_direct_write():
        return False, f"compatibility status {record.status.value} does not allow direct writes"
    if capcut_running:
        return False, "CapCut is running; writes are refused while it is open"
    if not target_is_duplicate:
        return False, "target is not a Coach duplicate; create a duplicate first"
    return True, "ok"
