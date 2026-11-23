# 23 November 2026 — CONTROL-HA implementation checkpoint

Owner requests implementation and documentation of distributed management.
Source: existing metadata branch33b9cbdc; dirty divergent main preserved.
[Architecture, ordered gates and rollback](../control-ha.md).

Latest known installation remains console5ce82415 and two NL GeoIP collectors
on22 November; public Android126/catalog9 unchanged. This is not control HA or
RU recovery. The22 November RU outage recorded in the main checkout remains open;
source inspection is not a fresh server-health check.

## Progress

- HA-01 isolated scope implemented and verified; details below.
- HA-02A enrollment slice qualified below; remaining HA-02 and HA-03..05 pending:
  no full canonical PostgreSQL migration, fenced authority,
  alternate API, client fallback or live cutover installed.
- No server service/policy, product database, consent or client artifact changed.
- Design checkpoint `e5eaef838863e2ce43110dd1821eef9df9b67df3` is committed/pushed;
  remote branch SHA independently matched. Implementation checkpoint
  `bbc0a9fb925165716052e3e574f8fa9da7c77a57` is also ordinarily pushed and verified
  against the remote feature-branch SHA; the worktree is clean after that commit.
- Old-main handoff `cf645e71` is retained locally. Its ordinary push was rejected
  `non-fast-forward`; no force, rebase, merge or change to pre-existing work.
  The feature branch, not that unpushed handoff, is the available source checkpoint.

## HA-02A — enrollment repository checkpoint, not complete HA-02

- Source/tests/docs checkpoint `9d1219d89b462e3ba87daa6e1e560dc1f238ce8b`
  ordinarily pushed to `feature/device-technical-metadata-20261115`; exact remote
  branch SHA independently matched. Staged scope/private-key markers, local
  documentation links and whitespace checks pass; no build output/private state.
- Old-main navigation checkpoint `a22efc6e3f1be5a813ac6469b9f80ce6c5543463`
  remains local. First push failed transient DNS; one ordinary retry was rejected
  `non-fast-forward`. Remote main remains `cb47bf230c6795cf21f4e6948253f49aa5377ed0`.
  No force/rebase/merge; the pre-existing40/66/11/6-line documentation changes and
  untracked root work remain untouched. Use the published feature-branch source.
- Shared `Access` domain logic now uses semantic transaction operations for invite,
  challenge, activation, status and device revocation. SQLite remains the default;
  existing API signatures, proof/binding validation,TTL100s and challenge limit8
  remain. The boundary stays in `access.py` to preserve closed artifact inventories;
  historical archive pins/overlays are not rewritten.
- `enrollment_postgres.py` is explicit synthetic-only injection, loopback/fixed
  disposable DB+role, versioned schema marker, native SQL and transactional locking.
  Legacy `db()` paths refuse instead of becoming mixed PostgreSQL/SQLite writers.
  No production DSN/HTTP switch or server configuration is added.
- Real PostgreSQL17.11 official image
  `postgres@sha256:18cfe3ef5e6815560c98237d6216d1e5119702fb0f3894c8785dd58b8bbe5d73`;
  psycopg/psycopg-binary3.3.9 pinned in an optional HA lockfile. Existing production
  and client dependency locks remain unchanged. Dependency notices updated.
- **40 SQLite/PostgreSQL contracts PASS /0 skipped** in the real runner. Includes
  eight competing independent connections spending one proof, two identities
  spending one invitation,16 simultaneous challenge requests respecting limit8,
  status replay, revoked/expired/wrong-device rejection, rollback after the last
  activation step, Support ID collision, lost-response status recovery, bounded
  lock refusal, schema mismatch and no silent SQLite fallback.
- Actual source-container SIGKILL/restart preserves committed identity/TCP ID,
  revocation and unused invitation, refuses consumed proof, drops an uncommitted
  insert and accepts a fresh reconnect with the same identity. fsync,
  full_page_writes and synchronous_commit are checked on; this is single-instance
  crash evidence, **not** host-loss RPO0, replication or hardware power-loss proof.
- Binary pg_dump restores into a second fresh owned container in one transaction.
  All five enrollment tables are nonempty and compare exactly:3 invites,2 devices,
  3 challenges,2 Support IDs,1 audit row. Restored identity sequence advances.
  This does not qualify paid/metadata/CRL backup or a production SQLite import.
- **353 consumer tests PASS /20 skipped**: Access/support, paid ledger/policy,
  old HA shadow/backup, packaged HTTP, restricted/chat/referral/subscription,
  technical metadata and GeoIP. Skips:15 explicitly configured real-nginx gates,
  1 pinned sync-archive interoperability gate,4 locked-Go compatibility cases.
  No claim of a complete release gate. A separate HTTP/runner rerun passes25
  tests /16 optional skips;5 of these are new runner safety tests. Final runner-only
  suite passes6 tests, adding refusal of a mismatched driver before container start.
