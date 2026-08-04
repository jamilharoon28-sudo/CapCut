# Claude Code Execution Runbook

## 1. How Claude Code must approach this repository

Claude Code is the implementation agent, not the source of product truth. Product truth is this handover pack, local fixtures, the user's explicit decisions, official documentation and reproducible tests.

At the beginning:

1. Read every file in this handover pack completely.
2. Inspect the repository and environment.
3. Create a concise plan mapped to the numbered phases.
4. Create `CLAUDE.md` from the non-negotiables below.
5. Execute the Phase 0 free local-render proof before optional CapCut work.
6. Continue independent work while clearly marking hardware/data-dependent gates.

Do not claim completion merely because code compiles. Completion requires the acceptance evidence in `05_ACCEPTANCE_TESTS.md`.

## 2. Required `CLAUDE.md` content

Create a root `CLAUDE.md` containing at least:

- Product is private/local for one beginner on an M2 Mac.
- Original media and original CapCut projects are immutable.
- Never write to a project while CapCut is running.
- Never use forced CapCut writes automatically.
- Direct write is feature-flagged by exact tested CapCut version/schema.
- Safe handoff must always work.
- Claude outputs are untrusted structured suggestions and must pass JSON Schema.
- Local deterministic processing before Claude.
- No full raw-video upload by default.
- No hidden paid overage.
- Required workflow has zero additional spend: no CapCut Pro, Remotion, paid API, hosted renderer or new subscription.
- Zero-example script+raw editing and local final MP4 work without CapCut.
- One heavy media job at a time.
- Use `apply_patch` or normal editor operations; preserve user changes.
- Every feature includes tests and documentation.
- Do not add a dependency without license, maintenance and capability justification.
- Do not expose the local API beyond loopback.
- Do not implement public accounts, cloud hosting or billing.
- Use plain-language UI and hide advanced technical detail.

## 3. Work discipline

### One phase, one evidence trail

For every phase:

1. State its goal.
2. List assumptions and blockers.
3. Implement the smallest vertical slice.
4. Run unit and integration tests.
5. Record commands/results in `docs/phase-evidence/PX.md`.
6. Update the implementation checklist.
7. Commit intentionally if the repository uses git.

### Context and Max 5x efficiency

- Use a fresh Claude Code conversation for each phase or coherent subsystem.
- Run `/clear` when switching subsystems.
- Use `/compact` only when a task remains continuous.
- Keep durable decisions in `CLAUDE.md`, ADRs and phase evidence rather than chat history.
- Use the efficient model for routine implementation; reserve the heaviest model for schema reverse engineering, alignment design or difficult failures.
- Do not launch multiple parallel agents unless the user explicitly requests it and the usage cost is justified.
- Ask Claude to inspect only the files relevant to the current task.
- Prefer targeted tests over repeatedly loading large logs.

### Git practice

- Never commit raw user footage, CapCut projects, transcripts, model binaries, credentials or absolute home paths.
- Add fixture sanitisation checks.
- Use small commits named by phase/task.
- Never rewrite user history or use destructive reset commands.
- Mark third-party code and preserve notices.

## 4. Development commands to provide

The completed repository should expose stable wrappers rather than forcing the user to remember tooling:

```bash
./scripts/bootstrap.command
./scripts/doctor.sh
./scripts/run-dev.sh
./scripts/test.sh
./scripts/install-launchagent.sh
./scripts/uninstall-launchagent.sh
./scripts/backup-database.sh
./scripts/restore-project.sh <backup-id>
```

Commands must quote paths, avoid `eval`, avoid shell interpolation of filenames and support spaces in paths.

## 5. Architectural decision records

Create ADRs for:

1. Local FastAPI/React rather than Electron/Tauri for v1.
2. whisper.cpp rather than cloud transcription.
3. Deterministic Style DNA rather than foundation-model fine-tuning.
4. Internal edit schema plus adapters.
5. Local FFmpeg RenderGraph compiler as the primary renderer.
6. Exact-version feature flag for direct CapCut writes.
7. AXUIElement-first automation rather than coordinate clicking.
8. No Docker in the normal Mac runtime.
9. One universal editing style plus separate asset packs.
10. Claude as a constrained decision provider, not an executor.

## 6. Prompt templates for implementation phases

These are task templates, not invitations to skip evidence gates.

### Phase 0 prompt

> Read the handover pack and repository. Execute Phase 0 only. Build the Mac/storage/tool doctor, a five-second FFmpeg/VideoToolbox/ASS render fixture, and a zero-example script+raw vertical slice that produces Clean/Enhanced/Bold previews plus one final MP4. Record real speed/memory/storage/source-hash evidence. Do not require CapCut or any paid dependency. Keep all CapCut project writes disabled.

### Foundation prompt

> Implement Phase 1 as a vertical slice: local loopback FastAPI API, React/Vite UI, SQLite migrations, persisted idempotent jobs, onboarding doctor and launchd scripts. Keep the UI beginner-friendly. Add tests for restart, cancellation, path safety and loopback-only binding. Do not add media intelligence yet.

### Media prompt

