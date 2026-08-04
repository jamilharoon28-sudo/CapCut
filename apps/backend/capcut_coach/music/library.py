"""Index an owner-approved music folder into rights-eligible MusicAssets.

Local-only, content-hashed. A track is OWNER_APPROVED purely because the owner
placed it inside a folder they explicitly approved; an optional sibling rights
note (``<track>.rights.txt`` or a ``RIGHTS.txt`` in the folder) is recorded for
provenance. Cloud/synced folders are refused. There is NO download/network code
here — selection can only ever act on files already on disk in approved roots.
"""

from __future__ import annotations

import uuid
from pathlib import Path

from ..media.cache import content_fingerprint
from ..security import is_cloud_path
from .schemas import MusicAsset, RightsStatus

AUDIO_EXTS = {".mp3", ".wav", ".m4a", ".aac", ".flac", ".aiff", ".ogg"}
_VOCAL_HINTS = ("vocal", "vox", "sung", "lyrics")


def _rights_note(track: Path) -> str:
    for candidate in (track.with_suffix(track.suffix + ".rights.txt"),
                      track.with_name(track.stem + ".rights.txt"),
                      track.parent / "RIGHTS.txt"):
        if candidate.exists():
            try:
                return candidate.read_text("utf-8", errors="replace").strip()[:500]
            except OSError:
                pass
    return "In owner-approved music folder."


def index_music(approved_roots: list[str] | list[Path], ffmpeg: str | None = None) -> list[MusicAsset]:
    """Return eligible MusicAssets found under the approved roots.

    Analyses tempo/energy/duration when librosa+ffmpeg are available; otherwise
    the track is still indexed (eligible) with zeroed analysis, so a music-led
    edit can proceed with a fixed phrase grid.
    """
    from ..analysis.audio import analyse_audio
    from ..toolpaths import ffmpeg_path

    ff = ffmpeg or ffmpeg_path()
    assets: list[MusicAsset] = []
    seen_hashes: set[str] = set()
    for raw in approved_roots:
        root = Path(raw).expanduser()
        if not root.is_dir() or is_cloud_path(root):
            continue  # cloud/synced or missing roots are never indexed for selection
        for path in sorted(root.rglob("*")):
            if not path.is_file() or path.suffix.lower() not in AUDIO_EXTS:
                continue
            if path.name.startswith("._"):
                continue
            try:
                fp = content_fingerprint(path)
            except OSError:
                continue
            if fp in seen_hashes:
                continue
            seen_hashes.add(fp)
            bpm = duration = energy = 0.0
            if ff is not None:
                dna = analyse_audio(path, ff)
                if dna is not None:
                    bpm, duration, energy = dna.tempo_bpm, dna.duration_s, dna.energy
            vocals = any(h in path.stem.lower() for h in _VOCAL_HINTS)
            assets.append(MusicAsset(
                id=f"music_{uuid.uuid4().hex[:12]}",
                content_hash=fp,
                path=str(path),
                title=path.stem,
                rights_status=RightsStatus.OWNER_APPROVED,
                rights_note=_rights_note(path),
                bpm=round(bpm, 1),
                duration_s=round(duration, 1),
                energy=round(energy, 3),
                vocals=vocals,
            ))
    return assets
