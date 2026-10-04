# Android beta62: owner accepted, targeted upgrade — 2026-10-04

## Accepted checkpoint — 12:41UTC

Status: **BETA62 OWNER DIAGNOSTIC ACCEPTED; TESTER UPGRADE ONLY**.
The diagnostic APK and gateway are accepted; the long server window and next Russian
reproduction are not. This release improves evidence, not transport behavior. No
retry/timer/wire tuning; no claim that the original disconnect or RKN filtering is fixed.

### Immutable artifacts and CI

- Source commit: `42a5e59b4bc2c43e56e018ce7287cd7b6e901db2`.
- Android package `com.familyconnect.app.friends`, `0.1.18-beta62`, versionCode62,
  ARM64,49654651 bytes. Production signing key unchanged from60/61.
- Signed, installed and publicly downloaded APK SHA256:
  `f60b8d3a74b85a5934b942d7e273831e7c1d88d35e4d8a87db7332fb7d7703d4`.
- Signer SHA256:
  `67a90d1bfcd5a2c0666f0cff1b0ac5e43aaa661ca1196f89e879aa39fe20848a`.
- CI unsigned APK SHA256:
  `1725aa08ea4d1b2bd2d1aed8e1915612dcb7b3fe5baa408b321d740107109ee0`.
- Restricted native SHA256:
  `bb192fcb009522990c9d2934e8f488f5423530f06601dd83cd095046edc77829`.
- Loaded NL gateway SHA256:
  `6773423c960c303c4a1b3b6dea35941d3011873d7ee7a3cf31818f3672372f09`.

Exact-source GitHub workflows all PASS: Client builds37200872349 (Android
job111432134538), phase0 37200872268, Linux control preview37200872337, readiness
contract37200872286. Android includes WG/AWG/TCP/Auto runtime, unit/lint, full Go race,
Python3.10 policy/timestamp contracts and matching native/gateway compilation. Artifact
FamilyConnect-Android-restricted-arm64 ID11303511195, ZIP SHA256
`545dd2b632b17b8768192a1bde07ed67b9d3cbc58cd41bf3343d966037fdb96e`.
Payload/source pins, ARM64-only/16K alignment and release manifest verified. Offline
signed only after those checks; no rebuild after signing and no resign for publication.
Local final182 Python tests and noncached full Go race PASS;25 repeated core race
runs PASS. Android233 unit tests/37 suites and lint PASS. Signed/unsigned APK privacy
scan zero findings; one standard-library Basic-scheme bytecode false positive was
reviewed, not a credential literal. Real exported/server trace allowlist scans PASS.

### Owner and real correlation

Redmi31ce63ba updated over accepted61 r2. UID10283, original install time/data inode,
Device Identity, enrollment, activation and Support FC-4D8Q-REEG preserved. Immediate
encrypted identity/config/readiness files unchanged across installation; subsequent
normal refresh legitimately changes config/readiness ciphertext. Final identity and
enrollment fingerprints still match. No product uninstall, data clear or reenrollment.
AWG connected1510ms, VPN present, HTTPS probe200; export/new numeric diagnostic fields,
private-field rejection, safe compiled/provider/updater checks and restart PASS.
Temporary instrumentation removed; installed APK pulled and reverified against above
SHA/signer. Synthetic test evidence selectively removed; real evidence retained.

One controlled owner restricted session followed fresh normal READY/ACK, not a cache
bypass or automatic fallback. Established/healthy at capture, failure_category NONE;
harness61391ms including about35s healthy observation. Correlation keys:

- Support ID `FC-4D8Q-REEG`.
- connection_id `4a166b7b-920c-4c2a-bb46-eac2650eb873`.
- incident_id `87802c9a-0a3b-48cf-a23e-71632b070450`.
- session_tag `237b90a80fde9731e1fb9665356bf8b3aa106343296c7d66e53b507e16a1a20c`.

48 client and75 server events; lookup from each of four IDs PASS. No server sequence
gaps; required lifecycle stages complete, carrier RX/TX and heartbeat TX/RX observed,
cleanup completed, first_client_failure null. At12:33:12.440UTC server records precise
RELIABLE_RETRY_EXHAUSTED (age9587ms, retries8, pending4, ACK/progress age9400ms,
ACK count292). **Owner intentionally stopped; client cleanup completed12:33:03.092UTC,
9.348s earlier.** This later server error proves instrumentation, not an unplanned
owner failure or reproduction of the Russian failure. Compare endpoint timestamps
before promoting an endpoint-local first_failure to a global initiating cause.

