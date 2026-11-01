# Deterministic physical gateway bootstrap

**Current work:** [FLEET-BOOTSTRAP-2](releases/2026-11-01-fleet-bootstrap-2.md) is explicitly
authorized for source preparation and one separately supplied disposable target. Production
RU/NL are excluded. The following FLEET-BOOTSTRAP-1 acceptance remains historical; its
synthetic archive is not a real VPN bundle and its live-mutation guard remains in place.

### Rehearsal source guard boundary

`fleet.permit` binds one independently pinned public IPv4, `fleet-rehearsal-*` instance,
provider/region, exact A/B bundle IDs, agent digest and bundle authority digest for at most
four hours. Catalog, production identity import, user and paid operations are always false.
`fleet.remote` uses a fixed SSH receiver and JSON stdin, no inventory shell commands or
password/agent/port forwarding. OpenSSL verifies the permit in memory before target upload;
the receiver checks actual local addresses and host keys, exact agent bytes/mode, then the
agent re-verifies the bundle. Missing ordinary OS tools may be installed only during
permitted enrollment/staging after those guards, never during read-only preflight.
Cryptography46.0.7/cffi2.1.1/pycparser3.0 are loaded from exact signed offline wheels for
CPython3.12, not from an unpinned target Python package. Their extracted inventory is
root-owned, immutable and rechecked on every agent invocation.

The operator reconstructs the agent and fixed receiver from the selected, signature-verified
bundle's `runtime/fleet/` members, checking `metadata/agent.json` and the permit hash again.
There is no working-tree agent fallback. An operator preflight repair therefore does not
silently replace an already enrolled node's exact agent or require reissuing its identity.
The read-only host probe accepts an explicitly empty port-absence set for post-enrollment
operations; enrollment/preflight still require the exact rehearsal ports to be free. Other
host checks remain mandatory, and live listener ownership is checked by local role health.

`status` first reads the durable journal and may add a separately permit-authorized read-only
host observation. Its fixed paths expose only ownership/modes/link counts and counts of
extended metadata; its fixed units expose whitelisted state/exit/restart fields. It never
reads config contents, environment values or raw journal messages. Unavailable diagnostics
do not discard the durable operation result. A failed start with successful rollback is not
an unknown outcome and must not be blindly replayed; localize the failure before a new intent.

`fleet.rehearsal_state` retains operation bindings, first failure and rollback receipts;
changed replay or interrupted operations are fenced. It requires a separately qualified
physical runtime implementation; synthetic callback tests are not VPN acceptance. Enrollment
uses a separate rehearsal scope/database and cannot consume synthetic proofs. The exact
verified `runtime/roles.py` entrypoint selects the bound role implementation; no fallback
to the old synthetic CLI is allowed.

The native-only [binding inventory](../fleet/inventory/deployable-gateway-v1.json) records
accepted binaries and public source/receipt hashes. The separate
[deployable inventory](../fleet/inventory/deployable-gateway-v2.json) admits awg, tcp, mesh,
profile-reader, publisher, snapshot, monitoring and load-monitor. Mailbox/chat-services,
production renewal/restricted-sync and registry/control-plane database are explicitly
disabled, not implicitly missing. Monitoring is new bound standard-library source:
read-only `127.0.0.1:19727/status`, no telemetry or mutation API. The receiver validates all signed
archive members before installing prerequisite OS packages; unsupported OS/architecture,
missing TUN, excluded local addresses and existing legacy Family Connect installs fail
before writes. Current exact test counts and remaining handoff gates are in the
[preparation receipt](releases/2026-11-01-fleet-bootstrap-2.receipt.json).

## Rehearsal operator handoff

Preparation and a later live rehearsal are distinct gates. Never select production RU/NL,
use the excluded hosts, publish a catalog, issue an invitation or perform a payment action.
The dated receipt is authoritative for the qualified source SHA, A/B IDs, public signer
fingerprint, archive/manifest/signature hashes and tests. Earlier private builds are
superseded attempts, not alternatives to the final bound pair.

`scripts/fleet-rehearsal prepare --source-commit COMMIT --artifact-root PRIVATE_INPUTS
--private-key PRIVATE_REHEARSAL_KEY --output NEW_PRIVATE_DIRECTORY` builds A and B twice.
Use canonical absolute paths without symlink ancestors. Private inputs include the exact
four native files, accepted source inventories, the282-file canonical MESH capsule,
upstream AWG/Xray source and pinned Python wheels. All are retained outside Git; only
safe receipts/hashes and source are committed. A new private Ed25519 bundle key is created
with0600 ownership if absent. Published synthetic signing seeds are explicitly rejected.
A/B differ only in `metadata/revision.json`; native/config/material/role contracts match.
The separately rebuilt operator-only probe is not a node role or a copied private identity.

