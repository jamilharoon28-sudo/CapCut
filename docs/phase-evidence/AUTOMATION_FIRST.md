# Automation-First Render Engine — Evidence

Implements the Automation-First pack (docs 15–17): **Coach renders the final MP4
itself with FFmpeg; CapCut is optional.** Release gate 11 #1 — "from raw + script
only, generate three playable candidates without Terminal or CapCut" — is met.

## Built
- `render/graph.py` — typed `RenderGraph` (single source of truth for preview and
  final) + `RenderStyle` (Clean/Enhanced/Bold) + `graph_from_edit_plan`.
- `render/ass.py` — safe-zone, readable ASS captions (libass).
- `render/renderer.py` — compiles a graph to a deterministic FFmpeg **argv**
  (scale/crop to 1080×1920, per-clip colour eq, concat, burned ASS captions,
  `loudnorm` audio, libx264+aac, faststart). Clips without audio get silence so
  concat never fails. `build_command` is pure; `render_graph` runs it.
- `render/candidates.py` — Clean/Enhanced/Bold from one plan; Bold leads with the
  highest-confidence shot as the hook (facts preserved); each difference recorded
  as a learnable dimension.
- `autocreate.py` — folder → media catalog (ffprobe, or `ffmpeg -i` fallback) →
  cold-start EditPlan → three rendered MP4s. Never invents spoken text.
- `toolpaths.py` — resolves ffmpeg/ffprobe including Homebrew dirs and
  `COACH_FFMPEG/COACH_FFPROBE`, so the GUI `.app` (no shell PATH) finds them.
- API: `POST /projects/{id}/autocreate` (background job) + `GET .../candidates`;
  previews served on loopback at `/previews`. UI: **Create** screen renders and
  plays the three candidates.

## Verified for real (FFmpeg 7.0.2, this CI run)
- CLI `python -m capcut_coach.autocreate <folder>` produced `clean/enhanced/bold`
  MP4s: **1080×1920, 30 fps, H.264 yuv420p, AAC stereo, exact target duration**.
- Caption path burns ASS text (video bitrate rises with text detail).
- End-to-end HTTP test: `POST /autocreate` → job succeeds → 3 candidates served,
  each a non-empty MP4. Cloud/synced folders rejected.

## Test results
```
backend: 52 passed  (incl. real render smoke + end-to-end autocreate API)
ruff: All checks passed!
frontend: 2 passed, tsc clean, production build ok
```

## Honest scope
- Cold-start montage sequencing is deterministic (one segment per clip toward a
  target length). Semantic clip ranking, subject-aware reframing, transitions
  (`xfade`), and Ken Burns (`zoompan`) are designed in the graph model but not yet
  in the default render path — clean cuts render reliably first (doc 15 §10).
- Whisper transcription (for dialogue-driven talking-head cuts) is wired but needs
  the model installed (`scripts/setup-whisper.sh`); the montage path needs no ASR.
- Remotion is deliberately excluded (doc 15 §5): zero additional spend.
