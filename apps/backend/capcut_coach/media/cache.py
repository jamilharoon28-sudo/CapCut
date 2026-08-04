"""Content-addressed cache (Phase 2, test F3).

Cache keys combine the *content hash*, the *tool*, and the *config* so that
re-importing identical media performs no duplicate heavy work, and changing the
tool/model/config invalidates only the affected stage. Large files are hashed
incrementally — never loaded whole into memory (F2).
"""

from __future__ import annotations

import hashlib
import json
import os
import time
from dataclasses import dataclass
from pathlib import Path

_CHUNK = 1024 * 1024  # 1 MiB streaming reads


def hash_file(path: Path, *, chunk: int = _CHUNK) -> str:
    """Streaming SHA-256 of a file's bytes. Never loads the whole file."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            block = f.read(chunk)
            if not block:
                break
            h.update(block)
    return h.hexdigest()


def content_fingerprint(path: Path) -> str:
    """Cheap-but-stable fingerprint: size + mtime + a bounded sample hash.

    Used for change detection where a full hash would be wasteful on multi-GB
    media. The full ``hash_file`` is used when integrity matters (immutability
    checks, cleanup gates).
    """
    st = path.stat()
    h = hashlib.sha256()
    h.update(str(st.st_size).encode())
    h.update(str(int(st.st_mtime)).encode())
    with open(path, "rb") as f:
        h.update(f.read(_CHUNK))  # head sample only
        if st.st_size > _CHUNK * 2:
            f.seek(-_CHUNK, os.SEEK_END)
            h.update(f.read(_CHUNK))  # tail sample
    return h.hexdigest()


def cache_key(*, content_hash: str, tool: str, config: dict) -> str:
    """Deterministic key from content + tool + normalised config."""
    payload = json.dumps(config, sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256(f"{content_hash}|{tool}|{payload}".encode()).hexdigest()
    return f"{tool}-{digest[:32]}"


@dataclass
class CacheEntry:
    key: str
    kind: str
    path: Path
    bytes: int
    pinned: bool
    created_at: float
    last_used_at: float


class ContentCache:
    """Filesystem cache with a small SQLite-free JSON index per kind directory."""

    def __init__(self, cache_dir: Path) -> None:
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _index_path(self) -> Path:
        return self.cache_dir / "index.json"

    def _load_index(self) -> dict[str, dict]:
        p = self._index_path()
        if not p.exists():
            return {}
        try:
            return json.loads(p.read_text("utf-8"))
        except (json.JSONDecodeError, OSError):
            return {}

    def _save_index(self, index: dict[str, dict]) -> None:
        tmp = self._index_path().with_suffix(".json.tmp")
        tmp.write_text(json.dumps(index, indent=0), "utf-8")
        os.replace(tmp, self._index_path())

    def get(self, key: str) -> CacheEntry | None:
        index = self._load_index()
        rec = index.get(key)
        if not rec:
            return None
        path = Path(rec["path"])
        if not path.exists():
            # Stale index entry — drop it (miss).
            index.pop(key, None)
            self._save_index(index)
            return None
        rec["last_used_at"] = time.time()
        self._save_index(index)
        return CacheEntry(
            key=key,
            kind=rec["kind"],
            path=path,
            bytes=rec.get("bytes", 0),
            pinned=rec.get("pinned", False),
            created_at=rec.get("created_at", 0.0),
            last_used_at=rec["last_used_at"],
        )

    def put(self, key: str, *, kind: str, path: Path, pinned: bool = False) -> CacheEntry:
        now = time.time()
        size = path.stat().st_size if path.exists() else 0
        index = self._load_index()
        index[key] = {
            "kind": kind,
            "path": str(path),
            "bytes": size,
            "pinned": pinned,
            "created_at": now,
            "last_used_at": now,
        }
        self._save_index(index)
        return CacheEntry(key, kind, path, size, pinned, now, now)

    def total_bytes(self) -> int:
        return sum(rec.get("bytes", 0) for rec in self._load_index().values())

    def evict_to_budget(self, budget_bytes: int) -> list[str]:
        """Remove least-recently-used *unpinned* entries until under budget.

        Only recomputable cache files are removed; pinned outputs and anything
        the index does not own are left untouched (test P6).
        """
        index = self._load_index()
        removed: list[str] = []
        entries = sorted(
            (k for k, r in index.items() if not r.get("pinned")),
            key=lambda k: index[k].get("last_used_at", 0),
        )
        total = self.total_bytes()
        for key in entries:
            if total <= budget_bytes:
                break
            rec = index.pop(key)
            p = Path(rec["path"])
            try:
                if p.exists() and self.cache_dir in p.parents:
                    p.unlink()
            except OSError:
                pass
            total -= rec.get("bytes", 0)
            removed.append(key)
        self._save_index(index)
        return removed
