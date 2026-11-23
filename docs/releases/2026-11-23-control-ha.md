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
- Full architecture: [CONTROL-HA plan](https://github.com/Joker20380/family_connect/blob/feature/device-technical-metadata-20261115/docs/control-ha.md).
- Full evidence: [source-worktree release record](https://github.com/Joker20380/family_connect/blob/feature/device-technical-metadata-20261115/docs/releases/2026-11-23-control-ha.md).
- Commands/limits: [isolated rehearsal runbook](https://github.com/Joker20380/family_connect/blob/feature/device-technical-metadata-20261115/deploy/control-ha/README.md).

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

## Not yet implemented

This is an isolated foundation, **not completed migration**. HA-02 must migrate all
canonical writers, one-time challenges, immutable payment events, metadata revoke
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
