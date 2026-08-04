# Ready-to-Paste Starting Prompt for Claude Code

Paste the following prompt into Claude Code from the directory where you want the new repository created. Place this entire handover folder in that directory first.

---

You are responsible for building **CapCut Coach**, a private local application for one beginner using CapCut Desktop Premium on an Apple-silicon M2 Mac.

The complete product, architecture, research, safety rules, implementation phases, dataset design and acceptance tests are contained in the folder:

`CapCut-Coach-Claude-Code-Handover-Pack/`

Read every file in that folder completely before modifying or creating product code. Treat the pack as the governing specification. If an instruction conflicts with actual reproducible evidence from the installed CapCut build, preserve safety, document the evidence and propose the smallest spec correction. Never silently override the pack.

Known facts:

- This is for one user, not a commercial SaaS.
- It runs locally on the same M2 Mac as CapCut.
- The user has CapCut Premium and Claude Code via a $100 Max 5x plan.
- The user is a complete editing beginner.
- The UI must use plain language and require no Terminal after installation.
- The system learns one universal editor style from approximately 15–20 paired raw/finished examples. Brands contribute asset packs only, not separate style models.
- Normal input is a three-part project: Word/PDF/text script pack (often a ZIP), large raw-footage folder (often around 2 GB) and approved finished reference. CapCut projects are optional high-confidence evidence; music matching is unimportant for this owner.
- After approval and learning, **Finish & Free Space** retains a compact learning capsule while offering a recoverable, explicitly confirmed move of eligible standalone local raw files to macOS Trash. Cloud/synchronised sources are never eligible.
- Style DNA is the baseline, not a ceiling. Build Faithful, Balanced and Bold creativity strengths. Balanced is default and may add reversible, clearly marked `COACH_IDEA` improvements while preserving facts, brand rules and mandatory script content. Learn from accepted/rejected ideas.
- The exact CapCut version, build, schema, M2 model, RAM and storage must be detected rather than guessed.

Non-negotiable safety rules:

1. Original media and original CapCut projects are immutable.
2. Never write to a CapCut project while CapCut is open.
3. Never force-write, bypass a version guard or target the user's only copy.
4. Direct CapCut writes are disabled until the exact-version ten-run canary and exact restore test pass.
5. Safe handoff must always work even when direct integration is disabled.
6. All heavy video processing is local. Do not upload full videos to Claude by default.
7. Claude outputs are untrusted structured suggestions. Validate ids, ranges and JSON Schema; never execute model-generated commands or paths.
8. Bind services to loopback only. Do not add accounts, cloud hosting, billing or multi-tenancy.
9. Additional paid Claude usage is disabled by default.
10. One heavy media job at a time; protect battery, storage and interactive CapCut performance.
11. Source cleanup requires a verified final, checksummed learning capsule, exact path/count/size preview, cross-project hash checks and explicit confirmation. Move exact files to macOS Trash only; never auto-delete, permanently delete, recurse over broad folders, follow symlinks or empty Trash.
12. CapCut account/Cloud/Team Space, Google Drive and all mounted/synchronised cloud folders are permanently read-only. Cleanup can remove only Coach-managed local staging/caches and explicitly approved standalone local raw files.

Begin as follows:

1. Inspect the current directory and preserve any existing user files.
2. Initialise the repository only if one does not exist.
3. Create a root `CLAUDE.md` containing the permanent rules in the pack.
4. Create a tracked implementation checklist mapped to Phases 0–10.
5. Execute **Phase 0 first**:
   - environment/system doctor;
   - CapCut bundle/version/build/source detection;
   - project-root discovery;
   - read-only project diagnostics using the safest evaluated tooling;
   - a disposable duplicate-project canary procedure;
   - a read-only macOS Accessibility probe;
   - an M2 processing benchmark harness.
6. Do not mutate any live project. If a canary requires the user to create or select a disposable CapCut project, build everything else first, then ask for that one action with exact instructions.
7. Continue independently with Phase 1 foundation work that does not depend on missing CapCut evidence, but keep direct-write code behind an off-by-default exact-version feature flag.

