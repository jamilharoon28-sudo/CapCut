# Implementation Plan — Start to Finish

This plan is deliberately gated. Claude Code may continue autonomously through unblocked engineering work, but it must not fake hardware, footage or CapCut evidence. When a phase requires the user's Mac, CapCut project or dataset, create the diagnostic/tooling first, state the exact command/action needed, and stop only that gated lane while continuing independent work.

## Phase 0 — Free local-rendering proof

### Objective

Prove the complete zero-cost path on the owner's M2 Mac before building optional integrations: ingest, local analysis, three previews and final MP4.

### Tasks

#### P0.1 Repository and environment inventory

- Create the repository and `CLAUDE.md`.
- Record macOS version, chip, RAM, architecture and free space.
- Detect CapCut Free if present, but do not require it or locate project roots during normal onboarding.
- Record Claude CLI version/auth state without printing secrets.
- Record Python, Node, `uv`, `pnpm`, FFmpeg and Xcode command-line tool status.

#### P0.2 Local renderer trial

- Install/pin FFmpeg/ffprobe and whisper.cpp using free builds with recorded licences/checksums.
- Render a five-second fixture with a cut, crop, loudness adjustment, ASS caption and SVG/raster graphic.
- Verify H.264 output playback, A/V sync and VideoToolbox encoding with a software fallback.
- Save results to `docs/local-renderer-compatibility.md`.

#### P0.3 Zero-example vertical slice

- Import a short script and raw fixture with no training examples.
- Generate valid Clean, Enhanced and Bold RenderGraphs.
- Render three previews, choose one and render a final local MP4.
- Verify source hashes remain unchanged and no paid/network renderer is invoked.

#### P0.4 Optional CapCut probe — non-blocking

- Only after the local vertical slice works, optionally build a minimal Swift CLI that lists the frontmost CapCut window and accessible controls after permission is granted.
- Test whether important controls expose stable roles, titles, identifiers and actions.
- Record behaviour for project home, timeline, Captions, Audio and Export panels.
- Do not click or change anything in this probe.

#### P0.5 M2 benchmark

- Create a 10-minute 1080p test input.
- Benchmark proxy creation, audio extraction, whisper.cpp model candidates and preview rendering.
- Record wall time, peak memory, output size and whether CapCut remains usable.
- Choose Quiet/Balanced/Maximum defaults based on evidence.

### Deliverables

- `scripts/doctor.sh`
- `docs/local-renderer-compatibility.md`
- `docs/m2-benchmark.md`
- RenderGraph fixture bundle with media excluded/redacted
- three preview MP4s plus one selected final MP4
- optional `apps/mac-bridge` read-only probe

### Exit gate

The zero-example local render must pass without CapCut, Remotion, a paid API or cloud rendering. Optional direct CapCut writes remain disabled unless their separate ten-run canary later passes.

## Phase 1 — Local application foundation

### Objective

Create a reliable local service and beginner-friendly shell before media intelligence.

### Tasks

- Scaffold FastAPI, React/TypeScript/Vite and SQLite.
- Build a normal `CapCut Coach.app` Swift/WKWebView shell and implement `14_PREMIUM_UX_DESIGN_SYSTEM.md`; browser fallback is for recovery.
- Create typed shared API schemas generated from JSON Schema/OpenAPI.
- Implement database migrations and WAL mode.
- Add project/job state machine and persisted queue.
- Implement cancellation, resume and idempotency.
- Bind only to `127.0.0.1` with local authentication.
- Build onboarding wizard and system doctor screen.
- Add notifications and launchd installation/uninstallation.
- Add structured logs with transcript/path redaction.
- Add automatic crash recovery.
- Add a simple status page and hidden Advanced area.
- Add visual-regression fixtures for polished empty/loading/paused/offline/error/success states.

### Exit gate

- `bootstrap.command` installs dependencies without manual code editing.
- Application starts at login and opens from a normal shortcut.
- User can create/rename/delete a Coach analysis project without touching source media.
- Restarting mid-job does not corrupt the database.

## Phase 2 — Media intake, cache and transcription

### Objective

Turn raw local media into searchable, reusable analysis while protecting the M2 and storage.

### Tasks

- Add user-approved root/folder selection.
- Add three-source intake: script pack, raw footage and finished references.
- Parse safe `.docx`/`.pdf`/text/ZIP scripts into typed reel/shot plans.
- Add Drive-for-desktop streamed-folder selection; stage sources read-only and forbid cleanup against cloud-mounted paths.
- Scaffold an optional later OAuth Drive adapter exposing only list/metadata/download operations.
- Implement secure realpath/symlink validation.
- Hash and probe incrementally; never load a complete multi-gigabyte file into memory.
- Add chunked/resumable staging and 2/10/50 GB fixtures.
- Detect VFR, missing audio, rotation and unsupported codecs.
- Generate 720p proxies using VideoToolbox when supported.
- Extract mono 16 kHz audio.
- Integrate whisper.cpp with model manager/checksums.
- Add word-level transcript, VAD, confidence and custom vocabulary correction.
- Generate SRT, waveform, thumbnails and contact sheet.
- Add scene boundary extraction.
- Cache outputs by content+tool+configuration hash.
- Add storage budget and cleanup UI.
- Add learning-capsule generation and local-only **Finish & Free Space** preview; source cleanup remains disabled until Phase 5 evidence exists.

