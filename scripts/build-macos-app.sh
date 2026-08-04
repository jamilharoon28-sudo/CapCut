#!/usr/bin/env bash
# Build "CapCut Coach.app" — a native macOS launcher around the local backend + UI.
# Produces ./dist/CapCut Coach.app. macOS only (needs swiftc + Xcode CLT).
set -euo pipefail
here="$(cd "$(dirname "$0")/.." && pwd)"

if [[ "$(uname -s)" != "Darwin" ]]; then
  echo "This builds a macOS .app and must run on the Mac. Skipping on $(uname -s)."
  exit 0
fi

app_name="CapCut Coach"
out="$here/dist/$app_name.app"
contents="$out/Contents"
python="$here/apps/backend/.venv/bin/python"

echo "== 1/4 Backend deps =="
[[ -x "$python" ]] || ( cd "$here/apps/backend" && uv venv --python 3.12 .venv )
# Always (re)sync deps so features like footage analysis (opencv) are present
# even when the venv already existed from an earlier build.
( cd "$here/apps/backend" && uv pip install -e ".[scripts,media,vision,audio]" )

echo "== 2/4 Build UI =="
( cd "$here/apps/frontend" && { [[ -d node_modules ]] || pnpm install; } && pnpm build )

echo "== 3/4 Assemble bundle =="
rm -rf "$out"
mkdir -p "$contents/MacOS" "$contents/Resources/ui"
cp -R "$here/apps/frontend/dist/." "$contents/Resources/ui/"

cat > "$contents/Info.plist" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>CFBundleName</key><string>$app_name</string>
  <key>CFBundleDisplayName</key><string>$app_name</string>
  <key>CFBundleIdentifier</key><string>com.capcutcoach.app</string>
  <key>CFBundleVersion</key><string>0.1.0</string>
  <key>CFBundleShortVersionString</key><string>0.1.0</string>
  <key>CFBundlePackageType</key><string>APPL</string>
  <key>CFBundleExecutable</key><string>CapCutCoach</string>
  <key>LSMinimumSystemVersion</key><string>13.0</string>
  <key>NSHighResolutionCapable</key><true/>
</dict></plist>
PLIST

# Detect FFmpeg so the GUI app (which does NOT inherit your shell PATH) can find it.
ffmpeg_path="$(command -v ffmpeg || true)"
ffprobe_path="$(command -v ffprobe || true)"
if [[ -z "$ffmpeg_path" ]]; then
  echo "WARNING: ffmpeg not found on PATH. Install it with 'brew install ffmpeg'"
  echo "         (the app builds, but video rendering needs FFmpeg)."
fi

# Runtime launch config (absolute paths for this Mac; not committed to git).
cat > "$contents/Resources/launch.json" <<JSON
{
  "python": "$python",
  "backendDir": "$here/apps/backend",
  "frontendDist": "$contents/Resources/ui",
  "ffmpeg": "$ffmpeg_path",
  "ffprobe": "$ffprobe_path"
}
JSON

echo "== 4/4 Compile Swift launcher =="
swiftc -O -o "$contents/MacOS/CapCutCoach" \
  "$here/apps/mac-app/Sources/main.swift" \
  -framework AppKit -framework WebKit

# Ad-hoc sign so Gatekeeper lets your own build run locally.
codesign --force --deep --sign - "$out" >/dev/null 2>&1 || true

echo ""
echo "Built: $out"
echo "Open it with:  open \"$out\"   (or drag it into /Applications)"
