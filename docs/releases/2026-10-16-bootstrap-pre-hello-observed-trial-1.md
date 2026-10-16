# BOOTSTRAP-PRE-HELLO-OBSERVED-TRIAL-1

16 October2026. **RESULT=WAITING_FOR_OWNER_ACTION** — installation checkpoint,
not a completed observed trial. Last device observation:10:49:01UTC.
The diagnostic APK is signed and installed privately; ordinary launch succeeds,
VPN OFF. **OWNER_CONNECT_COUNT=0; gateway controlled restarts=0; capture activation=0.**
No post-install owner readiness confirmation has been received at this checkpoint.
Signing interaction is not that confirmation. Do not sign or install again on resume.

Input review: `53c2eecfe63b5fe5226d4323f536e46dabd875e7`.
[Diagnostic source/build result](2026-10-16-bootstrap-pre-hello-correlation-1.md),
[existing runbook](../../research/bootstrap-pre-hello-20261016/RUNBOOK.md),
[correlation helper](../../research/bootstrap-pre-hello-20261016/correlate.py).
This task authorizes one future observed restricted CONNECT, not A→B acceptance,
a startup fix, a public release, or supervisor promotion.

## Signed and installed identities

| Item | SHA256 |
|---|---|
| Retained diagnostic unsigned APK | `b2a4b76b3218ec06f3409154a1a14f71bf4feff3206be3282c25852eabdd35ca` |
| **Signed and installed diagnostic APK** | `8e5579f04de91e4ec00e3e79271dbb0f380b1ed91945ff89016aa50d274a8845` |
| **Installed embedded native** | `be70a66ccc2bcbf0478915fd414c32de3bedb2a0ae0c3222a53e65eebd0a92b2` |
| Cumulative source inventory, NOT a Git commit | `b36c4a21ee6cf04acb192a0e6d140fa565b3e5ae75f6fc8d028d029c3152781d` |
| Retained build receipt | `98ad43326e31ad4c3f7311f6c1f6a998dbc71a3bba6db183219df681a75ba356` |
| Previous installed APK / available rollback artifact | `3c733d2fc3a0ec377143b668244a4c7d6619ff24abe024da4ee9bfe31d140513` |
| Previous embedded native | `2a974350c168913ca8a217d3fc73f452fdd709c3619d0c690abd5d884c54b88c` |
| Same verified signing certificate | `67a90d1bfcd5a2c0666f0cff1b0ac5e43aaa661ca1196f89e879aa39fe20848a` |
| Required gateway executable; fresh live readback still pending | `a537257162348afc35b1ebc08755d8c5dc1cd90e74c49e3987fb3eb81885e61f` |

Package `com.familyconnect.app.friends`, versionCode84,
versionName `0.1.18-research84-provisioning-seam`, non-debuggable.
Signing used the existing vault workflow and previous key; no plaintext key/password
export to argv, logs, Git or chat. Signed APK56,007,571 bytes; hash differs from both
unsigned and previous installed artifacts. Signature and16KiB alignment verified.
All unsigned non-signature ZIP entries are preserved, including DEX/native/manifest;
no rebuild, versionCode workaround, permissions change or product patch.

One ordinary `install -r`, no `-d`, uninstall, data/cache clear or re-enrollment.
Actual installed public APK was read back, hashed and signature/native verified.
Actual UID10283 before and after; package/version/signer unchanged. This supports
ordinary replace-install data preservation, not a private identity/database audit:
no private identity/database reads were performed. Previous signed APK is retained
and verified; matching package/signer/code and the unchanged-storage diagnostic delta
permit an ordinary compatible replacement if a newly serious usability regression
requires it. No rollback has been performed in this task.

## Preparation timeline (UTC,16October)

| Time | Observation/action |
|---|---|
|10:45:16|Retained build/APK/native checked; previous signed APK copied privately and verified.|
|10:45:27|One authorized Android device; actual previous APK matches expectation, UID10283, PID4826, VPN OFF.|
|10:46:01|Existing-workflow signing finishes; signature/alignment/payload checks PASS.|
|10:48:51.861|Immediate installed hash/UID/version/OFF guards pass; one replace-install begins.|
|10:48:57.055|ADB install returns Success.|
|10:48:59.737|Installed APK readback/signature/native match; UID10283; VPN OFF.|
|10:49:01.083|Ordinary launcher returns Status:ok, new PID12008; VPN OFF; zero recent matching error lines in one bounded UID-filtered logcat sample.|

The logcat sample covers AndroidRuntime/linker/libc errors after install, not a long
startup stability or exhaustive ANR check. No observed startup failure in this sample;
no claim of successful restricted transport or network restoration. Installation may
replace the old process; there has been no CONNECT in the new process.
Private receipts and APKs remain in the ignored task directory; none is published.

## Resume gate and prepared scope

1. Obtain fresh **post-install** owner confirmation of readiness for one CONNECT and
   VPN OFF. Until then do not activate capture/restart or spend its15-minute window.
   On resume use the installed artifact and existing receipts; no repeat signing/install.
2. Perform short fresh bounded server/device prerequisites, not historical journal
   searches or suites: actual loaded SHA, invocation, seed/strict served chain,
   current runtime-bound RU directory, material/process validity and ordinary
   scheduling, no pending recovery/maintenance/quiescence. Current values are not
   yet read in this task; old expiry/PID/directory values are not guarantees.
