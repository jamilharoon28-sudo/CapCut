"""End-to-end: POST /autocreate renders 3 candidates and serves the previews."""

from __future__ import annotations

import shutil
import subprocess
import time
from pathlib import Path

import pytest

pytestmark = pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="ffmpeg not installed")


def _make_clips(dirpath: Path, n: int = 3) -> None:
    ff = shutil.which("ffmpeg")
    dirpath.mkdir(parents=True, exist_ok=True)
    for i in range(n):
        subprocess.run(
            [ff, "-y", "-hide_banner", "-loglevel", "error",
             "-f", "lavfi", "-i", f"testsrc=size=640x360:rate=30:duration=3",
             "-f", "lavfi", "-i", f"sine=frequency={300 + 80 * i}:duration=3",
             "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p",
             "-c:a", "aac", "-shortest", str(dirpath / f"clip{i}.mp4")], check=True)


def test_autocreate_endpoint_renders_and_serves(client, tmp_path):
    media = tmp_path / "footage"
    _make_clips(media, 3)

    pid = client.post("/api/v1/projects", json={"title": "Reel"}).json()["id"]
    start = client.post(f"/api/v1/projects/{pid}/autocreate",
                        json={"media_dir": str(media), "target_seconds": 8})
    assert start.status_code == 202
    job_id = start.json()["job_id"]

    # Poll the job to completion (background render thread).
    state = None
    for _ in range(120):
        state = client.get(f"/api/v1/jobs/{job_id}").json()["state"]
        if state in ("succeeded", "failed"):
            break
        time.sleep(0.5)
    assert state == "succeeded"

    cands = client.get(f"/api/v1/projects/{pid}/candidates").json()["candidates"]
    names = {c["name"] for c in cands}
    assert names == {"clean", "enhanced", "bold"}
    assert all(c["ok"] for c in cands)

    # Each preview MP4 is served on loopback and is non-empty.
    for c in cands:
        r = client.get(c["url"])
        assert r.status_code == 200
        assert len(r.content) > 1000


def test_autocreate_rejects_cloud_folder(client):
    pid = client.post("/api/v1/projects", json={"title": "Reel"}).json()["id"]
    r = client.post(f"/api/v1/projects/{pid}/autocreate",
                    json={"media_dir": "/Users/x/Library/CloudStorage/GoogleDrive-a/My Drive"})
    assert r.status_code == 400
    assert r.json()["error"]["code"] in ("cloud_readonly", "bad_folder")
