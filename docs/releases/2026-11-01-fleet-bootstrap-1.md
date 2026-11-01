# FLEET-BOOTSTRAP-1 — deterministic physical gateway bootstrap

Scope: **SOURCE / SYNTHETIC ONLY**, owner-authorized1 November2026. IN_PROGRESS.
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
- Exact-source end-to-end artifact receipt: pending the committed harness execution.
  Architecture, threat model, operator flow and bounded FLEET-BOOTSTRAP-2 procedure documented.

## Next boundary

FLEET-BOOTSTRAP-2 requires a separately authorized disposable VM/VPS rehearsal.
It is not started automatically. Timing targets are unmeasured, not acceptance claims.
