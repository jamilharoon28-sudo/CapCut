"""The backend serves the built UI so the .app runs as a single process."""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient


def test_serves_index_when_dist_present(tmp_path: Path, monkeypatch):
    from capcut_coach.app import create_app
    from capcut_coach.config import StorageLayout

    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "index.html").write_text("<!doctype html><title>Coach</title>OK", "utf-8")
    monkeypatch.setenv("COACH_FRONTEND_DIST", str(dist))

    layout = StorageLayout(
        support_dir=tmp_path / "s", cache_dir=tmp_path / "c", logs_dir=tmp_path / "l"
    ).ensure()
    client = TestClient(create_app(layout))

    # UI is same-origin and unauthenticated; the API stays guarded.
    assert client.get("/").status_code == 200
    assert "Coach" in client.get("/").text
    assert client.get("/api/v1/system/status").status_code == 401
