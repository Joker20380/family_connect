# SUBSCRIPTION-PAID-119 — compatible paid policy and bounded installation

Owner-selected decision A, starting from verified remote main
`5197563916442d953746cb5aa3d03756ab85e51f`. PR1/PR2 are closed. The original dirty
checkout and parallel cold-provisioning work are untouched. This report fixes the
source/rollout contract; final-head hosted CI, normal merge and executed installation
receipts belong in the task PR, not a cosmetic post-CI documentation commit.

## Policy and artifact evidence

Only `0.1.18-beta108`/108/hash
`144b158fe4c07dd19a67683887558cf88a0202b937d135a9924698ffc11b4fdf` and
`0.1.18-beta119`/119/hash
`52a9847b74181c48808c86a0c5bf5925b53ef498eec628aef2d78d26f1c92d2d` are allowed.
Latest authenticated support/readiness observations must agree on one exact pair;
two individually allowed but equally-latest differing versions are a conflict.
New activate attests that pair's APK hash, not any allowed hash. Grace uses the same
eligibility with unchanged arguments/semantics. Future versions are not inherited.

Retained119 was rechecked:50,351,520 bytes, Friends package, code119/namebeta119,
exact ARM64, debuggable=false, APK v2/v3 signatures verified by existing apksigner35.
Single signer SHA256 `67a90d1bfcd5a2c0666f0cff1b0ac5e43aaa661ca1196f89e879aa39fe20848a`.
Its original build receipt/source remains `b2a37fe989294018ab08060bdebfa46d741d11d5`;
the policy/merge commit is not this APK's source. No rebuild/install/publication.

Canonical payload construction is unchanged. Exact old108 events return the original
receipt before current version/expiry/revocation eligibility. Conflicting reuse of an
event ID still fails. Active identity/invite, existing MESH revoke,10 slots, UTC bounds,
no shortening and terminal revoke remain enforced. No subscription schema migration.
Historical `PAID_ANDROID_*` and `confirm_android_baseline` remain108-bound for canaries
and demo metadata. Synthetic identities/observations/payments and immutable108 release
size/hash are not rewritten. No new free-payment mode or independent billing state.

## Focused checks

- Paid unit/CLI/canary/readiness/HTTP/backup selection includes the additional
  pair/grace-replay regressions; exact final selection receipt in PR.
- Packaged subscription/HTTP/boundary selection:75 PASS,15 conditional local skips
  (required fixture/runtime contexts are supplied by hosted repository gates).
- Isolated built panel, real PostgreSQL:102 PASS; Django checks and no-migration check
  PASS. The extra test proves seed_demo preserves registry bytes and immutable108
  metadata, with no119 ReleaseMetadata insertion.
- Real packaged operator `policy`, activate/grace/status/replay and HTTP archive paid
  module are executed in isolated subprocesses, not mocked source strings. Negative
  descriptor/hash/tie and old108 replay after119/expiry/revoke are covered.
- Overlay tests pin both input archive and old paid module, preserve the complete
  inventory and reject pin mismatches. Ordinary canary108 and CRL preconditions still
  reject119; no live canary is run.

## Actual serving baseline and minimal candidate

Read-only observation7 November12:41:56UTC: independent HTTP service active, actual
process argv resolves the pinned archive; Python3.14.4. No PartOf/BindsTo/RequiredBy
coupling. Existing serving archive:
`0fa13b0a92406c9d58043287e880b6533768d031f31e1de10059b9072eb6473e`;
paid module `207688fc4f4b6c151bba8887ba8d95a047ae831c9eddf023df41889e3005d014`.
Canonical count at that observation:1 subscription/4 events. These are not bank
payment counts or an authorization to alter the recipient's records.

Candidate HTTP SHA256 `4bcbd7ed0dcc756965f5eb60aa340c8d5d638513a0af64ca93b50affce86b7fb`;
operator SHA256 `1e833a9ada3b9b65b72dd187b4df3561511df2534b067b06ce5928075f72a227`.
Both contain paid module
`23abc32b16ed370033a898fb56c8b11d044153196379a4769d5bdfcffe8a2550`.
HTTP inventory: only `control/friends/paid_beta.py` changed, all35 other members
byte-identical. No full-feature-branch deployment or bootstrap/renewal replacement.
Operator `policy` reports exact descriptors, limit10, its archive SHA and executing
paid/admin module hashes without opening a registry. It is not a public HTTP route.

## Installation gate and rollback

Private bundle holds exact paths, effective units, inventories, registry/selectors,
rollback commands and receipts. Before installation take a consistent SQLite read-only
backup with `--include-paid`, verify integrity/FK and isolated canonical projections;
retain fingerprints for paid/identity tables. Never copy a live DB with ordinary cp.

Install immutable paid-only HTTP candidate and verified private operator, preserve
historical artifacts, retire legacy106 as the working operator path. Change only the
independent HTTP ExecStart using a dedicated override; daemon-reload and restart that
API only. Verify actual process/archive/module/policy, installed CLI canonical status,
and unchanged protected tables. Operational observations/challenges are separate from
paid/identity changes and must not be called ledger writes.

Update only archive path/SHA in external collector private subscriptions-source.json;
keep interpreter/known-hosts/HMAC and local panel data/volumes. Existing timer/importer
must produce a successful fresh observation from the new archive. Authenticated real
HTTP200/no-store `/subscriptions/` must show its hash, fresh observed_at and correct
latest attempt; a cached page/error is insufficient. The web process receives no DB,
SSH credentials or source pin. Synthetic108 web metadata need not be upgraded to119.

Rollback code, not the database: saved HTTP override/ExecStart + verified108 operator
and saved collector pin, then only HTTP reload/restart and fresh status/panel checks.
Never reinstate legacy106 as the working CLI, restore old paid data, or truncate events.
Already issued119 entitlements survive rollback; new119 writes must stop under108.
See [current operator guide](../operators/subscriptions.ru.md) for exact CLI semantics.

## Unchanged boundaries

No real payment/grace/expire/revoke, cohort/identity/period change or Android inputs.
No phone/APK/G4/renewal/cold-provisioning work. Decision B (AWG/TCP paid enforcement)
is not implemented. Client discovers the last corresponding event on subscription
open/Refresh; startup can deliver already saved events, no independent background fetch.
Prior physical outside-cohort result is not a physical paid-event result. Prior whitelist,
natural-expiry/UI identity change/mixed-network limits remain unchanged.
