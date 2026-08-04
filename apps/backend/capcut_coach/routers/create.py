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
    auto_save: bool = False         # trusted one-tap: auto-save best (increment #4)


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
    # Accept a folder of clips OR a .zip of clips (extracted safely by autocreate).
    is_zip = real.is_file() and real.suffix.lower() == ".zip"
    if not real.is_dir() and not is_zip:
        raise HTTPException(400, {"code": "bad_folder",
                                  "message": "Choose a folder of clips, or a .zip of clips."})
    if is_cloud_path(real):
        raise HTTPException(400, {"code": "cloud_readonly",
                                  "message": "Cloud/synced folders are read-only; "
                                             "copy clips to a local folder first."})
    # Record the source folder as an approved media root (explicit owner selection).
    root = str(real.parent if is_zip else real)
    roots = list(state.config.get("approved_media_roots") or [])
    if root not in roots:
        roots.append(root)
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


@router.post("/projects/{pid}/make-my-video", status_code=202)
async def make_my_video(pid: str, body: AutoCreateBody, request: Request) -> dict:
    """Full Autopilot (doc 20): auto-pick rights-approved music + best candidate."""
    state = request.app.state.coach
    if not state.projects.get(pid):
        raise HTTPException(404, {"code": "not_found", "message": "Project not found."})
    raw = Path(body.media_dir).expanduser().resolve(strict=False)
    if not raw.is_dir() and not (raw.is_file() and raw.suffix.lower() == ".zip"):
        raise HTTPException(400, {"code": "bad_folder", "message": "That folder wasn't found."})
    if is_cloud_path(raw):
        raise HTTPException(400, {"code": "cloud_readonly",
                                  "message": "Cloud/synced folders are read-only."})
    music_roots = list(state.config.get("approved_music_roots") or [])

    # Trusted one-tap auto-save is only honoured once trust is earned AND a local
    # default output folder is set (increment #4). Otherwise the video is still
    # rendered for the owner to review and save manually.
    auto_save = bool(body.auto_save) and _one_tap_ready(state)

    job = state.jobs.enqueue(type="make_my_video", project_id=pid, heavy=True)

    def _worker() -> None:
        import shutil as _sh

        from ..approvals import record_approval

        out_dir = state.layout.project_dir(pid) / "candidates"
        try:
            state.jobs.transition(job.id, JobState.RUNNING, stage="rendering", percent=5)
            results = autocreate(
                raw, out_dir, project_id=pid, target_seconds=body.target_seconds,
                captions=body.captions, mode=body.mode,
                music=Path(body.music_path) if body.music_path else None,
                logo=Path(body.logo_path) if body.logo_path else None,
                approved_music_roots=music_roots or None, make_my_video=True)
            manifest = [{"name": r.candidate_name, "file": r.output_path.name, "ok": r.ok,
                         "detail": r.detail} for r in results]
            (out_dir / "candidates.json").write_text(json.dumps(manifest, indent=2), "utf-8")
            ok = bool(results) and all(r.ok for r in results)
            if ok and auto_save:
                best = results[0]
                dest = Path(str(state.config.get("default_output_dir"))).expanduser()
                if dest.is_dir() and not is_cloud_path(dest):
                    title = state.projects.get(pid).title or "coach-video"
                    _sh.copy2(best.output_path, dest / f"{title}-{best.candidate_name}.mp4")
                    (out_dir / "approved.json").write_text(
                        json.dumps({"candidate": best.candidate_name, "auto_saved": True}), "utf-8")
                    record_approval(state.layout.db_path, pid, best.candidate_name,
                                    auto_saved=True)
                    state.projects.update(pid, step="review", status="approved")
            detail = "" if ok else next((r.detail for r in results if not r.ok), "")
            state.jobs.transition(job.id, JobState.SUCCEEDED if ok else JobState.FAILED,
                                  stage="done" if ok else "render_error", percent=100,
                                  error_code=None if ok else "render_failed",
                                  error_detail=detail[:400] or None)
        except Exception as e:
            state.jobs.transition(job.id, JobState.FAILED, error_code="autopilot_error",
                                  error_detail=str(e)[:400])

    threading.Thread(target=_worker, daemon=True).start()
    state.projects.update(pid, step="edit", status="rendering")
    return {"job_id": job.id, "auto_save": auto_save}


def _one_tap_ready(state) -> bool:
    """True when trusted one-tap auto-save is unlocked and a local dest is set."""
    from ..approvals import approval_count

    threshold = int(state.config.get("autopilot_trust_threshold") or 5)
    dest = state.config.get("default_output_dir")
    if not dest or is_cloud_path(Path(str(dest)).expanduser()):
        return False
    return approval_count(state.layout.db_path) >= threshold


class PreflightBody(BaseModel):
    media_dir: str
    captions: list[str] | None = None
    target_seconds: float = Field(default=20.0, ge=3, le=180)
    music_path: str | None = None
    logo_path: str | None = None


