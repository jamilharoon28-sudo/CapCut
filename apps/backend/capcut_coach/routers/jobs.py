"""Job endpoints (contract §4/§6): list, get, cancel, retry."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from ..jobs import JobTransitionError

router = APIRouter(tags=["jobs"])


@router.get("/jobs")
async def list_jobs(request: Request, project_id: str | None = None) -> dict:
    store = request.app.state.coach.jobs
    return {"jobs": [j.to_public() for j in store.list(project_id=project_id)]}


@router.get("/jobs/{job_id}")
async def get_job(job_id: str, request: Request) -> dict:
    store = request.app.state.coach.jobs
    job = store.get(job_id)
    if not job:
        raise HTTPException(404, {"code": "not_found", "message": "Job not found."})
    return job.to_public()


@router.post("/jobs/{job_id}/cancel")
async def cancel_job(job_id: str, request: Request) -> dict:
    store = request.app.state.coach.jobs
    if not store.get(job_id):
        raise HTTPException(404, {"code": "not_found", "message": "Job not found."})
    store.request_cancel(job_id)
    return {"cancel_requested": True}


@router.post("/jobs/{job_id}/retry")
async def retry_job(job_id: str, request: Request) -> dict:
    store = request.app.state.coach.jobs
    try:
        return store.retry(job_id).to_public()
    except JobTransitionError as e:
        raise HTTPException(409, {"code": "cannot_retry", "message": str(e)})
