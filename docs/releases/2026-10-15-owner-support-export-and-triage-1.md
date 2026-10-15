# OWNER-SUPPORT-EXPORT-AND-TRIAGE-1

Date: 2026-10-15. **RESULT: EVIDENCE_RECOVERED**.

| Result field | Current result |
|---|---|
| EXPORT_OBTAINED | YES; one owner-supplied JSON, 66,200 bytes |
| MATCHING_OWNER_EPISODE | OWNER_EPISODE_MATCHED, aliases C1/I1; binding explained below |
| NEWLY_PROVEN_BOUNDARY | BOOTSTRAP_HELLO_RECEIVE_FAILED_BEFORE_DESCRIPTOR |
| FIRST_RECORDED_FAILURE | Completed native startup: FAILED / HELLO_RECEIVE / cause UNKNOWN, attempt 1 |
| REMAINING_UNCERTAINTY | Underlying HELLO receive error and causal mechanism; unique server-session attribution; candidate-code/config/environment attribution |

Starting review commit: `d108609483c80886c46e775057f37fd2614fe2a2`.
The [previous retained-diagnostics report](2026-10-15-owner-episode-retained-diagnostics-1.md)
is unchanged as historical evidence. The waiting checkpoint was published at
`d2ae9b7b179803101ce928692b1838fd4ac104f5`; this continuation uses the exact file
subsequently supplied by the owner, without another export. Production acceptance
remains **FAIL**, root cause **NOT_PROVEN**. The old missing owner-dedicated-ready
evidence gap is now narrowed by a positive, completed startup failure **before
descriptor issuance and dedicated startup**, not by absence of a log event.

## Explicitly authorized export, not an entirely read-only operation

The owner now authorizes **one** normal `Diagnostics.share()` invocation, including
revocation of previous export URI grants, deletion of previous diagnostic cache
exports, creation of a new export and delivery to a chosen local receiver. That
exception supersedes the previous task's export-rotation stop; rotation is **not**
the blocker in this task. Primary diagnostic files and app identity/data must not
be cleared. No already accessible old support-export JSON was identified in the
previous task; its private supplemental capsule is preserved. No new machine-wide
search or attempt to access other old cache exports was made.

No export button or confirmation was pressed by the agent. One JSON was received
via an owner-selected existing host file. The owner's preceding UI/export/transfer
operations and the number of cache files rotated were not witnessed; the filename
is not evidence of a count of export invocations. Those mutations are **not observed**,
not silently reported as globally zero. This continuation only copies and analyzes
the supplied file; it neither repeats nor requests another export.

## Immediate call path checked in retained research84 source

Only the normal UI callback and export schema were inspected in the already verified
`whitelist-provisioning-block-seam-1/source/` tree. No full provenance/seal audit or
substitution of the dirty root checkout was performed.

`FriendsActivity.showSettings()` provides **Отправить диагностику / Send diagnostics**
through `Diagnostics.share(this)`. Its confirmation callback:

1. Obtains the diagnostic store and cached Support ID; no credential refresh is called
   in this export callback.
2. Reads the saved no-backup `diag-ring.json` and `diag-incident.json` independently.
   If the ring file is missing it can fall back to an in-memory ring snapshot; a
   missing incident is omitted. This fallback does not call native stats.
3. Revokes old diagnostic-export URI grants and deletes matching diagnostic cache
   export files; it does not delete or rewrite the primary ring/incident/JSONL files.
4. Writes the new bundle and opens ACTION_SEND with MIME `application/json` and a
   read URI grant to the selected receiver.

No CONNECT/reconnect, native stats poll, transport start or primary-log cleanup is
called by that callback. This is not a claim that the whole Activity lifecycle is
passive: `onResume` contains ordinary background work. The app was already foreground;
the agent did not launch, recreate, restart or resume it to reach the callback.

**`restricted-evidence.jsonl` is NOT_EXPORTED by this path.** Reading that app-private
file, repeating run-as/shell cat or granting shell the recipient's URI access is
neither required nor attempted.

## Earlier UI preparation, not the file's transfer provenance

