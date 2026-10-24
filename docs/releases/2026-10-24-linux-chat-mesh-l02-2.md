# L02.2 — local authenticated Linux MESH OFF→ON→OFF

Date: **2026-10-24**. Bounded source checkpoint, **review pending**.
**Parent L02 remains PARTIAL. STOP. NEXT — review L02.2.**

Entry: clean current `main`, remote verified at
`9d472e96b6854f26053ca8d797d2c73aad18b0ef`; no rollback to a review SHA.
L02.1-R2 review is accepted in its agreed scope. L01/L01-R, D03/D04/D05,
generation lifetime, atomic RetainChat, status classification and reference pins
are retained. D01 remains open; D02.1-R PARTIAL/NOT_RUN.

## Combined evidence and boundary

The [reproducible fixture](../../tests/fixtures/mesh_combined/README.md) extends
L02.1, not the shipped product. A disposable Docker system has its own netns,
mount/PID environment, private D-Bus and real systemd-resolved. Host routes and
resolver configuration are compared before/after; no host DNS/bus paths are mounted.
The host comparison covers default/underlay routes, rules and global/underlay DNS;
unrelated Docker veth churn is excluded. An initial all-interface comparison
detected other containers' veth disappearance despite all3 tests passing; the
combined namespace itself compares its complete route/rule/DNS snapshots.
The wrapper requires a distinct initially empty network and caps tests at 240s
(outer container 270s); it removes only its own container. Image build context is
only the Dockerfile and four lockfiles, not state/capsules/keys.

| Stage | Manual Supervisor | Auto Coordinator/Platform/MeshCandidate |
|---|---|---|
| VPN OFF | UID1000 → real ServiceHost → SERVICE_ONLY; authenticated challenge/register/duplex fixed-mailbox; generation lease1, opens1, no TUN | Same |
| Reservation/handoff | Real flock reservation fences chats; delayed old acquire and concurrent demand; cleanup held with old admission and no VPN worker | Same; actual native Auto policy/Guard and real failed normal DIRECT fetch |
| VPN ready | Old leases0/drain/worker exit before admission transfer; owned TUN, routes/private DNS readback, native health Probe, CONNECTED, publication | Same; actual nft guard ready and applied restricted session |
| VPN ON | Host → published native EXISTING_EXIT; exact validated profile; API/mailbox; opens2, operation leases return0 | Same |
| VPN OFF again | Borrowed active mailbox cancelled; held cleanup blocks chat; worker0, routes/rules/DNS restored, TUN/journal removed, admission released | Same, plus real guard removal |
| Renewed demand | New held generation, challenge/register/duplex fixed-mailbox; opens3, generation lease1 | Same |
| Terminal final generation | Signed CRL revocation through SessionAuthorizer/real lease renewal; active mailbox cancelled, leases0 and all three Muxes drained | Actual short signed grant/readiness/certificate expiry; same cleanup accounting |

Explicit barriers hold native cleanup and a successfully acquired old operation's
return. That late result is rejected after new VPN publication and cannot alter the
new Binding. Valid differently issued credentials for the same device/issuer are
rejected by native profile matching, while the published exact profile still works;
country is not an authority. HTTP403 remains **DENIED** to the UID child, exactly
one HTTP send, no replay. Neither same PID nor assigned flags are acceptance evidence.

**Real:** material verification and signed floors, native owner/refcounts/pins,
IPC, FamilyTLS, Mux, owned kernel TUN/packet conversion, DNS Probe, Linux network
readback/cleanup, manual/Auto lifecycle, publication and authenticated ChatAccess.
Broker Challenge/Create/Claim, signed BindClient/bindGateway, lifecycle-enabled
Mux and MaintainLease use the existing implementation; renewal sequence advances
and all peer socket/stream/retained-byte counters reach zero at teardown.

**Replaced external services:** Telemost rendezvous/media → paired bounded packet
endpoints; synthetic room provider and local broker outer calls instead of broker
HTTP, with fixture identity derived from validated credentials. Readiness fetch →
prefilled private cache issued by the real synthetic authority. DNS TCP upstream →
local NXDOMAIN responder; fixed HTTPS API → local real ChatAccess and ephemeral
matching certificate; mailbox → duplex byte relay. Only the overlay subprocess
uses the ephemeral API root. No production endpoint/trust switches or accepted
Xray/Android106 pins change. Actual LXMF/node/installed delivery remains **L05**.
This is **not live Telemost, installed acceptance or F-01**.

## Before / after resource corrections

1. **Lost release, reproduced before Python correction:** four real pending
   ChatLane CONTROL commands hold replies; a completed authenticated HTTP
   operation releases its lease. Old code drops local BUSY: the released lease
   still reports SERVICE_ONLY, opens1. `release-red-verified.log`: **1 expected
   failure / 5.26s**, explicit receive/submission barriers, actual native accounting.
   Final reproduction explicitly includes the actual watcher plus three other
   pending commands: **1 expected failure / 5.06s** before, **1 passed / 5.11s**
   after (`release-red-watcher.log`, `release-green-watcher.log`).
   After correction release waits for capacity within the existing 4s submission
   deadline, sends and receives native acknowledgement; the operation disappears,
   generation lease1/transport1 remain. No larger queue or compensating acquire.
   Capacity timeout closes the lane fail-closed; closed-lane wakeup is tested.
   The established drain/worker-exit/admission marker rules remain unchanged.
2. **Owned-TUN race exposed by the combined gate:** original race build reached
   CONNECTED/EXISTING_EXIT, but stop exited66. gVisor fdbased RX read transport
   handlers while Xray Start installed them (`manual-race.log`, four DATA RACE
   reports). Cleanup correctly remained sticky; success was not inferred from
   the stop reply. A platform-owned ingress fence now drops pre-initialization
   packets, enables delivery only after actual Start returns, and fences/drains
   delivery before Close. No packet queue, stubbed Attach/Probe or reference patch
   modification. Deterministic ingress tests and actual race-built handoff pass.

