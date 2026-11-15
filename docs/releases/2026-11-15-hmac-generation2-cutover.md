# HMAC generation2: authorized production cutover

Status: **SWITCHED — HMAC generation2**, not a metadata/Android release.
Owner authorization references qualified source
`61b00409e24b92651678b817d2a6f5d4796948f9` and documentation
`ca076b7e87e4d6af3d28b2dcd70d0010574c5f8a`.
[Runbook](../operators/hmac-generation.md) ·
[Historical rehearsal](2026-11-15-hmac-migration-rehearsal.md).

Only the eight-file HMAC delta plus alias module, protected manifests and two
pseudonymization keys are in scope. No metadata schema/API/UI, beta126, paid126,
catalog or complete PR/main deployment is authorized by this cutover.

**Operational warning:** RU AWG/TCP degraded during the window. No command in this
cutover restarted/stopped those transports, HTTP admission or paid reconciliation.
Do not read the successful HMAC acceptance as healthy-VPN acceptance; details and
the unresolved causality boundary are below. RU remains CAUSE_OPEN, PR36 NO_GO_PREFLIGHT.

## Fresh preparation

At11:44UTC all eight installed source inputs match the qualified baseline. Both
active key copies compare equal inside the process and differ from the retained
prepared generation2 key. No key value or identifier mapping is published.
The worker socket exists with its expected owner and0660 access. Effective unit
fragments/drop-ins and ownership were captured privately; configuration backups
contain24 local and24 RU files, with verified encrypted round trips.
Free space: RU7452MiB, local root13136MiB, staging volume26922MiB.

Production panel image remains
`sha256:61e4df54f1e1b83011b03427ec96e8941f9060173f7f756cbb4f1979fac81ad7`.
Qualified minimal candidate remains
`sha256:e44c342383f53feea8414f51033264079b7bfa86247c0b69e8dda2ad2510245d`.
The latter image became the running console at12:04UTC, with only its two importer
changes and alias module. Environment, command, existing volumes and users were
compared before recreation; PostgreSQL and system publisher were not recreated.

Fresh online SQLite copies pass integrity checks; PostgreSQL restores with
`--exit-on-error` in a network-isolated tmpfs container. Six encrypted data/key/
manifest round trips pass. Fresh copies contain66 canonical devices/4 canonical
events and8 pinned support contacts (the previous rehearsal had7).
All checked references map with0 missing/conflicts. Real-copy replay preserves
16 non-binding records,2 request identities,8 pins, baseline/cursor and restart;
0 messages sent. Panel replay preserves6262 subscription snapshots,4 events,
959704 inventory rows,106197 audit rows and0 labels; existing cardHTTP200,
no event duplicates, historical immutability enforced, partial activation rejected.
These are pre-pause observations, not the final paused coverage frontier.

## Final paused coverage

The first worker drain completed in0.57s: socket existed before SIGTERM; afterward
inactive/dead, exit0, released store lock, no remaining unit processes and socket
absent by normal cleanup. No manual socket deletion or forced sender kill was used.
Collector scheduling was paused first, then worker, then RU chat-sync. HTTP/paid
operations were not frozen, so these are consistent read-only copies, not a claim
that every production write stopped. Final backup completed11:57:03UTC.

The final canonical query again contains66 devices/4 events, with no1000-row limit.
The same prepared key and manifest retain all existing entities/handles. The table
counts stored references, not unique clients. All checked unresolved counts are0.

| Domain / store | Stored | Mapped | Missing | Conflicts |
|---|---:|---:|---:|---:|
| Device: inventory rows | 960298 | 960298 | 0 | 0 |
| Device: subscription snapshot JSON | 304555 | 304555 | 0 | 0 |
| Panel event: subscription snapshot JSON | 17554 | 17554 | 0 | 0 |
| Panel event: event row + immutable details | 8 | 8 | 0 | 0 |
| Device: event observations | 4 | 4 | 0 | 0 |
| Device: transport snapshot JSON | 1065152 | 1065152 | 0 | 0 |
| Device: measurement snapshot JSON | 360846 | 360846 | 0 | 0 |
| Device: audit references | 4 | 4 | 0 | 0 |
| Device: support projection | 66 | 66 | 0 | 0 |
| Device: pinned contacts | 8 | 8 | 0 | 0 |
| Device: saved support requests | 2 | 2 | 0 | 0 |
| Device labels / pending notification jobs | 0 | 0 | 0 | 0 |

