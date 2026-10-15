# TELEMOST-REAL-SAME-ROOM-REJOIN-1 — PASS

## Verdict

**SAME_ROOM_REJOIN_CAPABILITY = PROVEN_LIVE_PROVIDER**, for the measured isolated
provider connection-disconnect episode. Real Telemost retained the logical seed
room, accepted a fresh complete signaling/Pion/media join, and served a new
authenticated bootstrap using the original serialized directory. The existing
dedicated Family/Reliable/Mux/TCP stream stayed open and transferred numbered data.

**PROVIDER_GENERATED_WS1011 = NOT_PROVEN.** The driver really closed the upstream
WebSocket, then injected Gorilla CloseError1011 at the tagged read/classifier adapter.
This was not merely errors.New without disconnection, but neither was it a naturally
provider-generated1011. Provider internal-error cause remains UNKNOWN; earlier
historical UNKNOWN exits are not reattributed. This result establishes capability
after connection loss, not a guarantee that every natural1011 leaves a reusable room.

No production supervisor/behavioural patch was created. Production gateway/API,
owner phone, production directory and credentials were not modified. Historical
functional warm-start PASS is preserved; formal warm-start readiness is not raised.

## Exact inputs and isolation

Capsule: `state-client-build/field65-export16/telemost-real-same-room-rejoin-1/`.

| Identity | Exact value |
|---|---|
| Baseline source | `a4087e000fdbe674b72ede3a6c8822445c87c654` |
| Baseline classifier diff SHA256 | `7e7d408670a6ac6afa18e856beb8dcc0ca26a3b6f074e205d4dd25e62d78967b` |
| Previous local-proof capsule SHA256SUMS | `2b69feea345e5a731981554817eac429cb7f8dd05b8a8a2ddd5e3dcfa21b29a6` |
| New Go source-manifest SHA256 | `c488eab42c810fcd04702f5c354af63b3c5ea85e4211b1250a2af1bfc4bf747a` |
| Experimental diff SHA256 | `f5167c318a517cf577a3b59e19313d288d5b35a0ce7923789aeedc9c83b5e9a5` |
| Test executable SHA256 | `da4255d5cee0349daacabb3c49e8734ca09cd340ede5761898459df97776dccc` |
| Test run ID | `2d8700c99d79b7456f4ec09b` |
| Isolated test PID | `1598577`, terminated and absence verified |

4059 input checksum entries verified before copying and again at finalization. Exact
source copied into a new private workspace; main dirty product worktree and old
receipts preserved. Build: pinned Go1.26.1, Gorilla1.5.3, Pion4.2.15, test tag
`sameroomfixture`. No module/dependency changes, commit, release or push. This is
a test binary, not a deployable service candidate.

Live topology: one private NL Linux process tree, with logical seed gateway,
pre-failure synthetic client/dedicated session and post-rejoin synthetic client.
All joins use actual Telemost API/WSS/SFU, original STUN, system TLS roots, real SDP,
ICE, Pion PCs and RTP/VP8. Local Linux orchestrates over SSH; it is not a second
independently routed media endpoint. No local SFU/packet-pair exists in the live run.

Fresh disposable ProductStore-issued Family identities/profiles, independent root,
gateway and devices were used solely for this test. No production Family profile,
device identity/cache, publisher key, signing key or room URL was read. Existing
authorized project provider OAuth remained NL-only in the private child environment;
it was not exported to the local machine, argv or receipts. No unit was created.

## Preflight and bounded episode

- Provider config root-owned0600, readable only on NL. Local environment had no token.
- NL `timedatectl` confirmed NTP synchronized. The earlier absence of the timesyncd
  marker was not treated as proof that system time was unsynchronized.
- HTTPS to official conference API succeeded at transport level; unscoped collection
  GET returned405. This does **not** establish OAuth scope/quota. Actual single seed
  CreateRoom and subsequent joins established those operations worked in the episode.
- API quota is not separately exposed by this preflight; no probe room was created.
- Effective synthetic credential headroom before create:3335.5sec. No renewal.
- Parent budget8min, Go hard timeout9min, outer supervisor560sec. One episode marker,
  maximum3 CreateRoom calls, one actual disconnect and one same-room rejoin, no retries.
- Requested directory TTL20min is capped by the parent context: actual D expires
  `2026-10-12T22:01:17.665069713Z`. No validity extension or regeneration occurred.

## UTC chronology

All live event timestamps below come from the same NL process; no comparison of
unrelated monotonic clocks. Source: `receipts/live-result.json` and `chronology.json`.

