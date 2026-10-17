# TRANSPORT-BATCH-MAINTENANCE-AND-ROLLOUT-1

**RESULT=MAINTENANCE_COMMITTED_PAIR_INSTALLED_DEPLOYED_MOBILE_TEST_PENDING.**
17 October2026, operational observations08:56–09:01UTC. User explicitly approved
the accepted offline maintenance with restricted-session interruption, followed by
the already prepared private pair rollout. Input review
`16a7df9e5588c350f4d4d44a47c9ee889651768f` and its
[signed/not-installed checkpoint](2026-10-17-transport-batch-owner-rollout-1.md)
remain historical evidence, not rewritten as a completed earlier installation.
[Safe selected receipts](evidence/2026-10-17-transport-batch-maintenance-and-rollout-1.json).

## Exact private pair now installed/deployed

| Identity | Value |
| --- | --- |
| Android version / code | `0.1.18-research84-ui60-4-batch1` /84 |
| Signed **and installed** APK | `697f9c244b67f75e7e3e612dbcd91a48891d32ee77e23fd9bce173a5f049233f` |
| Embedded native | `dd722eada0da7c890a8d71a72099cba5d0bbac1ce73377bbdbc8e7b85d820c23` |
| Client source inventory | `cdd089478624ff5113d14590a340092684127a674565c3acfe6750aa76a17790` |
| Configured and loaded gateway | `4b722d2d7f2159b96953e27777494bf596768f860ee8da7e634fb1100b08fab7` |
| Gateway source inventory | `aeeb6755bd235160127cfed67da4a870ae340cfebe89fc6d0f937908607d9483` |
| Existing Android signer | `67a90d1bfcd5a2c0666f0cff1b0ac5e43aaa661ca1196f89e879aa39fe20848a` |

Publication commit, source inventories and executable/APK hashes remain separate.
The APK signed in the preceding turn was reused byte-for-byte; no new APK signing,
rebuild, product patch, regression matrix or emulator run in this continuation.
The [local batching implementation and tests](2026-10-17-transport-write-batching-1.md)
are prior evidence. Its synthetic median4.65× result is **not measured phone speed**.

## Ordinary maintenance, not expired recovery

Fresh authoritative scope and strict validation passed. Authority/grants still valid,
but due for operator maintenance; the leaf had also reached the ordinary90-minute
threshold. There was no active writer, pending owner/request or uncommitted operation.
Restricted-session count remained UNKNOWN; the authorized outage did not assume zero.
Both current unrevoked grants were eligible; their identity/scope was not changed.

One operation `batch-rollout-maintenance-20261017-085744` used the installed accepted
`authority-request` → existing offline signer → `operator --approve-maintenance-outage`
path, not expired recovery. Management source map remained
`5109a7c92ddd1937fe75ed7199866855a8cc20279bc226c35475d4cc81330145`.
Pinned signer `2de81e84c6b5fb39cbf5ca840e7a4791edec256bbb6e3fe7924efc24319ba5f6`
ran only on the previous signing host through vault custody/memfd. Root key/password
never went to either server; only the signed handoff bundle went to RU. No raw request,
credential bundle or secret was published. The accepted canonical node-dispatch request path was reused;
no production module was modified to accommodate the request.

Apply08:58:13.895–08:58:43.942UTC returned COMMITTED, first_cause=null. This30.047s
apply envelope is not an exact traffic-outage measurement. Authority sequence15→16,
both grant revisions+1, CRL27111→27112 and leaf renewed with existing keys/bindings.
Existing revocations remain; CRL entries1→2 through ordinary cutover. Grant scope,
policy and floors (minimum revision1, CRL27088) were preserved. No restored revoked
grant, identity, trust anchor, TTL adjustment or credential rollback.

Both nodes completed protected CLEANED archives: RU13/NL8 files, hashes verified,
45 retained operations each under the existing256 bound. Node state roots contain
only archive/completed.json/operation.lock; no pending owner or authority request.
The timer was paused once for handoff and restored once at08:59:32UTC, preserving its
enabled state/schedule. No parallel writer or restart-until-green.

**Maintenance preserved the then-current gateway079729e4…49639d**, checking configured
and loaded bytes before apply and after workflow start. It did not restore historical
21f0a0fd or a5372571. Only the subsequent separately authorized binary rollout replaced
079729e4 with4b722d2d. Thus this whole continuation is neither PRODUCT_BINARIES_UNCHANGED
nor PHONE_UNTOUCHED: operational material and the intended private product pair changed.

## Binary transition and phone readback

