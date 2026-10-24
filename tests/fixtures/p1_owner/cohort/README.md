# Confirmed three-device P1 policy —23 October2026

This fixture continues exact gateway3a08, not the older root carrier checkout.
No new APK, wire/auth/window/retry change. The owner confirmed owner plus the two
existing tester Support IDs. Private bindings and raw reports stay outside Git.

- `readback.py`: RU read-only mapping; distinguishes device hash from certificate
  signing-key hash. Checks activation/revocation and owner binding, exports no keys.
- `build.py`: reproduces3a08 byte-identically, freezes inventory, applies only the
  bounded group selector/helper plus tests, runs policy and five package race tests,
  builds a515. Shared bootstrap timestamp vector is copied outside the carrier tree.
  Initial run lacked that vector; its failure is retained and the bootstrap-only
  retry passes. Do not rerun build into the existing immutable capsule.
- `gateway-group.patch`: exact reviewed delta; absent group preserves old policy,
  group max3/max99 bytes, canonical unique hashes including owner, P1 only; file
  protection unchanged. Diagnostic single-owner selector is not broadened.
- `prepare_transition.py`: derives existing locked, guarded stage/deploy/rollback
  and readiness tools; no implicit deployment. Applied once with existing RU/NL
  renewal locks and explicit shared-restart approval. Read current receipts first.
- `policy.py apply|readback`: guarded atomic exact-three next-session policy;
  apply intent forbids blind retry. Neither service admission nor USB permission.
- `probe.py <unique-label> <fresh-gateway-directory>`: only1KiB through the existing
  Wi-Fi/TUN meter with the deployed a515 hash,106 and matched both-end profile pins.
  Shares the existing32MiB continuation ledger; no default bulk mode.

Accepted a515 hash and source inventory are in the private build receipt. Same
signed106 remains the field file; Volgograd's supplied positive cellular96 result
does not establish106/P1. See the dated report for failures, timings and limitations.
