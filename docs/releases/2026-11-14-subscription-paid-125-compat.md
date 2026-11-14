# SUBSCRIPTION-PAID-125-COMPAT — 14 November 2026

## Scope and accepted release

PR23 merged normally at `137f85dce19c6ea7fd3e235ae23cb85b32b8532a`, after
documentation head `fb386767fb2ffd95b783544119514a0a9ca2f404`. Tablet109→125
in-app download/install is **PASS — подтверждено пользователем**; the1–2%
interruption did not recur. No repeat tablet check, installed-SHA/full-data proof
or beta113 download root-cause claim. The56 publication tests are separate from
Android source `b293f9ac5f2cc6fe2d11777dae97f4423e2d073a` / CI43048235831.
The documentation head has no CI run; it is not reported as CI PASS.

This separate branch starts from that merged main. It reuses public signed
Friends0.1.18-beta125/code125, SHA256
`f1c5bf578a5ca1e8e864a60fa9ab33249807e22c4552b5da984d126720e5740c`.
Public APK/source/catalog8 and accepted support round trip remain unchanged.

## Explicit123 decision

Source policy123 was accepted in PR14: final source
`ff2d6c1a21dee4f1db1772cfa7d31d40da8a79a1`, normal merge
`7daf41418f0e8730f9636700bfb02556a8c56ce7`, exact signed123 descriptor and
source/package/CI receipts. See [original qualification](2026-11-09-subscription-paid-123.md)
and [PR14 acceptance and incident receipts](https://github.com/Joker20380/family_connect/pull/14).
Its attempted deployment was rolled back when RU transport stopped; the primary
trigger was not established. A later retry stopped at a preexisting RU incident.
Recovery restored108/119, not123. Thus source inclusion was NOT installed acceptance,
and no payment-eligibility defect in123 was proven by that incident.

The explicit chosen final policy is **android-paid-108-119-123-125-v1**:
exact108/119 retained, previously source/package-accepted signed123 retained and
requalified, exact public125 added. Successful delivery will therefore be a new
production admission of BOTH123 and125 relative to installed108/119, not a claim
that123 was already deployed. This is deliberate, not an unreported side effect.
No unsigned123,124,126 or version range is admitted. Historical108 baseline/demo/
canary constants, event payloads, replay ordering and active-access predicates stay
unchanged. No migration; installing an APK alone never enrolls a device or grants VPN.

## Actual serving baseline and minimal overlay

Fresh read-only inventory confirms HTTP/operator/reconciler all contain paid module
`32380afdeb6cb0bed6c038399fe0dadecc3e0ea25203c1073898f042fd8035b4` (108/119).
The current operator symlink is present. RU node does not contain paid_beta.
RU watcher/AWG/TCP active with zero restarts; central timer active and last cycle
successful, fresh state1.54s old at preflight. This is not a permanent RU cause fix.

| Consumer | Actual baseline SHA256 | Qualified overlay SHA256 |
| --- | --- | --- |
| HTTP, including support-only changes | `16d96eb767602188e1999052e11cfead8dc1a4b38ae8c15394a61dc9ce7f3503` | `617c7d752a20631d624b301c59142af34f3624483a5d2d5adc2a7c7722dd74b1` |
| Preparation-aware operator | `d1bcd1b57454c423ddc91334350cf7f6092c5ad6925480e66dfedfd616975948` | `a7c801dba6a09e35c9ca7a6e6d816bbb57bc4f483404d44b5ee7f641e70cac15` |
| Reconciler | `4c147f170948a7f28859ab5a0cba4561a30a3a3cd8bdf8d176a8d9b2042d0083` | `40e1d7212b158fa01e4e4a92c0b635a910ae05b8b350840c07629629108b7aeb` |

`package_paid_policy_overlay.py` replaces ONLY `control/friends/paid_beta.py`;
complete member sets and all other member hashes match each actual baseline.
Do not substitute a full main build, which would replace retained support/recovery.
The external subscription collector verifies/imports the actual HTTP archive; its
pin must change with that archive. Panel production reads imported snapshots; its
separate synthetic backend/demo remains108-based, not a second production allowlist.

## Isolated evidence and deployment gate

- 126 targeted tests PASS, including canonical exact descriptors, latest observations,
  all supported-version tie conflicts, payment/grace, negatives and packaged123.
- 38 tests PASS against the actual baseline-derived HTTP/operator overlays, including
 125 first payment, renewal, grace, authenticated HTTP and read-only projection,
  old108/119/123 payment/grace replay after125/expiry/revoke without period extension,
  altered event-ID contents rejection and terminal revoke.
- Public signed catalog descriptor must equal an exact paid-policy descriptor in a
  new regression test; a later release cannot silently drift from this contract.
- 441 broader paid/membership/backup regressions PASS;77 focused panel subscription,
  payment-purpose and backend workflow tests PASS. Existing locked environment has
  no broken requirements. All test writes use temporary registries/synthetic users.
- Documentation local-link/anchor and whitespace checks PASS. Hosted review/merge
  are pending at this source checkpoint, not inferred from local test success.

**DEPLOYED: NOT_YET. REAL_PAID_OPERATION: NOT_RUN.** Delivery follows green required
checks and ordinary merge, fresh health/protected-data inventory, consistent nonempty
backup with isolated restore verification, and guarded code/config rollback copies.
Pause new operator writes, replace only three archives atomically at a reconciler
boundary, restart only HTTP, update only the collector archive pin, verify loaded
policy/actual next cycles/fresh authenticated panel/support health, then resume the
current operator path. No node restart, schema migration or real payment is required.
Rollback restores predeployment archives and collector config, NEVER an older DB
over new user events; old code keeps existing entitlements/replay but rejects new123/125.

Next product task: automatic addressed notifications for confirmed subscription
events. It is queued only; no notification implementation, public announcement or
test message to users is part of this task. RU stop cause remains separate.

## CI scope and preexisting monitoring drift

On source540c5b97, hosted Control panel43534779716 and Android readiness contract
43534779818 PASS. Full phase043534779731 (including failover) and Linux
control43534779752 FAIL before tests, during inventory `--collect-only` (exit2).
Their retained receipts contain no executed full-suite result. A local isolated
reproduction using only two unchanged main files demonstrates the existing duplicate
module name: `tests/test_chat_service.py` versus
`clients/desktop/tests/test_chat_service.py`. Both files and the full-suite launcher
are unchanged by this task; the launcher suppresses collection stdout in CI, so the
CI receipt alone does not identify that underlying exception. Do not label these
full runs green or delete/skip tests to hide the failure. Global collection repair
remains separate; no Android/desktop release gate is advanced here.

The task-specific hosted paid-policy workflow runs the complete441-case selected
paid/membership/backup contract, including real temporary packaged HTTP/CLI and public
catalog consistency. It also runs on subsequent public catalog changes, not only
paid-module changes. This is the risk-selected compatibility gate, not a replacement
or waiver of a full/release gate where one is required. Full workflows are unchanged.

Preflight also finds an independent existing collector mismatch: installed HTTP is
support-only16d96eb7, but subscription-source still pins pre-supporta59956c4. Latest
subscription snapshot is therefore `unavailable`, not fresh usable paid data. Delivery
must repair this pin and verify successful import; rollback must use16d96eb7 with
the restored baseline code, not silently recreate the stalea59956c4 mismatch. Preserve
the original configuration as evidence. Panel's123 module is confined to synthetic
demo operations, not real payment writes; production uses the verified HTTP collector.
