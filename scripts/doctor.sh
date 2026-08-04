#!/usr/bin/env bash
# Environment / CapCut / M2 doctor (Phase 0, P0.1).
# Degrades gracefully off macOS: Mac-only checks are reported as "blocked".
# Never prints secrets. All paths are quoted; spaces are safe.
set -euo pipefail

say() { printf '%s\n' "$*"; }
check() { # name  command...
  local name="$1"; shift
  if command -v "$1" >/dev/null 2>&1; then
    say "  ok    $name ($("$@" 2>/dev/null | head -n1 || true))"
  else
    say "  MISS  $name (not on PATH)"
  fi
}

say "== CapCut Coach doctor =="
say "OS: $(uname -s) $(uname -r)  arch: $(uname -m)"

say ""
say "Toolchain:"
check "python3"  python3 --version
check "uv"       uv --version
check "node"     node --version
check "pnpm"     pnpm --version
check "ffmpeg"   ffmpeg -version
check "ffprobe"  ffprobe -version
# Claude CLI: presence only, never auth/secrets.
if command -v claude >/dev/null 2>&1; then say "  ok    claude (present)"; else say "  MISS  claude"; fi

say ""
if [[ "$(uname -s)" == "Darwin" ]]; then
  say "macOS checks:"
  # RAM / free space
  mem_bytes=$(sysctl -n hw.memsize 2>/dev/null || echo 0)
  say "  RAM: $(( mem_bytes / 1024 / 1024 / 1024 )) GB"
  say "  chip: $(sysctl -n machdep.cpu.brand_string 2>/dev/null || echo unknown)"
  df -h / | awk 'NR==2 {print "  free on /: "$4}'
  # Xcode command line tools
  if xcode-select -p >/dev/null 2>&1; then say "  ok    Xcode CLT"; else say "  MISS  Xcode CLT"; fi
  # CapCut bundle
  for app in "/Applications/CapCut.app" "$HOME/Applications/CapCut.app"; do
    if [[ -d "$app" ]]; then
      plist="$app/Contents/Info.plist"
      ver=$(defaults read "$plist" CFBundleShortVersionString 2>/dev/null || echo "?")
      build=$(defaults read "$plist" CFBundleVersion 2>/dev/null || echo "?")
      say "  ok    CapCut $ver (build $build) at $app"
    fi
  done
  say ""
  say "Next: create ONE disposable 5-second CapCut project (1 video + 1 caption),"
  say "close CapCut, then run the canary via the app or /api/v1/capcut/canary."
else
  say "macOS-only checks: blocked (not macOS)"
  say "  - CapCut bundle/version/build/source detection: blocked"
  say "  - Accessibility probe: blocked"
  say "  - M2 benchmark: blocked"
  say "Run this script on the target M2 Mac to gather Phase 0 evidence."
fi

say ""
say "Doctor complete."
