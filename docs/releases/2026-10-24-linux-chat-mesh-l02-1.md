# L02.1 — bounded service-only generation lifetime, 24.10.2026

## Result / scope

**Lifetime correction verified; combined native/process acceptance PARTIAL.**
**L02 remains PARTIAL. NEXT — review L02.1. Stop before review; no L03.**
Entry: clean current `main` and verified remote
`9b7418e2675d1e30787f491f8c924467835e7b05`; no reset or removal of other work.
The previous [L02 evidence](2026-10-24-linux-chat-mesh-l02.md) remains historical,
including its exact CI failures. L01/L01-R, D03/D04/D05 remain accepted; D01 is open,
D02.1-R remains PARTIAL/NOT_RUN. No acceptance is inferred from an unchanged PID.

## Before / after and ownership

- Before: ServiceOwner retains Binding/worker but no native generation reference.
  Last operation release drops actual native refs to zero, cancels the session and
  starts cleanup. A subsequent register cannot acquire that closing generation.
- A real native-owner test uses TLS API success, an explicit cleanup-entry barrier,
  a separate cleanup-release barrier, native state and transport-open count. It
  reproduces the operation-only failure and verifies a retained generation lease
  preserves the same transport. Coordinator behavior is **not changed**.
- Root/process red run loads the exact old Python ServiceOwner from entry SHA into
  the new isolated fixture. First authenticated challenge is 200; native leases=0,
  transport opens=1, cleanup is held; the next **register fails UNAVAILABLE**.
  The same test with the new host succeeds through challenge/register and duplex
  fixed mailbox with native lease transitions 1→2→1 and exactly one opening.
- An additional actual native IPC regression found a typed-nil `*Client` converted
  to the client interface on Acquire denial: the error path attempted Close on it,
  stalling IPC (before: read timeout/leaked server). The wrapper now returns a nil
  interface on error. After: repeated DENIED replies, IPC and owner remain usable.
  The isolated lifetime red run uses that corrected IPC to separate both defects.
- New ownership: **one ServiceOwner generation lease + separate Host operation
  leases**. Acquisition uses the existing native API and verified readiness/profile;
  completion of request/challenge/mailbox-open releases only its operation lease.
  Existing MaxLeases=8, native jobs/streams, HTTP budgets and 45-second idle remain.
- Teardown fences new operations, signals generation cancellation, closes Binding,
  releases the generation reference and closes the chat lane (cancels/releases
  outstanding operations). The worker stop protocol waits for native owner drain,
  sessions/streams and underlay cleanup before successful exit. Only then does
  Ownership.finish clear the marker/release flock. No coordinator/flock relaxation.
  Watcher expiry is now proactive, including without another request. Replacement
  uses the same fenced cleanup path; no current generation is silently overwritten.
- Explicit cleanup timeout remains sticky: worker termination is **not** cleanup
  confirmation; gate/marker survive, no replacement can enter. The authenticated
  negative gate verifies this, separately from successful cleanup cases.

## Evidence levels and fixture boundary

The [fixture runbook](../../tests/fixtures/mesh_lifetime/README.md) records exact
build/run instructions, substituted components and inspected public candidates.
`local_process_test.go` provides two-process Pion but no Linux/FamilyTLS owner;
`messenger_local_test.go` provides local Pion/FamilyTLS/Mux and a TCP proxy;
`session_test.go` provides authenticated endpoint pairs;
`lease_mux_test.go` supplies broker lease/clock tests. They are reusable components,
not a pre-existing Linux acceptance harness.

The disposable race-built overlay replaces external bootstrap/Telemost carrier
and broker bind/renewal with bounded packet channels and loopback fixed-service
peers. Pre-issued readiness uses normal native cache cooldown validation/readback
instead of external fetch. FamilyTLS, issued certificate/delegation/CRL validation,
ReliableStream/Mux, restricted native owner, AF_UNIX/stdio IPC, Linux ServiceOwner,
real isolated Underlying and inherited root flock remain real. TLS API trust is
ephemeral and confined to the fixture subprocess; product CLI/ENV/roots unchanged.
ChatAccess validates actual challenge/device/chat signatures and API revocation.
Mailbox evidence is bidirectional fixed-service **bytes**, not LXMF/node admission.