| UTC | Event | Correlation |
|---|---|---|
| 21:53:17.665 | Isolated process/profile preflight | run ID above; synthetic fingerprints hashed |
| 21:53:18.062 | Seed CreateRoom accepted | seed create1; PUBLIC waiting-room setting |
| 21:53:19.859 | Initial subscriber/publisher PC and ICE connected | seed room hash below |
| 21:53:19.861 | D committed once |292bytes; SHA below |
| 21:53:30.218 | Baseline dedicated room created | dedicated create1 |
| 21:53:46.961 | Family/Mux baseline READY; original TCP stream open | stream1; initial lease recorded |
| 21:53:47.870 | Actual seed upstream WebSocket close requested |1 completed numbered frame; dedicated socket remains open |
| 21:53:47.875 | Seed returned SEED_READ/SIGNAL_READ/WS_CLOSE1011 | ACTIVE; carrier_closed=false; test-injected classification |
| 21:53:51.866 | Fresh same-room signaling/sub/pub/ICE connected | no new seed create;3 original-stream frames complete |
| 21:54:03.000 | Old D produced second authenticated bootstrap/descriptor | dedicated create2 |
| 21:54:16.772 | Post-rejoin dedicated READY and nonce echoed |28 original-stream frames complete; same stream/socket |
| 21:54:18.871 | Test cleanup completed |61.206sec total; process subsequently absent |

Seed room identity hash before/after:
`a60d7598905ba23b6715fa76675d7947d4a7503bec8606309b9754b9e53f2c19`.

Directory D SHA256 before/after:
`d9f24bda521cf50604b2eee2132dfa35ca60a37e37203403c6398e77d713a93b`.

D was read from the same private serialized file by ParseDirectory/Recover for both
clients. There was no server-object substitution, cache import or publication. The
existing protocol authenticates the directory through Family; it does not have a
standalone directory signature. No new signature claim or schema was invented.

## Media and dedicated continuity

The rejoin invokes a new production TelemostSeed/Session with the old Room, reacquires
ephemeral connection metadata, and performs new subscriber/publisher SDP/ICE. Both
new PCs and both ICE states are connected. Actual subsequent bootstrap traffic, not
metadata GET or ICE alone, proves seed data reception/transmission.

Recovered seed stats:8640bytes sent,8098received,38messages sent,29received;
51VP8 samples written,38RTP packets received,36frames and29binary frames received.
The second synthetic client used old D, authenticated through Family, received a new
descriptor and reached a new dedicated READY. Its54-byte application nonce completed
byte-exact echo; SHA256:
`8651bb2b8ffc2b87fc94cf37def122baa40481b2c377ea57f7f2fe5a1b5433e5`.
The explicit nonce is on the **post-rejoin dedicated carrier**; seed byte delivery
evidence is the successful authenticated bootstrap plus its real RTP/binary counters.

The original dedicated session retained its holder, Mux stream1 and TCP socket.
Numbered frames:1 before disconnect,2 during recovery,3 at rejoin readiness,28 by
completion. Each response compared byte-for-byte; no stream reset/reopen or sequence
gap was accepted. There were exactly2 server TCP accepts overall: one per dedicated
client, not an original-socket reconnect. Maximum measured frame response1794ms;
this is whole-frame latency, not proof of a1794ms carrier outage. RTP sequence gaps
were observed and are not misreported as application data gaps.

Initial real lease deadline was22:03:28.354286745Z. Test ended earlier:
**LEASE_RENEWAL_CONTINUITY = NOT_REACHED**, not PASS. No accelerated clock in live.

Old callbacks exercised after new ACTIVE: old ICE callback, writer operation,
subscriber/publisher close callbacks, cancel/Close, then delayed cleanup during the
second bootstrap. New endpoint, D and existing dedicated stream remained usable.
Old PCs are synchronously retired before the fresh join; no parallel seed owner or
duplicate seed publisher was intentionally created. This does not prove every remote
SFU stale-event ordering; local failure/generation matrix supplies additional coverage.

## Local validation, security and resource bounds

Before live, the exact driver ran through local real WSS/Pion SFU alongside the
previous full same-room proof and15-case failure matrix. Race×3: **54PASS,0FAIL,0SKIP**.
Initial sandbox listener denial was preserved, then tests were approved outside the
sandbox. No dependency download, OAuth or live room in these local runs.

Matrix retains bounded attempts, stop during backoff, repeated1011, missing/expired
room/join credentials, metadata failure, SDP/ICE/readiness failures, policy1008,
protocol1002 and malformed signaling. Local security-bound expiry is a context
boundary, not a new proof of actual X509 expiry during live SDP. No live negative
room experiments, second disconnect or retry episode were performed.

