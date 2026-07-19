#!/bin/sh
# Build the Chrome Web Store upload ZIP into dist/.
# Only ships what the manifest references — no scripts, docs, or the
# (deliberately superwhite) README logo.
set -eu
cd "$(dirname "$0")/.."

VERSION=$(python3 -c "import json; print(json.load(open('manifest.json'))['version'])")
mkdir -p dist
OUT="dist/block-superwhite-abuse-$VERSION.zip"
rm -f "$OUT"
zip -q "$OUT" \
  manifest.json \
  content/clamp.css \
  icons/icon16.png icons/icon32.png icons/icon48.png icons/icon128.png
echo "wrote $OUT"
unzip -l "$OUT"
