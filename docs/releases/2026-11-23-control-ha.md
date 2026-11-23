# 23 November 2026 — distributed control implementation handoff

## Source, authorization and scope

The owner requested implementation of distributed management and documentation.
Work continues in the existing current worktree:
`/home/joker/.codex/worktrees/dad9/family_connect`, branch
`feature/device-technical-metadata-20261115`. This main checkout is older and
divergent; pre-existing modifications are preserved. Do not deploy its runtime.

- Design/gates commit: `e5eaef838863e2ce43110dd1821eef9df9b67df3`.
- HA-01 implementation: `bbc0a9fb925165716052e3e574f8fa9da7c77a57`.
- Both ordinarily pushed; remote branch SHA matched after each push.
- HA-02A implementation: `9d1219d89b462e3ba87daa6e1e560dc1f238ce8b`, ordinary
  push to the same metadata branch; no source merge/deployment to this old main.
- Full architecture: [CONTROL-HA plan](https://github.com/Joker20380/family_connect/blob/feature/device-technical-metadata-20261115/docs/control-ha.md).
- Full evidence: [source-worktree release record](https://github.com/Joker20380/family_connect/blob/feature/device-technical-metadata-20261115/docs/releases/2026-11-23-control-ha.md).
- Commands/limits: [isolated rehearsal runbook](https://github.com/Joker20380/family_connect/blob/feature/device-technical-metadata-20261115/deploy/control-ha/README.md).
- Storage/writer map: [HA-02 scope and queue](https://github.com/Joker20380/family_connect/blob/feature/device-technical-metadata-20261115/docs/control-ha-storage.md).

## Implemented and verified

HA-01 supplies read-only single-transaction SQLite fingerprints, HMAC-only row/
schema/paid-policy evidence, a loopback-only mTLS etcd adapter and a real pinned
three-process rehearsal. No row export, product write or automatic admission.
etcd3.7.4 archive and binary SHA256 are pinned in source; binaries, logs, test keys
and synthetic databases remain outside Git under `/tmp/fc-control-ha-20261123/`.

61 focused tests pass using control/identity lockfiles; `pip check` and whitespace/
documentation links pass. Real rehearsals verify leader crash, remaining majority,
no-quorum read/publication refusal, stale-CAS refusal, unauthenticated TLS rejection
and direct readback from every recovered member. Final local failover is1.766s,
not a WAN/product RTO or SLA. A separate SIGTERM check confirms all three owned
children are stopped. Initial strict X.509 failure was repaired with AKI/SKI and
KeyUsage extensions, not by weakening certificate checks.

## HA-02A — enrollment checkpoint

Shared Access domain logic now runs through explicit transaction operations,
preserving default SQLite and existing proof/identity/TTL/limit checks. PostgreSQL
is only an injected synthetic repository: no production DSN, fallback writer,
alternate HTTP endpoint or automatic migration. Legacy SQL paths refuse there.

Forty contracts pass on SQLite/real PostgreSQL with no skips: concurrent one-use
proof/invite/limit races, status/replay/revocation, rollback, lost-response recovery,
Support ID collision, schema guard and bounded lock refusal.353 consumer tests
pass;20 optional nginx/sync/Go gates remain skipped, not accepted. Six runner
safety tests pass; locked environments pass pip check. Existing closed HTTP archive
checks pass without changing historical manifests/pins or client dependencies.

PostgreSQL17.11 is pinned by official-image digest; psycopg/binary3.3.9 is optional
lab-only. Real owned-container SIGKILL/restart preserves committed identity,
invitation/revocation and consumed challenge, drops uncommitted insertion and
permits a fresh reconnect. Binary backup restores all11 rows across five nonempty
enrollment tables into a separate fresh container; identity sequence advances.
This is not replication/RPO0 or a full product backup. SIGTERM during pytest leaves
no owned test child/container. Source/restored containers and anonymous volumes
are removed; credentials/dumps/logs remain private under `/tmp`, not Git.

## Not yet implemented

These are isolated checkpoints, **not completed migration**. HA-02 must finish all
other canonical writers, subscription challenge transactions, immutable payment events, metadata revoke
tombstones and file coordination to an explicitly qualified replicated store.
HA-03 adds receiver-enforced fencing, HA-04 multi-endpoint API/clients, HA-05 live
shadow and cutover with real failure tests. No HA controller is installed on NL and
no alternative API serves users. RU remains a shared dependency.

Latest known console5ce82415, public Android0.1.18-beta126/catalog9 are unchanged.
No server restart, provider move, policy/consent change or fresh health claim.
The22 November RU outage remains a separate open operational issue.

## Rollback and publication

Current rollback is only stopping the isolated rehearsal and reverting unused
source through a new commit if requested. Do not restore a product DB or replace
deployed archives. After future cutover, old SQLite rollback must not discard
confirmed events; fencing and verified forward/reverse migration are mandatory.

This handoff is separately committed on the old main. Ordinary push remains
subject to its existing non-fast-forward divergence; no force/rebase/merge is
authorized merely to publish these notes. Source availability is established by
the verified feature-branch pushes, not by this main checkout.
