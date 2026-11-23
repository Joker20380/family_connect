# 23 November 2026 — CONTROL-HA implementation checkpoint

Owner requests implementation and documentation of distributed management.
Source: existing metadata branch33b9cbdc; dirty divergent main preserved.
[Architecture, ordered gates and rollback](../control-ha.md).

Latest known installation remains console5ce82415 and two NL GeoIP collectors
on22 November; public Android126/catalog9 unchanged. This is not control HA or
RU recovery. The22 November RU outage recorded in the main checkout remains open;
source inspection is not a fresh server-health check.

## Progress

- HA-01 selected: read-only consistency tool and isolated three-voter rehearsal.
- HA-02..05 pending: no canonical PostgreSQL migration, fenced authority,
  alternate API, client fallback or live cutover installed.
- No server service/policy, product database, consent or client artifact changed.
- Tests, rehearsal receipts and exact source/push results will be recorded here.

## Rollback

Only source and disposable local rehearsal state exist at this checkpoint.
Stop rehearsal children; keep private logs outside Git. Do not restore a product
DB or replace deployed archives to undo this work.
