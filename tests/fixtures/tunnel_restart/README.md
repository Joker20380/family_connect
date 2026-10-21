# Recurrent-closure diagnosis and narrow seed recovery

Scope:19 October2026, pushed source checkpoint
`dddc3347db5b02896c123488f2e5e0292ff2b7a7`. This is not PERF-3B/canary/throughput
optimization. [Report](../../../docs/releases/2026-10-19-tunnel-restart-fix.md).
Raw receipts, source capsules, diagnostics, APKs and credentials stay ignored in
`state-client-build/tunnel-restart-20261019`, private permissions. No secrets or
phone identity payload belongs in this fixture.

## Exact sources, not arbitrary main

`source-pins.json` pins patches and every modified/new file's input/output hash.
`prepare.py --apply` verifies the accepted gateway inventory and complete sealed
beta88 Android inventory plus88/89 APK hashes, copies to a new directory, dry-runs
then applies each patch with zero fuzz. Existing destination is an error, not an
invitation to apply twice. Set `TUNNEL_RESTART_OUT` to a fresh private directory
to reproduce. These capsules are local build inputs; this repository checkpoint
does not pretend to contain the complete clean-checkout installed application.

- `gateway.patch`: bootstrap-broker main, bounded seed recovery and tests only.
  Original inventory `aeeb6755bd235160127cfed67da4a870ae340cfebe89fc6d0f937908607d9483`;
  built inventory `4722b7353ba93209657f66b45c47874915362f1fbe732845ec61745abdb673e6`.
- `android.patch`: only version88→90 in the sealed normal88 recovery tree, for
  ordinary installation over89. All12 native files and Java behavior equal88;
  extended89 performance instrumentation is absent, not a speed/stability proof.
- `seal_sources.py`: original receipt/patch generator, not an instruction to
  overwrite published pins. `build_gateway.py` refuses unrelated changes;
  `build_android.py`, `sign90.py`, `upgrade90.py` retain existing signing and
  data-preserving checks. Signing requires the owner's protected vault dialog.

## Tested contract

Recover only seed_closed/SEED_READ/SIGNAL_READ with typed WS_CLOSE1011, ACTIVE
context, no parent cancellation and not already closed. At most three retries
per process lifetime,30s between attempts. Each old manager closes/joins before
fresh creation. Broker/dedicated parent is not cancelled by these attempts.
Original deadline, credential/lease/floor/publication bounds stay effective.
Other failures and exhausted budget retain fail-closed supervisor behavior.
This does not permit Closed resurrection, arbitrary transient PC tolerance or ICE
restart. Nor does it repair all signaling/media faults.

Go race checks run against the pinned capsule, not main. The initial missing
`tests/vectors/bootstrap-timestamps.json` fixture failure is retained; supplying
the unchanged vector and rerunning affected packages yields401PASS/25opt-inSKIP
including subtests. Android build reruns169 JVM cases in22suites. `test_health.py`
compiles actual VpnHealth with Android Network stubs and `HealthHarness.java`;
ten loopback scenarios cover normal/delayed/malformed/blackhole probes, current
Network, cancel/reuse and workers. It cannot establish real VPN routing.

`test_peer_states.py` verifies the built inventory, copies it into a **separate
test-only** tree and adds `peer_state_test.go`. Six subscriber/publisher cases
reproduce unchanged Disconnected/Failed/Closed→terminal behavior, later Connected
not resurrecting Send, and old callbacks not closing a replacement. They do not
demonstrate a newly implemented transient grace. Never add that test copy to the
deployed inventory or rebuild from it by accident.

## Evidence and one-shot operations

- `preserve.py`, `server_evidence.py`, `management_evidence.py`: preserve existing
  export and bounded current runtime/log/operation evidence, no new connection.
- `summarize.py`: explicitly selects diagnostic fields, retains parser-error
  counts; original fragment errors are not silently counted as missing packets.
- `observe.py`: five-minute passive, invocation-bound journal follow with4MiB cap
  plus phone PID/TUN polling. No Connect/probe/fault or global journald change.
- `physical_control.py`: one <=4KiB existing HTTPS control, only after owner
  Connect. Hash-pinned helper, current gateway executable/PID and phone PID,
  full-UID VPN route/DNS checks and NL TCP-socket attribution; no retries/bulk.
- `rollout.py`: narrow ordinary hash-pinned same-unit switch, current credentials,
  node locks, readback and readiness. A source checkpoint is never deployment.
- `resume_rollout.py`: this run's checked pre-mutation guard-abort reconciliation,
  not an automatic restart/retry loop. Preserve the first receipt.
- `interruption.py`, `renewal_failure.py`, `reconcile_readonly.py`: record the
  separate scheduled-renewal I/O failure after committed promotion.
- `forward_current_renewal.py`: **single exact-operation repair only**, not a
  general recovery recipe. Checks identical committed snapshots, locks, retained
  start-intent, old binary and current validity; starts current state once and
  completes the same controller transaction. Do not replay against a future
  operation or erase security/start-intent history to make it pass.

The owner explicitly authorized ordinary compatible rollout and normal short
restart; historical fixture canary requirements do not govern this operation.
Runtime approval/sandbox requirements still apply. No public release, push,
registration changes, arbitrary network/host mutations or live fault injection.
Rollback is original4b gateway with **current** credentials/floors, never an old
bundle. Phone rollback requires same-signer/package code>=91, no downgrade or
data clear. Existing beta88 tester delivery remains available.
