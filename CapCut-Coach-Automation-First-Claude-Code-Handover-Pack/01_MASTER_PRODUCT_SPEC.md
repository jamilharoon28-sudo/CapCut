# CapCut Coach — Master Product and Technical Specification

## 1. Product statement

CapCut Coach is a private automation-first local video editor for one beginner on an M2 Mac. Given raw footage and a script, it organises the job, proposes the story and visuals, renders three candidates and produces a near-finished or final MP4 using free local tools. It works with zero examples, learns a universal personal editing fingerprint from later choices and finished outputs, and offers CapCut Free only as an optional finishing path.

It is an automation-first local editor with optional CapCut Free finishing. It is not a CapCut license bypass, a public product, or a promise of viral performance. The full primary workflow and final MP4 rendering must work without CapCut Pro or any additional paid service.

## 2. Supported scope

### Version 1 primary formats

- Scripted story/offer reels, treatment or promotional montages, talking-head/educational videos and testimonials/interviews.
- One main speaker or a visually led montage assembled from labelled/scripted shots.
- Raw recording from approximately 1–20 minutes.
- Final output from 15–90 seconds.
- Portrait 9:16, normally 1080×1920.
- English speech initially; architecture must support more languages.
- Optional B-roll supplied locally.
- A script is preferred but the treatment-montage playbook can work from a brief and footage alone.

### Deferred formats

- True multi-camera podcast switching.
- Complex music videos where beat choreography is the main editorial requirement.
- Long-form documentary editing.
- Complex compositing and rotoscoping.
- Automatic browsing/licensing of third-party stock libraries.
- Mobile CapCut control.
- Public SaaS accounts and collaboration.

## 3. Jobs the system performs

### Intake and organisation

- Detect new approved media folders; CapCut project detection is optional.
- Create a Coach project automatically.
- Hash media to avoid duplicate processing.
- Read metadata: codec, resolution, frame rate, audio channels, duration, orientation and variable-frame-rate status.
- Generate lightweight analysis proxies and contact sheets.
- Preserve originals as read-only inputs.

### Dialogue understanding

- Produce word-level transcription locally.
- Detect speech, silence, filler words, restarts and repeated phrases.
- Identify sentences, semantic topics and candidate hooks.
- Allow custom vocabulary for names such as LawBridge, client names and technical terms.
- Give every word a confidence score and flag low-confidence captions.

### Edit planning

- Generate 30-, 45- and 60-second candidates where source material supports them.
- Create a clear hook, body and CTA structure.
- Rank alternative hooks.
- Mark must-review cuts where the confidence is low.
- Prefer natural breath and sentence boundaries over mechanical silence removal.
- Apply learned Style DNA within safe ranges.

### Timeline generation

- Create an internal OpenTimeline-style edit model independent of CapCut.
- Render a local preview with FFmpeg.
- Export selected individual clips, clean audio, SRT captions and a machine-readable edit manifest.
- Compile the internal RenderGraph to local previews and final MP4 using FFmpeg/VideoToolbox plus ASS/SVG/raster overlays.
- Optionally prepare a file-based CapCut Free handoff package. A duplicated CapCut draft is an evidence-gated future adapter, never a dependency.

### Optional CapCut Free finishing guidance

- Tell the user one next step at a time.
- Name the exact CapCut menu/panel/control.
- Provide exact suggested values where appropriate.
- Explain why the step matters in one sentence.
- Show a short local demo image or annotated screenshot where available.
- Detect completion through project data or the Accessibility tree when possible.
- Offer **I'm stuck** and safe **Do it for me** actions.

### Review and learning

- Watch the export folder.
- Match an export to its Coach project.
- Check technical and editorial quality.
- Compare the proposed preview with the approved export.
- Record accepted, changed and rejected suggestions.
- Update Style DNA only after explicit approval.

## 4. User experience

### Onboarding wizard

Screen 1: **Welcome**  
“Add your script and footage. Coach builds the edit, shows three choices and can finish the MP4 for you.”

Screen 2: **Computer check**

- Detect Apple chip, RAM, macOS version and free storage.
- Detect CapCut bundle/version if installed, without requiring a project directory.
- Detect Claude Code authentication.
- Detect or install application-managed FFmpeg and whisper.cpp binaries.

