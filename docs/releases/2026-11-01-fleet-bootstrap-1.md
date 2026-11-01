# FLEET-BOOTSTRAP-1 — deterministic physical gateway bootstrap

Scope: **SOURCE / SYNTHETIC ONLY**, owner-authorized1 November2026.
**FLEET_BOOTSTRAP_1_SOURCE_READY — synthetic bootstrap foundation, not a production
VPN distribution or live provisioning acceptance.**
Base main: `927c9a492166ec9b805b01b86be4e270ad126feb`.

Production writes, user invitations, paid events and phone actions: **0**.
Public109/Android sequence4, gateway catalog4, paid baseline108, entitlement,
ledger1/4, cohort1/10 and revenue0 preserved. Old NL FENCED; replacement NL ACTIVE.
Owner109 outcome remains OWNER109_TARGETED_AUTO_AWG_OWNER_PASS_SERVER_TX_RETAINED;
no further server-TX investigation or owner acceptance is part of this checkpoint.

## Read-only inventory

Actual NL and RU unit/effective-argv/file hashes, listeners, OS/package inventory,
firewall/sysctl and timer observations are retained privately. No runtime files are
copied into Git. The public role inventory exposes symbolic roles and public digests.
Existing restricted publisher is integrated into the gateway; renewal and snapshot
readers have separate state. A physical replacement must not import their journals,
temporary credentials, expired leafs or short-lived directories from its predecessor.
The existing client lease engine is not reused as a physical-instance state machine.

## Source checkpoints

- Strict fleet schemas/state graph:13 focused tests PASS. No live transition executed.
- Bundle/signature:35 combined contract/bundle tests PASS, including two byte-identical
  archives/manifests/signatures/hash inventories, traversal/link/duplicate/mode/target and
  signed-malicious archive rejection. Explicit generated test key only; no live signing key.
- CLI/atomic installer and enrollment implemented: isolated temporary roots only, explicit
  SSH fingerprint/read-only host probe, live mutation closed; atomic staging/pointer swaps,
  exact previous-bundle rollback, durable operation fencing and generated node identity.
  One-use enrollment uses hash-only tokens/600s TTL and possession proofs; no user invitations.
  Combined source/unit tests:67 PASS, including unsupported-host-before-writes, dry-run,
  stage replay, verified activation, failed activation evidence, upgrade rollback, all-role
  health binding, SSH fingerprint, enrollment expiry/cancel/replay and identity binding.
- Django fleet models, Russian read-only admin and operator intents implemented. The web
  process cannot execute SSH; append-only completion/enrollment receipts are imported by
  the separate operator. Signed enrollment possession is required before activation.
  PostgreSQL audit triggers reject update/delete, including queryset bypass attempts.
  Existing ServerObservation snapshots remain intact with optional instance-health links.
  Disposable container/PostgreSQL acceptance:199 PASS (128 console +71 fleet), no skips;
  Django check and migration drift PASS.33 existing-style static-directory test warnings;
  initial new-template test setup was repaired without changing production static policy.
- Final source hardening: parent traversal cannot escape the temporary install root;
  silent preflight commands use exit status; SQLite enrollment connections close promptly;
  concurrent enrollment accepts one proof only. Upgrade cancellation preserves the running
  predecessor; failed rollback retains the first failure and fences further writes.
  Fleet79 PASS on host and disposable Ubuntu24.04/Python3.12 container; no skips.
  Existing focused paid/backend/canary/package tests170 PASS with the unchanged control and
  identity locks in an isolated Python3.13 container. Initial host missing-RNS and copied
  harness missing-module/git prerequisites were corrected; no backend/test gate was weakened.
- Final combined console/fleet rerun:206 PASS,1 unrelated existing failure,33 static-directory
  warnings. `test_legacy_12_to_50_preserves_identities_and_paid_events` reaches the unchanged
  synthetic seeder's bare UUID invite hash: a UUID starting `fc` is interpreted as an `FC`
  invitation prefix, leaving30 rather than32 hex digits. No fleet test failed. The earlier
  full199 PASS is retained, not substituted for this latest result. No retry-until-green,
  test exclusion or production/paid backend correction is made in this checkpoint.
