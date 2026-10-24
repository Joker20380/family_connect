# Closed three-device P1 delivery and Volgograd field result —23 October2026

**PRIVATE_FIELD_READY — for the confirmed existing three-device group only.**
No public release, automatic sending, enrollment, global profile, purchase, push or
hosting migration. The APK remains the already signed/accepted106; no rebuild,
re-signing or owner reinstall in this phase. Owner distributes the file manually.

## Volgograd: positive field evidence, not a106/P1 acceptance

On23 October the owner reports receiving a definite positive answer from the
Volgograd tester on22 October: the connection worked under mobile whitelist
conditions. Whitelist conditions are **tester testimony relayed by the owner**,
not something the diagnostic JSON independently detects. Operator, tariff state,
exact whitelist policy and a full application-body digest remain UNKNOWN.

Original `/home/joker/Загрузки/FamilyConnect-diagnostics(21).json` preserved unchanged
in ignored `state-client-build/tester-p1-cohort-20261023/field-volgograd/original.json`:
113,531 bytes, SHA256 `04ca8b2de73538272617245bb134eeb795fe9b5e7db0de400926b9b64d1d7904`.
Filesystem arrival on23 October is not the test time.

- Current ring identifies **FC-ZMVK-MM7C, beta96-bootstrap/code96, API34**, not94
  and not106. CELLULAR, CONNECTED, TUN open, READY/USABLE, restricted SUCCESS;
  no AWG/TCP event in this current ring. CONNECTED16:54:25.453UTC22 October;
  final native sample16:55:00.657UTC. Native session
  `28bb86544b7e0c6969ec24ffdb01a2c016d547ec6434802b0b24738b64e90b90`.
- Both-direction native byte counters326,675 sent /1,618,354 received,82 TCP opens,
  40 DNS responses and terminal NONE corroborate actual MESH activity beyond a
  CONNECTED label. They are not benchmark byte-exact/full HTTPS-body verification.
- Nonzero evidence remains:5 TCP-open errors,7 protocol errors,44 recovery timeouts
  and DNS_PROBE_FAILED16:54:35.514 despite later aggregate dns_errors0. This older
  ring lacks the newer classifications; do not label these all expected or erase them.
- Direct HTTPS challenge CONNECT failed; RNS RELAY_OPEN was unavailable. The
  successful startup selected a validated READY cache, age63s, expiring19:16:23UTC.
  It does **not** prove cold/expired-cache bootstrap under those restrictions, or
  that preceding preparation happened on Wi-Fi. Normal expiry checks remain intact.
- `incident` is a separate retained **beta94 failure on20 October**, not a failure
  of the successful96 session. It stays in the original file and report history.
- The bounded selected current journal file returns no rows for the requested
  historical interval. This is no server-side session correlation, not proof that
  no historical journal/connection exists.96 exports no speed/RS/Mux contract here;
  do not claim P1 or reconstruct its limits from today's policy.

Thus **FIELD_WHITELIST_VALIDATION is now a positive reported Volgograd96 result,
corroborated by cellular MESH diagnostics**.106/P1 in that field and the separate
Krasnodar scenario remain NOT_RUN. The owner's exhausted allowance explanation is
not used to explain these tester incidents.

## Confirmed group and minimal policy

Owner explicitly confirmed on23 October:
**FC-4D8Q-REEG + FC-ZMVK-MM7C + FC-YHQB-9VJN**, no other devices.
Read-only RU lookup verifies three existing non-revoked registrations/invitations
and no revoked existing grant; no DB/grant write. Each RNS identity binding and the
hash of its certificate's Ed25519 public-key half are checked separately: a device
ID is **not** the speed-target hash. No raw public/private keys exported.

