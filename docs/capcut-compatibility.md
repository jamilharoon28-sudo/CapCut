# CapCut Compatibility Record

This file records reproducible evidence about the installed CapCut build. It is
populated by the Phase 0 spike (`scripts/doctor.sh`, `capcut/detect.py`, and the
`/api/v1/capcut/*` endpoints). **Direct writes stay OFF until the ten-run canary
and restore test below pass on the owner's Mac.**

## Registry key (per `04_CLAUDE_CODE_RUNBOOK.md §9`)

| Field | Value |
| --- | --- |
| CapCut semantic version | _pending — read from Info.plist_ |
| Build number | _pending_ |
| macOS version | _pending_ |
| App source (`cc` = International, else JianYing) | _pending_ |
| Top-level schema version | _pending_ |
| Canonical timeline filename / layout | _pending_ |
| Readable / writable evidence status | READ pending / WRITE disabled |
| Supported operations | none confirmed |
| Canary date | not run |
| Fixture hash | n/a |

## Effective status

`CANARY_REQUIRED` (default). Possible values: `READ_ONLY`, `HANDOFF_ONLY`,
`CANARY_REQUIRED`, `DIRECT_WRITE_CAPTION_ONLY`, `DIRECT_WRITE_TEMPLATE_CLONE`,
`BLOCKED`. Any CapCut app update automatically drops this to `CANARY_REQUIRED`
or safer.

## Canary result (P0.3)

- Ten-run caption-only mutation on a **disposable duplicate**: ⛔ not run.
- Exact-hash restore after each run: ⛔ not run.
- Refuse-on-write-guarded/unsupported: ✅ enforced in code.

## Read-only diagnostics (P0.2)

Populate with redacted `info` / `version` / `diagnose` / `lint` output once run
against a duplicated canary project on the Mac. Do not paste absolute home paths.

## Accessibility probe (P0.4)

Record which panels (project home, timeline, Captions, Audio, Export) expose
stable roles / titles / identifiers / actions. ⛔ not run (needs macOS +
granted permission). Probe is strictly read-only — it never clicks.
