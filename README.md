# CapCut Coach

A private, **local** editing assistant for one beginner on an **Apple-silicon M2
Mac**. **Automation-first:** Coach turns a folder of raw clips (+ an optional
script) into three finished vertical videos — **Clean / Enhanced / Bold** —
rendered locally with FFmpeg. **CapCut is optional**, not required to get an MP4.
It can also learn one universal editing style over time and prepare a safe CapCut
handoff when you want to finish there.

### Try it in one command (on the Mac, after setup)

```bash
python -m capcut_coach.autocreate ~/Movies/my-raw-clips --seconds 20
# → coach-candidates/clean.mp4, enhanced.mp4, bold.mp4  (1080×1920, no CapCut)
```

Or use the app: **Create → paste a folder path → Create my videos** and play the
three results in the window.

> **Governing specification:** everything in this repository implements the
> handover pack in [`CapCut-Coach-Claude-Code-Handover-Pack/`](CapCut-Coach-Claude-Code-Handover-Pack).
> Read [`CLAUDE.md`](CLAUDE.md) for the permanent, non-negotiable rules and
> [`docs/IMPLEMENTATION_CHECKLIST.md`](docs/IMPLEMENTATION_CHECKLIST.md) for
> phase-by-phase status.

## Safety first

- Original media and original CapCut projects are **immutable**.
- Direct CapCut writes stay **disabled** until an exact-version, ten-run canary
  and restore test pass on the owner's Mac. A safe Finder + CapCut **handoff**
  always works regardless.
- Everything binds to `127.0.0.1` with a local bearer token. No accounts, no
  cloud, no billing. CapCut Cloud / Team Space and Google Drive are permanently
  read-only.

## Status of this scaffold

This tree was built in a Linux CI container, **not** on the target Mac. The
environment-independent core is implemented and tested here:

| Area | State |
| --- | --- |
| Governance, checklist, ADRs | ✅ implemented |
| Phase 0 tooling (doctor, compatibility model, benchmark harness, Swift probe) | ✅ authored — runs gated on macOS |
| Phase 1 backend (loopback FastAPI, bearer auth, SQLite WAL, jobs, projects) | ✅ implemented + tested |
| Phase 2 media wrappers, cache, SRT, script-pack parser, path safety | ✅ implemented (FFmpeg/whisper degrade gracefully when absent) |
| Phase 3 deterministic rough-cut (edit-plan schema, detection, candidates) | ✅ implemented + tested |
| Phase 4 Claude decision provider (schema-validated, fallback, overage guard) | ✅ implemented + tested |
| Frontend shell (design tokens, five destinations, project path) | ✅ implemented |
| Canary / Accessibility / M2 benchmark runs, Style DNA, Guided Mode, QC | ⛔ **BLOCKED BY EVIDENCE** — needs the Mac, CapCut, and the dataset |

See [`docs/phase-evidence/`](docs/phase-evidence) for exactly what was run.

## Quick start (developers)

```bash
# One-time setup (installs uv, pnpm deps, prints a doctor report)
./scripts/bootstrap.command      # on macOS; on Linux CI, see scripts/README

# Environment / CapCut / M2 doctor (degrades gracefully off-Mac)
./scripts/doctor.sh

# Run backend + frontend in development
./scripts/run-dev.sh

# Run the whole test suite
./scripts/test.sh
```

The backend serves `http://127.0.0.1:<assigned-port>/api/v1` (loopback only,
bearer token required). The normal user launches the `CapCut Coach.app` shell —
no Terminal after bootstrap.

## Layout

```
apps/backend/     FastAPI service + deterministic media/edit engine
apps/frontend/    React + TypeScript beginner UI (design tokens)
apps/mac-bridge/  Swift read-only probe (macOS only)
scripts/          bootstrap / doctor / dev / test / launchd / backup / restore
docs/             checklist, ADRs, compatibility & benchmark records, evidence
```

## Licensing

Third-party components are catalogued in
[`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md). This project ships no
copyrighted media; fixtures are synthetic or redacted.
