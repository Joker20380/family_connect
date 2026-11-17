# 17 November — isolated RU persistence/readback source candidate

Status: local candidate qualification; final exact-head CI/review pending.
**NOT_DEPLOYED; RU NOT_FIXED.** No production access, SSH, services, databases,
policies, keys, APKs or public catalogs changed. Physical iOS remains deferred.

PR43 reconciles the incident evidence with accepted PR42 by ordinary merge at
`7640c581ecb10e691878597af47380a28b2d841f`. Its exact runs, final integration and
remote/tree readback belong to its [receipt](https://github.com/Joker20380/family_connect/pull/43).
Neither document integration nor the measurements below assert present RU uptime.

## Candidate and limits

[Contract, consumers, reproduction and future gates](../operators/transport-readback-candidate.md).
Explicit `observations-v1` mode retains authoritative durability, confirmations,
real enforcement, existing bounds, first failure and legacy default behavior.
Freshness is disposable, state/boot/process-bound and fail-unknown on invalid input.
Candidate registration failure handling covers acceptance/preparation before ACK.

Local real-engine fixture uses a new network-none Docker namespace, synthetic user,
actual AWG3.1/Xray commands and real temporary-file syncs. Each mode receives the
same six unchanged cycles after its initial application:

| Measurement | Baseline | Candidate |
| --- | ---: | ---: |
| Real AWG/Xray queries | 18 | 18 |
| Authoritative/attempt writes | 12 | 0 |
| File fsync | 12 | 0 |
| Directory fsync | 12 | 0 |
| Disposable observation replacements | 0 | 6 |
| Correct successful collector samples | 6 | 6 |

The working-tree receipt records native hashes: AWG tool
`906d6795af1dd4adee7b11bf1e7fa133d4795c8a8d6e2099b34a026f810a3278`, engine
`e7f00e47d6df853ade5dcd2fe79240f01ff897d75088c768316a444c27c87e0f`, Xray
`4f7a4436f86798bbb5c875014e352021a1673710a45e170ccc507c5f59341940`.
This is a procedural/behavioral comparison, not bit-reproducible build or traffic
acceptance. Exact committed-source rerun and CI artifact identity go in the PR receipt.

## Qualification boundaries

The existing seven risk groups pass63 tests, preserving the explicit legacy
two-write assertion. Added tests cover permit/renew/deny/revoke/preparation,
all six mandatory sync-before-ACK boundaries, actual registration entrypoint commit
timeout, crash/reload after JSON write/file sync/replace/directory sync, corrupt
and missing observations, producer/boot/clock/monotonic changes, expiry during
commit, late completion, concurrent registration/watch/revoke, stale-plan rejection,
watchdog ordering and first-error/cleanup. Full selected counts belong to the final
receipt rather than a stream of CI-triggering documentation edits.

Panel observation/metrics groups pass20 tests against a disposable local PostgreSQL
with the panel lockfile verified; actual schema2 ingestion preserves readback time
and errors. The initial isolated-network PostgreSQL harness had no published host
port and produced connection-refused setup errors, not product failures; a fresh
loopback-only disposable database fixes the harness, with no assertion changes.
Control and device-identity environment versions also match both lockfiles.

The expanded transport suite exposed two historical overlay tests that implicitly
used moving source despite forbidding gateway-entrypoint changes. Their successful
historical package path now uses a complete clean worktree at accepted `b3fefac1`;
all old assertions and pins remain, and an additional negative case requires the
old tools to reject this new candidate. No PR16/17 packaging contract is broadened
and no historical deployment is repeated.

Fault injections use synthetic storage/engines where stated, real temporary-file
operations and process exits, not destructive power-loss tests. Long kernel I/O
cannot be cancelled by Python; the unchanged external watchdog/delivery contract
still requires future systemd and rollout qualification. Mandatory security fsync
can still exceed8s and must fail closed. Underlying historical storage latency
attribution remains UNKNOWN. The selected task stops at source-candidate review.