Only after the ten private host inputs are supplied may an operator issue the four-hour
signed permit using `fleet.permit.sign`. A separate private rehearsal authority signs the
permit, enrollment/material bindings and external acceptance; Django receives public keys
only. Never reuse the product release signer. Record provider-console recovery availability
before host work, and independently pin the single-host known_hosts file.

Host commands share `--permit`, `--permit-key`, `--bundle` (the A-first/B-first four-file
directory), `--bundle-key`, `--known-hosts`, `--fingerprint`, `--host`, `--user`, `--instance`,
`--operation-id`; optionally `--ssh-key` or the confirmed SSH-agent context. All key options
are paths, never key values. A non-root SSH account needs noninteractive sudo for the fixed
receiver, not a password sent in chat. Every mutation rechecks permit/window/pins and a fresh
host preflight; there is no arbitrary command, force, insecure or skip-health option.

1. `plan`, `preflight`: read-only planning/host qualification; Ubuntu24.04/x86_64 only.
2. `enroll --authority-key PATH --operator-state PRIVATE_DIRECTORY`: node-local Ed25519
   ownership and separately generated X25519 encryption key; only public proofs leave it.
3. `deliver-materials --input PRIVATE_PLAN --create-materials --authority-key PATH
   --operator-state PRIVATE_DIRECTORY`: create fresh disposable transport material after
   enrollment; the private plan has `probe_identity` and `publisher_material` custody paths.
   The approved probe is opened only at this later live step, with `create=False`, never
   copied to the node. The publisher input must be a separately supplied disposable token.
   Alternatively deliver the already authenticated encrypted envelope with `--input PATH`.
4. `stage`: immutable `/opt/family-connect/releases/<bundle_id>/`; config/secrets remain in
   `/etc/family-connect/rehearsal/` and `/var/lib/family-connect-rehearsal/<instance_id>/`.
5. `start-verification`: validate config and units, atomically switch `current`, start roles,
   check local health, persist `AWAITING_EXTERNAL_ACCEPTANCE` with unpredictable nonce.
   Absence of an external receipt is not failure and does not trigger rollback.
6. `run-acceptance --authority-key PATH --input PRIVATE_HARNESS_CONFIG --output RECEIPT`:
   operator-only AWG/TCP/MESH probes outside the node, root required for the isolated AWG
   interface/policy route. Configuration names exact `native_directory`, `operator_probe`,
   `awg_peer`, `tcp_client`, `mesh_profile`, `probe_identity` paths. No identity/token bytes
   appear in argv, stdout, receipts or Django. Cleanup runs before the authority signs.
7. `complete-verification --input RECEIPT`: verify signature, instance/bundle/nonce/operation,
   <=300-second receipt lifetime, cleanup and repeated local-health digest. Only then
   `activate-local` is allowed. Local ACTIVE still does not publish anything.
8. Stage B, then `upgrade` → external acceptance → completion → activation. An injected
   local B failure restores A's pointer/config/owned firewall. A signed negative external
   B receipt also rolls back; an untrusted/absent receipt cannot fabricate a PASS.
   Explicit `rollback` to accepted A repeats the two-phase external gate.
9. A provider-console-controlled reboot is a later physical action; the CLI does not reboot
   hosts. `reboot-verify` requires a changed boot ID and unchanged enrollment, then fresh
   two-party verification. `drain`, `retire` stop only owned units, restore prior forwarding,
   delete only the owned nft table/sysctl file and remove disposable secret files.

`status` reads durable operation receipts. Any timeout, broken SSH channel, nonzero receiver
exit or malformed response is UNKNOWN until reconciled by exact operation ID/request binding.
Never blindly retry. If the remote journal is RUNNING, `drain --recover-operation-id ID`
uses the observed binding to stop, not rerun, that operation. A failed rollback/retirement
fences mutations as QUARANTINED: retain evidence and use the provider console for recovery
or disposal rather than bypassing guards. Old read-only releases remain available for audit.

Retirement fsyncs a final signed custody receipt before zero-overwrite/unlink of disposable
files. Overwrite cannot guarantee forensic erasure on SSD/COW/provider snapshots; destroy
the disposable VPS and provider snapshots after the final safe receipt. No production
backup, profile or identity is imported, overwritten or removed.

### Private publisher input and retained host capacity

