"""Typed configuration and macOS-standard storage layout.

The home path is discovered at runtime — never embedded in source, tests, or
logs (CLAUDE.md). On non-macOS hosts (CI) the layout falls back to a local
``.coach-data`` directory or ``COACH_DATA_DIR`` so the service is testable
anywhere without touching a real user's Library.
"""

from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

APP_NAME = "CapCut Coach"
CONFIG_SCHEMA_VERSION = 1

# Default config per 09_API_CONFIG_AND_STORAGE_CONTRACT.md §2. Secrets never live
# here — the bearer token is a mode-0600 file (see security.py).
DEFAULT_CONFIG: dict[str, Any] = {
    "schema_version": CONFIG_SCHEMA_VERSION,
    "approved_media_roots": [],
    "capcut_project_roots": [],
    "export_roots": [],
    "processing_mode": "balanced",
    "pause_on_battery": True,
    "pause_heavy_work_while_capcut_open": True,
    "minimum_free_space_gb": 30,
    "minimum_free_space_percent": 15,
    "cache_budget_gb": 40,
    "source_cleanup_policy": "ask_after_verified_completion",
    "source_cleanup_destination": "macos_trash",
    "retain_approved_finals": True,
    "retain_scripts": True,
    "retain_learning_capsules": True,
    "whisper_model": "auto-benchmarked",
    "language": "en",
    "claude_enabled": True,
    "claude_paid_overage_enabled": False,
    "screen_help_enabled": False,
    "accessibility_automation_enabled": False,
    "direct_capcut_write_enabled": False,
    "active_style_dna_version": None,
    "active_asset_pack_id": None,
}


def _base_support_dir() -> Path:
    """Resolve the writable application-support root for the current host."""
    override = os.environ.get("COACH_DATA_DIR")
    if override:
        return Path(override).expanduser()
    home = Path.home()
    if sys.platform == "darwin":
        return home / "Library" / "Application Support" / APP_NAME
    # CI / dev fallback — kept inside the repo working dir if HOME is unusual.
    return home / ".coach-data" / APP_NAME


@dataclass(frozen=True)
class StorageLayout:
    """Concrete on-disk paths (09_API_CONFIG_AND_STORAGE_CONTRACT.md §1)."""

    support_dir: Path
    cache_dir: Path
    logs_dir: Path

    @property
    def db_path(self) -> Path:
        return self.support_dir / "coach.sqlite3"

    @property
    def config_path(self) -> Path:
        return self.support_dir / "config.json"

    @property
    def auth_token_path(self) -> Path:
        return self.support_dir / "auth-token"

    @property
    def models_dir(self) -> Path:
        return self.support_dir / "models"

    @property
    def style_dna_dir(self) -> Path:
        return self.support_dir / "style-dna"

    @property
    def asset_packs_dir(self) -> Path:
        return self.support_dir / "asset-packs"

    @property
    def backups_dir(self) -> Path:
        return self.support_dir / "backups"

    @property
    def projects_dir(self) -> Path:
        return self.support_dir / "projects"

    @property
    def compatibility_dir(self) -> Path:
        return self.support_dir / "compatibility"

    @property
    def log_path(self) -> Path:
        return self.logs_dir / "coach.log"

    def project_dir(self, coach_project_id: str) -> Path:
        return self.projects_dir / coach_project_id

    def ensure(self) -> StorageLayout:
        """Create the directory tree. Idempotent."""
        for d in (
            self.support_dir,
            self.cache_dir,
            self.logs_dir,
            self.models_dir,
            self.style_dna_dir,
            self.asset_packs_dir,
            self.backups_dir,
            self.projects_dir,
            self.compatibility_dir,
        ):
            d.mkdir(parents=True, exist_ok=True)
        # Restrictive perms on the support dir (contains the token + db).
        try:
            os.chmod(self.support_dir, 0o700)
        except OSError:
            pass
        return self


def default_layout() -> StorageLayout:
    base = _base_support_dir()
    if sys.platform == "darwin":
        cache = Path.home() / "Library" / "Caches" / APP_NAME
        logs = Path.home() / "Library" / "Logs" / APP_NAME
    else:
        cache = base.parent / f"{APP_NAME} Caches"
        logs = base.parent / f"{APP_NAME} Logs"
    return StorageLayout(support_dir=base, cache_dir=cache, logs_dir=logs)


@dataclass
class Config:
    """Typed settings wrapper. Written through, never hand-edited by users."""

    layout: StorageLayout
    values: dict[str, Any] = field(default_factory=lambda: dict(DEFAULT_CONFIG))

    @classmethod
    def load(cls, layout: StorageLayout | None = None) -> Config:
        layout = (layout or default_layout()).ensure()
        values = dict(DEFAULT_CONFIG)
        if layout.config_path.exists():
            try:
                on_disk = json.loads(layout.config_path.read_text("utf-8"))
                if isinstance(on_disk, dict):
                    values.update({k: on_disk[k] for k in on_disk if k in DEFAULT_CONFIG})
            except (json.JSONDecodeError, OSError):
                # Corrupt config must not crash startup — fall back to defaults.
                pass
        cfg = cls(layout=layout, values=values)
        cfg.save()
        return cfg

    def get(self, key: str) -> Any:
        return self.values.get(key, DEFAULT_CONFIG.get(key))

    def set(self, key: str, value: Any) -> None:
        if key not in DEFAULT_CONFIG:
            raise KeyError(f"unknown config key: {key!r}")
        self.values[key] = value
        self.save()

    def save(self) -> None:
        self.layout.ensure()
        tmp = self.layout.config_path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(self.values, indent=2, sort_keys=True), "utf-8")
        os.replace(tmp, self.layout.config_path)
