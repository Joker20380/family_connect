# L02 — Linux chat MESH service-only / ownership, 24.10.2026

## Result and entry

**PARTIAL — source integration and bounded checks, not L02 acceptance. NEXT — review L02.**
Entry: clean current `main` / verified remote
`b3301d07cb6e06f3c032b31a99f39e9535d3b21d`; no reset, branch replacement or other work removed.
The user accepted L01/L01-R in Linux source/native/root→UID/isolated-kernel scope.
The exact positive [L01](2026-10-24-linux-chat-direct-l01.md) and
[L01-R](2026-10-24-linux-chat-direct-l01-r.md) evidence remains in their reports; acceptance does
not turn those checks into installed/live evidence. D03/D04/D05 remain accepted.
D01 stays open; D02.1-R remains PARTIAL/NOT_RUN. Full-suite and old GTK failures
are not repaired or reclassified by this checkpoint.

The missing completion gate is a **successful authenticated MESH API/mailbox
OFF→ON→OFF exercise through the actual Linux service processes and native owner**.
The available positive host tests use a synthetic lane/material verifier. The new
cross-process tests run real `fc-mesh` workers but only their idle/control boundary,
not an authenticated MESH transport or VPN publication. Neither set substitutes
for the missing combined gate. L02 is therefore not DONE despite passing checks.

## Actual source wiring

1. `mesh_chat_service.ServiceOwner` is a separate root, per-UID demand host, not a
   VPN supervisor. Public `prepare` accepts only device-bound identity/WG material
   from `FriendsOwner.chat_materials`, never endpoints, server keys, commands,
   paths, interfaces, resolver or trust anchor. The anchor is a root-owned packaged
   file; profile P0 and resolver are fixed by root. Existing `MaterialOwner` and
   native refresh/inspect perform signature/identity/expiry/revocation validation,
   floors, durable write and readback in the existing per-UID cache. This does not
   create a new device, encrypted store, history or user VPN intent.
2. The host starts `NativeWorker --stdio-chat-fd`, **without a start command**.
   Chat `acquire` invokes the existing native `restrictedchat.Owner` service-only
   open; no packet `Attach`, VPN TUN, DNS/default routes or reconnect owner is used.
   UID/device checks, fixed API and bounded AF_UNIX mailbox proxy are reused.
   CONNECTING is accepted only for the root-selected SERVICE_ONLY binding; completed
   operations report that binding's route, not a response-supplied authority.
3. `mesh_ownership.Ownership` serializes independent Linux processes using two
   root0600 flock files in a root0711 directory. VPN takes an exclusive reservation,
   then waits for transport admission. The service-only watcher cancels on that
   reservation, shutdown, idle demand or changed underlying. The old binding is
   fenced, native leases/streams are cancelled, worker cleanup/process exit is
   awaited, and only then is admission released. A child inherits the transport
   descriptor, including the materials worker, so parent FD loss cannot admit a
   competing worker. A nonempty durable marker after unconfirmed cleanup refuses
   replacement even when no process retains the flock. There is no unsafe reset.
4. Actual manual `Supervisor` and Auto `MeshCandidate` constructors use that gate.
   Reservation starts before materials/network setup and spans native drain,
   route detach and verified network cleanup. The existing per-worker native
   ReserveVPN/Wait/Publish/Drain/Release and exact verified profile matching remain;
   no process-local Go coordinator is claimed to be cross-process. Native
   `restrictedchat.Owner.Close` uses the existing reservation/wait mechanism to
   await late service-only bootstrap cleanup. The pinned `restrictedowner` source
   and Android106/reference manifests are unchanged.
