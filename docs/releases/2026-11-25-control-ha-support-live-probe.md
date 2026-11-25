# HA-02 — working support admission probe, 25 November 2026

Selected CONTROL-HA-20261123 / HA-02, continuing the
[isolated bridge](2026-11-25-control-ha-support-bridge.md) and
[installed-shape candidate](2026-11-25-control-ha-support-overlay.md).
**The reversible application admission probe passes on working OWNER support. This is not
runtime drain, safe shutdown, candidate installation, coherent capture or stage2 acceptance.**

## Actual attempts and corrections

The owner successfully authenticated through the already-requested local GUI password dialog.
The password went directly to sudo, never chat, files or evidence. No sudoers/polkit edit,
permanent privileged session or timestamp keepalive was introduced. Normal credential expiry
and terminal scope remain; missing authorization is not the current engineering blocker.

Two live attempts refused before admission changed, preserving the same working process:

1. At16:31:25UTC the launcher staged under host `/var/tmp` was not visible in the service's
   `PrivateTmp=yes` mount namespace. No bridge entry receipt appeared. Its bounded request expired;
   it was not replayed. The unchanged unit has `ProtectSystem=strict` and an existing service
   runtime directory. No sandbox setting was weakened. Preparation now compares target/host
   device, inode and mode for the parent before staging and every staged file afterward, with
   process binding rechecked. Missing, different or unreadable namespace paths refuse.
2. At16:33:40UTC staging in the shared service runtime directory reached the bridge but returned
   `RUNTIME_BINDING`. A metadata-only diagnostic at16:36:35UTC found `__main__` and `__mp_main__`
   aliases of one module, plus a distinct named `provisioning.support_worker` import. The latter
   is also imported by subscription notification handling. The old one-module-count assumption
   was incorrect for this installed runtime. Binding now deduplicates aliases by identity and
   selects only the unique main frame whose code and globals belong to that exact module/function.
   An inactive import or copied module namespace cannot stand in for the running main. Existing
   exact source/code, serial-loop, partial-accept and delivery-owner checks remain mandatory.

Neither refusal permits capture or ordinary old shutdown. Raw diagnostics contain module metadata
only, not private frame locals, chat data or keys. Original failure receipts remain retained.

## Qualification

Final **62 checks PASS/0 skips**,77.82s:37 bridge cases and25 unchanged packaging regressions.
Seven additional cases cover the real module-entry shape, mismatched active globals, an inactive
duplicate namespace, missing/different target namespace paths, and post-staging namespace/process
drift. Synthetic module-mode workers use CPython's actual `runpy._run_module_as_main` entry helper
under the installed interpreter. Source bytes, main/delivery implementations and baseline contract
remain unchanged. Existing interrupted-delivery, receipt-failure, controller-exit, stale-request,
reader/child and encrypted-store readback cases still pass. The focused subset passed6 cases.

```sh
FC_TEST_SUPPORT_BASELINE=/opt/family-connect-support/app \
FC_TEST_SUPPORT_PYTHON=/opt/family-connect-support/venv/bin/python \
python -m pytest -q -ra tests/test_control_ha_legacy_support.py \
  tests/test_package_support_capture.py
```

An additional transient system unit passes at16:40:23UTC under actual `fc-support`/
`fc-support-ipc`, the installed interpreter, `PrivateTmp=yes`, `ProtectSystem=strict`,
`ProtectHome=yes` and synthetic data. Hidden host `/var/tmp` staging refuses before output
creation; shared `/run` staging succeeds with the alias/named-import shape. Application drain
and online restoration pass; no capture permission. Only that synthetic fixture unit is stopped
and removed. The working service's prestate remains identical. This is not a stop/replacement
qualification or a complete production sandbox/runtime attestation.

## Working result and rollout

At **16:40:26UTC** the fresh one-use request succeeds on actual support PID2022541. The request
budget is10s with a0.25s post-drain hold. Serial main-loop/delivery admission pauses; admitted
delivery and route-reader scope drains without requesting cancellation. Online admission restores
in `finally`, then malformed local IPC succeeds with its expected rejection before and after.
Those malformed inputs fail JSON parsing before mailbox refresh and do not send chat messages.

Independent controller readback after callback return and an additional2s confirms the same
PID/start/boot/command/cgroup,19 source hashes,3 original unit-file hashes and15 effective unit
fields. Support stays active/running,0 restarts/no reload warning. The old control-group/SIGKILL/
40s stop policy remains. No installed source, unit or candidate change, no signal or working
service restart, no product-store copy/rewind or pending-marker deletion occurred.

The actual census reports four continuing RNS jobs: Reticulum periodic jobs, transport jobloop,
traffic counting and inbound dispatch. Therefore `runtime_drained=false`,
`external_settlement_proven=false` and `capture_permitted=false`, even with
`application_drained=true`. No RNS job was stopped. OWNER containers and RU/NL were not contacted
or requalified; older observations remain historical. No product/public installer/catalog,
invitation-page version or signing change.

Private evidence locator: `/tmp/fc-ha-support-live-20261125`; no raw private evidence is in Git.

| Evidence | SHA-256 |
| --- | --- |
| Final62 JUnit | `78529193b72950858c355af604a731ca0769691c3ff0b315f89b339bfa2d3df5` |
| First invisible-staging refusal | `008465ccacc1a0bd4637d062cd582475a1629d37016af20cad81e007079d4319` |
| Runtime-binding refusal | `df00313439410cad1ebad9413e308440a16c7c8b68ea2ba04ae8ffe70a95345e` |
| Module-only diagnostic | `144f43e6f64b0b4d4cdd2e0941f671dae335cac0fdd143df7df0032d1e548846` |
| Native PrivateTmp system unit | `6f3dc5780e9e80c5228eb4ecfc3871b54a8280ea107ca7411ad85e13528f129c` |
| Working successful probe/readback | `cb958948903438b73c50645b0fe35b856c8e29aec1da3c6fd2dec415e533c0a5` |

## Rollback and remaining gate

The probe restores application admission itself, independently of controller survival; actual
resumed IPC is verified. There is no persistent deployment to roll back. A source revert removes
only optional probe corrections/tests/docs; never rewind a live store. Retained requests are
expired/single-use and must not be replayed. No forced-stop fallback is authorized by this result.

Next: exact pinned RNS periodic/queued/exit persistence closure and independently supervised safe
old-process stop/replacement/rollback. Then installed manual/OWNER writer coverage, coherent fleet
capture, independent current-input trust/custody/approval and combined full post-ACK recovery.
The candidate is still not installed. Isolated replication PASS; same three HA-02 exit gates
partial. No HA-03, automatic failover, release acceptance, new numbered phase or completion ETA.
