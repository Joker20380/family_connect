# Server resource and cleanup contract

Product source is exact baseline plus only Reliable stream/protocol and Telemost
session changes. No policy/concurrency changes accompany the transport correction.

## Per carrier / stream

- Telemost recvQueue: 64 complete messages, each <=65536 bytes: at most4194304
  bytes of queued payload (previously1048576). Channel slots/slices, trace metadata
  and allocator overhead are additional. This is a capacity bound, not measured RSS.
- Reliable adds exactly one writer to the existing run and reader workers: three
  stream workers. There is no worker per frame. Pending jobs are bounded at34
  (MaxWindow32+2); outgoing is unbuffered and completion has one slot. ACK/OPEN
  coalesce by kind/target; DATA is not silently discarded. Exhaustion is observable
  ErrBackpressure, distinct from carrier RECEIVE_QUEUE_FULL.
- Pending DATA references normally alias engine send payloads, not copies of every
  frame. A conservative payload-reference ceiling for34 queued jobs plus one
  in-flight job is35*32768=1146880 bytes, separate from metadata and the send/receive
  windows. This must not be added as if every reference were a distinct allocation.
  Default engine windows8/16 with payload16384 give128KiB send +256KiB receive
  payload capacity; configurable maxima32/32 at32768 give1MiB each. Encoding one
  outgoing frame adds up to32832 bytes. Reader/incoming also retain bounded carrier
  messages; invalid frames are not assumed to have already passed Reliable decoding.
- Existing Telemost sendQueue256, reassembly pending16 / recent4096, RTP/Pion/TLS,
  socket, Mux and diagnostic buffers are unchanged and are NOT included in4MiB.
  Caller-owned blocked writes/objects and OS/network stacks are not a proven total
  process RSS bound. Dedicated MaxVideoTracks remains its baseline setting; no new
  global track/connection quota is inferred from this patch.

## Concurrent server objects

The actual bootstrap-broker entrypoint constructs one Broker with DefaultLimits
Outstanding32. Its map counts challenged/creating/ready/active and closing setups;
worker finish follows gateway.Close, including failed-start cleanup. One dedicated
Telemost carrier is constructed per started setup. This does not count seed carriers
or pre-authentication work and is not a universal process-wide quota.

SeedManager normally owns one seed carrier; the existing configured rotation path
may own two generations during overlap. serveCarrier has one active bootstrap lease
per seed and does not create a new Telemost carrier for each incoming OPEN. That
lease has its own incoming16 packet channel (packetLimit33000) and its Family/Reliable
exchange, bounded by the existing ExchangeTimeout. HTTP control/admission reads use
existing HTTP/TLS limits, not dedicated carrier queue slots.

For this single unchanged entrypoint topology,32 dedicated +2 overlapping seed
carriers illustrates136MiB maximum receive-queue payload if every queue is full
(previously34MiB; increase102MiB). It is NOT an all-process or fleet RSS guarantee:
pre-auth TLS/HTTP goroutines, retained closed references, media buffers and runtime
allocation are outside this arithmetic. Actual production occupancy/RSS was not
observed, and broker32 is never substituted for a cap on every reader or worker.

## Cleanup versus retained memory

The run loop cancels then joins writer; endpoint.Close and reader join follow.
Telemost.Close closes WebSocket/data/Pion resources, waits its workers, completes
cleanupDone and closes idle transport connections. Mixed fixtures verify adapter
active calls return to0, subsequent B is independent, and delayed A cleanup does not
close B. These are source/fixture checks, not production Pion/JNI lifecycle evidence.

A new test fills64 distinct maximum-sized messages and closes the carrier. It
observes cleanupDone but4194304 bytes still referenced by recvQueue while the test
retains Session. Close does not drain that channel; this was already true with16.
The test explicitly drains only its own fixture for accounting. Object reachability
and eventual GC, not a claim of zero post-Close queue memory, bound retention.
No new product draining policy is introduced. Resource allocation remains finite;
actual reclamation latency and peak live RSS remain unmeasured.

Supported finite8/16/19/20 and40 stress bursts must preserve operation. A separate
sustained blocked receiver is allowed to terminate observably; no result that closes
on a supported burst is converted to PASS merely because a guard fired.
