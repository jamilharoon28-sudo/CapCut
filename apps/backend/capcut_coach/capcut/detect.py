"""CapCut bundle / version / source detection and project-root discovery (P0.1).

Pure Python. On macOS it reads the app bundle ``Info.plist`` and known project
roots; on other hosts every result is reported as ``blocked`` so callers never
fabricate evidence. No hardcoded single project path — known locations plus
user selection.
"""

from __future__ import annotations

import plistlib
import sys
from dataclasses import dataclass
from pathlib import Path

# Known CapCut app bundle locations (macOS).
KNOWN_APP_PATHS = (
    "/Applications/CapCut.app",
    "~/Applications/CapCut.app",
)

# Known project-root locations (macOS). Discovery also allows user selection.
KNOWN_PROJECT_ROOTS = (
    "~/Movies/CapCut/User Data/Projects/com.lveditor.draft",
    "~/Library/Application Support/CapCut/User Data/Projects/com.lveditor.draft",
)


@dataclass
class CapCutBundle:
    found: bool
    path: str | None = None
    short_version: str | None = None
    build: str | None = None
    app_source: str | None = None  # "cc" (International) or other
    reason: str = ""

    @property
    def is_international(self) -> bool:
        return self.app_source == "cc"


def detect_bundle(candidates: tuple[str, ...] = KNOWN_APP_PATHS) -> CapCutBundle:
    if sys.platform != "darwin":
        return CapCutBundle(found=False, reason="blocked: not macOS")
    for raw in candidates:
        path = Path(raw).expanduser()
        info = path / "Contents" / "Info.plist"
        if info.exists():
            return _read_info_plist(path, info)
    return CapCutBundle(found=False, reason="CapCut.app not found in known locations")


def _read_info_plist(bundle_path: Path, info_plist: Path) -> CapCutBundle:
    try:
        with open(info_plist, "rb") as f:
            data = plistlib.load(f)
    except (OSError, plistlib.InvalidFileException) as e:
        return CapCutBundle(found=False, path=str(bundle_path), reason=f"unreadable Info.plist: {e}")
    return CapCutBundle(
        found=True,
        path=str(bundle_path),
        short_version=data.get("CFBundleShortVersionString"),
        build=data.get("CFBundleVersion"),
        # CapCut International records its source; JianYing differs. Best-effort key.
        app_source=str(data.get("appSource") or data.get("CPAppSource") or "").lower() or None,
        reason="ok",
    )


def read_info_plist_file(info_plist: Path) -> CapCutBundle:
    """Testable entry point: parse a specific Info.plist (used with fixtures)."""
    bundle = info_plist.parent.parent
    return _read_info_plist(bundle, info_plist)


def discover_project_roots(extra: tuple[str, ...] = ()) -> list[str]:
    """Return existing known project roots (macOS). Empty list off-Mac."""
    roots: list[str] = []
    if sys.platform != "darwin":
        return roots
    for raw in (*KNOWN_PROJECT_ROOTS, *extra):
        p = Path(raw).expanduser()
        if p.exists():
            roots.append(str(p))
    return roots
