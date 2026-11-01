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
- Django models/UI and final combined acceptance: pending.
- Final synthetic acceptance and rehearsal runbook: pending.

## Next boundary

FLEET-BOOTSTRAP-2 requires a separately authorized disposable VM/VPS rehearsal.
It is not started automatically. Timing targets are unmeasured, not acceptance claims.
