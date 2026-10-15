# OWNER-CUMULATIVE-CLIENT-ACCEPTANCE-1-RESUME

**RESULT: WAITING_FOR_OWNER_ACTION — cumulative APK installed and read back;
CONNECT1/2 have not been performed.**

Input review: `7e93a596ef2d0e919485f94d8378f5e07f55e8c4`.
This resumes the remaining device steps after
[server recovery](2026-10-15-current4h-expired-recovery-deploy-and-restore-1.md).
The earlier [ENVIRONMENT_BLOCKED report](2026-10-15-owner-cumulative-client-acceptance-1.md)
is preserved as historical evidence, not rewritten as a failed client connection.

The short fresh server/owner preflight passed its installation prerequisites. One
ordinary `adb install -r` succeeded; the installed APK, embedded native, signer and
UID were verified. The normal launcher opened EXIT/FriendsActivity successfully.
The protected screen was not extracted, bypassed or operated through blind taps.
The currently selected route/transport needs owner confirmation before CONNECT.
No long-running wait or device attempt budget has been started.

## Exact installed identities

| Item | Observed value |
|---|---|
| Signed artifact and installed/pulled APK SHA256 | `3c733d2fc3a0ec377143b668244a4c7d6619ff24abe024da4ee9bfe31d140513` |
| Embedded `lib/arm64-v8a/libfc_restricted.so` SHA256 | `2a974350c168913ca8a217d3fc73f452fdd709c3619d0c690abd5d884c54b88c` |
| Original/rollback APK SHA256 | `fd3106170ceeb1e24dad6c8eacda4107b1ab09a6ee120ccf495d92d96841aa48` |
| Original embedded restricted native SHA256 | `cb3af31f62fdc1339df5f03374652ef6c62c4382ed10ef2d314bd6b610c989e2` |
| Original and installed signer certificate SHA256 | `67a90d1bfcd5a2c0666f0cff1b0ac5e43aaa661ca1196f89e879aa39fe20848a` |
| Package / UID before and after | `com.familyconnect.app.friends` / **10283** |
| Both versions | versionCode **84**, `0.1.18-research84-provisioning-seam` |
| Cumulative source inventory, from existing build receipt | `a4d489079e3da0df7fdd01b7977962b20ddbbf8605fbf682a349703a88b916d5` |

No rebuild, re-signing, alignment rewrite, version change or APK publication.
Signature verification succeeded for both retained APKs and the newly pulled
installed APK. This publication commit is not a new APK source identity.
There is one base APK and no reported splits. The verified original backup remains
available for the already authorized same-version, same-signer ordinary return.
A return was neither needed nor exercised; its success is not assumed from the file alone.

## Fresh environment and device timeline

All times in this table are **2026-10-15 UTC**.

| Time | Observation / evidence |
|---|---|
| 18:17:00–18:17:08 | Existing read-only RU/NL security and entry collectors: loaded baseline, active services, valid material and strict served chain |
| 18:17:23 | Saved owner selector matches the authorized device; original APK hash matches backup; UID10283; no VPN transport |
| Before install | Bounded current-invocation journal returns `bootstrap_seed_ready` at 17:37:22.264648; no fatal/panic in that selected result. Scoped writer query has only its own shell/grep, no matching controller/node process |
| 18:21:52–18:21:58 | One ordinary replace-install, exit0 / `Success`, no downgrade/uninstall/data clear |
| 18:24:01 | Device APK hash, pulled bytes, signature, embedded native and unchanged UID verified |
| 18:24:01–18:24:06 | Normal MAIN/LAUNCHER activity start: `Status: ok`; FriendsActivity focused, app process present, VPN OFF |
| 18:25:10 | Final device metadata: same cumulative APK/UID; FriendsActivity focused; ChatDeliveryService present; no VPN transport |

The first two host-side APK pull attempts could not write the destination because
the **host `/tmp` quota was exceeded**. The second attempt retained the exact
`Disk quota exceeded` error. Installed-device SHA had already matched. Readback was
completed to an existing Git-ignored, private disk-backed build-artifact directory;
there was **no second install**, Android permission bypass, deletion or client repair.
This is a collection interruption, not a product startup/traffic failure.

Android exit metadata records termination of the prior app process due to
`installPackageLI` (reason10, USER REQUESTED). The task therefore does not claim
zero process changes. After normal launch, the bounded UID-filtered
AndroidRuntime/linker/libc error query returned no new matching lines; the final
process remained present. This is a short launch observation, not restricted JNI,
native startup, long-running ANR or VPN acceptance.

The package, signer and UID are preserved through nondestructive replacement.
No re-enrollment was initiated; no vault, identity keys, messages or app databases
were read/copied/cleared to prove preservation. Full private-data equivalence and
completion of fresh delivery/ACK are not asserted. Normal foreground/background
application work was allowed, not replaced with the provisioning-block seam.

## Server binding and validity

The baseline configured/loaded SHA is unchanged:
`21f0a0fdc27b50c00ea922f0b716516e2422aedf1b3797369718f7d00070509a`.
At the fresh check: PID3903125, invocation
`c11ce23c7d124f2790fa9f35f13f5693`, active/running, NRestarts0, listener18444.
Loaded/configured argv agree and contain no acceptance/research trigger.
The seed-ready event belongs to that invocation; live provider probing was not
performed. A running PID is not a count of user sessions.

Strict served TLS: hostname/chain verification and expected leaf match PASS.
This check explicitly does **not** claim client mTLS or application-session READY.
RU delegation signature and directory binding pass. RU/NL CRL signatures and
CRL number27096 agree; directory SHA is
`d4fa4a8b785e2d677006c02c5f2cca66e220405c4f44dd726d084d690db4e280`,
issued at17:37:22.261585216 UTC for the current runtime. Grant aggregate: two,
unrevoked, revisions4/6; no grant list is published.

