# Product images

`android113-server-picker-ru.png` and `android113-server-picker-en.png`: unchanged native
Android API35 UI renders from exact source d2882cd, workflow41833086774 attempt2,
artifact13327137775, captured4 November2026 and visually reviewed before publication.
Hybrid flat list; green selected row/checkmark and right-aligned load squares, orange at85%.
Values24/58/87% are synthetic fixtures, not measured fleet load. No product identities,
invitations, contacts or keys; not the earlier AI reference board. The narrow emulator
uses the responsive stacked-load layout. [Release](../releases/2026-11-04-android113-server-picker.md).

`android-beta38-home.png` is the unchanged native View.draw render from beta38/code38, captured on the connected Android phone on 2026-09-23. It is a historical beta38 capture; the current Android update is beta50. Country and protocol are selectable in the connection panel beneath the battery. VPN is off in the capture; the device was reconnected after tests. The image contains no invitation, contact, device identity or private key. It remains on the landing page with an explicit version/date caption, not as a beta50 screenshot.

[Build and verification record](../releases/2026-09-23-public-client-status.ru.md).


`android-beta19-home.png` is an unchanged copy of the Android native View.draw render
captured by device instrumentation for beta19 (0.1.18-beta19/code19) on Redmi Note9 Pro,
Android 12, 2026-09-19. It is an actual application view, not a generated design mockup
or an OS screenshot. The VPN is off; no personal contact, invitation or device key appears.

Source receipt: [beta19 verification](../releases/2026-09-19-android-beta19.ru.md).
This older screen is retained only as historical evidence. Earlier desktop images
in docs/images are historical. The rejected vector-smiley study is not a product screenshot.

For future additions: capture the current app, record version/device/date, inspect for
private data, and show at most four relevant images. Do not add empty image placeholders.

`invitation-beta50-off.png`: Firefox headless render of the final invitation page on23 September2026,390×1100px. Synthetic invitation; no private token or identity is displayed. The segmented circle shares native dial geometry and uses orange OFF. Captured by scripts/check_invitation_page.py after the requested circle correction.
