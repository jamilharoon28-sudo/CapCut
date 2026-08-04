# Semantic Layer — Evidence

Adds footage *understanding* on top of the automation-first renderer (pack docs
15 §6, 16): pick the best moment in each shot, reframe on the subject, and — for
talking-head footage — cut by the spoken words.

## Built
- `analysis/visual.py` — samples frames with FFmpeg and scores each for
  **sharpness** (focus), **exposure**, and **subject** (OpenCV Haar face
  detection). Picks the clip's best-moment start and a horizontal **reframe
  offset** so the subject isn't cut off. OpenCV is optional; without it, analysis
  degrades to centre framing and the montage still renders. No model downloads,
  no network.
- `render/graph.py` + `render/renderer.py` — `RenderClip` carries `crop_x_norm`;
  the crop expression shifts horizontally to keep the subject in frame (safe
  no-op when there is no horizontal room). Ken Burns is modelled but off by
  default (zoompan needs more tuning).
- `autocreate.py` — `smart=True` runs analysis per clip; the montage starts each
  shot on its best moment, reframes on the subject, and **orders clips by quality
  so the strongest shot opens**. New `mode` (auto | montage | talking).
- `talking.py` — **speech-driven editing**: extract audio → whisper.cpp
  transcription → deterministic rough-cut (drop fillers / silence / restarts /
  repeats) → keep the good spoken lines, **captions from the real words**.
  Returns None when there's too little speech, so the montage is the fallback.
  Needs a whisper.cpp model (`scripts/setup-whisper.sh`); unavailable otherwise.

## Verified (FFmpeg 7.0.2 + OpenCV 5.0, this CI run)
- `analyse_clip` scores frames, picks a best moment, returns a reframe offset
  (centre when no face) — runs on real sampled frames.
- Reframe offset renders: the crop expression shifts and produces a valid
  1080×1920 file, fast (no zoompan stall).
- Full `autocreate --smart` end-to-end renders clean/enhanced/bold at 1080×1920.
- Talking mode unit-tested with a stubbed transcriber: fillers dropped, captions
  come from the real words and align 1:1 with kept segments; returns None below
  the speech threshold.

## Test results
```
backend: 56 passed  (adds visual reframe, talking-head cut, smart pipeline)
ruff: All checks passed!
```

## Honest scope
- Face detection is a fast frontal Haar cascade — good for talking-head/subject
  shots, not a general object detector. Non-frontal or crowd shots fall back to
  centre framing.
- Talking-head quality depends on the whisper model chosen (`base.en` is a good
  default); larger models are more accurate but slower.
- Script *beat-by-beat* matching (align a written script to specific clips) is
  the next step; today captions can be supplied per shot, and talking mode uses
  the spoken transcript directly.
