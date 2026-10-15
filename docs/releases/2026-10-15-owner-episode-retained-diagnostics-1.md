# OWNER-EPISODE-RETAINED-DIAGNOSTICS-1

Date: 2026-10-15. **RESULT: ACCESS_BLOCKED**.

Production acceptance remains **FAIL**. **ROOT_CAUSE_PROVEN: NO**.
No retained owner-native snapshot was recovered or bound to the failed attempt.
**FIRST_NEWLY_PROVEN_BOUNDARY: NONE**. The prior evidence boundary remains
**EVIDENCE_INSUFFICIENT_AT_OWNER_DEDICATED_SESSION_READY**; this is not a finding
that dedicated startup failed, nor a DNS defect diagnosis.

Starting publication: `f5d7a4b156f66f2ce38fe7976d99f6f39678bb00` on
`review/supervisor-state-20261015`. Neither that SHA nor this documentation commit
is the frozen candidate source SHA. Frozen identities and the original
[rootcause report](2026-10-15-supervisor-candidate-dataplane-rootcause-1.md) and
[production FAIL report](2026-10-15-seed-supervisor-owner-acceptance-3-final.md)
are unchanged.

## Scope and supplemental provenance

This is a bounded retained-evidence retrieval, not a repeat rootcause/seal audit,
EXACT-LOCAL-TESTABILITY, A/B/C, recovery acceptance or product correction.

Private supplemental capsule:
`/tmp/owner-episode-retained-diagnostics-1-20261015/` (directory mode 0700).
It is separate from the initial sealed episode. Each selected existing input was
copied before analysis; `provenance.jsonl` records original path, acquisition UTC,
size, SHA256 and whether size/mtime changed during copying. No copied input changed
during acquisition. ADB outputs and the historical journal query have separate
command/acquisition/hash receipts. Raw files, device identifiers, app paths,
server identifiers and the small host-side parsing scripts remain private.
Local paths in this report are **not GitHub-readable evidence**.

### SOURCES_CHECKED

| Source | Result and limit |
|---|---|
| 15 existing owner-acceptance manifests plus research84 manifest | Copied and examined for retained diagnostic/export references; no reference to an additional restricted-evidence/support bundle found. This was not a verification of all 1,899 sealed entries. |
| Known isolated `artifacts/seed-supervisor-owner-acceptance*` task directories (16 roots) | Filename search for restricted-evidence, diag-ring, diag-incident, diagnostics, support and startup; no retained client diagnostic file found. `episode/production-startup-contract.txt` is a contract receipt, not an owner snapshot. |
| `state-client-build/field65-export16/` scoped tasks | Searched the four `gateway-seed-supervisor-{op-readiness,predeploy,deploy}-1` / `whitelist-provisioning-block-seam-1` roots, plus `owner-pinned-evidence-1`, `owner-selected-retry-beta68-1`, `owner-selected-retry-beta69-1`, `owner-controlled-loss-1`, `owner-retry-selection-audit-1`, `owner-retry-prep-review-1`. Only a startup source test matched in the first group; no diagnostic export in the six additional roots. Root-level filename lookup, depth two, also yielded no target export. |
| Repository `artifacts/`, depth two | No target diagnostic/export filename. Not a recursive home-directory or app-storage search. |
| Existing `episode-90m` owner/UI/final/readiness/browser/gateway receipts | Selected copies retain the already known system TUN and browser failure. No client attempt ID/session_tag/native state/counters were recovered from them. |
| Older `owner-readonly-capabilities.json`, `owner-package-readonly.json`, `owner-readonly.log` | Copies; JSON receipts are dated 2026-10-14 15:53:08 UTC, a different read-only preflight context. Not owner CONNECT evidence for 15 October. |
| Authorized phone, read-only package metadata and installed APK digest | Current research84 identity confirmed; access details below. No app launch or native stats invocation. |
| Historical candidate invocation journal, 2026-10-15 06:45:00–07:12:30 UTC | Exact invocation-filtered read returned no rows. Details below; no current invocation substituted. |

The filename searches pruned source/build/private/vault/Git/vendor/harness and
validation trees; their exact roots, exclusions and matches are in the private
`local-name-search-complete.json`. They do not establish absence from every possible
backup or renamed export. No private keys, vault, raw cache, profiles, unrelated app
databases, contacts, messages or browsing history were accessed.

