#!/usr/bin/env bash
# Back up the Coach SQLite database using the online .backup API (safe while
# the service runs). Backups live outside CapCut's project directory (contract §9).
set -euo pipefail

if [[ "$(uname -s)" == "Darwin" ]]; then
  support="$HOME/Library/Application Support/CapCut Coach"
else
  support="${COACH_DATA_DIR:-$HOME/.coach-data/CapCut Coach}"
fi
db="$support/coach.sqlite3"
backups="$support/backups"
mkdir -p "$backups"

if [[ ! -f "$db" ]]; then echo "No database at: $db"; exit 1; fi
stamp="$(date +%Y%m%d-%H%M%S)"
dest="$backups/coach.$stamp.sqlite3"
sqlite3 "$db" ".backup '$dest'"
echo "Backed up to: $dest"
