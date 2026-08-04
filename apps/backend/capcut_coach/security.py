"""Local security primitives: bearer token and filesystem path safety.

Safety rules enforced here (CLAUDE.md #7, #8, #11, #12; acceptance test S7):
- The API binds to loopback and requires a per-install bearer token.
- Every user-supplied path is resolved (symlinks included) and must live inside
  an explicitly approved root. Traversal, absolute escapes, symlink escapes, and
  shell metacharacters are rejected without executing anything.
- Cloud / synchronised folders are permanently ineligible for cleanup.
"""

from __future__ import annotations

import hmac
import os
import re
import secrets
from dataclasses import dataclass
from pathlib import Path

from .config import StorageLayout

TOKEN_BYTES = 32
# Characters that must never appear in a user-supplied path segment we act on.
_SHELL_METACHARACTERS = set(";|&`$<>\n\r\0")

# Path fragments that indicate a cloud / synchronised location. Cleanup against
# any of these is permanently forbidden (CLAUDE.md #12).
CLOUD_MARKERS = (
    "Library/CloudStorage",
    "Google Drive",
    "GoogleDrive",
    "Dropbox",
    "OneDrive",
    "iCloud Drive",
    "Mobile Documents",  # iCloud
    "com~apple~CloudDocs",
    "CapCut/Cloud",
    "CapCut Cloud",
)


def ensure_token(layout: StorageLayout) -> str:
    """Return the install's bearer token, creating a mode-0600 file if absent."""
    layout.ensure()
    path = layout.auth_token_path
    if path.exists():
        token = path.read_text("utf-8").strip()
        if token:
            return token
    token = secrets.token_urlsafe(TOKEN_BYTES)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(token, "utf-8")
    os.chmod(tmp, 0o600)
    os.replace(tmp, path)
    return token


def constant_time_equals(a: str, b: str) -> bool:
    return hmac.compare_digest(a.encode("utf-8"), b.encode("utf-8"))


class PathSafetyError(ValueError):
    """Raised when a path fails validation. Message is safe to show as Advanced."""


@dataclass(frozen=True)
class PathSafety:
    """Validates user-supplied paths against a set of approved roots."""

    approved_roots: tuple[Path, ...]

    @classmethod
    def from_roots(cls, roots: list[str] | list[Path]) -> PathSafety:
        resolved: list[Path] = []
        for r in roots:
            try:
                resolved.append(Path(r).expanduser().resolve(strict=False))
            except (OSError, RuntimeError):
                continue
        return cls(approved_roots=tuple(resolved))

    def is_within_approved(self, candidate: Path) -> bool:
        for root in self.approved_roots:
            try:
                candidate.relative_to(root)
                return True
            except ValueError:
                continue
        return False

    def validate(self, raw: str, *, must_exist: bool = True) -> Path:
        """Resolve and authorise a path, or raise PathSafetyError.

        Rejects shell metacharacters, resolves symlinks, and requires the real
        path to sit inside an approved root. Never executes anything.
        """
        if raw is None or raw == "":
            raise PathSafetyError("empty path")
        if any(ch in _SHELL_METACHARACTERS for ch in raw):
            raise PathSafetyError("path contains forbidden characters")
        if "\x00" in raw:
            raise PathSafetyError("path contains a null byte")

        candidate = Path(raw).expanduser()
        # Resolve symlinks and ".." fully before authorisation (S7).
        real = candidate.resolve(strict=False)

        if must_exist and not real.exists():
            raise PathSafetyError("path does not exist")

        if not self.approved_roots:
            raise PathSafetyError("no approved roots configured")

        if not self.is_within_approved(real):
            raise PathSafetyError("path is outside every approved root")
        return real


def is_cloud_path(path: Path | str) -> bool:
    """True if the path looks like a cloud / synchronised location.

    Uses the un-resolved textual path *and* the resolved one so a symlink that
    points into a synced folder is still caught.
    """
    texts = [str(path)]
    try:
        texts.append(str(Path(path).expanduser().resolve(strict=False)))
    except (OSError, RuntimeError):
        pass
    for text in texts:
        norm = text.replace("\\", "/")
        for marker in CLOUD_MARKERS:
            if marker.replace("\\", "/") in norm:
                return True
    return False


_SAFE_ID_RE = re.compile(r"^[A-Za-z0-9_-]{1,64}$")


def is_safe_id(value: str) -> bool:
    """Whitelist for ids that become path segments (project ids, job ids)."""
    return bool(_SAFE_ID_RE.match(value or ""))