- Initial unit run:165 PASS,19 PostgreSQL skips,1 fixture failure because the
  identity is already base64 text; corrected the fixture. First real PostgreSQL
  run:42 PASS,1 test used the deliberately refused legacy `db()` interface;
  replaced that assertion with the semantic transaction check, not a fallback.
  First broader collection lacked LXMF; installed the existing provisioning and
  messenger lockfiles in the same isolated `/tmp` venv. `pip check` passes.
- Private evidence under `/tmp/fc-control-ha-20261123/enrollment-1..5` retained;
  final `enrollment-5` passes contracts/crash/restore and removes both owned
  containers/anonymous volumes. Dumps, credentials, synthetic keys and raw logs
  are not committed. The runner is pinned to the local Docker socket and checks
  ownership before destructive cleanup; no existing panel container is touched.
- SIGTERM during a real pytest child: parent exits143, test child is gone and
  the owned container is absent. An earlier cleanup assertion expected capitalized
  Docker wording; independent readback confirmed removal, then the corrected
  case-insensitive exact-error check passed. No runtime cleanup change was needed.

[Exact writer inventory/remaining work](../control-ha-storage.md) ·
[Reproducible runner](../../deploy/control-ha/README.md#ha-02a-isolated-postgresql-enrollment).

## HA-01 implementation and validation

- `control/friends/control_shadow.py`: one read-only SQLite snapshot, schema/all
  table HMACs and existing paid-policy projections for RU/NL1/NL2. Dedicated
  synthetic HMAC key; no raw rows or identities in the manifest, no write/migration.
- `control/friends/control_quorum.py`: loopback-only verified mTLS, linearizable
  reads, revision CAS, replay/conflict/expiry rejection and lost-ACK readback.
  It is not a product leader lease or a replication adapter for application data.
- `scripts/control_ha_rehearsal.py`: three real etcd children, disposable CA,
  synthetic SQLite and owned-process cleanup. No production config or credential.
- etcd3.7.4 official archive SHA256
  `a0d47d07d081c12611fe69dc81a16ae8dd758401c0fe3a83d508823a1dac558e`;
  binary SHA256 `6fcf4a133e477a2340c59a287461b4988f0ed5c7559ff4750a8695ac41ae5a2a`.
  Source/version pins are committed, downloaded binaries are not.
- **61 focused tests PASS**: shadow, paid-registry backup, transport enforcement,
  membership. Dependencies installed from control/identity lockfiles in an isolated
  venv; `pip check` PASS. No full historical/platform release suite claimed.
- First unit pass exposed an incorrect synthetic key length; fixed without
  relaxing32-byte validation. First live rehearsal failed strict X.509 verification
  (missing Authority Key Identifier). Added AKI/SKI and KeyUsage to disposable
  certificates; did not disable verification, mTLS or downgrade TLS.
- Two subsequent real rehearsals PASS. Final run adds direct per-member readback
  after recovery, disallowing fallback to a healthy neighbour as acceptance proof.
  Leader SIGKILL → next confirmed shadow publication **1.766s** on this laptop;
  earlier less-strict rehearsal1.611s. Neither is a production availability promise.
- Minority linearizable read refuses; publication refuses before attempting a
  write. Confirmed manifest survives two crashed members and their return. Stale
  CAS is refused, unauthenticated TLS clients rejected. Only own children stopped.
- Separate real SIGTERM check stops the runner during startup: exit143, all three
  owned child PIDs gone; final61-test rerun PASS. This does not promise SIGKILL cleanup.
- Private local evidence: `/tmp/fc-control-ha-20261123/rehearsal-1`,
  `tls-diagnostic`, `rehearsal-2`, `rehearsal-3`. These contain only synthetic state
  and ephemeral test credentials; retain locally, never commit raw directories.

[Reproducible commands and limits](../../deploy/control-ha/README.md).

## Remaining work — not a production HA acceptance

HA-02 must finish **all** canonical writers beyond the enrollment slice, including
subscription's own challenge transaction, immutable paid events, separate metadata
tombstones and filesystem coordination. Full import, PostgreSQL replication and
Patroni/RPO0 gates are not implemented by this checkpoint.
Then HA-03 receiver-enforced fencing, HA-04 multi-endpoint clients and HA-05 live
shadow/cutover and real failure acceptance. No alternate API is serving users;
RU remains a shared dependency. No provider replacement or live outage test done.

## Rollback

Only source and disposable local rehearsal state exist at this checkpoint.
Stop rehearsal children; keep private logs outside Git. Do not restore a product
DB or replace deployed archives to undo this work.
