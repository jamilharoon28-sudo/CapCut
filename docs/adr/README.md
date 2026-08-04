# Architectural Decision Records

Each decision below is recorded per `04_CLAUDE_CODE_RUNBOOK.md §5`. Status:
Accepted unless noted. These are durable; change them only with a new ADR.

## ADR-0001 — Local FastAPI + React, not Electron/Tauri (v1)
**Context.** One-user local tool needing FFmpeg, Metal/VideoToolbox, launchd,
macOS Accessibility, and native folder access.
**Decision.** Python FastAPI service + React/Vite UI, wrapped by a thin Swift
`WKWebView` shell (`CapCut Coach.app`) with a browser fallback for recovery.
**Consequences.** Full access to Python's media ecosystem and native macOS APIs
without an Electron runtime; two processes to supervise via launchd.

## ADR-0002 — whisper.cpp local transcription, not cloud
**Decision.** Transcribe locally with whisper.cpp on Apple Silicon.
**Why.** Privacy (no raw media leaves the Mac), no per-minute cost, offline
capability. A model manager pins checksums; the model choice is benchmarked.

## ADR-0003 — Deterministic Style DNA, not foundation-model fine-tuning
**Decision.** Learn the editor's fingerprint as explainable distributions
(pace, margins, caption density, B-roll frequency, CTA duration) with provenance
and rollback. No opaque fine-tuning.
**Why.** Reviewable, reversible, requires far less data (15–20 pairs), and never
invents accuracy.

## ADR-0004 — Internal edit schema + adapters
**Decision.** A single typed edit-plan contract (integer microseconds) is the
source of truth; every output (preview, SRT, CapCut handoff/clone) is an adapter.
CapCut-specific ids never leak into editorial planning.

## ADR-0005 — Safe handoff is a permanent fallback
**Decision.** The Finder + CapCut handoff package (ordered clips, clean audio,
UTF-8 SRT, assets, manifest, guide) always works, independent of direct-write
status. Direct writes never become the only path.

## ADR-0006 — Exact-version feature flag for direct CapCut writes
**Decision.** `direct_capcut_write_enabled` defaults OFF and only turns on for a
CapCut version/build/schema that passed the ten-run canary + restore test. Any
CapCut update drops the effective status to `CANARY_REQUIRED` or safer.

## ADR-0007 — AXUIElement-first automation, not coordinate clicking
**Decision.** Guided/automated steps resolve controls by Accessibility role /
identifier / title before any coordinates. Unknown state pauses and asks; it
never guesses clicks. Screen capture is user-triggered only.

## ADR-0008 — No Docker in the normal Mac runtime
**Decision.** Run natively. CapCut, Metal, local folders, launchd, and
Accessibility need host integration that containers obstruct.

## ADR-0009 — One universal editing style + separate asset packs
**Decision.** A single Style DNA models the editor. Logos, colours, fonts, and
CTAs are lightweight per-brand asset packs, not separate style models.

## ADR-0010 — Claude as a constrained decision provider, not an executor
**Decision.** Claude receives only pre-validated ids, transcript units, numeric
features, and selected low-resolution evidence, and returns only
schema-conformant JSON. Its output is untrusted: ids/ranges are validated, one
repair retry is allowed, and it never runs commands or reads/writes files. A
deterministic fallback covers every Claude-assisted stage.
