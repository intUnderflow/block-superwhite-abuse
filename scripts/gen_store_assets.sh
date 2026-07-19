#!/bin/sh
# Generate Chrome Web Store listing images from store/promo.html.
#
# Produces, per size, an SDR capture and an HDR (PQ cICP) variant whose
# logo glare and headline glow at 5000 nits. All outputs are 24-bit RGB
# PNGs with no alpha, per the store's promo-image requirements. Requires
# Google Chrome and ffmpeg. See scripts/hdrify.py for the HDR combine.
set -eu
cd "$(dirname "$0")/.."

CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
PAGE="file://$PWD/store/promo.html"

capture() { # width height query outfile
  "$CHROME" --headless=new --disable-gpu --hide-scrollbars \
    --window-size="$1,$2" --screenshot="$PWD/store/$4" "$PAGE$3" 2>/dev/null
}

for size in "1280 800 screenshot" "440 280 tile" "1400 560 marquee"; do
  set -- $size
  W=$1; H=$2; NAME="$3-${W}x${H}"
  capture "$W" "$H" ""      "$NAME.png"
  capture "$W" "$H" "?mask" "$NAME-matte.png"
  # Chrome captures RGBA; the store wants 24-bit PNG with no alpha.
  ffmpeg -v error -y -i "store/$NAME.png" -pix_fmt rgb24 "store/$NAME.tmp.png"
  mv "store/$NAME.tmp.png" "store/$NAME.png"
  python3 scripts/hdrify.py \
    "store/$NAME.png" "store/$NAME-matte.png" "store/$NAME-hdr.png" 8
  rm "store/$NAME-matte.png"
  echo "wrote store/$NAME.png (SDR) and store/$NAME-hdr.png (HDR)"
done
