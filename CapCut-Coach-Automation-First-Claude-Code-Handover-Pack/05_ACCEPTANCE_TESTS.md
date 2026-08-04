# Acceptance, Safety and Evaluation Tests

No release is complete until the required-path tests are run and results are recorded. Tests requiring the user's Mac/footage may be marked `BLOCKED BY EVIDENCE`; they must never be marked passed by simulation alone. CapCut-specific tests are release-blocking only when that optional adapter is enabled.

## 1. Safety tests — release blockers

### S1 Original immutability

- Hash every original source media file and original CapCut project file before a full workflow.
- Run ingestion, analysis, draft generation, CapCut handoff, export review and cleanup.
- Re-hash originals.
- Pass: every hash is identical and no mtime changed without explicit user action.

### S2 Open-CapCut write guard

- Start CapCut and open the canary project.
- Request a direct Coach mutation.
- Pass: mutation is queued/refused; no target file changes.

### S3 Unsupported-version guard

- Feed a fixture with a beyond-evidence version/schema.
- Pass: read-only inspection may occur, but all mutations refuse without a hidden bypass.

### S4 Duplicate-only target

- Attempt to target an original/non-Coach project.
- Pass: transaction refuses and directs the user to create a duplicate.

### S5 Atomic failure

- Inject a failure halfway through a draft mutation.
- Pass: no partial project becomes visible; temporary data is isolated; original and prior duplicate remain intact.

### S6 Backup and restore

- Perform a supported mutation, restore backup, compare all relevant hashes.
- Pass: restored files match exactly.

### S7 Path traversal/symlink

- Submit `../`, absolute unapproved roots, symlink escapes and shell metacharacters.
- Pass: rejected without command execution or external writes.

### S8 Paid-overage guard

- Exhaust/mock Claude allowance.
- Pass: Claude-assisted stages pause/fallback; no additional paid usage occurs unless the user explicitly changes the setting.

### S9 Delete semantics

- Use **Delete Coach Analysis**.
- Pass: caches/database records are removed as described; originals and CapCut projects remain.

### S10 Emergency UI-automation stop

- Begin an Accessibility sequence and trigger emergency stop/unexpected dialog.
- Pass: automation halts immediately and does not resume silently.

### S11 Zero-cost dependency and network gate

- Run a fresh required-path install and project with CapCut absent, no Remotion licence, no API key and no payment method.
- Pass: script+raw produces three previews and a final MP4; dependency manifest and network trace show no paid/licence-gated renderer, hosted service, overage or purchase path.

## 2. Functional tests

### F1 Onboarding

- Detect chip, RAM, free storage and Claude CLI status; detect CapCut version if installed without requiring a project root.
- User can correct any failed autodetection through a picker.

### F1A Zero-example local final

- Start with an empty Style DNA database, no finished references and no CapCut project.
- Import one supported script/raw fixture and generate Clean, Enhanced and Bold RenderGraphs/previews.
- Choose Enhanced, render the final MP4 and validate container, codec, A/V sync, dimensions, captions, mandatory script facts and source hashes.
- Pass: the job completes locally and every uncertain grouping is surfaced as a small explicit choice rather than silently guessed.

### F2 Ingest

- Import MOV, MP4, portrait, landscape, rotated, VFR and no-audio fixtures.
- Media metadata and warnings are correct.
- Register individual 2 GB, 10 GB and 50 GB fixtures without HTML multipart upload or loading the full file into memory.
- Pause/restart during incremental hash, Drive staging and proxy work; resume without corrupt output or duplicate processing.

### F2A Selected Google Drive folder

- Connect a streamed Drive-for-desktop folder containing scripts, raw footage and finals; only the selected subtree is indexed.
- Native Drive-adapter tests mock list/metadata/download only and fail the build if any remote write/delete/move/trash/permission method is reachable.
- Cleanup removes Coach staging only. CapCut Cloud/account/Space, Google Drive and mounted/synchronised source files remain byte-for-byte and metadata unchanged.

### F3 Cache

