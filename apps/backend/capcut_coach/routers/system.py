"""System endpoints: status, doctor, storage, permissions (contract §4)."""

from __future__ import annotations

import shutil
import sys

from fastapi import APIRouter, HTTPException, Request

from ..capcut.detect import detect_bundle, discover_project_roots

router = APIRouter(tags=["system"])


@router.get("/system/status")
async def status(request: Request) -> dict:
    state = request.app.state.coach
    return {
        "version": request.app.version,
        "processing_mode": state.config.get("processing_mode"),
        "direct_capcut_write_enabled": state.config.get("direct_capcut_write_enabled"),
        "claude_enabled": state.config.get("claude_enabled"),
        "claude_paid_overage_enabled": state.config.get("claude_paid_overage_enabled"),
        "platform": sys.platform,
    }


@router.post("/system/doctor")
async def doctor(request: Request) -> dict:
    """Environment + CapCut probe. Mac-only checks report 'blocked' off-Mac."""
    bundle = detect_bundle()
    checks = {
        "python": {"ok": True, "detail": sys.version.split()[0]},
        "ffmpeg": _tool("ffmpeg"),
        "ffprobe": _tool("ffprobe"),
        "node": _tool("node"),
        "pnpm": _tool("pnpm"),
        "uv": _tool("uv"),
        "claude_cli": _tool("claude"),
        "capcut": {
            "ok": bundle.found,
            "detail": bundle.reason,
            "short_version": bundle.short_version,
            "build": bundle.build,
            "international": bundle.is_international if bundle.found else None,
        },
        "capcut_project_roots": discover_project_roots(),
    }
    macos_only = sys.platform != "darwin"
    return {"platform": sys.platform, "macos_only_checks_blocked": macos_only, "checks": checks}


def _tool(name: str) -> dict:
    found = shutil.which(name)
    return {"ok": bool(found), "detail": "found" if found else "not on PATH"}


@router.get("/system/storage")
async def storage(request: Request) -> dict:
    state = request.app.state.coach
    layout = state.layout
    usage = shutil.disk_usage(str(layout.support_dir))
    return {
        "free_gb": round(usage.free / 1e9, 1),
        "total_gb": round(usage.total / 1e9, 1),
        "minimum_free_space_gb": state.config.get("minimum_free_space_gb"),
        "cache_budget_gb": state.config.get("cache_budget_gb"),
    }


def _dir_size(path) -> int:
    total = 0
    if not path.exists():
        return 0
    for p in path.rglob("*"):
        try:
            if p.is_file():
                total += p.stat().st_size
        except OSError:
            pass
    return total


@router.get("/system/cache/size")
async def cache_size(request: Request) -> dict:
    """Bytes of Coach-created cache/temp that can be safely reclaimed."""
    layout = request.app.state.coach.layout
    return {"bytes": _dir_size(layout.cache_dir), "path_kind": "coach_cache"}


@router.post("/system/cache/cleanup")
async def cache_cleanup(request: Request) -> dict:
    """Delete ONLY the Coach cache dir contents, after an explicit confirm.

    Never touches originals, project outputs, backups, or anything outside the
    Coach cache directory.
    """
    import shutil as _sh

    body = {}
    try:
        body = await request.json()
    except Exception:
        body = {}
    if not body.get("confirm"):
        raise HTTPException(400, {"code": "confirm_required",
                                  "message": "Confirmation is required before removing files."})
    layout = request.app.state.coach.layout
    before = _dir_size(layout.cache_dir)
    for child in layout.cache_dir.glob("*") if layout.cache_dir.exists() else []:
        try:
            if child.is_dir():
                _sh.rmtree(child, ignore_errors=True)
            else:
                child.unlink(missing_ok=True)
        except OSError:
            pass
    freed = before - _dir_size(layout.cache_dir)
    return {"freed_bytes": max(0, freed), "originals_touched": False}


@router.get("/system/permissions")
async def permissions(request: Request) -> dict:
    state = request.app.state.coach
    return {
        "accessibility_automation_enabled": state.config.get("accessibility_automation_enabled"),
        "screen_help_enabled": state.config.get("screen_help_enabled"),
        # Actual macOS permission state is provided by the Swift bridge on Mac.
        "macos_accessibility_granted": None if sys.platform == "darwin" else False,
    }
