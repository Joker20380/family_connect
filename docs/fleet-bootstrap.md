# Deterministic physical gateway bootstrap

**Current work:** [FLEET-BOOTSTRAP-2](releases/2026-11-01-fleet-bootstrap-2.md) is explicitly
authorized for source preparation and one separately supplied disposable target. Production
RU/NL are excluded. The following FLEET-BOOTSTRAP-1 acceptance remains historical; its
synthetic archive is not a real VPN bundle and its live-mutation guard remains in place.

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
--key PUBLIC_KEY`. Keys are raw Ed25519; `fleet/requirements.lock` pins the existing
cryptography dependency and its dependencies. Python3.12+, zstd and OpenSSH client are
operator prerequisites. No production key is checked into Git. The simulation's explicitly
public test signing seeds are only valid for its synthetic trust domain.

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

## Reproduce the source checkpoint

From an exact committed checkout, with the dependencies installed in an isolated environment:

```sh
python3 -m pytest -q fleet/tests
python3 -m fleet.simulate --source-commit "$(git rev-parse HEAD)" --output SYNTHETIC_OUTPUT
```

OUTPUT must not already exist. It is private0700: only its sanitized `receipt.json` may be
committed after review. Node keys, enrollment DB, raw receipts and inventory stay private.
The command verifies every input against `git show` for that exact source, builds twice,
compares archive/manifest/signature/hash inventory byte-for-byte and runs the real CLI through
plan → preflight → stage → verify → activate → status → rollback → status. It generates a
fresh node identity and one-use synthetic enrollment, and destroys the disposable install root.
This bundle contains the complete bootstrap Python runtime, templates, dependency lock and
license; it does **not** contain the production AWG/TCP/MESH executable distribution.
Unit integration additionally exercises upgrade to a second bundle, exact predecessor rollback,
cancellation of an unactivated upgrade without disconnecting the predecessor, and failed
activation/rollback evidence. An unresolved rollback failure fences further mutations.

Equivalent individual commands use the same inventory, signature key and isolated root:

```sh
scripts/fleetctl plan --instance nl-test-001 --host 192.0.2.10 --inventory INVENTORY --bundle BUNDLE --public-key PUBLIC_KEY --dry-run
```

For preflight/stage/verify/activate, add `--sandbox-root TEMP_ROOT --operation-id UNIQUE_ID`.
Preflight takes `--host-report SYNTHETIC_HOST`; verify takes `--health-report SYNTHETIC_HEALTH`.
Both verify and activate take `--enrollment-receipt RECEIPT --enrollment-key AUTHORITY_PUBLIC_KEY`.
An already completed operation ID only replays the identical request's saved receipt; changed
parameters or an interrupted RUNNING operation fail closed. Do not invent PASS health reports
for real servers. The simulation intentionally labels all hook evidence synthetic.

## Django operator boundary

The existing console adds `fleet_console` models/migrations, `/fleet/`, Russian read-only admin,
and an intent form protected by explicit Django permissions and CSRF. PostgreSQL triggers make
artifact, enrollment-token, operation and health audit rows append-only. Completion creates a
new record linked to its immutable intent. Actual operation execution is never a web action.
`ServerObservation` is linked by optional health observation FK; existing snapshots and imports
are not rewritten. Production-readonly observations cannot satisfy synthetic activation gates.

In a separately initialized **local synthetic** console, use `import_fleet_synthetic` to import
a signature-verified initial DISCOVERED/NEW inventory (documentation-range IPs only), then
`fleet_enrollment_receipt` to accept signed node enrollment. The API must not receive the raw
enrollment token. `fleet_intent OPERATION_ID` exports a safe intent; pass its ID to the operator
CLI and import its receipt with `fleet_complete OPERATION_ID --operator OPERATOR --receipt RECEIPT`
(plus `--health REPORT` for verify). These commands neither issue user invitations nor call
the subscription/payment backend. See [console commands](../control_plane/README.md).

## Threat model and limitations

| Threat | Boundary |
| --- | --- |
| Archive substitution, traversal, links, duplicate/missing/extra members | Offline manifest signature; exact hashes/targets/modes and canonical bounded tar verification before staging |
| Wrong host or SSH interception | Independently accepted host-key fingerprint, strict checking, no passwords or forwarding, bounded explicit argv |
| State/identity copied from replaced instance | Fresh node-local key, one-use bound proof and signed receipt; journal/root instance binding |
| Stale/forged health or premature activation | Exact role inventory, freshness, instance/bundle binding and VERIFIED gate; synthetic reports never authorize live publication |
| Interrupted install or upgrade | Immutable version directories, fsync/atomic pointer, retained predecessor, durable operation ID and rollback-failure fence |
| Secret leakage | Slots outside releases,0600 node material, generic error codes, private evidence separate from Git; scanners supplement review, not replace it |
| Web privilege escalation into hosts | Read-only inventory plus audited intents; no SSH credential mounts or execution from Django |

The operator, signing authority and local filesystem owner are trusted. Root/DB-superuser
compromise is outside the append-only audit guarantee. Health reports are not remote attestation.
Test keys must never become production trust anchors. Compression reproducibility is verified
with the recorded toolchain; byte equality across different zstd versions is not asserted.
No automatic apt package selection, production role adapter, VPN credential issuance, physical
health probe, service restart or catalog publication is accepted here. Existing legacy role
hashes are observations, not complete redistributable/source-provenance qualification.
Symbolic root ownership maps to the current UID in the sandbox; real root/service-user ownership,
systemd hardening, firewall coexistence and reboot persistence remain live-rehearsal gates.

## Next: separately authorized FLEET-BOOTSTRAP-2

Do not start this procedure automatically, and never select existing RU/NL as its target.

1. Allocate one disposable Ubuntu24.04/x86_64 VM/VPS; record provider/region, resources and
   independently authenticated SSH fingerprint privately. No user identity, invitation, payment,
   production database or FLEET_MESH_PROBE_1 private material enters the bundle.
2. Bind each required real role binary/package to its accepted source/license/artifact receipt.
   Resolve the private role matrix's remaining provenance entries; reject unexplained drift.
   Review actual per-role argv, users, capabilities, persistent state, secret slots and port map.
3. Qualify the remote execution adapter and concrete role templates on that disposable target,
   retaining the existing source guard until explicit rehearsal authorization. No manual bypass
   of the current `live_rehearsal_required` guard or synthetic scope flag is acceptance.
4. Build twice, independently verify with the accepted signing public key, retain exact rollback
   assets, and run real read-only preflight. Unsupported OS/architecture/TUN/time/ports fails
   before writes. Ubuntu26.04 remains rejected until separate package/runtime compatibility proof.
5. Run bounded SSH stage and fresh local-node enrollment; validate config/secrets; execute real
   systemd, firewall/NAT and all enabled-role health adapters. Verify staged service operation
   before any local ACTIVE transition; publication is still a separate explicit gate.
6. Measure upgrade, injected failure and rollback, reboot persistence, listener ownership,
   material freshness and resource release. Run the privately bound MESH probe only under that
   checkpoint's permission; filesystem simulation is not handshake/DNS/HTTPS/NL-egress evidence.
7. Preserve sanitized receipts, stop disposable services and retire/delete only the test target.
   Stop on actual health/rollback/identity failure; do not expand cohort or modify RU/NL catalogs.

Targets (not measured): preflight≤5 minutes, stage≤5, verification≤10, unattended work≤30.
This checkpoint makes no claim that these times or unattended production installation were met.
