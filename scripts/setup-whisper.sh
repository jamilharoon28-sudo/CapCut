#!/usr/bin/env bash
# Build whisper.cpp and download a transcription model into the Coach models dir.
# Local, one-time. Prints the model path to use. macOS (Apple Silicon) + Linux.
set -euo pipefail

model="${1:-base.en}"   # e.g. tiny.en | base.en | small.en

if [[ "$(uname -s)" == "Darwin" ]]; then
  models_dir="$HOME/Library/Application Support/CapCut Coach/models"
else
  models_dir="${COACH_DATA_DIR:-$HOME/.coach-data/CapCut Coach}/models"
fi
mkdir -p "$models_dir"
build_dir="$models_dir/whisper.cpp"

echo "== Setting up whisper.cpp (model: $model) =="

# 1) Clone (or update) whisper.cpp
if [[ ! -d "$build_dir/.git" ]]; then
  git clone --depth 1 https://github.com/ggml-org/whisper.cpp "$build_dir"
else
  git -C "$build_dir" pull --ff-only || true
fi

# 2) Build the CLI (cmake is the current path; falls back to make)
cd "$build_dir"
# whisper.cpp builds with CMake; install it via Homebrew if it is missing.
if ! command -v cmake >/dev/null 2>&1 && command -v brew >/dev/null 2>&1; then
  echo "Installing cmake (needed to build whisper.cpp)…"
  brew install cmake
fi
if command -v cmake >/dev/null 2>&1; then
  cmake -B build -DWHISPER_COREML="$([[ "$(uname -s)" == "Darwin" ]] && echo ON || echo OFF)" >/dev/null
  cmake --build build --config Release -j
  bin="$build_dir/build/bin/whisper-cli"
else
  make -j
  bin="$build_dir/main"
fi

# 3) Download the model
bash "$build_dir/models/download-ggml-model.sh" "$model"
model_path="$build_dir/models/ggml-${model}.bin"

# 4) Make the binary discoverable on PATH for the app
ln -sf "$bin" "$models_dir/whisper-cli"

echo ""
echo "whisper binary: $bin"
echo "model file:     $model_path"
echo ""
echo "Add these to your shell so Coach finds them:"
echo "  export PATH=\"$models_dir:\$PATH\""
echo "  export COACH_WHISPER_MODEL=\"$model_path\""