Screen 3: **Permissions**

- Footage folder access.
- Optional CapCut project folder access, requested only if the owner enables experimental integration.
- Export folder access.
- Notifications.
- Optional Accessibility access.
- Optional Screen Recording access used only for **I'm stuck**.

Screen 4: **Choose how Coach starts**

- Default to **Start with Coach's editing judgment**.
- Optionally import finished examples now or later.
- Explain that the system improves from every approved choice; 10–20 suitable outcomes create much stronger personalisation.
- Let the user rate each final as Excellent, Good, Average or Do Not Copy.

Screen 5: **Ready check**

- Render a five-second local fixture and verify FFmpeg, hardware encoding, captions and free-space policy.
- Report: Local editing ready; CapCut Free detected/not detected; optional experimental connection not configured.

### Home screen

Only four primary actions:

- **Create Video**
- **Review My Drafts**
- **Learn My Style**
- **Free Local Space**

The home screen also shows current jobs and weekly video count. Technical logs live under Advanced.

### New edit form

Required:

- footage selection;
- objective: educate, promote, testimonial, explain or other;
- target duration: Auto, 30, 45, 60 or 90 seconds.

Optional:

- reference video;
- CTA text;
- logo/asset pack;
- must-include statement;
- words/claims to avoid.

### Project screen

- Side-by-side raw transcript and preview.
- Alternative hooks.
- Timeline explanation in plain language.
- Confidence flags.
- Buttons: **Choose This**, **Change Hook**, **Make Faster**, **Make Calmer**, **Render Final**, **Open in CapCut Free** and **Learn This Edit**.

### Guided Mode

Always-on-top companion window or browser panel. Each card contains:

- step number and short title;
- the exact action;
- where the control is located;
- recommended setting;
- a one-sentence reason;
- expected visual/audio result;
- **Show me**, **I'm stuck**, **Done**, and optionally **Do it for me**.

Instructions must be generated from a versioned local CapCut knowledge map, not improvised on every request. Claude may translate a known step into simpler language but must not invent UI control names.

## 5. Architecture

### Recommended stack

| Layer | Choice | Reason |
|---|---|---|
| Local API | Python 3.12 + FastAPI | Strong media/ML ecosystem and simple local API |
| Dependency management | `uv` with lockfile | Fast, reproducible Python environments |
| Web UI | React + TypeScript + Vite | Responsive, testable, familiar |
| Frontend package manager | `pnpm` with lockfile | Deterministic and efficient |
| Database | SQLite in WAL mode | No server; sufficient for one user |
| Jobs | `asyncio` worker plus persisted job table | Avoid Redis/Celery complexity |
| File watching | `watchfiles` initially; FSEvents helper if needed | Local project/export detection |
| Video/audio | FFmpeg/ffprobe subprocesses | Mature deterministic media processing |
| Transcription | whisper.cpp Metal/Core ML build | Apple-silicon optimisation and local privacy |
| Scene detection | PySceneDetect | Shot boundaries and analysis data |
| Similarity/alignment | NumPy/SciPy/OpenCV plus audio fingerprints | Raw-to-final mapping |
| Timeline model | Internal typed schema with OTIO export adapter | Avoid CapCut lock-in |
| Optional CapCut adapter | evidence-gated capcut-cli wrapper | Never required; safer experimental inspection/writes |
| Claude | `claude -p --output-format json` behind strict schemas | Personal non-interactive decision layer |
| macOS integration | Small Swift helper + launchd | App version, Accessibility, windows, notifications |
| Tests | pytest, Vitest, Playwright, fixture corpus | Unit, UI and end-to-end verification |

Do not put the normal application in Docker. Docker prevents straightforward access to CapCut, macOS Accessibility, launchd, Metal acceleration and user-selected folders.

### Processes

1. `coach-api`: local API and static frontend on `127.0.0.1`, never `0.0.0.0` by default.
2. `coach-worker`: one persisted heavy-media job at a time.
3. `coach-bridge`: small macOS helper for CapCut process/version/window/Accessibility functions.
4. `coach-launcher`: launchd item that starts API/worker at login and opens the UI.

### Component diagram

