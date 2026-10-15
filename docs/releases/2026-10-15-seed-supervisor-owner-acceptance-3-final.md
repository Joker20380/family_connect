# SEED-SUPERVISOR-OWNER-ACCEPTANCE-3-FINAL = FAIL

First failed product boundary: ordinary owner HTTPS/DNS over the established
Android VPN, BEFORE the planned WS1011. Chrome's actual page for
https://api.ipify.org/?format=json reports DNS_PROBE_FINISHED_NO_INTERNET.
NL HTTPS egress was not established. No trigger or second CONNECT was attempted
after this failed baseline traffic check. One authorized rollback completed.

This is a failed production acceptance episode, not a demonstrated failure of
same-room recovery after WS1011: that phase was NOT_RUN. Neither a helper limitation
nor maintenance-due health is used as the cause. No new helper/evaluator work is
required by this report. A later bootstrap challenge timeout is recorded separately;
it is not asserted to be the proven root cause of the browser DNS failure.

## Timeline (UTC,15.10.2026)

-06:45:10: the single fresh starting readback passes90/180m. Leaf122.43m,
  CRL107.40m, grants256.50m, authority256.40m. Previous120m stop is reclassified
  START_WINDOW_POLICY_MISS; previous maintenance-due block remains superseded.
-06:48:10: `готов` accepted as OPERATOR_READY_NOW; device/public services checked
  by06:48:52: VPN OFF, app and ChatDeliveryService ON. No new readiness gate asked.
-06:51:23.600: exact candidate loaded/next after the one controlled stop/start;
  startup is within5m of acknowledgement. PID3516748, invocation
  3e6421a73c3e40b09addffa44a4f4dc0, NRestarts0. Permanent unit unchanged;
  runtime argv differs only by the approved flag. Transient drop-in removed and
  daemon-reload completed; future ExecStart has no research flag.
-06:51:27.863: TARGET_AVAILABLE generation1/ACTIVE and directory published.
  Requested prelive interval120s ends06:53:27.863. Postcheck readbacks completed
  06:54:48 NL/06:55:10 RU, confirming the same process, strict served chain PASS,
  current unchanged credentials and RU/NL equality. No longer prelive threshold
  was introduced; postcheck/collection elapsed time is stated rather than hidden.
- First physical CONNECT instructed after postcheck. Android records full VPN
  creation06:55:43.785: TUN addresses10.79.0.2/fd79:fc::2, both default routes,
  DNS10.79.0.1, owner UID10283, all UID range0–99999, bypassable=false.
  The existing native code only attaches this TUN after its ready phase; explicit
  per-owner descriptor/native-input digest receipts were not collected.
- Candidate journal records GATEWAY_SESSION ESTABLISHED, RTP/VP8 delivery and
  Family auth. Later06:57:50.482 bootstrap_exchange_rejected has
  stage=challenge/reason=context_deadline. The initial observation that CONNECT
  had not established a VPN was corrected by the Android connectivity evidence.
- Normal Chrome HTTPS request was launched without ADB input injection or another
  CONNECT. `https-before.xml` contains DNS_PROBE_FINISHED_NO_INTERNET, not an
  external IP success response. This fails the ordinary HTTPS/DNS product gate.
-07:05:33.232: first-failure/process/control evidence saved before rollback.
  Candidate still PID3516748/same invocation/NRestarts0, D unchanged, no recovery
  receipts or natural fatal receipt. Trigger remained NOT_TRIGGERED.
-07:05:36.326: the sole rollback restores exact baseline loaded/next and original
  argv. New PID3525336, invocation9860ce9589064656859d5a2f6bb32deb, NRestarts0.
  This invocation/directory change is the explicit rollback, not a WS1011 restart.
-07:09:07: owner VPN OFF, app PID26585 and ChatDeliveryService ON; helpers absent,
  APK/UID/version/install times unchanged; temporary phone UI file absent.
-07:12:16.268: all copied remote receipts hash-verified, task-owned staging removed;
  policy/control directory/drop-in absent. Cleanup completed27m06s after starting
  readback, within30m and before07:15:10 deadline. No maintenance was run.

