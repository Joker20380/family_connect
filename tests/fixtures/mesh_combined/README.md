# L02.2 disposable Linux authenticated handoff gate

Not a product build, installed acceptance, live Telemost test or LXMF/node delivery.
Requires Docker with privileged disposable containers (TUN, NET_ADMIN, nftables).
Never run `run.sh` on the host or mount host `/run`, D-Bus, resolver files or Docker
socket into this container. `check.sh` supplies `--network none`, distinct netns,
private mount/PID environment, private D-Bus and an actual systemd-resolved process.
It compares host default/underlay routes, rules and resolver configuration
before/after (unrelated Docker veth churn is excluded) and removes only its
own named container on exit. Image build context contains only four lockfiles and
the Dockerfile; no state or private source capsule is sent to the builder.

From the repository root, with the pinned public Xray checkout available:

```sh
python tests/fixtures/mesh_lifetime/build.py --go /path/to/go --xray /path/to/xray --out /tmp/l022-worker
bash tests/fixtures/mesh_combined/check.sh /tmp/l022-worker
```

The native fixture is always built with Go race instrumentation. The container
test budget is 240s; its outer runtime is 270s. No production binaries are installed.
The existing 15 authenticated regressions remain a separate CI step.

## Real boundaries

- UID1000 child → real ServiceHost/Host Unix IPC; real ServiceOwner, manual
  Supervisor and Auto Coordinator/Guard/Platform/MeshCandidate, PacketSession.
- Native material verification, atomic generation-pinned operation leases,
  restrictedowner, worker IPC, owned TUN/Xray packet engine, native UDP DNS Probe.
- Kernel routes/rules and genuine private resolver application/readback; health,
  CONNECTED and VPN publication are never assigned or mocked.
- FamilyTLS authentication, lifecycle Mux, real room broker Challenge/Create/Claim,
  signed BindClient/bindGateway and MaintainLease renewal. Renewal sequence and
  zero Mux socket/stream/retained-byte cleanup are observed, not synthesized.
- Real ChatAccess challenge/register, fixed HTTPS origin (ephemeral fixture cert),
  and duplex fixed-mailbox byte relay. SERVICE_ONLY → EXISTING_EXIT → SERVICE_ONLY
  each uses one intended transport; three sequential opens, no overlapping owner.

## Replaced external dependencies

The existing test-only Go overlay replaces Telemost rendezvous/media with paired
bounded in-memory PacketEndpoints. The room provider supplies a synthetic room;
broker outer HTTP/authorization transport is replaced by local method calls using
the cryptographically validated fixture identity. Binding signatures, gateway
SessionAuthorizer/CRL checks and lease protocol remain real. Readiness fetch uses
a prefilled private fixture cache issued by the real synthetic authority; Auto's
normal DIRECT fetch actually fails in the isolated underlay (not stubbed).

TCP DNS upstream is a local NXDOMAIN responder. Native owned-TUN health packets
still traverse the packet engine, Family Mux and that upstream. Fixed API HTTPS
and mailbox TCP backing listeners are local. No arbitrary destination proxy,
production endpoint option or product trust-root change is introduced. Test-only
`SSL_CERT_FILE` is confined to the fixture worker environment. User identities,
profiles, CRLs and databases exist only in disposable temporary directories.

## Negative and resource gates

Both owner paths hold real cleanup, reject simultaneous chat demands before send,
fence a barrier-delayed old acquire result, reject a different **valid verified**
profile under the same issuer/device, and cancel a borrowed mailbox on VPN stop.
Manual's final SERVICE_ONLY checks real signed CRL revocation; Auto's final
SERVICE_ONLY checks actual signed grant/readiness/certificate expiry. HTTP403 stays
typed DENIED with exactly one send. Kernel resources return to the pre-VPN snapshot.

The separate release regression occupies all four real ChatLane CONTROL slots,
holds their replies, then releases a completed authenticated operation. Release
must reach native accounting after capacity returns, leaving exactly the same
generation lease and transport. Its timeout/closed-lane cases are bounded unit
tests; unconfirmed drain still retains the admission marker.

See [L02.2 evidence](../../../docs/releases/2026-10-24-linux-chat-mesh-l02-2.md).
