#!/usr/bin/env bash
# Remove the launchd agent (macOS). Does not remove data or backups.
set -euo pipefail
if [[ "$(uname -s)" != "Darwin" ]]; then echo "macOS-only; skipping."; exit 0; fi
label="com.capcutcoach.local"
plist="$HOME/Library/LaunchAgents/${label}.plist"
launchctl unload "$plist" 2>/dev/null || true
rm -f "$plist"
echo "Removed ${label}. Your projects, backups and config are untouched."