| Layer | Outcome / limit |
|---|---|
| Python/native/D03/Auto/DIRECT targeted | **556 PASS**, locked Python3.13.15 image; no full local suite claim |
| Linux owner/mailbox | **24 PASS**, identity/history/provenance regressions retained |
| Native owner | Go/race restrictedchat, restrictedowner, desktopmesh, wholedevice, underlay, desktopauto **PASS**; exact-profile borrowing, invalid/revoked/expired materials and late-open drain are lower-layer evidence |
| Native bridge | Eight package race suites **PASS**, including new actual Owner denial regression; sealed production build succeeds |
| Root→UID/process | **13 PASS** (6 L01-R + 7 cross-process admission); unchanged idle-worker portion is not authenticated VPN evidence |
| Authenticated service-only | **7 PASS**: shutdown/cancel/idle/host-expiry/preemption, demand re-entry, unconfirmed cleanup and active-mailbox cancellation. Native expiry/revoked-CRL/profile-negative checks are separate; host-expiry is explicitly advanced in the fixture |
| Kernel | Auto policy (18 checks), traffic guard (44 checks) and DIRECT **PASS**; real UID packets/TUN/nftables and synthetic TLS fatal-alert gate; isolated only, never host-network modification |
| Reference | **PASS**, 175 shared files; Android106/native105 and Xray pins unchanged |

Local evidence is preserved under `/tmp/fc-l021/evidence`; raw disposable credentials,
logs, fixture binary, build outputs and state are not committed. Earlier setup errors
are retained: non-root image caused SKIP; missing cache directory/refresh timeout
were fixture setup failures; missing image nft and container AppArmor prevented
initial kernel attempts; Docker read-only `/proc/sys` required a disposable privileged
container for the existing per-netns DIRECT rp_filter fixture. None of the failed
attempts is counted as PASS. Final DIRECT reports `host_network_changed=false`.

## Exact remaining combined gate

**NOT_RUN:** successful Linux VPN Supervisor/PacketSession publication, API/mailbox
EXISTING_EXIT with the same verified profile, then VPN OFF and resumed service-only
through those real owners; simultaneous VPN/chat plus late result/profile mismatch
in that **combined authenticated chain**. Separate native-negative and flock tests
do not close it. Root VPN admission in the fixture is only admission, not a published
VPN. DIRECT unavailability is a missing DIRECT endpoint here, not live outage proof.

The concrete fixture/interface gap is the local peer's **chat-only Mux policy**:
no generic packet/DNS service for real Linux platform.Attach/owned-TUN Probe and
native health checks, and no room-broker lease lifecycle. It cannot make the actual
VPN CONNECTED/publication path pass honestly. Next fixture work would implement
that peer interface and drive the existing Linux owners without stubbing Attach,
Probe, publication or trust checks. Lack of that implementation does **not** establish
a requirement for production/live Telemost or any private source capsule.

## Build, source receipt and rollout

Local production worker: Go1.26.1, source manifest
`801b637325a334fc69467f1af5b4e73cf186764a28c8a84884c50fe44c9e1540`, binary SHA256
`0c177e578d50418376734f574042b62ad1a4bf02523c90896c184ea0b8493f37`.
Xray revision `d2758a023cd7f4174a5a5fa4ff66e487d4342ba0`, patch SHA256
`eaeb30fd1e2aa52272d7f3a2a06bcad7b983ca9866a87fbd0a614eede6048872` unchanged.
Source/remote and exact CI receipts are appended after the ordinary source push;
until then no CI result is claimed for this checkpoint. Mandatory full suites,
root→UID and existing Auto/DIRECT CI gates are retained; the isolated fixture gate
is additive, never a replacement or skip for failures.

Versions unchanged: public Linux0.2.11, Windows0.2.15, accepted Android106/native105;
no installer/catalog/invitation-page changes, installation, deployment, live,
publication, fleet, Windows or iOS work. Runtime rollback is unnecessary. Source
rollback is an ordinary revert with a new commit, not reset/force-push. Preserve
private identity/history/settings, state and existing admission markers.
