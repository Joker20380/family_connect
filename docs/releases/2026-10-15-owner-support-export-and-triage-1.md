# OWNER-SUPPORT-EXPORT-AND-TRIAGE-1

Date: 2026-10-15. **RESULT: WAITING_FOR_OWNER_EXPORT**.

| Result field | Current result |
|---|---|
| EXPORT_OBTAINED | NO; no export JSON has been received |
| MATCHING_OWNER_EPISODE | NOT_ASSESSED; not a finding that the attempt is absent |
| NEWLY_PROVEN_BOUNDARY | NONE |
| FIRST_RECORDED_FAILURE | No newly recovered failure; the previous browser observation remains `DNS_PROBE_FINISHED_NO_INTERNET`, native first failure unproven |
| REMAINING_UNCERTAINTY | Contents and historical coverage of the normal ring/incident export are pending |

Starting review commit: `d108609483c80886c46e775057f37fd2614fe2a2`.
The [previous retained-diagnostics report](2026-10-15-owner-episode-retained-diagnostics-1.md)
is unchanged. Production acceptance remains **FAIL**, root cause **NOT_PROVEN**,
first missing evidence boundary
**EVIDENCE_INSUFFICIENT_AT_OWNER_DEDICATED_SESSION_READY**.

## Explicitly authorized export, not an entirely read-only operation

The owner now authorizes **one** normal `Diagnostics.share()` invocation, including
revocation of previous export URI grants, deletion of previous diagnostic cache
exports, creation of a new export and delivery to a chosen local receiver. That
exception supersedes the previous task's export-rotation stop; rotation is **not**
the blocker in this task. Primary diagnostic files and app identity/data must not
be cleared. No already accessible old support-export JSON was identified in the
previous task; its private supplemental capsule is preserved. No new machine-wide
search or attempt to access other old cache exports was made.

The one-export allowance is **not yet consumed by the agent**. No export button or
confirmation has been pressed by the agent, and no owner export receipt has yet
arrived. Export/cache mutations must be recorded separately when the normal export
is performed; they must not be hidden in zero deployment/product counters.

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

## Actual device/UI and recipient observations

The already authorized owner device was addressed using the previous task's known
selector, retained privately. ADB returned `device`; the existing app process was
present and the resumed Activity was `com.familyconnect.app.friends/FriendsActivity`.
No new package/source identity audit was run.

A normal package-manager query for ACTION_SEND + `application/json` returned installed
local receivers, including Total Commander's `DirBrowseActivity` and the system file
manager's `CopyFileActivity`. Total Commander is therefore not suggested merely on
the assumption that any file manager accepts JSON. Actual receipt/save success is
still pending the normal user flow; no receiver has been launched or granted a URI
by the agent. No email, messenger or cloud recipient was selected.

One standard `adb exec-out screencap -p` returned exit 0 but **zero image bytes**.
The exact Activity also sets FLAG_SECURE. The observed result is only that no usable
screen image was obtained, not a proven explanation of why. The current tab and
button coordinates cannot be verified visually. No blind taps, security bypass,
alternative screen-extraction attempts, instrumentation or helper APK followed.
This is **WAITING_FOR_OWNER_EXPORT**, not EXPORT_FAILED and not absence of history.

### One owner action

In the already open EXIT, go to **ОПЦИИ → Отправить диагностику**, confirm
**Отправить диагностику once**, choose **Total Commander** in Share, and save the
received `FamilyConnect-diagnostics.json` into a **new** local folder
`Download/owner-support-20261015-1/`; then report that it is saved. Do not overwrite
an existing export, press CONNECT or repeat the export. The proposed destination
is not claimed to exist yet. The receiver, not shell, receives the URI grant.

## Export schema and pending triage

These are **source-supported schema capabilities**, not observations from an obtained
bundle. Missing payloads are not classified as missing events.

| Exact schema surface | Handling once the file is received |
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

No ring, incident or restricted-history entry has been parsed in this task because
no export was received. Therefore **EXPORTED_NO_MATCHING_EPISODE is not established**.
If the eventual export lacks the target attempt, this path ends with that result,
without another general evidence search. If it contains a suitable identifier,
the already saved `first-connect-gateway.log` is the first correlation source.
No journal query was made here; the previous empty invocation-filtered query was
not repeated. No current gateway runtime is substituted for historical evidence.

## Private receipts, publication and action counters

Private task capsule: `/tmp/owner-support-export-and-triage-1-20261015/` (0700).
It contains only acquisition metadata, current-activity/receiver observations and the
empty screenshot receipt, with sizes, UTC acquisition times and SHA256. There is
**no support JSON**, so its SHA256, size, receipt time and transfer method are pending,
not invented. Known prior private capsules and their contents are unchanged.

| Action | Performed by this task so far |
|---|---:|
| Normal Diagnostics.share confirmation/export | 0; waiting for the single owner action |
| Export URI revocation/cache deletion/new export file | 0 by the agent; authorized as part of that pending export |
| Export recipient delivery / received support JSON | 0 |
| Native stats polls / diagnostic broadcasts | 0 |
| CONNECT/reconnect / VPN disconnect | 0 |
| APK installs / instrumentation / process restarts | 0 |
| Deployments / credential mutation or refresh / intentional provider actions | 0 |
| Product patches/builds / A-B-C / recovery triggers | 0 |

Only this sanitized report and necessary STATUS/PLAN/publication-index pointers are
published on the existing review branch. Main, workflows, frozen snapshots and
product source are not changed. No raw diagnostic payload or user identifier is
published. The verified remote commit and report URL are supplied in the task reply.
