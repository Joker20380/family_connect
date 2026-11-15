# HMAC migration preparation — 15 November2026

**NOT_SWITCHED. Metadata NOT_DEPLOYED / beta126 NOT_PUBLISHED.**
Preparation is part of draft PR38, based on remote main53a780d9. It is not permission
to deploy the whole PR or main. [Exact proposed switch/recovery plan](../operators/hmac-generation.md).

## Exposure scope

The known previous tool result contained the same key used by the operator inventory
and RU support inventory publisher (equality checked in-process, value not emitted).
The local session JSONL stores that result twice, as completion/output records.
One of11 specifically scoped generated private support scripts also contains it.
That script already had0600 permissions. The session file was0664; it is now0600,
without deleting or rewriting history. A known CLI history file has no match; the
standard CLI log path was absent. Other infrastructure/session retention is not
attested by these local checks. There is no evidence here of a public leak.

Exact raw/hex/base64 comparison found zero matches in12,143 locally reachable Git
blobs,33 scoped preparation logs/receipts and all members of8 known ZIP/APK/PYZ
artifacts (no oversized member omitted). This is a bounded scan, not a claim about
all remote CI logs or every file on the laptop. No mapping, key or private matched
line is committed. No broad log deletion or Git history rewrite was performed.

## Installed boundary and protected copies

Fresh runtime checks identify the RU `friends-access/app/control/friends/support.py`
publisher used by chat-sync, its forced-command reader and subscription event
reader, the local root collectors and support worker, and the console importers.
All eight overlay inputs match the accepted main53 source, recorded individually in
`deploy/support-chat/pseudonym-baseline.json`. The notification engine/feed canonical
reader remain unchanged. HTTP/operator/reconciler paid policy108/119/123/125 remains
unchanged; rotation requires no replacement of those archives or VPN restart.

At01:43:45UTC, SQLite online backups passed integrity checks; the PostgreSQL dump
restored with `--exit-on-error` into a network-isolated, tmpfs-backed PostgreSQL17.
Encrypted off-host copies and replacement key/aliases are in the protected operator
area. A duplicate derived row-export encryption hit the local disk bound; only that
incomplete duplicate was removed. Complete encrypted canonical/support/PG backups
were retained and checked; no original backup was deleted. No giant derived export
is needed for recovery. Recheck space before any additional staging.

## Complete reference coverage

Counts are **stored references**, not unique clients/events, and belong only to
this consistent-copy rehearsal. Full canonical source:66 device IDs and4 event IDs,
using an unbounded `paid_beta_events` query, not the1000-event export. A1503-event
synthetic regression also checks the full query and delta incorporation.

| Domain / store | Stored | Mapped | Missing | Conflicts |
|---|---:|---:|---:|---:|
| Device: production inventory rows | 926176 | 926176 | 0 | 0 |
| Device: subscription snapshot JSON | 268365 | 268365 | 0 | 0 |
| Panel event: subscription snapshot JSON | 14969 | 14969 | 0 | 0 |
| Panel event: event row + details | 8 | 8 | 0 | 0 |
| Device: event observations | 4 | 4 | 0 | 0 |
| Device: transport snapshot JSON | 962720 | 962720 | 0 | 0 |
| Device: measurement snapshot JSON | 321033 | 321033 | 0 | 0 |
| Device: audit references | 4 | 4 | 0 | 0 |
| Device: support binding projection | 66 | 66 | 0 | 0 |
| Device: pinned support threads | 7 | 7 | 0 | 0 |
| Device: saved support requests | 2 | 2 | 0 | 0 |
| Device labels / pending notification jobs | 0 | 0 | 0 | 0 |

The event-domain8 references are4 rows plus their4 immutable details, not8 canonical
events. Production technical metadata is not installed, so there are no new metadata
rows to migrate. Source tests preserve consent epoch/sequence/revocation and sample
times. No unresolved legacy record was found in these checked domains. The tool
explicitly marks missing history `legacy_unresolved` and blocks missing critical
references rather than guessing matches. Active/pending coverage must be refreshed
under the final bounded pause, not inferred from this table indefinitely.

