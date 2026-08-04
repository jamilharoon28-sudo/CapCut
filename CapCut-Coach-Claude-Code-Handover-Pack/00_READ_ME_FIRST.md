# CapCut Coach — Read This First

Status: complete implementation handover  
Prepared: 4 August 2026  
Target computer: one Apple-silicon M2 Mac  
Target editor: CapCut Desktop Premium  
Target user: one beginner editor; no commercial multi-user product  
Primary content: short-form talking-head, educational and promotional videos  

## 1. The outcome

Build a private, local application called **CapCut Coach**. It watches the user's CapCut and media folders, learns one universal editing style from paired raw footage and finished videos, prepares strong first cuts, transfers them into CapCut as safely and automatically as the installed CapCut version permits, teaches the user the remaining CapCut Premium steps, reviews exports, and learns from the user's corrections.

The finished user experience must be simpler than the technology behind it. The user should not need to understand Python, FFmpeg, JSON, models, APIs, terminals, project schemas or file paths.

The default workflow is:

1. Add footage or begin a CapCut project.
2. CapCut Coach detects it.
3. Coach transcribes, analyses and creates a first cut.
4. The user previews the proposed edit.
5. The user presses **Open in CapCut**.
6. Coach either opens a safe generated duplicate project or performs the safest available prepared handoff.
7. Guided Mode gives one CapCut Premium instruction at a time.
8. The user exports normally.
9. Coach detects and reviews the export automatically.
10. Coach learns from differences between its proposal and the approved final export.

## 2. Known user constraints

- The user owns an M2 Mac. The exact model, RAM and storage are not yet known.
- The user owns CapCut Premium. The exact numerical CapCut Desktop version is not yet known.
- The application is only for the user and may run as a local service on the same Mac.
- The user has Claude Code in Terminal and a $100/month Claude Max 5x plan.
- The user is a CapCut beginner and requires step-by-step instructions in plain language.
- The system should learn one main editor style across brands. Logos, colours, fonts and CTAs are project assets, not separate editing models.
- The normal learning input is a three-part example: a script pack, a large raw-footage folder (often around 2 GB) and the approved finished video. Approximately 15–20 correctly matched examples are recommended.
- If the editor's CapCut project is available through the user's Premium account/Space or local Mac, it is optional but exceptionally valuable because it exposes exact timelines, text, effects and Premium asset identifiers.
- Raw footage is disposable after the final, script, CapCut evidence and learning capsule are verified. The product must provide a recoverable **Finish & Free Space** flow; it must never silently or permanently delete originals.
- The objective is maximum time saving without risking source media or original CapCut projects.

## 3. Mandatory first gate

**Do not begin by writing to live CapCut projects.** First complete the compatibility spike in Phase 0.

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

If any check fails, retain the safe handoff workflow and Guided Mode. Do not force-write or bypass a version guard.

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
10. The user must approve a proposed edit before any direct CapCut mutation.
11. A failure in Claude must not disable local transcription, cutting, proxy creation, caption generation or QC.
12. The application must remain usable through a simple browser UI even if macOS Accessibility automation is unavailable.
13. macOS UI automation is optional, version-scoped and never the only path to completing an edit.
14. Do not claim that a generated edit is professional, publish-ready or performance-optimised until the user has reviewed it.
15. Do not silently reuse copyrighted music, stock media or Premium assets outside the licensing context in which CapCut provides them.
16. Never remove source media automatically. Cleanup requires an approved final, completed learning capsule, an exact file list/size preview, explicit confirmation, cross-project reference checks and a recoverable move to macOS Trash.
17. CapCut account/Cloud/Team Space and Google Drive are permanently read-only. Cleanup may remove only Coach-managed local staging/caches and explicitly approved standalone local raw files; it must never delete from cloud or from a mounted/synchronised cloud folder.

## 5. Product modes

### CapCut Finish — default

Coach creates most of the edit. The user finishes and approves it in CapCut Premium.

### Learn Mode

Coach gives one action at a time, explains why it matters, shows where the CapCut control is, and records whether the user needed help.

### Autopilot Preview

Coach renders a complete local preview for review. It must still require approval before publishing or modifying a CapCut project.

## 6. Definition of success

For the initial supported format—single-speaker, 30–90-second vertical videos—the system is successful when:

- it reduces median hands-on editing time by at least 40% across five unseen test videos;
- its generated rough cut opens reliably through the supported handoff path;
- originals are never modified or lost;
- captions contain no time overlaps and are editable in CapCut;
- the user can complete the remaining workflow without Terminal;
- every instruction names the exact CapCut control and expected result;
- at least 60% of the proposed timeline duration remains unchanged in the user's approved final across the initial evaluation set, after the style profile has been trained;
- the application clearly admits uncertainty and asks for a choice instead of inventing one.

The stretch target after refinement is a 60–80% reduction in hands-on time for repeatable talking-head formats. Do not make that a release gate or guarantee.

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

## 8. Decisions already made

- Local-first; no SaaS, billing, authentication or multi-tenancy.
- Python FastAPI backend, React/TypeScript frontend, SQLite database.
- FFmpeg for media operations; whisper.cpp for local transcription on Apple Silicon.
- No Docker for the normal Mac runtime because CapCut, Metal, local folders, launchd and Accessibility need host integration.
- One universal Style DNA, with lightweight asset packs for logos, fonts, colours and CTAs.
- Deterministic local analysis before Claude. Claude is a decision layer, not the video processing engine.
- Template cloning is preferred over attempting to click every Premium control.
- A read-only CapCut integration ships before any write integration.
- CapCut direct-write support is enabled only for the exact tested app/schema combination.

## 9. Decisions still requiring evidence

- Exact CapCut version and project schema on the user's Mac.
- Exact M2 model, RAM and free storage.
- Whether the selected CapCut version exposes enough Accessibility metadata for reliable control.
- Whether local Premium effect resource identifiers survive safe template duplication.
- Which whisper.cpp model meets the user's accuracy/speed needs.
- Whether the first training dataset contains clean one-to-one raw/final pairs.
- Whether generated CapCut drafts can be exported on this Mac version without a Windows dependency.

The implementation plan converts each uncertainty into an explicit experiment and gate.
