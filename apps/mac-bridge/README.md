# mac-bridge (macOS only)

A small, **read-only** native probe the Python service shells out to. It reports
CapCut's version/build/source and running state, and performs a **read-only**
Accessibility inspection of the frontmost CapCut window. It never clicks, types,
or changes anything (ADR-0007; CLAUDE.md).

## Build & run (on the Mac)

```bash
cd apps/mac-bridge
swift build -c release
.build/release/mac-bridge version
.build/release/mac-bridge is-running
.build/release/mac-bridge probe     # needs Accessibility permission granted
```

Grant permission in **System Settings → Privacy & Security → Accessibility**.
Without it, `probe` returns `{"granted": false}` instead of guessing.

> This target intentionally does not build in the Linux CI scaffold. Phase 0
> evidence from it is recorded in `docs/phase-evidence/P0.md` as blocked until
> run on the target Mac.