```text
Browser UI
   |
FastAPI local API ---- SQLite
   |
Job orchestrator
   |---- Media probe/proxy/cache
   |---- whisper.cpp/VAD/transcript
   |---- Raw/final alignment + Style DNA
   |---- Edit planner + Claude decision adapter
   |---- FFmpeg preview renderer + QC
   |---- CapCut read/write adapter
   `---- macOS bridge (Accessibility, process guard, notifications)
```

## 6. Repository structure to create

```text
capcut-coach/
├── CLAUDE.md
├── README.md
├── LICENSE
├── THIRD_PARTY_NOTICES.md
├── pyproject.toml
├── uv.lock
├── package.json
├── pnpm-lock.yaml
├── apps/
│   ├── api/
│   ├── worker/
│   ├── web/
│   └── mac-bridge/
├── packages/
│   ├── domain/
│   ├── media/
│   ├── transcription/
│   ├── alignment/
│   ├── style-dna/
│   ├── edit-planner/
│   ├── renderer/
│   ├── capcut-adapter/
│   ├── guidance/
│   └── qc/
├── schemas/
│   ├── project.schema.json
│   ├── edit-plan.schema.json
│   ├── style-dna.schema.json
│   ├── claude-decision.schema.json
│   └── qc-result.schema.json
├── fixtures/
│   ├── capcut/
│   ├── media/
│   └── golden-edits/
├── scripts/
│   ├── bootstrap.command
│   ├── doctor.sh
│   ├── run-dev.sh
│   ├── install-launchagent.sh
│   └── uninstall-launchagent.sh
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── e2e/
│   ├── performance/
│   └── safety/
└── docs/
    ├── architecture.md
    ├── capcut-compatibility.md
    ├── data-and-privacy.md
    ├── recovery.md
    └── user-guide.md
```

## 7. Persisted domain model

### Project

- id, name, objective, target duration, aspect ratio;
- source path, CapCut project path, export path;
- state, created/updated timestamps;
- selected asset pack and Style DNA version;
- requested claims, must-include and must-avoid text.

### MediaAsset

- content hash, path, kind, duration, dimensions, fps, codec;
- proxy path, waveform path, thumbnail/contact sheet paths;
- audio loudness, VFR status, quality flags;
- never store only a mutable path without the content hash.

### TranscriptWord

- media id, word, start/end, confidence, speaker, sentence id;
- filler/restart/duplicate flags;
- corrected text and correction provenance.

### EditPlan

- immutable version id;
- ordered source segments with source in/out and timeline in/out;
- narrative role: hook, context, body, proof, CTA;
- cut reason and confidence;
- caption segments, B-roll placements, audio decisions, zoom/keyframe decisions;
- renderer and CapCut adapter status.

### StyleDNA

- version and training example ids;
- distributions and confidence intervals rather than single magic values;
- weights for example quality;
- separate sections for selection, pacing, captions, framing, motion, B-roll, audio, transitions and CTA;
- manual overrides and learned values kept separate;
- approval state and changelog.

### QCResult

- rule id, severity, start/end time, message, evidence and suggested correction;
- machine-detected versus Claude-advised;
- resolved/ignored status.

### Feedback

- proposed edit version, approved export, alignment result;
- retained, moved, shortened, lengthened or removed segments;
- explicit A/B choice;
- whether the example may update Style DNA.

## 8. State machine

```text
DISCOVERED
  -> INGESTING
  -> PROXYING
  -> TRANSCRIBING
  -> ANALYSING
  -> PLANNING
  -> PREVIEW_READY
  -> APPROVED
  -> CAPCUT_PREPARING
  -> CAPCUT_READY
  -> EDITING
  -> EXPORT_DETECTED
  -> REVIEWING
  -> CHANGES_REQUESTED | COMPLETE