## Exact source and access decision

The complete **retained research84 source**, not the dirty root checkout or the
published selected slice, was used:
`state-client-build/field65-export16/whitelist-provisioning-block-seam-1/source/`.
Its base is `f5240994869826c6a28f59e58e38256c688cf6eb`, research delta
`d7907697d71f119c21bced533f08abae06ae33ef9159c5fd9bd54cf031a481e7`.
The inspected Java diagnostics/export classes and native snapshot code match their
base Git blobs. `app/build.gradle` matches the research manifest SHA256
`612c2275f882743dafc91f63df3947e50c98508fc493d656f51c51f92b045cd4`.
Only these relevant source bindings were checked, not the full capsule.

Important distinction: researchProvisioning selects `src/publicStartup/java`.
That `StartupDiagnostics` class has no-op begin/capture/stopped methods; the
ownerDiagnostic implementation is not this APK's Java collector. This does **not**
disable `RestrictedTunnelEngine.evidence()` or prove native `owner_startup` absent:
native `startupStats` may include a matching startup snapshot, and `Diagnostics`
also consumes native statistics independently of the no-op Java collector.

- `RestrictedTunnelEngine.java:136–154`: reads native stats, then appends to
  `getFilesDir()/restricted-evidence.jsonl`; normal snapshots stop appending when
  the existing file is already over 1 MiB. The native read and diagnostic-ring
  update precede that size guard.
- `RestrictedTunnelEngine.java:124–133`: Java failure records append separately,
  without this size guard, with state/class/frames but no added wall-clock or
  elapsed timestamp. A bare failure record cannot be assigned to this attempt.
- `native/main.go` clears `owned.events` during stats-read; no fresh native read
  was requested in this task. `wholedevice.Session.Snapshot()` can contain
  counters, terminal reason, diagnostics and Mux stats; availability in code is
  not proof of a retained record.
- `Diagnostics.share()` reads existing no-backup `diag-ring.json` and
  `diag-incident.json`; it does **not** export `restricted-evidence.jsonl`.
  It revokes previous export URI grants and **deletes previous diagnostic exports**
  before creating the new cache file. Thus it does not meet this task's
  no-deletion/no-replacement requirement and was **not invoked**.
- `DiagnosticsProvider` is non-exported, accepts only read mode for an exact
  `diagnostics-<random>.json` cache URI, and rejects exports older than one hour.
  No existing authorized URI was available; no URI guessing, permission changes,
  broad cache read or diagnostic broadcast was attempted.

Small exact-source excerpts, not runtime evidence:

```java
// publicStartup/StartupDiagnostics.java
static void capture(Context context, long handle, JSONObject stats) {}
```

```java
// Diagnostics.share(), existing-export loop
if(!file.delete())throw new IOException("Diagnostic cleanup");
```

These two classes and the full export implementation remain local, not newly
published source files. Their SHA256 respectively:
`02e9ad77efa1597ca38b7170d5b90899f107a1a820afe55853969ff2215ef149`
and `25fd11be881bfbb979ca8c10326d931a58dc08b86322dcce05bd47a62b1afb1f`.
DiagnosticsProvider SHA256:
`10a7773069bcac78d62f7fa7af29146882a146a74058ccfd5ea5e529cd67cfae`.

## Phone read-only receipts

At 08:52–08:53 UTC, ADB reported one already authorized device. Its USB selector
matches the saved owner-capability collector; the selector itself remains private. Package
`com.familyconnect.app.friends` remains versionCode84,
`0.1.18-research84-provisioning-seam`, UID10283, non-debuggable.
The installed APK SHA256 is exactly
`fd3106170ceeb1e24dad6c8eacda4107b1ab09a6ee120ccf495d92d96841aa48`, matching the
research manifest and historical final receipt. Package lastUpdateTime remains
`2026-10-12 13:47:32` as printed by Android (device-local string, not relabelled UTC).
No package change is observed; that does not prove diagnostic data continuity.

The actual package `dataDir` plus the exact source's files-directory convention
identified the target. At 08:53:05 UTC the two ordinary read paths returned:

```text
D1 run-as: package not debuggable: com.familyconnect.app.friends
D2 cat: <app_files>/restricted-evidence.jsonl: Permission denied
```

