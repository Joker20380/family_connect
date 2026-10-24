# L01-R — review corrections for protected Linux chat DIRECT, 24.10.2026

## Scope and result

**Local corrections complete; L01 NOT ACCEPTED. NEXT — review L01-R.**
Entry: clean current `main`, HEAD and verified remote
`968e71d437d2e5fa03c7ebe17db8f2648433bfe3`. No checkout rollback or other work removed.
D03/D04/D05 remain accepted dependencies. D01 remains open; D02.1-R PARTIAL/NOT_RUN.
No L02, installer, live, Windows integration, fleet or iOS work is authorized here.

1. Product `chat_direct_host.main()` now calls `prepare_runtime`: check root-owned,
   non-writable, non-symlink ancestors and leaf, then descriptor-based chmod0711
   after inode verification. This explicitly overrides unit umask0077 for traversal,
   not for user writes. Socket remains assigned-UID0600; root lock must be0600.
   Unsafe existing directories/locks are refused, not silently repaired into trust.
2. ChatHTTP records the locally selected successful request route, never a response
   field. ChatOwner consumes the **register** response's route after FriendsClient
   validation. EXIT registration clears the user's old DIRECT digest and selects
   an EXIT-only ProtectedMailbox; it does not replace root authority with user data.
   A later successful root DIRECT registration restores DIRECT. Route changes
   recreate the carrier; endpoint/key changes and refreshed expiry are reflected.
   Root digest/device/chat identity/sequence/equivocation/expiry/revocation checks
   remain unchanged. EXIT retains the existing verified native profile context;
   no VPN/MESH owner is created and no SYSTEM route is introduced.
3. Native `failure()` recognizes Go TCP TLS `net.OpError{Op:"remote error"}` even
   with empty Net and an internal `tls.alert`. It remains DENIED through Python
   DirectHTTP/ChatHTTP; no EXISTING_EXIT fallback. Ordinary TCP failures remain
   transient; explicit cancellation/deadline remain terminal. D03 first-terminal,
   bounded bodies and no-replay cases are retained.

## Before → after evidence

Tests were added and run before product fixes. The final Python regressions were
also replayed against an isolated export of entry SHA968e71d (not the checkout).

| Boundary | Before | After |
|---|---|---|
| Actual main(), fresh runtime under unit umask, forked UID65534/65533 | Fresh assigned UID denied; writable ancestor and0644 lock erroneously admitted: **3 failed / 3 passed** | **6 passed**: assigned UID succeeds, other UID denied; owner/symlink/writable ancestor/leaf/lock negatives retained |
| Actual ChatOwner/FriendsClient/proofs → root IPC → ProtectedMailbox | **4 failed** at `access_denied` after EXIT registration while root service still running | **4 passed**, included in145 below: stale root authority both live/expired, unchanged/changed node metadata, sequence1→2→3, DIRECT restoration |
| Real local trusted TCP TLS peer, requires missing client certificate | TLS1.2 and1.3 both return UNAVAILABLE, not DENIED | Both PASS with DENIED, one dial, zero HTTP handler calls |
| Isolated native→Python→ChatHTTP, same real fatal TLS | Old L01 worker reaches forbidden fallback (`AssertionError: fallback used`) | New worker returns native DENIED; ChatHTTP access_rejected; fallback untouched |

The provenance regression uses actual protected/EXIT AF_UNIX admission and sockets
with synthetic native EXIT lane/profile materials. Only the lower RNS exchange
is replaced by byte probes to deterministically observe the selected route; real
ProtectedMailbox.exchange and terminal routing policy are exercised. This is not
live RNS delivery. Existing encrypted mailbox tests provide separate evidence.
The root/UID test starts the real main function under the unit's parsed umask in
a disposable container `/run` directory; it is **not systemd/full installed acceptance**.

Prepared D01 image: Python3.13.15, control/provisioning/device_identity lockfiles,
messenger `--no-deps --require-hashes`, unchanged from L01. Non-root suites:

```sh
python -m pytest -q clients/desktop/tests/test_chat_direct.py tests/test_chat_bridge_http.py \
  clients/desktop/tests/test_chat_host_registration.py clients/desktop/tests/test_mesh_chat_host.py \
  clients/desktop/tests/test_mesh_chat.py clients/desktop/tests/test_chat_service.py \
  tests/test_friends_chat.py tests/test_linux_chat_package.py
python -m pytest -q messenger/tests/test_linux_owner.py messenger/tests/test_linux_mailbox.py \
  messenger/tests/test_android_carrier.py messenger/tests/test_delivery.py
# Separate disposable root environment; no installation:
python -m pytest -q clients/desktop/tests/test_chat_direct_runtime.py
(cd clients/mesh && go test -race -count=1 ./direct ./chatipc ./normal)
(cd carrier && go test -race -count=1 ./underlay ./restrictedchat ./restrictedowner)
```

- **145 passed**, native lane enabled with FC_TEST_MESH_WORKER; **49 passed** mailbox/
  owner; **6 passed** root/UID; zero failures/errors/skips in these final selections.
  Earlier run without worker:143 passed/2 native skips, not substituted for final PASS.
- All six Go/race packages PASS. Go1.26.1; pinned Xray
  `d2758a023cd7f4174a5a5fa4ff66e487d4342ba0` and packet patch unchanged.
  Local test worker SHA256 `be89c45b75e9d2f9f4db7bc74529825c7f973651b6a22b0936e28c3fc32b2b6d`.
- `scripts/check_chat_direct_underlay.py` PASS with that worker under trusted `/root`
  ancestors. Existing VPN-OFF/guarded-marked route, unmarked UNREACHABLE, proofs,
  half-close, interface-change cancellation, revocation and encrypted reopen retained;
  new real fatal TLS rejection added. Empty disposable netns; host network unchanged.
  Synthetic peer only, no live gateway. Namespace-only rp_filter fixture unchanged.
- Public reference verifier PASS175 files. No private capsule replay or full local
  pytest. Initial local build lacked module-cache write permission; retried with
  approved access in a fresh output directory, preserving failed logs.
- Unchanged isolated Auto kernel gate **PASS18 checks** with the new worker.
  First attempt lacked `/usr/sbin/nft` in the test image; nftables was installed
  only in a disposable container, then the gate passed. No host package/network change.
- CI keeps all mandatory suites and original kernel gates, adds root/UID step;
  no tests are hidden or failures reclassified. Source, links and whitespace checked.

## CI provenance and remaining gates

New source CI is pending the code push; no historical result is attributed to it.
The exact source SHA and observed runs will be recorded after the push.
Entry docs-only SHA968e71d ran [phase0/40101235791](https://github.com/Joker20380/family_connect/actions/runs/40101235791):
FAILURE, separate from product/native evidence.
[L01's positive evidence](2026-10-24-linux-chat-direct-l01.md) remains:
`bff34ebbb19501261eb19ac6ba4e325d31f3b180` Client Linux/AWG/TCP and protocol PASS;
`edc79c2631ef75b85452e6cf605706eed1f9e08a` Auto/isolated DIRECT kernel PASS.
Their residual full-suite and GTK voice failures are **not** fixed or reclassified.

Built only: local test native. Installed: unchanged, full acceptance0/2. Public:
Linux0.2.11/Windows0.2.15 unchanged; invitation/catalog/download artifacts not changed
or freshly verified. No deployment, release tag, signing, server or fleet policy change.
L03 owns packaging/activation; L04/L05 own installed/live acceptance. Source rollback
is an ordinary reviewed revert, not a history rewrite; no runtime rollback is needed.
Stop here: **NEXT — review L01-R**.
