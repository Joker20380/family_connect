# Beta63: genuine native exhaustion and recovery, 2026-10-04

## Result and unchanged delivery

**Physical native exhaustion → production poll → fresh session → HTTPS PASS.** This
closes the narrower native-failure integration gate left open by the earlier synthetic
policy test. It does not establish mobile-network stability or fix the original DATA stall.

Owner Redmi31ce63ba remains `0.1.18-beta63`/code63, source
`de7cacde133d96423939dfcde5da048f97d87d46`, published/installed APK SHA256
`ce81216a84005880eef834dd5f576d0c43082b1c501767c7cf83522a765aebb8`.
No product APK build/install/signing/publication, gateway deployment, admission change
or material renewal in this task. Only a private, same-signer instrumentation APK was
installed and subsequently removed. Default/updater/invitation remain60; tester last
authenticated receipt remains62. Existing [delivery/rollback](2026-10-04-beta63-recovery-candidate.md)
is unchanged. No tester repeat requested.

## Preflight and fault isolation

17:04UTC read-only RU/NL preflight: Redmi connected; two existing devices admitted and
non-revoked, revisions3/1, issuer4, CRL4441, loaded certificate/profile match. Gateway
PID3908811/restarts0 and binary
`6773423c960c303c4a1b3b6dea35941d3011873d7ee7a3cf31818f3672372f09` unchanged.
Effective expiry remains **04.10 17:30:19UTC**; authenticated native-validated owner
refresh/ACK passed with1340s remaining in its receipt, no cache clear. The earlier
gateway bound, not the later receipt expiry17:31:33UTC, governed this acceptance.

Private JNI test code attaches classic socket filters to56 UDP sockets belonging only
to the app process. It drops incoming RTP/RTCP-version2 datagrams while allowing STUN
and DTLS shapes and leaving TCP/WebSocket untouched. Before use, an on-device loopback
selftest verified control passage, RTP-shaped drop and delivery after filter removal.
No root, phone-wide firewall, server filtering, key/profile edits or production hooks.
Duplicated socket descriptors keep detach ownership stable despite original fd closure;
all filters and duplicates are released before recovery, and again in a finally block.
The copied private library is removed afterwards.

The test-only Host adapter selects restricted after ordinary configuration, without
deleting existing AWG/TCP profiles. Native code, classifier, `AutomaticConnection.poll`,
orchestrator, guard/TUN owner and BOOT-1 use the installed production implementation.
The test explicitly calls production poll after observing native failure; it is not a
long-running user-interface/service scheduler or mobile handover acceptance.

First attempt hit the harness's32-socket safety bound, detached all installed filters
and stopped before the fault scenario. Its failure receipt is retained. Revised private
bound512 accepted the actual56 sockets; no production binary/assertion was weakened.

## Physical observations

- Initial real restricted session and HTTPS200 succeeded.
- RTP receive loss applied **17:11:58.253–17:12:07.573UTC** (9320ms).
- Native itself entered phase3, `reliable_terminal=recovery_exhausted`, terminal
  `IO_CLOSED`; no injected failure enum or synthetic diagnostic snapshot.
- First native failure: CARRIER/FAILED/RELIABLE_RETRY_EXHAUSTED, sequence34,
 17:12:07.486UTC, oldest block9540ms, retries8, pending8, ACK received57,
  ACK age9285ms and progress age9285ms. Failure precedes local-close/TLS cleanup events.
- After removing the filters, production poll emitted NETWORK transport loss and one
  restoration success. Old native handle invalidated; new handle/session established;
  healthy polling and HTTPS200 succeeded again.
- Filter cleanup errors0; copied probe library removed. Final UID/inode/first install,
  identity, enrollment, activation and Support preserved; private instrumentation removed.

Original tag:
`272114ff166d5b28c804703428acf0aedf0dece215a4c36b4db977ca50744c1f`.
Restored tag:
`febba6e99fc75bb2be7a29d06273bbd3befb2f60a7bf70c4652afcbaafc20090`.
Read-only Amsterdam journal projection:53/56 events respectively, gap-free sequences;
both include descriptor issued, gateway join, carrier, Family TLS/session and cleanup.
Only allowlisted trace fields retained. No full four-ID export correlation claimed here.

