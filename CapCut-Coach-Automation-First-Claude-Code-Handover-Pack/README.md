# CapCut Coach — Automation-First Claude Code Handover

This is a complete build handover for a private local video-editing coach on one M2 Mac. Its required path costs $0 beyond the owner's existing Claude Max plan and storage: raw footage plus a script become three locally rendered candidates and a final MP4. CapCut Free is optional.

Start with `00_READ_ME_FIRST.md`, then read every numbered file through `18_REFERENCE_QUALITY_AND_AUDIO_DNA.md`. Paste `07_START_PROMPT_FOR_CLAUDE_CODE.md` into Claude Code to begin.

Important properties:

- Works with no finished examples and no CapCut project.
- Learns from chosen drafts, revisions and optional finished examples over time.
- Handles multi-gigabyte inputs incrementally and can read user-selected Google Drive folders without changing cloud content.
- Never requires CapCut Pro, Remotion, paid APIs, hosting or cloud rendering.
- Renders with FFmpeg/ffprobe, VideoToolbox, whisper.cpp and local ASS/SVG/raster assets.
- Understands soundtrack structure and aligns cuts/text reveals to safe musical onsets while protecting speech and mixing levels.
- Never deletes from CapCut Cloud/Space or Google Drive. Cleanup is local, previewed and explicitly approved.
- A CapCut project canary is required only if the owner later chooses to experiment with direct project writing; it never blocks the normal local renderer.

The pack is an implementation specification, not a finished application. Claude Code can build it, but real footage testing and the owner's review are necessary to measure edit quality and time savings.
