# TELEMOST-WORKABILITY-PROOF-1

## Final result — PARTIAL; core warm start, egress and client-confirmed renewal PASS

The one allowed physical attempt was completed inside the valid gate window.
**ATTEMPT_CONSUMED=YES. Do not run another CONNECT.** The missing acceptance boundary
is independent owner-scoped attribution of zero server provisioning attempts, not
a demonstrated Telemost/routing/lease failure. The shared server probe log cannot
be reported as zero: it contains two403 records whose owner is not identified.

### Acceptance matrix

| Required result | Observation |
|---|---|
| GATEWAY_CLASSIFIER_DEPLOYMENT | PASS, exact observation-only binary; one controlled restart |
| GATEWAY_PRELIVE_STABILITY | PASS_LIMITED,912.754s/16 snapshots |
| CURRENT_DIRECTORY_AND_CACHE | PASS, sole current directory252c3535…e4341 |
| RESEARCH84_IDENTITY | PASS, unchanged installed APK/code84/signer/UID10283 |
| TWO_PHASE_OPERATOR_PROTOCOL | PASS, fresh ACK before arm; physical CONNECT inside45s |
| PROVISIONING_GATE_ACTIVE_WINDOW | PASS,900s/32 contract,2 blocks, cleanup before expiry |
| ZERO_DIRECT_PROVISIONING | Client pre-dial block proven; independent server attempt attribution INCOMPLETE |
| CACHED_NATIVE_INPUT | PASS, native startup fingerprint equals pre-arm selected cache |
| TELEMOST_BOOTSTRAP / SEED_ADMISSION | PASS by successful authenticated descriptor and production contract |
| FAMILY_AUTH / DEDICATED_READY | PASS, dedicated Family TLS and native state2/full TUN |
| FULL_TUNNEL_EGRESS | PROVEN,7 ordinary Android HTTPS requests, NL source |
| DNS_EGRESS | GATEWAY for the controlled query |
| LEASE_RENEWAL | PASS, authenticated client request/confirmation, sequence1, same session |
| TRAFFIC_AFTER_RENEWAL | PASS, including full responses after the original deadline |
| UNEXPECTED_CLOSES / automatic recovery | NOT_OBSERVED /0 |
| FAILOVER_LEAK | NOT_TESTED; no artificial loss |
| GATE_CLEANUP | CLEANED before absolute expiry |
| OWNER_PRESERVATION | Cache/vault bytes unchanged through closeout; main APK/UID unchanged |

`WHITELIST_WARM_START_READY=NO` for the strict unfinished evidence gate, not a claim
that the successful cached startup failed. `WHITELIST_COLD_START_READY=NO`;
`REAL_RESTRICTED_NETWORK_FIELD=NOT_RUN`; `PUBLIC_RELEASE=NOT_RUN`.

### UTC chronology and continuity

-17:35:22.700 fresh operator ACK received after the preparation prompt.
-17:35:51.106 signed role-only gate ARMED; absolute expiry17:50:51.106.
-17:35:54.693 manual window opened, deadline17:36:39.693. No injected input.
-17:36:22.028 first blocked provisioning operation;17:36:28.894 second block.
-17:36:28.793 client ORCHESTRATOR DISCONNECTED→CONNECTING; exactly one physical CONNECT.
-17:36:29.087 native attempt1 started with directory252c3535…e4341.
-17:36:46.018 authenticated descriptor issued; dedicated join follows. Dedicated
  Family TLS established17:36:52.604; gateway session established17:36:57.466.
-17:37:00.090 harness confirms dedicated READY/full TUN/cached-unavailable fallback.
-17:37:03.860 IPv4 response,17:37:07.613 normal HTTPS response complete via NL.
  Controlled DNS response complete17:37:17.384.
- Initial authenticated lease deadline17:46:39.097.
-17:44:43.828 renewal request sequence1;17:44:45.849 authenticated confirmation;
  deadline advances to17:54:44.145. Session tag unchanged:
  `776990f9668b7dad4f4cc7a047dfd5bc8e038e1a90dfc2d47290aa20d953e5f3`.
- Further complete HTTPS responses include17:47:16.865, after the old deadline;
  the final17:49 request also has independent Mux/wire/endpoint correlation.
-723.814s observation after READY completed;8 probe operations total,3581 received
  bytes (7 HTTPS +1 DNS), below4MiB. No manual reconnect, native retry or tag change.
