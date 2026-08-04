#!/usr/bin/env bash
# Run backend (loopback) + frontend dev server together.
set -euo pipefail
here="$(cd "$(dirname "$0")/.." && pwd)"

cd "$here/apps/backend"
[[ -d .venv ]] || { uv venv --python 3.12 .venv && uv pip install -e ".[dev,scripts,media,vision,audio]"; }
# shellcheck disable=SC1091
source .venv/bin/activate
COACH_PORT="${COACH_PORT:-8787}" python -m capcut_coach &
backend_pid=$!
trap 'kill "$backend_pid" 2>/dev/null || true' EXIT

cd "$here/apps/frontend"
[[ -d node_modules ]] || pnpm install
pnpm dev