- Process the same content under the same config twice.
- Second run reuses deterministic outputs.
- Changing tool/model/config invalidates only affected cache stages.

### F4 Transcription

- Word timestamps are monotonic and inside media duration.
- SRT is UTF-8, parseable and contains no negative/overlapping timestamps.
- Custom vocabulary correction retains provenance.

### F4A Script-pack import

- Import a ZIP containing Word campaign scripts, recording instructions and reusable cutaway lists, including names/folders with spaces.
- Pass: extraction blocks traversal/zip bombs; reel/shot headings, time ranges, camera directions, speech, overlays, cutaways, pacing, transitions, end cards and cross-references survive in a reviewable typed shot plan. Music fields may be ignored by owner preference.
- Unknown content is retained rather than silently dropped; user corrections persist.

### F5 Dialogue detection

- Golden fixtures cover silence, filler, repeated take, false restart and intentional dramatic pause.
- The system identifies candidates and allows restoration.

### F6 Edit plan

- All references resolve to known assets/units.
- No source or timeline interval is invalid.
- Target-duration overflow is explained rather than silently truncating meaning.

### F7 Preview render

- Audio/video remain in sync.
- No blank gaps unless intentional.
- Captions match internal plan.

### F8 Claude schema

- Valid response accepted.
- Malformed JSON, unknown ids, invented paths, duplicate ids and invalid ranges rejected.
- One repair retry maximum.

### F9 Optional CapCut Free handoff

- Package includes preview, ordered clips, clean audio, UTF-8 SRT, assets and manifest.
- CapCut imports the SRT into editable caption blocks.
- This test is non-blocking when CapCut is absent; F1A remains the primary completion path.

### F10 Direct template clone

- Only run if compatibility status permits.
- Ten consecutive generated projects open, save, close and reopen.
- Effects/captions/media remain present.
- No corruption warning.

### F11 Export detection

- Partial/growing files are ignored until stable.
- Correct project match is automatic when unambiguous.
- Ambiguous match asks user rather than guessing.

### F12 QC

- Detect seeded black frame, loud peak, caption overlap, misspelling, missing CTA and wrong aspect ratio.
- Each finding includes timecode, severity and suggested action.

### F13 Feedback

- Compare proposed/final timelines and correctly classify retained, removed, shortened and moved units on fixtures.
- No Style DNA update without approval.

## 3. Style-learning evaluation

### Dataset split — only when historical examples exist

- Minimum 15 paired examples recommended.
- Use approximately 80% for Style DNA and 20% held out.
- Never evaluate on the same examples used to fit settings.

### L1 Raw/final alignment coverage

- Measure percent of finished duration matched to raw assets.
- Target on clean talking-head pairs: at least 95% or explicit unmatched labels.

### L2 Alignment boundary error

- Manually annotate a representative sample.
- Report median and 95th-percentile boundary error.
- Do not hide outliers behind average coverage.

### L3 Style extraction sanity

- Compare learned medians/distributions to manual review for shot length, opening delay, caption density, B-roll frequency and CTA duration.
- User approves the readable profile.

### L4 Held-out edit retention

- Produce drafts for held-out raw footage and compare with approved final edits.

### L5 Coach Magic control

- Generate Clean, Enhanced and Bold candidates from the same fixture.
- Pass: all mandatory script facts remain; every `COACH_IDEA` has a reason/confidence and can be removed independently; Clean contains no unapproved experimentation; rejected idea types reduce future proposal weight without corrupting Style DNA.
- Initial release target after refinement: at least 60% of proposed timeline duration remains unchanged.

### L5 A/B preference

- Present pairs that differ in one meaningful dimension.
- Verify feedback updates the expected preference weight without changing unrelated dimensions.

### L6 Conflicting examples

- Import inconsistent examples.
- System reports multimodality/low confidence instead of averaging into a nonsensical hard rule.

## 4. Performance and M2 tests

Record exact Mac model, RAM, macOS, power state, tool versions and input properties.

### P1 Balanced-mode benchmark