5. With VPN ON, the existing manual/Auto chat endpoints borrow the verified VPN
   context. A live reservation prevents another service-only worker. After VPN
   cleanup/release, a subsequent still-authorized chat operation can prepare a new
   generation. ChatBridge prepares SERVICE_ONLY only when no existing exit is
   available; it does not replay a completed EXIT API operation. ProtectedMailbox
   has DIRECT→EXISTING_EXIT→SERVICE_ONLY, with explicit terminal/deadline/cancel
   handling and no SYSTEM. A registration over either MESH route clears the user
   DIRECT digest rather than importing the response into root DIRECT authority.
   Fresh root DIRECT registration restores DIRECT. Native malformed IPC replies
   now fail as DENIED instead of transient UNAVAILABLE.

The source unit `family-connect-chat-mesh@.service` is **not installed or enabled**.
Only the dependency list of the existing MESH bundle gains `mesh_ownership.py`, so
its already-bundled manual/Auto modules do not import a missing module. Full root
chat service/anchor/dependency packaging and coherent activation remain L03.
Do not activate the new service alongside older, ungated MESH components.
Build metadata says `linux-demand-host-source-partial`, not installed capability.

## Checks and precise evidence boundaries

- D01 Docker environment: Python3.13.15, `/tmp/test-venv`, control/identity and
  messenger locked dependencies; targeted owner/mailbox/host/IPC/manual/Auto tests.
  **354 passed** in the targeted owner/mailbox/host/IPC/manual/Auto selection;
  the affected lifecycle subset was also rechecked (**93 passed**) after fencing
  the watcher against an old generation and serializing admission FD operations.
  Root/process plus L01-R root→UID: **13 passed** (7 + 6) in disposable netns.
  Additional real-worker material/configuration and Auto platform selection:
  **82 passed** (separate from the 354), including the default native subprocess
  adapter affected by inherited-descriptor support.
  CI source SHA is recorded in the receipt below.
- Unit/source: service API and real duplex AF_UNIX FD with synthetic native lane;
  concurrent requests share one generation; revocation/expiry/material rejection;
  cancellation during bootstrap; preemption, underlying change, shutdown and
  sticky cleanup failure; unknown public fields; EXIT terminal/no-replay;
  manual/Auto reservation→native-drain→detach→cleanup→release ordering.
- Real ChatOwner/root DIRECT IPC/ProtectedMailbox regression now exercises both
  EXIT and SERVICE_ONLY registration provenance, old authority expiry, sequence
  and node metadata changes, and DIRECT recovery. MESH lane and lower mailbox
  exchange remain synthetic, as in the original EXIT regression.
- Root/process: separate Python owner processes and actual sealed native workers
  check admission barriers, inherited lock continuity, no replacement after
  unconfirmed cleanup, cancellation and unsafe paths. No TUN is created, worker
  PIDs exit, parent FDs/threads return to baseline. These workers are idle, not a
  successful authenticated MESH/VPN handoff. The six L01-R real root→UID checks
  remain mandatory and pass separately.
- Native: race suites for `restrictedchat`, unchanged `restrictedowner`,
  `desktopmesh`, `wholedevice`, `underlay`, `desktopauto`; eight native bridge
  package race suites via sealed build. Includes signed materials/exact-profile
  borrowing/revocation and late-open cleanup tests. Those native fixtures do not
  replace Linux process-chain acceptance.
- Kernel: existing protected DIRECT synthetic-TLS gate passes, including fatal
  TLS no-fallback, root proofs, encrypted reopen and guarded underlying; Auto
  native policy gate (18 assertions) and traffic guard (44 assertions) pass in
  disposable netns. New root/process tests also pass inside isolated netns.
  Host networking and deployed services are unchanged.
- Source reference verifier: PASS, 175 shared files. `git diff --check`, targeted
  documentation links and staged secret/build-output inspection are required.
  Mandatory control/full suites, root→UID and existing kernel CI gates are kept;
  new service-only and process-admission tests are additive.

Local sealed Linux worker (Go1.26.1, unchanged native105/Android106 reference):

