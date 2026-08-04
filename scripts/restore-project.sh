#!/usr/bin/env bash
# Restore a Coach-generated project duplicate from its backup by id.
# NEVER touches an original CapCut project — only Coach-managed backups.
set -euo pipefail

if [[ "${1:-}" == "" ]]; then
  echo "Usage: $0 <backup-id>"
  exit 2
fi
backup_id="$1"

if [[ "$(uname -s)" == "Darwin" ]]; then
  support="$HOME/Library/Application Support/CapCut Coach"
else
  support="${COACH_DATA_DIR:-$HOME/.coach-data/CapCut Coach}"
fi
backups="$support/backups"
src="$backups/$backup_id"

if [[ ! -d "$src" && ! -f "$src" ]]; then
  echo "Backup not found: $src"
  exit 1
fi
echo "Restore is performed through the app so hashes are verified before and after."
echo "Located backup: $src"
echo "Open CapCut Coach → Settings → Recovery → Restore '$backup_id' to complete safely."
