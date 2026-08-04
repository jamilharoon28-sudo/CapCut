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
import shutil
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
    # Recurse so clips inside subfolders (common after unzipping) are found; skip
    # macOS AppleDouble/resource files (._name) and __MACOSX metadata folders.
    for path in sorted(media_dir.rglob("*")):
        if not path.is_file():
            continue
        if path.suffix.lower() not in VIDEO_EXTS:
            continue
        if path.name.startswith("._") or "__MACOSX" in path.parts:
            continue
        dur_us, has_audio = _probe(path, ffmpeg, ffprobe)
        if dur_us > 0:
            assets.append(CatalogAsset(id=f"asset_{len(assets)}", path=path,
                                       duration_us=dur_us, has_audio=has_audio))
    return assets


def _extract_zip_of_media(zip_path: Path) -> Path:
    """Safely extract a .zip of clips to a sibling folder; return that folder.

    Blocks path traversal, absolute paths, and symlink entries. No size cap (the
    owner's own footage), but nothing is written outside the destination.
    """
    import zipfile

    dest = zip_path.with_suffix("")
    dest.mkdir(parents=True, exist_ok=True)
    dest_resolved = dest.resolve()
    with zipfile.ZipFile(zip_path) as zf:
        for info in zf.infolist():
            name = info.filename
            if name.endswith("/") or name.startswith("__MACOSX") or Path(name).name.startswith("._"):
                continue
            if name.startswith("/") or ".." in Path(name).parts:
                raise RuntimeError(f"unsafe path in archive: {name!r}")
            if ((info.external_attr >> 16) & 0o170000) == 0o120000:
                raise RuntimeError(f"symlink entry refused: {name!r}")
            target = (dest / name).resolve()
            if dest_resolved not in target.parents and target != dest_resolved:
                raise RuntimeError(f"path escapes destination: {name!r}")
            target.parent.mkdir(parents=True, exist_ok=True)
            with zf.open(info) as src, open(target, "wb") as out:
                shutil.copyfileobj(src, out, length=1024 * 1024)
    return dest


MIN_SHOT_US = int(2.0 * SECOND_US)   # keep each shot on screen long enough to read
MAX_SHOT_US = int(5.0 * SECOND_US)
DEFAULT_MAX_CLIPS = 8                 # a watchable montage, not a frantic slideshow


def _select_clips(catalog: list[CatalogAsset], max_clips: int) -> list[CatalogAsset]:
    """Pick up to ``max_clips`` clips, evenly sampled across the folder order."""
    if len(catalog) <= max_clips:
        return catalog
    n = max_clips
    last = len(catalog) - 1
    idxs = sorted({round(i * last / (n - 1)) for i in range(n)})
    return [catalog[i] for i in idxs]