- Exact-source end-to-end artifact receipt PASS: two byte-identical builds; real CLI
  plan/preflight/stage/verify/activate/status/rollback in a disposable temporary root,
  fresh node identity/possession/signed receipt, all40 synthetic health checks for11 roles.
  Architecture, threat model, operator flow and bounded FLEET-BOOTSTRAP-2 procedure documented.

## Frozen source and reproducible artifact

Artifact source: `a3fc3bf1c11a686ea444ad36d576c05ac5e24810`, pushed and remote-verified.
Earlier coherent source checkpoints: `8d8823f`, `bd05636`, `446297d`, `035a6de`.
Later receipt/documentation commits do not change this exact build input.

| Evidence | Value |
| --- | --- |
| Bundle | `gw-074b2076b9ed20bba1c107091f0d08e6` |
| Archive SHA256 | `f2f218df82c3c84e9f82cc14364ff30feb75281e73fa37f1c40b245ef6b18ec2` |
| Signed manifest SHA256 | `451a4161e6dcd2d9db7b2aa5cb76832b1730eccd8c49ca0bdfb80e4803c2d4bd` |
| Hash inventory SHA256 | `81d85d1ec72dc959b1b08a877065b2655f9d84acbfd39958a874fe55e911f5b7` |
| Signature-file SHA256 | `13f975ea89ef417733dc22c7b50182d359c66169d4ff6728fcffca1a6f4a2e18` |
| Toolchain | Python3.14.4, cryptography46.0.7, zstd1.5.7 |
| Bundle inventory |18 exact bootstrap source/template/lock/license members; no VPN keys/material or production journals |
| Target contract | Ubuntu24.04/x86_64; Ubuntu26.04 rejected/unqualified |
| Independent userland simulation | Disposable Ubuntu24.04/Python3.12 container;79 fleet tests PASS |
| Live data plane / production publication | NOT_RUN |

[Sanitized acceptance receipt](2026-11-01-fleet-bootstrap-1.receipt.json) and
[signed manifest evidence](2026-11-01-fleet-bootstrap-1.manifest-receipt.json) are public.
The latter is an envelope: verify its signature over `fleet.contracts.canonical(manifest)`,
not over the human-readable receipt file's bytes. It preserves the exact18-member inventory.
Archives, node keys, enrollment DB and raw operation/host observations remain private/ignored.
The signing key is an explicitly public synthetic test fixture, never a production anchor.

## Acceptance boundary and retained limitations

New fleet source tests79 PASS, Django fleet tests10 PASS, existing focused paid/backend/canary
and package tests170 PASS; migration drift NONE and Django check PASS. The broader console
rerun has the one unchanged legacy synthetic-seeder failure described above, not a clean full
suite. No test exclusion, weakened assertion or retry-until-green is used to conceal it.

Only the **bootstrap source bundle** is qualified. Real VPN binaries/package lock/provenance,
per-role service/firewall adapters, root/service-user mapping, remote installation, physical
health and reboot behavior are not qualified by these filesystem tests. SSH mutation remains
closed; only explicit read-only preflight exists. The runbook lists those live-rehearsal entry
gates and the unbound legacy-role provenance honestly. This is not a measured≤30-minute
production deployment, a catalog cutover or permission to reuse production credentials.

No Android, gateway catalog or production backend source changes. Public109/sequence4,
catalog4, paid baseline108, entitlement, ledger1/4, cohort1/10, revenue0, old-NL fencing and
replacement-NL routing are unchanged by this checkpoint. No paid migrations run on production.

Final guards: strict JSON, public manifest signature and all18 source-member digests PASS;
indexed Markdown480 local links/anchors checked with0 errors; public-source/privacy guard0
blocked files; staged scope and `git diff --check` PASS. Only the new current-checkpoint blocks
of STATUS/PLAN were staged; unrelated local owner changes remain unstaged. Disposable test
PostgreSQL/container network removed; production containers and normal schedules untouched.

## Next boundary

FLEET-BOOTSTRAP-2 requires a separately authorized disposable VM/VPS rehearsal.
It is not started automatically. Timing targets are unmeasured, not acceptance claims.