- binary SHA256 `037a5a263dd0b5ccb1f8088464d020f73d8d919a37726ef5f7e9d0d68affadf9`;
- source manifest `b0b33414960ad8823d6d13ae74581bd1422169bec383c2d301f4ac345f964198`;
- Xray pin `d2758a023cd7f4174a5a5fa4ff66e487d4342ba0`, unchanged patch
  `eaeb30fd1e2aa52272d7f3a2a06bcad7b983ca9866a87fbd0a614eede6048872`.

## CI / source receipt

Source/tests/docs checkpoint **`383ef3606aaa4dbd29f0c7c0f755e6faec6e309f`** was
ordinarily pushed to `main`; remote SHA verified equal. The local native build's
source manifest was recomputed against that committed tree and matches exactly.
Results below are for that exact SHA, not the later documentation receipt:

| Gate | Observed result |
|---|---|
| [Auto bridge run40115518564](https://github.com/Joker20380/family_connect/actions/runs/40115518564), [isolated-linux job120935872792](https://github.com/Joker20380/family_connect/actions/runs/40115518564/job/120935872792) | **PASS**. Existing protocol matrix, new L02 host/native/process checks, L01-R root→UID, Auto and DIRECT kernel gates all retained. No authenticated cross-process MESH success claim. |
| [Client Linux job120935873108](https://github.com/Joker20380/family_connect/actions/runs/40115518559/job/120935873108) | **PASS**, mandatory Linux build/smoke checks; not a complete L03 package or installed acceptance. |
| [AWG job120935872744](https://github.com/Joker20380/family_connect/actions/runs/40115518554/job/120935872744), [TCP job120935872740](https://github.com/Joker20380/family_connect/actions/runs/40115518585/job/120935872740) | **PASS**, release jobs skipped. |
| [Linux voice job120935872765](https://github.com/Joker20380/family_connect/actions/runs/40115518527/job/120935872765) | **PASS** on this SHA only. Previous GTK failures were not investigated, repaired or declared flaky. |
| [Control job120935872858](https://github.com/Joker20380/family_connect/actions/runs/40115518556/job/120935872858) | **FAIL**, mandatory full pytest: 3015 passed / 54 failed / 120 skipped, 7 subtests passed, exit1. No blanket claim that every failure has the old cause. |
| [phase0/tests job120935872823](https://github.com/Joker20380/family_connect/actions/runs/40115518548/job/120935872823) | **FAIL**, mandatory full pytest: 3015 passed / 54 failed / 120 skipped, 7 subtests passed, exit1. |
| [phase0/Docker job120935872627](https://github.com/Joker20380/family_connect/actions/runs/40115518548/job/120935872627) | **FAIL** at Dockerfile.control full pytest: 3013 passed / 54 failed / 122 skipped, 7 subtests passed, exit1; downstream failover checks not reached. |

Local evidence is under `/tmp/fc-l02/evidence`, not published private state.
No full local pytest rerun is claimed. CI failures remain separate from targeted PASS.
The source CI results are recorded without rerunning failed suites to obscure their
outcome. Remaining non-Linux Client-build jobs do not change the recorded Linux
job result and are not Windows/Android feature acceptance for L02.

## Remaining gates / rollout

- **L02 remaining:** combined authenticated native MESH API/mailbox and successful
  VPN publication/borrowing across real Linux owner processes, including wrong
  profile, simultaneous VPN/chat demand, late results and actual transport leases.
  Existing unit/native/process evidence is explicitly not that combined proof.
- **L03:** complete coherent root/user bundle, packaged anchor and dependencies,
  activation and safe operational recovery of an unconfirmed admission marker.
  Current source deliberately fails closed; no automatic marker deletion or
  service restart is advertised as recovery.
- **L04/L05:** installed VPN/messenger/live acceptance NOT_RUN. Linux0.2.11 and
  Windows0.2.15 public versions/catalogs stay unchanged. No installation,
  deployment, fleet, iOS, Windows feature work, server permission or release tag.
  No runtime rollback is needed; source rollback would be an ordinary revert,
  never reset/force-push or deletion of private identity/history/state.

**Stop after this checkpoint. NEXT — review L02. Do not automatically start L03.**