The already authorized owner device was addressed using the previous task's known
selector, retained privately. ADB returned `device`; the existing app process was
present and the resumed Activity was `com.familyconnect.app.friends/FriendsActivity`.
No new package/source identity audit was run.

A normal package-manager query for ACTION_SEND + `application/json` returned installed
local receivers, including Total Commander's `DirBrowseActivity` and the system file
manager's `CopyFileActivity`. Total Commander was suggested based on its declared
JSON receiver, not an assumption about arbitrary file managers. Its actual use is
not established by the supplied file. No receiver was launched or granted a URI
by the agent, and no outgoing email/messenger/cloud transfer was performed by it.

One standard `adb exec-out screencap -p` returned exit 0 but **zero image bytes**.
The exact Activity also sets FLAG_SECURE. The observed result is only that no usable
screen image was obtained, not a proven explanation of why. The current tab and
button coordinates cannot be verified visually. No blind taps, security bypass,
alternative screen-extraction attempts, instrumentation or helper APK followed.
That checkpoint was **WAITING_FOR_OWNER_EXPORT**, not EXPORT_FAILED or evidence
that history was absent. No ADB/device access was repeated after file delivery.

## Acquired file and preservation

The owner supplied one exact desktop-side file path. Only that file was opened;
no adjacent messenger cache/database or other files were searched or read. It was
copied **before analysis** to the private capsule as
`owner-supplied-support-export.json` (0600, parent 0700). Source size/mtime did not
change during copying; the source file was not moved, deleted or rewritten.

| Acquisition field | Observation |
|---|---|
| Received/copied UTC | 2026-10-15 09:53:54.574255 UTC |
| Size | 66,200 bytes |
| SHA256 | `85722f4a9fe2a1089f7b7e20cbafec5b5546cc545dbf3160a8f57e9f10e16a1a` |
| Transfer actually observed | Owner supplied an existing host-local file; agent performed a local byte-for-byte copy only |
| Prior transfer route / exact export time | Not witnessed; neither receipt time nor filesystem mtime is treated as an event/export timestamp |
| Format | Complete parseable JSON with separate `ring` and `incident`, schema 1, research84/versionCode84 |

The full origin path, acquisition receipt, raw JSON and alias mapping remain private.
This is supplemental evidence, not a retroactive addition to the original sealed
episode. No assertion is made that the file came through the previously suggested
Total Commander route. No further outbound transfer was made by the agent.

## Schema limits applied to this export

These schema capabilities delimit the observations below. Supported but missing
fields are **NOT_RECORDED**; fields excluded by this export are **NOT_EXPORTED**.

| Exact schema surface | Interpretation |
|---|---|
| Separate `ring` and optional `incident` | Inspect independently; export/receipt time is not event time |
| Version, connection_id, incident_id and up to 128 diagnostic events | Match version, identifiers and event sequence, not time proximity alone |
| `restricted_startup` | May support an early failure before a session tag exists; a not-yet-issued tag is not mandatory for such analysis |
| `restricted_session` and up to four tagged `restricted_history` entries | Keep each session/lifecycle/first_failure separate; archived lifecycle traces are capped at 32 entries |
| `native_state`, projected lifecycle/terminal fields and counters | Use only actually retained fields; do not attach top-level counters to a different historical session |
| Protect and DNS/TCP counters | `protect_ok`, `protect_denied`, `dns`, `tcp`, `tcp_active`, `tcp_peak`, `udp_denied`, `ipv6_denied` are supported; only explicit retained numbers can be reported |
| Native-event projection | `bootstrap_descriptor_received` maps to `BROKER_DESCRIPTOR_READY`; `dedicated_data_ready` maps to `SESSION_READY`; selected failure events map to failure codes |
| Cleanup observations | The ring can retain `cleanup_completed` / `cleanup_failed`; they require attempt/sequence binding |
| Raw `restricted-evidence.jsonl`, its Java-failure stack frames and full native events array | NOT_EXPORTED; their omission cannot prove that an event did not happen |
| Literal `vpn_packet_ready` native event | Not mapped by `DiagnosticRing.nativeEvent`; do not demand this literal in the export. Native state and other retained evidence must be evaluated instead |