-17:49:28.984 cleanup receipt CLEANED, before gate expiry. No rearm/extension.
-17:51:33.840 final owner snapshot: VPN OFF, app ON, ChatDeliveryService ON.

Times are wall-clock UTC; gateway monotonic Mux timestamps are joined through the
explicit gateway wall/monotonic receipt, not directly compared with phone monotonic time.

### Egress and DNS evidence

`final-egress-reconciliation.json` reuses only already executed requests: each nonce
joins standard Android socket with VPN=true/TUN address, unique gateway Mux stream
and session tag, NL SYN/time and return tuple, endpoint source port/nonce, and full
Android response. It performs no new network request. All7 HTTPS nonces independently
return `FULL_TUNNEL_EGRESS_PROVEN`. External source is the known NL gateway,
`186.246.45.***`, AS57043 HOSTKEY, not the Orange baseline. Full IPs remain private.

The controlled DNS query uses Android's VPN resolver10.79.0.1, TUN address10.79.0.2,
and a unique nonce observed in the same gateway `Mux.resolveDNS` session; response
rcode0/one answer completes. Exact production path invokes `exchangeDNS` and TCP
configured/default gateway resolver. The upstream resolver address was not retained
in this per-query receipt. This is not a comprehensive DNS/DoH leak suite; Private
DNS was not changed. Global underlay IPv6 absent: `IPV6_EGRESS=UNAVAILABLE`,
`IPV6_LEAK=NOT_APPLICABLE_FOR_THIS_EPISODE`, not IPv6 PASS.

During the test: UNDERLAY available by strict-TLS controls; FULL_VPN established;
ACTIVE_CARRIER=TELEMOST; MESSENGER_ROUTE=DIRECT. Messenger was not used as VPN proof.

### Evidence limitations — not hidden as success

1. Client gate emitted2 blocks before provisioning dial; exact cache and identity
   vault stayed unchanged. Server owner readiness timestamps show0 newly accepted
   challenge/fetch/ACK. However, shared Nginx probe delta contains2 HTTP403 records
   at17:42:19: one restricted-readiness challenge and one `other`. The retained log
   lacks owner attribution and the readiness DB does not count rejected requests.
   Therefore owner server **attempt** count is independently UNKNOWN, not proven0;
   shared log count is2, not0. Do not assign these to owner or to another device.
   They are not evidence of an owner bypass either. This is the first formal blocker.
2. Separate bounded current-invocation startup and episode journal queries each
   timed out; neither query was repeated. Independent server lease event receipt
   unavailable. Client `confirmed` is a validated response from the authenticated
   lease protocol, not a local timer: production `exchangeLease` checks setup,
   sequence and expiry before tracing confirmation. Together with same-session
   post-deadline egress it proves client-observed continuity, but is not relabelled
   an independently collected server `accepted` event.
3. Proposed parallel-stream series NOT_RUN: the unchanged accepted probe has one
   executor. Sequential traffic, pauses and final nonce ran; no parallel-load PASS.
   No natural recovery occurred, so fail-closed during loss remains untested here.

### Counters

| Counter | Value |
|---|---:|
| Fresh operator ACK / physical CONNECT |1 /1 |
| Manual reconnect / native attempts / observed automatic recovery |0 /1 /0 |
| Blocked provisioning operations |2 |
| Accepted owner challenge / fetch / ACK during window |0 /0 /0 |
| Independently attributed owner server provisioning attempts |UNKNOWN |
| Shared probe log records, without owner attribution |2 (403) |
| Client seed bootstrap join / successful dedicated join |1 /1 |
| Shared seed created by controlled gateway start |1 |
| Independent server room-creation counter |NOT_RETAINED |
| Full-phase probe operations / authenticated lease renewals |8 /1 |
| Controlled gateway restarts / natural fatal exits |1 /0 |
| Same-key renewal / owner APK installs / agent owner refresh |1 /0 /0 |
| Instrumentation starts / final launcher restoration |5 /1 |

Instrumentation comprises preparation offline selection, signed gate arm, passive
owner observer, gate cleanup, and post-cleanup offline selection. Existing background
preparation refresh was reused; normal background traffic after final restoration is
outside the closed window. No synthetic CONNECT, input injection or second attempt.

### Cleanup, final runtime and artifacts

