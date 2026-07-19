#!/bin/sh
# Generate Chrome Web Store listing images from store/promo.html.
#
# Produces, per size, an SDR capture and an HDR (PQ cICP) variant whose
# logo glare and headline glow at 5000 nits. Requires Google Chrome and
# ffmpeg. See scripts/hdrify.py for how the HDR combine works.
set -eu
cd "$(dirname "$0")/.."

CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
PAGE="file://$PWD/store/promo.html"

capture() { # width height suffix
  "$CHROME" --headless=new --disable-gpu --hide-scrollbars \
    --window-size="$1,$2" --screenshot="$PWD/store/$4" "$PAGE$3" 2>/dev/null
}

for size in "1280 800 screenshot" "440 280 tile"; do
  set -- $size
  W=$1; H=$2; NAME="$3-${W}x${H}"
  capture "$W" "$H" ""      "$NAME.png"
  capture "$W" "$H" "?mask" "$NAME-matte.png"
  python3 scripts/hdrify.py \
    "store/$NAME.png" "store/$NAME-matte.png" "store/$NAME-hdr.png"
  rm "store/$NAME-matte.png"
  echo "wrote store/$NAME.png (SDR) and store/$NAME-hdr.png (HDR)"
done
