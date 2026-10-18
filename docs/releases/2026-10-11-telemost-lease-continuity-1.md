# TELEMOST-LEASE-CONTINUITY-1 — renewal PASS, persistent TCP PARTIAL

11.10.2026. **AUTHENTICATED RENEWAL LIVE PASS / PERSISTENT TCP PARTIAL.** This is a new
continuity requirement, not a retrospective implementation defect. The previous
600s expiry was expected. Historical unexpected carrier/DATA failures stay OPEN;
no attribution to this lease is made.

Bundle **B**: `state-client-build/field65-export16/telemost-lease-continuity-1/`.
Work only in **B/source**, copied from the preserved continuation checkout.
Parent HEAD `6f3772942f3f3e45aba9a309233ebe8b8a31bf14` plus the retained ownership
overlay; prior native provenance `aebd6fa70d3b1b8cd894e3816eb9633a52a71cff` is
historical, NOT the provenance of a new native build. `research-manifest.json`
records exact candidate file hashes and baseline-relative patch. Explicit local
commit authorization was given; source fbbecb81c033557f6c29819a02b8382519465961,
tree06ca3d03620fc773d4bbb1528e2a0f193d7727a5. No push/tag/public distribution.

## Private build and installation checkpoint

- Research82/code82, `0.1.18-research82-lease`, package unchanged. Signed APK
  c84060e715c0f128e939cc90ca2cbc5225887325b20ba60f89d5a9354ea36b18.
- Restricted native743080ad01481ef2e839a1e4e92619a32956bb52bf85c7b666e6ac0ac51e8664,
  current embedded restricted-build.json, Go1.26.1/NDK28.2.13676358, real Telemost,
  no diagnostic build tags. Other23 native libraries and original normal-native
  manifest byte-identical to81; not represented as a new normal-native build.
- Gateway34704e26029bf1eee4ae7679712c673eec7989b291f1a6f47c87c2b40973d958,
  same frozen source, loaded/next verified, invocation3d9e1d2923a5423e9a11afbed13648de.
- Same Android signer67a90d1bfcd5a2c0666f0cff1b0ac5e43aaa661ca1196f89e879aa39fe20848a
  and UID10283. One in-place update; no uninstall/data clear/re-enrollment. Update
  briefly stopped ChatDeliveryService; ordinary launch restored it before trial.
- Frozen-source targeted Go/race PASS,10 repeated lease/race runs PASS,51 targeted
  Android JVM tests PASS, actual non-debuggable packaged JNI device fixture PASS
  with zero network/owner-native starts. Test helper removed. Full suite NOT green:
  the six historical diagnostic assertions stay unchanged and separately open.
- One attempt used old disposable fixture with insufficient22min security headroom
  and correctly hit expiry. Fresh same-policy disposable fixtures PASS; product
  expiry was not relaxed. Gradle sandbox socket denial rerun outside sandbox.
  Current-source normal-native verifier rejects historical tcp_source hash; exact
  baseline artifact/manifest/23-library reuse is the applicable check, not rebuilt
  normal-native provenance. The failed check is not called a PASS.
- Actual preflight found the old gateway leaf expired although directory/process
  were still present. Existing same-key4h policy renewed only leaf/canary material;
  authority10, grants, floors, publisher and normal services preserved. One bounded
  NL replacement/reload and normal RU sync. New served chain and directory PASS.
- Owned nginx8443 uses keepalive_timeout10s. Direct25s socket preflight failed,
  unrelated to Telemost; before trial the workload was fixed at128-byte numbered
  ranges every5s (~26B/s), without changing nginx. Independent64KiB HTTPS every120s
  runs separately. One socket/handshake, no reopen; total well below8MiB.
- Ordinary one-CONNECT trial completed. Two renewals and application traffic after
  both previous deadlines PASS. Persistent TCP passes only the first boundary;
  full live SEAMLESS_CONTINUITY is **not established**. No second attempt.

## LEASE_CONTRACT

Originally `Challenge` granted a nonrenewable 10-minute lifetime starting at
acquisition, implemented as the parent context deadline. The descriptor's 60s
unused/admission budget is separate; READY did not reset the lifetime. Setup,
create/ready timeouts, bootstrap exchange lifetime and cached directory expiry
remain unchanged. The broker-process lifetime is terminated by `Broker.Close`.

