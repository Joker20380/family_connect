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

## Operator commands and isolation

`python3 -m fleet` (or `scripts/fleetctl`) exposes plan/preflight/stage/verify/activate/
rollback/status/drain/quarantine. Common arguments: `--inventory`, `--instance`, `--bundle`,
`--public-key`. Inventory artifact hashes, signature and source binding must all match.
`--dry-run` performs no filesystem or remote writes. Mutations require `--sandbox-root`
inside an isolated temporary directory and a synthetic signed bundle; live SSH mutation
unconditionally fails `live_rehearsal_required`. No web request can override this boundary.

Remote **read-only** preflight additionally needs an independently accepted `--fingerprint`,
a single-host `--known-hosts` file and explicit `--ports`. SSH disables password/interactive
authentication, config/proxy/forwarding/multiplexing and uses the operator's SSH agent/key.
No blind ssh-keyscan trust. User data travels as JSON stdin, not interpolated shell code.
Ubuntu26.04, other architectures, missing TUN, time sync, ports, resolver/HTTPS or reboot
checks fail before writes. Test `--host-report` inputs are synthetic only, not remote proof.

Inside the sandbox the layout mirrors `/opt/family-connect/releases/<id>`, `current`,
`/etc/family-connect`, `/var/lib/family-connect` and `/run/family-connect`. Immutable releases
are fsynced before rename; `current` is replaced atomically. State and `.slot` secrets remain
outside releases. Versioned configuration does not overwrite the running predecessor.
The first rollback target is the explicitly empty, inactive bootstrap state; upgrades retain
their exact accepted predecessor. Interrupted RUNNING journals fence replay for operator
reconciliation, not blind re-execution. Completed operation IDs replay their saved receipts.
Activation failure preserves first cause and restores the previous pointer. Rollback retains
both releases and returns the old candidate to STAGED for fresh health, not assumed ACTIVE.
All of this is a filesystem simulation; no systemd service or firewall rule is installed.

## Enrollment and health

`fleet.enrollment.EnrollmentStore` is the local synthetic authority:256-bit random token,
hash-only persistence, maximum600s TTL, cancellation, atomic one-use consumption and immutable
audit. `issue()` returns the raw value exactly once; never put it in argv/logs/inventory.
The node calls `generate_node_key()` locally (exclusive0600 creation), signs the binding and
challenge with its own Ed25519 key, and sends only public identity and proof. Every instance,
gateway, bundle, provider/region, public-IP and role binding is checked. No public enrollment
endpoint or production credential issuance exists. AWG/REALITY/restricted/monitoring material
are future issuers behind symbolic slots, not inherited physical identities or journals.

`fleet.health` requires every host/enabled-role hook, exact instance/bundle binding and fresh
observations before VERIFIED. MESH includes the FLEET_MESH_PROBE_1 hook but never its private
identity. Test hooks and file-supplied reports prove contract enforcement, not VPN acceptance.
Templates are rendered from validated roles/interfaces/subnets; they are inert rehearsal
inputs, not substitutes for reviewed per-role runtime argv/capabilities or firewall policy.