## What this adds to the DATA/ACK investigation

The intentionally blocked direction was gateway→phone RTP. On the gateway, the same
original session reaches retries8/pending8 with **ACK age664ms but progress age9139ms**
(68 ACKs received). Thus the actual stack can produce continuing ACK traffic without
confirming outstanding DATA under known one-direction media loss. On the blocked phone,
ACK traffic also stops; its ACK age9285ms is intentionally different from export(11).

This explains why fresh ACKs alone do not prove DATA delivery, but it does **not** locate
the field loss. Original mobile sessions lack matched per-block transmit/receive/SACK
and fragment-reassembly decisions. Do not infer RKN, certificate failure or a particular
network hop from this controlled result. Later failure in the restored server session
is confounded by intentional teardown, not a second uncontrolled reproduction.

## Local cross-layer regression

Added `carrier/telemost/reliable_framing_test.go`: real ReliableStream → carrier
fragmentation → VP8 payloading/RTP → reorder/frame assembly → fragment reassembly →
ReliableStream, using synthetic data, two in-memory endpoints and production defaults.
One middle RTP packet of the head DATA message is selectively dropped on each attempt;
ACK frames and later DATA are not targeted. Controls cover no loss and healing on a
later attempt; persistent loss must exhaust with fresh ACK/no cumulative progress.
Sequence numbers start near RTP wraparound. This is not a live SFU/network simulation.
Validation **PASS**: focused race run; full race for `telemost`, `reliablestream`,
`sessiondiag`, `sessiontrace`; three additional focused race repetitions. Initial two
compilation attempts failed on `/tmp` quota before tests ran (including outside sandbox);
build temporaries/cache moved to ignored workspace storage, not a code/test failure.

| Control | Actual head DATA attempts | Deliberately dropped RTP packets | Outcome |
| --- | --- | --- | --- |
| No loss | 1 | 0 | Eight byte-exact16KiB blocks, window reopened |
| Heal after four losses | 5 | 4 | Same ordered bytes, window reopened, no terminal failure |
| Persistent head gap | 9 | 9 | Eight retries,8 pending, terminal recovery_exhausted |

Persistent cases in the three repeated runs still received25–26 ACKs/21–22 SACKs,
with ACK age≤2s and progress age≥8s. No direct failure injection; only one RTP packet
per targeted DATA transmission is removed. This narrows a reproducible mechanism, not
the field attribution. Tests use unchanged default payload/window/RTO/retry/age settings.

Reproduce from `carrier/` with Go1.26.0 (set GOTMPDIR/GOCACHE to writable, sufficiently
large directories if `/tmp` is quota limited):

```sh
go test -race ./telemost ./reliablestream ./sessiondiag ./sessiontrace
go test -race ./telemost -run TestReliableStreamOverVP8MissingRTPWithFreshACK -count=3 -v
```

## Remaining work and rollback

1. DONE focused/full-neighbor race checks and three repeated cross-layer runs. Only a
   regression test was added to production source control; no runtime implementation change.
2. Add bounded paired per-block/fragment evidence before another mobile request:
   session-local sequence/ACK/SACK, frame/reassembly drop reason and counters, no payload,
   destination, keys or provider credentials. Distinguish not-sent, incomplete reassembly,
   delivered-but-unconsumed and confirmation loss. Existing export cannot decide these.
3. Keep timers/windows/retry budgets unchanged until a demonstrated root cause exists.
4. Before later live use, verify/renew the full material chain and fresh native READY/ACK;
   the recorded17:30:19UTC window is not reusable or extended by this successful test.

No runtime rollback required: beta63 and the gateway were not replaced. Harness rollback
is filter detach/descriptor close, normal explicit disconnect and removal of only the
test package/library, all completed. Private receipts/source/signing results remain
under ignored `state-client-build/field63-nativefault`; no keys or raw profiles in Git.