Generation ownership remains: deny new operations → cancel/release operation and
generation leases → confirmed native drain/cleanup → worker exit → release flock.
The native Coordinator semantics, fixed scope, UID/device/profile checks, D03
typed errors/no-replay, L01-R provenance and absence of SYSTEM fallback are retained.

## Local checks for this source

Locked Python3.13 environments, Go1.26.1, disposable network-only/system containers;
all private generated material and raw logs stay under `/tmp/fc-l022/` or disposable
container storage. Prior L02.1/R/R2 evidence is preserved.

| Check | Result |
|---|---|
| Python lane/host/service/status, manual/Auto lifecycle, mailbox/error dependencies | **242 passed / 32.50s** |
| Actual root→UID/process ownership | **13 passed / 0.81s** |
| Original lifetime/terminal/status authenticated regressions | **15 passed / 109.69s** |
| Combined manual + Auto + release regression | **3 passed / 80.31s**, final `combined-verified.log`: full kernel/lease accounting and actual watcher contention; wrapper exit0 |
| Standard native build/test | PASS; all desktop native packages, race-enabled test log |
| Desktop platform/chatipc/worker `go test -race -count=3` | PASS (1.762s / 1.469s / 1.063s) |
| Carrier restrictedowner/restrictedchat/wholedevice/roombroker/familysession/tcpforward `-race -count=1` | PASS |
| Existing actual Auto policy/root adapter isolated kernel | PASS, 18 checks, host_network_changed=false |
| Existing DIRECT isolated kernel | PASS, real proofs/TLS/fatal DENIED/no fallback; host_network_changed=false |
| Reference verifier | **175 pins PASS**, unchanged |

The first DIRECT invocation correctly refused the container PID1 namespace; its
successful rerun used an additional `unshare --net`. No safety guard was weakened.
Exploratory fixture/test failures are retained, not counted as product full-suite
failures or green evidence. Mandatory full CI suites remain enabled and unchanged.
Local full-suite reruns were **NOT_RUN**; unrelated failures are not fixed here.

CI adds a bounded combined step to `Desktop Auto native bridge / isolated-linux`,
retaining all original15 authenticated, root→UID/process and Auto/DIRECT gates.
The same job adds packet/IPC/worker race checks; no mandatory suite is disabled.

Sanitized SHA256 receipts (not release assets):

| Evidence | SHA256 |
|---|---|
| release red log | `b10fb593b9462d5b0c265aa89979633e7a483ea16b736d231181823c9434ac54` |
| release red with actual watcher | `efaec20e89f3e709a284f01f7ac37ac16a2e729a54e422d78bce7abde8dca2f7` |
| release green with actual watcher | `1a99469259bc882fa27cef7a10eff4745b58e5280d71b55bab3ccf496328acaf` |
| final combined gate | `05973ff27de01e84654ce95b16ba5c8dbd8f909eac3f9775d24e609b71267b1d` |
| packet initialization race log | `78086bb4c6bae9031b8afb8104d3b93245d1d3be8671d95fa792d191d0e9c9e2` |
| local standard worker | `a63cac0491887e6a2393a034442eb093f2e2b16ae140e710794eace3265eced8` |
| race authenticated worker | `12d32026aae224ac2e9d62f3a48955966e29ec8a0a3c5dc6d1d773530618bf40` |
| standard source inventory | `c79c1fa36c4b5b6984e5f513a446b1abef76363ce61fa987396e876bdcb5ebdb` |

## Completed R2 CI — separate source

Source **`89e20a3437b2ba1b02f7d1649487579678158373`**, not this L02.2 source.
The formerly IN_PROGRESS phase0/tests job was rechecked from its own completed
log, not copied from control or Docker. All three summaries report errors0.

| Suite | Exact run/job | Completed result |
|---|---|---|
| control | [40124588227 / 120963186558](https://github.com/Joker20380/family_connect/actions/runs/40124588227/job/120963186558) | **3030 passed / 54 failed / 135 skipped**, 184.67s |
| phase0/tests | [40124588219 / 120963186536](https://github.com/Joker20380/family_connect/actions/runs/40124588219/job/120963186536) | **3030 / 54 / 135**, 162.84s |
| phase0/Docker | [40124588219 / 120963186307](https://github.com/Joker20380/family_connect/actions/runs/40124588219/job/120963186307) | **3028 / 54 / 137**, 160.06s |
| isolated-linux (15 authenticated) | [40124588213 / 120963186437](https://github.com/Joker20380/family_connect/actions/runs/40124588213/job/120963186437) | PASS |
| Client Linux | [40124588212 / 120963186543](https://github.com/Joker20380/family_connect/actions/runs/40124588212/job/120963186543) | PASS |
| AWG / TCP / voice | 40124588222/120963186495; 40124588218/120963186500; 40124588221/120963186475 | PASS |

These failures remain D01 work, not overall CI acceptance or L02.2 counts.

## Source / current CI receipt

Source commit, ordinary push/remote verification and new CI jobs are recorded in
the post-push receipt for this checkpoint, separately from the R2 results above.

## Limits / rollout

Parent L02 remains **PARTIAL pending review**, not an automatic release gate.
No product version, installed bundle, update catalog, public artifact or server
policy changed. No rollout/rollback operation occurred; installed/distributed
versions remain the entry state. Identity, WG keys, activation, Support ID,
history/settings, signed floors and accepted reference pins are untouched.
L03, installation, live, publication, Windows, fleet and iOS **NOT_RUN**.
**STOP. NEXT — review L02.2.**
