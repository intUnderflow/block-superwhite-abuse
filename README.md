# Block Superwhite Abuse

<p align="center">
  <img src="icons/logo-superwhite.png" width="160"
       alt="A red prohibition sign over a blinding superwhite glare. Yes, the logo itself uses superwhite.">
</p>

> **⚠️ The logo above is superwhite.** On an HDR display it is doing the
> exact thing this extension blocks: the glare behind the sign is PQ-encoded
> at 5000 nits — the same peak brightness superwhite uses. Install the
> extension, reload this page, and it becomes an ordinary logo. The logo is
> the demo.

A Chrome extension that neutralizes ["superwhite"](https://github.com/dtinth/superwhite)
abuse — profile pictures, images and videos crafted with HDR trickery to render
blindingly bright on HDR-capable displays (recent MacBooks, iPhones, and HDR
monitors).

## What it blocks

Superwhite content is typically a ~1 KB HEVC 10-bit video encoded with PQ
transfer at up to 5000 nits, or an HDR AVIF/PNG still, uploaded where user
content is allowed (avatars, post images, embeds). On an HDR display it renders
far brighter than the page's `#ffffff`, which is somewhere between distracting
and physically painful.

This extension clamps **all** page content to standard dynamic range, so HDR
abuse renders at normal brightness. Legitimate SDR content — which is virtually
everything — is completely unaffected.

## How it works

One inherited CSS property, injected into every page and frame at
`document_start`:

```css
:root {
  dynamic-range-limit: standard !important;
}
```

[`dynamic-range-limit: standard`](https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Properties/dynamic-range-limit)
(Chrome 136+, April 2025) caps an element's luminance at HDR reference white.
Because the property is **inherited**, the `:root` rule flows into shadow DOM
trees (Reddit, YouTube, and most modern web apps use them), which extension
stylesheets cannot otherwise select into. A universal `*` rule additionally
overrides any page that opts specific elements back into HDR, and an
`@supports` fallback covers Chrome versions before 136 by forcing HDR media
through the SDR rendering path with a no-op filter.

There is **no JavaScript**: the extension is a single static stylesheet. It
collects nothing, phones home to nothing, and has no runtime behavior at all.

## Install

**From the Chrome Web Store:**
[Block Superwhite Abuse](https://chromewebstore.google.com/detail/block-superwhite-abuse/icgaohmdaiamelgkcbljioombconcmfl)
*(pending review — this link goes live once Google approves the first
version)*.

**From source:**

1. Clone this repository.
2. Open `chrome://extensions`.
3. Enable **Developer mode** (top right).
4. Click **Load unpacked** and select the repository directory.

To test it, look at the logo at the top of this README on an HDR display —
or visit the [superwhite repository](https://github.com/dtinth/superwhite),
whose README embeds the original HDR video. With the extension enabled, both
render as ordinary white instead of searing your retinas.

## Limitations

- **Chrome 136+** for full coverage (the property also works in Edge 136+ and
  Safari 26+, should you load this elsewhere). Older Chrome gets the filter
  fallback, which covers `<img>`/`<video>` but not backgrounds.
- Content is **clamped, not removed** — a superwhite avatar becomes a plain
  white square rather than disappearing. This is deliberate: it means false
  positives are impossible, and legitimate HDR photos simply display in SDR.
- A page could theoretically re-enable HDR with an inline
  `!important` style inside a shadow root. No real site does this; it can't be
  done by an attacker who only controls an uploaded image file.
- The separate [`backdrop-filter` EDR trick](https://github.com/kiding/wanna-see-a-whiter-white)
  on macOS is a different (compositing) exploit and is out of scope here.

## Development

The icons and logo are generated (pure standard-library Python, no
dependencies):

```sh
python3 scripts/gen_icons.py       # SDR toolbar icons
python3 scripts/gen_logo.py        # the superwhite README logo
./scripts/gen_store_assets.sh      # Web Store images (SDR + superwhite HDR)
./scripts/package.sh               # Web Store upload ZIP -> dist/
```

The toolbar icons are deliberately plain SDR PNGs: Chrome composites its
own UI in SDR, so an HDR icon in the toolbar would gain nothing. The README
logo is a 16-bit PNG with a `cICP` chunk (BT.2020 primaries, PQ transfer —
`9/16/0/1`), which current Chrome, Firefox and Safari render as true HDR.
The prohibition sign is encoded at the 203-nit HDR reference white, the
glare at 5000 nits. Viewers that don't understand `cICP` show the raw PQ
values, which look muddy — that's expected, and every modern browser gets
it right.

## License

[MIT](LICENSE)
