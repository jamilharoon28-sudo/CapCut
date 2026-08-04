# CapCut Coach.app (macOS)

A native launcher: a thin AppKit + `WKWebView` window (`Sources/main.swift`) that
starts the local FastAPI backend on a free loopback port, waits for health,
injects the per-install bearer token as `window.__COACH_TOKEN__`, and shows the
bundled React UI. One process, one origin, no Terminal after the first build.

## Build it (on the Mac)

```bash
./scripts/bootstrap.command       # once: installs backend + UI deps
./scripts/build-macos-app.sh      # produces ./dist/CapCut Coach.app
open "dist/CapCut Coach.app"      # or drag it into /Applications
```

`build-macos-app.sh` builds the UI (`pnpm build`), assembles the `.app` bundle
with the built UI in `Resources/ui`, writes a `launch.json` with this Mac's
absolute backend/venv paths, compiles the Swift launcher with `swiftc`, and
ad-hoc-signs it so Gatekeeper allows your own local build.

## Why a launcher (not an embedded Python)

For a personal, single-user tool the app launches the backend from the repo's
`.venv` via absolute paths baked into `launch.json` at build time — robust and
simple, no fragile relocatable-venv or notarization dance. The browser at
`http://127.0.0.1:<port>` remains the recovery fallback.

## Not built in CI

This target needs `swiftc` + Xcode CLT and only builds on macOS. The Swift source
is authored and reviewed; compile it on the Mac with the script above.