### Exit gate

- Re-importing identical media performs no duplicate heavy work.
- A 10-minute 1080p clip completes on Balanced mode without concurrent heavy jobs.
- Transcript, proxy and SRT are visible and editable in the UI.
- Original file hashes remain unchanged.

## Phase 3 — Deterministic rough cut and visual playbooks

### Objective

Deliver useful scripted, montage, talking-head and testimonial drafts before preference learning or CapCut integration.

### Tasks

- Segment transcript into phrases/sentences.
- Detect silence, filler words, repeated phrases and restart attempts.
- Implement adjustable natural-cut margins.
- Detect clipped phoneme/breath risk.
- Build internal edit-plan schema and validator.
- Render a preview and a removed-content preview.
- Add manual transcript-based keep/remove controls.
- Generate 30/45/60-second candidates where possible.
- Export selected individual clips, cleaned audio and SRT.
- Implement the four format playbooks in `15_AUTOMATION_FIRST_ENGINE.md`.
- Compile typed RenderGraphs and render Clean/Enhanced/Bold previews locally.

### Exit gate

- All edit-plan source ranges exist and do not overlap illegally.
- No generated cut begins/ends outside media duration.
- User can restore any removed phrase in one click.
- Preview audio has no obvious clicks across the golden fixture set.

## Phase 4 — Claude decision layer

### Objective

Use Claude for semantic judgment while keeping media processing local and outputs constrained.

### Tasks

- Implement one `ClaudeDecisionProvider` interface.
- Call `claude -p --output-format json` through argument arrays.
- Provide only ids, transcript units, local numeric features and selected low-resolution evidence.
- Define JSON Schemas for hook ranking, narrative selection, B-roll concepts, explanations and editorial QC.
- Validate every response; allow one schema-repair retry.
- Reject unknown ids/time ranges.
- Cache decisions by input/model/prompt version.
- Add allowance usage telemetry and hard stop before paid overage.
- Implement deterministic fallback when Claude is unavailable.

### Exit gate

- Invalid/malicious model output cannot access files or run commands.
- The application still creates a deterministic rough cut with Claude disabled.
- Identical cached requests do not make repeated Claude calls.

## Phase 5 — Optional paired alignment and universal Style DNA

### Objective

Improve the already-useful cold start from approved choices/exports and, where supplied, 10–20 paired examples without opaque model fine-tuning.

### Tasks

- Build three-input dataset import/validation for script packs, raw footage and finished videos.
- Add quality labels: Excellent, Good, Average, Do Not Copy.
- Match final audio windows to raw assets through feature fingerprints and cross-correlation/DTW.
- Verify alignment visually.
- Prefer exact readable CapCut timeline data when supplied.
- Extract cut/pacing/caption/zoom/B-roll/audio/CTA features.
- Infer crop/zoom with frame feature matching where confidence permits.
- Produce per-example alignment report with unmatched portions.
- Aggregate robust distributions into Style DNA v1.
- Build readable learned-profile screen.
- Add manual corrections and approval.
- Retrieve nearest prior examples for a new project.
- Add A/B preference capture.
- Commit/checksum learning capsules and enable guarded cleanup of Coach staging/standalone local raw only. CapCut/Drive cloud and mounted sync sources remain read-only.

### Exit gate

- Clean talking-head training pairs achieve at least 95% matched final duration or are explicitly flagged.
- No low-confidence inferred effect becomes a hard rule.
- Style DNA has source example provenance and can be rolled back.
- The user approves the learned summary before it affects automatic drafts.

## Phase 6 — Style-aware planning, captions, B-roll and audio

### Objective

Apply the universal Style DNA to produce a much closer first cut.

### Tasks

- Apply learned pace and margin distributions within safe constraints.
- Implement caption line breaking, duration, position and highlight logic.
- Add face/subject detection and vertical crop plan.
- Add learned punch-in/zoom schedule with sensible minimum spacing.
- Index the user's local B-roll library with filenames, transcript/OCR and optional local image embeddings.
- Match B-roll concepts to owned local assets.
- Add placeholders when no suitable owned asset exists.
- Analyse voice loudness and create music-ducking plan.
- Add logo and CTA asset pack independent from Style DNA.
- Render styled local previews.

### Exit gate

- No caption overlaps; reading-speed warnings are visible.
- No automatic B-roll uses unapproved external media.
- Speech remains intelligible and within target loudness rules.
- Style-aware candidates visibly reflect approved profile settings.

