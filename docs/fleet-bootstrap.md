# Deterministic physical gateway bootstrap

FLEET-BOOTSTRAP-1 is source/synthetic only. No production transport issuance,
catalog publication, paid operation or SSH mutation is authorized by this foundation.
See the [checkpoint](releases/2026-11-01-fleet-bootstrap-1.md).

Logical gateways own country/routing intent. Physical instances own deployment identity,
bundle version, health and operation history. Replacements never inherit physical keys,
renewal/rollback journals, pending operations or short-lived transport material.

State graph: DISCOVERED → PREFLIGHTED → STAGED → VERIFIED → ACTIVE, with DRAINING,
QUARANTINED, FAILED and RETIRED. STAGED cannot become ACTIVE directly. Local synthetic
ACTIVE is not client-visible publication. The [strict contract](../fleet/schemas/README.md)
is independent of existing client leases, subscription and payment state machines.

## Signed bundle v1

`python3 -m fleet.bundle build --source-root SOURCE --spec SPEC --key EXTERNAL_KEY
--directory OUTPUT` emits `fc-gateway-<id>.tar.zst`, `manifest.json`, `manifest.sig`
and `sha256.json`. Verification uses `python3 -m fleet.bundle verify --directory OUTPUT
--key PUBLIC_KEY`. Keys are raw Ed25519; use the existing cryptography dependency from
the control-plane lockfile, and an installed zstd executable. No key is checked into Git.

The specification pins every input hash and names relative sources, output paths, read-only
modes, restart groups and symbolic secret slots. A signed manifest binds the exact source
commit, sorted member inventory, target paths and compressed archive hash. The bundle ID is
the digest of canonical core metadata, avoiding a circular archive/manifest hash dependency.
Ed25519 signatures and tar/zstd output are deterministic; tar uid/gid/mtime are normalized.
Verification reconstructs the canonical tar stream: duplicate/extra/missing members, links,
path traversal, altered modes and even trailing metadata are rejected before extraction.
Member and aggregate bounds also apply to decompression. Secrets/state files are forbidden;
the operator must additionally review pinned inputs because scanning is not proof of absence.
Only Ubuntu24.04/x86_64 is admitted;26.04 is intentionally unqualified and rejected.

The synthetic fixture is **not** an accepted production VPN executable. Real gateway inputs
must be bound to accepted source/artifact receipts before the separate live rehearsal.
