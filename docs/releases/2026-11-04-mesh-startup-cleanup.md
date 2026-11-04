# MESH startup — cancellation and bootstrap cleanup, 4 November 2026

## Selected scope and version boundary

Owner selects the remaining HELLO/reconnect diagnosis after the bounded114 DNS gate.
Continue FLEET-BOOTSTRAP-2 only: pair the existing phone session with gateway cleanup,
reproduce lifecycle failures locally, fix them without preempting active ownership or
changing admission/timeouts. No public release or production mutation is selected.

Installed owner Android remains0.1.18-beta114/code114, exact source3d3bf26 and APK
SHA256 `53b824cebc963dfcb2478c8bf53262d0093cd530f020ea2d3588474227cb97ac`.
Public/invitation/updater113/catalog7; Linux0.2.11 and Windows0.2.16/catalog12 unchanged.
The [17:00 DNS/HTTPS acceptance](2026-11-04-android114-dns.md#final-bounded-dns-gate--1700utc)
remains valid for that one session, not stable reconnect. The changes here are source
and local-test results, not an installed phone or server fix.

## Paired physical observation

- 17:06:22 phone114 is CONNECTED/Wi-Fi/native2/NONE with renewed app USB consent.
  A read-only NL1 journal match uses the exact private native session tag; no identity,
  tag, credentials or room URL is printed or committed.
- 17:09:30.865 normal Disconnect;17:09:31.356 DISCONNECTED with capture released.
  A single normal reconnect starts17:09:34.978, then enters RESTORING at17:10:09.200
  with SEED_ADMISSION/DEADLINE, not the earlier HELLO_RECEIVE stage. The bounded150s
  observation does not recover; normal Disconnect releases capture again. The final
  observed phone state is DISCONNECTED, not the earlier17:00 CONNECTED. No repeated
  blind connection attempts, data clearing, profile change or permission bypass.
- The exact old gateway session first reports RELIABLE_RETRY_EXHAUSTED17:09:40.937,
  then gateway_session_failed and CLEANUP/COMPLETED by17:09:40.963: about10.1s after
  local Disconnect, not prompt peer RESET termination. The process stays PID991255,
  active since16:41:26, NRestarts0 across these observations; no service restart here.
- A separate bootstrap exchange authenticates17:09:28.330 and waits at challenge
  until context_deadline17:11:25.629. Its opening17:09:25.629 precedes the controlled
  Disconnect. Its identity is not established by the available log; do not attribute
  it to the owner or infer a specific other user. The single-seed exchange model and
  this occupied window are consistent with admission blocking, not a packet-level
  proof that the owner's OPEN frames reached the gateway.

The first extended1000-record tail is limited; a narrower17:09-onward reread has277
records without truncation and34 exact old-session matches. Earlier evidence stays
retained. No server write, restart, ownership takeover, renewal or policy change is
issued. Private snapshots/receipts remain under ignored
`state-client-build/android114-startup-20261104/`.

## Reproduced causes and source changes

1. **Carrier cancellation races RESET delivery.** Android VPN and chat cancellation
   reaches the media carrier and ReliableStream through the same parent. Media closes
   while ReliableStream is trying its already-bounded RESET writes. A deterministic
   real Session/VP8-framing test holds the first RESET at the writer: cancellation and
   deadline cases fail with the old constructor; explicit close is the control.
   Client-only `NewOwned` retains the media path for upper-layer teardown, while all
   authentication/data/admission contexts remain cancelled. No grace timeout is added.
2. **Authenticated dead waiters retain the bootstrap exchange.** The broker correctly
   waits for old active ownership, but that wait was not tied to the new peer's closed
   Family stream. A real Family-authenticated fixture closes its waiting caller; the
   old code still holds the exchange. `Session.Done` now cancels only that exchange.
   The previous active gateway remains busy and unclosed: no preemption or duplicate
   room is used to make the test pass.
3. **Lease-reader teardown also races RESET.** Fixing only the server's closed-peer
   cancellation makes direct secure-close pass, but client bootstrap cancellation
   still fails. Its read loop closes the routing lease before secure RESET can pass.
   The reader now drains with the owned carrier, then is explicitly stopped and joined.
   The full cancelled-bootstrap regression passes and admits a fresh seed lease while
   preserving the existing active owner.

These are independently reproduced lifecycle defects matching the failure mechanisms;
the available physical logs do not prove every earlier timeout has the same cause.
Loss of every bounded RESET remains possible. No blanket startup, low-speed, provider
availability or sustained-stability claim follows from local tests.

## Qualification and next gate

Retain red/partial-fix/green receipts. New tests cover cancellation, deadline, explicit
close, cancelled creation, failed-connect cleanup, authenticated wait cancellation,
old-owner preservation and shared seed-slot reuse using disposable ProductStore-issued
Family fixtures. Go1.26.0 and fresh disposable fixture material are used; no production
profile or credential is copied into tests.

- The initial seven-package `-race` run has510 passing test/subtest events,29 optional
  skips and7 failing events (six cases plus their parent), all in the old
  `TestProductIdentityOverBootstrapCarrier`. The failure is its assertion that rejected
  TLS emits no diagnostic; the current server already emits `family_open` evidence.
- The same test on an ignored clean export of unchanged parent `d8c510499316f006d8223ec0244825b7edcd3ce6`
  reproduces exactly the six failing cases and assertion. No unrelated test is rewritten
  or diagnostic suppression added to obtain green results. The complete run is NOT PASS.
- The separate mandatory negative boundary suite executes with fixtures: valid control,
  unknown identity, wrong family, revoked identity, wrong gateway, stale CRL and stale
  revision. Rejected identities still create no room and never authenticate.
- `telemost`, `familysession`, `wholedevice`, `restrictedowner`, `roombroker` and
  `reliablestream` package race runs pass. Optional live-provider, isolated canonical-root,
  process/helper and packaged Python-publication checks are not claimed as executed.
- A second bootstrap run excluding only the first inherited test finds a second old
  intermittent assertion in `TestAuthenticatedBusyExchangeReportsChallengeReason`:
  direct error equality rejects the existing primary-cause wrapper even though the
  visible rejection code is unchanged. Unchanged parent reproduces9 failures/21 passes
  over30 runs. The first full current run passed this test; the later negative is also
  retained. Neither test is removed or altered in this patch.
- Final new regressions pass under `-race -count=10`:90 test/subtest pass events,
  zero failures/skips, covering the two authenticated-wait cases and all owned-carrier
  cases. The shared-seed-reuse assertion is included in this repeated final source.
- The final bootstrap selection excludes exactly those two baseline-failing tests:
  103 test/subtest passes, one optional Python-publication skip, zero failures. The
  mandatory negative-authentication boundary executes in this selection. This focused
  result does not turn either retained failed full-package attempt into a PASS.
- `gofmt -l` and `git diff --check` are clean. Targeted documentation links pass for
  six changed documents/540 links. STATUS checks109 links and retains one unchanged
  October27 historical anchor error; none of the new links is missing.
- Exact-source hosted CI/build/runtime qualification is not inferred from these local
  source checks; the older phase0 provisioning failure also stays open.

The bounded diagnosis/source correction is complete; full-suite and delivery acceptance
are not. Safe source/tests/docs form one logical checkpoint; raw private evidence and
disposable credentials are excluded from Git.

Delivery remains OPEN: qualify the exact source for the Android native client and both
gateway runtimes, preserve current fleet writer/renewal custody, then deliver a new
immutable Android version and the qualified gateway change. Existing114 alone cannot
exercise this source fix. Physical acceptance requires paired disconnect/reconnect,
prompt remote cleanup/seed-slot release and ordinary-UID DNS/hostname HTTPS, with
failure/low-speed cases retained. Do not announce rollout from a source push.

## Rollback and privacy

No production rollback is needed for this source-only change. Revert only this logical
source change if qualification fails; retain local evidence and immutable113/114 APKs.
Do not reset/clean other work or restore product DB/profiles, keys, floors or invitations.
Future runtime delivery needs its own exact-version rollout/rollback receipt; no server
unit, timer, catalog, signer or protected identity is changed here.