The target interval is anchored by the already recorded TUN creation
**06:55:43.785 UTC**, candidate rollback **07:05:36.326 UTC**, and final owner OFF
observation **07:09:07 UTC**, all on 15 October. A diagnostic snapshot's capture time
does not date every accumulated event in it. An early startup failure may be bound
through version/connection/incident/startup sequence without a dedicated session tag.

## Ring and incident, analyzed separately

Aliases are consistent throughout: **C1/I1** is the target connection/incident,
**U1** its exported Support ID, **D1** its directory fingerprint. **C2/I2** is a
different earlier readiness context, not assigned to this CONNECT. Native
`attempt=1` is process-local and is not itself the connection identifier.

| Field | `incident` | `ring` |
|---|---|---|
| Events | 72; target C1/I1 occupies zero-based indices 59–71 | 109; indices 0–71 are identical parsed events to incident, not independent witnesses |
| State / system capture | FAILED / `vpn_capture_open=true` | DISCONNECTED / `vpn_capture_open=false` |
| Readiness / directory | READY / USABLE | FETCH_FAILED / NOT_USABLE, after later background observations |
| Transport outcome | restricted: BOOTSTRAP_UNAVAILABLE | Same retained outcome |
| Native startup | FAILED, HELLO_RECEIVE, cause UNKNOWN, complete=true | Identical retained startup object |
| Native session | state 3, correlation MISSING; no tag or lifecycle | Identical retained session projection |
| Counters | protect_ok=74, protect_denied=0; no DNS/TCP counters | Same values; no per-counter timestamp exported |
| `restricted_history` | Empty array | Empty array |

All parsed event timestamps are nondecreasing. The ring adds 37 events after the
incident snapshot, including disconnect and later readiness checks through
09:47:51.692 UTC. Its later FETCH_FAILED **must not replace the incident's READY**
as the initial failure explanation. Empty restricted history does not prove that
no sessions ever existed: the schema archives only tagged sessions and is bounded.
This JSON is structurally complete, not a complete lifetime history of the app.

### OWNER_EPISODE_BINDING

The match is based jointly on the owner-supplied file provenance, research84 build,
the same C1/I1 in startup and orchestrator events, a coherent CONNECTING → FAILED →
DISCONNECTED sequence, and two independent retained context checks:

- C1 CONNECTING at 06:55:43.732 and VPN_CAPTURE_READY at 06:55:43.788 bracket the
  already sealed system TUN creation at 06:55:43.785 (53 ms before / 3 ms after).
- The native D1 fingerprint exactly matches `directory_sha256` in the previously
  copied `owner-readiness-server.json`; this strengthens episode/config context,
  but is not a unique client or server-session identifier.
- The exported disconnect finishes at 07:06:20.661, after the known rollback
  07:05:36.326 and before the known final OFF observation 07:09:07.

No record is assigned solely because it falls near the date. U1 is consistent
within the export but is not claimed to match an absent server Support ID. No
session tag is required to analyze this early, pre-descriptor failure.

## Recovered timeline and concrete record references

All event indices below are zero-based JSON pointers. Times are UTC on 15 October.

