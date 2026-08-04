"""Project endpoints (contract §4). Analysis-only; never touches source media."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

router = APIRouter(tags=["projects"])


class CreateProject(BaseModel):
    title: str = Field(default="Untitled", max_length=200)


class UpdateProject(BaseModel):
    title: str | None = Field(default=None, max_length=200)
    step: str | None = None
    status: str | None = None


@router.get("/projects")
async def list_projects(request: Request) -> dict:
    repo = request.app.state.coach.projects
    return {"projects": [p.to_public() for p in repo.list()]}


@router.post("/projects", status_code=201)
async def create_project(body: CreateProject, request: Request) -> dict:
    repo = request.app.state.coach.projects
    return repo.create(body.title).to_public()


@router.get("/projects/{pid}")
async def get_project(pid: str, request: Request) -> dict:
    repo = request.app.state.coach.projects
    project = repo.get(pid)
    if not project:
        raise HTTPException(404, {"code": "not_found", "message": "Project not found."})
    return project.to_public()


@router.patch("/projects/{pid}")
async def update_project(pid: str, body: UpdateProject, request: Request) -> dict:
    repo = request.app.state.coach.projects
    if not repo.get(pid):
        raise HTTPException(404, {"code": "not_found", "message": "Project not found."})
    return repo.update(pid, title=body.title, step=body.step, status=body.status).to_public()


@router.delete("/projects/{pid}/analysis")
async def delete_analysis(pid: str, request: Request) -> dict:
    """Delete Coach analysis only. Originals and CapCut projects are untouched."""
    repo = request.app.state.coach.projects
    removed = repo.delete_analysis(pid)
    if not removed:
        raise HTTPException(404, {"code": "not_found", "message": "Project not found."})
    return {"deleted": True, "originals_touched": False, "capcut_projects_touched": False}
