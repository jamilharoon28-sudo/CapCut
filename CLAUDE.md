# CLAUDE.md — CapCut Coach permanent rules

These rules govern every change in this repository. They are derived from the
handover pack (`00_READ_ME_FIRST.md` … `14_PREMIUM_UX_DESIGN_SYSTEM.md`) and are
**non-negotiable**. If an instruction ever conflicts with reproducible evidence
from the installed CapCut build, preserve safety, document the evidence, and
propose the smallest correction — never silently override these rules.

## What this product is

- A **private, local** application for **one beginner** editing with **CapCut
  Desktop Premium** on an **Apple-silicon M2 Mac**.
- Not a SaaS. No accounts, cloud hosting, billing, or multi-tenancy — ever.
- The finished experience must be simpler than the technology behind it. Normal
  users never see Python, FFmpeg, JSON, model names, APIs, terminals, project
  schemas, or file paths.

## Safety rules (release blockers)

1. **Original media and original CapCut projects are immutable.** Never modify a
   user's only copy of a project.
2. **Never write to a CapCut project while CapCut is running.**
3. **Never use `--force-write` automatically**, bypass a version guard, or target
   the user's only copy.
4. **Direct CapCut writes are disabled** until the exact-version ten-run canary
   and exact restore test pass. They stay behind an off-by-default,
   exact-version feature flag.
5. **Safe handoff must always work**, even when direct integration is disabled.
6. **All heavy video processing is local.** Do not upload full raw videos to
   Claude by default — send text and a small number of selected low-resolution
   frames only.
7. **Claude outputs are untrusted structured suggestions.** Validate ids, ranges,
   and JSON Schema. Never execute model-generated commands or paths.
8. **Bind services to loopback only** (`127.0.0.1`) with a local bearer token.
9. **Additional paid Claude usage is disabled by default.** No hidden overage.
10. **One heavy media job at a time.** Protect battery, storage, and interactive
    CapCut performance.
11. **Never remove source media automatically.** Cleanup requires a verified
    final, a checksummed learning capsule, an exact path/count/size preview,
    cross-project hash checks, and explicit confirmation. Move exact files to
    macOS Trash only — never auto-delete, permanently delete, recurse over broad
    folders, follow symlinks, or empty Trash.
12. **CapCut account/Cloud/Team Space, Google Drive, and every mounted or
    synchronised cloud folder are permanently read-only.** Cleanup may remove
    only Coach-managed local staging/caches and explicitly approved standalone
    local raw files.
13. A failure in Claude must not disable local transcription, cutting, proxy
    creation, caption generation, or QC.
14. Do not claim a generated edit is professional, publish-ready, or
    performance-optimised until the user has reviewed it. The word "automatic"
    is reserved for stages that start from a reliable local event, need no file
    re-selection, report progress/failure, are idempotent, produce a verifiable
    output, and can recover or fall back safely. Prepared Finder + CapCut handoff
    is **assisted handoff**, not automatic editing — label it honestly.

## Engineering rules

- Python 3.12 + FastAPI (managed with `uv`); React + TypeScript + Vite
  (managed with `pnpm`). SQLite in WAL mode with persisted idempotent jobs — no
  Redis/Celery, no Docker in the normal Mac runtime.
- FFmpeg/ffprobe as subprocesses; whisper.cpp for local transcription;
  PySceneDetect for shot boundaries.
- Persisted edit data uses **integer microseconds** (never floating-point
  seconds). A typed internal edit schema is the single source of truth; CapCut
  ids never leak into editorial planning.
- Every feature ships with tests and documentation. Record phase evidence in
  `docs/phase-evidence/`.
- Never commit raw user footage, CapCut projects, transcripts, model binaries,
  credentials, or absolute home paths. Discover the home path at runtime.
- Do not add a dependency without recording license, maintenance, capability,
  network/data behaviour, and a removal strategy (`docs/adr/` + THIRD_PARTY_NOTICES).
- Use small, intentional commits. Never use destructive git commands or rewrite
  user history.
- Mark hardware/data-dependent tests as **BLOCKED BY EVIDENCE** — never falsely
  passed by simulation.

## Repository map

- `apps/backend/` — FastAPI service, deterministic media/edit engine, adapters.
- `apps/frontend/` — React beginner UI implementing `14_PREMIUM_UX_DESIGN_SYSTEM.md`.
- `apps/mac-bridge/` — Swift read-only probe (app/process/version, Accessibility,
  notifications). Built and run **only on macOS**.
- `scripts/` — stable command wrappers (bootstrap, doctor, dev, test, launchd,
  backup, restore).
- `docs/` — checklist, ADRs, compatibility + benchmark records, phase evidence.
- `CapCut-Coach-Claude-Code-Handover-Pack/` — governing specification (source of
  product truth). Do not treat code as truth over the pack.

## Current environment note

This repository was scaffolded in a **Linux CI container**, not on the target
M2 Mac. Every step that requires the Mac, CapCut, or the paired dataset is built
here but recorded as **BLOCKED BY EVIDENCE** until it can be run on the owner's
machine. See `docs/phase-evidence/P0.md`.