Gate cleanup instrumentation controlledly interrupted target lifecycle; VPN OFF
was verified before one ordinary launcher restoration. Cache3301bytes SHA256
`f69338248ef8f422127c06207f3ced3bca6869d04e7403de1fc03abe0d4faab6` and identity vault
are byte-equal before/after the test, before restoring normal background delivery.
Selected canonical response remains
`ea0467c2d8bc356e01d02d8d524bdbb58c182864856cb61c7fe839def757c84b`.
Post-cleanup production identity-bound and installed native offline checks PASS.
No claim is made that every app-data file stayed unchanged or that subsequent
normal background refresh leaves the encrypted cache frozen indefinitely.

Temporary signed control/owner-observer/exact-reader helpers removed. Existing
ordinary probe retained idle as regression tool. Server endpoint/trace units and
test firewall rules removed. Initial cleanup stopped at an absent transient timer
target; a readback reconciled already-stopped units and completed only remaining
cleanup. This was a harness cleanup limitation, not a gateway restart/failure.

Final server17:52UTC snapshot: PID1415977, invocation
`1613fa1ce16d4ea5a649255ddf76829f`, NRestarts0, loaded=next21f0a0fd…509a;
observer ARMED_NOT_TRIGGERED. Strict served chain/DER PASS; same directory252c3535…e4341
on RU/NL, only its current seed accepted. Leaf expiry20:48:29UTC,10568s headroom at
the snapshot. No natural fatal receipt for this invocation; historical causes remain
unchanged. Baseline binaries/configuration/rollback and operational observer retained.

Immutable preparation receipts remain intact. Final local evidence:
`RESULT.json`, `SHA256SUMS-final` (1616 files), `receipts/live-result.json`,
`receipts/final-egress-reconciliation.json`, `receipts/gate-cleanup.json`,
`receipts/provisioning-counter-after.json`, `receipts/provisioning-counter-inspect.json`,
`receipts/cache-window-unchanged.json`, `receipts/owner-final.json`,
`receipts/server-collectors-reconciled-cleanup.json`, `receipts/nl-final.json`.
`final_reconcile.py` and `closeout_result.py` are offline evidence-only adapters;
no product patch/rebuild, no mutation of historical receipts, no commit/push.

**Human result:** основной warm-start и NL egress прошли; lease renewal и трафик
после старого deadline подтверждены. Полный acceptance остаётся PARTIAL из-за
недостающей серверной атрибуции и независимого server lease receipt, а не из-за
найденного отказа продукта.

**One next operation:** offline collector-attribution/server-lease-evidence readiness.
Do not automatically repeat CONNECT, deploy, publish APK, send to testers or run FIELD.

## Historical preparation checkpoint — superseded by final result above

Statements about pending ACK/CONNECT below describe the preserved preparation state,
not the final state. Exact source/build/renewal provenance is retained here.

Evidence root: `state-client-build/field65-export16/telemost-workability-proof-1`.
Previous sealed122 artifacts and source-file hashes verified unchanged. Main dirty
worktree preserved; no product-source patch, commit, push or APK rebuild.

| Identity | Exact value |
|---|---|
| Observation base source | `a4087e000fdbe674b72ede3a6c8822445c87c654` |
| Exact source/test diff SHA256 | `7e7d408670a6ac6afa18e856beb8dcc0ca26a3b6f074e205d4dd25e62d78967b` |
| New binary SHA256 | `21f0a0fdc27b50c00ea922f0b716516e2422aedf1b3797369718f7d00070509a` |
| Previous binary SHA256 | `fa4cf8672c3606c1b6d4d665a6944b4ebe8661076a19a6d2187909263f733eea` |
| New invocation | `1613fa1ce16d4ea5a649255ddf76829f` |
| PID / NRestarts at deployment | `1415977 / 0` |
| Start UTC | `2026-10-12T16:52:44Z` |
| New directory SHA256 | `252c3535d2217e5cf5e2e14264625191e19d7b0dd95625c595426e92ca9e4341` |
| Renewed gateway leaf DER SHA256 | `d1a75cbcc7dc3d39889233f448158261ee0fe9a11e05d6ff875bf1c48936d7b0` |
| Gateway leaf expiry | `2026-10-12T20:48:29Z` |

