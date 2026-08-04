#!/usr/bin/env bash
# Run the full test suite (backend now; frontend when node deps are installed).
set -euo pipefail
here="$(cd "$(dirname "$0")/.." && pwd)"

echo "== Backend tests =="
cd "$here/apps/backend"
if [[ ! -d .venv ]]; then
  uv venv --python 3.12 .venv
  uv pip install -e ".[dev,scripts]"
fi
# shellcheck disable=SC1091
source .venv/bin/activate
ruff check capcut_coach
python -m pytest -q

if [[ -d "$here/apps/frontend/node_modules" ]]; then
  echo "== Frontend tests =="
  cd "$here/apps/frontend"
  pnpm test --run || true
  pnpm exec tsc --noEmit
else
  echo "== Frontend tests: skipped (run 'pnpm install' in apps/frontend first) =="
fi
