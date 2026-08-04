"""Automation-first one-command creation: raw footage (+ optional script) → three
playable MP4 candidates, no CapCut required (pack docs 15–16; release gate 11).

Pipeline:  media folder -> MediaCatalog -> cold-start EditPlan -> Clean/Enhanced/
Bold RenderGraphs -> rendered MP4s.

Runs deterministically without Claude (doc 15 §10). Uses ffprobe when present and
falls back to parsing ``ffmpeg -i`` so it works wherever FFmpeg is installed.
Never invents spoken text: captions come only from a supplied script/transcript.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
import uuid
from dataclasses import dataclass
from pathlib import Path

from .render.candidates import build_candidates
from .render.renderer import render_graph
from .schemas.edit_plan import Caption, EditPlan, Segment

VIDEO_EXTS = {".mov", ".mp4", ".m4v", ".avi", ".mkv"}
SECOND_US = 1_000_000
_DUR_RE = re.compile(r"Duration:\s*(\d+):(\d+):(\d+\.\d+)")
_AUDIO_RE = re.compile(r"Stream #\d+:\d+.*: Audio:")


@dataclass
class CatalogAsset:
    id: str
    path: Path
    duration_us: int
    has_audio: bool


def _probe(path: Path, ffmpeg: str, ffprobe: str | None) -> tuple[int, bool]:
    """Return (duration_us, has_audio). Prefers ffprobe; falls back to ffmpeg -i."""
    if ffprobe:
        try:
            out = subprocess.run(
                [ffprobe, "-v", "error", "-show_entries",
                 "format=duration:stream=codec_type", "-of", "default=nw=1", str(path)],
                capture_output=True, text=True, timeout=60, check=False,
            ).stdout
            dur = 0.0
            has_audio = "codec_type=audio" in out
            for line in out.splitlines():
                if line.startswith("duration="):
                    dur = float(line.split("=", 1)[1] or 0.0)
            if dur > 0:
                return int(dur * SECOND_US), has_audio
        except (ValueError, subprocess.SubprocessError):
            pass
    # Fallback: parse ffmpeg -i stderr.
    err = subprocess.run([ffmpeg, "-i", str(path)], capture_output=True, text=True,
                         check=False).stderr
    m = _DUR_RE.search(err)
    dur_us = 0
    if m:
        h, mnt, sec = int(m.group(1)), int(m.group(2)), float(m.group(3))
        dur_us = int((h * 3600 + mnt * 60 + sec) * SECOND_US)
    return dur_us, bool(_AUDIO_RE.search(err))


def build_catalog(media_dir: Path, ffmpeg: str, ffprobe: str | None) -> list[CatalogAsset]:
    assets: list[CatalogAsset] = []
    for path in sorted(media_dir.iterdir()):
        if path.suffix.lower() in VIDEO_EXTS and path.is_file():
            dur_us, has_audio = _probe(path, ffmpeg, ffprobe)
            if dur_us > 0:
                assets.append(CatalogAsset(id=f"asset_{len(assets)}", path=path,
                                           duration_us=dur_us, has_audio=has_audio))
    return assets


def cold_start_plan(
    catalog: list[CatalogAsset],
    *,
    project_id: str,
    target_us: int = 20 * SECOND_US,
    captions: list[str] | None = None,
) -> EditPlan:
    """Sequence clips into a montage that lands near the target duration.

    Cold-start defaults (doc 16 §3): visually distinct opening, clean cuts, keep
    each shot short. Each clip contributes one segment from just after its start.
    """
    if not catalog:
        raise ValueError("no usable video clips found in the folder")
    per_clip_us = max(int(1.5 * SECOND_US), min(int(4 * SECOND_US), target_us // len(catalog)))
    segments: list[Segment] = []
    caption_events: list[Caption] = []
    cursor = 0
    for i, asset in enumerate(catalog):
        lead_in = min(int(0.3 * SECOND_US), asset.duration_us // 10)
        seg_dur = min(per_clip_us, asset.duration_us - lead_in)
        if seg_dur <= 0:
            seg_dur = asset.duration_us
            lead_in = 0
        seg = Segment(
            id=f"seg_{uuid.uuid4().hex[:12]}",
            asset_id=asset.id,
            source_start_us=lead_in,
            source_duration_us=seg_dur,
            timeline_start_us=cursor,
            timeline_duration_us=seg_dur,
            role="hook" if i == 0 else "point",
            reason="cold_start_sequence",
            confidence=0.5,
        )
        segments.append(seg)
        if captions and i < len(captions):
            caption_events.append(Caption(id=f"cap_{uuid.uuid4().hex[:12]}", text=captions[i],
                                          start_us=cursor, duration_us=seg_dur))
        cursor += seg_dur
        if cursor >= target_us:
            break
    return EditPlan(id=f"edit_{uuid.uuid4().hex}", project_id=project_id,
                    segments=segments, captions=caption_events)


@dataclass
class AutoCreateResult:
    candidate_name: str
    output_path: Path
    ok: bool
    detail: str


def autocreate(
    media_dir: Path,
    out_dir: Path,
    *,
    project_id: str = "cli",
    target_seconds: float = 20.0,
    captions: list[str] | None = None,
    ffmpeg: str | None = None,
    ffprobe: str | None = None,
) -> list[AutoCreateResult]:
    from .toolpaths import ffmpeg_path, ffprobe_path

    ff = ffmpeg or ffmpeg_path()
    if not ff:
        raise RuntimeError("ffmpeg not found; install it (brew install ffmpeg)")
    fp = ffprobe or ffprobe_path()
    catalog = build_catalog(media_dir, ff, fp)
    if not catalog:
        raise RuntimeError(f"no video clips found in {media_dir}")
    plan = cold_start_plan(catalog, project_id=project_id,
                           target_us=int(target_seconds * SECOND_US), captions=captions)
    asset_paths = {a.id: a.path for a in catalog}
    has_audio = {a.id: a.has_audio for a in catalog}
    out_dir.mkdir(parents=True, exist_ok=True)

    results: list[AutoCreateResult] = []
    for cand in build_candidates(plan, asset_paths, asset_has_audio=has_audio):
        out_path = out_dir / f"{cand.name}.mp4"
        r = render_graph(cand.graph, out_path, ffmpeg=ff)
        results.append(AutoCreateResult(
            candidate_name=cand.name, output_path=out_path,
            ok=(r.returncode == 0 and out_path.exists()),
            detail="ok" if r.returncode == 0 else r.stderr_tail,
        ))
    return results


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Create 3 video candidates from a folder of clips.")
    ap.add_argument("media_dir", type=Path)
    ap.add_argument("--out", type=Path, default=Path("./coach-candidates"))
    ap.add_argument("--seconds", type=float, default=20.0)
    args = ap.parse_args(argv)
    try:
        results = autocreate(args.media_dir, args.out, target_seconds=args.seconds)
    except (RuntimeError, ValueError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    print("Rendered candidates:")
    for r in results:
        mark = "✓" if r.ok else "✗"
        print(f"  {mark} {r.candidate_name}: {r.output_path}  ({r.detail if not r.ok else 'ok'})")
    return 0 if all(r.ok for r in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