Critical support references:8/8 mapped. Thirty additional production tables have
0 extra known-HMAC references and0 unresolved named fields. The earlier32-table
replica scan included two isolated technical-metadata tables: neither the original
nor fresh production dump contains them. No metadata migration was installed.

Final canonical/support copies pass SQLite integrity; the final PostgreSQL dump
also restores with `--exit-on-error` in isolation. Six final encrypted round trips
pass. Fresh real-copy replay again preserves8 pins,16 non-binding records,2
requests, baseline/cursor and restart, with0 sends. Panel replay keeps6271 snapshots,
4 events,960298 inventory rows and106306 audit rows, cardHTTP200 and immutability.
The isolated restore container is stopped; protected backups/evidence are retained.

Final backup SHA256, not public backup payloads:

| Copy | SHA256 |
|---|---|
| Canonical SQLite | `a9d1c2ab2b5ca47a9061f7e5af2f57d72e15dca377f74f983ea75fec8c9248fe` |
| Support SQLite | `f3d5cf537b7213ada3a16030e441322ad7682ec267c83441c9fca00c9fdbbdfd` |
| Panel dump | `ea081f1d7857a6812f6e93e3a276b912610e023e5f0d3d3a59d30df0e010c7d7` |

## Loaded consumers

All listed consumers use generation2 and the same manifest SHA256
`8602e6526ca1ec0e408c99a7ca37aedc4413b417f392e32096d5167517fcdcb8`.
The operator and RU key equality check runs inside processes; the new key matches
the retained prepared key and differs from the old one. Normal consumers no longer
read the old key. Old protected backups remain evidence, not active rollback keys.

| Consumer / installed file | SHA256 |
|---|---|
| Shared alias module | `ada9defd475c676e2f27398060ecbbe493a264b030385ae5ef83182b136ab6e9` |
| RU chat-sync support publisher | `fcb134324d4e8f868cdc8757d52095e9d0d6c7f44f738de93c149b309f42f0cf` |
| RU forced-command reader | `6ff3e2517267292c72e42d157dce3acb1f8d992c7cb1b2771b638e430511cdff` |
| Operator inventory collector | `a848b67feb86d8fa89722327c43539456ef20cb4cac60b4e2caefccc52e9b976` |
| Operator monitor | `00d8baf3659e1d02dff866eb4313ef5d1f42d82cb00522bf6bf404792fb9c84c` |
| Local support/feed collector module | `47d85678954ce07e7662a4da64fbbe117c60e69ba726e551c60934f555088372` |
| Local support owner | `0b90fd275ec09c0d9b1f54735062e20b55fb4a48707faaf56797fa9e1ef48a57` |
| Console inventory importer | `d4e4a3b4265d96e801470692315ec5cc6ee932ea25139703a8e81bc5fe32899d` |
| Console subscription importer | `0a5d89786c4af7c9ba61e2a8aa3b445c671ed6f7d369a914e5e864bca1c33c7c` |

Minimal patch SHA256:
`828ad17a43435605e1e8f2cf0549662b00348abe565b54f1aa8da89c1971e65a`.
The original chat-sync entry point, canonical subscription reader and notification
engine stay unchanged. Generation2 alias loading was checked as the actual support
user and console UID10001, not only root. Effective collector/owner drop-ins select
the intended protected manifest; no diagnostic override remains active.

## Activation and forward recovery

- Both atomic key-file replacements and minimal overlays finished while consumers
  were paused, at12:04:10UTC. No old database was restored into production.
- The first resumed chat-sync oneshot returned1. A bounded direct normal-sync
  retry and subsequent systemd runs succeeded, producing authenticated fresh
  generation2 leases. The initial exception was swallowed by its existing entry
  point; no specific network/root cause is claimed from that exit status alone.
- The installer initially created two new public code directories with root0700
  under its private umask. This blocked the support-user import. Only those code
  directory permissions were corrected to0755; private files remained0600.
  Owner-context import/manifest read then passed; its start-limit was cleared.
- A temporary sanitized startup exception hook produced no exception record and
  was retired. The owner was gracefully drained again with released lock and
  normal socket cleanup, then started without that diagnostic override. The same
  generation2 key, aliases and live data were retained throughout; no forced kill.
