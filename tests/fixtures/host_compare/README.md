# Same transport / different host — bounded isolated comparison

This is a workload adapter for the existing `cmd/telemost-binary` Family TLS/Mux
live harness, not a product entry point, proxy, provisioning API or new transport.
It pins `state-client-build/rtp-pacing-20261020/candidate` and its sealed inventory.
No APK, production gateway, credentials, directory, API or transport setting changes.

## Implementation and scope

- One Linux/amd64 binary for local client, NL186.246.45.246 and RU185.251.89.19.
  RU city is not established; do not label it Saint Petersburg.
- Unchanged VP8/RTP/UDP4, Family TLS, ReliableStream, Mux64, A0, OFF/Q0;
  pinned dependency versions. No `WithCompletion` or pacer configured by the CLI.
- Only CLI workload/configuration plus numeric/candidate metadata projection changes.
  `host_compare.go` uses the existing Mux streams; it implements no multiplexing.
- Fixed SHA256(counter)-generated4MiB synthetic payload. All requested bytes are
  compared at the client and checksummed. Reverse control is checked by the fixture.
- Loopback-only fixture accepts at most8 connections, lengths64KiB/2MiB/4MiB,
  bounded150s operations. It cannot forward traffic. Existing authenticated Mux
  listener uses the existing exact test-loopback-port allowance, not a public port.
- Linux client has no Android/TUN, product readiness/bootstrap/admission, external
  destination HTTPS or mobile network. Results are not comparable speed acceptance
  against earlier phone measurements. Family admission uses disposable test CA only.

## Procedure and limits

`prepare.py` verifies all baseline source hashes, stages a separate capsule, applies
the workload adapter, runs affected CLI/fixture race tests, and builds the harness.
The initial sandbox socket denial is retained in `local-tests.log`; the successful
outside-sandbox repeat is `local-tests-host.log`. No dependency upgrade occurred.

`run.py` uses the existing `pilot.telemost_family_fixture` issuer/new temporary
ProductStore. The first minimal Python environment lacked pydantic; its failure
and zero-traffic preflight were preserved. The existing complete admission-fixture
environment is used instead; no production issuer/DB/private key is imported.
Provider OAuth remains on NL; only fresh disposable room descriptors and ephemeral
test peer credentials travel to the test processes. Links/keys never enter argv,
public receipts or source. Each phase creates a different non-production room.

Order A1(NL), B1(RU), B2(RU), A2(NL). Each phase uses the same local client/network:
64KiB bidirectional echo control, single4MiB download, two parallel2MiB downloads,
then64KiB upload with32-byte checksum acknowledgement. Echo is not pure download
or network RTT. Per-phase synthetic bytes across both directions including25 request
header bytes and32-byte acknowledgement: **8585273**; four phases **34341092**,
below64MiB. Deployment/SSH/log bytes are administrative overhead, not claimed as
useful throughput. A failed phase keeps its entire reservation, never zeroed/retried
to remove failures. No extra placements, rates or phases are automatically enabled.

Both server peers run as nobody in separate transient units:220MiB memory, no swap,
50% of one CPU,96 tasks,510s hard lifetime, low priority and no privilege escalation.
The same limits on different host CPU counts are recorded; throttling is a confounder,
not evidence of network capacity. Local and remote resource samples are bounded.
Production binary/PID/invocation/profile hashes and OFF/LEGACY64/export-OFF flags are
checked before/through/after every phase, without requesting a phone reconnect.

`summarize.py` is read-only/offline. It retains request-local monotonic timestamps,
failed requests, latest nominated ICE paths **before** peer closure, exact counter
scopes and whole-host versus process resource distinctions. Do not sum overlapping
Mux/RS waits or treat missing RTP counters as zero. No inter-machine clock subtraction.
Any observed protocol error stops subsequent phases; its unresolved category must
be reported, not silently erased because a body passed.

## Teardown and reuse

Finite workers terminate/reap only their owned CLI children. Transient units are
stopped, private remote stages removed, local room/profile inputs and temporary
test DB/identities deleted. Standard `Session.Close` closes WebSocket normally and
both PeerConnections. The existing provider abstraction has no conference-delete
method: participant departure is verified, provider metadata deletion is not claimed.

Never run this against an existing room, production identity or the excluded
186.246.51.201 host. Existing result paths intentionally refuse overwrite. The
capsule, patch, binary hash, build manifest, configurations and source scripts are
the reproducible kit; a future rerun needs a separately authorized fresh experiment
directory/session namespace, not reuse of expired fixture identities or old intents.
