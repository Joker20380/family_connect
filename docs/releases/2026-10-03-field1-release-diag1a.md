# FIELD-1 release / DIAG-1A — 2026-10-03

**FIELD-1-RELEASE: PARTIAL. DIAG-1A: PARTIAL. Stage5N remains CLOSED.**

## Provenance and gate

Starting HEAD `911fea59e08e5ee8844852ae1e2834812632fbde`; Stage5N checkpoint
`ea25a5e`, local only. Unrelated VPN-health files/STATUS sections preserved unstaged.
Candidate source `0.1.18-beta59` / code59, `com.familyconnect.app.friends`, ARM64,
minSDK26. Expected unchanged beta signer:
`67a90d1bfcd5a2c0666f0cff1b0ac5e43aaa661ca1196f89e879aa39fe20848a`.
Artifact/source/test evidence follows when available. No connected Redmi: in-place
acceptance cannot run. No installation, data reset, production writes or push.

## Distribution and migration audit

Live03.10 07:34UTC: `/invite/` and `/updates/android-friends.json` at
`https://185.251.89.19:8443` advertise beta51/code51,36,456,636 bytes; manifest hash
`79a2d28667332ea442eae1b895b4fc632b52734cbed1e75bd95f32b7175ad366`.
No public59; Windows/Linux and invitation behavior unchanged.

Legacy Settings → Check for updates uses HTTPS schema1, strict origin/package/ABI/
version/size/hash, downloaded SHA256 and installed-signer matching before Android
confirmation. No offline manifest signature/lease/floor, foreground discovery or
mandatory policy. Published beta35 documentation describes this checker; beta51
source contains it. Exact first distributed checker build is not proven.
Class A unattended install unsupported. Class B checker-equipped users need a
manual Settings check and OS approval; class C builds without it need one manual
invitation-page download. Same-package/same-beta-signer Friends builds are intended
to update in place; technical/debug/foreign-package APKs are not that population.
Never uninstall to bypass mismatch. After acceptance use existing operator support:
ask users to check Settings or download once from their existing invitation URL,
then return to landing → Open. No bulk message sent.

Live DB28 activated records:24 non-revoked/4 revoked, not28 proven Android installs
or DAU. Only1 latest authoritative readiness receipt reports private58; other27
platform/version states unknown. Known59 upgrades in this task0, public59 offers0;
exact pending/manual-upgrade counts **unknown**, not zero. No complete adoption
telemetry; historical distributed versions do not prove current installed versions.

## Signed discovery and policy

Candidate59 reads `/updates/android-friends-v2.json`: Ed25519 base64 envelope with
domain `family-connect/android-update/v1\0`, reusing the existing desktop update
root, not a new private key. Offline `scripts/sign_update.py --platform android`
checks APK package/version/non-debuggable/signer/size/hash. Use existing local key
only after accepted platform checks/artifacts, never CI/server. No signed59 catalog
issued. Payload: schema1, channel, sequence, package, abi, version/version_code,
url/size/sha256, signer_fingerprint, minimum_supported_version, mandatory_after,
release_notes, issued_at/expires_at (maximum90 days).

Client verifies signature/domain/root/origin/package/signer/lease and monotonic
sequence+digest floor, then APK hash/version/installed AND pinned signer. No unsigned
fallback in59; ordinary Android approval only. Floor is separate from identity.
Publisher takes legacy manifest plus `--signed-catalog`, verifies matching signed
metadata, serves both endpoints. Preserve legacy schema1 for one-time transition.
Policy: latest59, minimum1, mandatory_after0: optional. Review adoption7 days after
publication; raising minimum/deadline requires a later signed decision, no automatic
cutoff. Foreground check≤once/6h, notice≤once/24h with Later; manual checks available.
A future required notice never clears data, tears down VPN or bricks recovery.

## DIAG-1A

Existing Orchestrator/owner/readiness/native stats instrumented, not replaced;
selection/timeouts/fail-closed/native algorithms unchanged. Random persistent
device_support_id independent of Device Identity, random connection/incident IDs.
128-event private AtomicFile ring; latest incident snapshot only, automatically
on CONNECTING→FAILED and RESTORING→FAILED. Codes cover normal failures, typed
readiness, BOOT-1/cache/carrier, Family auth, broker descriptor, dedicated session,
VPN capture, DNS probes and restoration. Native lifecycle names come from the
structured JNI callback, not arbitrary log parsing; unknown fields/names discarded.
Some failures remain STARTUP_FAILED; no invented cause. Numeric DNS/TCP/denial/
protection counters only; unavailable observations absent/UNKNOWN, not zero.

Settings → Send diagnostics explains fields and opens Android chooser with local
JSON. Non-exported read-only provider, exact one cache file,≤256KiB,1h access-age
limit. Each export uses a fresh unguessable URI; previous grants revoked and previous
export deleted, so an old recipient cannot read a future bundle. No upload/DIAG-1B.
No browsing/destinations/DNS names/SSIDs/messages/raw
Device Identity/tokens/keys/room URLs/credentials. Existing native/private logs NOT
bundled. Future authenticated upload may accept this schema under separately defined
consent, retention and support-code policy. Device export validation still required.

## FIELD and remaining acceptance

Live admission1 existing owner, no wildcard; no new FIELD cohort selected/enabled.
Need1–2 more explicitly selected trusted physical devices, ideally naturally
restricted cellular. Version59 never implies admission. Normal Auto only, no
diagnostic exhaustion. STOP at2–3; no regional/general widening.

Connect/unlock Redmi; capture safe signer/package/UID/identity/enrollment/readiness
continuity evidence; install signed59 with `adb install -r`, never uninstall/clear.
Verify fresh-process continuity, absence of private components, ordinary Auto/AWG/
TCP, incident/export privacy and authorized normal restricted path where applicable.
Expired readiness uses existing trusted provisioning, not a new Stage5N gate.
JVM/static checks cannot establish physical acceptance. Then publish immutable59,
verify full public APK hash/cert, publish signed+legacy catalogs, change Android-only
invitation download, check install→return→Open, update RU/EN links/hashes, then push.

Rollback before publication: keep51 primary/58 installed; no server action. After
publication halt offers with higher signed sequence/explicit policy; never replace59,
lower replay floors, force downgrade or clear data. Fix-forward with higher code.
Revoke only newly selected admissions if needed; preserve owner/normal access.
Private acceptance APK is never a public rollback.

## Validation checkpoint

Initial clean export `ea7f69882566a78c9dc9a477e027e46fff5b9530`:224 JVM tests PASS,
lint0 errors/37 warnings, assembleFriends PASS;243 Python PASS/7 skipped (optional
toolchain fixtures), five native Go race packages PASS. APK1071-entry nested scan
has0 findings after one previously reviewed hash-pinned stdlib false positive.
JNI inputs are byte-identical to accepted58 and their native source0615953 is
unchanged; these are reused verified native artifacts, not a fresh JNI rebuild.
Final export after grant-lifetime hardening must be rebuilt and rechecked.
Whole-index source guard currently FAILS on an unchanged pre-existing assertion
at `tests/test_readiness_adapter_packaging.py:283` containing a literal private-key
PEM header as a negative test, not key material. Preserve it; do not claim global
guard PASS or publish while this guard finding lacks an accepted resolution.
Owner installation/runtime/UI checks NOT RUN: no device. No production changes,
public59, cohort expansion or push.
