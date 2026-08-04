"""Project repository — Coach analysis projects (never touches source media).

A Coach project references media by path/hash; creating, renaming, or deleting a
project's *analysis* never modifies or removes originals or CapCut projects
(acceptance test S9; Phase 1 exit gate).
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass
from pathlib import Path

from .db import connect
from .security import is_safe_id


@dataclass
class Project:
    id: str
    title: str
    step: str
    status: str
    created_at: float
    updated_at: float
    style_dna_version: str | None

    @classmethod
    def from_row(cls, row) -> Project:
        return cls(
            id=row["id"], title=row["title"], step=row["step"], status=row["status"],
            created_at=row["created_at"], updated_at=row["updated_at"],
            style_dna_version=row["style_dna_version"],
        )

    def to_public(self) -> dict:
        return {
            "id": self.id, "title": self.title, "step": self.step, "status": self.status,
            "style_dna_version": self.style_dna_version,
        }


class ProjectRepository:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path

    def create(self, title: str) -> Project:
        now = time.time()
        pid = f"proj_{uuid.uuid4().hex}"
        with connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO projects(id,title,step,status,created_at,updated_at) "
                "VALUES(?,?,?,?,?,?)",
                (pid, title.strip() or "Untitled", "sources", "new", now, now),
            )
            return Project.from_row(conn.execute("SELECT * FROM projects WHERE id=?", (pid,)).fetchone())

    def get(self, pid: str) -> Project | None:
        if not is_safe_id(pid.replace("proj_", "")):
            return None
        with connect(self.db_path) as conn:
            row = conn.execute("SELECT * FROM projects WHERE id=?", (pid,)).fetchone()
            return Project.from_row(row) if row else None

    def list(self, limit: int = 100) -> list[Project]:
        with connect(self.db_path) as conn:
            rows = conn.execute(
                "SELECT * FROM projects ORDER BY updated_at DESC LIMIT ?", (limit,)
            ).fetchall()
            return [Project.from_row(r) for r in rows]

    def update(self, pid: str, *, title: str | None = None, step: str | None = None,
               status: str | None = None) -> Project | None:
        fields, params = [], []
        if title is not None:
            fields.append("title=?"); params.append(title.strip())
        if step is not None:
            fields.append("step=?"); params.append(step)
        if status is not None:
            fields.append("status=?"); params.append(status)
        if not fields:
            return self.get(pid)
        fields.append("updated_at=?"); params.append(time.time())
        params.append(pid)
        with connect(self.db_path) as conn:
            conn.execute(f"UPDATE projects SET {', '.join(fields)} WHERE id=?", params)
        return self.get(pid)

    def delete_analysis(self, pid: str) -> bool:
        """Delete the Coach project rows (cascades jobs/media/analysis).

        Originals and CapCut projects are untouched — only Coach's own database
        records and derived caches are removed (test S9).
        """
        with connect(self.db_path) as conn:
            cur = conn.execute("DELETE FROM projects WHERE id=?", (pid,))
            return cur.rowcount > 0
