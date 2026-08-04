"""Phase 1 analysis report — run on the Mac to produce real evidence (add-on §20).

Given a folder of clips, this ties the Phase 1 pieces together on real footage:
probe → shot boundaries → candidate windows → decode window frames → technical
distributions → project-relative usability. It prints a human summary and can dump
full JSON evidence. It reads sources only; it never renders or modifies anything.

    python -m capcut_coach.judgement.report "/path/to/clips" [--json out.json]

This is the Phase 1 acceptance harness: it stays BLOCKED BY EVIDENCE until it has
run against the owner's fixtures on the M2 (FFmpeg + optional PySceneDetect).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .boundaries import candidate_windows, detect_boundaries
from .calibration import build_baseline, hard_failures, usability_score
from .sampling import read_gray_frames
from .schemas import ShotWindow, TechnicalEvidence
from .technical import analyse_window


def analyse_asset(
    path: Path, duration_us: int, *, ffmpeg: str,
) -> list[tuple[ShotWindow, TechnicalEvidence]]:
    """Boundaries → windows → per-window technical evidence for one clip."""
    out: list[tuple[ShotWindow, TechnicalEvidence]] = []
    for shot_start, shot_end in detect_boundaries(path, duration_us):
        for win in candidate_windows(path.name, shot_start, shot_end):
            frames = read_gray_frames(path, win.window_start_us, win.duration_us, ffmpeg=ffmpeg)
            out.append((win, analyse_window(frames)))
    return out


def analyse_folder(media_dir: Path) -> dict:
    """Analyse every clip and rank windows against the project baseline.

    Accepts a folder of clips or a ``.zip`` of clips (extracted safely, read-only).
    """
    from ..autocreate import _extract_zip_of_media, build_catalog
    from ..toolpaths import ffmpeg_path, ffprobe_path

    ff = ffmpeg_path()
    if not ff:
        raise RuntimeError("ffmpeg not found (brew install ffmpeg)")
    if media_dir.is_file() and media_dir.suffix.lower() == ".zip":
        media_dir = _extract_zip_of_media(media_dir)
    catalog = build_catalog(media_dir, ff, ffprobe_path())
    if not catalog:
        raise RuntimeError(f"no video clips found in {media_dir}")

    per_asset: dict[str, list[tuple[ShotWindow, TechnicalEvidence]]] = {}
    for asset in catalog:
        per_asset[asset.id] = analyse_asset(asset.path, asset.duration_us, ffmpeg=ff)

    all_focus = [t.focus_median for wins in per_asset.values() for _, t in wins]
    baseline = build_baseline(all_focus)

    assets_report = []
    for asset in catalog:
        scored = []
        for win, tech in per_asset[asset.id]:
            blockers = hard_failures(tech)
            scored.append({
                "window": [win.window_start_us, win.window_end_us],
                "usability": round(usability_score(tech, focus_baseline=baseline), 3),
                "focus_median": round(tech.focus_median, 1),
                "blockers": blockers,
            })
        usable = [s for s in scored if not s["blockers"]]
        best = max(usable, key=lambda s: s["usability"], default=None)
        assets_report.append({
            "asset": asset.path.name,
            "windows_total": len(scored),
            "windows_usable": len(usable),
            "best_window": best,
        })
    return {"clips": len(catalog), "focus_baseline": [baseline.median, baseline.mad],
            "assets": assets_report}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Phase 1 window-analysis report.")
    ap.add_argument("media_dir", type=Path)
    ap.add_argument("--json", type=Path, default=None, help="write full JSON evidence here")
    args = ap.parse_args(argv)
    try:
        report = analyse_folder(args.media_dir)
    except RuntimeError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2

    print(f"Analysed {report['clips']} clips. Focus baseline "
          f"(median, MAD) = {report['focus_baseline']}\n")
    for a in report["assets"]:
        best = a["best_window"]
        where = (f"{best['window'][0] / 1e6:.1f}–{best['window'][1] / 1e6:.1f}s "
                 f"(usability {best['usability']})" if best else "no usable window")
        print(f"  {a['asset']}: {a['windows_usable']}/{a['windows_total']} usable → best {where}")
    if args.json:
        args.json.write_text(json.dumps(report, indent=2), "utf-8")
        print(f"\nFull evidence written to {args.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
