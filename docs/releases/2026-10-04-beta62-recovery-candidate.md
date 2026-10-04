# Android beta62: recovery diagnostics and long window — source candidate

## Distribution and owner state

Source metadata: `0.1.18-beta62`, versionCode62, current checkpoint
`b04f5c2a5827c7d3ad108b4ec68923f20f3518ac`, following2c52e82. Both scoped commits
pushed with explicit user authorization. No accepted signature, installation or publication yet; therefore
there is no beta62 APK SHA256 or beta62 download to report. A Java unit-test/lint
build is not a newly rebuilt/verified restricted native library or deliverable APK.
Existing dirty work, including unrelated VPN health docs, is preserved.

Initial Linux control preview37197471972 exposed three related stale tests: the
negative directory lifetime still used1h+1ns, native parity shared that fixture,
and a publish_crl test stub did not accept the new lifetime keyword. Corrected to
4h+1ns, asserted unchanged900s sync default, added native/Python acceptance at
1h+1ns and exactly4h. Android CI now runs directory and long-window contracts too.
Do not accept the initial source artifact before corrected-source CI passes.

Corrected-source local directory/readiness/correlation suite99 PASS. Hosted phase0
37197973235, Linux control preview37197973213 and readiness contract37197973259 PASS.
Client builds37197973321 passed Android emulator WG/AWG/TCP/Auto and control checks,
then failed the full Go race step in job111423710235. The complete local non-cached
`go test -race -count=1 ./...` subsequently passed all carrier packages. One repeat
of the same Android job was requested; no transport/code change or failure waiver.
The failed job produced no restricted release artifact. Precise initial CI failure
is not established from the bounded log projection; do not call it a proven flake.
Private owner instrumentation compiled separately, not yet signed or installed.

Same-source retry job111428157461 passed full Go race, but the newly added Python
contracts failed during collection. Reproduced locally in a clean cryptography/pytest
environment: missing `RNS`, imported by DeviceIdentity. Install the existing pinned
device_identity lockfile for this CI-only check. Move race/contracts before the
expensive native/emulator steps and retain their logs in the existing diagnostic CI
artifact with pipefail, without removing or relaxing any release check. Local four
core packages repeated25 times under race also PASS; no product transport change.

Follow-up CI902e4db (Client builds37200537346, job111431145897) passed race and
installed the correct dependencies. Retained contract log proves13 failures/86 PASS:
Python3.10 datetime.fromisoformat rejects production nine-digit fractional seconds.
The same tests on Python3.13/3.14 passed; this is not evidence of a live Russian
transport failure. Parse validated whole seconds/zone with datetime, then add the
original exact fraction as integer nanoseconds. No rounding, grace or expiry change.
Added27 fraction-width/zone regressions and existing Friends timestamp vectors to
the early Android Python3.10 CI contract gate. No product APK accepted or deployed.

Read-only server preflight11:26UTC: exact two-device admission, beta60 default and
discovery/invitation hashes unchanged; gateway binaryb9b7d542 still loaded, certificate
expires13:39:54UTC, issuer14:13:53UTC. CRL3826 and directory match RU/NL; old cached
owner/tester receipts expired. Fresh owner READY/ACK is required, not an old snapshot.

Connected owner Redmi31ce63ba remains0.1.18-beta61/code61, UID10283. Pulled installed APK:
SHA256 `4297ea1a7124f048bdfca4889e89114e84465fab3100a3caea7cbe23cd5e35fb`;
verified signer `67a90d1bfcd5a2c0666f0cff1b0ac5e43aaa661ca1196f89e879aa39fe20848a`.
Accepted owner-only instrumentation ran registrationSnapshot: activated=true,
identity_decrypts=true, readiness_decrypts=true, Support FC-4D8Q-REEG. Encrypted identity,
configuration/readiness and enrollment fingerprints saved locally; no secret bytes
printed or committed. Decryptable readiness is not a claim of unexpired readiness.
Temporary test package installed/removed, product APK/data/UID/install inode unchanged;
no product uninstall, clear data or reenrollment. This is a baseline, not62 acceptance.
Private receipt location: `state-client-build/field-next-recovery-owner/`.
Comparison with the prior accepted r2 after-state confirms unchanged encrypted
identity bytes, enrollment fingerprint, activation and owner Support ID. Readiness
and configuration ciphertext equality across ordinary refreshes is not asserted.

