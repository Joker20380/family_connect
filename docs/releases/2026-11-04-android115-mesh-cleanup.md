# Android115 and gateway MESH cleanup delivery — 4 November 2026

## Selected scope and version state

Owner selects qualification and delivery of the lifecycle correction `f66b533`,
followed by paired physical reconnect/cleanup and ordinary-UID DNS/HTTPS checks.
Preserve active-session ownership, security deadlines, retry limits, identity/P1
policy, canonical source/runtime custody and the shared fleet renewal writer.
No unrelated development successor or general public rollout is selected.

Candidate source is Android0.1.18-beta115/code115, ARM64/minSDK27/targetSDK35.
It retains the114 DNS fix and adds ordered RESET/carrier cleanup. At this source
checkpoint115 is not built, signed, installed or public. Owner remains114;
public/invitation/updater113/catalog7, Linux0.2.11 and Windows0.2.16/catalog12 remain.
The [source diagnosis](2026-11-04-mesh-startup-cleanup.md) retains both physical
failures, all local regression results and the two reproduced baseline test failures.
Full historical-suite or sustained/low-speed acceptance is not implied.

Source metadata/payload/notification/orchestrator/field checks:59 PASS, one unrelated
Windows case deselected, zero skips. Documentation links and whitespace are checked
before the source push; hosted/artifact gates remain pending.

## Required qualification and delivery

1. Exact-source hosted Android/native, JVM, API27/API35 and downloaded source/license,
   ABI/16K/provenance checks before offline existing-key signing. Retain negative CI
   attempts; no replacement of an already signed or published version.
2. Project only the reviewed server lifecycle change onto the accepted private gateway
   capsule; do not deploy generic main. Verify the full predecessor inventory, reproduce
   its binary, run fixture/negative/ownership regressions with production tags, and
   reproduce the candidate binary under the original Go/CGO/build-tag contract.
3. Inspect both current nodes and shared maintenance custody. Perform guarded runtime
   delivery with exact predecessor/rollback pins; preserve profiles, DB, grants, units,
   timers and ordinary AWG/TCP services. Stop on custody or inventory mismatch.
4. Owner115 installation is in place only (`adb install -r`), with package/signer,
   version/UID/first-install and installed-byte readback. Never clear app data, reenroll,
   bypass Android input restrictions or bypass app USB-support consent.
5. Consented bounded disconnect/reconnect must pair actual client/gateway sessions and
   check remote cleanup plus DNS/normal-TLS hostname HTTPS and selected-node egress.
   CONNECTED alone is not acceptance. Public distribution remains113 until separately
   selected and verified; do not edit invitation/download links for an owner candidate.

## Rollback and remaining gates

Until delivery, no production rollback is needed. Keep immutable113/114 APKs and the
exact previous gateway binary/source/runtime references. For a runtime failure restore
only the recorded gateway executable under the same guarded custody; never restore
product DB, keys, profiles or signed floors. Android downgrade is not a data-preserving
rollback: retain data and issue a higher versionCode if a client repair is needed.
Each build/install/runtime result and remaining acceptance gate is appended here before
claiming completion. Private evidence and signing material stay outside Git and CI.