This is base+exact diff provenance, **vcs.modified=true**, not an invented clean
source commit. Exact sealed candidate rebuilt byte-identically. Accepted targeted
matrix/race×3/privacy/first-cause gates reused for identical inputs. Full suite
still NOT_GREEN: six historical diagnostic assertions and baseline busy-wire flake.
No new failure-name class; assertions unchanged. Observation only, not a Telemost fix.

## Operations already completed

- Fresh observer/NL/RU snapshots before mutation. Pre-renewal leaf17:39:22UTC had
  about3247s headroom, below the planned4020s full preparation/observation/live/cleanup
  budget. Old expiry preserved, not used to reinterpret historical fatal events.
- One accepted AKI-corrected same-key issuance and publication. Standard4h TTL,
  same authority/keys/grants/bindings; normal CRL/floor sequence advancement only.
  Local native, strict OpenSSL/Python checks PASS. RU/NL equality and servedDER
  checked before restart. No owner refresh initiated.
- One controlled restart loads exact candidate; current argv/config matches next.
  Old invocation `e24e32cf8121436ca6ab772f7779362b` stopped16:52:43UTC:
  application `exit_path=signal`, `SIGTERM`, `fatal=false`, cleanup complete;
  systemd exit0/success. This is NOT a natural fatal trigger.
- New invocation creates one normal shared seed. No extra synthetic/owner rooms.
  Routine publication sync performed once; old invocation cache route is not
  assumed accepted. Rollback binary/config retained, rollback NOT_RUN.
- Mandatory900s passive prelive observation completed:912.754s,16 observer+NL
  snapshots and final RU equality. PASS_LIMITED, no fatal/change/restart. Final
 17:26UTC additional checks retain the same invocation/PID/NRestarts0, strict chain,
  servedDER, directory and RU/NL consistency. Leaf headroom12135s at that snapshot.
  This is limited prelive stability, not a long-term guarantee.

Operational stage and rollback:
`/opt/apps/family_connect/restricted-materials-stage-20261001/telemost-workability-proof-20261012`.
Rollback uses its prepared `rollback-observation.sh`, only if needed; no cleanup
restart. Observation executable:
`/opt/apps/family_connect/friends-restricted/bin/bootstrap-broker-signal-observation-20261012`.
Observer directories/0700 files0600 and bounded retention remain in place.

## Operator protocol and finite budget

Current task supersedes the historical arm-before-ACK runbook order:

`PREPARED → READY_FOR_OPERATOR → OPERATOR_ACK → GATE_ARMED → GATE_RECHECK → CONNECT_WINDOW_ACTIVE → CONNECT_OBSERVED → TEST_RUNNING → CLEANUP`.

Early «готов» received before preparation was explicitly rejected as readiness:
no arm, no CONNECT instruction. A fresh ACK is required after PREPARATION COMPLETE.

Research84 gate stays900s/32 operations. Host acceptance budget is30s setup reserve,
45s physical CONNECT window,45s startup acceptance budget,720s after READY,60s cleanup.
These sum900s; transport startup deadlines are NOT shortened. If the acceptance
budget cannot cover renewal, return PARTIAL/budget exhausted, never extend/rearm or
declare a product timeout from this host cutoff. Host crash has bounded TTL fallback,
not a guarantee of instantaneous cleanup.

Pure host protocol9 tests (including6 abort subcases), unchanged event-gate10 and
actual diagnostic-to-protocol/renewal adapter3 tests PASS:22 total. Current binary
Go field layout and ELF Mux symbols rebound locally; remote BPF dry-run PASS.
Initial local `go tool nm` was unavailable; recovered using system `nm` on the exact
candidate, without replaying staging/deployment. Live adapter wired locally using
the existing reader/probe/correlation code. Live execution remains NOT_RUN.
Accepted probe/observer/control helpers installed; no owner APK installation.
Actual collectors start/TLS endpoint validation happen after fresh ACK before arm,
so their finite collection window is not spent waiting for the operator.

## Exact owner/cache preparation

- Fresh installed research84/code84, package `com.familyconnect.app.friends`, UID10283,
  non-debuggable arm64. Pulled APK SHA256
  `fd3106170ceeb1e24dad6c8eacda4107b1ab09a6ee120ccf495d92d96841aa48`;
  signer `67a90d1bfcd5a2c0666f0cff1b0ac5e43aaa661ca1196f89e879aa39fe20848a`.
  Main APK not rebuilt/reinstalled. Native bytes remain the accepted research84 reuse.
