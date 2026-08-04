# CapCut Coach — Read This First

Status: complete implementation handover  
Prepared: 4 August 2026  
Target computer: one Apple-silicon M2 Mac  
Target editor: CapCut Desktop Free; Premium is optional and never required  
Target user: one beginner editor; no commercial multi-user product  
Primary content: scripted reels, promotional/treatment montages, talking-head, educational and testimonial videos  

## 1. The outcome

Build a private local application called **CapCut Coach**. From a script and raw footage, it automatically organises takes, understands the story, builds three editable candidates and renders a near-finished or final MP4 with free local tools. CapCut Free is an optional finishing layer, not a requirement. Previous finished videos and CapCut projects are optional learning evidence; the first job must work using Coach's general editing judgment, and later choices teach one universal personal style.

The finished user experience must be simpler than the technology behind it. The user should not need to understand Python, FFmpeg, JSON, models, APIs, terminals, project schemas or file paths.

The default workflow is:

1. Add a script ZIP/document and raw footage, or select an approved Google Drive folder.
2. Coach safely parses the script, groups reels/shots/takes and analyses the footage in the background.
3. Coach renders **Clean**, **Enhanced** and **Bold** previews locally.
4. The user chooses one or asks for a simple change such as “faster,” “calmer” or “different hook.”
5. Coach renders the final MP4 locally and runs automatic quality checks.
6. Optionally open the result and prepared assets in CapCut Free for a manual touch-up.
7. Coach explains only the next CapCut step when help is requested.
8. Coach learns from the chosen candidate, revisions and final export.
9. **Finish & Free Space** removes only approved Coach-managed local files or explicitly selected standalone local raw footage; cloud content is untouched.

## 2. Known user constraints

- The user owns an M2 Mac. The exact model, RAM and storage are not yet known.
- The user currently uses CapCut Free. The exact numerical CapCut Desktop version is not yet known. The complete primary workflow must work without upgrading.
- The application is only for the user and may run as a local service on the same Mac.
- The user has Claude Code in Terminal and a $100/month Claude Max 5x plan.
- The user is a CapCut beginner and requires step-by-step instructions in plain language.
- The system should learn one main editor style across brands. Logos, colours, fonts and CTAs are project assets, not separate editing models.
- The normal job input is a script pack and a large raw-footage folder, often around 2 GB. A finished reference may improve learning but is not required. Approximately 10–20 good outcomes make personalisation substantially stronger.
- CapCut projects are not required. If a disposable local project becomes available later, integration may be tested as an optional enhancement.
- Raw footage may be eligible for cleanup after the final, script and learning capsule are verified. The product must provide a recoverable **Finish & Free Space** flow; it must never silently or permanently delete originals.
- The objective is maximum time saving without risking source media or original CapCut projects.
- Additional mandatory spend is exactly $0. Use existing Claude Max allowance and free/local components; never require paid overage, API billing, hosting, Remotion, CapCut Pro or another subscription.

## 3. Optional CapCut-write gate

The primary local render workflow must proceed without reading or writing any CapCut project. **Never write to a live or original CapCut project.** If optional direct integration is developed later, first complete the compatibility canary.

The installed CapCut version must be read from the application bundle and from a throwaway project. Run the chosen draft tool's version and diagnostic commands against a duplicated canary project. Direct project writes remain disabled until all of these are true:

- CapCut is closed.
- The project is a disposable duplicate.
- Every relevant project file is backed up with hashes.
- The draft is readable and its canonical timeline file is identified.
- The tool does not report an unsupported or write-guarded version.
- A small caption-only mutation opens successfully in CapCut.
- The mutation survives saving, closing and reopening CapCut.
- Automatic restore returns the canary project to its exact pre-test hashes.
- The test passes ten consecutive times.

If any check fails, keep direct integration disabled. Local preview/final rendering and optional file-based CapCut Free handoff must still work. Do not force-write or bypass a version guard.

## 4. Non-negotiable product rules

1. Never modify a user's only copy of a project.
2. Never write while CapCut is running.
3. Never use `--force-write` automatically.
4. Never remove source media without the verified local-only cleanup gates and explicit owner confirmation.
5. Every generated CapCut project must be clearly named as a Coach duplicate.
6. Every mutation must be atomic, backed up, hashed, logged and reversible.
7. Video processing is local by default.
8. Claude receives text and a small number of selected low-resolution frames, not entire raw video files.
9. Additional paid Claude usage must remain disabled by default.
10. The user must approve a proposed edit before a final publish render or any optional direct CapCut mutation.
11. A failure in Claude must not disable local transcription, cutting, proxy creation, caption generation or QC.
12. The application must remain usable through a simple browser UI even if macOS Accessibility automation is unavailable.
13. macOS UI automation is optional, version-scoped and never the only path to completing an edit.
14. Do not claim that a generated edit is professional, publish-ready or performance-optimised until the user has reviewed it.
15. Do not silently reuse copyrighted music, stock media or Premium assets outside the licensing context in which CapCut provides them.
16. Never remove source media automatically. Cleanup requires an approved final, completed learning capsule, an exact file list/size preview, explicit confirmation, cross-project reference checks and a recoverable move to macOS Trash.
17. CapCut account/Cloud/Team Space and Google Drive are permanently read-only. Cleanup may remove only Coach-managed local staging/caches and explicitly approved standalone local raw files; it must never delete from cloud or from a mounted/synchronised cloud folder.
18. Zero additional cost is a release blocker. A paid dependency/service may be documented only as a rejected alternative, never placed on the required or recommended path.

