# Chrome Web Store listing

Copy-paste material for the [developer dashboard](https://chrome.google.com/webstore/devconsole).

## Store listing

**Name:** Block Superwhite Abuse

**Summary** (132 chars max):

> Clamps HDR page content to standard brightness, neutralizing blinding
> 'superwhite' avatars, images and videos on HDR displays.

**Description:**

> People have started uploading "superwhite" profile pictures and images —
> tiny HDR videos and HDR AVIF files crafted to render far brighter than
> white on HDR displays (recent MacBooks, iPhones and HDR monitors).
> Somewhere between distracting and physically painful, they follow you
> around every comment thread they appear in.
>
> This extension neutralizes them. It applies the CSS property
> `dynamic-range-limit: standard` to every page, capping all content at
> standard-dynamic-range brightness. HDR abuse renders as ordinary white.
> Normal (SDR) content — which is virtually everything — is pixel-for-pixel
> unaffected, so there are no false positives, ever.
>
> Notable properties:
>
> • No JavaScript. The entire extension is one static stylesheet.
> • Collects nothing, stores nothing, contacts no servers.
> • Works in every frame, and reaches shadow-DOM UIs (Reddit, YouTube)
>   through CSS inheritance.
> • Legitimate HDR photos and videos still display — just at standard
>   brightness.
>
> Free and open source: https://github.com/intUnderflow/block-superwhite-abuse

**Category:** Accessibility

**Language:** English

**Images:**
- Icon: `icons/icon128.png` (uploaded from the ZIP automatically)
- Screenshot: `store/screenshot-1280x800-hdr.png`
- Small promo tile (optional): `store/tile-440x280-hdr.png`

The `-hdr` variants are, naturally, superwhite: the logo glare and the word
"neutralized." are PQ-encoded at 5000 nits and glow on HDR displays. If the
dashboard preview or published listing shows them washed out and muddy, the
store re-encoded the image and stripped the `cICP` color metadata — upload
the plain SDR variants (same filenames without `-hdr`) instead.

Regenerate all of them with `scripts/gen_store_assets.sh` (needs Chrome and
ffmpeg).

## Privacy tab

**Single purpose description:**

> Limits all web page content to standard-dynamic-range brightness so that
> maliciously bright HDR ("superwhite") images and videos display at normal
> brightness.

**Host permission justification** (`<all_urls>`):

> The extension injects one static CSS rule (`dynamic-range-limit:
> standard`) into every page, because abusive HDR content can appear on any
> site that displays user-uploaded media. No JavaScript runs and no page
> data is read; the extension has no other functionality.

**Remote code:** No, I am not using remote code.

**Data usage:** Does not collect any user data (tick nothing).

## Distribution

- Visibility: Public
- Regions: All regions