No node owner marker; coordinator transaction COMMITTED. RU HTTP active; current4h
timer enabled/active/waiting, last service inactive/success/exit0; directory timer
active, legacy writer timer disabled/inactive. No evaluation or renewal was invoked
by this task. The latest service result is observed, not invented as a new renewal
PASS. No second recovery/checkpoint/source-map audit or120-second server-only test.

| Boundary | Absolute UTC |
|---|---|
| Fresh server collectors | **2026-10-15 18:17:00–18:17:08** |
| Authority/delegation and current grants expire | **2026-10-16 17:34:58** |
| Leaf expiry / CRL nextUpdate, earliest observed bound | **2026-10-15 21:37:06** |
| Directory expires | 2026-10-15 21:37:17.752732812 |
| Conservative process lifetime boundary | approximately2026-10-15 21:37:17.622 |
| Existing next operator threshold, unchanged policy | 2026-10-16 11:34:58 |
| Latest CONNECT1 start for18minutes under these unchanged bounds | **2026-10-15 21:19:06** |

The server window was sufficient at preflight. At final device readback18:25:10,
the observed earliest limit would leave11516seconds, of which1080seconds are the
agreed entire device sequence including cleanup. That subtraction is conditional
on unchanged material, not a new server check or a promise of future readiness.
Preparation/owner delay consumes the remainder. Recheck current prerequisites
briefly when the owner is ready; do not require the old invocation/directory if
ordinary current4h has legitimately changed them. Do not repeat recovery/sign/install.

## Attempt matrix and missing evidence

| Field | Result at this checkpoint |
|---|---|
| CONNECT1 / CONNECT2 | **NOT_RUN / NOT_RUN**, both intentional attempts unspent |
| Dedicated READY / native attach / app CONNECTED | NOT_RUN; launcher start is not CONNECTED |
| Owner HTTPS egress / DNS path | NOT_MEASURED / NOT_MEASURED |
| Stability240seconds after READY | NOT_RUN |
| CHAT_FIRST_PRECONDITION | NOT_PROVEN; service presence does not prove an independent holder |
| Chat recovery / borrowing / HANDOFF_ON_DEVICE | NOT_PROVEN / NOT_PROVEN / NOT_PROVEN |
| NORMAL_SUPPORT_EXPORT / NORMAL_EXPORT_ON_DEVICE | NOT_RUN; no new Share or cache rotation |
| FIRST_FAILURE | No new VPN attempt/failure; host readback interruption described above |
| First missing prerequisite | Owner confirmation of the supported restricted route/transport in the UI |
| CLIENT_DEVICE_SMOKE / DEVICE_ACCEPTANCE | NOT_RUN / NOT_RUN |
| SUPERVISOR_PRODUCTION_ACCEPTANCE | **FAIL**, historical result unchanged |
| HISTORICAL_CAUSAL_BINDING | **NOT_PROVEN**, not established by this install |

No new connection/incident/startup/session tag is assigned to this task. Historical
C1/I1 is not reused. No new native stats poller was started; the installed normal
diagnostic pipeline remains the evidence path. Its cause-fidelity/export behavior
on a new VPN attempt remains to be measured, not inferred from host tests.

## Action counts and final state

| Action | Count / scope |
|---|---|
| Replace-install / normal launcher start | **1 / 1** |
| Install-induced prior process termination | **1 observed**, not an explicit force-stop |
| Intentional CONNECT / DISCONNECT / client rollback | **0 / 0 / 0** |
| UI taps / protected screen extraction / native polls | **0 / 0 / 0** |
| Support export / export-cache rotation | **0 / 0** |
| Build / resign / release / APK upload | **0 / 0 / 0 / 0** |
| Uninstall / clear / downgrade bypass / re-enrollment action | **0 / 0 / 0 / 0** |
| Gateway/management deployment, restart/reset, config change | **0** |
| Administrative credential renewal/sign/apply / scheduler changes | **0 / 0** |
| Fault injection / intentional provider operations | **0 / 0** |
| Ordinary app/provider/provisioning/ACK/lease/background activity | Allowed, not fully counted; **not asserted zero** |

At18:25:10 UTC: cumulative client remains privately installed, app process present,
VPN OFF. No client regression requiring rollback is established. Gateway executable,
management/configuration and credentials received no administrative changes from
this task; ordinary background activity remains possible. There is no claim that
all production state was unchanged.

Safe selected [receipt](evidence/2026-10-15-owner-cumulative-client-resume-checkpoint.json)
is published with this report. Raw metadata/logs, APK readback and historical export
remain private. No APK, diagnostic payload, user/device selector, grant IDs, room
URL, key or secret is added to Git. Original dirty checkout and frozen snapshots
are preserved. Only this report, receipt, STATUS, PLAN and publication index change.

## Resume point — owner action required

On the opened EXIT main screen, select **Нидерланды → Telemost** (not Auto),
leave **Подключить** unpressed, and confirm readiness. The selectors and label
are checked against the retained cumulative FriendsActivity, not stale root code;
their actual current values were not read through the protected screen.

Then continue with a short freshness/owner-state check and existing bounded evidence
collection before the first intentional CONNECT. No reinstall/re-sign/full audit.
Only after successful CONNECT1, traffic and240seconds may CONNECT2 run. On the first
unexpected startup/traffic failure, preserve/export and clean up without CONNECT2.
One normal support export belongs after that failure or the completed sequence,
not to this waiting checkpoint. Keep the agreed18-minute CONNECT1-to-cleanup budget.
