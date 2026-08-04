# First Prompt for Claude Code

Open Terminal in the parent folder containing this handover, start Claude Code, and paste everything below.

```text
You are the lead engineer for CapCut Coach, a private, automation-first local video editor for one beginner on an Apple-silicon M2 Mac. Read every file in `CapCut-Coach-Automation-First-Claude-Code-Handover-Pack/` from `00_READ_ME_FIRST.md` through `18_REFERENCE_QUALITY_AND_AUDIO_DNA.md` before changing code. Treat the pack as the product contract. Create and maintain `CLAUDE.md`, a decision log, a requirements-to-tests traceability matrix and an evidence register.

Non-negotiable outcome:
- With only a script and raw footage, and with zero training examples or CapCut projects, Coach automatically parses and groups shots, analyses the footage, builds typed RenderGraphs, renders Clean/Enhanced/Bold previews, accepts a simple choice or revision and renders a final local MP4.
- The primary path must work without CapCut. CapCut Desktop Free is an optional finishing layer only.
- Zero additional cost is a release blocker. Do not require or introduce CapCut Pro, Remotion, a paid API, Claude overage, hosted services, cloud rendering, paid transcription, paid stock or another subscription. Use the owner's existing Claude Max allowance only through the documented spend-stop policy.
- Use FFmpeg/ffprobe, VideoToolbox with software fallback, whisper.cpp, ASS subtitles and locally generated SVG/raster assets. Pin versions/checksums and generate third-party notices.
- Audio intelligence is required. Locally detect speech/music/SFX, tempo, beats, onsets, phrase/energy changes and EBU R128 loudness; align eligible cuts and text reveals without clipping speech/action. Implement `18_REFERENCE_QUALITY_AND_AUDIO_DNA.md` and its same-footage parity test.
- Work incrementally with 2/10/50GB fixtures. Never load a whole large media file into RAM or browser upload it.
- Google Drive and CapCut account/Cloud/Team Space are read-only. Never expose remote write, move, trash, permission or delete methods.
- Never silently delete local originals. Finish & Free Space must show the exact local paths and bytes, check references, require explicit approval and move eligible standalone local raw to macOS Trash without emptying it.
- Every Coach idea is reversible and labelled with reason/confidence. Never invent factual or medical/commercial claims.
- The installed app must be polished and usable without Terminal after bootstrap.

Build in this order:
1. Inspect the workspace and report existing files, tools, assumptions and blockers without printing secrets.
2. Create the repository architecture and plan mapped to acceptance tests.
3. Execute Phase 0 free local-render proof: doctor, five-second render fixture, hardware/software encoder check, storage policy and a zero-example script+raw vertical slice that outputs three previews and one final MP4.
4. Continue Phases 1–6 autonomously where evidence permits. Deliver the useful vertical slice before preference learning or CapCut integration.
5. Add optional learning from choices/exports and paired examples; cold start must remain useful when the profile is empty.
6. Add optional file-based CapCut Free handoff and beginner guidance only after the local renderer works.
7. Keep direct CapCut project writing off. If it is ever proposed, implement it as a separate experimental feature behind an exact-version ten-run duplicate-project canary; it must never block release.
8. Run tests after each slice, record real results and mark hardware/media-dependent work BLOCKED BY EVIDENCE rather than pretending it passed.

The first milestone shown to the owner must be:
script ZIP/document + raw folder + optional owned audio/assets -> automatic shot/take grouping and Audio DNA -> Clean/Enhanced/Bold previews -> choose/revise -> locally rendered final MP4 + SRT + QC report.

Before coding, respond with:
1. your understanding of the finished owner experience;
2. the proposed repository tree;
3. the Phase 0 implementation/test plan;
4. any genuinely blocking owner action (avoid asking for CapCut projects or examples);
5. then begin the unblocked implementation.
```

## Prompt after the first local-render milestone

```text
Audit the milestone against files 00, 05, 15, 16 and 17. Demonstrate a zero-example run without CapCut, Remotion, paid APIs or network rendering. Record source hashes, peak memory, temporary storage, render time and output validation. Fix every release-blocking failure, then implement the four format playbooks, simple review commands, learning from choices/exports and local Finish & Free Space. Do not start direct CapCut project writing.
```

## Prompt for final packaging

```text
Run the full acceptance matrix and a dependency/billing audit. The required path must incur $0 extra and work with CapCut absent. Distinguish passed, failed and evidence-blocked tests. Package a normal Mac application with bootstrap, recovery, uninstall, logs, licences and a beginner guide. Do not claim a time-saving or quality number that was not measured on unseen videos.
```