## 5. Product modes

### Review First Cut — default

Coach organises the job, renders three candidates and asks for one easy choice before producing a final local MP4.

### Guide Me

Coach gives one action at a time, explains why it matters, shows where the CapCut control is, and records whether the user needed help.

### Autopilot — earned after safe use

After at least five successfully reviewed jobs, Coach may automatically select its best candidate and render it. The user still approves publishing, cleanup and any optional CapCut project action.

## 6. Definition of success

For the initial supported formats—15–90-second vertical scripted reels, treatment/promotional montages, talking-head/educational and testimonial videos—the system is successful when:

- it reduces median hands-on editing time by at least 40% across five unseen test videos;
- a first-time user with no historical examples can generate and review three local previews;
- the selected edit renders to a valid local MP4 without CapCut or a paid renderer;
- originals are never modified or lost;
- captions contain no time overlaps and an SRT is available for optional CapCut import;
- the user can complete the remaining workflow without Terminal;
- every requested CapCut instruction names the exact verified control and expected result;
- after enough approved jobs exist, at least 60% of the proposed timeline duration remains unchanged across the evaluation set;
- the application clearly admits uncertainty and asks for a choice instead of inventing one.

The stretch target after refinement is a 60–80% reduction in hands-on time for repeatable formats. Do not make that a release gate or guarantee.

## 7. Pack contents and reading order

1. `00_READ_ME_FIRST.md` — project scope and non-negotiables.
2. `01_MASTER_PRODUCT_SPEC.md` — full behaviour, architecture and data model.
3. `02_OPEN_SOURCE_RESEARCH.md` — repository evaluation, licensing and source links.
4. `03_IMPLEMENTATION_PLAN.md` — phased build from compatibility spike to packaging.
5. `04_CLAUDE_CODE_RUNBOOK.md` — how Claude Code should execute the work efficiently.
6. `05_ACCEPTANCE_TESTS.md` — objective release and safety gates.
7. `06_DATASET_AND_LEARNING_GUIDE.md` — how to ingest paired raw/final examples and learn style.
8. `07_START_PROMPT_FOR_CLAUDE_CODE.md` — the first prompt to paste into Claude Code.
9. `08_SIMPLE_USER_OUTCOME.md` — plain-English explanation for the owner.
10. `09_API_CONFIG_AND_STORAGE_CONTRACT.md` — concrete API, configuration, job and file contracts.
11. `10_RISK_REGISTER.md` — risks, mitigations and release blockers.
12. `11_OWNER_QUICKSTART.md` — beginner steps from opening Claude Code to the first useful edit.
13. `12_COST_AND_OPERATING_BUDGET.md` — mandatory/optional cost, allowance and spend-stop rules.
14. `13_GOOGLE_DRIVE_AND_LARGE_MEDIA.md` — multi-gigabyte ingest, selected Drive folders and strict cloud read-only boundaries.
15. `14_PREMIUM_UX_DESIGN_SYSTEM.md` — the polished Mac application experience and visual system.
16. `15_AUTOMATION_FIRST_ENGINE.md` — local rendering, format playbooks and maximum automation.
17. `16_ZERO_EXAMPLE_COLD_START.md` — useful first edits without training examples or CapCut projects.
18. `17_AUTONOMY_POLICY_AND_HUMAN_GATES.md` — what runs automatically and what always needs approval.
19. `18_REFERENCE_QUALITY_AND_AUDIO_DNA.md` — same-footage target comparison, audio intelligence and measurable parity tests.

## 8. Decisions already made

- Local-first; no SaaS, billing, authentication or multi-tenancy.
- Python FastAPI backend, React/TypeScript frontend, SQLite database.
- FFmpeg for media operations; whisper.cpp for local transcription on Apple Silicon.
- No Docker for the normal Mac runtime because CapCut, Metal, local folders, launchd and Accessibility need host integration.
- One universal Style DNA, with lightweight asset packs for logos, fonts, colours and CTAs.
- Deterministic local analysis before Claude. Claude is a decision layer, not the video processing engine.
- FFmpeg/ffprobe, VideoToolbox and locally generated ASS/SVG/raster graphics are the free rendering foundation; Remotion is excluded.
- The local RenderGraph and MP4 renderer ship before any CapCut integration.
- CapCut Free handoff is optional. Direct-write support is an optional future adapter enabled only for an exact tested app/schema combination.
- Zero-example cold start is the default, with Clean/Enhanced/Bold candidates and reversible Coach ideas.
- Audio intelligence is mandatory: speech, music, onsets, phrase timing, mixing and QC influence the edit even when automatic music selection is disabled.

## 9. Decisions still requiring evidence

- Optional integration only: exact CapCut version and project schema on the user's Mac.
- Exact M2 model, RAM and free storage.
- Whether the selected CapCut version exposes enough Accessibility metadata for reliable control.
- Which whisper.cpp model meets the user's accuracy/speed needs.
- Measured first-job quality for each supported format and which ambiguities need one simple user choice.
- Whether optional finished examples can be reliably matched to their raw footage.
- Optional only: whether a disposable local CapCut project passes the exact-version direct-write canary.

The implementation plan converts each uncertainty into an explicit experiment and gate.
