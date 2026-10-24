# L01 — fixed protected Linux chat DIRECT, 24.10.2026

## Result and scope

**Historical local evidence; L01 NOT ACCEPTED after review.** The three defects
and their bounded correction are tracked in [L01-R](2026-10-24-linux-chat-direct-l01-r.md).
All positive results below retain their original SHA; they are not L01-R results.
Entry: clean
`main`, HEAD/remote `a1d79001be2a20dd72cb5f75607843218bbaa428`. D03/D04/D05 reviews
accepted. D01/general CI stays open; D02.1-R stays PARTIAL/NOT_RUN. No deployment,
version/catalog, server grant, identity/WG key, accepted pin or private state change.

Chat daemon actually constructs DirectBridge and ChatOwner uses DirectHTTP through
the accepted ChatHTTP policy, then ProtectedMailbox (DIRECT/EXISTING_EXIT, not SYSTEM).
The independent root service needs no VPN/MESH runtime. It authenticates Unix peer
UID and device/proofs, allows only `/friends/chat/challenge` and `/friends/chat/register`,
and retains mailbox authority from the fixed TLS endpoint, not a user-provided address.
Authority binds device/chat public, sequence, canonical endpoint/key and ≤120s expiry.
Open sends only the digest of that exact registration; pending, altered, revoked,
expired or replaced authority is not a new privileged connection. Sequence equality
cannot change node identity/address. Root state is memory-only; no user-store migration.

Native private inherited-FD mode is Linux/root-only. It reuses the existing Go
underlay and Native.Protect; bind/mark precede connect. All destinations are literal
IPv4, so this path performs no DNS. Root-selected Underlying is checked before/after
operations and during lifetime. No ordinary-socket retry exists. Fixed HTTP bounds,
identity encoding, no redirects/proxy environment, TLS/HTTP/invalid-response/deadline
terminal errors and D03 no-replay rules remain. Existing-exit profile binding is unchanged.
Mailbox uses the existing 0600 socket admission and CLOEXEC AF_UNIX descriptor relay,
bounded duplex/half-close, four-operation capacity, cancellation and child/thread/FD cleanup.
Replacement/expiry/shutdown cancel only DIRECT work, never the VPN owner.

## Evidence

Prepared D01 Python3.13.15 environment, unchanged control/provisioning/identity locks;
messenger separately `--no-deps --require-hashes`; strict imports PASS.

```sh
python -m pytest -q clients/desktop/tests/test_chat_direct.py tests/test_chat_bridge_http.py \
  clients/desktop/tests/test_chat_host_registration.py clients/desktop/tests/test_mesh_chat_host.py \
  clients/desktop/tests/test_mesh_chat.py clients/desktop/tests/test_chat_service.py \
  tests/test_friends_chat.py tests/test_linux_chat_package.py
python -m pytest -q messenger/tests/test_linux_owner.py messenger/tests/test_linux_mailbox.py \
  messenger/tests/test_android_carrier.py messenger/tests/test_delivery.py
(cd clients/mesh && go test -race -count=1 ./direct ./chatipc ./normal)
(cd carrier && go test -race -count=1 ./underlay ./restrictedchat ./restrictedowner)
python scripts/verify_desktop_reference.py
```

- First selection: **141 passed / 0 failed/errors/skipped**, native lane enabled with
  `FC_TEST_MESH_WORKER`; second: **49 passed / 0 failed/errors/skipped**.
- All six Go packages PASS with race detector. HTTP tests use actual TLS streams,
  cleanup errors, response bounds and no-replay; denied protection never reaches connect.
- Python tests exercise actual ChatOwner/FriendsClient proofs and root IPC with a
  synthetic native transport: forbidden fields/UID/device, authority substitution,
  pending/expiry/revocation/replacement, cancellation during registration/open, late
  result disposal, disconnect/shutdown, terminal BridgeError vs OSError and encrypted reopen.
- `scripts/check_chat_direct_underlay.py`: **PASS**, real production Native/DirectHost/
  ChatOwner/ProtectedMailbox in an initially empty namespace with a separate synthetic
  TLS peer namespace. Both VPN-OFF and guarded underlying work; marked route is eth0,
  ordinary unmarked route is UNREACHABLE. Actual proofs, proxy half-close, interface
  rename cancellation, revocation and store reopen pass; no VPN owner or host routes changed.
  The fixture disables rp_filter only inside its disposable namespace: otherwise the
  artificial unreachable reverse route drops reply packets. This is not an installed
  VPN/sysctl acceptance claim. RNS/LXMF delivery is separately exercised by the existing
  mailbox tests; kernel peer payload is synthetic bytes, not live encrypted delivery.
- Worker built with Go1.26.1, pinned Xray `d2758a023cd7f4174a5a5fa4ff66e487d4342ba0`
  and unchanged packet patch. Test binary SHA256
  `74bce848fac9f497f66c18cee9860b90e2654d6267425a2ae3535e869e3a6d84`.
- Public source verifier: **175 files PASS**; full private capsule not rerun. Links,
  source diff and `git diff --check` checked. No private fixtures/binaries committed.

