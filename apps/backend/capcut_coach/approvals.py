"""Approval log and earned-trust level (increment #4).

Every time the owner approves a finished video, Coach records it. Once enough
videos have been approved, the one-tap "make & save automatically" flow unlocks —
"automatic" is earned from demonstrated reliability, never assumed (CLAUDE.md
rule 14). The count is a simple, auditable tally of real approvals.
"""

from __future__ import annotations

import time
from pathlib import Path

from .db import connect

# The owner must approve this many videos before trusted one-tap auto-save unlocks.
DEFAULT_TRUST_THRESHOLD = 5


def record_approval(db_path: Path, project_id: str | None, candidate: str,
                    *, auto_saved: bool = False) -> None:
    with connect(db_path) as conn:
        conn.execute(
            "INSERT INTO approvals(project_id, candidate, auto_saved, created_at) "
            "VALUES(?,?,?,?)",
            (project_id, candidate, 1 if auto_saved else 0, time.time()),
        )


def approval_count(db_path: Path) -> int:
    with connect(db_path) as conn:
        row = conn.execute("SELECT COUNT(*) AS n FROM approvals").fetchone()
        return int(row["n"]) if row else 0


def trust_state(db_path: Path, threshold: int = DEFAULT_TRUST_THRESHOLD) -> dict:
    n = approval_count(db_path)
    return {
        "approvals": n,
        "threshold": threshold,
        "remaining": max(0, threshold - n),
        "autopilot_unlocked": n >= threshold,
    }