Private accepted receipts: `state-client-build/field62-owner/acceptance-summary.json`,
`real-export.json`, `real-correlation-r2.json`, `real-correlation-summary-r2.json`,
`real-journal-receipt-r2.json`. Initial local helper accidentally shadowed selected TAG
with a parser regex; corrected to SELECTED_TAG and repeated read-only correlation of
the same session. Initial zero-event receipts are retained but superseded by-r2;
no second connection or product change was needed.

### Gateway and targeted delivery

Only NL diagnostic bootstrap binary changed; acceptance starts12:28:10UTC,
PID3875972/restarts0. Fresh actual seed directory verified12:28:12–13UTC, expires
13:23:10.209388518UTC. Bounded bootstrap acceptance PASS; loaded hash matches above.
RU admission/Support/enrollment/grants and ordinary HTTP/AWG/TCP service snapshots
unchanged. Exactly two FIELD devices; no expanded admission or long-mode activation.
Private deployment receipt: `state-client-build/field62-gateway/deployment.json`.

[Android beta62 diagnostic](https://185.251.89.19:8443/downloads/FamilyConnect-Test-0.1.18-beta62.apk)
was copied as a new immutable APK and exact nginx download location. Public readback
12:41:19UTC: TLS verification true, HTTP200, exact49654651 bytes/SHA/signer. No GitHub
Release, landing link or extra public artifact. Existing downloads including Linux,
Windows and beta61 r2 unchanged. Private receipt:
`state-client-build/field62-direct-delivery/verification.json`.

Production invariants checked after publication:

- Primary/default/updater/invitation Android is still0.1.18-beta60/code60.
- Beta60 APK SHA256 `8ee59352e5f490aea74c3c8c8aeefd0d65bec0c261a044899d512ca376cf6104`.
- Signed catalog SHA256 `f042becae969474ed7ebc28890a635ae5812769a3203fa6d75cf18fd22060006`.
- Discovery SHA256 `6e5817dc109b579384985b7f966bcf56c22ec59b4759eb477ef031cdc59a6a3b`.
- Invitation SHA256 `014ebdbd78966185b1d99823ae5e7e0251369dde26059bc82957e454ea99a49f`.
- Beta61 r2 SHA256 `4297ea1a7124f048bdfca4889e89114e84465fab3100a3caea7cbe23cd5e35fb`.

### Remaining gates and rollback

Supply beta62 only for FC-YHQB-9VJN to **upgrade on working Wi-Fi over the existing app**.
Do not uninstall/clear data/reenroll; no new invitation. Confirm62 and same Support ID
before any mobile attempt. At acceptance the tester last reports61 with expired
readiness; no tester attempts were performed in this rollout.

The four-hour contract is implemented, but live CRL policy remains3600s, RU archive
1bfa085b unchanged, gateway leaf ends13:39:54UTC and issuer/grants14:13:53UTC. These
are checkpoint expiries, not promises of availability after those times. Old61 rejects
long material. After tester compatibility, deploy compatible RU policy/sync and renew
the full issuer/grant/gateway/device/CRL/actual seed chain. Prove owner usable headroom
>=3h45m and fresh tester READY/ACK before one coordinated mobile attempt. Export
immediately after failure/disconnect and correlate exact ReliableStream cause and
ACK/progress. Do not infer a four-hour window from the gateway certificate alone.

NL protected rollback binary: `/opt/apps/family_connect/restricted-materials-stage-20261001/field62-binary-42a5e59/bootstrap-broker.previous`,
SHA256 `b9b7d542e6f196e2ffcfb9e913f1d065cf83529bb29726ec93daca740a241217`.
If rollback is needed, use bounded stop/replace/start/acceptance with currently valid
material, not expired trust or reset monotonic floors. RU publication backups are in
`/opt/apps/family_connect/release-beta62-diagnostic-20261004`; remove only the new62
location after checking intervening config changes and testing nginx. Do not overwrite
immutable APKs or restore whole old configs over unrelated edits. Android rollback is
a forward candidate, not downgrade/uninstall/data clear. No rollback was performed.

## Historical source preparation — superseded by accepted checkpoint above

The following records describe earlier gates/failures, not the current installation
or distribution state. Preserve them as the CI audit trail.

### Initial distribution and owner state

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