- Input: 10-minute 1080p talking-head fixture.
- Measure proxy, transcription, analysis and preview stages independently.
- Record wall time, peak memory, temporary storage and final cache size.

### P2 Concurrency

- Queue three projects.
- Pass: only one heavy media stage runs at once; UI and light jobs remain responsive.

### P3 CapCut coexistence

- Open and scrub a normal CapCut project while Coach runs Balanced mode.
- Pass: Coach pauses/lowers work according to policy and does not attempt writes.

### P4 Low storage

- Simulate below-threshold free space.
- Pass: new proxy/render pauses before consuming critical space.

### P5 Battery policy

- Disconnect power under Quiet/Balanced policies.
- Pass: behaviour matches user setting and is visible.

### P6 Cache cleanup

- Reach configured cache budget.
- Pass: only recomputable unpinned cache items are removed; active outputs and originals remain.

### P7 Finish & Free Space safety

- Use a fixture representing 2 GB of raw media, scripts, approved final, a shared source hash and an incomplete learning job.
- Pass: source cleanup is blocked until final/capsule verification completes; shared media is not targeted silently.
- After all gates pass, the UI shows exact targets/count/bytes and requires confirmation. Only approved raw files move to macOS Trash; scripts/final/capsule remain under the recommended policy; only recomputable caches are removed; Trash is never emptied.
- Inject a mid-move failure. Pass: completed/pending items are journaled, no unrelated file moves and retry is idempotent.

No hard thermal-limit claim is required. Rely on one-job design, low priority, proxies, cache and macOS protection; display measured behaviour.

## 5. Beginner usability tests

### U1 No-Terminal path

A first-time user must install, open, process, render a final MP4 and review without Terminal or CapCut after bootstrap.

### U2 Three-action clarity

From Home, the user can identify how to create, continue and review an edit without documentation.

### U2A Three-source clarity

- A beginner adds a script ZIP and raw folder/selected Drive folder, optionally adds a finished reference, confirms automatic grouping and understands which files are temporary.
- Pass: no terminal/path/API terminology; Drive and CapCut cloud are visibly labelled read-only; the local cleanup preview is unambiguous.

### U3 Guided task completion

A beginner completes caption styling, voice enhancement, music ducking, CTA and export using Guided Mode only.

### U4 One instruction at a time

Guided Mode never presents a wall of technical instructions by default.

### U5 Unknown UI

When CapCut UI does not match the knowledge map, Coach says it cannot safely identify the control and requests a screenshot/manual selection.

### U6 Recovery comprehension

The user can restore a generated project or switch to safe handoff using plain-language controls.

### U7 Explanation quality

Every recommendation answers: what to do, where, why, expected result and common mistake.

## 6. Time-saving study

### Baseline

For at least three representative videos, record:

- active footage-review time;
- active rough-cut time;
- caption time;
- B-roll/audio/polish time;
- QC/revision time;
- total hands-on time.

### Coach condition

Repeat on at least five unseen comparable videos, separating unattended processing from hands-on time.

### Release target

- Median hands-on time reduction of at least 40% for the v1 supported format.
- No increase in critical quality/safety defects.
- Report the actual result; do not substitute predicted savings.

## 7. Regression corpus

Maintain small sanitised fixtures for:

- each supported CapCut schema/layout;
- one unsupported future version marker;
- portrait/landscape/VFR/missing-audio media;
- clean and noisy speech;
- repeated take and dramatic pause;
- SRT with names, punctuation and Unicode;
- optional CapCut Free master-template snapshot without personal paths/media;
- golden raw/final alignment pairs with redistribution rights.

Fixtures must not contain client-confidential media or absolute user paths.

## 8. Final release report template

```text
Release:
Date:
Mac model/RAM/macOS:
CapCut version/build/schema (optional):
Direct adapter status:
Tests passed:
Tests failed:
Tests blocked by evidence:
Ten-run canary result:
Original immutability result:
Median hands-on time reduction:
Known limitations:
Recovery test result:
Third-party notice status:
Owner approval:
```