ADB exec-out returned transport exit code 0 for these textual errors: **no JSONL
was read**, and exit code 0 was not treated as successful acquisition. Android
permission protection was respected. No root, debuggable override, helper APK,
instrumentation, shell-UID bypass, app restart or transport interaction followed.

**ACCESS_UNAVAILABLE**, not FILE_ABSENT: existence, size, last append time, whether
the 1 MiB threshold was reached, partial final lines and historic contents of the
target file are unknown. The current boot/time observation is not a historic
native snapshot or a reconstructed attempt timeline.

## Record classes and owner-attempt observations

`O1` = copied `owner-first-ui.txt`, line 4; `O2` = copied `https-before.xml`, its
Chrome error node; `O3` = copied `owner-final.txt`, lines 1–8 and the existing
production final assessment. These retain their **OWNER_EPISODE_MATCHED** capsule
provenance; no new native attempt/session is assigned on time proximity alone.
`S1` is the single tag in the saved gateway sample, consistently pseudonymized;
**S1 is not assigned to the owner VPN**. `D1/D2` are today's access receipts,
not historical startup events.

| Record class | Application |
|---|---|
| OWNER_EPISODE_MATCHED | O1/O2/O3, existing episode observations only; no recovered owner-native record. |
| OTHER_ATTEMPT | Older read-only preflight context is excluded from the target attempt; this label does not claim that a CONNECT occurred in that preflight. Today's package/access receipts are likewise non-episode observations, not a new transport attempt. |
| TIME_BINDING_INSUFFICIENT | A timestamp alone cannot bind S1 or any untagged bootstrap error to the owner VPN. No client attempt ID/elapsed_ms record was acquired to pair with a process/boot context. |
| PARTIAL_RECORD | Client JSONL truncation/append completeness cannot be evaluated without read access. The saved server sample is incomplete in coverage (sequence 23–137), not evidence of malformed client JSON. |
| FIELD_NOT_RECORDED | Requested owner-native fields below are not recorded in the available copied receipts; they may still exist in the inaccessible app file. Missing does not mean failure or zero. |

| Owner-attempt field | Status | Concrete observation / limit |
|---|---|---|
| SYSTEM_TUN_CREATED | PROVEN | O1 line 4: full system VPN/TUN created at 06:55:43.785 UTC. Already known; not the exact button press. |
| NATIVE_START_ENTERED | NOT_RECORDED | No bound native begin/attempt record; service presence is insufficient. |
| BOOTSTRAP_DESCRIPTOR_OBTAINED | NOT_RECORDED | Existing provisioning READY/auth observations do not supply a client-bound dedicated descriptor record. |
| DEDICATED_SESSION_READY | NOT_RECORDED | No bound `dedicated_data_ready`; S1 is unbound. |
| NATIVE_PHASE_1 | NOT_RECORDED | No owner-native state snapshot. |
| TUN_ATTACHED / NATIVE_PHASE_2 | NOT_RECORDED | Initial blocking system TUN is not native packet attach/phase 2. |
| VPN_PACKET_READY | NOT_RECORDED | No bound `vpn_packet_ready`. |
| DNS/TCP_COUNTERS | NOT_RECORDED | `dns`, `tcp`, `tcp_active`, `tcp_peak`, `udp_denied`, `ipv6_denied` unavailable. No zero values inferred. |
| FIRST_RECORDED_FAILURE | OBSERVED_FAILURE, browser only | O2 contains `DNS_PROBE_FINISHED_NO_INTERNET`. Exact DNS-event time, Java failure, native first failure and causal mechanism remain NOT_RECORDED. This is not a newly recovered failure. |
| CLIENT_SERVER_BINDING | NOT_RECORDED | No client session_tag/attempt identifier to pair with S1; no Support-ID-to-dedicated-session binding recovered. |
| CLEANUP_EVIDENCE | PROVEN, system/final observation only | O3: final OFF assessment at 07:09:07 UTC; ChatDeliveryService still present. Native stop/LOCAL_CLOSE/cleanup result and exact OFF transition remain NOT_RECORDED. No shutdown was performed now. |

Protect counters `protect_ok`/`protect_denied`, `underlay_dns`, native terminal
reason, lifecycle, Java failure and startup attempt timestamps are also
**NOT_RECORDED in the available owner receipts**, not observed zero or failure.
System VPN CONNECTED/VALIDATED is not proof of the app orchestrator's native-ready
CONNECTED state or a working dedicated session.