| UTC | Boundary |
| --- | --- |
|08:58:38 | Maintenance workflow starts unchanged079729e4, PID1159966 / INV_MAINT |
|08:58:41.628 | Fresh maintenance directory, copied to RU by normal publication |
|08:59:59 | Post-maintenance preinstall guard PASS; current gateway backup staged |
|09:00:11.154–09:00:16.502 | Exactly one ordinary `adb install -r`; success |
|09:00:17.335 | Installed APK/native/signature/alignment read back, UID10283 |
|09:00:47.015 | Fresh pretransition guard: valid material, evaluate NOOP, schedule gap>180s |
|09:00:50.796–09:00:53.405 | Existing RU coordinator/node and NL node lock coordination |
|09:00:53.358 | New gateway4b722d2d loaded, PID1162821 / INV_BATCH |
|09:00:55.526 | New runtime-bound directory, subsequently verified on RU |
|09:01:06.332 | Strict served chain/listener/seed/current directory PASS |
|09:01:11.448 | Ordinary app launch/readback: PID14226, VPN OFF |
|09:01:38–09:01:42 | Final runtime readback and read-only evaluate NOOP |

INV_MAINT=`64d0a059a6e646b89ad3540a86afcab8`;
INV_BATCH=`e1a7f717217a4132b5f5a4b81b10e95d`.
Pre-maintenance invocation=`58898c9dbe1e405a941c6b61e522c775`, PID1119177.
Both planned stop/starts lose prior in-memory holders; no continuity claim spans them.

Deployment used an atomic fsynced replacement and existing bounded locks/receipts.
Unit/argv, renewed credentials/profile and management code were unchanged across that
binary transition. No supervisor/acceptance flag, observer re-arm or timer suspension
for rollout. Final gateway active/running, NRestarts0 within INV_BATCH. Listener18444,
seed READY, strict served certificate and current NL/RU directory all verified.
Directory SHA `5f7d564508878395e71beafabaa7889367d3b96494c01d8637efe7a05be04e55`.
These are server readiness checks, not phone TUN/throughput acceptance.

Phone package `com.familyconnect.app.friends`, API31/ARM64, code84, existing signer and
UID10283 preserved. Installed APK pulled and native/payload checked against signed
receipt. No downgrade bypass, uninstall, cache/data clear, re-enrollment or private
identity/database reads. This verifies ordinary replacement without deletion, not a
content-level database audit. Ordinary launch succeeded; one bounded UID-filtered
AndroidRuntime/linker/libc startup-error sample contained0 new error lines. This is
not exhaustive crash/ANR or runtime testing. Last observed VPN transport/service absent;
no intentional CONNECT, support export or speed measurement was performed.

## Current absolute bounds and residual state

| Boundary | UTC |
| --- | --- |
| Authority and both grants expire |2026-10-18 08:57:40 |
| Next mandatory operator threshold, six-hour headroom |**2026-10-18 02:57:40** |
| Leaf and CRL expire |2026-10-17 12:58:21 |
| Leaf/CRL ordinary90-minute renewal threshold |2026-10-17 11:28:21 |
| Current directory issued |2026-10-17 09:00:55.525883713 |
| Conservative process bound |2026-10-17 13:00:53.262 |
| Current directory/context bound |2026-10-17 13:00:53.338499258 |
| Next scheduled run at final readback |2026-10-17 09:06:52.834534 |

Final evaluate exits0/NOOP with no due/alerts or mutations. This is not another renewal.
The timer is active/waiting; its service still retains the preceding scheduled
exit75/exit-code observation until another invocation. No reset-failed or manual
scheduled invocation was used to hide that historical result. Future scheduling is
not assumed complete. No active writer/owner/request remains; maintenance transaction
COMMITTED and cleanup verified. Leaf/CRL validity is earlier than runtime/directory.

## Return path, counts and remaining test

The immediate previous signed APK761430c0…2149b1f is privately preserved and matches
the same package/signer/code84; unchanged storage source supports compatible ordinary
replacement in either direction. Gateway079729e4…49639d is saved in the private remote
stage with exact SHA and metadata. **Neither rollback was executed.** Any future
binary-only return must preserve current credentials/floors and reacquire readiness/
locks; never restore old credential snapshots. Known old-pair performance limitations
are not claimed fixed by rollback.

Actions in this continuation: logical maintenance1, accepted request1, offline-root
signature1, operator apply1, resume0; renewal timer pause/restore1 each; gateway
maintenance stop/start1 plus gateway binary-rollout stop/start1. RU HTTP workflow
stop/start1 and directory-timer workflow stop/restore1. APK signing0/rebuild0/new
regression suites0; replace-install1/ordinary launch1; CONNECT/export/rollback0.
No emulator, new native-stats reader, public distribution, main/workflow/catalog edit.

**WAITING_FOR_OWNER_MOBILE_SPEED_CHECK.** Next is one normal restricted CONNECT on
the same mobile underlay, fresh app VPN-bound IP check and a small timed download
(record byte count, elapsed time and source). A VPN-OFF comparison must use the same
resource/underlay and an uncached transfer; one site is not a universal benchmark.
Do not report the previous local synthetic speedup as a mobile result. First failure
means normal OFF and a normal export, not repeated CONNECT/restart/install. No automatic
A→B, field trial, long soak or artificial burst test. Historical acceptance/causality,
chat handoff, supervisor and release status are not promoted.

Raw receipts, grants, requests/bundles, signing material, APKs and binaries stay private.
Only safe documentation/evidence is published; previous reports and dirty root worktree
remain untouched.
