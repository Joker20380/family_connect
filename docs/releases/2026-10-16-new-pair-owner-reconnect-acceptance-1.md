# NEW-PAIR-OWNER-RECONNECT-ACCEPTANCE-1

## Result at the preparation checkpoint

**RESULT=WAITING_FOR_OWNER_ACTION.** Existing C_NEW was signed without rebuilding,
verified and installed once over the expected owner application. Ordinary launch
succeeded; final bounded device observation is VPN OFF. **CONNECT_A=NOT_RUN;
CONNECT_B=NOT_RUN; NEW_PAIR_DEVICE_RECONNECT=NOT_RUN**, not PASS or transport FAIL.
The first-CONNECT 18-minute window has not started. Current owner availability for
the complete sequence has not been confirmed; no long wait or automatic CONNECT.

Input review publication: `f6dfd846c25dd94fee14d89e0f14e02c96299dd6`.
This is a new device-acceptance episode. The previous [single smoke PASS](2026-10-15-owner-cumulative-client-acceptance-1-resume.md),
[reconnect FAIL](2026-10-15-owner-restricted-reconnect-and-chat-1.md),
[local new-pair acceptance](2026-10-16-gateway-transport-progress-burst-candidate-1.md)
and [gateway rollout](2026-10-16-gateway-transport-progress-live-1.md) retain their
original scope and outcomes. No historical attempt or failure is rewritten.

## Signed and installed identities

| Identity | Exact value |
| --- | --- |
| Existing unsigned APK | `cc5b883395c59d2f76f4cf8ce1d787fa764c1fac2936c9148f9876697d2c5013` |
| SIGNED_C_NEW_SHA256 | `28772ccb111623741dc12f14e387f1535095502748165ab87d51fdde751c004b` |
| INSTALLED_C_NEW_SHA256 | `28772ccb111623741dc12f14e387f1535095502748165ab87d51fdde751c004b` |
| C_NEW embedded NATIVE_SHA256 | `253e0e15f38223288571d3e682f6876269aa9c6d1c0c5157588ed8287ba6f3a3` |
| Cumulative source inventory | `c2dc3dd860044b31696893244995cbc5cc8eb805ee34319df99cce085cf40d08` |
| Existing build receipt SHA256 | `e75f67b360b4f05b26bae2760bbef804e4ddd507904af33ff2f581d9bd66a5ab` |
| Immediately previous APK / preserved rollback | `3c733d2fc3a0ec377143b668244a4c7d6619ff24abe024da4ee9bfe31d140513` |
| Previous embedded native | `2a974350c168913ca8a217d3fc73f452fdd709c3619d0c690abd5d884c54b88c` |
| Both signer certificates, SHA256 | `67a90d1bfcd5a2c0666f0cff1b0ac5e43aaa661ca1196f89e879aa39fe20848a` |
| Package / actual Android UID | `com.familyconnect.app.friends` / `10283` |
| Both version codes / names | `84` / `0.1.18-research84-provisioning-seam` |

The retained successful build receipt identifies the exact input APK and native.
The canonical35-file source inventory digest and every retained file hash were
rechecked; the installed provisioning/restricted build assets carry that digest.
The retained standalone native artifact matches the installed embedded native.
No Gradle/native rebuild or host/race/JVM suite was repeated. The existing
`sign_android_vault.credentials/sign` workflow and its signing-only local vault
selection were used. Keystore/password remained in memory/memfd; no new key,
plaintext secret export, argv password or helper APK. Signed size is 56,003,475 bytes.
Its digest differs from both the unsigned artifact and the previous installed APK.

`apksigner verify` and the pinned single signer pass. 16 KiB alignment passes for
unsigned, signed and preserved rollback APKs. Every DEX/native entry and every
unsigned non-signature ZIP entry is byte-identical after signing, including the
manifest and assets. The application remains non-debuggable. A pulled readback of
the actually installed APK matches the new signed digest; its signature and
embedded native digest were independently checked. No APK is published.

## Replacement and preservation boundary

At08:54:59UTC, scoped ADB found exactly one authorized device, the expected previous
APK, UID10283, code84, PID26459 and no VPN transport. The pre-install guard repeated
package/hash/UID and VPN-OFF checks immediately before the single ordinary
`adb install -r`. A different build or active VPN would have stopped replacement.

Replacement succeeded; installed readback completed **09:04:25UTC**. One ordinary
launcher start completed **09:04:26UTC**, producing app PID**30105**. Installation
replaces the earlier process; no claim of continuity across installation is made.
The future same-process requirement applies only to A→B after this point.

