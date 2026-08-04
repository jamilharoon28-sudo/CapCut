from __future__ import annotations

import os
from pathlib import Path

import pytest

# Force the storage layout into a temp dir before importing app modules so no
# test ever touches a real user's Library.
os.environ.setdefault("COACH_DATA_DIR", "")


@pytest.fixture()
def layout(tmp_path: Path):
    from capcut_coach.config import StorageLayout

    from capcut_coach.db import migrate

    lay = StorageLayout(
        support_dir=tmp_path / "support",
        cache_dir=tmp_path / "cache",
        logs_dir=tmp_path / "logs",
    ).ensure()
    migrate(lay.db_path, backups_dir=lay.backups_dir)
    return lay


@pytest.fixture()
def client(layout):
    from fastapi.testclient import TestClient

    from capcut_coach.app import create_app

    app = create_app(layout)
    token = app.state.coach.token
    c = TestClient(app)
    c.headers.update({"Authorization": f"Bearer {token}"})
    return c
