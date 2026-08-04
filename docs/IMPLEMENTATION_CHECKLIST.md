# Implementation Checklist (Phases 0–10)

Legend: ✅ done · 🟡 partial/scaffolded · ⛔ BLOCKED BY EVIDENCE (needs Mac /
CapCut / dataset) · ⬜ not started.

This checklist is the tracked map required by `07_START_PROMPT_FOR_CLAUDE_CODE.md`.
It reflects what has been built in the Linux CI scaffold. Gated items are built
where possible and clearly blocked where they need the owner's hardware.

## Phase 0 — Evidence & compatibility spike
- ✅ P0.1 Repository + `CLAUDE.md` + environment doctor (`scripts/doctor.sh`).
- ✅ P0.1 CapCut bundle/version/build/source detection logic (`capcut/detect.py`,
  runs on macOS; degrades on Linux).
- ✅ P0.1 Project-root discovery via known paths + user selection (no hardcoded path).
- 🟡 P0.2 `capcut-cli` safe-trial harness authored; ⛔ run requires macOS + CapCut.
- ✅ P0.2 Compatibility registry model + `docs/capcut-compatibility.md` template.
- 🟡 P0.3 Caption-only canary procedure + ten-run automation authored; ⛔ run blocked.
- 🟡 P0.4 Swift read-only Accessibility probe authored (`apps/mac-bridge`); ⛔ run blocked.
- 🟡 P0.5 M2 benchmark harness authored (`scripts/benchmark.py`); ⛔ run blocked.
- **Exit gate:** ⛔ ten-run canary not yet run → direct writes remain OFF.

## Phase 1 — Local application foundation
- ✅ FastAPI + SQLite (WAL) + migrations scaffold.
- ✅ Loopback-only bind (`127.0.0.1`) + local bearer token.
- ✅ Typed config / storage layout (`config.py`), Application Support paths.
- ✅ Project/job state machine + persisted idempotent queue.
- ✅ Cancellation, resume, idempotency keys.
- ✅ System doctor endpoint + status.
- 🟡 `CapCut Coach.app` Swift/WKWebView shell scaffolded (macOS build blocked).
- 🟡 launchd install/uninstall scripts authored (macOS).
- ✅ Structured logs with path/transcript redaction.
- **Exit gate:** ✅ restart mid-job does not corrupt DB (tested); other items ⛔ on macOS.

## Phase 2 — Media intake, cache & transcription
- ✅ Approved-root selection + realpath/symlink path-safety guard.
- ✅ Three-source intake model (script pack / raw footage / finished refs).
- ✅ Safe `.docx`/`.pdf`/text/ZIP script parser (zip-bomb + traversal guards).
- ✅ Content-addressed cache (content+tool+config hash).
- 🟡 FFmpeg/ffprobe wrappers (proxy, audio extract) — degrade when binary absent.
- 🟡 whisper.cpp transcription wrapper + model manager/checksums — ⛔ model run blocked.
- ✅ SRT writer (UTF-8, monotonic, non-overlapping) + validator.
- 🟡 Drive-for-desktop streamed-folder selection (read-only staging) scaffolded.
- 🟡 Learning-capsule + local-only Finish & Free Space preview scaffolded (cleanup OFF).
- **Exit gate:** ✅ identical re-import reuses cache (tested); original hashes unchanged (tested).

## Phase 3 — Deterministic dialogue rough cut
- ✅ Transcript → phrase/sentence segmentation.
- ✅ Silence / filler / repeated-phrase / restart detection.
- ✅ Adjustable natural-cut margins + clipped-phoneme risk flag.
- ✅ Internal edit-plan schema (microseconds) + validator.
- ✅ 30/45/60s duration candidates.
- 🟡 Preview / removed-content preview render (needs FFmpeg on host).
- **Exit gate:** ✅ all ranges valid & non-overlapping, within media duration (tested); restore-a-unit (tested).

## Phase 4 — Claude decision layer
- ✅ One `ClaudeDecisionProvider` interface.
- ✅ JSON-Schema-validated outputs; one repair retry; unknown-id/range rejection.
- ✅ Decision cache keyed by input/model/prompt version.
- ✅ Allowance telemetry + hard stop before paid overage.
- ✅ Deterministic fallback when Claude unavailable.
- **Exit gate:** ✅ malicious output cannot touch files/commands (tested); deterministic cut without Claude (tested).

## Phase 5 — Paired alignment & universal Style DNA — ⛔ BLOCKED (needs dataset)
- 🟡 Dataset import/validation model + quality labels scaffolded.
- ⬜ Audio-first alignment (fingerprint + cross-correlation/DTW) — needs footage.
- ⬜ Style DNA v1 aggregation, provenance, rollback, approval — needs dataset.

## Phase 6 — Style-aware planning, captions, B-roll, audio — ⛔ depends on Phase 5
- 🟡 Caption line-break/duration/position logic scaffolded.
- ⬜ Face/subject crop, punch-in schedule, B-roll matching, ducking — needs media.

## Phase 7 — CapCut connection
- 🟡 P7A read-only watcher (debounce/stability) scaffolded.
- ✅ P7B guaranteed handoff package builder (ordered clips, SRT, manifest, guide).
- ⛔ P7C direct template clone — gated on Phase 0 canary (OFF).

## Phase 8 — Guided CapCut Premium Mode — ⛔ needs exact CapCut version
- 🟡 Versioned guidance knowledge-base model + one-step UI scaffolded.
- ⬜ Verified control paths, Accessibility actions, emergency stop — needs macOS.

## Phase 9 — Export watcher, QC & feedback learning
- 🟡 Export watcher (size-stability) scaffolded.
- ✅ Deterministic QC checks (caption overlap, aspect, duration) implemented + tested.
- ⬜ Editorial QC via Claude, proposed-vs-final diff, learning — needs media/dataset.

## Phase 10 — Packaging, docs & operational hardening
- ✅ Command wrappers (`scripts/*`).
- ✅ THIRD_PARTY_NOTICES + dependency policy.
- 🟡 launchd installer, DB backup/restore scripts authored (macOS run blocked).
- ⬜ Full user guide with screenshots, update checker, re-probe — later.

## Cross-cutting release blockers (from `05_ACCEPTANCE_TESTS.md`)
- S1 original immutability — ✅ unit-tested on synthetic fixtures.
- S3 unsupported-version guard — ✅ tested.
- S7 path traversal/symlink — ✅ tested.
- S8 paid-overage guard — ✅ tested.
- S2, S4, S5, S6, S9, S10 — 🟡 logic present; ⛔ full run needs CapCut/macOS.
