"""FastAPI application factory (Phase 1).

Binds to loopback only and requires a local bearer token on every route except a
tiny liveness probe. Errors carry a stable code + a plain-language message + an
optional Advanced detail (contract §3). The app object is created via
``create_app`` so tests can inject a temporary storage layout.
"""

from __future__ import annotations

from dataclasses import dataclass

from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse

from . import __version__
from .config import Config, StorageLayout, default_layout
from .db import migrate
from .jobs import JobStore
from .logging_setup import configure_logging
from .projects import ProjectRepository
from .security import constant_time_equals, ensure_token


@dataclass
class AppState:
    layout: StorageLayout
    config: Config
    token: str
    projects: ProjectRepository
    jobs: JobStore


def build_state(layout: StorageLayout | None = None) -> AppState:
    layout = (layout or default_layout()).ensure()
    configure_logging(layout.log_path)
    config = Config.load(layout)
    migrate(layout.db_path, backups_dir=layout.backups_dir)
    token = ensure_token(layout)
    jobs = JobStore(layout.db_path)
    jobs.recover_orphans()  # re-queue any job left RUNNING by a crash
    return AppState(
        layout=layout,
        config=config,
        token=token,
        projects=ProjectRepository(layout.db_path),
        jobs=jobs,
    )


def create_app(layout: StorageLayout | None = None) -> FastAPI:
    state = build_state(layout)
    app = FastAPI(title="CapCut Coach", version=__version__, docs_url=None, redoc_url=None)
    app.state.coach = state

    def require_token(authorization: str | None = Header(default=None)) -> None:
        expected = app.state.coach.token
        if not authorization or not authorization.lower().startswith("bearer "):
            raise HTTPException(status_code=401, detail={"code": "missing_token",
                                                         "message": "Local authorisation required."})
        supplied = authorization.split(" ", 1)[1].strip()
        if not constant_time_equals(supplied, expected):
            raise HTTPException(status_code=403, detail={"code": "bad_token",
                                                         "message": "Not authorised."})

    @app.exception_handler(HTTPException)
    async def _http_exc(_: Request, exc: HTTPException) -> JSONResponse:
        detail = exc.detail
        if not isinstance(detail, dict):
            detail = {"code": "error", "message": str(detail)}
        return JSONResponse(status_code=exc.status_code, content={"error": detail})

    # Liveness probe is unauthenticated but reveals nothing sensitive.
    @app.get("/api/v1/health")
    async def health() -> dict:
        return {"ok": True, "version": __version__}

    from .routers import jobs as jobs_router
    from .routers import projects as projects_router
    from .routers import system as system_router

    guard = [Depends(require_token)]
    app.include_router(system_router.router, prefix="/api/v1", dependencies=guard)
    app.include_router(projects_router.router, prefix="/api/v1", dependencies=guard)
    app.include_router(jobs_router.router, prefix="/api/v1", dependencies=guard)
    return app


def run() -> None:  # pragma: no cover - entry point
    """Run uvicorn bound to loopback with an OS-assigned port."""
    import os
    import socket

    import uvicorn

    layout = default_layout().ensure()
    # COACH_PORT lets dev pin the port the Vite proxy expects (default 8787).
    # In production the shell reads the recorded port and finds a free one.
    env_port = os.environ.get("COACH_PORT")
    if env_port:
        port = int(env_port)
    else:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("127.0.0.1", 0))
            port = s.getsockname()[1]
    (layout.support_dir / "port").write_text(str(port), "utf-8")
    uvicorn.run(create_app(layout), host="127.0.0.1", port=port, log_level="info")
