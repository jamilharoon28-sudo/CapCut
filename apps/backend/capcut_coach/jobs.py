"""Persisted job state machine and queue (contract §6).

States: queued → running → (succeeded | failed | cancelled); running ⇄ paused.
Heavy media jobs are serialised (one at a time, CLAUDE.md #10); light jobs may
run concurrently. Idempotency keys make duplicate submissions harmless. Because
jobs are persisted, a restart mid-job re-queues cleanly instead of corrupting
state (Phase 1 exit gate).
"""

from __future__ import annotations

import json
import sqlite3
import time
import uuid
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

from .db import connect


class JobState(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    PAUSED = "paused"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


TERMINAL_STATES = {JobState.SUCCEEDED, JobState.FAILED, JobState.CANCELLED}

# Allowed transitions. Any other transition is a programming error and refused.
_ALLOWED: dict[JobState, set[JobState]] = {
    JobState.QUEUED: {JobState.RUNNING, JobState.CANCELLED, JobState.PAUSED},
    JobState.RUNNING: {JobState.SUCCEEDED, JobState.FAILED, JobState.CANCELLED, JobState.PAUSED},
    JobState.PAUSED: {JobState.QUEUED, JobState.RUNNING, JobState.CANCELLED},
    JobState.SUCCEEDED: set(),
    JobState.FAILED: {JobState.QUEUED},  # retry
    JobState.CANCELLED: set(),
}


class JobTransitionError(RuntimeError):
    pass


@dataclass
class Job:
    id: str
    project_id: str | None
    type: str
    state: JobState
    stage: str | None
    percent: float | None
    heavy: bool
    attempt: int
    max_attempts: int
    cancel_requested: bool
    error_code: str | None
    error_detail: str | None
    output_artifact_ids: list[str]
    created_at: float

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> Job:
        return cls(
            id=row["id"],
            project_id=row["project_id"],
            type=row["type"],
            state=JobState(row["state"]),
            stage=row["stage"],
            percent=row["percent"],
            heavy=bool(row["heavy"]),
            attempt=row["attempt"],
            max_attempts=row["max_attempts"],
            cancel_requested=bool(row["cancel_requested"]),
            error_code=row["error_code"],
            error_detail=row["error_detail"],
            output_artifact_ids=json.loads(row["output_artifact_ids"] or "[]"),
            created_at=row["created_at"],
        )

    def to_public(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "project_id": self.project_id,
            "type": self.type,
            "state": self.state.value,
            "stage": self.stage,
            "percent": self.percent,
            "heavy": self.heavy,
            "attempt": self.attempt,
            "max_attempts": self.max_attempts,
            "cancel_requested": self.cancel_requested,
            "error_code": self.error_code,
            "output_artifact_ids": self.output_artifact_ids,
        }


class JobStore:
    """Thin persistence + transition guard over the ``jobs`` table."""

    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path

    def enqueue(
        self,
        *,
        type: str,
        project_id: str | None = None,
        heavy: bool = False,
        idempotency_key: str | None = None,
        input_fingerprint: str | None = None,
        max_attempts: int = 3,
    ) -> Job:
        """Create a queued job. If an idempotency key matches a live job, return it."""
        now = time.time()
        with connect(self.db_path) as conn:
            if idempotency_key is not None:
                existing = conn.execute(
                    "SELECT * FROM jobs WHERE type=? AND idempotency_key=?",
                    (type, idempotency_key),
                ).fetchone()
                if existing is not None:
                    return Job.from_row(existing)
            job_id = f"job_{uuid.uuid4().hex}"
            conn.execute(
                """INSERT INTO jobs
                   (id, project_id, type, state, heavy, idempotency_key,
                    input_fingerprint, attempt, max_attempts, created_at)
                   VALUES (?,?,?,?,?,?,?,0,?,?)""",
                (
                    job_id,
                    project_id,
                    type,
                    JobState.QUEUED.value,
                    1 if heavy else 0,
                    idempotency_key,
                    input_fingerprint,
                    max_attempts,
                    now,
                ),
            )
            row = conn.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
            return Job.from_row(row)

    def get(self, job_id: str) -> Job | None:
        with connect(self.db_path) as conn:
            row = conn.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
            return Job.from_row(row) if row else None

    def list(self, *, project_id: str | None = None, limit: int = 100) -> list[Job]:
        with connect(self.db_path) as conn:
            if project_id:
                rows = conn.execute(
                    "SELECT * FROM jobs WHERE project_id=? ORDER BY created_at DESC LIMIT ?",
                    (project_id, limit),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM jobs ORDER BY created_at DESC LIMIT ?", (limit,)
                ).fetchall()
            return [Job.from_row(r) for r in rows]

    def transition(
        self,
        job_id: str,
        to: JobState,
        *,
        stage: str | None = None,
        percent: float | None = None,
        error_code: str | None = None,
        error_detail: str | None = None,
        output_artifact_ids: list[str] | None = None,
    ) -> Job:
        with connect(self.db_path) as conn:
            row = conn.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
            if row is None:
                raise JobTransitionError(f"unknown job {job_id}")
            current = JobState(row["state"])
            if to not in _ALLOWED[current]:
                raise JobTransitionError(f"illegal transition {current.value} -> {to.value}")
            now = time.time()
            fields = ["state=?", "heartbeat_at=?"]
            params: list[Any] = [to.value, now]
            if stage is not None:
                fields.append("stage=?")
                params.append(stage)
            if percent is not None:
                fields.append("percent=?")
                params.append(max(0.0, min(100.0, percent)))
            if error_code is not None:
                fields.append("error_code=?")
                params.append(error_code)
            if error_detail is not None:
                fields.append("error_detail=?")
                params.append(error_detail)
            if output_artifact_ids is not None:
                fields.append("output_artifact_ids=?")
                params.append(json.dumps(output_artifact_ids))
            if to == JobState.RUNNING and row["started_at"] is None:
                fields.append("started_at=?")
                params.append(now)
                fields.append("attempt=attempt+1")
            if to in TERMINAL_STATES:
                fields.append("finished_at=?")
                params.append(now)
            params.append(job_id)
            conn.execute(f"UPDATE jobs SET {', '.join(fields)} WHERE id=?", params)
            return Job.from_row(conn.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone())

    def request_cancel(self, job_id: str) -> None:
        with connect(self.db_path) as conn:
            conn.execute("UPDATE jobs SET cancel_requested=1 WHERE id=?", (job_id,))

    def retry(self, job_id: str) -> Job:
        job = self.get(job_id)
        if job is None:
            raise JobTransitionError(f"unknown job {job_id}")
        if job.state != JobState.FAILED:
            raise JobTransitionError("only failed jobs can be retried")
        if job.attempt >= job.max_attempts:
            raise JobTransitionError("max attempts exhausted")
        return self.transition(job_id, JobState.QUEUED, error_code=None, error_detail=None)

    def heavy_job_running(self) -> bool:
        with connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT COUNT(*) AS n FROM jobs WHERE heavy=1 AND state=?",
                (JobState.RUNNING.value,),
            ).fetchone()
            return row["n"] > 0

    def recover_orphans(self) -> int:
        """On startup, re-queue jobs stuck in RUNNING from a previous process."""
        with connect(self.db_path) as conn:
            cur = conn.execute(
                "UPDATE jobs SET state=?, started_at=NULL WHERE state=?",
                (JobState.QUEUED.value, JobState.RUNNING.value),
            )
            return cur.rowcount