New candidate: 10 minutes becomes a renewable authorization interval, not an
unconditional maximum session age. New expiry is server-selected
`min(server_now + existing Lifetime policy, dedicated Family security deadline)`.
Neither client heartbeat nor ordinary availability authorizes an extension.
The Family deadline remains the minimum of the established local/peer certificate,
CA and CRL expirations. Grant lifetime is materialized in issuer certificate
expiry; issuer/grant/CRL/floor publication retains its existing contract. There
is no new direct ProductStore query or stronger revocation propagation claim.
Renewal never replaces these credentials; a nonextendable security bound is
confirmed without extension and awaited, not polled or silently increased.

## AUTHENTICATED_RENEWAL

No existing authenticated active-holder renewal was found. Existing HTTPS and
bootstrap refresh provision directories/credentials or acquire new rooms; they
are not active-holder continuation. Repeated `ChallengeAfterCleanup` would wait
for this identity's current holder and is explicitly not used.

One narrowly scoped internal service, `lease-renewal.family-connect.invalid:1`,
uses ordinary OPEN/DATA on the **existing Family TLS/Mux**. No second carrier,
Family session, room, PKI or network-listening control server. The service callback
is installed only on the broker-bound dedicated gateway session. It closes over
the actual setup object/generation, validates fresh `SessionAuthorizer` material,
same identity/key/role, state ACTIVE, current deadline, setup ID, sequence and
previous accepted deadline. TLS record protection and existing room binding are
reused. An exact retry returns the same receipt without further extension; old
sequences or another session cannot acquire authority.

Flow: offer → renewal request → accepted receipt → client applied → confirmed.
Lost-result reconciliation reads the same holder's accepted state rather than
renewing twice. Both sides retain bounded action/sequence/deadline metadata in
the existing trace; Android projection preserves only enumerated/numeric fields.
The public diagnostic golden schema is explicitly extended by those two optional
fields; historical negative-auth assertions are unchanged.

Scheduler starts at approximately 80% of the remaining permission (normally
minute 8), leaving 120s for at most three 15s exchanges plus two 5s retry delays.
The client uses server remaining time anchored at request start, not receipt time,
so round-trip time cannot lengthen its permission. AUTH/protocol rejection stops
without retry. Temporary failure cannot exceed the last confirmed deadline.
Initial offer loss does not tear down an otherwise valid legacy lease early.

## SECURITY_NEGATIVE_CASES

Managed-clock tests cover foreign identity/session, stale sequence, expired
security bound, revoked authorization, canceled context and late authorization.
Real Family control tests re-read a raised CRL floor and reject renewal without
advancing the sequence. The established bootstrap mandatory rejection test is
6/6 negative PASS plus valid control. The full bootstrap suite still reports
the **six pre-existing diagnostic assertion failures**, separately tracked as
DIAG-AUTH-REJECTION-1; no skips/relaxed assertions or global green claim.

## LIFETIME_AND_TIMER_RACES

The renewable lease owns a finite cancel-cause timer, not an immutable deadline
in descendants. Setup/connect/read/write/security deadlines are unchanged.
Renewal and timer expiry serialize under the lease mutex; elapsed permission
cannot be resurrected. A delayed old callback checks the current deadline.
Cancellation, server close and unrecoverable transport failure still close the
same context. Deadline cause remains identifiable in Telemost and Family traces.
Authorization and diagnostics callbacks execute outside the broker mutex.
Tests include blocked authorizer with expiry/cancel/server-close, timeout to the
old deadline, two renewals, stale timer and replacement-generation isolation.

## ADMISSION_OWNERSHIP

One identity holder remains one holder throughout; unchanged admission limits.
Existing lookup paths now perform authorization outside the broker lock. Cleanup
removes the map entry only when its pointer is still the same holder. Renewal
uses no Challenge/provider call. The optional control exchange consumes one
ordinary bounded Mux stream briefly; it opens no destination TCP socket. Existing
Mux scheduler, framing, queues, Reliable RTO/MaxRetries and Codec2 are unchanged.

## CLIENT_SERVER_COMPATIBILITY

