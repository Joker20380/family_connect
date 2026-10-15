# GATEWAY-SEED-SUPERVISOR-1 — source-only design

## Exact baseline and preservation boundary

Authority is the saved loaded/next snapshot in formal-acceptance-2, linked to
workability-proof build.json and its exact binary (21f0a0fd…509a). It is **not**
a4087e alone: that commit plus the sealed SIGNAL_READ classifier diff forms the
deployed observation source. `receipts/entry.json` records hashes for all226 Go files,
the build/source/diff identities and20,355 verified earlier checksum entries.
No fresh runtime values are asserted; no SSH/ADB was used.

Only the gateway Go module is included. The independently deployed Python API is
not copied, built, replaced or distributed. Its exact AKI/skew/ACK/publisher inventory
is preserved as API_FEATURE_INVENTORY_REFERENCE.md. This deliberately avoids the
previous stale-API rollback. The accepted, not-yet-deployed structured collectors
remain a separate patch stack; their lease/provisioning files are not replaced here.

The preceding live-provider capability proof is evidence, not implementation source.
Test adapters, local SFU, injected close codes and synthetic profiles are excluded
from `source/` and the normal gateway build. `validation/` is a separately hashed
test overlay and is not deployable.

## Current fatal flow and ownership

`cmd/bootstrap-broker/main.go:runObserved` owns the SERVICE signal/duration context,
HTTP listener and Broker; its deferred Broker.Close tears down dedicated holders.
SeedManager.Run creates one provider Room, connects TelemostSeed, publishes Directory
once, and calls serveCarrier. Optional runOverlap is the already-existing scheduled
room rotation (at most current+previous), not a new recovery scheduler.

TelemostSeed -> telemost.New/Session.Connect -> Auth.FetchConnection for the existing
JoinURL -> setupPeerConnections/setupTransport/dialWebSocket -> signalingLoop,
writerLoop, heartbeatLoop and RTP pumps. Gorilla ReadJSON errors are classified and
retained by retainSignalingReadFailure before signalClosedAt. Recv returns the
failure; serveCarrier observes SEED_READ and quiesces its seed/exchange subtree.
Before this patch Run returns seed_closed; main returns, cancels SERVICE, closes
Broker, exits1. Systemd's unchanged policy then creates a new invocation/room/D.

Dedicated holders already belong to independent bounded broker/session lifetimes.
They are not reparented or modified. A recovered seed error no longer leaves Run,
so the global Close is not reached. Fatal security/protocol/exhaustion still reaches
the existing global teardown. SERVICE cancellation still closes every subtree.

## State machine and narrow policy

SEED_STARTING -> SEED_ACTIVE -> SEED_RECOVERING -> SEED_ACTIVE or SEED_TERMINAL.
Only SEED_READ, SIGNAL_READ, WS_CLOSE1011, ACTIVE context, no requested local close
and no parent error enter recovery. UNKNOWN,1002/1007/1008, JSON/protocol, auth,
configuration, expiry and other network errors do not gain retry permission.
An in-connect1011 is retryable only with the same preserved production classifier.

Remote close1011 is a proven boundary, not a proven provider internal cause. The
live proof used a real upstream disconnect with an injected classifier code;
earlier natural1011 and older UNKNOWN receipts keep their original attribution.

Budget: at most **three rejoin attempts per logical room lifetime**, across successful
episodes too. This is stricter than a reset-on-success retry series and bounds
flapping. Total per-episode recovery deadline is the existing bootstrap ConnectTimeout
(45s), clipped by directory/SERVICE and current security expiry. Backoffs1/2/4s derive
from the existing seed admission one-second open retry cadence; no new jitter
framework. Maximum backoff total7s leaves38s of the existing connect budget. Each
join uses only the remaining budget, not a newly extended45s timeout. A slow first
attempt may consume the whole budget. No new room creation is permitted.

`seedRecoverySecurity` rereads the current bounded private profile, uses the existing
Family Configuration/VerifyConnection rules to validate the local gateway certificate
as a peer, strict x509 chain, role/binding, CRL/floors and returned limiting expiry.
It runs before recovery, after backoff, and before promotion; join contexts are
clipped to security expiry. It does not change issuance, skew, trust or lease policy.
No new always-on file watcher is claimed. Security changes are rechecked at those
boundaries; new bootstrap auth continues using the existing fresh profile validation.

## Generation isolation and readiness

Each generation owns a new context/Session/WS/Pion/ICE/pumps/endpoint, cancel and
cleanup-once. Session callbacks are bound to that Session object; they never look up
or mutate the manager's new Session. The sole shared pointer uses compare-and-swap
under manager.mu. Failed-attempt generation IDs are never reused. No lock covers
metadata, WS, SDP, ICE, media wait, exchange draining or receipt I/O.

Existing serveCarrier already closes a failed transport before returning and drains
its transient bootstrap exchanges. That transport quiescence is retained to prevent
parallel publishers. **It is not postponed until swap.** The logical failed-generation
pointer stays current/inactive until the fresh endpoint is ready; compare/swap and
final logical retirement cannot affect its successor. Keeping a broken publisher
alive until promotion would contradict the no-duplicate-owner requirement.

TelemostSeed performs actual production Connect, which waits for connected subscriber
and publisher Pion states; there is no fake READY. Readiness receipts include measured
PC states and media counters. Zero RTP RX at promotion is not rewritten as proof of
payload delivery; real old-cache authenticated bootstrap/RTP after promotion supplies
that evidence. RTP sequence numbers are not reused as generation identity.

Stable Room value and Directory object/serialized bytes remain unchanged. Ephemeral
join metadata, WS and PeerConnections change. No Publish/CreateRoom runs on recovery.
While unavailable, independent clients keep the original bounded admission retry/
unavailable contract; no partially initialized endpoint is exposed. Planned directory
rotation and expiry are still the original contract, not perpetual old-cache support.

## Observability and wire scope

The existing fatal observer receives only terminal first causes; a recovered episode
does not poison a later controlled stop. Every episode's original safe source/class
is copied immutably into recovery events; cleanup never replaces it. New-flow explicit
SERVICE cancellation returns normally; expiry/security/exhaustion remain terminal.

Events enter a nonblocking32-slot process-local queue. One writer uses a separate
`FC_FATAL_RECEIPT_DIR/seed-recovery` subdirectory (0700), atomic non-overwriting files
(0600), max4KiB/file and64 owned receipt files. No I/O under broker/session locks;
write failures do not affect protocol. Missing/dropped/unwritten receipts are not
proof of absence. No journal query or new endpoint is introduced. No raw errors,
room URLs, SDP, addresses, identities, headers, tokens or payloads are serialized.

Directory/bootstrap/Family/lease/API/publisher wire formats unchanged. No client APK
or mandatory field. Recovery policy is deliberately behavioral; it is not labeled
an observability-only change. Separate stack diffs are supplied.

## Test model limits

Real-media acceptance uses the sealed local TLS/WSS SFU with Gorilla, real Pion,
SDP/ICE/RTP/VP8, production bootstrap/Family/Reliable/Mux and a real persistent TCP
echo socket. It now drives SeedManager's production supervisor, not manual rejoin.
Lease clock alone is controlled to cross the policy boundary without ten wall minutes.
Security/directory expiry tests use bounded real contexts. Selected matrix ICE/media
timeouts use a declared500ms test connector limit, not a production timeout change.
This task creates no live Telemost rooms and proves no real restricted network behavior.
