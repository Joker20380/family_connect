# 25 November 2026 — offline checkpoint signing workflow

Selected CONTROL-HA-20261123 / HA-02, existing **current-input trust** gate. This implements
the previously missing owner-facing review/sign/verify workflow for the
[forward checkpoint contract](2026-11-24-control-ha-forward-checkpoint.md). It is not a new
gate, production approval, signing-authority enrolment or deployment. No real key was created,
selected, read or registered; no actual checkpoint was signed. Installed/public versions unchanged.

## Implemented boundary

`scripts/control_ha_forward_signing.py` has three explicit offline commands:

- `review`: validate the canonical request, separately supplied request/public-key SHA256 pins,
  external minimum sequence and current time; emit a bounded summary, **not an approval**.
- `sign`: repeat those checks, require `--confirm-offline-only`, load an explicitly selected
  private32-byte Ed25519 seed and require its public key to equal the separately pinned key.
  Sign exactly the existing `DOMAIN + request`; write one new64-byte detached signature.
- `verify`: verify an explicitly pinned signature with the same independent request/key/floor
  inputs and freshness checks. This checks a signature, **not the bound recovery material**.

The wire protocol is unchanged: purpose
`family-connect/current-state-checkpoint/v1/isolated-qualification-only`, action
`QUALIFY_CURRENT_STATE_OFFLINE`. The pre-existing full checkpoint and encrypted archive
verifiers are unchanged. A generated signature was consumed successfully by the full verifier
using its synthetic source/history/recovery/publication materials and independently supplied
CRL/authority floors. Host activation, database import and live capture remain unauthorized.

There is no key generator, key discovery, first-use trust, network fetch, SSH/Docker dispatch,
database access, automatic replay-floor update or approval-registry mutation in the tool.
It cannot establish that the caller obtained its pins/floor independently. Every receipt keeps
`independent_approval_established`, `trust_enrolled`, `replay_floor_updated`,
`material_validation_performed`, `capture_permitted`, `database_import_authorized` and
`activation_authorized` false. A human confirmation flag cannot substitute for independent trust.

## Owner procedure — not executed on actual material

1. Separately approve/provision a **dedicated HA checkpoint signer** and retain its raw32-byte
   public key/fingerprint outside the recovery capsule and originating machine. Do not reuse
   release, control-root, issuer, gateway or client keys. Authority enrolment/key custody still
   requires the owner; this change does not fabricate it. No private key belongs in Git/CI/server.
2. Produce the canonical request with the existing `request_for` only for the intended captured
   material. Independently review/retain its exact SHA256 and the current durable sequence floor.
   Do not obtain trust pins or floors solely from the incoming request/bundle or a self-generated
   receipt. Old captures do not become fresh by changing their timestamps or recomputing pins.
3. On a trusted offline POSIX workstation, place the request and public key in private files.
   Use `review`, inspect the exact request/material bindings independently, then explicitly use
   `sign` only if this request is approved. The tool accepts only the declared offline scope.
4. Transfer only the request/signature and required nonsecret metadata, not the signing seed.
   Verify against the independently retained request/key pins, signature hash and replay floor.
5. Run the **existing full checkpoint/archive verifier** over the exact bound ciphertexts,
   history, sources, issuer, both publications, authorities and independently held floors/keys.
   Signature success alone is not offline material qualification, coherent capture or final DR.
   Maintain the durable replay floor in the independently approved custody workflow; this CLI
   neither advances it nor makes repeated verification/signing equivalent to fresh approval.

Example arguments below are placeholders, not real authority or checkpoint values. Supply
independently approved hashes/floor; never paste a private seed into argv or environment:

```sh
python -m scripts.control_ha_forward_signing review \
  --request /private/request.json --request-sha256 "$APPROVED_REQUEST_SHA256" \
  --trusted-key /private/ha-checkpoint.pub --trusted-key-sha256 "$TRUSTED_KEY_SHA256" \
  --minimum-sequence "$RETAINED_SEQUENCE"

python -m scripts.control_ha_forward_signing sign \
  --request /private/request.json --request-sha256 "$APPROVED_REQUEST_SHA256" \
  --trusted-key /private/ha-checkpoint.pub --trusted-key-sha256 "$TRUSTED_KEY_SHA256" \
  --minimum-sequence "$RETAINED_SEQUENCE" --key-file /private/ha-checkpoint.seed \
  --output /private/new-signature.bin --confirm-offline-only

python -m scripts.control_ha_forward_signing verify \
  --request /private/request.json --request-sha256 "$APPROVED_REQUEST_SHA256" \
  --trusted-key /private/ha-checkpoint.pub --trusted-key-sha256 "$TRUSTED_KEY_SHA256" \
  --minimum-sequence "$RETAINED_SEQUENCE" \
  --signature /private/new-signature.bin --signature-sha256 "$SIGNATURE_SHA256"
```

