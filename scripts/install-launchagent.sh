#!/usr/bin/env bash
# Install a per-user launchd agent so the local service starts at login (macOS).
# Loopback only; never a system-wide daemon.
set -euo pipefail
here="$(cd "$(dirname "$0")/.." && pwd)"

if [[ "$(uname -s)" != "Darwin" ]]; then
  echo "launchd is macOS-only; skipping on $(uname -s)."
  exit 0
fi

label="com.capcutcoach.local"
plist="$HOME/Library/LaunchAgents/${label}.plist"
py="$here/apps/backend/.venv/bin/python"

mkdir -p "$HOME/Library/LaunchAgents"
cat > "$plist" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>${label}</string>
  <key>ProgramArguments</key>
  <array>
    <string>${py}</string>
    <string>-m</string>
    <string>capcut_coach</string>
  </array>
  <key>WorkingDirectory</key><string>${here}/apps/backend</string>
  <key>RunAtLoad</key><true/>
  <key>KeepAlive</key><true/>
  <key>ProcessType</key><string>Background</string>
  <key>StandardOutPath</key><string>${HOME}/Library/Logs/CapCut Coach/launchd.out.log</string>
  <key>StandardErrorPath</key><string>${HOME}/Library/Logs/CapCut Coach/launchd.err.log</string>
</dict>
</plist>
PLIST

mkdir -p "$HOME/Library/Logs/CapCut Coach"
launchctl unload "$plist" 2>/dev/null || true
launchctl load "$plist"
echo "Installed and loaded ${label}."