## Phase 7 — Optional CapCut Free connection

### Objective

Offer an optional CapCut Free finishing path without making it part of the primary renderer.

### P7A Read-only watcher

- Watch project roots with debounce/stability checks.
- Create Coach projects from new/changed CapCut drafts.
- Ignore cache/transient file storms.
- Match media references by path and hash.
- Show project timeline/captions in Coach where supported.

### P7B Guaranteed handoff

- Generate handoff directory with ordered clips, preview, clean audio, SRT, B-roll, brand assets and HTML/edit JSON guide.
- Open Finder and CapCut.
- Provide exact import steps.
- Verify official SRT path and UTF-8 encoding.

### P7C Direct template clone — only if a separate optional canary passed

- Create an immutable Free-compatible master-template registry with no Pro dependencies.
- Clone template to temporary project.
- Replace placeholders and add supported tracks.
- Run version/diagnose/lint/sync checks.
- Perform atomic publish as a new Coach project.
- Register project when required by the exact Mac layout.
- Open and verify.
- Add one-click restore/removal of the generated duplicate.

### Exit gate

- Safe handoff works regardless of direct-write status.
- Direct path opens successfully ten consecutive times on golden projects.
- No original project file hash changes.
- Offline/missing media is reported before opening CapCut.

## Phase 8 — Optional Guided CapCut Free Mode

### Objective

Ensure a beginner can complete the remaining work without searching tutorials.

### Tasks

- Create a versioned guidance knowledge base for the user's exact CapCut version.
- Cover captions, audio enhancement, noise reduction, keyframes, zooms, B-roll, music, transitions, colour, CTA and export.
- Store control names, prerequisites, expected result and fallback instructions.
- Create one-step-at-a-time companion UI.
- Implement progress and confidence tracking.
- Add **Show me** annotated images.
- Add **I'm stuck** using one user-approved screenshot and current state.
- Use Accessibility tree for detection and safe actions.
- Add emergency stop and unexpected-dialog detection.
- Add Beginner, Learning, Checklist and Fast Production levels.

### Exit gate

- A novice completes one golden project without Terminal or outside tutorials.
- Every guide step has a verified control path for the exact CapCut version.
- An unknown screen produces a safe request for help, not guessed clicks.

## Phase 9 — Export watcher, QC and feedback learning

### Objective

Close the loop and improve future drafts.

### Tasks

- Watch user-selected export roots.
- Wait for file size stability before probing.
- Match export to project using filename/time/duration and ask if ambiguous.
- Run deterministic QC.
- Run schema-constrained editorial QC.
- Show timecoded, severity-ranked corrections.
- Compare proposed preview to approved export through audio/visual alignment.
- Calculate retained/removed/moved/changed decisions.
- Ask whether to learn from this result.
- Create new Style DNA candidate; require approval.

### Exit gate

- Export reviews do not begin on partial files.
- Findings link to exact preview timecodes.
- Ignored suggestions are retained as feedback.
- Style updates are reversible and never silent.

## Phase 10 — Packaging, documentation and operational hardening

### Objective

Turn the development repository into a reliable personal tool.

### Tasks

- Create `bootstrap.command`, launchd installer and uninstall/recovery scripts.
- Pin dependencies and model checksums.
- Add database backup/export/import.
- Add crash reports with privacy redaction.
- Add full user guide with screenshots.
- Add backup/restore and “safe mode” guide.
- Generate third-party notices and license manifest.
- Add update checker that never auto-updates CapCut or critical adapters.
- Add compatibility re-probe when CapCut changes version.
- Disable direct writes automatically after any untested CapCut update.
- Run all acceptance tests.

### Final release gate

- Phase 0 free local-render evidence exists.
- Safety, functional, performance, UX and golden-video tests pass.
- Direct adapter is either proven for the exact version or clearly disabled.
- The user can install, create three drafts, render a final MP4, review and recover without Terminal or CapCut.
- The dependency/billing audit proves the required path cannot create an extra charge.

## Post-release operating loop

For the first ten real videos:

1. Record baseline manual editing time.
2. Use CapCut Coach in Review First Cut mode.
3. Record active editing time, not background processing time.
4. Review every suggested cut.
5. Mark errors and approve only correct learning updates.
6. Re-run evaluation after videos 5 and 10.
7. Promote Autopilot only if safety is stable and at least 60% of proposed timeline remains unchanged.

## Estimated implementation reality

This is not a one-prompt build. Claude Code can realistically create it because the scope is one user, one Mac, one CapCut build and one editing style, but the limiting work is empirical testing.

- Several focused days: environment probe plus zero-example local-render proof.
- Approximately 1–2 weeks: useful local first version with script parsing, transcription, three drafts, captions and final MP4.
- Approximately 4–8 weeks: robust multi-format automation, Style DNA, optional CapCut Free guidance, QC and packaging.

These are planning estimates, not deadlines. Each gate matters more than elapsed time.