3. Save bounded pre-restart observations using existing sources. Active restricted
   session count may remain UNKNOWN; authorized interruption is not zero outage.
   Prepare exact removal of only this task's temporary startup delta, preserving
   foreign changes, before applying it under existing current4h/service coordination.
4. Only then add existing `--research-admission-evidence` with a fresh absolute
   private path and required directory permissions. Do not precreate its exclusive
   output file or add other flags. One coordinated restart of the same executable
   is authorized. This is an argv/config mutation, NOT read-only observation.
5. Restart destroys prior in-memory Broker holders. Record old/new invocation and
   state loss; it does not continue historical A. Recheck loaded SHA, seed/TLS/RU
   runtime publication and readable capture header schema/PID/invocation/enabled,
   until_ms/event_limit512. Capture lasts15minutes from process start. Require enough
   remaining time for normal startup budget, outcome, OFF and event preservation;
   otherwise no CONNECT and no automatic re-arm/restart.
6. Give the owner the complete one-shot sequence before CONNECT: one ordinary
   restricted CONNECT; if failure, no retry and normal OFF without waiting for agent;
   if success, dedicated/app readiness and one VPN-bound HTTPS/IP check, then OFF.
   One normal support export afterwards; retrieve the newly generated file, not a
   previous export. No second CONNECT, reconnect,240s stability or burst workload.
7. Preserve raw export/capture privately with hashes, receipt time and provenance;
   analyze copies. Prefer bounded waiting to the collector's known natural expiry.
   Missing footer while running is IN_PROGRESS, not write failure. No footer-only
   restart. Remove this task's temporary next-start configuration without another
   process restart where supported; do not claim the running argv lost its flag.

Fresh owner confirmation and subsequent gates remain outstanding, not presumed PASS.
No server SSH/readback, config write or restart has occurred in this checkpoint.
No future capture file exists yet; there is no temporary delta to remove at present.

## Correlation and limits to retain

Match server Exchange exactly to the new startup's `bootstrap_exchanges[]`, keeping
Family authentication separate. Consider `bootstrap_exchanges_dropped` and the
independently retained `observation.bootstrap_exchange_tag`, including a tag omitted
from the capped array. Dedicated session_tag is a different identifier. Publish only
consistent requester/holder aliases, never real tags, nonce, identities or room URLs.

For matched wait, bind holder generation/exchange/state/same_identity; generation
also joins existing dedicated traces. Empty-Exchange release/cleanup events join by
holder generation/exchange, not nearest timestamp. Role may remain UNKNOWN; ACTIVE
is not remote health. Local cleanup is not server slot removal. Late cancellation
or exchange_end must not replace first failure. HELLO send completion is not receive.

Check header/footer, sequence/written/limited, invocation/PID and actual event-window
coverage. The helper's COMPLETE_WINDOW tests startup inclusion only; it does not by
itself establish coverage of the whole significant wait. Incomplete traces support
positive retained facts with scope, never negative "holder absent" conclusions.
No observed chat-first premise yet; ChatDeliveryService/online alone cannot prove it.
Success in the restarted environment without that premise means NOT_REPRODUCED,
not a repaired or retrospectively explained historical failure.

## Requested result fields at this checkpoint

| Field | State |
|---|---|
| RESULT | WAITING_FOR_OWNER_ACTION; experiment not yet started |
| SIGNED_AND_INSTALLED_APK / NATIVE | Exact hashes above; verified |
| GATEWAY_EXECUTABLE_UNCHANGED | No gateway mutation by task; fresh loaded identity pending |
| OLD_TO_NEW_INVOCATION_AND_STATE_LOSS | NOT_RUN; no controlled restart |
| CAPTURE_HEADER_FOOTER_COMPLETENESS | NOT_ACTIVATED; no capture claim |
| OWNER_CONNECT_COUNT | 0 |
| CLIENT_EARLY_TAG_TO_SERVER_EXCHANGE | NOT_MEASURED on device |
| MATCHED_ADMISSION_SEQUENCE | NOT_MEASURED |
| REQUESTER_TO_HOLDER / HOLDER_ROLE | NOT_MEASURED / UNKNOWN |
| HELLO_SENT / HELLO_RECEIVED | NOT_MEASURED / NOT_MEASURED |
| FIRST_FAILURE_OR_SUCCESS | No trial attempt; ordinary app launch succeeds |
| OBSERVED_PREMISE / NOT_REPRODUCED_LIMITS | Premise not observed; no trial outcome yet |
| NORMAL_EXPORT_ON_DEVICE | NOT_REQUESTED;0 new exports |
| FINAL_VPN_APP_GATEWAY_STATE | Checkpoint VPN OFF/PID12008/diagnostic APK retained; gateway not touched |
| TEMPORARY_CAPTURE_CONFIG_CLEANUP | NOT_APPLICABLE_YET; no delta applied |
| ACTION_COUNTS | signing1, install1, ordinary launch1, CONNECT0, task DISCONNECT0, HTTPS0, export0, rollback0, SSH0, controlled restart0, config mutation0, rebuild0, extra native readers0 |

Review-only checkpoint publication; remote HEAD/readback belongs to the publication
receipt, not the source-inventory identity. No APK/key/raw logs/export/JSONL published.
**HISTORICAL_A_CAUSE=NOT_PROVEN; HISTORICAL_B_CAUSAL_BINDING=NOT_PROVEN.**
Historical A/B/smoke/reconnect reports remain unchanged. Full device/supervisor
acceptance stays open; this diagnostic build is not a startup fix or public release.
