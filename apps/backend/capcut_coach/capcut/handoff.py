"""Guaranteed safe handoff package builder (Phase 7B; test F9).

The handoff always works, independent of direct-write status (ADR-0005). It
prepares a directory with ordered clip instructions, a UTF-8 SRT, a manifest, and
a plain-language HTML guide, then the app opens Finder + CapCut. Actual clip
extraction uses FFmpeg when present; when absent, the package still lists exact
clip ranges so the user can trim in CapCut. This is *assisted handoff*, labelled
honestly — not automatic editing (runbook §11).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from ..media import ffmpeg
from ..media.srt import captions_to_srt, validate_srt
from ..schemas.edit_plan import EditPlan


@dataclass
class HandoffResult:
    directory: Path
    srt_path: Path
    manifest_path: Path
    guide_path: Path
    clips_exported: int
    clips_planned: int
    srt_valid: bool


def build_handoff(
    plan: EditPlan,
    *,
    asset_paths: dict[str, Path],
    out_dir: Path,
    project_title: str = "My Video",
) -> HandoffResult:
    out_dir.mkdir(parents=True, exist_ok=True)
    clips_dir = out_dir / "selected-clips"
    clips_dir.mkdir(exist_ok=True)

    # 1) SRT — official path, UTF-8, validated (F9).
    srt_text = captions_to_srt(plan.captions)
    srt_path = out_dir / "captions.srt"
    srt_path.write_text(srt_text, "utf-8")
    srt_valid = len(validate_srt(srt_text)) == 0

    # 2) Ordered clips (export when FFmpeg is available; always list the plan).
    clip_entries: list[dict] = []
    exported = 0
    have_ffmpeg = ffmpeg.available()
    for i, seg in enumerate(sorted(plan.segments, key=lambda s: s.timeline_start_us), start=1):
        src = asset_paths.get(seg.asset_id)
        entry = {
            "order": i,
            "asset_id": seg.asset_id,
            "source_start_us": seg.source_start_us,
            "source_duration_us": seg.source_duration_us,
            "role": seg.role,
            "caption": next((c.text for c in plan.captions
                             if c.start_us == seg.timeline_start_us), ""),
            "exported_file": None,
        }
        if have_ffmpeg and src and src.exists():
            dst = clips_dir / f"{i:03d}_{seg.role}.mp4"
            try:
                _export_clip(src, dst, seg.source_start_us, seg.source_duration_us)
                entry["exported_file"] = dst.name
                exported += 1
            except Exception:
                entry["exported_file"] = None
        clip_entries.append(entry)

    # 3) Manifest (edit JSON) — records versions for reproducibility (contract §8).
    manifest = {
        "project_title": project_title,
        "edit_plan_id": plan.id,
        "schema_version": plan.schema_version,
        "style_dna_version": plan.style_dna_version,
        "canvas": plan.canvas.model_dump(),
        "clips": clip_entries,
        "captions_srt": srt_path.name,
        "clips_exported": exported,
        "clips_planned": len(clip_entries),
        "warnings": plan.warnings,
        "note": "Assisted handoff. Coach prepared these files; you finish in CapCut.",
    }
    manifest_path = out_dir / "handoff.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), "utf-8")

    # 4) Plain-language guide.
    guide_path = out_dir / "guide.html"
    guide_path.write_text(_render_guide(project_title, clip_entries, srt_path.name, exported,
                                        have_ffmpeg), "utf-8")

    return HandoffResult(
        directory=out_dir,
        srt_path=srt_path,
        manifest_path=manifest_path,
        guide_path=guide_path,
        clips_exported=exported,
        clips_planned=len(clip_entries),
        srt_valid=srt_valid,
    )


def _export_clip(src: Path, dst: Path, start_us: int, dur_us: int) -> None:
    import subprocess

    ff = ffmpeg._resolve("ffmpeg")  # raises FFmpegUnavailable if missing
    start_s = start_us / 1_000_000
    dur_s = dur_us / 1_000_000
    cmd = [ff, "-y", "-ss", f"{start_s:.3f}", "-i", str(src), "-t", f"{dur_s:.3f}",
           "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-c:a", "aac", str(dst)]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=600, check=False)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip()[:200])


def _render_guide(title: str, clips: list[dict], srt_name: str, exported: int,
                  have_ffmpeg: bool) -> str:
    rows = "\n".join(
        f"<li><b>Clip {c['order']}</b> — {c['role']}: "
        f"{'imported file ' + c['exported_file'] if c['exported_file'] else 'trim in CapCut'}"
        f"{(' — “' + c['caption'] + '”') if c['caption'] else ''}</li>"
        for c in clips
    )
    clip_note = (
        "Coach exported the clips into <code>selected-clips/</code> in order."
        if exported else
        "Coach listed the exact clip ranges below; trim each in CapCut."
    )
    return f"""<!doctype html>
<html><head><meta charset="utf-8"><title>{title} — CapCut handoff</title>
<style>body{{font-family:-apple-system,Helvetica,Arial;max-width:640px;margin:40px auto;
color:#15161A;background:#F6F5F2}}h1{{font-size:22px}}li{{margin:8px 0}}
code{{background:#E7E5E0;padding:2px 6px;border-radius:6px}}</style></head>
<body>
<h1>Your edit is ready to finish in CapCut</h1>
<p>{clip_note}</p>
<ol>
<li>Open CapCut and create a <b>new</b> project (or duplicate an existing one).</li>
<li>Drag the clips from <code>selected-clips/</code> onto the timeline in order.</li>
<li>Import captions: <b>Captions → Import</b> and choose <code>{srt_name}</code>.</li>
<li>Review, then export as usual. Coach will detect and review the export.</li>
</ol>
<h2>Clips in order</h2>
<ul>{rows}</ul>
<p style="color:#676A73">This is an assisted handoff. Coach never modified your
originals or your CapCut projects.</p>
</body></html>"""