Old client/new server: never requests the service, retains original finite expiry.
New client/old server: an ordinary OPEN receives existing `policy_rejected`;
client sends no renewal body and retains legacy expiry/recovery. New payload is
sent only after OPEN_OK. No bootstrap JSON, descriptor or binding-ACK change.
Local Family/Mux tests verify both directions. Startup-refresh, recovery and UI
are retained; UI rollback draft remains in its previous separate bundle.

## LIVE_RENEWALS

**PASS for this episode.** Exactly one ordinary UI/orchestrator CONNECT,
08:48:19.153UTC; READY08:48:44.010. Acquisition08:48:29.318, original deadline
08:58:29.318. Evidence-first TEST_STOP09:10:44.219:1320.209s after READY,1345.066s
after CONNECT, including snapshot overhead; workload uses finite1320s/1500s limits.
No manual reconnect, code change during the trial or repeated trial.

Same holder/session tag throughout:
`08146581a668ab56208b865b3a5f78d827cb85559f85c4e085d4d0b61cadf7e5`.

| Sequence | Server request / accepted UTC | Server applied / client confirmed UTC | New deadline UTC |
| --- | --- | --- | --- |
| 1 | 08:56:34.129 / 08:56:34.129 | 08:56:35.122 / 08:56:35.314 | 09:06:34.129 |
| 2 | 09:04:33.621 / 09:04:33.623 | 09:04:33.790 / 09:04:33.977 | 09:14:33.623 |

Both accepted before the previous deadline; exactly600s server-selected new term,
not a client-assigned deadline. Both sides' receipts match. Existing bounded
diagnostic-ring snapshots and finite filtered journal reads at9/17/21 minutes,
failure and cleanup used; no15min collector represented as22min coverage. Initial
confirmation with sequence0 is not counted as a renewal. Source/build clean gate
passed before building; no fabricated embedded provenance. Evidence:
`B/receipts/live-analysis.json`, `live-result.json`, `gateway-after-cleanup.json`.

## PERSISTENT_TCP_CONTINUITY

**LOCAL PASS, LIVE PARTIAL.** Real Family TLS/reliability + production Mux and
a real loopback TCP echo socket, with manually controlled broker lease clock.
One accepted TCP socket and the same MuxStream pass exact numbered payloads at
lease ages 0,10,20,22 minutes; renewals accepted at 8 and16, final deadline26.
The test then expires the lease and checks holder/socket cleanup. No socket
reopen is counted. This is more than an ACK-only test, but not Telemost media
or Android/TUN live evidence and not a22-minute wall-clock soak by itself.

Live uses exactly one Java Socket/SSLSocket, one TLS handshake, local port42184,
socket identity93679769, connection108ab33a-34e3-4c01-bf9b-466b98049c3c. Verified
128-byte numbered ranges0–169 (21,760 bytes),08:48:45.323–09:02:50.900UTC, through
the original08:58:29.318 deadline. At sequence170/09:02:55.114 the helper recorded
IllegalStateException and closed that socket; **no reopen**. The precise failed
assertion/HTTP header was not retained, so endpoint EOF/response-contract failure
and other causes are not distinguished. Do not invent a TCP/carrier root cause.
The contemporaneous ring is CONNECTED/native_state2/terminal_reasonNONE, same
session, no typed carrier close. Persistent data after the second renewal/previous
09:06:34.129 deadline is **not proven**. The full persistent-stream criterion is
not met; ACKs and new HTTPS sockets do not replace this missing evidence.

The helper's generic final string `NOT_REPRODUCED_IN_THIS_EPISODE` covers its old
carrier-loss counters and does not incorporate persistent_failed. It is retained
unaltered but explicitly **not used as a continuity PASS**; live-analysis is PARTIAL.

## APPLICATION_REQUESTS

11 complete independently verified HTTPS206 responses ×65,536 bytes, zero request
failures, including after both previous deadlines on the same selected Family/Mux
session. Plus21,760 verified persistent bytes =742,656 bytes (~0.708MiB). Workload
maximum including all scheduled bodies is820,480 bytes; failed chunk170 is not
counted as verified. Own previously authorized RU8443 download endpoint, exact
TLS verification and pinned body/chunk hashes; no scan/speedtest/FIELD. Background
chat remains on, DIRECT at all captured checkpoints, not silently disabled.

## UNEXPECTED_CLOSES

