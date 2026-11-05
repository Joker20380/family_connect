# Opt-in online runtime candidate

This is a separate source/runtime package, not a replacement for the accepted
maintenance API archive. Default quiesced operation and its approval rules are
unchanged. Source qualification does not authorize deployment or schedule changes.

The Android `fc_local_core` qualification build is a separate x86_64 artifact, never
the release native library. Its build-tagged connector reuses `wholedevice` bootstrap,
Family TLS/mux and credential maintenance through protected loopback packet sockets.
Normal Android builds retain Telemost and exclude the qualification dependency; the
release payload verifier rejects the local provider/tag/diagnostic markers. A native
build or shared-runtime test alone does not qualify Android HTTP/cache/owner delivery.

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

After both NL publications, `online/confirm` re-reads the serving PID/UID/executable
and profile under the existing node/profile locks before RU can publish delivery-ready.
A cached receipt from a dead/replaced process is insufficient; replacement enters the
linked emergency path and never silently claims continuity. A stopped reader after
COMMIT also enters emergency, remaining stopped until approved recovery starts it.
Participants must advertise `pre-delivery-runtime-confirmation`; mixed packages fail
the existing source/capability check. Confirmation adds no signer, writer or timer.

The remaining budget is checked again after read-only inspection, before journal/owner
writes. The eight bounded RPC rounds are acquire, prepare, stage, decide, NL publish,
NL confirmation, RU delivery publish and **parallel** participant completion. Completion
reconciles the same durable ledgers after lost responses/partial cleanup. SSH remains120s
and the eligibility contract remains8×120+435=1395s plus scheduling lateness. No timeout,
TTL, security clock or mandatory gate is relaxed to fit the added readback.

`emergency` without approval preserves the original COMMIT and returns the linked
quiesced request. `--outage-approval <private-file>` is allowed only in this mode;
the canonical object has `operation_id`, `expected_state_sha256`, `approved_at`,
`expires_at`, `approval: "OPERATOR_APPROVED_OUTAGE"`. It is the existing operator
authorization contract (maximum900s), not a new signing key. Bind the approval to
the returned current state; a subsequent revoke invalidates it. Do not manufacture
an approval from an obsolete request or edit the journal to bypass it. Recovery
reuses the continuation and start intents; emergency closes old TCP connections.

## Qualification boundary

### Isolated packet runtime (not a production provider)

`carrier/gatewayruntime` owns the shared SeedManager, admission, broker and profile
observer lifecycle. Production `bootstrap-broker` still constructs Telemost only,
accepts no `-mode`/local-provider flag, and retains its original duration limit.
The separate `carrier/internal/qualification/cmd/mesh-runtime` executable requires
`FC_LOCAL_CORE=1`. Its relay allocates real ephemeral rooms and framed loopback TCP
endpoints; it replaces only the external room/packet transport. It does not implement
Telemost signaling/media and is not a production-gateway artifact. Family TLS, mux,
lease/credential handlers and the reader run in the actual serving gateway process.

For this isolated scope only, controller configuration and every node's `online`
object may explicitly include `isolated_runtime`, an absolute root-private manifest
path. Its exact fields are `schema: 1`, `scope: "isolated-core-not-production"`,
`source_commit`, `native_sources`, `entrypoint:
"carrier/internal/qualification/cmd/mesh-runtime"`, `executable_sha256`. Source
commit/inventory must equal the frozen package. Capabilities add `runtime_scope`,
`reader_sha256` and `runtime_manifest_sha256`; all three participants must agree.
The production `gateway_sha256` remains separate and unchanged. NL still pins the
actual executable hash, UID and peer PID against the supervisor's real MainPID.
Absent this explicit binding, only the package's production gateway is accepted.
Neither the qualification binary nor its private configuration is put in the archive.

`tests/test_mesh_core_runtime.py` builds the separate driver from the same frozen
export, runs packaged controller/node/API/HTTP, and uses a real disposable supervisor
(`tests/fixtures/mesh_supervisor.py`). Its container-only systemctl-compatible shim
performs real start/stop/wait; this is **not systemd qualification**. SIGKILL cleanup
removes a dead process's observer socket only after wait and inode verification.
The negative nonresponding-proxy fixture below remains independent and unchanged.

The positive preflight runs both NL beyond15s, performs HTTP readiness with a
synthetic TLS CA, real Family bootstrap/dedicated handshakes, original and new TCP,
DNS and verified HTTPS, then checks process/socket cleanup. The emergency test
SIGKILLs a controller after COMMIT, replaces one gateway, observes the changed
runtime instance, requires outage approval, loses a real start response, reconciles
the saved intent and establishes new sessions. It does not claim that a killed
gateway preserves an old TCP connection, or that the revoke scenarios are covered.

The separate revoke test issues synthetic predecessor credentials through the frozen
API with the existing issuer/DB and wall clock, using the actual SeedManager directory.
These fixture credentials are not evidence of Android HTTP/cache delivery. A read-only
`admission-probe` in the isolated driver proves they work before COMMIT and fail Family
TLS admission afterwards, against the actual recovered reader process. Server rejection
is checked separately: TLS1.3 client handshake completion alone is not server acceptance.
Neither expired credentials nor an unreachable seed may stand in for revoked denial.

Explicit local `control.friends.restricted_admin --db <existing-db> revoke-device
--device <identity>` uses the existing Access transaction, is monotonic/idempotent and
rejects unknown identities or a missing DB. It creates no authorization store, network
API, signer or timer, and does not itself publish a CRL. The existing controller publishes
current revocations through the same custody boundary. The module is in this candidate's
API inventory; an isolated caller imports only `<package>/api.pyz` with Python `-I`.
Do not interpret test authorization as permission to revoke a production identity.
The test revokes after durable COMMIT and again after approval; the old approval must
fail its state binding. Recovery needs a newly bound synthetic outage approval, preserves
the COMMIT/fence/floors, reconciles lost start response, denies both revoked identities,
and allows the survivor via normal packaged HTTP readiness and new TLS/TCP/DNS/HTTPS.

Provider creation remains15s; seed lifetime is at most4h; lease defaults remain600s;
online SSH eligibility remains1395s+lateness. The isolated driver can use a bounded
process duration up to8h with the existing SeedManager overlap rotation (seed4h,
rotation3h), independently of process lifetime. Production CLI duration semantics
and certificate/CRL lifetimes are unchanged. A20s preflight does not establish
cryptographic-boundary or two-renewal continuity; security clocks are never frozen.

Service-start failure/timeout after the emergency COMMIT is an uncertain outcome,
not permission to stop the newly started reader and erase its usability. Recovery
keeps the durable intent and reconciles actual active state without issuing another
start. A start that never became active remains blocked with
`START_ALREADY_ATTEMPTED`; there is no implicit retry or rollback.

### Retained negative and fault evidence

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
