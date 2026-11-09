# SUBSCRIPTION-PAID-123 — 9 November 2026

## Scope and owner acceptance

Base: current remote main `d42e81632bae97946941b1a64ea3771d2bf2067e` (PR13).
Owner confirms beta123 appearance «выглядит норм»; the delivered recovery,
ALL/INCLUDE/EXCLUDE, pending and live MESH results remain accepted.
[Closed owner receipt](https://github.com/Joker20380/family_connect/pull/13#issuecomment-6737682320).
Two system launcher applications remain accessible only through the expanded list;
main-catalog completeness is not claimed. No Android/JNI/G4 or cold tests reopened.

This task prepares source, executable packages and one addressed policy rollout.
**DEPLOYED: NOT_RUN. REAL_PAID_OPERATION: NOT_RUN.** Installed policy remains
`android-paid-108-119-v1`. Final SOURCE_AND_PACKAGE_ACCEPTED and
READY_FOR_POLICY_DEPLOYMENT statuses require the final green CI/merge receipt.
No production writes, phone/USB/signing/rebuild, paid/cohort/identity/period changes.

## Immutable Android input

| Input | Exact identity |
| --- | --- |
| Android source | `73064237fca7ea311501f1b3dda8a4a2689bf8bc` |
| Client builds / ARM64 artifact | `42534974451` / `13640643434` |
| Signed123 SHA256 | `ae011307b4afc58ea211ea6c5cd27c28bc472bda6af9b19892de400a3d3de15d` |
| Original unsigned SHA256 — not eligible | `96a4eaed68ab31313d2d5ace3136998880d2d2fb8a803bde2d30cc17816efcae` |
| Original verification.json SHA256 | `6389fef2661a15a6ea7ac0387f7cf38da22a3aee1eb1e0e89f6c6c499bf7e28b` |
| Signing certificate SHA256 | `67a90d1bfcd5a2c0666f0cff1b0ac5e43aaa661ca1196f89e879aa39fe20848a` |

Rechecked the retained signed file and previous actual installed-APK readback:
identical SHA256. Signature v2/v3 and alignment pass; Friends package
`com.familyconnect.app.friends`, `0.1.18-beta123`/123, ARM64, minSDK27, not debuggable.
All original unsigned ZIP payload entries are unchanged, including native/trust
inputs; only signature entries are additional. No locator added. The original
source/native inventory remains the CI123 inventory, not this server merge SHA.
Observed app_version is not cryptographic APK attestation; operator handoff evidence
still supplies the exact signed hash.

## Minimal canonical change

`control.friends.paid_beta.AndroidRelease` adds exactly signed123 and changes the
reported identifier to `android-paid-108-119-123-v1`.108/119 hashes and historical
PAID_ANDROID baseline108 constants remain unchanged.120/121/122, unsigned123 and
future versions are not admitted. No schema migration or altered event payload.
Canary/permit baseline108 and immutable synthetic ReleaseMetadata stay108-only.
No second allowlist in the panel. Exact old108/119 replay returns the original
receipt before current eligibility, including after123 observation/expiry/revoke.
Conflicting event ID, version ties, wrong hash/recipient, cohort limit and terminal
revoke remain rejections. No subscription is created merely by installing123.

## Actual serving baseline and candidate

Fresh read-only inventory on9 November confirms effective HTTP/reconciler service
commands, running archive paths, current operator target and complete member hashes.
Runtime paths, units, protected fingerprints and collector settings are private.
All three central executables contain the same paid_beta; RU node archive does not.
Node enforcement, membership, units, native engines and renewal are not in this kit.

| Component | Observed baseline SHA256 | Candidate SHA256 |
| --- | --- | --- |
| HTTP | `a59956c40af36d6172e5f35f1804fe3c7bc93993c21f5f4cc1030820383e8ec1` | `2bbfbc756a60fe7d78fa0a497484415c72bcefd9448ecb614930f1f538b831fc` |
| Operator | `d1bcd1b57454c423ddc91334350cf7f6092c5ad6925480e66dfedfd616975948` | `813d40e9fc696a4a07d549dbee87da6d2f7950f1235429bb593ff3ca32df89fe` |
| Reconciler | `4c147f170948a7f28859ab5a0cba4561a30a3a3cd8bdf8d176a8d9b2042d0083` | `05f6318d34673f56aa0ce12ce715d7341257b8bf69bd177d36528004e6db1d19` |

`scripts/package_paid_policy_overlay.py` pins each actual archive and old module,
preserves its complete ZIP inventory and every non-paid member. The executable
module diff is only the policy identifier and the descriptor123: no unrelated
current-main transport/bootstrap implementation is substituted. Final private kit
includes full before/after inventories, exact source SHA, immutable candidates,
baseline code rollback copies, preflight and private operator handoff.

## Evidence

- 382 targeted Python regressions pass: paid contract/release observations, historical
  canary/CRL constraints, membership preparation and existing packaging.
- 23 tests against the **actual baseline-derived HTTP/operator pair**
  pass: real CLI, running packaged HTTP challenge/proof/subscription handlers,
  isolated canonical archive-backed read-only collector, protected rows unchanged
  by reads, activate/renew/grace and old108/119 replay. All writes use synthetic data.
- Two-way version conflicts, unsigned/wrong/future input, altered event ID/recipient,
  limit10 and terminal revoke are covered; tests never label APPLIED as bank payment.
- The first new clock-fixture run failed because a lazy lambda consumed argv too
  late; the isolated test clock was corrected. No production contract change needed.
- Mandatory hosted CI/review and merge identities are retained in the final PR
  receipt, not followed by a cosmetic documentation-only head. Android production
  inputs and accepted123 bytes do not change.

## One subsequent rollout, not executed here

Use the closed handoff only after an explicit policy-delivery decision. Recheck all
baseline hashes/current paths/effective units and exact source pins; unexplained
drift stops installation. Pause new paid CLI operations, take consistent nonempty
`--include-paid` SQLite backup plus isolated restore verification, preserve current
protected fingerprints/code/units/collector settings. Atomically replace the three
central archives with accepted candidates, preserving the preparation-aware current
operator path and all registry-adjacent transport configuration. Keep central lease
updates running; restart only HTTP, not AWG/TCP/MESH or renewal. Verify loaded HTTP,
operator policy/status, next reconciler cycles and protected data. Switch only the
external subscription archive pin to the verified HTTP bytes; preserve HMAC and
per-node pins. Require a fresh successful import and authenticated panel readback.

Code rollback restores the exact saved108/119 HTTP/operator/reconciler and collector
pin, not an old ledger. Previously issued entitlement/events persist; new123
operations stop,108/119 and exact old replay remain. No real activate is required
to qualify or deploy this policy. Receiver, absolute period and payment basis remain
mandatory for any later real operation.

See [operator instruction](../operators/subscriptions.ru.md). Future panel ↔ official
support chat ↔ Android work is not part of this task.
