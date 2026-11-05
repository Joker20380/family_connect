# Opt-in online runtime candidate

This is a separate source/runtime package, not a replacement for the accepted
maintenance API archive. Default quiesced operation and its approval rules are
unchanged. Source qualification does not authorize deployment or schedule changes.

Build from a committed revision with `python -m scripts.package_online_renewal
--ref <commit> --go <absolute-go-binary> --output <new-archive>`. The builder reads
only committed regular files; it builds the Linux/amd64 gateway with the selected
Go toolchain, readonly dependencies, no VCS/path/build-ID variability. The manifest
records the source, native inventory/toolchain and every package member checksum.
It contains the current `api.pyz`, closed `http.pyz`, gateway and renewal sources,
plus dependency lockfiles. It includes no configuration, authority keys, identities,
databases, permits or automatic activation. Extract into a root-owned mode0700
directory. Do not extract over an installed or previously accepted package.

## Node

Use the existing `python -E -s -B <package>/renewal/node.py --config <root-config>`
JSON RPC entrypoint and existing SSH authorization. All existing node/canonical
ProfileStore/issuer-custody fields remain required. The source inventory and API
hash must exactly match this package's manifest. Online additionally requires
`admission_mode: "all_activated"`, the exact two `gateway_ids`, `gateway_slot`, and:

- RU: `online: {"contract":"MESH_SAME_HOLDER_ONLINE_V1"}`.
- NL/NL2: the same object plus `reader_socket` (absolute protected Unix socket),
  `reader_uid` (service UID), `reader_executable_sha256` (manifest gateway SHA256).

The actual gateway uses `-publication-observer <reader_socket>` with its existing
canonical `-family-config` path. This is not a sidecar signing/authorization service.
The reader checks socket custody, SO_PEERCRED UID/PID, the allowlisted service's
MainPID and executable digest before and after its bounded query. The receipt
binds contract, gateway, profile hash and process-instance nonce. A loaded profile
receipt is not evidence of a READY provider, usable traffic or retained TCP.

`online/capabilities` reports package/API/native identities, membership, features
and the observed reader. Stopped gateways explicitly have no runtime receipt;
they cannot enter a new online renewal. Recovery may inspect stopped participants.
Absent opt-in retains `ONLINE_QUALIFICATION_ONLY`; the source-only qualification
flag is never set by these entrypoints. Fenced maintenance recovery cannot opt in.

## Controller

Use `python -E -s -B <package>/renewal/online_cli.py --config <root-config>
--operation <stable-operation-id> --mode <mode>`. Modes: `inspect` (default,
capabilities only), `online`, `resume`, `abort`, `emergency`. There is no timer or
implicit operation ID. Configuration is canonical JSON in a root-owned mode0600
file under a mode0700 directory, with exactly:

- `schema: 1`, `online: "MESH_SAME_HOLDER_ONLINE_V1"`;
- `state`: the existing private coordinator-state directory;
- `anchor`: base64 public trust anchor; `gateway_ids`: exact NL/NL2 identities;
- `schedule_seconds`: explicit lateness, 0–900;
- `ssh_routes`: exactly RU/NL/NL2 using the existing SshNode route contract
  (`key`, `known_hosts`, `target`, `command`). Each command is the existing seven
  arguments: Python, `-E`, `-s`, `-B`, absolute node entrypoint, `--config`, config.

All participants run in independent handlers over the ordinary bounded SSH RPC.
Capability/API/source/membership and actual-reader preflight precede controller
journal/owner writes. SSH120 remains120 seconds: the window is1395s plus lateness.
There is no reduced transport budget or changed production lifetime. Existing
single-writer locks, fenced durable COMMIT, publication, delivery gate and emergency
continuation implement the operation, not a second controller/signing database.

`emergency` without approval preserves the original COMMIT and returns the linked
quiesced request. `--outage-approval <private-file>` is allowed only in this mode;
the canonical object has `operation_id`, `expected_state_sha256`, `approved_at`,
`expires_at`, `approval: "OPERATOR_APPROVED_OUTAGE"`. It is the existing operator
authorization contract (maximum900s), not a new signing key. Bind the approval to
the returned current state; a subsequent revoke invalidates it. Do not manufacture
an approval from an obsolete request or edit the journal to bypass it. Recovery
reuses the continuation and start intents; emergency closes old TCP connections.

## Qualification boundary

Tests cover deterministic packaging/import closure/default-off, capability/membership
refusal, actual reader PID/executable, three independent SSH handlers, COMMIT/replay,
controller SIGKILL at six durable boundaries, and six RPC loss/corruption cases.
All use the packaged controller/node entrypoints, not a qualification constructor.
Set `FC_TEST_ONLINE_PACKAGE` to an immutable archive to qualify that exact package;
the reproducibility check exports its committed revision into a disposable clone.
The test image is defined in `tests/fixtures/online-runtime.Dockerfile`. Root checks
require an explicit network-none container, `FC_ONLINE_ISOLATED=1`, `FC_ONLINE_SSH=1`,
an absolute `FC_ONLINE_GO`, and a private `--basetemp=/run/fc-online-tests`.

The observer fixture holds seed creation at a local nonresponding proxy with a synthetic
unused token. The actual gateway exits at its unchanged15s provider timeout; a separate
test reproduces that limit and verifies fail-closed without journal/owner writes.
This is NOT a long-lived READY provider, useful traffic, G1–G4 or production acceptance.
It cannot establish emergency restart/new authorized Family TLS, retained connections
across leaf/CRL/lease bounds, or actual Android HTTP/cache/native delivery. Those remain
separate mandatory gates. Never extend production timeouts or use production credentials
to turn this narrow observer fixture into a false full-path acceptance.