Technical direction:

- Python 3.12 + FastAPI + `uv`.
- React + TypeScript + Vite + `pnpm`.
- SQLite WAL and persisted idempotent jobs; no Redis/Celery.
- FFmpeg/ffprobe subprocesses.
- whisper.cpp for local transcription on Apple Silicon.
- PySceneDetect for shot-boundary analysis.
- typed internal edit schema with adapters.
- evaluate `capcut-cli` first for CapCut inspection/writes.
- small Swift macOS bridge for app/process/version, Accessibility and notifications.
- normal `CapCut Coach.app` shell using Swift/WKWebView around the local React/FastAPI system; browser fallback for recovery.
- Google Drive for desktop streamed-folder selection first; optional later read-only OAuth/Drive API adapter. Never implement cloud write/delete methods.
- incremental/resumable processing for multi-gigabyte media; no browser multipart upload path or whole-file RAM loads.
- launchd for local startup.
- pytest, Vitest and Playwright plus a sanitised fixture corpus.
- no Docker for the normal Mac runtime.
- implement the exact beginner UX and visual tokens in `14_PREMIUM_UX_DESIGN_SYSTEM.md`; generic scaffolding/admin-dashboard styling is not acceptable.

Open-source rules:

- Read `02_OPEN_SOURCE_RESEARCH.md` before adding dependencies.
- Confirm current licenses and pin exact versions/revisions.
- Do not copy code from a repository without an explicit compatible license.
- Generate `THIRD_PARTY_NOTICES.md`.
- README claims are not evidence of Mac/CapCut compatibility; canary tests are.

Working method:

- Implement vertical slices rather than a giant untested code dump.
- Add tests and documentation with each feature.
- Record phase evidence in `docs/phase-evidence/`.
- Mark hardware/data-dependent tests as blocked, never falsely passed.
- Use small intentional commits if git is configured.
- Do not use destructive git commands.
- Do not ask broad questions that the handover already answers.
- If blocked, state the exact evidence/action required and continue other safe work.

For this first turn, report:

1. what you found in the environment/repository;
2. the Phase 0 plan;
3. which actions can proceed immediately;
4. the minimum user action needed for the canary, if any;
5. then begin implementing the unblocked Phase 0 tasks.

Do not claim that the entire application is complete in this first turn.

---

## Follow-up prompt after the canary

Use only after Phase 0 evidence has been gathered:

> Review every Phase 0 artifact and test result against `00_READ_ME_FIRST.md`, `03_IMPLEMENTATION_PLAN.md` and `05_ACCEPTANCE_TESTS.md`. State the exact compatibility status: READ_ONLY, HANDOFF_ONLY, CANARY_REQUIRED, DIRECT_WRITE_CAPTION_ONLY, DIRECT_WRITE_TEMPLATE_CLONE or BLOCKED. Do not enable more than the evidence supports. Then proceed with Phases 1–3 to deliver the first useful vertical slice: local beginner UI, protected media ingest, whisper.cpp transcription, deterministic dialogue rough cut, preview, SRT and safe CapCut handoff. Run and record all unblocked acceptance tests.

## Follow-up prompt for style learning

> Implement Phases 4–6 using the approved vertical slice and the supplied paired dataset. Keep full media local. Build schema-constrained Claude decisions, raw/final alignment reports, approved versioned universal Style DNA, style-aware candidates, captions, reframing, B-roll matching from owned assets and audio planning. Use a held-out evaluation split and report actual alignment coverage and timeline-retention evidence. Do not fine-tune a foundation model or invent accuracy.

## Follow-up prompt for finishing and release

> Implement Phases 7–10. Preserve the guaranteed handoff. Enable direct template cloning only if the exact CapCut compatibility status permits it. Build Guided CapCut Premium Mode, export watching, deterministic and editorial QC, feedback learning, packaging, recovery and user documentation. Run the full acceptance matrix and distinguish passed, failed and evidence-blocked tests. Package only after release-blocking safety tests pass.