At **09:06:21UTC**, FriendsActivity is focused, PID30105 remains present, VPN transport
is absent, and the bounded UID-filtered error sample contains no post-install
AndroidRuntime/linker/libc error lines. At09:07:11UTC, package-scoped exit-info has
no new crash/ANR exit: the latest record is old PID26459, USER REQUESTED, at
09:04:21.149UTC during replacement. This is a bounded startup observation, not proof
of successful restricted JNI attach or future traffic. ChatDeliveryService presence
is not evidence of online UI, mailbox completion or VPN borrowing.

SIGNER_UID_AND_DATA_PRESERVATION: package, signer, versionCode and UID preserved;
no uninstall, `-d`, data/cache clear, root, re-enrollment or identity/database read.
Data preservation is the normal in-place replacement boundary, **not a byte-level
private-storage comparison**. Existing cumulative-change records describe ownership/
diagnostic changes, not identity/database migrations; later transport corrections
change the ReliableStream writer and Telemost receive reserve. No incompatible
storage migration is introduced by those declared deltas. Equal actual package,
signer and versionCode support ordinary replacement in either direction.

The immediately previous signed APK is copied into the protected task capsule and
signature/hash/alignment verified. **CLIENT_ROLLBACK=NOT_PERFORMED.** Availability
of that copy is not a successful rollback test. One compatible client-only return
is reserved for a serious new usability regression after preserving evidence;
never uninstall/downgrade bypass. The old client's known transport limits remain.
No serious new regression requiring rollback was observed in this preparation.

## Fresh gateway readiness and natural changes

The retained bounded read-only collectors were reused; no server suite,
13-module/checkpoint audit or separate120-second stability exercise. The management/
configuration inventory part of the extra collector was omitted. Raw receipts remain
private. The initial sandbox SSH attempt was denied by local SSH configuration access;
an outside-sandbox inline collector timed out after70seconds without a complete
receipt. A narrow runtime readback succeeded, and the retained collector sent through
stdin completed. These are collection limitations, not a proven gateway failure.

Fresh observations **09:00:49–09:01:01UTC** establish:

| Boundary | Observation |
| --- | --- |
| Loaded gateway executable | `a537257162348afc35b1ebc08755d8c5dc1cd90e74c49e3987fb3eb81885e61f` |
| Current process / invocation | PID265201 / `d578312a01514ea98e136a94bae5feec` |
| Service | active/running, NRestarts0, Result success |
| Runtime start / seed READY | 08:43:56UTC / 08:44:00.320891UTC, current invocation |
| Listener / strict served chain | listener18444 present; strict TLS chain and configured served-leaf match PASS |
| Current directory SHA256 | `90c5bed9e02d93ddf8ee0911b2d7a719f83569897b2efcb206f1d4619716cdbd` |
| Runtime/directory/RU binding | issued08:44:00.31830657UTC after current start; current-invocation seed receipt; identical NL/RU digest and scope checks PASS |
| Leaf / CRL | newly issued08:43:43UTC, both expire12:43:43UTC; CRL27102 |
| Authority / RU delegation | valid until17:34:58UTC; signatures and current binding verified |
| Directory / conservative process boundary | 12:43:56.594775648UTC / approximately12:43:56UTC |
| Maintenance / recovery | no pending node-owner marker or matching writer on either host; RU transaction COMMITTED, no first_cause |
| Existing automation | current4h timer active/waiting; last service success/inactive; directory timer active/waiting |

The prior report's08:42:45UTC renewal threshold was **not assumed completed**. The
newly issued material, committed scheduled transaction, new runtime and seed above
are fresh evidence of external scheduled activity. They are not client-caused changes
or changes performed by this task. No old PID/invocation/directory was required.

The existing read-only current4h evaluate completed **09:02:50UTC**: NOOP, due=[],
alerts=[], files_changed0, remote_writes0, restarts0. Reported headroom: leaf/CRL
13,254seconds, authority/grants30,729seconds. The previously documented operator
threshold11:34:58UTC remains earlier than the current leaf/CRL expiry. At this check
an18-minute device sequence plus cleanup fits; this is **not a future readiness
guarantee**. Owner-specific delivery/ACK is not inferred from these server checks.
No active maintenance was observed, so no maintenance wait/recheck was needed.

## Unfinished device acceptance and continuation

Current availability for the owner sequence must be obtained explicitly; interaction
with a signing password dialog is not confirmation of availability for A→B. Resume
with one short fresh environment/device/PID check and rebind the prepared bounded
collector windows to that actual invocation. Do not reinstall or sign again.
Allow normal current delivery and ACK; never enable the provisioning-block seam or
restore stale cache. If environment is unusable, record ENVIRONMENT_BLOCKED without
repairing the gateway in this task. If maintenance is already running, permit its
normal bounded completion and one readiness recheck, not indefinite waiting.

