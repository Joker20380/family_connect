# Smooth smileys — expression study 01

Status: rejected in visual review on 2026-09-19. The user chose to keep the current
app smileys for now. Expansion and Android integration are deferred.

Original vector drawings inspired by the familiar yellow expressions of classic messengers.
These are design samples, not copied ICQ artwork and not yet Android assets.

Open [index.html](index.html) in a browser for animation and a pause button.
[preview.png](preview.png) is a Chromium rendering of the page, not an app screenshot.
Five expressions are shown at large size and 24/32/48 CSS pixels on dark and light surfaces.
SVG canvas includes padding for motion. The background is transparent; there is no raster matte.

Regenerate the ten SVGs and HTML with `python3 docs/design/smileys-smooth/generate.py`.
The five `-still.svg` variants support pause and the browser's reduced-motion preference.
No external libraries, fonts, requests or raster source images are used.

After visual review: refine expressions, extend the token mapping, implement Android drawing
and lifecycle-aware animation. Preserve plain-text tokens, message compatibility, line bounds,
reduced-motion settings and foreground-only animation. Review on the physical phone before
publishing a new APK. Existing GIFs and the running client remain unchanged for this preview.