- Existing ChatDeliveryService background challenge/fetch/import/ACK at17:10:24–26UTC
  reused. Agent preparation refresh0; prior ordinary background fetches are not
  rewritten as zero. ACK revision3/minimumCRL23266/expiry20:52:44 match the signed
  cached response. ACK lacks a directory digest: correlation uses stable publication,
  signed metadata and the exact committed-reader result, not an invented digest.
- One accepted84 offline instrumentation around17:10:40: production vault only in
  memory, selector `RestrictedBootstrap.cached → RestrictedCache.usable(now)`, full
  identity-bound and installed native validation PASS/code0. No network/native startup,
  UID Tx/Rx deltas0; original cache/vault unchanged and temporary arrays zeroized.
- Directory selected and accepted by the running sole-seed invocation:
  `252c3535d2217e5cf5e2e14264625191e19d7b0dd95625c595426e92ca9e4341`.
  No previous invocation overlap. Directory v1 has no independent signature; trust
  comes from the existing authenticated signed-delivery/cache contract.
- Committed encrypted cache3301bytes SHA256
  `f69338248ef8f422127c06207f3ced3bca6869d04e7403de1fc03abe0d4faab6`.
  Selected canonical response SHA256
  `ea0467c2d8bc356e01d02d8d524bdbb58c182864856cb61c7fe839def757c84b`
  equals the original response after the production canonical transformation, not
  encrypted-file bytes. Selection context is availability-failure cached fallback,
  not a claim that ordinary unblocked CONNECT skips authenticated refresh.
- Exact-selection helper removed. Main target remains stopped intentionally:
  VPN OFF/app OFF/ChatDeliveryService OFF, freshly checked17:26:24UTC. No launcher
  start; restoration to app/chat ON belongs to final episode cleanup.
- Deterministic probe ping and unique nonce arm completed without network requests.
  No global IPv6 at the17:19 check: IPv6 UNAVAILABLE, not PASS.
- Underlay Telemost API HEAD (404 with strict TLS verification0) and independent
  ordinary HTTPS control (200/TLS0) pass. Initial new control at RU port443 failed
  TLS verification (`curl60`); retained as a harness control-selection failure,
  not hidden or bypassed. Accepted controlled egress endpoint29443/29445 must still
  pass its own strict live TLS preflight before gate arm. These controls are not
  full-tunnel egress proof and create no Telemost room/session.

## Pending / safety state

`READY_FOR_OPERATOR=YES`; `READY_FOR_LIVE` still requires fresh ACK, read-only
gateway/owner recheck, actual collector attach/endpoint preflight and signed gate
ARMED/recheck. Gate is NOT armed while waiting. Do not show a CONNECT instruction.
Current-task physical CONNECT0, manual reconnect0, owner native/TUN actions0,
agent owner refresh0, owner APK installs0, exact-selection instrumentation1,
gate arms0, full-phase requests0, lease renewals NOT_RUN, controlled gateway
restarts1, same-key renewal1, natural fatal exits0 at the final snapshot.
One ordinary shared seed created by the controlled gateway start; no synthetic
or owner Telemost sessions initiated. Existing background work is accounted separately.
Previous late physical CONNECT remains consumed in its historical task only.

`preparation-manifest.json`, `SHA256SUMS-preparation`, `cache-preparation-correlation.json`,
`gateway-prelive-stability.json`, `all-adapter-tests.log` and the original immutable
receipts retain provenance. Observation binary and rollback remain installed.
Temporary collectors are prepared but not running; signed helpers remain installed
idle for the authorized continuation. Cleanup after the episode remains required.

Do not publish or send APK. Cold start remainsNO; real restricted FIELD/public
release NOT_RUN. **One next operation:** fresh explicit «ГОТОВ» after PREPARATION
COMPLETE, then guarded `after_ack.py EXPLICIT_USER_GOTOV` sequence. Any invocation
change aborts before arm/CONNECT; do not restart/rearm or consume another attempt.
The script does not inject input. Display the manual CONNECT text only after
`manual-listener-ready.json` and `MANUAL_CONNECT_WINDOW_OPEN_45_SECONDS` appear.
After evidence it closes the window and performs gate/collector cleanup; accepted
cache-byte closeout and app/chat restoration still require their explicit final checks.
