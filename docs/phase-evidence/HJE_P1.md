# Phase evidence — Human Judgement Engine, Phase 1 (shot windows & technical evidence)

Implements the add-on's Phase 1 (§20): PySceneDetect boundaries + overlapping
candidate windows, multi-frame technical **distributions** (not single-frame
picks), project-relative calibration, optical-flow motion/jerk, and freeze/black
detection. Pure logic is unit-tested here; the FFmpeg decode + PySceneDetect run
on the Mac against real footage. **Nothing is wired into the live render path** —
this is a parallel analysis path used to gather A/B evidence before any default
switchover (add-on §19 product-success rule: ≥70% owner preference, no regression).

## Delivered (implemented + unit-tested)

`apps/backend/capcut_coach/judgement/`:

- **`technical.py`** — `analyse_window(frames)` → `TechnicalEvidence`: variance-of-
  Laplacian focus (median + worst-decile), luma-percentile exposure + clipping,
  relative flicker, camera motion/jerk (OpenCV optical flow when present, else a
  frame-difference fallback), freeze and black ratios. Distributions over the
  window's frames, replacing the current ~6-isolated-frame heuristic (§7.2).
- **`boundaries.py`** — `candidate_windows()` generates overlapping 2–5 s windows
  that snap toward motion valleys so cuts don't land mid-action; `detect_boundaries()`
  uses PySceneDetect's `AdaptiveDetector` when installed and falls back to uniform
  splitting so the pipeline runs anywhere (§7.1/§7.2).
- **`sampling.py`** — pure FFmpeg argv builders for a 540p proxy and for decoding a
  window to low-res grayscale frames (`-noautorotate`, downscaled, low-fps →
  cheap; add-on §16), plus `read_gray_frames()` (Mac step).
- **`report.py`** — the Phase 1 acceptance harness. `python -m
  capcut_coach.judgement.report "<folder>"` probes → boundaries → windows →
  frame decode → technical evidence → project-relative usability, and prints the
  best usable window per clip (with `--json` for full evidence). Read-only.

Calibration reused from Phase 0 (`calibration.py`): robust median/MAD z-scores +
absolute hard blockers — a clip can no longer inflate its own score, and
intentionally-dark footage isn't rejected.

## Test results (this container)

- `tests/test_judgement_phase1.py` — 11 tests (sharp-beats-blurred focus, black/
  frozen/flicker detection, empty-frames blocker, short/long/valley-snap/tiny
  window generation, uniform-shot partition, sampling argv). All passing.
- Full backend: **119 passed, 5 skipped** (FFmpeg-gated), `ruff check capcut_coach`
  clean.

## To produce Phase 1 evidence (run on the M2 Mac)

```bash
cd apps/backend && source .venv/bin/activate
python -m capcut_coach.judgement.report "/path/to/a/real/clips/folder" --json /tmp/p1.json
```

Paste the printed summary (and attach `/tmp/p1.json`). That is the Gate 1 evidence:
window analysis vs the current single-frame selection, severe-failure recall, and
confirmation that no original file changed.

## BLOCKED BY EVIDENCE

- Gate 1 acceptance (window analysis beats single-frame selection on the annotated
  fixtures; high severe-failure recall without rejecting intentionally dark
  footage) — needs FFmpeg + real footage on the Mac via the harness above.
- PySceneDetect boundary quality vs the uniform fallback — measured on the Mac.
- Optical-flow motion/jerk on real camera moves — the numpy fallback is exercised
  here; the OpenCV path is validated on the Mac.

## Related render robustness (shipped this round, live path)

Real `.mov` footage exposed a hard-fail: a clip flagged with audio but carrying a
channel-less/data stream made `[N:a]` "match no streams" and killed the render.
Fixed by (a) counting only audio streams with real channels, (b) an automatic
silent-audio fallback render (a finished, if silent, video beats none — reported
in the result notes), and (c) compressing FFmpeg's giant embedded-graph error
lines so the real message is readable in the UI's "Technical details".