The owner sequence is prepared in advance: restricted CONNECT A → successful ordinary
VPN-bound Check IP → DISCONNECT → **immediately after local OFF, CONNECT B without an
agent-response wait or a server-slot wait** → fresh VPN-bound Check IP → fixed240seconds
after B READY → repeat Check IP → normal DISCONNECT → one ordinary support export.
Maximum two intentional CONNECTs, total18minutes from A CONNECT through final OFF;
no app restart between A and B. On the first unexpected startup/traffic failure, skip
further CONNECTs, preserve first failure, disconnect and export. No timing retry.

Capture A's available short readiness/traffic observations before it becomes an
archive, using the existing bounded sources and owner result, without another native
stats reader. Distinguish UI-reported IP from an actual saved response. Obtain
session-bound DNS evidence independently. Ordinary mailbox/sync while VPN and after
OFF is optional within the remaining window; no correspondence reads or new messages.
Independent chat, borrowing and handoff require their own evidence and do not block
the core sequence when absent. One support export follows the sequence/first failure
through normal cache rotation; raw JSON stays private before analysis.

## Required result fields at this checkpoint

| Field | Result |
| --- | --- |
| RESULT | WAITING_FOR_OWNER_ACTION |
| SIGNED_C_NEW_SHA256 / INSTALLED_C_NEW_SHA256 / NATIVE_SHA256 | Exact verified identities above |
| SIGNER_UID_AND_DATA_PRESERVATION | In-place boundary verified; private storage not read |
| CURRENT_GATEWAY_EXECUTABLE_AND_INVOCATION | Exact current-check values above; refresh before A |
| CONNECT_A / CONNECT_B | NOT_RUN / NOT_RUN |
| OFF_A_TO_CONNECT_B_INTERVAL | NOT_MEASURED |
| APP_PROCESS_CONTINUITY_A_B | NOT_TESTED; post-install PID30105 recorded |
| DEDICATED_NATIVE_APP_READY_A_B | NOT_RUN / NOT_RUN |
| SESSION_A_B_CLIENT_SERVER_BINDING | NOT_AVAILABLE; no new A/B sessions assigned |
| OWNER_HTTPS_A / B_INITIAL / B_AFTER_240S | NOT_RUN / NOT_RUN / NOT_RUN |
| DNS_A / DNS_B | NOT_MEASURED / NOT_MEASURED; absent evidence is not zero errors |
| B_STABILITY_240S | NOT_RUN |
| CHAT_UI_ONLINE / CHAT_OPERATION_COMPLETED | NOT_MEASURED / NOT_MEASURED |
| CHAT_OPERATION / BORROWING / DIRECT-BORROWED-INDEPENDENT_RESTRICTED | NOT_MEASURED / NOT_PROVEN / NOT_CLASSIFIED |
| HANDOFF_ON_DEVICE | NOT_PROVEN |
| NORMAL_EXPORT_AND_RETENTION_LIMITS | No export yet; each surface's retained/drop counters NOT_OBSERVED, not zero |
| FIRST_FAILURE | No new A/B trial; none observed in bounded post-install checks |
| EXTERNAL_ENVIRONMENT_CHANGE | Natural scheduled material/runtime/directory change recorded separately |
| FINAL_DEVICE_STATE / CLIENT_ROLLBACK | New signed APK retained privately; last observed VPN OFF, app30105 / rollback0 |
| ACTION_COUNTS | Signing1; replace-install1; ordinary launch1; intentional CONNECT0/2; export0; rollback0 |
| REMOTE_HEAD_SHA / REPORT_URL | Supplied by verified publication receipt/final response; this report is on the existing review branch, not main |

Additional counts: rebuild0, host/race/JVM reruns0, new native-stats readers0, helper0,
new key0, force-stop0, uninstall/data/cache clear0, manual renewal/recovery0,
gateway/management deployment/restart0, scheduler/config/network/fault changes0,
release/main/catalog changes0. Ordinary background provisioning/chat effects are not
counted as intentional VPN CONNECTs or claimed absent without evidence.

**LIVE_BURST_ENVELOPE=NOT_DIRECTLY_EXERCISED. SUPERVISOR_ACCEPTANCE=UNCHANGED,
not promoted. HISTORICAL_B_CAUSAL_BINDING=NOT_PROVEN.** No all-suite-green or release
authorization follows from this preparation or a possible later bounded PASS.

Only this safe report, STATUS, PLAN and publication index are published. Exact APKs,
rollback, selector, raw device/server receipts and operational wrappers stay in the
protected ignored local task capsule. No room URLs, product-user identifiers,
private logs, keys or databases are included. Public release/catalog/invitation
versions and download links are unchanged; this same-version private replacement
is not a public distribution. Preserve the dirty main checkout; publication uses
the existing clean detached review worktree based on the input SHA.