Production/default/updater and invitation download remain beta60; targeted publicly
downloadable asset remains immutable61 r2. No catalog, Linux/Windows, admission,
Support-ID or server changes in this task. Do not overwrite existing download bytes.

## Proven failure versus unknown cause

[Export(10)](2026-10-04-field-export10-reliable.md) establishes successful restricted
TLS and bidirectional traffic followed by reliable recovery exhaustion before expiry.
That does not identify an ISP filter or a proven retry-count versus frame-age cause.
ACK loss, failure of forward delivery and stalled upper-layer consumption are not
distinguished by the old exported aggregate counters. Do not raise limits blindly.

The source-level diagnostic gap is confirmed: ReliableStream owns ErrExhausted but
closes the carrier before Family TLS observes its downstream error. LOCAL_CLOSE sets
the recorder's cleanup boundary, so a later TLS failure cannot become first_failure.
This explains why exact correlation succeeded while structured first_failure remained
absent and the outer orchestrator displayed UNKNOWN_INTERNAL.

## Local diagnostic correction

- Retain the original ErrExhausted and every existing timer, retry budget, ACK/SACK
  rule, queue/window and packet byte. The three existing exhaustion branches now
  retain bounded failure evidence; they do not change when failure is returned.
- Emit CARRIER/FAILED with RELIABLE_HANDSHAKE_TIMEOUT, RELIABLE_FRAME_TIMEOUT or
  RELIABLE_RETRY_EXHAUSTED before RESET/cancel/endpoint.Close, using metadata frozen
  before buffers are cleared. Later TLS/cleanup evidence remains separate from first_failure.
- Include numeric reliable_age_ms, reliable_retries, reliable_pending, reliable_sacked,
  reliable_ack_received, reliable_ack_age_ms and reliable_progress_age_ms. ACK/progress
  ages use stream start if never observed; SACKed=true distinguishes received-but-not-
  cumulatively-consumed data. Native zero values may be omitted. No payloads, keys,
  authentication material, room URLs or raw errors are added.
- Update Go/Android/offline-operator reason and numeric allowlists, including outer
  Android diagnostic enum. Existing old trace inputs remain accepted. Four-hour
  validation/opt-in issuance changes from the [previous work](2026-10-04-four-hour-readiness.md)
  are included locally, still not activated against the old installed clients.

## Validation checkpoint

- Python171 PASS: four-hour policy/native compatibility, friends issuance,
  isolated sync/runtime and operator correlation/privacy allowlists.
- Android233 unit tests (37 suites, zero failures/errors) and lintFriends PASS;
  rerun after the metadata bump, generated versionCode62/versionName0.1.18-beta62.
  New JVM checks retain exact reliable cause/numeric metadata, reject malformed
  counts and strip sentinel private fields. Not Android instrumentation of62.
- Full carrier `go test ./...` PASS outside sandbox. Initial sandbox full-suite
  failures were local socket/netlink restrictions; no product patch was made for them.
- Race suites PASS for reliablestream/sessiontrace/familysession/wholedevice.
  New exact-branch/first-cause-ordering tests repeated10 times under race PASS,
  including an established stream with deliberately dropped DATA. Default timers,
  delivery behavior and ErrExhausted remain unchanged in these regressions.
- Go formatting/diff whitespace checked; documentation link check separately.
  Initial Gradle sandbox failure was its daemon socket; approved outside-sandbox
  run passed. Existing deprecation/watch warnings remain, no unrelated build fixes.

## Release gates and rollback

Next: finish platform CI on the authorized pushed source, download/verify its
matching native+Java APK and gateway, sign Android with
the accepted key, and install62 in place on this Redmi. Recheck UID/identity/enrollment/
activation/Support, AWG, export/privacy and a real restricted session. If a local
failure reproduction is used, record exact branch and prove first_failure precedes
cleanup rather than inferring the field root cause from synthetic loss.

Only after owner acceptance, coordinate four-hour issuer/grant/certificate/CRL/seed
material validity and compatible RU/NL deployment, verify remaining usable time, then
offer the targeted artifact to FC-YHQB-9VJN. Preserve FIELD cohort. A single subsequent
reproduction should now distinguish exact reliability failure with ACK/progress
evidence; fix the demonstrated cause and add a focused regression afterward.

No runtime rollback needed now: no product update or server deployment. Do not force
an Android downgrade/uninstall or restore expired trust material as rollback. Separate
future artifact rollback must preserve data and monotonic trust/CRL floors.