## Required fields

| Field | Outcome |
|---|---|
| WORKTREE_SAFETY | PASS; isolated only;1912 main paths/HEAD/index exactly unchanged during this continuation |
| FROZEN_CANDIDATE_IDENTITY | PASS; source134083d87773dacc038c9593afdaff0c57ea951d; binary53beb661cab014c32494fa8d7384f9565300311ef467e62ae9f8c20201e5138f; no rebuild |
| CREDENTIAL_WINDOW | PASS at the authorized90/180m start gate; all credential hashes unchanged through cleanup |
| CONTROLLER_STATE | DEGRADED_ACKNOWLEDGED_FOR_BOUNDED_ACCEPTANCE; latest MAINTENANCE_REQUIRED/mutations0; replacement timer active, old timer disabled; no renewal transaction started |
| DIRECTORY_BASELINE | PASS; RU/NL equality and issuer delegation valid; predeployment efb8121f…f62195 |
| TLS_PROBE_LAUNCH_SUCCESSOR | EXCLUDED; no further build/test/install |
| TLS_PROBE_CORE_UNCHANGED | PASS retained; no TLS Probe code touched |
| OPERATOR_GATE | OPERATOR_READY_NOW accepted once; physical owner available |
| TRANSIENT_POLICY | CREATED/VERIFIED/REMOVED; root:9790750 parent, root:9790640 file, TTL<25m; service979 read allowed/write/replace/parent write denied |
| DEPLOYMENT | PASS; exact loaded/next, single controlled restart, permanent unit unchanged, future flag absent |
| PRELIVE | Stable candidate/ACTIVE seed, strict served chain PASS, unchanged credentials, no natural fatal/renewal; see exact timing above |
| FIRST_OWNER_CONNECT | FULL_ANDROID_VPN_ESTABLISHED; ordinary HTTPS/DNS FAILED |
| POSTDEPLOY_DIRECTORY_RUNTIME_BINDING | Authenticated server fetch/READY ACK and candidate runtime events observed; exact client response/native-input digest chain NOT_FULLY_PROVEN |
| FULL_TUNNEL_EGRESS | FAIL; full TUN established but Chrome DNS/HTTPS test failed; NL egress not proven |
| CONTROLLED_OR_NATURAL_WS1011 | NOT_RUN; executions0; no natural qualifying event accepted |
| SUPERVISOR_RECOVERY | NOT_RUN; not a demonstrated recovery defect |
| PROCESS_CONTINUITY | Candidate stable until intentional rollback; after-trigger proof NOT_RUN |
| SEED_ROOM_CONTINUITY | Generation1 target recorded; after-trigger proof NOT_RUN |
| DIRECTORY_CONTINUITY | Candidate D unchanged through pre-rollback snapshot; after-trigger proof NOT_RUN |
| PION_ICE_RTP_RECOVERY | Initial seed readiness/RTP/VP8 observed; recovery NOT_RUN |
| POST_RECOVERY_HTTPS_DNS | NOT_RUN; pre-trigger traffic check already failed |
| PERSISTENT_STREAM_CONTINUITY | NOT_MEASURED; intentionally excluded, not the failure cause |
| OLD_CACHE_RECONNECT | NOT_RUN; CONNECT2 not requested after failed first traffic gate |
| ZERO_DIRECT_PROVISIONING | NOT_RUN for old-cache test; normal first-connection/background fetch/ACK occurred |
| GATECONTROL_CLEANUP | PASS_NOT_ARMED; exact existing helper installed then removed, arm0/cleanup instrumentation0 |
| HELPER_CLEANUP | PASS; owner helpers absent; no new TLS endpoint/cert/token; control/policy/staging removed; temporary UI file removed |
| ROLLBACK_STATE | PASS; exactly1 rollback, exact original binary/argv; no old credential or directory restored |
| RESEARCH84_UNCHANGED | PASS; APK/signer by byte identity, UID/version/install times unchanged; no target install/data clear/enrollment/private reader/instrumentation |
| MAIN_SOURCE_AND_CONFIG_UNCHANGED | PASS; main-before/main-after equal, changed_sections=[] |