Selected live carrier: no unexpected close/loss before TEST_STOP. Persistent
application-stream assertion failure is separate and UNKNOWN, not a lease expiry.
Server first-close RELIABLE_EXHAUSTION09:10:54.429 follows deliberate client
disconnect09:10:44, not either lease boundary; terminal cleanup follows.

The shared gateway journal also contains a distinct session be1f2f9e…70eed,
authorized08:47:43.360 **before CONNECT**, first-close RELIABLE_EXHAUSTION
08:48:21.125. It is not the tested session or either renewal and is not erased or
counted as renewal recovery. Its exact cause/producer is not established by this
journal alone. Entry old process86e… with NRestarts2 also remains unattributed.
Historical unexpected failures remain OPEN/UNKNOWN.

## AUTOMATIC_RECOVERY_IF_ANY

No recovery/loss events or replacement session for the selected live connection.
Ordinary recovery code is untouched. Prior
research81 recovery evidence remains historical, not renewal acceptance evidence.
This implementation targets preserved streams, not BOUNDED_RECONNECT; overall
live SEAMLESS_CONTINUITY is not claimed because persistent acceptance is partial.

## CLEANUP

Evidence saved before TEST_STOP; native-fixture and episode helper packages
removed. No new persistent peer/collector. Temporary staged issuer validator/
publication/acceptance helpers and upload copy removed after receipts; protected
rollback/evidence retained. Exactly one production gateway replacement/reload and
one same-policy leaf renewal; **cleanup restarts0**. Main dirty tracked diff was
byte-identical before adding these documentation updates (SHA256
`8883ce617af5f657c16481acbc8045bad9502ec4fa3f73f4b41027e0f5c9a86c`).
Previous artifacts, receipts, signing material and UI rollback draft are retained.
Disposable local test profiles remain in B/private (not Git, mode0700 directory).

Final installed owner: research82-lease/code82,
APK `c84060e715c0f128e939cc90ca2cbc5225887325b20ba60f89d5a9354ea36b18`.
Gateway loaded/next:
`34704e26029bf1eee4ae7679712c673eec7989b291f1a6f47c87c2b40973d958`.
Final invocation `3d9e1d2923a5423e9a11afbed13648de`; matched loaded/next arguments.
Family Connect VPN OFF (ConnectionService absent), ChatDeliveryService ON.
Final served-chain/directory preflight PASS; normal AWG/TCP/API/mailbox runtime,
keys, identity/admission/revocation/publisher bindings preserved; CRL floor
monotonic and sync timer restored. No data clear/re-enrollment or public release.

Rollback is **not executed**: retain old gatewayc101… and exact prior unit in
`/opt/apps/family_connect/restricted-materials-stage-20261001/lease-continuity82-20261011/`.
Revert only the new99-zzzz-lease-continuity82.conf ExecStart with a separately
bounded reload and valid current credentials; do not restore the expired leaf or
blindly re-enable spent O_EXCL observer paths. Android rollback requires signed
in-place build with unused higher code; never downgrade/data-clear or overwrite81/82.
UI rollback draft stays separate, not applied. No public APK/FIELD distribution.

## Remaining work

Persistent TCP acceptance remains OPEN. Before any separately authorized future
episode, distinguish endpoint/socket EOF from response/assertion failure using
bounded non-sensitive error codes; do not rerun this trial until success. Historical
unexpected closes and six diagnostic assertions remain separate open issues.
The new lease no longer mandates a ten-minute carrier break in this observed
authorized session, but this is not a general end-to-end seamlessness claim.

## Local receipts

- `lease-accepted-repeat.log`: managed-clock renewal/lifetime and real Family/Mux
  tests repeated10× with race detection.
- `core-accepted.log`, `diagnostic-accepted.log`: targeted package checks,
  including ordinary and owner-diagnostic builds; no live provider.
- `targeted-authenticated-final.log`: wider regression, including Telemost,
  and the explicitly retained bootstrap diagnostic failures.
- `auth-boundary-final.log`: actual negative security rejection plus valid control.
- `java-projection.log`: five focused JVM projection tests, not Android runtime CI.
- `go-vet-accepted.log`: targeted vet. Initial sandbox socket denial and intermediate
  failing checks are preserved separately, not reported as successful receipts.
- `research-manifest.json`, `RESULT.json`, `SHA256SUMS`: source/evidence inventory.
