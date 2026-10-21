# QUIC over the existing media carrier — isolated lab ADR

Status: laboratory implementation and bounded comparison completed; no repeatable
clean speed or product admission. Results and final disposition are recorded in
the mesh-capacity report and `2026-10-21-quic-carrier.evidence.json`.

## Decision

Compare the improved laboratory A (L carrier, effective RS32/32, Family TLS,
Mux128, packing OFF, Q0) against QN: reliable independent QUIC streams within one
connection, carried as whole messages by the unchanged legacy L/VP8 path. QS is
a diagnostic Mux128 over one QUIC stream, without another Family TLS layer.
No ReliableStream, TCP, ordered adapter, fragment ARQ or direct-UDP fallback sits
under QN. Pion WebRTC/NACK and VP8 assembly remain below it.

Pin quic-go v0.54.1 (MIT, module requires Go1.23; local toolchain Go1.26.1) in an
isolated copy. Production module files are untouched. The implementation retains
its default **Reno** controller and internal pacer, not a custom algorithm.
InitialPacketSize1200, disabled virtual-path PMTU probing, QUICv1, no DATAGRAM
extension, no unidirectional streams and no0-RTT. Each phase has one connection.

The PacketConn uses synthetic198.18.0.1/2:4443 addresses only as session-local
routing labels. WriteTo preserves one complete datagram and waits for existing
localwrite completion of the carrier's actual media write, not merely enqueue.
ReadFrom exposes only complete carrier messages; oversize/truncated data is not
successful receive. One serialized write,5s maximum local write, dynamic deadlines,
close cancellation; no adapter retries/reordering. quic-go's existing send queue
has8 entries. Carrier queues remain finite; no fake ECN/GSO/UDP-buffer interfaces.

Both ends use fixed128KiB per-stream and512KiB connection receive windows,
24 incoming bidirectional streams. These are explicit resource limits, not an
extra Mux128 imposed on QN. QS retains its own Mux credit in addition to QUIC flow
control and changes TLS integration relative to A; A→QS is not a pure recovery
algorithm comparison.

Ephemeral one-hour Ed25519 test CA/certificates use standard Go crypto/x509 and
TLS1.3. Both roots and peer DNS roles are verified, ALPN is
`family-connect-quic-lab-v1`; no InsecureSkipVerify, key log, production identity
or anonymous data service. Client session cache is nil and Allow0RTT=false.
SessionTicketsDisabled triggered a local quic-go/Go ticket-event assertion;
ordinary tickets with no client cache work. That initial failure is retained,
not hidden or patched inside the library.

## Cadence and acceptance

Keep L framing,33ms nominal RTP timestamp progression and keepalive policy common.
First test the original2ms/frame policy. The single permitted normalized policy
is a common1,048,576B/s conservative RTP/RTCP service budget with at most2ms earned
burst credit and no additional frame sleep. Repair/FEC is absent. This is not the
previous FIXED4M controller. Count actual packet sizes and media write delay.

Reuse existing deterministic bodies, single/parallel and small-response workload.
QN receiver checks full body/SHA256 and sends an explicit40B receipt on its stream;
the sender verifies it before the two-end controller barrier. Write/FIN/connection
close alone is never success. A retains the terminal-reset LabDrain guard. QS has
both-end closed-stream/byte conservation checks. Preserve every attempt, including
preflight failures and post-delivery closure warnings. No sparse-sample p99.

Live limits64MiB synthetic source /128MiB total outgoing media,180s transfer;
32MiB bulk reserved for A/QN/QN/A. Local tests are accounted separately, never as
fictional Telemost traffic. Production readback is observational only; a changed
epoch requires a fresh explicit manifest, not restoration of the previous hash.

The main-series v2 adds a common bounded start gate after both media endpoints
connect, before RS/QUIC startup. It does not extend transport/retry timeouts or
the180s application phase. This addresses a measured harness startup race, not
a throughput optimization: the earlier A1R server's20s RS timeout elapsed during
the client's21.153s media setup. A separate operator correction waits for complete
JSONL records instead of parsing an in-progress final line. Both failed phases
and the pre-correction source/binary remain in the all-attempts record.
Full remote log transfer must not lie on the completion critical path. QN1
delivered all bodies and receipts, then timed out while the controller retrieved
14MiB of logs. Select only the complete bounded proof before the finish barrier,
and download full evidence after closure. Preserve this as post-delivery failure,
not a failed download; do not increase QUIC idle timeouts to mask the controller.

## Not implemented or admitted

Product device/gateway identity, Family/role binding, claim/certificate protocol,
revocations, floors, leases, production resource/admission policy and safe legacy
compatibility require independent design and testing. No production session API,
Android change, rollout, deployment, hosting, push or user migration is authorized.
S/FCF2 and SF/8+2 remain closed; no size/FEC/window/controller sweep belongs here.

## Outcome

Eleven live sessions, six clean, seven complete application/remote-receipt proofs.
QN1 delivered single4MiB at0.469Mbit/s and parallel2×2MiB at0.524Mbit/s, then failed
late completion while the controller fetched logs. QN2 lost its media publisher
before bulk. Clean final A2 achieved1.080/1.813Mbit/s. Different SFUs and failed
main phases prevent repeated clean performance acceptance; sparse lower observed
QN small-response latency is separate. Default Reno responds to real carrier
delay/loss; local write/queue time, CPU and flow-blocked counters do not establish
an adapter ceiling, CPU bottleneck or need for larger windows. The inherited RTP
timebase and shared lower assembly remain limitations, not eliminated by QUIC.

Close this bounded profile with code and negative/inconclusive evidence preserved.
No extra QN rerun, automatic optimization or product migration. All test processes,
collectors, credentials and stages are removed; production current epoch is stable.
