"""SQLite (WAL) access and forward-only migrations.

No ORM: a one-user local tool does not need one. A ``schema_migrations`` table
records applied versions; the DB is backed up before a migration runs
(contract §9). WAL mode plus ``foreign_keys`` are set on every connection.
"""

from __future__ import annotations

import shutil
import sqlite3
import time
from collections.abc import Callable
from pathlib import Path

# Ordered list of (version, description, sql). Forward-only; never edit an
# already-shipped migration — add a new one.
MIGRATIONS: list[tuple[int, str, str]] = [
    (
        1,
        "initial schema",
        """
        CREATE TABLE projects (
            id            TEXT PRIMARY KEY,
            title         TEXT NOT NULL,
            step          TEXT NOT NULL DEFAULT 'sources',
            status        TEXT NOT NULL DEFAULT 'new',
            created_at    REAL NOT NULL,
            updated_at    REAL NOT NULL,
            style_dna_version TEXT
        );

        CREATE TABLE jobs (
            id            TEXT PRIMARY KEY,
            project_id    TEXT,
            type          TEXT NOT NULL,
            state         TEXT NOT NULL DEFAULT 'queued',
            stage         TEXT,
            percent       REAL,
            heavy         INTEGER NOT NULL DEFAULT 0,
            idempotency_key TEXT,
            input_fingerprint TEXT,
            attempt       INTEGER NOT NULL DEFAULT 0,
            max_attempts  INTEGER NOT NULL DEFAULT 3,
            cancel_requested INTEGER NOT NULL DEFAULT 0,
            error_code    TEXT,
            error_detail  TEXT,
            output_artifact_ids TEXT,
            heartbeat_at  REAL,
            created_at    REAL NOT NULL,
            started_at    REAL,
            finished_at   REAL,
            FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
        );
        CREATE UNIQUE INDEX idx_jobs_idempotency
            ON jobs(type, idempotency_key) WHERE idempotency_key IS NOT NULL;
        CREATE INDEX idx_jobs_state ON jobs(state);

        CREATE TABLE media_assets (
            id            TEXT PRIMARY KEY,
            project_id    TEXT NOT NULL,
            role          TEXT NOT NULL,           -- raw | finished | broll
            original_path TEXT NOT NULL,
            content_hash  TEXT,
            duration_us   INTEGER,
            width         INTEGER,
            height        INTEGER,
            fps_num       INTEGER,
            fps_den       INTEGER,
            has_audio     INTEGER,
            is_vfr        INTEGER,
            rotation      INTEGER,
            created_at    REAL NOT NULL,
            FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
        );
        CREATE INDEX idx_media_project ON media_assets(project_id);

        CREATE TABLE cache_entries (
            key           TEXT PRIMARY KEY,        -- content+tool+config hash
            kind          TEXT NOT NULL,
            path          TEXT NOT NULL,
            bytes         INTEGER NOT NULL DEFAULT 0,
            pinned        INTEGER NOT NULL DEFAULT 0,
            created_at    REAL NOT NULL,
            last_used_at  REAL NOT NULL
        );

        CREATE TABLE claude_decisions (
            key           TEXT PRIMARY KEY,        -- input+model+prompt version
            schema_name   TEXT NOT NULL,
            response_json TEXT NOT NULL,
            created_at    REAL NOT NULL
        );
        """,
    ),
    (
        2,
        "approvals log (trusted autopilot)",
        """
        CREATE TABLE approvals (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id    TEXT,
            candidate     TEXT NOT NULL,
            auto_saved    INTEGER NOT NULL DEFAULT 0,
            created_at    REAL NOT NULL
        );
        CREATE INDEX idx_approvals_created ON approvals(created_at);
        """,
    ),
]


def connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path, isolation_level=None, timeout=30.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    conn.execute("PRAGMA busy_timeout=30000;")
    return conn


def _current_version(conn: sqlite3.Connection) -> int:
    conn.execute(
        "CREATE TABLE IF NOT EXISTS schema_migrations "
        "(version INTEGER PRIMARY KEY, applied_at REAL NOT NULL, description TEXT)"
    )
    row = conn.execute("SELECT MAX(version) AS v FROM schema_migrations").fetchone()
    return int(row["v"]) if row and row["v"] is not None else 0


def _backup_before_migration(db_path: Path, backups_dir: Path | None) -> None:
    if backups_dir is None or not db_path.exists():
        return
    backups_dir.mkdir(parents=True, exist_ok=True)
    stamp = int(time.time())
    dest = backups_dir / f"coach.pre-migration.{stamp}.sqlite3"
    try:
        shutil.copy2(db_path, dest)
    except OSError:
        pass


def migrate(db_path: Path, backups_dir: Path | None = None) -> int:
    """Apply pending migrations. Returns the resulting schema version."""
    current = 0
    with connect(db_path) as conn:
        current = _current_version(conn)
    pending = [m for m in MIGRATIONS if m[0] > current]
    if not pending:
        return current
    _backup_before_migration(db_path, backups_dir)
    with connect(db_path) as conn:
        for version, description, sql in sorted(pending, key=lambda m: m[0]):
            conn.executescript("BEGIN;" + sql + "COMMIT;")
            conn.execute(
                "INSERT INTO schema_migrations(version, applied_at, description) VALUES (?,?,?)",
                (version, time.time(), description),
            )
        return _current_version(conn)


def with_connection(db_path: Path, fn: Callable[[sqlite3.Connection], object]) -> object:
    with connect(db_path) as conn:
        return fn(conn)