## SERVER_SESSION_CORRELATION

The already saved `first-connect-gateway.log` was used first: 120 JSON records,
including 115 traces, sequence 23–137, with one session alias S1. Its
GATEWAY_SESSION/ESTABLISHED observation and carrier byte counters are not bound to
owner VPN DNS/TCP traffic. Untagged `bootstrap_family_open`, `bootstrap_family_auth`
and `bootstrap_exchange_rejected` / `context_deadline` cannot fill that gap.
No DNS/OpenTCP, external dial or response claim is made for the owner attempt.

At 08:54:43 UTC a read-only journal query was issued for exactly the supplied
historical candidate invocation (alias INV-C1), using `_SYSTEMD_INVOCATION_ID`,
and 06:45:00–07:12:30 UTC on 15 October. SSH/journal command exit 0, stdout 0 bytes,
stderr 0 bytes: **no retained rows were available through that exact filter**.
Rotation, lack of retention, or missing invocation attribution are not distinguished
by this result. This is not proof that no event happened. No query of the current
gateway invocation or provider session was substituted; no service was restarted.

## Safe retained excerpts and digests

All aliases below refer to the same records used above; unrelated addresses,
device identifiers and the raw session tag are omitted.

```text
O1: VPN CONNECTED; created=2026-10-15T06:55:43.785Z; interface=<TUN-1>
O2: Chrome error = DNS_PROBE_FINISHED_NO_INTERNET
O3: 2026-10-15T07:09:07Z; ChatDeliveryService present; research84/versionCode84
S1: sequence=23; stage=GATEWAY_SESSION; state=ESTABLISHED; owner binding=NOT_PROVEN
D1/D2: app-private diagnostic file access denied (see exact error excerpts above)
```

| Private input | Bytes | SHA256 |
|---|---:|---|
| O1 `owner-first-ui.txt` | 3004 | `1063177abf5d7aae6a5eadefcac4b993d2a7762d0a4206b95b60c03c54a6e876` |
| O2 `https-before.xml` | 20119 | `a2fcb8c6be8adebe7a5ac2350498b5fdd6f7130580eb042fa6ecb0bb6e822e5c` |
| O3 `owner-final.txt` | 510 | `ed80c00f28cacbf70697a1b67dd293d7ab9673bf3b61a1e245bff7dbe15ab491` |
| S1 sample `first-connect-gateway.log` | 859799 | `9a1b06562e2aa5de51ff632ca14201c9e49b2e9743dfc3da6129b4e3aa93c084` |

O1/O3/S1 copies were acquired at 08:50:29 UTC; O2 at 08:57:15 UTC. These are copy
times, not event times. Digests identify the retained private inputs, not public
downloads. A digest or source excerpt cannot replace missing runtime evidence.

## Terminal result and publication boundary

**ROOT_CAUSE_PROVEN: NO.** Even a recovered startup failure would establish a failed
stage before necessarily proving its causal mechanism; no such owner-bound failure
was recovered here. **REMAINING_UNCERTAINTY:** historical native entry, descriptor,
dedicated READY, phase 1/2, packet pump, counters and first native failure remain
unresolved. The app file may exist but cannot be read by the permitted methods.
The existing export UI is incompatible with this task's retention constraints.

Stop this retrieval task. Do not repeat the same audit, infer a root cause,
automatically start CONNECT/A-B-C, patch Android/gateway, or create a candidate.
The failed frozen candidate and restored baseline identities are unchanged.

Publication contains **only this sanitized report, STATUS, PLAN and the publication
index** on the review branch. No raw diagnostics, source changes, frozen snapshots,
workflow changes or binary artifacts are included. The exact remote commit and
verified report URL are recorded in the task's final response after push/readback.

**PRODUCTION_UNCHANGED:** CONNECT/reconnect/VPN disconnect, APK install,
instrumentation, app/gateway restart, deployment/release, provider actions,
credential mutation/refresh, intentional drops/triggers, product patches/builds =
**0**. Native stats polls, diagnostic broadcasts and export invocations = **0**.
Only scoped read-only ADB and historical journal access occurred. No manual tests,
CI dispatch, acceptance or live transport session was run.

Сохранённого доступного evidence недостаточно на точной границе
**OWNER_DEDICATED_SESSION_READY**; app-private файл недоступен разрешёнными
способами. Production повтор не выполнялся.
