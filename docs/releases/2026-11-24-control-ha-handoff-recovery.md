# 24 November 2026 — encrypted recovery of retained handoff authority

## Scope

Continuation of HA-02, not another stage. The preceding49-table importer and replication
rehearsal retained handoff history/floors, but the encrypted recovery reader still only
accepted the29-table source schema. Consequently its independently pinned forward archive
could not carry the recognized installed schema. This source change closes that format
integration gap; it does not capture production data or establish live authorization.

## Recovery contract

The explicit `seal_handoff` entry point in
[recovery bundle](../../scripts/control_ha_recovery_bundle.py) uses a distinct v2 header,
purpose and AES-GCM associated data. The reader recognizes only v1 and this exact closed-
handoff profile. Its independently supplied ciphertext/checkpoint/anchor/snapshot pins
remain mandatory. The original `seal` still emits v1 and rejects the overlay; v2 rejects
the old-only schema, unknown DDL, unsettled operations, missing security floors and
inconsistent history. No row or table is dropped to get through the importer.

After decryption, v2 invokes the same strict installed-schema/handoff validator and the
existing issuer-key, signed CRL, directory and referral-secret checks. Its canonical
fingerprint binds both retained rows and v2 provenance. Header/content downgrade, a
recomputed ciphertext hash without the correct key, and a mismatched snapshot fail.

The existing receiver/maintenance and signed forward-archive paths now read this profile
through the common verified reader. No new permissive flag or approval authority is
introduced. Forward request signature, independent trusted public key/request digest,
sequence/CRL/delegation floors, expiration, source bytes and both publications are still
required. An offline qualification signature does not authorize a database import or
host resume. The five imported PG tables remain immutable recovery retention, not a
new operational handoff writer.

## Verification

**Isolated encrypted recovery PASS; HA-02 overall is not complete.**
Private evidence: `/tmp/fc-control-ha-20261124/handoff-recovery/run-4/`.

-555 contracts PASS,0 failures/errors/skips,108.345 seconds, including27 new checks.
  The selection covers v1/v2 bundles, handoff import, current audit, signed forward
  checkpoint/archive, external roles, receivers and bounded maintenance.
-A fresh isolated Python process reads only the encrypted forward archive plus external
  keys/pins/floors, after removal of its complete synthetic source directory. It verifies
  the signed request and imports49 PG tables with exactly retained handoff counts1/2/1/1/1.
  This laboratory import is not permission conferred by the offline signature.
-The native lifecycle removes the original source fixture before recovery, reconstructs
  issuer/referral authority from the bundle, and restores four stores plus38 artifacts
  across eight roles. PG17.11 crash/restart and independent disposable-target restore
  preserve49 tables; post-restore product writes produce95 acknowledged rows. The old
  dump and repeated old import refuse; the current dump and consumed-proof rejection pass.
-Aliases/admission, allocation uniqueness/replay, sender/routing state, receiver lease/
  denial floors and three bounded maintenance journals retain their semantic checks.
  Wrapping key and independent checkpoint remain externally retained in this laboratory,
  not recovered from an independently operated production custodian.
-Owned-container cleanup PASS. Product versions and deployment state unchanged.

Receipt SHA256: `7f9f80123761d9f56d83f42c10b0d530162881ca69d8726ddb2a21584615c98a`.
JUnit SHA256: `0ec93c8143675ea7b27bcad4e0e69725de7f901cd825b89c9679782d5d902f99`.
Earlier runs1–3 remain private failed evidence: fixture scope assumptions, old-profile
external fixture creation and one FD-limit error in the combined suite. The final run
uses the explicit installed-profile fixture factories and a process-local soft FD limit
of4096 (previously1024). No server limits changed, tests skipped or validators weakened.

The owned rehearsal entry point is:

```sh
ulimit -n 4096
python -m scripts.control_ha_handoff_rehearsal --encrypted --workdir /tmp/fc-ha-handoff-recovery-new
```

It creates only labelled disposable laboratory resources. The unencrypted retention-only
entry point remains available without `--encrypted`; neither command reads live stores.

## Deployment, rollback and remaining gates

No server/service/container policy, public artifact, catalog, installer or product version
changes. No production rollout. Older readers cannot read v2; preserve the new source
revision with any v2 laboratory capsule. Never “roll back” by removing handoff tables or
floors or by silently replacing a v2 capsule with an older v1 snapshot. Source-only
rollback disables the new experimental entry point; it does not alter live data.

HA-02 remains **IN_PROGRESS**. Synthetic source-removed restoration does not establish
independent off-node custody of actual keys, actual-current approval, a coherent live
capture/writer barrier, OWNER panel recovery or post-capture production DR. The owner
decision about the reviewed limited live-capture/current-checkpoint path is still pending;
the earlier development-only/no-server-change boundary remains in force. No authority
key was registered and no live writer was stopped. HA-03..05 are not selected.