```

Every state transition is persisted. Jobs are idempotent and resumable. A crash must never leave the database claiming that a CapCut write succeeded when it did not.

## 9. Media pipeline

### Ingest

1. Resolve real paths and reject anything outside user-approved roots.
2. Compute SHA-256 content hash.
3. Probe with ffprobe JSON.
4. Copy no originals; store references plus hashes.
5. Import a matching script or script ZIP when supplied. Safely extract archives and parse `.docx`, `.pdf`, `.txt` and `.md` into a typed shot plan while preserving the original.
6. Recognise reel/shot numbers, hooks, time ranges, camera directions, speech, text overlays, cutaways, music, transitions, pacing and end cards. Keep unrecognised content attached to its nearest section rather than dropping it.
7. Create a 720p analysis proxy with hardware-assisted VideoToolbox encoding where available.
8. Extract mono 16 kHz analysis audio.
9. Generate waveform, thumbnails and scene-boundary data.
10. Cache every deterministic output by source hash plus tool/version/config hash.

### Three-input project and optional CapCut evidence

Each learning example accepts a script pack, one or more raw-footage folders/files and an approved finished video. A readable editor-authored CapCut project is optional high-confidence evidence. When a project exists in a CapCut Cloud/Team Space, the owner opens it fully on the Mac and quits CapCut; Coach then discovers the local project copy or lets the owner select it. Coach never asks for CapCut credentials.

The script parser converts creative instructions into candidate constraints. It maps requested shots and overlays to detected footage, preserves cross-references such as `Reel 5 – Shot 3`, shows missing shots and permits correction. Raw footage remains the selection evidence; the approved final remains the visual outcome; readable CapCut timeline facts override uncertain inference.

Music matching is optional and off for the initial owner workflow. The system may learn cut rhythm and audio-level preferences without retaining or identifying the original music track.

### Finish & Free Space

After export approval, create a compact versioned learning capsule containing original hashes/names/technical metadata, normalised script and shot plan, raw-to-final alignment, selected/rejected segment features, representative low-resolution evidence, edit plan, Style DNA contribution, final-video hash and all relevant versions.

The recommended cleanup choice is **Keep learning, remove large local files**: retain the script, approved final, capsule and Style DNA contribution; remove Coach-managed staging/caches; offer to move exact standalone local raw files to macOS Trash. Also offer **Keep selected clips for re-editing** and **Delete all local project media, keep learned style only**, with consequences shown clearly.

Before any source move, require a playable hashed final, completed analysis, committed/checksummed capsule, no active job, no shared content-hash reference from another project, targets inside approved standalone local roots, an exact item-count/size preview and explicit confirmation. Move exact files to Trash; never empty Trash, follow symlinks, permanently delete or recursively target a broad/unresolved folder. Journal partial completion so retry is safe. CapCut account/Cloud/Team Space, Google Drive and any mounted/synchronised cloud path are read-only and never source-cleanup targets.

### Transcription

- Default model chosen by a benchmark during onboarding, not hardcoded.
- Generate word timestamps and confidence.
- Use VAD to avoid transcribing long silence.
- Apply custom vocabulary through post-correction and Claude review; preserve original recognition.
- Export valid UTF-8 SRT and internal JSON.
- Caption line-breaking is a separate deterministic stage governed by Style DNA.

### Rough-cut logic

1. Create speech units from words and sentence boundaries.
2. Mark silence, filler, duplicate/restart and low-confidence units.
3. Detect candidate hooks and complete claims.
4. Ask Claude for structured selection/ranking only after local feature extraction.
5. Validate returned source ids and time ranges against the transcript.
6. Expand cuts by learned pre/post-roll margins.
7. Reject cuts that produce clipped phonemes or breaths.
8. Apply narrative constraints and target duration.
9. Produce several candidates and score them.
10. Render previews locally.

Claude must never return arbitrary filesystem paths or shell commands. Its output must conform to JSON Schema and refer only to supplied ids.

## 10. Optional style learning from choices, raw/final pairs and exports

### Alignment stages

1. Extract clean/voice-focused audio from raw and final videos.
2. Generate short-window fingerprints or MFCC/chroma features.
3. Propose raw-source/time matches for every final window.
4. Refine boundaries with cross-correlation and dynamic time warping.
5. Validate with visual perceptual hashes or feature matching.
6. Segment the final timeline at shot/cut boundaries.
7. Label unmatched segments as likely titles, generated graphics, external B-roll or transitions.
8. If a readable CapCut project exists, prefer its exact timeline facts over inferred alignment.

### Extracted style features

- opening delay;
- distribution of shot lengths;
- speech pause retained before/after cuts;
- filler/restart handling;
- sentence truncation tolerance;
- hook types and hook duration;
- zoom frequency, magnitude and duration;
- crop and subject position;
- captions: words/line, characters/line, lines, duration, vertical position, highlight rate;
- B-roll frequency, duration and semantic relationship;
- transition types and rate;
- music loudness relative to speech;
- CTA timing, duration and visual density;
- overall duration and pacing by content characteristics.

### Learning method

Do not fine-tune a foundation model initially. Build a versioned statistical profile plus example retrieval:

- robust medians, quantiles and distributions;
- weight Excellent examples more than Good examples;
- exclude Do Not Copy examples from positive learning but retain them as negatives;
- retrieve the most similar 3–5 prior examples for a new edit;
- use explicit A/B feedback to tune preference weights;
- require approval before publishing a new Style DNA version;
- show the user a readable summary of what was learned.

This approach is auditable, cheap, editable and appropriate for 15–40 examples.

With zero examples, start from the format playbooks in `16_ZERO_EXAMPLE_COLD_START.md`. Every chosen candidate, simple revision and approved export becomes evidence; paired raw/final examples are an optional accelerator, not an onboarding gate.

### Coach Magic — controlled creative improvement

Style DNA is the baseline, not a ceiling. After creating a faithful candidate, Coach may propose an enhanced version using its own editorial judgment where the footage and script support it. Creativity has three owner-facing strengths:

- **Clean** — follow the script and established format playbook with minimal experimentation; once a profile exists this becomes **Faithful**.
- **Balanced** — default; keep the learned style while adding a small number of high-confidence improvements.
- **Bold** — offer more adventurous alternatives for explicit review.

Permitted ideas include a stronger opening visual, improved shot order, match cuts, purposeful speed changes, freeze frames, split screens, before/after reveals, kinetic emphasis text, restrained punch-ins, pattern interrupts and more effective CTA timing. Music selection/matching is optional for this owner.

Every creative addition must be labelled internally as `COACH_IDEA`, have a reason/confidence, be removable without rebuilding the edit and appear in the comparison view. It may not invent or change factual claims, misrepresent treatment/results, override mandatory script information, break brand assets or add effects merely to look busy. Show **Clean**, **Enhanced** and **Bold** previews; use the owner's accept/reject decisions to learn which kinds of flair belong in the universal style.

## 11. CapCut integration lanes

### Lane A — read-only, always first

- Discover project folder and app version.
- Snapshot draft files after a quiet/debounce period.
- Refuse to inspect a partially written file.
- Read timeline, captions, media references and effect metadata where supported.
- Never write.

### Lane B — optional file-based handoff

- Create selected clips, cleaned audio, SRT, B-roll folder, brand assets and edit manifest.
- Open the project/package in Finder and open CapCut.
- Guided Mode walks through import and styling.
- This lane must remain functional when CapCut Free is installed even if all direct adapters are disabled; its absence never blocks local rendering.

### Lane C — template-cloned direct draft, optional experiment

- User creates one disposable known-good local project in CapCut Free if this lane is ever enabled.
- Coach snapshots it as an immutable template.
- Coach duplicates it under a new UUID/name.
- Replace placeholder media/text and add only supported new tracks/segments.
- Use only resources legitimately available in the installed CapCut edition; do not depend on Pro resources.
- Validate/lint/synchronise all canonical timeline mirrors.
- Register the new project if the tested CapCut layout requires it.
- Open only after the writer exits successfully.

### Lane D — Accessibility automation, optional

- Use AXUIElement roles, labels and actions before pixel coordinates.
- Scope scripts by CapCut version and UI language.
- Pixel/image matching is a last resort.
- Require the CapCut window to be frontmost and at a known layout.
- Pause on any unexpected dialog.
- Provide a visible cancel button and keyboard emergency stop.
- Use only for safe reversible actions such as opening a panel, selecting an import file or applying a known template.
- Do not automate publishing, deletion, purchases or account actions.

## 12. CapCut write-safety transaction

1. Resolve exact target project and confirm it is a Coach duplicate.
2. Verify CapCut process is not running.
3. Acquire an exclusive Coach lock.
4. Snapshot every timeline/meta file to a timestamped backup directory.
5. Record file size, mtime and SHA-256.
6. Copy the template to a temporary sibling directory.
7. Apply mutation to the temporary copy.
8. Validate schema, ids, time ranges, references and media existence.
9. Run adapter lint and version checks.
10. Atomically rename the temporary copy into the new project location.
11. Re-read and hash the result.
12. Release the lock.
13. Open CapCut.
14. If CapCut reports corruption or fails to show the project, close it and restore automatically.

No existing original is overwritten in this transaction.

## 13. Quality control

### Deterministic checks

- duration and aspect ratio;
- resolution, codec, bit rate and frame rate;
- VFR warning;
- black/frozen frames;
- audio peak, integrated loudness and true-peak risk;
- abrupt audio discontinuities;
- caption overlaps, gaps, excessive reading speed, spelling dictionary and safe zone;
- logo and CTA presence/duration;
- blank timeline gaps;
- missing/offline media references;
- duplicated caption tracks;
- crop/face outside safe area where detectable.

### Claude-assisted editorial review

- opening clarity;
- narrative completeness;
- repeated ideas;
- unsupported or risky claims;
- CTA clarity;
- whether B-roll supports or distracts;
- whether the output resembles the Style DNA examples.

Editorial findings are advice, not facts. Present evidence and timecodes.

## 14. Resource protection on M2

### Modes

- Quiet: one low-priority worker, 540p proxy, pause on battery.
- Balanced: default, one heavy job, 720p proxy, hardware encode, pause while CapCut exports.
- Maximum: user-invoked, higher-quality analysis and no interactive pause.

### Required safeguards

- maximum one heavy media job at a time;
- process niceness/quality-of-service lowered for background jobs;
- no repeated re-encoding when cache is valid;
- configurable minimum free-space threshold, default max of 30 GB or 15% of volume;
- pause new work when below threshold;
- clean temporary files only after output verification;
- cap proxy and cache retention by size;
- detect whether on battery and respect the selected policy;
- never promise a fixed processing speed without benchmarking the actual M2/RAM.

## 15. Claude integration and usage control

### Calls allowed

- rank hooks from transcript units;
- assemble narrative from supplied candidate units;
- generate B-roll search concepts;
- explain deterministic editing decisions in beginner language;
- review a small contact sheet or selected frames;
- generate structured QC advice;
- answer **I'm stuck** from one user-approved screenshot plus current guidance state.

### Calls prohibited

- uploading full source videos by default;
- executing arbitrary model-provided commands;
- deciding file deletion;
- bypassing CapCut safety/version gates;
- silently using additional paid credits;
- continuous screenshot streaming.

### Cost/allowance controls

- use non-interactive `claude -p` behind one adapter;
- capture usage metadata when available;
- daily and monthly soft limits;
- hard stop before paid overage;
- cache identical decisions;
- one retry only for schema repair;
- use the efficient model for ordinary decisions and reserve heavier reasoning for explicit re-analysis.

## 16. Security and privacy

- Bind API to loopback only.
- Use a random local bearer token stored in Keychain or a permission-restricted file.
- Never expose project paths in browser logs.
- Protect against path traversal and symlink escapes.
- Sanitize filenames and shell arguments; use subprocess arrays, never string interpolation.
- Permit reads/writes only beneath user-approved roots.
- Keep audit logs free of transcript content by default.
- Provide **Delete Coach Analysis** without deleting original media or CapCut projects.
- Screen capture is off by default and only activated by the user.
- Document exactly which excerpts are sent to Claude.

## 17. Failure behaviour

- If transcription fails: keep project and offer retry/model change.
- If Claude is unavailable: use deterministic rough-cut candidate and mark editorial selection unavailable.
- If CapCut adapter is unsupported: use safe handoff.
- If Accessibility fails: show manual step with screenshot.
- If storage is low: pause before creating a proxy.
- If export cannot be matched: ask the user to choose among recent projects.
- If style confidence is low: present alternatives instead of auto-applying.
- If a CapCut project is open: queue the write and explain that CapCut must be closed.

## 18. Success metrics shown to the user

- hands-on time per video;
- total processing time separated from hands-on time;
- proposed duration versus approved duration;
- percentage of proposed timeline retained;
- number of corrections after export;
- captions corrected;
- videos completed this week;
- learning confidence and number of approved training examples.

Do not gamify quality with a meaningless single score. Show concrete findings and trends.
