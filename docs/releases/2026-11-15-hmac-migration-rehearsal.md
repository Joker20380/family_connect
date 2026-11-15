# HMAC migration preparation — 15 November2026

**HMAC PREPARATION QUALIFIED FOR OWNER REVIEW; NOT_SWITCHED.**
**Metadata NOT_DEPLOYED / beta126 NOT_PUBLISHED.**
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
Final reachable-Git rescan after source61b00409 and its CI merge checks12,173 blobs:
0 matches for either the old or prepared replacement key (raw/hex/base64).

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
All six encrypted round trips compare exactly in-process: canonical registry,
support store, support encryption key, panel dump, replacement HMAC key and aliases.
Neither plaintext key nor private mapping is included in a public receipt/artifact.

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
An additional scan of32 other PostgreSQL tables found0 extra known-HMAC references
and0 unmapped named pseudonym fields. FK-linked rows, users/passwords and canonical
notification records are not relabelled. This does not replace the final delta scan.

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
- The exact minimal image's real `import_subscriptions` command also passes:
  original snapshot/event counts and digests remain,0 event duplicates. It appends
  one ordinary `subscriptions.attempt` audit record, as the existing command should;
  this legitimate attempt is not a historical rewrite or suppressed audit.
- Repeated support replay using the minimal worker overlay over the actually
  installed support app passes with the same7 pins/16 records/2 requests, preserved
  baseline/cursor and restart,0 sends. Only the new HMAC key and alias manifest are
  mounted; old HMAC material is absent from that isolated runtime.
-167 additional metadata/GeoIP/support HTTP/paid125/policy/boundary/overlay tests
  PASS using the existing locked environment. These are compatibility checks, not
  admission of126 or a substitute for installed Android end-to-end qualification.

The isolated real-copy PostgreSQL instance was stopped after these checks. The
original encrypted backups, candidate key/manifest and bounded receipts remain in
the private operator area. Production console/PostgreSQL remain running unchanged.

Source61b00409e24b92651678b817d2a6f5d4796948f9 is committed and pushed. Minimal
eight-file delta SHA256:
`828ad17a43435605e1e8f2cf0549662b00348abe565b54f1aa8da89c1971e65a`.
All baseline pins are checked before applying that delta; its zero-context result
was compared byte-for-byte with a context-checked patch over the same accepted
baseline. No entire main/PR archive is installed. Own review5908648910 explicitly
means self-review, not independent approval. Documentation receipts have a separate
head from this source; PR38 remains draft and there is no merge head or release tag.

Hosted full Python/Cargo job132667962357 passes on source61b00409. Its complete
context inventory covers6337 tests: standard:5705 PASS/276 explicit SKIP, root:258
PASS, snapshot314:98 PASS;356 standard deselections run in the latter contexts.
The receipt reports coverage_pass=true and no failed/error IDs. PR test-merge
918191db7510973edae32e35db02cdef21df4acf has the same tree as source61b00409:
`d4568dc5923facedcd52573c1e8ec46f170e26a9`. This temporary CI merge is not a merge
into main. Artifact14143296602 SHA256:
`7aa421f6f30c785c7cb9e2f99cd0c6e01014a816ac8c50fa5ecbce1365851b12`.
The separate phase0 failover job132667962562 also passes; the complete phase0
run43666831501 is successful. Android matrix results remain separately recorded.

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

On source61b00409, job132667993489 compiles and runs99 debug/Friends instrumented
cases without failures, including all three `TechnicalMetadataRuntimeTest` methods
in both variants on API35. Thus real Build/network/radio-fallback/consent assertions
have Android instrumentation evidence, not just the20 JVM tests. The later separate
per-app harness fails1 of10 cases: `independentUidsUseRealBuildersAndTraffic`,
`AppVpnRuntimeTest.route:49`, DNS lookup timeout8000ms despite successful VPN TCP
IPv4/IPv6 TLS traffic. No assertion is removed or relaxed. Artifacts14143203828 and
14143418160 retain the bounded evidence. A standard exact-source Android rerun is
requested. Android/native/harness/workflow paths are byte-identical between419279c8
and61b00409; that observation does not substitute for a successful current-head job
or prove a root cause for the intermittent DNS failure.

The unchanged419279c8 Android job132666741992 (run43664069230, attempt2) now
passes the complete standard API35/27 transport/Friends and API28/31 per-app matrix.
This confirms the correction beyond JVM/compilation. The earlier failed attempts
remain part of the record. Exact-head61b00409 rerun job132675960943 also completes
SUCCESS, including API35/27/28/31 and the per-app assertions. Run43666831505 attempt2
is successful with no failed steps. No source/assertion change was made for reruns.

Final applicable source61b00409 contexts:

| Context | Run | Result |
|---|---:|---|
| Full Python/Cargo + failover | 43666831501 | PASS |
| Client builds / Android full matrix | 43666831505 attempt2 | PASS |
| Paid Android release compatibility | 43666831450 | PASS |
| Readiness wire contract | 43666831474 | PASS |
| Control panel | 43666831482 | PASS |
| Subscription notification route | 43666831483 | PASS |
| Linux control preview | 43666831529 | PASS |
| Linux voice / messenger / internal candidate | 43666831489 /43666831471 /43666831495 | PASS |
| Explicit support runtime contracts + closed kit + panel | 43672504816 | PASS |

The last run uses the existing `/qualify-support-runtime` automation command
(review5908843075), not independent approval. Jobs132685440944/132685441145 pass;
support-android is intentionally not selected by this runtime-only command. The
separate standard Android matrix above supplies instrumentation qualification.
Subsequent documentation-only head checks are separate; these results qualify the
exact source/overlay, not any later unexamined source or a production release.

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