Family authentication, admission, revocation/floors, certificate validity and lease
policy functions are unchanged. No production AKI/publisher/API code changed.
The test fault adapter changes only this experiment's read-error classification;
the original service still treats seed failure as fatal unless the experimental
driver retains broker/service. A production resilience fix remains future work.

Cleanup inside process: FD6→11, goroutines2→4. Those are bounded snapshots, not zero
or a long-running leak guarantee. Whole test process subsequently exited; absence
was independently verified, so its listeners/WS/PC/ICE sockets are no longer owned
by a running process. Remote private workspace, profiles, temp D and raw log removed;
local synthetic database/profiles and private transfer tar removed. Sanitized receipts
and test-only source/binary retained.

Official conference API inspected documents create/read/update, not a conference
DELETE or object TTL. No guessed destructive API was called. All test participation
was closed; **provider conference-object deletion and object TTL are NOT_EXPOSED**.
No claim that participant exit deletes the provider's persistent conference object.
Raw room references were erased; D expires normally. No production cleanup/restart.

## Required classifications

| Field | Result |
|---|---|
| LIVE_TEST_TOPOLOGY | Isolated NL synthetic participants; actual Telemost API/WSS/SFU |
| SEED_ROOM_CREATE_COUNT |1; dedicated rooms counted separately2 |
| BASELINE_REAL_MEDIA / BASELINE_BOOTSTRAP | PASS |
| DIRECTORY_D_IDENTITY |292bytes, exact SHA above, unchanged |
| EXISTING_DEDICATED_SESSION | PASS; Family/Reliable/Mux/TCP |
| REAL_PROVIDER_SIGNALING_DISCONNECT | PASS; actual socket closed |
| CLIENT_OBSERVED_WS1011 | PASS at explicit test classifier adapter |
| PROVIDER_GENERATED_WS1011 | NOT_PROVEN |
| ROOM_SURVIVAL / SAME_ROOM_SIGNALING_REJOIN | PASS by same conference identity/full rejoin |
| SDP_ICE_RENEGOTIATION / PION_MEDIA_REJOIN | PASS |
| RTP_VP8_DATA_AFTER_REJOIN | PASS; actual authenticated bootstrap and post-join nonce |
| DIRECTORY_BYTES_UNCHANGED | PASS |
| CACHED_BOOTSTRAP_AFTER_REJOIN / POST_REJOIN_DEDICATED_READY | PASS |
| EXISTING_DEDICATED_CONTINUITY | PASS; same original socket/stream,28frames |
| GENERATION_ISOLATION | PASS in exercised live and local callbacks/cleanup |
| RESOURCE_BOUNDS | PASS for bounded episode/local matrix; not long-term guarantee |
| SECURITY_INVARIANTS | Existing validation unchanged; synthetic authenticated joins |
| SAME_ROOM_REJOIN_CAPABILITY | PROVEN_LIVE_PROVIDER in measured disconnect model |
| CLEANUP | PASS for test processes/participants/private state; object TTL not exposed |

Counters:
`PRODUCTION_GATEWAY_DEPLOYMENT=0; PRODUCTION_GATEWAY_RESTART=0;
PRODUCTION_RENEWAL=0; OWNER_INSTALL=0; OWNER_INSTRUMENTATION=0; OWNER_REFRESH=0;
OWNER_CONNECT=0; PROVISIONING_GATE_ARM=0; TEST_SEED_ROOM_CREATE=1;
TEST_DEDICATED_ROOM_CREATE=2; REAL_TELEMOST_TEST_EPISODE=1; TEST_SIGNALING_DISCONNECT=1`.

## Artifacts and next operation

Capsule includes `manifest.json`, `RESULT.json`, `experimental.diff`, exact baseline
and source, build/local race receipts, sanitized live chronology, media/cache/session
receipts, privacy and local/remote cleanup receipts, `DESIGN.md`, `scope.txt`,
`REPRODUCE.md`, test executable and `SHA256SUMS`. Secrets/raw SDP/room URLs are absent
from the exported live evidence. Source/build manifests pin the exact tested bytes.

**Exactly next operation:** minimal production seed-supervisor source patch and
controlled local acceptance, using this measured provider capability; **no deployment**.
Keep observability and behavioural deltas separate. Preserve generation-scoped
contexts, dedicated isolation, unchanged D, finite recovery, service-stop cancellation
and fail-closed security/expiry handling. Do not treat injected1011 as a universal
provider guarantee or turn UNKNOWN/protocol/auth failures into blind retries.

`PUBLIC_RELEASE=NOT_RUN; REAL_RESTRICTED_NETWORK_FIELD=NOT_RUN`.
