# Beta61 r2 targeted GitHub delivery — 2026-10-04

## Result: BLOCKED before publication

Superseded by the user's direct-server delivery request. GitHub was not used;
[separate direct download PASS](2026-10-04-beta61-r2-direct-delivery.md). Do not resume
the GitHub continuation below; it records the earlier blocked attempt only.

Requested repository `Joker20380/family_connect`, tag
`android-beta61-r2-diagnostic`, title `Android beta61 r2 — diagnostic`.
This is explicitly authorized prerelease delivery of the existing owner-accepted
diagnostic APK, not a production update or an admission expansion.

| Check | Result |
|---|---|
| Existing artifact | `state-client-build/field61-r2-delivery/FamilyConnect-Test-0.1.18-beta61-r2.apk` |
| Exact asset name | `FamilyConnect-Test-0.1.18-beta61-r2.apk` |
| VersionName / versionCode | `0.1.18-beta61` / `61` |
| Source | `64849e828add45407625d31df61413ac98e9a2cc` |
| Local APK SHA256 | `4297ea1a7124f048bdfca4889e89114e84465fab3100a3caea7cbe23cd5e35fb` — PASS |
| Size | `49654651` bytes |
| Signer SHA256 | `67a90d1bfcd5a2c0666f0cff1b0ac5e43aaa661ca1196f89e879aa39fe20848a` — PASS |
| Independent retained beta60 signer comparison | Exact match; beta60 APK SHA `8ee59352e5f490aea74c3c8c8aeefd0d65bec0c261a044899d512ca376cf6104` verified |
| APK signature verification | v2/v3 PASS, no signing operation performed |
| Rebuild / resign | Neither performed |
| Intended prerelease / make_latest | `true` / `false`; prepared, not submitted |
| Release created / asset uploaded | No / no |
| GitHub download verification | Not run: no uploaded asset |
| Verified release/download URL | None |

GitHub target-release lookup returned404; the latest-release endpoint also returned404.
These reads are not successful publication or proof that no other prereleases exist.
The available connected GitHub actions do not expose Release creation or binary asset
upload; local `gh` and its authenticated session are unavailable. Plugin discovery
found the already-connected GitHub integration, not another confirmed upload path.
No token was requested in chat, no credential was exposed, and no CI/workflow workaround
was created. Publication must not be claimed without a usable authorized upload path.

## Prepared notes and continuation

Private local receipts and notes:
`state-client-build/field61-r2-github-delivery/preflight.json`,
`release-request.json`, `release-notes.txt`. These are not uploaded release artifacts.
Notes identify the targeted diagnostic FIELD build for existing FC-YHQB-9VJN and state:
install over beta60; do not uninstall; do not clear app data; no new invitation;
retain enrollment/Support ID; original restricted-session disconnect is not claimed
fixed. Fresh gateway leases and tester READY/ACK are required before a later test.

To continue, provide a locally authenticated GitHub CLI/API release-upload session
with repository Contents:write permission. Do not paste credentials into chat.
Re-read the tag and release before any write; preserve any existing published asset,
never overwrite different bytes. Target the accepted source commit, not an assumed
latest main. Create only the requested prerelease, explicitly not latest; upload only
the exact APK. Download its actual GitHub asset URL to a separate verification path,
recompute SHA256 and verify signer independently. Both must equal the pins above.
Re-read prerelease/assets and confirm production latest metadata is unchanged before PASS.

No production server/catalog/landing/admission/Support or existing release mutation
was performed in this task. Beta60 remains the production distribution; this statement
describes unchanged distribution and no writes, not a new public APK download audit.
No rollback is needed because nothing was published. Keep the accepted APK unchanged;
no new tag/release artifact, product commit, build, key use or Russian test was created.
Owner diagnostic acceptance is recorded in
[the preceding report](2026-10-03-beta61-targeted-acceptance.md), independently of this
blocked GitHub delivery step.