## Binding, cleanup and evidence details

Candidate D:3b38925badd9dfeca9d5c9f466dc048040677393683aa3e0d39db4c5058cbe74.
Target seed room hash:843252af4c80bfd3b52aa72f05660978265eeed98a02702f3f982679e4fe8970.
Control TARGET_AVAILABLE binds exact binary/PID/startticks275480135/invocation/
generation1/room hash. Runtime was /dev/family-seed-acceptance-final, a temporary
service9790700 directory under the existing root0755 writable /dev mount;
PrivateDevices=no. No ReadWritePaths, namespace or sandbox weakening was applied.
Root policy stayed under /run/family-seed-acceptance-final. Service979 AF_UNIX
connection was closed before command acceptance (BrokenPipe); unrelated UID lacked
directory access. No root command/replay was sent. On controlled stop the existing
controller recorded CLEANED/NOT_TRIGGERED/REMOVED. Current process was not restarted
for cosmetic cleanup; the one rollback followed the failed product traffic gate.

Baseline restored SHA256:
21f0a0fdc27b50c00ea922f0b716516e2422aedf1b3797369718f7d00070509a.
Rollback RU/NL D:
04620414095026b90df87a7854d6ad174541bae0f167dd7f143cde255282186c.
Gateway active, admissions restored by normal baseline start. Authority/CRL/leaf/
grant snapshots equal their starting snapshots; controller's last committed
transaction remains scheduled-1792039653-55c83cb47ff5ea45. Maintenance-due is still
acknowledged, not relabelled as expired/unavailable.

Research84 com.familyconnect.app.friends, UID10283, version84,
0.1.18-research84-provisioning-seam; APK
fd3106170ceeb1e24dad6c8eacda4107b1ab09a6ee120ccf495d92d96841aa48;
firstInstallTime2026-09-19 17:30:26, lastUpdateTime2026-10-12 13:47:32.
No ExactReader, egress helper or new observer was installed. The attempted existing
startup diagnostic broadcast returned no diagnostic data and is not counted as
successful evidence. Empty screencap and /dev/tty UI export attempts were not used
as product failure evidence; the actual saved XML provides the Chrome error.

Primary evidence: fresh-1792046701-{summary,NL,RU}.json; deployed.json;
before.json; policy-verification.json; postdeploy-{NL,RU}.json;
owner-first-ui.txt; first-connect-gateway.log; owner-readiness-server.json;
https-before.xml; failure-before-rollback.json; terminal-seed-trigger-*.json;
rollback-result.json; cleanup-{NL,RU}.json; cleanup-staging.json; owner-final.txt;
main-before.json/main-after.json/worktree-result.json. Original preflight reports
remain preserved; prior classifications are historical, not current blockers.

## Counters and disposition

Current continuation: controlled deployments1, rollback1, physical CONNECT1,
manual reconnects0, triggers0, GateControl installs1/uninstalls1/arm0/cleanup0.
TLS builds/tests/live preflights/owner installs0 in this continuation; cumulative
earlier optional TLS build1/disposable test1, live preflights0/owner installs0.
New helper packages0; research84 installs/updates/uninstalls0; data clears0;
re-enrollments0; authority/grant/leaf/CRL mutations0; policy changes0; releases0.

ATTEMPT_CONSUMED=YES.
NEXT_REQUIRED_OPERATION=OFFLINE_AUTHORITY_GRANT_MAINTENANCE (NOT_RUN).
READY_FOR_FAIL_CLOSED_TEST=NO. Fail-closed and Krasnodar FIELD NOT_RUN.

Seed-supervisor не прошёл production acceptance. Первая продуктовая граница
отказа: обычный DNS/HTTPS через VPN после первого CONNECT — Chrome сообщил
DNS_PROBE_FINISHED_NO_INTERNET. WS1011/recovery и old-cache reconnect не запускались;
выполнен один rollback. Отказ механизма seed recovery этим эпизодом не доказан.
