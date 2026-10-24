# L01 — fixed protected Linux chat DIRECT, 24.10.2026

## Result and scope

**DONE in local Linux source/native/kernel scope; NEXT review L01.** Entry: clean
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
Mailbox uses the existing0600 socket admission and CLOEXEC AF_UNIX descriptor relay,
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

Initial code `bff34ebbb19501261eb19ac6ba4e325d31f3b180` pushed and remote verified.
Client Linux, Auto protocol/Ubuntu, AWG and TCP PASS; control/phase0/Docker and voice
remain FAIL. Control on this SHA: **2977 passed / 54 failed / 0 errors / 107 skipped**,
exit1; subsequent GUI/package acceptance skipped. Other old counts are not transferred.
The new isolated DIRECT gate also FAILed:
[run40099764860/job120889322393](https://github.com/Joker20380/family_connect/actions/runs/40099764860/job/120889322393),
`('registration', False)`; prior mandatory Auto kernel checks passed.

Harness follow-up: keep the worker under root-owned non-writable ancestors in
`/root/fc-chat-direct-test`, not assume `/opt` is trusted on every runner. Controlled
Python3.12 reproduction: `/opt` mode0777 gives `ProtocolError` before native networking;
the same image with the worker under `/root` passes. Production `trusted()` is not
weakened. The fixture now records safe action/error categories and `/opt` ownership/mode
for diagnostics; no request/response/identity bytes. CI for this follow-up is separate.
D05 `c53265d`: Client Linux job120874251704 is now verified completed **PASS**.
Voice GTK Return gate remains **FAIL, cause unknown**, not declared flaky/fixed.
Previous D01 residual failures remain separate; no count is predicted for L01.

L02 service-only/OFF→ON→OFF, L03 full root/user dependency packaging and activation,
L04 installed VPN, L05 installed/live messenger, Windows and live gateways remain
**NOT_RUN**. Existing component-r18 is not declared to contain this new root service.
Only the added user-module dependency is copied into the existing bundle source list;
no full installer, installed service or public artifact is produced. Source rollback
is an ordinary reviewed revert; no live runtime rollback is needed. Stop after review handoff.