The disposable publisher OAuth token must be supplied independently of production. A new
token cannot be inferred from SSH access, generated offline or replaced with a synthetic
fixture. Do not read/copy the working gateway's provider environment or use its token.

For the operator, create a separate test OAuth application through
[Yandex OAuth](https://oauth.yandex.ru/), granting only `telemost-api:conferences.create` for
the publisher's conference creation. Set its Redirect URI to
`https://oauth.yandex.ru/verification_code`, then open
`https://oauth.yandex.ru/authorize?response_type=token&client_id=YOUR_TEST_CLIENT_ID`
in the browser and approve that test application. Use its actual ClientID; do not change or
revoke the production application. See the official [Telemost access guide](https://yandex.ru/dev/telemost/doc/ru/access)
and [manual token instructions](https://yandex.ru/dev/id/doc/ru/tokens/debug-token).

From the repository root, run `python3 scripts/fleet-rehearsal-publisher-input` and paste the
test token at the hidden terminal prompt, not into chat, argv, an environment variable or a
shell command. The helper makes no network request and does not install/start anything.
It writes only ignored `state-client-build/fleet-bootstrap-2/publisher-input/publisher-material.json`
under0700 custody with0600 file permissions. Existing files, symlinks, noninteractive input
and echo fallback are rejected. Its safe JSON receipt deliberately reports credential
validity `NOT_CHECKED`; only later real publisher acceptance proves provider access.
Revoke this separate test application's access after retirement; never revoke production access.

The owner now requests keeping capacity for two Amsterdam servers. This does not turn a
four-hour rehearsal permit into production authorization or allow the temporary material to
be promoted. Finish the existing checkpoint's physical verification, rollback, reboot and
retirement gates first, with provider-backed cleanup/reprovisioning before permanent use.
Do not destroy the reserved VPS automatically or clone the first server's identity. The
working Amsterdam host remains excluded. Catalog/public client selection and a persistent
second gateway are not accepted merely because SSH, enrollment or local activation passes.
No new top-level PLAN ID is introduced here.

## Append-only rehearsal evidence

The operator exporter `scripts/fleet-rehearsal-evidence --kind KIND --source PRIVATE_JSON
--permit PRIVATE_PERMIT --authority-key PRIVATE_KEY --operation-id ID --bundle-id BUNDLE
--output SAFE_RECEIPT` projects only fixed safe fields and source hashes. Supported kinds:
artifact, permit, enrollment, intent, completion, local-health, external-acceptance, reboot,
retirement. Supply a distinct operation ID for each A/B artifact. For nested operation
evidence, select the local-health/external-acceptance object into a private input file first.
An intent is an intention, not proof of execution. UNKNOWN remains UNKNOWN.

Import with `python manage.py import_fleet_rehearsal --kind KIND --receipt SAFE_RECEIPT
--public-key AUTHORITY_PUBLIC_KEY`. Identical reimports are idempotent; changed same-event
receipts and UPDATE/DELETE are rejected by model checks and PostgreSQL append-only triggers.
The Russian summary shows provider/region, target hash (not raw IP), bundles, operation/state,
local/external role health, duration, rollback/reboot/retirement. The web process never executes
SSH, decrypts envelopes or holds signing/transport keys. It cannot issue users or payments.

## Source/container qualification

`scripts/qualify-fleet-rehearsal.py` is permitted only inside an isolated root Ubuntu24.04
container. Run it with network disabled and only namespace-local NET_ADMIN, read-only source
and package mounts, and a private output mount. It checks exact native help/version/Xray
config-test, signed A/B target reverification, offline wheels, rendered systemd units,
`nft -c`, neighboring-table preservation and owned-table rollback. It delivers synthetic
encrypted material into a fake root and exercises actual versioned filesystem installation,
two-phase signed synthetic acceptance, B failure→A, B success, explicit rollback and retirement.
Only command execution/service observations are isolated fixtures; no physical PASS is inferred.
Actual systemd starts, AWG handshake, TCP/MESH data planes and reboot persistence remain NOT_RUN.
The pinned base and test dependencies are in
[`scripts/fleet-rehearsal.Dockerfile`](../scripts/fleet-rehearsal.Dockerfile). Build using
a minimal context containing only that Dockerfile and `fleet/requirements.lock`, not
the repository's private state. Do not mount private signing keys or identity custody into
the qualification container; only the public bundle key, signed packages and safe source
are needed. Never replace `--network none` with host networking for this source gate.

## Historical FLEET-BOOTSTRAP-1 foundation

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

## Historical foundation handoff checklist

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
