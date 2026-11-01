# FLEET-BOOTSTRAP-2 — compatible physical NL assignment

The owner authorizes the implementation and subsequent production admission, explicitly for
Android, Linux and Windows. This continues the existing checkpoint; no new top-level PLAN ID
is created. This report describes a source transition, not a completed production deployment.

## Compatibility and scope

The earlier diagnosis that a third entry cannot be appended to schema2 remains correct.
Instead, each authenticated device receives one offline-signed RU/NL catalog bound to its
physical NL assignment. Catalog schema, public anchor, proof, response fields, private
address ranges and country selectors remain unchanged. No validator is weakened and no
client runtime binary is changed. This is server-side assignment, not a new two-NL UI selector.

- Existing devices are seeded to the exact previous catalog in one SQLite transaction.
- Devices first assigned after installation receive the explicitly admitted catalog. They
  stay on that physical node, even after a later admission-policy change.
- RU and NL configuration requests for a device use the **same** signed catalog and floor.
  All variants retain byte-equivalent RU templates. Existing RU registrations are unchanged.
- Each catalog has a distinct sequence. Explicit movement uses a higher signed sequence;
  returning to the first node requires a newer rollback catalog, never a lower client floor.
- These are AWG/TCP assignments. They do not issue entitlements, revoke peers, interrupt
  existing sessions, reroute MESH or extend a rehearsal permit. The existing MESH route and
  production renewal controller are unchanged. **Second-node MESH/renewal admission is not
  implemented by this source transition and remains a separate required production gate.**
- Rehearsal retirement remains terminal. No temporary role, key, peer, publisher credential
  or expiring certificate has been promoted into a permanent production service.

## Implementation boundary

[Routing implementation](../../control/friends/gateway_routing.py) loads a root-owned private
policy directory only after a corresponding DB transaction enables it. With no routing state,
the unchanged legacy catalog path remains active. Once enabled, missing/corrupt material
fails closed rather than silently routing an assigned device to the old NL.

The immutable policy is addressed by SHA256 and contains `schema`, `generation`, `legacy`,
`admit` and `catalogs`. Each catalog entry contains only `node` and `sha256`; it supplies no
path, command or shell arguments. Files under `gateway-routing/` are `<digest>.policy.json`,
`<digest>.catalog.json` and `anchor.pub`. The directory is0700 and files are0600, owned by
the process owner (root in production). Symlinks, hardlinks, unexpected file types, invalid
signatures, hash mismatches, duplicate sequences and inconsistent node/host bindings are rejected.
Installation additionally binds the exact existing `catalog.json`, not a substitute baseline.

Assignments and operation evidence commit together with SQLite synchronous FULL. Operation
IDs reject changed replays. Evidence has UPDATE/DELETE rejection triggers. Policy replacement
retains every referenced catalog and cannot implicitly reassign devices. Neither policy nor
catalog bytes contain client private keys. Safe receipts contain counts, node labels, hashes
and operation IDs, not device identifiers, identities, keys or TCP credentials.

The [HTTP artifact](../../deploy/friends/access-api.py) includes the routing module through
its [closed inventory](../../deploy/friends/restricted/http-runtime-files.json). Device proof
verification still precedes selection and registration. The fixed SSH command and strict
known-hosts check remain; no arbitrary remote command is introduced. No HTTP administration
endpoint exists. The root-only local CLI adds `--gateway-routing-request /absolute/private.json`:

| Action | Required fields in addition to `schema:1, action` |
| --- | --- |
| status | None; read-only, explicitly reports data-plane acceptance NOT_CHECKED |
| install | operation_id, policy_sha256, legacy_sha256 |
| replace-policy | operation_id, policy_sha256, previous_policy_sha256 |
| assign | operation_id, policy_sha256, device, expected, destination |

The request file must have a0700 parent and be a0600 regular single-link file. Secret values
or identifiers are not passed as process arguments. The CLI accepts neither a command nor
an SSH path. `expected` and `destination` are catalog hashes, not user-supplied addresses.
The CLI is a local DB operation, **not** a deployment, health, signature-authority or permit
bypass. Deployment must independently qualify the target, its permanent material and services
before routing installation or reassignment. Root CLI receipts cannot assert data-plane PASS.

## Qualification

[Public synthetic vectors](../../tests/vectors/friends-multinode-v2.json) use documentation-only
IPs and a deterministic test-only signer, never the production or rehearsal private signer.
The unchanged Python, Android Java and Windows C# verifiers each accept both physical nodes
and a forward-only return catalog, and reject lower sequence values.

- Python routing/client/HTTP/owner/store suite:204 PASS,14 existing conditional integration
  skips (nginx matrix and separately supplied restricted-sync archive),0 failures/errors.
  New routing tests:46 PASS, no skips. Production host access is not part of this run.
- Android JVM contour:174 tests PASS,0 skipped/failures/errors, including the new common vectors.
- Windows C# core on Linux: existing conformance checks and3 assigned catalogs +3 downgrade
  refusals PASS. The two existing Windows DPAPI suites skip on Linux; this is not native
  Windows/DPAPI or Windows UI acceptance. Hosted Windows verification remains pending.
- The isolated HTTP test uses real device proofs and an actual loopback HTTP listener, but a
  synthetic registration executor. Both target choices, proof replay rejection, credential-free
  argv and absence of an admin HTTP route are checked; no SSH connection is made.
- Failure-injected DB commits roll back both assignment and journal; changed operation replays,
  revoked/unregistered devices and file/signature corruption are rejected.
- The closed HTTP package builds twice byte-identically, with33 packaged source/output members.
  Archive SHA256: `6e12d8321b9bf054f2875867a5e62ab0ec7c3536cd8f60a96a01c0d2375103a0`.
  Both copies remain in ignored private artifact storage; neither has been deployed.
- Staged scope, strict changed JSON and whitespace PASS;501 local Markdown links across the
  four changed documents PASS; public-source guard3360 entries,0 blocked files.

The first operator-image run lacked httpx; rerunning under the existing control/identity-lock
image resolved the environment mismatch. A new pytest parameter initially used the reserved
name `request`; it was corrected, not skipped. The Android copy harness was corrected to use
the invoking UID and ordinary copies with dropped capabilities, without weakening test gates.

## Production gate and preserved state

No live SSH or production mutation was performed for this transition. The new VPS host key
is still owner-accepted TOFU, not independently compared with the provider console. The owner
was asked to run `ssh-keygen -lf /etc/ssh/ssh_host_rsa_key.pub -E sha256` **through VNC**, not
the same SSH channel, and provide only its public fingerprint. No password is requested.

Production RU/NL writes0; catalog publications0; invitations0; paid events0; phone actions0.
Public Android109/sequence4, gateway catalog4, paid baseline108, entitlement, ledger1/4,
cohort1/10 and revenue0 are unchanged. No production-ready or fully deployed second-NL claim
is made. The completed physical rehearsal does not substitute for permanent-node admission.