The loaded3a08 baseline was rebuilt byte-identically before changing two production
files. New policy reads an optional protected `speed-targets` file, maximum99 bytes/
three distinct canonical16-byte hashes, requiring the original owner target.
Absent/empty group retains prior owner-only behavior; invalid/duplicate/wildcard/
overlarge/unsafe files fail closed. Group mode permits P1, not experimental P2 or
pacing. Existing authentication and negotiation remain unchanged. Nonselected
identities remain P0; old clients keep negotiated compatible limits, not guaranteed
RS32 solely because their identity is selected. The separate diagnostic target stays
owner-only; normal user profile selection does not require USB permission.

No ReliableStream, Mux window, retry, buffer, deadline, native APK or security delta.
Two changed production files plus one policy test file are frozen in the source
inventory. Local race tests PASS: roombroker, familysession, reliablestream,
tcpforward and bootstrap. The first bootstrap invocation failed only because the
capsule lacked its shared timestamp JSON vector; retained failure log, supplied
the unchanged project vector, then bootstrap passed. No test/source bypass.
Existing actual96/new-P1 byte-exact compatibility evidence is retained separately;
TLS old/new legacy/CREDIT128 and invalid/expired/family/floor cases pass here too.

## Applied gateway and post-deploy control

Only Amsterdam `family-connect-restricted-bootstrap.service` changed. Existing
RU coordinator/node and NL node locks serialize with renewal; baseline saved first.
One approved normal restart, completed **05:43:09.452UTC**. No emergency kill,
firewall shaping or neighboring service operations.

- Gateway SHA256: `a515539af72844cb5af4f918a229c85e23cff874f0f6ac369649df3839273c85`.
- Exact parent/rollback: `3a0804cd3da63135dce387d1dff9afdc4588562186abea2e5d00da1d9f5c31ae`.
- Source inventory SHA256: `862676f51502adb09293bb70d8af2de3f0a3191389d40353fd25bb80537513c2`.
- PID2249749, invocation `35a4b1e34b244265a3b9c46a2c99d936`, active/NRestarts0.
- Gateway config remains `f8188a9763c091984166788f1dd0456cadeeb730fa43b9557f59fe3bb63ed5f7`;
  unit/argv unchanged. TLS/served certificate/directory binding and RU/NL publication
  PASS. Current leaf/CRL bound07:48:57UTC; no manual extension/floor rollback/timer change.
- Three-target P1 applied05:44:52UTC and independently read back, no second restart.
  Group file SHA256 `1cb942471c3d1349a4551b7acb922adc75e788549201a0cbabb764b72b858103`;
  service-owned0600 under0700 directory. PacingOFF, default muxLEGACY64/countersOFF;
  negotiated P1 CREDIT128 remains distinct from the global default.
- Owner USB snapshot initially unavailable; owner confirmed the hour expired and
  enabled diagnostics again. Fresh JSON then succeeds. USB grant is diagnostic
  access only, not a VPN activation or profile entitlement.
- New automatic owner session
  `f7b99af5a2538b0cd8a8fd1cab9599bfbb50819e431ef5e828617d28530cb2f4`
  matches both-end P1/RS32/32/CREDIT128, same106/Support ID, Wi-Fi422/TUN.
  No Connect/Disconnect/profile command sent in this phase. Full1024-byte HTTPS200,
  TLS verification, TUN-bound request completes **3.421557s**; no topology change.
  Raw protocol errors2→2 are expected crossings; actual/unclassified and Mux
  incident_dropped0 (bounded lifecycle trace evictions remain separately recorded),
  DNS errors0, DNS responses33→34, TCP-open errors0. Standard normal JSON preserved.

This post-deploy check supplements, not duplicates, earlier19/19 Wi-Fi bodies and
the real automatic Wi-Fi-return check (106.578s from Wi-Fi creation to CONNECTED).
No overnight, arbitrary-low-bandwidth, universal speed or Wi-Fi-upstream guarantee.
Same32MiB continuation budget now **8,408,064 bytes**,25,146,368 remaining; old
25,204,736 reservations untouched. Carrier/background bytes separate. All temporary
collectors/finite monitor exited; normal bounded diagnostics intentionally retained.