| Time | Record | Observation |
|---|---|---|
| 06:55:43.732 | `/incident/events/59`, also `/ring/events/59` | C1/I1 ORCHESTRATOR DISCONNECTED → CONNECTING; event-record time, not a measured physical button press |
| 06:55:43.788 | `/incident/events/60` | VPN_CAPTURE_READY, consistent with the initial system TUN; not native packet attach |
| 06:55:45.033 / .833 | `/incident/events/62`, `/incident/events/63` | READINESS READY while CONNECTING |
| 06:55:45.846 | `/incident/restricted_startup/started_unix_ms` | Native attempt 1 begins; `1792047345846` |
| +120001 ms / +120010 ms | `/incident/restricted_startup/observed_ms`, `/completed_ms` | First startup failure observed / startup completed, respectively; relative to native start, not Android boot elapsed time |
| 06:57:45.951 | `/incident/events/64`–`67` | Batch projection BOOT_CACHE_READY, BOOT_CARRIER_READY, FAMILY_AUTH_READY, STARTUP_FAILED; these equal timestamps are observation time, not exact timestamps of all accumulated native events |
| 06:57:45.951 | `/incident/restricted_session/terminal_observed_at_ms` | Terminal native projection, state 3 |
| 06:57:45.956 | `/incident/events/68` | Restricted candidate classified BOOTSTRAP_UNAVAILABLE |
| 06:57:45.995 | `/incident/events/69` | A second system VPN_CAPTURE_READY; not phase 2 or proof of dedicated readiness |
| 06:57:46.077 | `/incident/events/70` | SESSION cleanup_completed |
| 06:57:46.080 | `/incident/events/71` | ORCHESTRATOR CONNECTING → FAILED, BOOTSTRAP_UNAVAILABLE, duration_ms=122349 |
| 07:06:20.544 / .635 / .661 | `/ring/events/74`, `/75`, `/76` | FAILED → DISCONNECTING; VPN_RELEASED; DISCONNECTED |

Adding native relative durations to `started_unix_ms` gives approximately
06:57:45.847 for failure and 06:57:45.856 for completion, assuming no intervening
wall-clock adjustment. Those are **derived**, not independently exported wall-clock
failure timestamps. Approximately 120 seconds does **not** turn `cause=UNKNOWN`
into a recorded DEADLINE, TLS timeout, Reliable timeout or supervisor cancellation.

## FIRST_RECORDED_FAILURE and proven boundary

Safe excerpt; U1/C1/I1/D1 consistently replace private identifiers:

```json
{
  "record": "/incident/restricted_startup",
  "connection_id": "C1", "incident_id": "I1", "directory_fingerprint": "D1",
  "attempt": 1, "started_unix_ms": 1792047345846,
  "observed_ms": 120001, "completed_ms": 120010,
  "status": "FAILED", "stage": "HELLO_RECEIVE", "cause": "UNKNOWN",
  "complete": true
}
```

Only the relevant exact retained research84 source was consulted to interpret the
new record, not a repeated rootcause/provenance audit:

- `carrier/startupdiag/enabled.go`: first failure is retained; observed/completed
  milliseconds are elapsed since native recorder start. Completion does not turn
  an earlier failure into success.
- `carrier/bootstrap/protocol.go`, `requestTransport`: HELLO receive/validation
  precedes creating/publishing the setup/session trace, sending REQUEST_TRANSPORT
  and receiving/validating the descriptor. HELLO failure returns immediately.
  `Recover`/`recoverCarrier` use this request once in this path; there is no later
  successful retry hidden behind the first-failure record in this native attempt.
- `carrier/wholedevice/session.go`, `openDirectory`: a failed bootstrap Recover
  returns before dedicated carrier creation/auth/bind/Mux startup.
- `pilot/android-restricted/native/main.go`: failed Open records phase/state 3;
  phase 1 is assigned only after a successful wholedevice Open.
- `RestrictedTunnelEngine.up`: failure of the phase-1 gate rejects before native
  TUN attach/packet startup. The system's initial blocking TUN is a separate event.

The newly proven first failed stage is **BOOTSTRAP_HELLO_RECEIVE**, before a usable
descriptor and dedicated session. The precise returned error is not exported.
`cause=UNKNOWN` remains UNKNOWN; it is not evidence of why HELLO receive failed.