## Rehearsal and limits

- New-generation HMACs map to stable internal entities/handles. Historical snapshots,
  audit records/digests, labels, request originals and canonical notification IDs are
  not rewritten. The new key and private alias file have0600 permissions.
- Restored real support:7 pins,16 non-binding records,2 old requests preserved;
  replay with both old and new pseudonyms returns the original messages. Zero sends.
  Baseline/cursor preserved; close/reopen preserves decrypted content exactly.
  The isolated process has no external network and no old HMAC key mounted.
- Restored real panel: reimport is the same subscription snapshot;0 duplicate events;
  5754 snapshots,4 event observations,926176 inventory rows and100530 audit rows
  remain. Existing card rendersHTTP200. Immutability trigger rejects historical
  updates. Real label rows are0; preservation of an explicit name is tested in the
  synthetic panel test, not claimed as an observed production name.
-70 focused source/support tests PASS, including rotation with saved jobs, unchanged
  request source/address/text/expiry conflict checks, blocked identities, excluded
  history and real isolated mailbox late storage ACK after restart.48 panel tests
  PASS. Wrong key/generation/channel/manifest and partial installation fail closed.
- Atomic manifest rerun preserves mappings. A synthetic canonical delta creates
  new exact mappings without changing existing entities; stale manifests reject
  new envelopes. Fresh live-copy delta at02:05UTC still has66 devices/4 events,
  added0/removed0. This is not a claim that all panel timestamps/counters froze.
  Individual online backups are transaction-consistent, not a global write freeze.
- Minimal panel image candidate overlays only two importers and the alias module on
  accepted61e4df54. Candidate SHA256:
  `e44c342383f53feea8414f51033264079b7bfa86247c0b69e8dda2ad2510245d`.
  This is a prepared image, not a running production version.

Recovery keeps new data/key/aliases; finish the missing consumer or deploy compatible
alias-aware code. No old-DB restore and no automatic old-key reactivation. See the
numbered plan for drain, final delta, coordinated switch and resumption boundaries.

## Android and remaining product gates

Source419279c873981bf8b13677dec38ece02a79c593c fixes the non-public transport test
mutators.20 JVM tests PASS. Hosted compilation now passes; the push run reaches99
instrumentation cases with no reported case failures, then fails the separate
per-app routing harness. PR run132659528644 fails TCP IPv6 connectivity to the
synthetic fd79:fc::1 endpoint. Neither is a full Android CI PASS; a standard job
rerun is requested without dropping tests or changing assertions. Phase0, panel,
Linux control, paid and readiness contexts pass on419279c8; final source qualification
is tracked separately from these earlier results.

Original public125 remains immutable and published. Its ARM64 library raises SIGILL
in `golang.org/x/sys/cpu.getisar0.abi0` on the x86_64 translation bench after normal
activation. A compatible ARM64 bench or authorized physical device must perform the
in-place125→candidate preservation check; do not rebuild125 or bypass CPU checks.
The unused own emulator5590, synthetic Django18769 and synthetic PostgreSQL55439
were stopped, preserving private evidence/state. No other project's services changed.

Before user release: complete Android contexts and exact signed candidate/signer,
in-place upgrade, exact paid descriptor, installed APK→API→collector→production
panel, minimal deployment and public discovery/invitation/download verification.
No126 paid admission or public catalog change has occurred. Separate consent/revoke/
TTL remains; phone number/GPS/content harvesting is excluded. GeoIP candidate covers
only identity-bound recent RU/AWG observations; NL/TCP has no qualified peer binding,
MESH has no direct location observation and must show unavailable or an independently
aged previous observation. Never label gateway/relay geography as the client's city.