## APK and delivery scope

`state-client-build/owner-diagnostic106-20261022/delivery/FamilyConnect-0.1.18-beta106-recovery.apk`

- SHA256 `242855c43e889e708234ce2f687fa02d37bccb1eee408904f09216b6abd8f020`.
- Signer SHA256 `67a90d1bfcd5a2c0666f0cff1b0ac5e43aaa661ca1196f89e879aa39fe20848a`.
- Package `com.familyconnect.app.friends`, versionCode106, Android12+/API31,
  arm64-v8a,16KiB aligned; native performance build tags empty, fault schema0.
-102 health /103 deadline-cancel /104 bounded750ms reorder /105 pressure fix
  retained for their own regression evidence;106 restores bounded diagnostic export.
  Native bytes unchanged from105;219 JVM tests passed in the existing106 build.
- Exact signed65/96→106 package/signer/increasing-code static paths now checked,
  in addition to88/94/104/105.65 minSDK26 is historical, not106's requirement;
  recorded Krasnodar API31 and Volgograd API34 meet106's API floor. The server's
  Krasnodar65 observation is stale05 October; do not claim it is still installed.
  Volgograd96 is established by the supplied22 October ring. Physical tester
  updates to106 are not yet observed; owner105→106 physical data/identity preservation
  is already verified. Do not overwrite a newer installed version.

| Gate | Result |
|---|---|
|OWNER_WIFI_ACCEPTANCE|PASS_BOUNDED106, including one small body on new gateway|
|RECOVERY_ACCEPTANCE|PASS_BOUNDED106 automatic Wi-Fi return; explicit cancellation separate|
|SIGNED_APK_READY|YES, same already signed106|
|TESTER_P1_POLICY_READY|YES, exact confirmed three; actual tester106 negotiation pending field use|
|FIELD_WHITELIST_VALIDATION|POSITIVE_REPORTED_VOLGOGRAD96_WITH_CELLULAR_MESH_DIAGNOSTICS|
|FIELD_106_P1_VALIDATION|NOT_RUN; Krasnodar also NOT_RUN|
|PRIVATE_FIELD_READY|YES, limited manual handoff, not a public/general acceptance|

Next: owner sends the unchanged106 privately. Install in place, preserve data/ID,
choose `P1 · RS32/32 · CREDIT128` while disconnected in the ordinary Settings item
still labelled “MESH owner test · next session”, then one MESH mobile-data attempt
with Wi-Fi off and a new small response. No mandatory preliminary Wi-Fi refresh;
record valid cache/expiry separately. Export JSON regardless of result. Do not choose
P2/Q1. [RU/EN instructions](../clients/OWNER_RECOVERY_CANDIDATE.md).

Rollback: preserve evidence, use the generated existing transition operator
`state-client-build/tester-p1-cohort-20261023/transitions/operate.py rollback --shared-restart-approved`
only for a demonstrated need, with a coordinated restart and fresh guards. It restores
the exact3a08 executable, not old credentials/DB/config; that executable ignores the
new group file and retains owner-only P1. No rollback performed or automatic P0.
APK stays106; no uninstall/downgrade/data clear. Any app correction must preserve
signer and increasing code. Do not rerun stage/deploy/apply with uncertain outcomes;
reconcile durable receipts first.

Raw source, original report, identity mapping, test logs, rollback receipts and
post-deploy meter evidence remain ignored under `state-client-build/`. Exact hashes
are indexed by the [delivery receipt](2026-10-22-private-field-delivery-receipt.json).
Closeout verifies all88 evidence hashes, all279 frozen gateway source files and the
actual APK/binary against the receipt, with no mismatches. Five policy fixture
Python files parse; `git diff --check` passes. The delivery directory also contains
`PRIVATE_TEST_README.txt` (RU/EN), indexed by the receipt. No additional traffic,
signing, installation or deployment was needed for this closeout.