@router.post("/projects/{pid}/preflight")
async def preflight(pid: str, body: PreflightBody, request: Request) -> dict:
    """Inspect sources and return a readiness report BEFORE rendering (doc 19)."""
    from ..autocreate import _extract_zip_of_media, build_catalog
    from ..preflight import run_preflight
    from ..toolpaths import ffmpeg_path, ffprobe_path

    # Smart Check only inspects a folder; it does not need a persisted project,
    # so the UI can re-scan the active draft (or "adhoc") without creating throwaways.
    ff = ffmpeg_path()
    if not ff:
        raise HTTPException(400, {"code": "no_ffmpeg", "message": "FFmpeg isn't installed yet."})

    raw = Path(body.media_dir).expanduser().resolve(strict=False)
    if raw.is_file() and raw.suffix.lower() == ".zip":
        raw = _extract_zip_of_media(raw)
    if is_cloud_path(raw) or not raw.is_dir():
        raise HTTPException(400, {"code": "bad_folder",
                                  "message": "That folder couldn't be used."})

    catalog = build_catalog(raw, ff, ffprobe_path())
    # Light visual analysis for quality signals (best-effort, capped for speed).
    analyses: dict = {}
    try:
        from ..analysis.visual import analyse_clip, cv2_available
        if cv2_available():
            for a in catalog[:12]:
                try:
                    analyses[a.id] = analyse_clip(a.path, a.duration_us, ff)
                except Exception:
                    pass
    except Exception:
        pass

    report = run_preflight(
        catalog, script_beats=body.captions, analyses=analyses,
        target_seconds=body.target_seconds,
        music_present=bool(body.music_path), logo_present=bool(body.logo_path),
    )
    data = report.model_dump()
    data["headline"] = report.headline
    return data


class ApproveBody(BaseModel):
    candidate: str                       # clean | enhanced | bold
    destination_dir: str | None = None   # optional local folder to save a copy into
    acknowledged: list[str] = Field(default_factory=list)  # ticked review items


@router.post("/projects/{pid}/approve")
async def approve_candidate(pid: str, body: ApproveBody, request: Request) -> dict:
    """Record the chosen candidate and optionally save a copy to a local folder.

    Before saving, every *required* factual-review item (increment #3) must be
    acknowledged — Coach never treats an edit as publish-ready on its own.
    Never modifies originals or cloud content. If a destination is given it must
    be a local (non-cloud) folder; the chosen MP4 is *copied* there.
    """
    import shutil as _sh

    from ..approvals import record_approval
    from ..autocreate import load_edit_state
    from ..editing import build_review_groups, required_ack_ids

    state = request.app.state.coach
    if not state.projects.get(pid):
        raise HTTPException(404, {"code": "not_found", "message": "Project not found."})
    out_dir = state.layout.project_dir(pid) / "candidates"
    src = out_dir / f"{body.candidate}.mp4"
    if not src.exists():
        raise HTTPException(400, {"code": "no_such_candidate",
                                  "message": "That version hasn't been rendered."})

    # Enforce the pre-publish factual review: all required items must be ticked.
    loaded = load_edit_state(out_dir)
    if loaded is not None:
        plan, _catalog, _analyses, ctx = loaded
        groups = build_review_groups(
            plan, music_present=bool(ctx.get("music_path")),
            music_name=ctx.get("music_name"), logo_present=bool(ctx.get("logo_path")))
        missing = required_ack_ids(groups) - set(body.acknowledged)
        if missing:
            raise HTTPException(409, {"code": "review_incomplete",
                                      "message": "Please confirm the highlighted items first.",
                                      "missing": sorted(missing)})

    (out_dir / "approved.json").write_text(
        json.dumps({"candidate": body.candidate}), "utf-8")
    state.projects.update(pid, step="review", status="approved")

    saved_to = None
    if body.destination_dir:
        dest = Path(body.destination_dir).expanduser().resolve(strict=False)
        if is_cloud_path(dest) or not dest.is_dir():
            raise HTTPException(400, {"code": "bad_destination",
                                      "message": "Choose a local folder to save into."})
        target = dest / f"{state.projects.get(pid).title or 'coach-video'}-{body.candidate}.mp4"
        _sh.copy2(src, target)
        saved_to = str(target)

    # Record the approval — this grows earned trust toward one-tap (increment #4).
    record_approval(state.layout.db_path, pid, body.candidate, auto_saved=False)
    return {"approved": body.candidate, "saved_to": saved_to, "originals_touched": False}


@router.get("/projects/{pid}/candidates")
async def list_candidates(pid: str, request: Request) -> dict:
    out_dir = _candidates_dir(request, pid)
    manifest_path = out_dir / "candidates.json"
    if not manifest_path.exists():
        return {"candidates": [], "features": []}
    manifest = json.loads(manifest_path.read_text("utf-8"))
    for item in manifest:
        item["url"] = f"/previews/{pid}/candidates/{item['file']}"
    features = []
    summary_path = out_dir / "summary.json"
    if summary_path.exists():
        features = json.loads(summary_path.read_text("utf-8")).get("features", [])
    return {"candidates": manifest, "features": features}