## File, clock and failure rules

Inputs are same-user0600 regular single-link files under a same-user0700 immediate parent.
Every path component opens descriptor-relative with no symlink following. Relative paths,
traversal, links, FIFO/devices/directories, oversized files, wrong ownership/permissions and
observed input replacement/mutation refuse. Request limit16KiB; public/seed exactly32 bytes,
signature exactly64. No normalization of noncanonical/duplicate JSON or repair of invalid input.

Signing rejects the request's issuer public key and the known `update-signing` path family.
This is not a detector of renamed/copied release keys; dedicated-key provenance remains an
independent owner obligation. The tool supports raw seeds, not PEM/vault decryption. Use it
only in the approved offline custody environment; core dumps are disabled, but Python memory
zeroization, protection against a compromised account and secure key provisioning are not claimed.

Sequence must exceed the externally supplied floor. Wall-clock time must be within the request's
existing validity window (at most one hour); the CLI has no time-override switch. Checks repeat
around signing/output. A trusted clock is still external. Requests are never extended or resigned
automatically. Outputs are exclusive0600 files, fsynced with their parent; no overwrite/cleanup.

Normal failure exits1 with only `FORWARD_SIGNING_REFUSED`, without paths, credentials or traceback.
If output fsync or the final freshness check fails, a complete/partial signature may already exist:
**treat issuance as uncertain**, preserve the file and independently reconcile it. Do not blindly
retry, change the output name or lower the floor. Readback verification establishes signature
validity, not prior fsync durability, authority enrolment or off-machine custody.

## Validation and rollback

Final focused suite started **25 November00:36:05.127UTC** (JUnit timezone+01:00):
**231 PASS,0 skips,54.91s**, including73 new signing checks. All26 distinct control/identity
lockfile pins match. Checks cover native CLI review/sign/verify, full-verifier interoperability,
scope/pin/key/floor/time rejection, file safety, input mutation, exclusive output, expiry during
signing, uncertain fsync and sanitized errors. All keys, signatures and capsules are synthetic.
Documentation: five files/1086 link targets/zero errors; clean whitespace. External URLs are
enumerated, not fetched. The documentation receipt is retained with the private test receipts.

```sh
python -m pytest -q tests/test_control_ha_forward_signing.py \
  tests/test_control_ha_forward_checkpoint.py tests/test_control_ha_forward_archive.py
```

| Evidence | SHA256 |
| --- | --- |
| Signing source | `ce3d0550951e46bc7ecaf16320b7f45b985a3f7b782250718a6ab6d8d4b0d2ab` |
| Signing tests | `af2c06082b8af92a128badb3dcf825a624d2bca8e91ba4d2cd68d643a895313c` |
| Sanitized final summary | `224330542a92cc722398c85e2b757ed44e8bb641e741223b7f2eb0a8edc9b1c3` |
| Final JUnit | `6e318adfeed285b3f36ccc7294e02a36c65c3de4db482e320cdc43a932efd92b` |

Private validation receipts remain under
`~/.local/share/family-connect/control-ha/20261125-forward-signing-*`, referenced by
`/tmp/fc-ha-forward-signing-current`. No private fixture/capsule/key is committed.

No working service, production key, registry, sequence floor, gate or source/config was changed.
Rollback is to stop using the new offline CLI; the old verifier/wire format and existing services
are untouched. Never erase signatures, lower floors or restore old product DBs as rollback.

The signing-tool code gap is closed. Actual independent signer/pin/floor custody and approval of
a **fresh coherent checkpoint** are still unperformed. Installed OWNER/RU/NL/manual/transport
participation, existing-work settlement, coherent capture and final independent recovery remain.
Working-NL changes are still outside permission; console namespace access remains unqualified.
Keep the already passed publication/overlay/cross-mount/replication evidence; no repeat stand,
new stage/ETA, live deployment or claim of HA-02 COMPLETE follows from these signatures.