def cold_start_plan(
    catalog: list[CatalogAsset],
    *,
    project_id: str,
    target_us: int = 20 * SECOND_US,
    captions: list[str] | None = None,
    max_clips: int = DEFAULT_MAX_CLIPS,
    per_clip_us: int | None = None,
    analyses: dict[str, object] | None = None,
) -> EditPlan:
    """Sequence clips into a watchable montage near the target duration.

    Cold-start defaults (doc 16 §3): distinct opening, clean cuts, each shot on
    screen 2–5 s. A big folder is *sampled* down to ``max_clips``. When per-clip
    visual ``analyses`` are supplied, each shot starts on its best moment and is
    reframed on the subject (``transform.x``), and clips are ordered by quality
    so the strongest shot opens.
    """
    if not catalog:
        raise ValueError("no usable video clips found in the folder")
    analyses = analyses or {}
    chosen = _select_clips(catalog, max_clips)
    # Order by analysed quality (best first) when we have it — a stronger opening.
    if analyses:
        chosen = sorted(chosen, key=lambda a: -getattr(analyses.get(a.id), "score", 0.0))
    if per_clip_us is None:
        per_clip_us = max(MIN_SHOT_US, min(MAX_SHOT_US, target_us // max(1, len(chosen))))

    from .schemas.edit_plan import Transform

    segments: list[Segment] = []
    caption_events: list[Caption] = []
    cursor = 0
    for i, asset in enumerate(chosen):
        an = analyses.get(asset.id)
        default_lead = min(int(0.3 * SECOND_US), asset.duration_us // 10)
        lead_in = getattr(an, "best_start_us", default_lead)
        lead_in = max(0, min(lead_in, max(0, asset.duration_us - MIN_SHOT_US)))
        seg_dur = min(per_clip_us, asset.duration_us - lead_in)
        if seg_dur <= 0:  # clip shorter than the window: use the whole clip
            seg_dur = asset.duration_us
            lead_in = 0
        crop_x = float(getattr(an, "crop_x_norm", 0.0))
        seg = Segment(
            id=f"seg_{uuid.uuid4().hex[:12]}",
            asset_id=asset.id,
            source_start_us=lead_in,
            source_duration_us=seg_dur,
            timeline_start_us=cursor,
            timeline_duration_us=seg_dur,
            role="hook" if i == 0 else "point",
            reason="best_moment" if an is not None else "cold_start_sequence",
            confidence=float(getattr(an, "score", 0.5)),
            transform=Transform(scale=1.0, x=crop_x, y=0.0),
        )
        segments.append(seg)
        if captions and i < len(captions):
            caption_events.append(Caption(id=f"cap_{uuid.uuid4().hex[:12]}", text=captions[i],
                                          start_us=cursor, duration_us=seg_dur))
        cursor += seg_dur
    return EditPlan(id=f"edit_{uuid.uuid4().hex}", project_id=project_id,
                    segments=segments, captions=caption_events)


@dataclass
class AutoCreateResult:
    candidate_name: str
    output_path: Path
    ok: bool
    detail: str
    qc: list[dict] | None = None   # loudness / true-peak QC findings (may be empty)


def autocreate(
    media_dir: Path,
    out_dir: Path,
    *,
    project_id: str = "cli",
    target_seconds: float = 20.0,
    captions: list[str] | None = None,
    max_clips: int = DEFAULT_MAX_CLIPS,
    mode: str = "auto",          # auto | montage | talking
    smart: bool = True,          # visual moment-picking + subject reframe
    music: Path | None = None,   # music track → beat-synced montage + soundtrack
    logo: Path | None = None,    # logo image → branded outro
    phrase_seconds: float = 2.0,
    approved_music_roots: list[str] | None = None,  # auto-pick a rights-approved track
    make_my_video: bool = False,  # render only the auto-chosen best candidate
    ffmpeg: str | None = None,
    ffprobe: str | None = None,
) -> list[AutoCreateResult]:
    from .toolpaths import ffmpeg_path, ffprobe_path

    ff = ffmpeg or ffmpeg_path()
    if not ff:
        raise RuntimeError("ffmpeg not found; install it (brew install ffmpeg)")
    fp = ffprobe or ffprobe_path()
    # Accept a .zip of clips directly: extract it safely, then use that folder.
    if media_dir.is_file() and media_dir.suffix.lower() == ".zip":
        media_dir = _extract_zip_of_media(media_dir)
    catalog = build_catalog(media_dir, ff, fp)
    if not catalog:
        raise RuntimeError(f"no video clips found in {media_dir}")

    target_us = int(target_seconds * SECOND_US)

    # Autopilot: auto-select a rights-approved music track when none was supplied.
    music_choice = None
    if music is None and approved_music_roots:
        from .music import index_music, select_music
        assets = index_music(approved_music_roots, ff)
        music_choice = select_music(assets, target_seconds=target_seconds,
                                    avoid_vocals=(mode == "talking"))
        if music_choice.chosen is not None:
            music = Path(music_choice.chosen.path)

    # Understand the footage: pick each clip's best moment + subject reframe.
    analyses: dict = {}
    if smart:
        from .analysis.visual import analyse_clip, cv2_available
        if cv2_available():
            for a in catalog:
                try:
                    analyses[a.id] = analyse_clip(a.path, a.duration_us, ff)
                except Exception:
                    pass

    plan = None
    voice_led = False
    # Talking-head mode: keep good spoken lines, cut fillers; captions = real words.
    if mode in ("auto", "talking"):
        from .talking import build_talking_plan, resolve_transcriber
        transcriber = resolve_transcriber()
        if transcriber is not None:
            plan = build_talking_plan(catalog, transcriber=transcriber, project_id=project_id,
                                      target_us=target_us, ffmpeg=ff, analyses=analyses)
            voice_led = plan is not None
        elif mode == "talking":
            raise RuntimeError(
                "Talking-head mode needs a whisper.cpp model. Run scripts/setup-whisper.sh, "
                "then set COACH_WHISPER_MODEL.")

    # Beat-synced campaign montage when a music track is supplied (pack doc 18).
    if plan is None and music is not None:
        from .analysis.audio import analyse_audio
        dna = analyse_audio(music, ff)
        if dna is not None:
            from .montage import build_music_montage
            plan = build_music_montage(catalog, dna, project_id=project_id, target_us=target_us,
                                       phrase_seconds=phrase_seconds, captions=captions,
                                       analyses=analyses)

    if plan is None:  # montage (also the fallback when there is too little speech)
        plan = cold_start_plan(catalog, project_id=project_id, target_us=target_us,
                               captions=captions, max_clips=max_clips, analyses=analyses)
    asset_paths = {a.id: a.path for a in catalog}
    has_audio = {a.id: a.has_audio for a in catalog}
    out_dir.mkdir(parents=True, exist_ok=True)

    from .render.graph import Outro
    outro = Outro(logo_path=logo) if logo is not None else None

    candidates = build_candidates(plan, asset_paths, asset_has_audio=has_audio)
    for cand in candidates:
        # Attach the soundtrack + branded ending to every candidate.
        if music is not None:
            cand.graph.music_path = music
            # Hybrid: when the edit is voice-led, duck the music under speech.
            cand.graph.duck_music = voice_led
        if outro is not None:
            cand.graph.outro = outro

    # Full Autopilot: score the graphs and render ONLY the best safe candidate
    # (doc 20 §6 — don't waste storage rendering every full-res version).
    to_render = candidates
    if make_my_video:
        from .autopilot import choose_best
        decision = choose_best(candidates)
        chosen = next((c for c in candidates if c.name == decision.chosen), candidates[0])
        to_render = [chosen]

    from .media.audioqc import loudness_findings, measure_loudness

    results: list[AutoCreateResult] = []
    for cand in to_render:
        out_path = out_dir / f"{cand.name}.mp4"
        r = render_graph(cand.graph, out_path, ffmpeg=ff)
        ok = r.returncode == 0 and out_path.exists()
        qc: list[dict] = []
        if ok:
            # EBU R128 loudness / true-peak gate on the finished file.
            findings = loudness_findings(measure_loudness(out_path, ff))
            qc = [f.to_public() for f in findings]
        results.append(AutoCreateResult(
            candidate_name=cand.name, output_path=out_path,
            ok=ok, detail="ok" if r.returncode == 0 else r.stderr_tail, qc=qc,
        ))
    return results


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Create 3 video candidates from a folder of clips.")
    ap.add_argument("media_dir", type=Path)
    ap.add_argument("--out", type=Path, default=Path("./coach-candidates"))
    ap.add_argument("--seconds", type=float, default=20.0)
    ap.add_argument("--max-clips", type=int, default=DEFAULT_MAX_CLIPS,
                    help="most shots to include (default 8)")
    ap.add_argument("--mode", choices=["auto", "montage", "talking"], default="auto",
                    help="auto picks talking-head cutting when speech + a whisper model exist")
    ap.add_argument("--no-smart", action="store_true",
                    help="disable visual moment-picking and subject reframe")
    ap.add_argument("--music", type=Path, default=None,
                    help="music track → beat-synced montage cuts + soundtrack")
    ap.add_argument("--logo", type=Path, default=None,
                    help="logo image → a branded outro")
    ap.add_argument("--captions", type=Path, default=None,
                    help="text file, one narrative line per shot")
    ap.add_argument("--music-library", type=Path, default=None,
                    help="a folder of rights-approved tracks Coach may auto-select from")
    ap.add_argument("--make-my-video", action="store_true",
                    help="render only the auto-chosen best candidate (Full Autopilot)")
    args = ap.parse_args(argv)
    caption_lines = None
    if args.captions and args.captions.exists():
        caption_lines = [ln.strip() for ln in args.captions.read_text("utf-8").splitlines()
                         if ln.strip()]
    music_roots = [str(args.music_library)] if args.music_library else None
    try:
        results = autocreate(args.media_dir, args.out, target_seconds=args.seconds,
                             max_clips=args.max_clips, mode=args.mode, smart=not args.no_smart,
                             music=args.music, logo=args.logo, captions=caption_lines,
                             approved_music_roots=music_roots,
                             make_my_video=args.make_my_video)
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