- Fresh chat binding, owner and original-cursor notification projection resumed.
  First complete inventory cycle passed12:16:40UTC. All original timers resumed
 12:21:16UTC. The collector maintenance window was approximately25 minutes,
  including permission/startup repair, not merely the0.57s worker drain.

This is an observed partial-installation recovery by completing the narrow setup,
not by rolling back the key or replacing current databases. Future recovery uses
the same alias-aware image/code or a qualified forward correction and preserves
new requests/messages/events. Prepared restore copies are not overwrite instructions.

## Live preservation and normal cycles

After resumption, all17 support records remain. All16 non-binding records are
exactly equal after decryption, including8 pinned contacts and identity/block state,
2 original requests,8 message IDs, baseline, cursor, highwater/position hashes and
excluded-history state where present. Only the acknowledged binding projection
advances. No new notification jobs or messages were manufactured. No natural new
payment/event was observed, so real notification receipt and a production late ACK
are **NOT_OBSERVED**; isolated pending-job/late-ACK tests remain in the source receipt.

Existing historical panel rows remain equal, including their JSON and digests:
41534 inventory snapshots,960298 inventory-device rows,6271 subscription snapshots,
4 event observations,106306 audit records,18285 transport snapshots and14765
measurement snapshots. The one existing panel user/password record is unchanged;
actual device-label count is0, so no invented production-name preservation claim.
Distinct device handles remain66 and event handles4; rotation added0 duplicates.
New normal collection snapshots/audit attempts are allowed, not mistaken for damage.

Three successive automatic cycles completed **12:22:39,12:23:49,12:24:59UTC**.
Each imported gateway-ru and both existing Amsterdam sources; support owner stayed
active, bindings were fresh, notification feed ages were28.1/29.8/4.7s and collector
exit statuses were0. Final support comparison after these cycles still passes.
An existing authenticated device card rendersHTTP200; unauthenticated access to
[the production panel](http://127.0.0.1:8765/inventory/) returns the expected login302.
The old panel has no technical-metadata model/UI installed.

## Separate RU observation — not a healthy-fleet claim

Before cutover RU AWG/TCP and paid-watch were active. Journal timestamps show a
stop of AWG/TCP at12:06:49UTC: TCP exited0 by12:06:51; AWG timed out and was killed
by systemd at12:06:54. Paid-watch subsequently restarted repeatedly, and the paid
reconciler failed. This task issued **no stop/restart/kill for these units**, no
transport configuration change, no paid operation, and no persistence change.
The existing paid-watch dependency can stop transports on watcher failure, but
the triggering cause is **not established** by the bounded observations here.
Do not label it proven unrelated to the time window or silently restore transports.

HTTP admission retains its original running process and archive
`617c7d752a20631d624b301c59142af34f3624483a5d2d5adc2a7c7722dd74b1`;
the reconciler archive remains
`40e1d7212b158fa01e4e4a92c0b635a910ae05b8b350840c07629629108b7aeb`.
The peer worker also retains its process. These unchanged pins do not turn the
failed reconciler or stopped RU transports into PASS. Their diagnosis/recovery
requires the separate RU operational scope; this HMAC authorization excludes VPN
restarts and does not authorize changes to persistence or RU restrictions.
An additional read-only canonical comparison after resumption confirms that the
one `paid_beta_subscriptions` row and all4 `paid_beta_events` rows are unchanged,
including their existing terms; this task created no payments or expiry changes.

## Source, documentation and release boundary

Qualified implementation source remains61b00409; its already recorded applicable
CI results are unchanged. This continuation changes documentation, not qualified
implementation source or signed Android artifacts. Authorization/drain checkpoint
`2558d5eb229ef42f299b4a0129d24384b68bbc11` was committed/pushed separately.
The final documentation commit is recorded in PR38 and the task handoff. PR38 stays
draft/unmerged; remote main remains53a780d9 at final branch verification. No PR
test-merge ref is represented as an actual merge or deployment of main.

Public beta125 and paid108/119/123/125 remain unchanged. Metadata release still
needs the signed candidate, compatible ARM64 upgrade125→126, exact paid descriptor
and installed APK→API→panel qualification. No real notification receipt is claimed
without a new naturally occurring event.