Reproduce the kernel check only with the explicit empty-netns guard, a root-owned
test worker under trusted parents, and the prepared Python interpreter:
`sudo unshare --net -- <python> scripts/check_chat_direct_underlay.py --host-netns <parent-inode> --worker <test-worker>`.
The existing isolated CI gate retains all Auto checks and adds the DIRECT checks;
its required paths/lock filter is updated. Mandatory full suites are not weakened.

## CI and limits

Initial product code `bff34ebbb19501261eb19ac6ba4e325d31f3b180` pushed and remote verified:

| Gate on bff34eb | Actual result |
|---|---|
| [Client Linux](https://github.com/Joker20380/family_connect/actions/runs/40099764878/job/120889323177) | PASS, including mandatory desktop and subsequent steps. |
| [AWG](https://github.com/Joker20380/family_connect/actions/runs/40099764881/job/120889322281), [TCP](https://github.com/Joker20380/family_connect/actions/runs/40099764875/job/120889322227) | PASS. |
| [Auto bridge](https://github.com/Joker20380/family_connect/actions/runs/40099764860/job/120889322393) | Protocol/Ubuntu PASS; prior mandatory Auto kernel PASS; new DIRECT kernel FAIL: `('registration', False)`. |
| [Control](https://github.com/Joker20380/family_connect/actions/runs/40099764889/job/120889322477) | 2977 passed / 54 failed / 0 errors / 107 skipped, exit1. Subsequent GUI/package acceptance skipped. |
| [phase0/tests](https://github.com/Joker20380/family_connect/actions/runs/40099764865/job/120889322156) | Full pytest FAIL; cargo skipped. No older counts attributed to this job. |
| [phase0/Docker](https://github.com/Joker20380/family_connect/actions/runs/40099764865/job/120889322067) | Build/tests-stage FAIL; provision/failover/auth/offline/revocation not run. |
| [Voice](https://github.com/Joker20380/family_connect/actions/runs/40099764863/job/120889322171) | FAIL at real GTK/synthetic microphone step; cause not reclassified or repaired in L01. |

Harness follow-up: keep the worker under root-owned non-writable ancestors in
`/root/fc-chat-direct-test`, not assume `/opt` is trusted on every runner. Controlled
Python3.12 reproduction: `/opt` mode0777 gives `ProtocolError` before native networking;
the same image with the worker under `/root` passes. Production `trusted()` is not
weakened. The fixture now records safe action/error categories and `/opt` ownership/mode
for diagnostics; no request/response/identity bytes.

Follow-up code/harness `edc79c2631ef75b85452e6cf605706eed1f9e08a` pushed and remote
verified; product/native sources unchanged from bff34eb:

- [Auto bridge run40100690072](https://github.com/Joker20380/family_connect/actions/runs/40100690072)
  **PASS**, including [isolated-linux job120892040344](https://github.com/Joker20380/family_connect/actions/runs/40100690072/job/120892040344).
  Artifact12562377847 contains both original Auto kernel PASS (18 checks) and DIRECT
  kernel PASS: API/mailbox protected, VPN OFF, guarded underlying, unmarked route
  UNREACHABLE, real owner proofs, encrypted reopen, revocation and interface-change
  closure. It also records runner `/opt` mode0777, matching the controlled refusal;
  host network unchanged, no VPN owner, live=false. Root admission was not weakened.
- [phase0/tests job120892040164](https://github.com/Joker20380/family_connect/actions/runs/40100690073/job/120892040164)
  **FAIL** at full pytest; cargo skipped.
- [phase0/Docker job120892040305](https://github.com/Joker20380/family_connect/actions/runs/40100690073/job/120892040305)
  **FAIL**: 2976 passed / 53 failed / 0 errors / 109 skipped, 7 subtests passed,
  exit1 in non-root full pytest. Artifact12562434516 `build.log` confirms counts;
  `/tmp/tests-passed` is not created and downstream provision/failover/auth/offline/
  revocation are skipped. No DIRECT/ChatHTTP cases appear in the failure summary.
- Client Linux/control/AWG/TCP/voice are **NOT_RUN (path-filtered)** on the harness-only
  SHA. Their bff34eb results above remain evidence for that SHA, not new executions.

The final evidence checkpoint changes documentation only; its commit/remote SHA is
reported in the handoff. Any resulting phase0 run is separate, not an additional L01
product/kernel acceptance. No full suites were manually repeated.

D05 `c53265d`: Client Linux job120874251704 is now verified completed **PASS**.
Voice GTK Return gate remains **FAIL, cause unknown**, not declared flaky/fixed.
Previous D01 residual failures remain separate; no count is predicted for L01.

L02 service-only/OFF→ON→OFF, L03 full root/user dependency packaging and activation,
L04 installed VPN, L05 installed/live messenger, Windows and live gateways remain
**NOT_RUN**. Existing component-r18 is not declared to contain this new root service.
Only the added user-module dependency is copied into the existing bundle source list;
no full installer, installed service or public artifact is produced. Source rollback
is an ordinary reviewed revert; no live runtime rollback is needed. Stop after review handoff.
