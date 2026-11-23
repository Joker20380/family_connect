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
- HA-02..05 pending: no canonical PostgreSQL migration, fenced authority,
  alternate API, client fallback or live cutover installed.
- No server service/policy, product database, consent or client artifact changed.
- Design checkpoint `e5eaef838863e2ce43110dd1821eef9df9b67df3` is committed/pushed;
  remote branch SHA independently matched. Implementation checkpoint
  `bbc0a9fb925165716052e3e574f8fa9da7c77a57` is also ordinarily pushed and verified
  against the remote feature-branch SHA; the worktree is clean after that commit.
- Old-main handoff `cf645e71` is retained locally. Its ordinary push was rejected
  `non-fast-forward`; no force, rebase, merge or change to pre-existing work.
  The feature branch, not that unpushed handoff, is the available source checkpoint.

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

HA-02 must migrate **all** canonical writers, including single-use challenge and
immutable paid events, separate metadata tombstones and filesystem coordination.
Then HA-03 receiver-enforced fencing, HA-04 multi-endpoint clients and HA-05 live
shadow/cutover and real failure acceptance. No alternate API is serving users;
RU remains a shared dependency. No provider replacement or live outage test done.

## Rollback

Only source and disposable local rehearsal state exist at this checkpoint.
Stop rehearsal children; keep private logs outside Git. Do not restore a product
DB or replace deployed archives to undo this work.
