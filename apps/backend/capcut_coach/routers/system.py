"""System endpoints: status, doctor, storage, permissions (contract §4)."""

from __future__ import annotations

import shutil
import sys

from fastapi import APIRouter, Request

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


@router.get("/system/permissions")
async def permissions(request: Request) -> dict:
    state = request.app.state.coach
    return {
        "accessibility_automation_enabled": state.config.get("accessibility_automation_enabled"),
        "screen_help_enabled": state.config.get("screen_help_enabled"),
        # Actual macOS permission state is provided by the Swift bridge on Mac.
        "macos_accessibility_granted": None if sys.platform == "darwin" else False,
    }
