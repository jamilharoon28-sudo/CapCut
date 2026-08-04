#!/usr/bin/env bash
# One-time setup. Double-clickable on macOS (.command). Installs dependencies
# without any manual code editing (Phase 1 exit gate). Safe to re-run.
set -euo pipefail
here="$(cd "$(dirname "$0")/.." && pwd)"
cd "$here"

echo "== CapCut Coach bootstrap =="

# 1) uv (Python toolchain)
if ! command -v uv >/dev/null 2>&1; then
  echo "Installing uv..."
  curl -LsSf https://astral.sh/uv/install.sh | sh
  export PATH="$HOME/.local/bin:$PATH"
fi

# 2) Backend venv + deps
cd "$here/apps/backend"
uv venv --python 3.12 .venv
uv pip install -e ".[dev,scripts,media,vision,audio]"

# 3) Frontend deps (if pnpm available)
cd "$here/apps/frontend"
if command -v pnpm >/dev/null 2>&1; then
  pnpm install
else
  echo "pnpm not found — install Node + pnpm to build the UI (optional for API tests)."
fi

# 4) Doctor
cd "$here"
bash scripts/doctor.sh || true

echo ""
echo "Bootstrap complete. Start the app with:  ./scripts/run-dev.sh"
