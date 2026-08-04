"""Automation-first creation endpoint (pack docs 15–17).

POST /projects/{id}/autocreate  → validates the chosen folder, then renders three
MP4 candidates (Clean/Enhanced/Bold) in a background job. GET .../candidates
returns their preview URLs (served from /previews, loopback-only, same-origin).
"""

from __future__ import annotations

import json
import threading
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from ..autocreate import autocreate
from ..jobs import JobState
from ..security import is_cloud_path

router = APIRouter(tags=["create"])


class AutoCreateBody(BaseModel):
    media_dir: str
    target_seconds: float = Field(default=20.0, ge=3, le=180)
    captions: list[str] | None = None
    max_clips: int = Field(default=8, ge=1, le=40)
    mode: str = Field(default="auto", pattern="^(auto|montage|talking)$")
    music_path: str | None = None   # music track → beat-synced montage
    logo_path: str | None = None    # logo image → branded outro


def _candidates_dir(request: Request, pid: str) -> Path:
    return request.app.state.coach.layout.project_dir(pid) / "candidates"


def _run_job(app_state, pid: str, media_dir: Path, target_seconds: float,
             captions: list[str] | None, max_clips: int, mode: str,
             music: Path | None, logo: Path | None, job_id: str) -> None:
    jobs = app_state.jobs
    out_dir = app_state.layout.project_dir(pid) / "candidates"
    try:
        jobs.transition(job_id, JobState.RUNNING, stage="rendering", percent=5)
        results = autocreate(media_dir, out_dir, project_id=pid,
                             target_seconds=target_seconds, captions=captions,
                             max_clips=max_clips, mode=mode, music=music, logo=logo)
        manifest = [
            {"name": r.candidate_name, "file": r.output_path.name, "ok": r.ok,
             "detail": r.detail}
            for r in results
        ]
        (out_dir / "candidates.json").write_text(json.dumps(manifest, indent=2), "utf-8")
        if all(r.ok for r in results):
            jobs.transition(job_id, JobState.SUCCEEDED, stage="done", percent=100,
                            output_artifact_ids=[r.output_path.name for r in results])
        else:
            jobs.transition(job_id, JobState.FAILED, stage="render_error",
                            error_code="render_failed",
                            error_detail=next((r.detail for r in results if not r.ok), ""))
    except Exception as e:
        jobs.transition(job_id, JobState.FAILED, error_code="autocreate_error",
                        error_detail=str(e)[:400])


@router.post("/projects/{pid}/autocreate", status_code=202)
async def start_autocreate(pid: str, body: AutoCreateBody, request: Request) -> dict:
    state = request.app.state.coach
    if not state.projects.get(pid):
        raise HTTPException(404, {"code": "not_found", "message": "Project not found."})

    raw = Path(body.media_dir).expanduser()
    real = raw.resolve(strict=False)
    if not real.is_dir():
        raise HTTPException(400, {"code": "bad_folder",
                                  "message": "That folder could not be found."})
    if is_cloud_path(real):
        raise HTTPException(400, {"code": "cloud_readonly",
                                  "message": "Cloud/synced folders are read-only; "
                                             "copy clips to a local folder first."})
    # Record the folder as an approved media root (explicit owner selection).
    roots = list(state.config.get("approved_media_roots") or [])
    if str(real) not in roots:
        roots.append(str(real))
        state.config.set("approved_media_roots", roots)

    def _opt_file(raw: str | None) -> Path | None:
        if not raw:
            return None
        p = Path(raw).expanduser().resolve(strict=False)
        if is_cloud_path(p) or not p.is_file():
            raise HTTPException(400, {"code": "bad_file",
                                      "message": "That music/logo file couldn't be used."})
        return p

    music = _opt_file(body.music_path)
    logo = _opt_file(body.logo_path)

    job = state.jobs.enqueue(type="autocreate", project_id=pid, heavy=True)
    thread = threading.Thread(
        target=_run_job,
        args=(state, pid, real, body.target_seconds, body.captions, body.max_clips,
              body.mode, music, logo, job.id),
        daemon=True,
    )
    thread.start()
    state.projects.update(pid, step="edit", status="rendering")
    return {"job_id": job.id}


@router.get("/projects/{pid}/candidates")
async def list_candidates(pid: str, request: Request) -> dict:
    out_dir = _candidates_dir(request, pid)
    manifest_path = out_dir / "candidates.json"
    if not manifest_path.exists():
        return {"candidates": []}
    manifest = json.loads(manifest_path.read_text("utf-8"))
    for item in manifest:
        item["url"] = f"/previews/{pid}/candidates/{item['file']}"
    return {"candidates": manifest}
