"""Post-render editorial endpoints (increments #2 and #3).

* GET  /projects/{pid}/slots                  — timeline slots + alternative clips
* POST /projects/{pid}/slots/{index}/replace  — swap a slot's clip, re-render
* GET  /projects/{pid}/review                  — grouped pre-publish factual review

All operate on the plan Coach persisted at render time; they never re-analyse
footage and never touch originals.
"""

from __future__ import annotations

import threading
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from ..autocreate import load_edit_state, rerender_from_plan
from ..editing import (
    AssetRef,
    build_review_groups,
    build_slots,
    replace_slot,
    required_ack_ids,
)
from ..jobs import JobState

router = APIRouter(tags=["editing"])


def _candidates_dir(request: Request, pid: str) -> Path:
    return request.app.state.coach.layout.project_dir(pid) / "candidates"


def _asset_refs(catalog) -> list[AssetRef]:
    return [AssetRef(id=a.id, name=a.path.name, duration_us=a.duration_us) for a in catalog]


def _load_or_404(request: Request, pid: str):
    state = request.app.state.coach
    if not state.projects.get(pid):
        raise HTTPException(404, {"code": "not_found", "message": "Project not found."})
    loaded = load_edit_state(_candidates_dir(request, pid))
    if loaded is None:
        raise HTTPException(400, {"code": "no_saved_edit",
                                  "message": "This video hasn't been made yet."})
    return loaded


@router.get("/projects/{pid}/slots")
async def list_slots(pid: str, request: Request) -> dict:
    plan, catalog, analyses, _ctx = _load_or_404(request, pid)
    slots = build_slots(plan, _asset_refs(catalog), analyses)
    return {"slots": [s.model_dump() for s in slots]}


class ReplaceBody(BaseModel):
    asset_id: str


@router.post("/projects/{pid}/slots/{index}/replace", status_code=202)
async def replace_slot_clip(pid: str, index: int, body: ReplaceBody, request: Request) -> dict:
    state = request.app.state.coach
    plan, catalog, analyses, _ctx = _load_or_404(request, pid)
    out_dir = _candidates_dir(request, pid)
    try:
        new_plan = replace_slot(plan, _asset_refs(catalog), analyses, index, body.asset_id)
    except KeyError:
        raise HTTPException(400, {"code": "unknown_clip",
                                  "message": "That clip isn't in this project's footage."})
    except IndexError:
        raise HTTPException(400, {"code": "bad_slot", "message": "That slot doesn't exist."})

    # Persist the edited plan, then re-render all three versions so the owner can
    # compare. Originals are untouched — only Coach's derived MP4s are rebuilt.
    (out_dir / "plan.json").write_text(new_plan.model_dump_json(indent=2), "utf-8")
    job = state.jobs.enqueue(type="rerender", project_id=pid, heavy=True)

    def _worker() -> None:
        import json
        try:
            state.jobs.transition(job.id, JobState.RUNNING, stage="rendering", percent=5)
            results = rerender_from_plan(out_dir, make_my_video=False)
            manifest = [{"name": r.candidate_name, "file": r.output_path.name, "ok": r.ok,
                         "detail": r.detail} for r in results]
            (out_dir / "candidates.json").write_text(json.dumps(manifest, indent=2), "utf-8")
            ok = bool(results) and all(r.ok for r in results)
            state.jobs.transition(job.id, JobState.SUCCEEDED if ok else JobState.FAILED,
                                  stage="done" if ok else "render_error", percent=100,
                                  error_code=None if ok else "render_failed")
        except Exception as e:
            state.jobs.transition(job.id, JobState.FAILED, error_code="rerender_error",
                                  error_detail=str(e)[:400])

    threading.Thread(target=_worker, daemon=True).start()
    state.projects.update(pid, step="edit", status="rendering")
    return {"job_id": job.id}


@router.get("/projects/{pid}/review")
async def review_groups(pid: str, request: Request) -> dict:
    plan, _catalog, _analyses, ctx = _load_or_404(request, pid)
    groups = build_review_groups(
        plan, music_present=bool(ctx.get("music_path")),
        music_name=ctx.get("music_name"), logo_present=bool(ctx.get("logo_path")))
    return {"groups": [g.model_dump() for g in groups],
            "required_ack_ids": sorted(required_ack_ids(groups))}