| Boundary / field | Status | Evidence and limit |
|---|---|---|
| SYSTEM_TUN_CREATED | PROVEN | Existing system receipt plus events/60; system TUN is not packet readiness |
| NATIVE_START_ENTERED | PROVEN | Bound completed startup record, attempt 1 |
| Seed carrier and Family auth | PROVEN | BOOT_CARRIER_READY / FAMILY_AUTH_READY in events/65–66; exact underlying event times unavailable |
| HELLO_RECEIVE | OBSERVED_FAILURE | Completed FAILED startup with cause UNKNOWN, native_state=3 |
| Descriptor / dedicated READY | PROVEN — not reached in this attempt | Positive HELLO failure plus the sequential source gates above; not an inference from a missing tag alone |
| NATIVE_PHASE_1 / native attach / phase 2 | PROVEN — not reached in this attempt | Open failure/state 3 precedes the phase-1 attach gate |
| Literal `vpn_packet_ready` event | NOT_EXPORTED | Not mapped by the normal ring; separately, the native attach path was not reached |
| DNS/TCP packet counters | NOT_RECORDED | Schema supports them, but neither bundle contains them; no zeros inferred |
| protect_ok / protect_denied | PROVEN | Explicit 74 / 0 in both C1/I1 snapshots; not proof of packet capture or successful Internet traffic |
| session_tag / lifecycle.first_failure | NOT_RECORDED | Schema supports them; trace publication follows successful HELLO. Their absence does not invalidate the early failure |
| Java failure stack / raw JSONL | NOT_EXPORTED | Not part of normal share bundle |
| Cleanup | PROVEN | cleanup_completed at 06:57:46.077; later VPN_RELEASED/DISCONNECTED at 07:06:20.635/.661 |
| Native terminal cause | NOT_RECORDED beyond UNKNOWN | Session terminal_reason/signaling/ICE are UNKNOWN; authorization_denied=false is explicit, not proof of all authorization paths |
| Working app CONNECTED / dedicated data plane | Not established; failed startup is proven | C1 goes CONNECTING → FAILED; system VPN CONNECTED/VALIDATED is not a successful dedicated session |

## Correlation with retained server evidence

The saved `first-connect-gateway.log` was examined first, using its existing private
copy. It contains 120 records / 115 traces (sequence 23–137) for unbound alias S1.
No exported C1, I1 or U1 value is present in that log. D1 matches the separate saved
owner-readiness directory hash, but that hash is shared configuration context, not
a connection/incident/session binding. **CLIENT_SERVER_SESSION_BINDING: NOT_PROVEN**.

The untagged server bootstrap auth and later `context_deadline` exchange failure
remain temporal candidates, not a proven pair with C1. S1 must not be reassigned to
the owner VPN. No DNS/OpenTCP/external-dial/response assertion is made for that tag.
No suitable unique new server identifier was recovered, so no new journal query
was justified or run. The earlier empty invocation-filtered query was not repeated,
and current runtime was not substituted for history.

**ROOT_CAUSE_PROVEN: NO.** This establishes the failed startup stage and rules out
treating this attempt as an established dedicated VPN with a demonstrated DNS-only
defect. It does not prove a candidate regression, acceptance-flag side effect,
server defect, provider defect, credential defect or Reliable/Mux causal mechanism.
No patch, new candidate, A/B/C, recovery trigger or CONNECT follows this result.

## Private receipts, publication and action counters

Private task capsule: `/tmp/owner-support-export-and-triage-1-20261015/` (0700).
It now also contains the raw support JSON, acquisition receipt, private alias map,
bounded parser and derived triage/correlation result. Raw identifiers and the full
JSON remain private. Known prior capsules and their contents are unchanged.

| Action | Performed by this task so far |
|---|---:|
| Normal Diagnostics.share confirmation/export | 0 by the agent; owner's action count not observed; no repeat requested |
| Export URI revocation/cache deletion/new export file | 0 by the agent; normal owner export/cache rotation authorized, actual mutation count not observed |
| Received support JSON | 1 owner-supplied file, copied and retained privately |
| Agent outbound diagnostic transfers | 0 |
| Native stats polls / diagnostic broadcasts | 0 |
| CONNECT/reconnect / VPN disconnect | 0 |
| APK installs / instrumentation / process restarts | 0 |
| Deployments / credential mutation or refresh / intentional provider actions | 0 |
| Product patches/builds / A-B-C / recovery triggers | 0 |

Only this sanitized report and necessary STATUS/PLAN/publication-index pointers are
published on the existing review branch. Main, workflows, frozen snapshots and
product source are not changed. No raw diagnostic payload or user identifier is
published. The verified remote commit and report URL are supplied in the task reply.