> Implement Phase 2 using FFmpeg/ffprobe and whisper.cpp. Add content-addressed caching, 720p proxy generation, VAD transcription, word timestamps, SRT, waveforms and contact sheets. Benchmark on the supplied M2 fixture. Ensure one heavy job at a time and preserve original hashes.

### Rough-cut prompt

> Implement Phase 3. Build a typed internal timeline, deterministic phrase/silence/restart detection, natural margins, multiple duration candidates, preview rendering and restore-a-phrase UI. Every time range must validate against source duration. Add audio-boundary tests.

### Claude adapter prompt

> Implement Phase 4 as one provider with strict JSON Schema. Send only transcript ids/features and selected low-resolution evidence. Reject unknown ids, paths and commands. Cache requests. Add a deterministic fallback and a hard stop before paid overage.

### Style learning prompt

> Implement Phase 5 as an optional accelerator after cold start works. Learn first from chosen candidates, simple revisions and approved exports. Add paired raw/final alignment with audio-first matching, visual verification, reports, robust aggregation, quality weights and approved Style DNA versions. Do not fine-tune a foundation model. Low-confidence inferences remain suggestions.

### CapCut prompt

> Implement Phase 7 in order: read-only watcher, guaranteed handoff, then direct template clone only if the exact version gate is green. Use temporary copies, atomic publish, hashes, backups, lint, PID guard and rollback. Never modify the original or use force-write.

### Guided Mode prompt

> Implement Phase 8 using a versioned local knowledge map. Show one exact CapCut action at a time. Use AXUIElement roles/identifiers before coordinates. Any unknown state must pause and ask, never guess. Screen capture is user-triggered only.

### Release prompt

> Run the entire acceptance matrix. Report passed, failed, skipped and evidence-needed tests separately. Do not mark skipped hardware/CapCut tests as passed. Package the personal Mac installer only after safety gates pass.

## 7. Claude runtime prompt design

### General system instruction for Coach decisions

> You are the editorial decision component of a local video editing assistant. You receive only pre-validated transcript units, numeric features, user constraints and a Style DNA summary. Return only JSON conforming to the supplied schema. Refer only to provided ids. Never invent source footage, quotes, file paths, UI controls or claims. Preserve full meaning, avoid misleading edits, and flag uncertainty. Optimise for a clear short-form story in the requested duration while respecting must-include and must-avoid constraints.

### Hook-ranking output

Required fields:

- candidate id;
- rank;
- reason;
- risks/needed context;
- confidence 0–1.

### Narrative-plan output

Required fields:

- ordered transcript-unit ids;
- narrative role for each;
- optional omission reason;
- target duration;
- unresolved questions;
- confidence.

Claude may select/reorder supplied units. It may not change quoted speech or generate fake spoken lines.

### Beginner explanation output

Required fields:

- short title;
- single action;
- one-sentence reason;
- expected result;
- common mistake;
- known knowledge-base step id.

If no verified knowledge-base step id applies, return `needs_human_mapping: true`.

## 8. Debugging order

When an edit is wrong, diagnose in this order:

1. Source media metadata and VFR.
2. Transcript word timing.
3. Sentence/restart segmentation.
4. Local feature extraction.
5. Claude input ids and constraints.
6. Claude structured response.
7. Edit-plan validation.
8. Preview renderer.
9. CapCut adapter translation.
10. CapCut version/schema/UI change.

Do not “fix” an upstream timing error with arbitrary downstream offsets.

## 9. Compatibility registry

Create a registry keyed by:

- CapCut semantic version;
- build number;
- macOS version;
- app source;
- top-level schema version;
- canonical timeline filename/layout;
- readable/writable evidence status;
- supported operations;
- canary date and fixture hash.

Possible statuses:

- `READ_ONLY`
- `HANDOFF_ONLY`
- `CANARY_REQUIRED`
- `DIRECT_WRITE_CAPTION_ONLY`
- `DIRECT_WRITE_TEMPLATE_CLONE`
- `BLOCKED`

An app update automatically drops the effective status to `CANARY_REQUIRED` or safer.

## 10. Dependency policy

For every dependency, record:

- exact version/revision;
- license;
- why it is required;
- whether it handles user data;
- whether it makes network calls;
- binary source/checksum;
- upgrade procedure;
- fallback/removal strategy.

Reject packages that duplicate small standard-library functionality, add a server for a one-user local task, or have unclear licensing.

## 11. Definition of “automatic”

Do not misuse this word. A stage is automatic only when:

- it starts from a reliable local event;
- it needs no file re-selection;
- it reports progress and failure;
- it is idempotent;
- it produces a verifiable output;
- it can recover or fall back safely.

Opening Finder with files prepared is an assisted handoff, not direct automatic CapCut editing. Label it honestly in the UI.

## 12. Final handoff from Claude Code

At completion, provide:

- working repository;
- exact install/uninstall instructions;
- environment doctor output;
- tested CapCut compatibility status;
- fixture/test report;
- known limitations;
- backup/restore instructions;
- third-party notices;
- user guide with screenshots;
- benchmark and measured time-saving study;
- a roadmap of deferred features, not fake placeholders.
