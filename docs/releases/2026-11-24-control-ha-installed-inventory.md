# 24 November 2026 — installed journal inventory handoff

Authoritative source remains `/home/joker/.codex/worktrees/dad9/family_connect`,
branch `feature/device-technical-metadata-20261115`. Commit
`bea5ab07a5a5305d02e5b23d569a2e941cc06c0c` ordinarily pushed and independently
remote-SHA verified. The full report and collector/tests are in that worktree;
this divergent old main is navigation only, not a deployment source.

Read-only observation at23 November23:16:08–23:16:13UTC
(24 November00:16 Brussels), against canonical RU185.251.89.19,
NL1 185.10.158.212 and NL2 185.10.158.196, with existing strict SSH pins.
Retired186.246.45.246 and excluded186.246.51.201 were not queried.

| Observation | RU | NL1 | NL2 |
| --- | ---: | ---: | ---: |
| Ledger entries / archive directories | 366 /366 | 366 /366 | 172 /172 |
| Fenced rollback entries | 3 | 3 | 2 |
| Service-bearing archive shapes | 15 | 6 | 5 |
| Missing/unledgered archives | 0 /0 | 0 /0 | 0 /0 |

172 common operations agree on ledger result; current scheduled COMMITTED operation
is common, no active owner marker observed.194 RU/NL1 operations are outside NL2;
unequal historical cohorts do not prove corruption or authorize deleting/backfilling.
Canonical coordinator history is absent:365 RU entries lack a current/history-name
counterpart. Five adjunct JSON documents are not complete validated history. Original
approval/handoff custody is unestablished, not globally proven absent from backups.
Installed14-file source manifests match e9fd3175; online_history.py is not installed.

26 focused tests /0 skips, six source docs/1014 links and whitespace PASS. The census
rejects unsafe/racing objects and redacts private values. Archive profiles/keys/DB
payloads were not exported; journal executors and services were not invoked. Serial
metadata stability is not a writer barrier, cryptographic archive validation or full DR.
Private final evidence: `/tmp/fc-control-ha-20261124/installed-inventory-qualified/`.
Collector SHA256: `323035f48bc156215085a0dcc28eb5b5fc1b85747b6ae7d0d51f3d5208ef40fe`.

NEXT, not started: lossless legacy-prefix custody contract for actual mixed/service
archives and adjunct/fenced evidence, preserving every member without invented history
or approval. Preservation must not authorize replay/resume. Stage2 of5 and the other
three HA-02 blocks remain open; RU dependence remains. No deployment/version/catalog
change: console5ce82415, NL GeoIP22 November20:53:48UTC, Android126/catalog9;
8/12/120s and all-three-node ACK unchanged. These versions were not requalified here.

Rollback: stop using/revert the source-only collector. No host rollback, service
restart or old DB restore is needed. Preserve all native/private evidence. Scoped unit
discovery also observed product-cert-renew.service failed; this unrelated condition
was not investigated or changed, and is not proof that the management service is down.
Original dirty files/untracked work in this checkout must remain unchanged.
