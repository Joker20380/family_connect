# CURRENT4H-EXPIRED-RECOVERY-DEPLOY-AND-RESTORE-1

**RESULT: ENVIRONMENT_RESTORED at 2026-10-15 17:43:43 UTC.**

The authorized management deployment and one offline-authorized expired recovery
completed on RU/NL. The unchanged baseline is running, seed readiness is recorded,
the served TLS chain passes strict verification, and a new runtime directory is
published on RU. This is server-environment recovery, **not Android acceptance**.
No phone access, APK build/sign/install, owner CONNECT/export, supervisor deployment,
fault injection, product patch, release or main merge occurred.

PRODUCTION_ACCEPTANCE=FAIL; HISTORICAL_CAUSAL_BINDING=NOT_PROVEN;
DEVICE_ACCEPTANCE=NOT_RUN remain unchanged. Server management, credentials and runtime
**did change**; PRODUCTION_UNCHANGED is not claimed.

## Exact inputs and installed scope

Followed the existing [controlled recovery runbook](../../research/current4h-expired-recovery-20261015/RUNBOOK.md)
and [source manifest](../../research/current4h-expired-recovery-20261015/source-manifest.json),
not root main, the legacy issuer5→6 procedure or experimental CRL writer.

| Identity | SHA256 / source |
|---|---|
| Starting review commit | `de8d5926fa4541e1d3b0a846026e97203243e908` |
| Accepted controller base | `9423d45ee013b349f342a81be502757b17b3fbf2` |
| Accepted source archive | `5fa24f5383e3f64c6ce7368e807972a6a4e4e9d832268feabefb9fea396c0e00` |
| Old installed management map, both nodes | `107d1c4219e13fdb91283b9e34f01951f95436a30c9b155f57ea427041221a5b` |
| New installed 13-module map, both nodes | `5109a7c92ddd1937fe75ed7199866855a8cc20279bc226c35475d4cc81330145` |
| Cumulative source inventory | `338faa75b96ff7ad3eb0d961e1cfa47d79eb75e60d285165cacec9ddf7df3e8b` |
| Baseline configured and loaded executable | `21f0a0fdc27b50c00ea922f0b716516e2422aedf1b3797369718f7d00070509a` |
| Signed client, rehashed unchanged | `3c733d2fc3a0ec377143b668244a4c7d6619ff24abe024da4ee9bfe31d140513` |
| Exact offline signer | `2de81e84c6b5fb39cbf5ca840e7a4791edec256bbb6e3fe7924efc24319ba5f6` |

Reused the prepared, hash-verified package and cumulative source. Did not repeat the
221 Python/Family/race suites, rebuild the gateway/client or modify implementation.
Installed the complete allowlisted set: credential_renewal, grant_cutover,
maintenance_policy, offline_handoff, production_node, production_transport,
production_controller, renewal_cli, node, scheduled_evaluate, renewal_health,
runtime_controller and expired_recovery (`.py`). No signer, fixture, root key,
API replacement or receiver replacement was installed online.

`configure.py` generated private config copies. Only node `source_files` /
`source_sha256` and RU controller `nl_source_sha256` changed. Other paths, policy,
SSH custody, anchor/API hashes, schedule settings and unit definitions were preserved.

## Fresh applicability, checkpoint and topology

Fresh readback began at 17:24:46 UTC; both source maps matched the old accepted map.
No node owner marker or incompatible pending transaction existed. Existing locks were
available. The last coordinator decision was COMMITTED, with matching node completed
ledgers, archive manifests, archived plan/files/reconciliation and current file hashes:

| Binding | Value |
|---|---|
| Previous committed operation | `scheduled-1792039653-55c83cb47ff5ea45` |
| Previous plan digest | `65403ea0edca61bb83ef9eed30576ea026d929452ad99744e3f27f7d92d59393` |
| Predecessor snapshot digest | `5031522ab89f89dee571696fa64b63b65117b523dccbe03ac23f7eb566b35bd5` |
| Current grants | Two unrevoked grants; current device/invite/admission eligibility confirmed |
| Checkpoint grant/device checks | Family bindings, device public keys and monotonic revisions/revocations preserved |

No checkpoint was synthesized; no owner marker or transaction was removed for admission.

NL was failed/PID0. A retained application fatal receipt, also present in the fresh
collector readback, records 11:08:07.758734711 UTC, PROFILE / CREDENTIALS_REJECTED,
invocation `c332f43e5ced4aa58258e4d3877434fe`, followed by exit1. This is
LAST_GATEWAY_EXIT_CAUSE. Separately, current admission blockers were expired
authority/grants, leaf and CRL. Their current expiry was not invented as a new causal
explanation for an unrelated historical event.

Unit ExecStart/config paths and running processes were checked, not just unit names.
The approved barrier covers RU HTTP publisher on port18086, restricted sync timer/
service, restricted-directory-sync timer/service and NL restricted bootstrap. RU HTTP
was active despite NL PID0. The legacy restricted sync writer was disabled/inactive.
The fixed privileged receiver and launcher matched retained accepted hashes.
Directory-only sync uses the accepted management reader; renewal shares the coordinator
lock. The separate health reader does not authorize or publish credentials.

Known adjacent components were checked without stopping them: direct-chat membership
sync uses device/invite membership, not restricted issuer/CRL/grant publication;
mailbox uses its separate settings; the peer worker writes the separate product DB/WG
tree, not restricted credentials. The old invitation API was inactive. No additional
active restricted admission reader or credential writer was found in this scoped
topology. This is not a claim of zero users or sessions.

## Management switch and independent authorization

Saved original enabled/active timer states. Stopped only the renewal timer for the code
switch; its service was failed/PID0, not an executing writer. Held the existing RU
coordinator and both node `operation.lock` files exclusively/nonblocking. Backed up
only management modules/configs privately. Installed NL then RU with same-directory
staging, fsync, rename and directory fsync; configs switched after modules, root0600.

All13 installed hashes and config projections matched. An initial task-side direct
inspect request used noncanonical JSON and was rejected NON_CANONICAL_INPUT. This did
not mutate credentials. The helper exited and released its locks; no install was
replayed. Corrected **read-only** canonical readback verified both installed identities,
lock availability and RU→NL fixed privileged RPC. There was no product-code correction.
Locks were not held during offline review/signing. The renewal timer remained paused.

| Authorization binding | Value |
|---|---|
| One new recovery operation | `expired-recovery-20261015-173455` |
| Explicit purpose | `EXPIRED_PREDECESSOR_RECOVERY` |
| Request result | `RECOVERY_REQUESTED` |
| Request SHA256 | `90fa7e78edbf28f050b4e9c6b52ca2b894df2fb5c592e1ed6604f44b7bd418e5` |
| Approved scope SHA256 | `d373a861d6f457fea6f0eec0971a1bfa7616b5d3bc29c43a18b0a48264de374d` |
| Signed bundle SHA256 | `f7581c2ec60e16c3bec3694a3f4c369d2a213514c63f3180f53e43cd3bc54c87` |
| New committed plan SHA256 | `de9f593db75e73b1fe2e7307397f7c086f9b91e6341f6ee5cd1f14c013b6a1b9` |

Scope came from current authoritative state and included the entire two-grant eligible
unrevoked set. No entitlement was edited, no grant silently excluded or added.
The request binds predecessor, checkpoint, both node states, floors, successor and
approved update classes. No ordinary authority-request/operator retry occurred.

Used the original trusted local signing host and existing pinned root key through a
protected FD, with exact signer plus compatible retained API/dependencies in an isolated
local environment. Import origins were checked before signing; the initial interactive
import check from root cwd resolved the stale checkout and was rejected as an environment
check, then corrected before any key use. The actual signer ran from exact retained
source with `-E -s -B`, `--expired-recovery` and `--confirm-authority-renewal`.
No physical unlock was required by the existing custody mechanism. No key was copied
into artifacts, argv, output, Git or RU/NL. One bundle was signed, independently verified,
transferred and hash-verified; authority had86276seconds remaining at transfer verification.
The window was not restarted at apply.

## Apply, quiescence, commit and cleanup

One `expired-apply --approve-maintenance-outage` completed with COMMITTED and
`first_cause=null`; no resume, re-sign, retry issuance, reset-failed or manual gateway
restart was needed. Production cursor9 records all nine acquisition/quiescence/
prepare/stage/promote steps completed. Actual systemd barrier checks gated prepare and
publication; these were live commands, not the local fixture. Archived services-before
records capture RU HTTP/directory timer active and NL failed before the outage.
RU HTTP stopped and later received a new invocation. No reader was manually stopped
ahead of the workflow's state capture.

Strict readback/reconciliation preceded COMMIT_DECIDED and the normal one-shot start
intents. Both completed ledgers and every protected archive hash verified after cleanup;
both owner markers were absent. Source/config backups and the operation's private
request/bundle/archives remain retained for audit, not as an instruction to roll back
security floors or install old management over recovery state.

Authority sequence13→14; grant revisions[3,5]→[4,6]; CRL and authoritative DB sequence
27095→27096. Two grants renewed, zero new identities/grants, zero reinstatements.
Revocation-set digest is unchanged; old expired certificates did not require new
revocations. Family/device/gateway/key bindings and non-expiry grant scope are preserved.
Gateway minimum_revision1 and minimum_crl27088 remain compatible with current CRL27096;
the policy floor is not confused with the latest CRL sequence. Normal strict validators
and actual served-chain checks passed at current time; no historical-time validation
bypass, TTL extension or new anchor/key was used.

Matching RU/NL hashes are reconciliation evidence, **not distributed online atomicity**.
Safety used the approved closed-reader interval and durable commit gates.

## Live baseline, directory and bounded observation

| Observation | Evidence |
|---|---|
| NL start intent | 17:37:17.608605 UTC, exactly one |
| Loaded baseline | Expected SHA256 above; PID3903125 |
| New gateway invocation | `c11ce23c7d124f2790fa9f35f13f5693` |
| Actual seed-ready event | `bootstrap_seed_ready` at17:37:22.264600190 UTC, same invocation |
| Listener | Existing loopback18444 present |
| Served TLS | TLS1.3 minimum, strict chain/hostname verification PASS; expected leaf DER matches |
| Directory issued | 17:37:22.261585216 UTC, after this runtime start and alongside seed READY |
| New RU/NL directory SHA256 | `d4fa4a8b785e2d677006c02c5f2cca66e220405c4f44dd726d084d690db4e280` |
| RU restoration | HTTP start intent17:37:22.648793 UTC; directory timer17:37:22.729193 UTC |
| RU HTTP final | Active, PID135921, invocation `b19f0148281248cb9de449cc2a34fc49` |

Loaded argv matches configured baseline argv:4h lifetime, chat services and existing
3h seed rotation; no supervisor acceptance/research trigger flag. No expired directory
was copied back. Normal directory parser/scope validation and RU publication passed.
TLS observation is explicitly **server certificate chain only**: client mTLS admission,
Android TUN/DNS/HTTPS and device handoff were not exercised.

One fixed interval ran **17:40:40.546427–17:42:40.546571 UTC**,120.000145seconds.
PID/invocation/state remained unchanged, NRestarts0, no new fatal receipt, and the bounded
same-invocation fatal/panic journal query had no match. The final existing collectors
again verified TLS, binary, credentials, directory and active services.

Initial default journal queries timed out and are retained as collection limitations.
The bounded active-system-journal selection subsequently succeeded, including the exact
seed-ready and scheduled-result events. Its80-row general JSON extract has33 omitted
long MESSAGE fields; it is not claimed to be a full transcript. Separate bounded
fatal/panic filtering and fatal-receipt/process continuity support the observation above.
This120seconds is not proof of long-term autonomy or a user-session inventory.

## Current4h and absolute boundaries

After COMMITTED and cleanup, explicit read-only evaluate returned **NOOP**: alerts/due
empty, files_changed0, remote_writes0, restarts0. Restored the originally enabled/active
renewal timer without changing its configuration or manually starting a writer.
Its naturally due scheduled run started17:40:12 UTC and completed17:40:15 UTC:
actual journal result **NOOP**, no credential/remote writes or restart. Service final
inactive/success/exit0; timer enabled/active/waiting. Directory-only sync also completed
successfully; its timer is active. Legacy restricted sync remains disabled/inactive.

| Boundary | Absolute UTC |
|---|---|
| Final collectors completed | **2026-10-15 17:43:43** |
| Authority / both grants expire | **2026-10-16 17:34:58** |
| Root recovery approval expires | 2026-10-16 17:35:03 |
| Leaf expires | **2026-10-15 21:37:06** |
| CRL nextUpdate | **2026-10-15 21:37:06** |
| Directory expires | 2026-10-15 21:37:17.752732812 |
| Conservative process-start lifetime boundary | 2026-10-15 21:37:17.622194 |
| Next current4h run estimated from systemd monotonic timer | **2026-10-15 17:55:12.847151**, subject to timer accuracy |
| Leaf/CRL ordinary renewal threshold | 2026-10-15 20:07:06 |
| Next operator-maintenance threshold (six-hour headroom) | **2026-10-16 11:34:58** |
| Earliest currently observed device limit | **2026-10-15 21:37:06**, leaf/CRL |

DEVICE_WINDOW_READY_AT_CHECK=YES **for server prerequisites only**:14003seconds
(3h53m23s) remained at final check. The agreed18-minute device sequence fits, leaving
12923seconds for subsequent preparation at that check; no arbitrary extra gate was
introduced. With unchanged boundaries, CONNECT must begin before21:19:06UTC to fit
the entire18minutes including its agreed cleanup. Owner availability/current phone state
was not checked here; elapsed preparation must be charged to real remaining headroom.
Future scheduled renewal may change runtime/directory boundaries, so these are not a
promise that today's invocation remains valid until the next operator date.

Current4h can maintain due leaf/CRL within its existing authority. It cannot sign daily
authority/grants; operator action before the stated threshold remains necessary.
No new alerting, timer, long-lived credentials or TTL migration was introduced.

## Action counts and publication evidence

| Action | Count/result |
|---|---|
| Logical management deployment | 1, full13-module set on each of2nodes |
| Renewal timer pause / restore | 1 / 1; enabled setting unchanged |
| Recovery request / root signing / apply / resume | 1 / 1 / 1 / 0 |
| Credential recovery committed | 1 transaction; authority1, grants2, leaf1, CRL1 |
| Gateway starts / automatic restarts observed | 1 workflow start / 0 |
| Manual gateway restart/reset / gateway deployment | 0 / 0 |
| RU HTTP stop / start | 1 / 1, workflow-controlled |
| Directory timer stop / restore | 1 / 1, workflow-controlled |
| Explicit evaluate / naturally due scheduled evaluation | 1 / 1, both NOOP |
| Recovery rollbacks / fault triggers | 0 / 0 |
| Product changes / new keys / new identities | 0 / 0 / 0 |
| ADB / phone operations / owner CONNECT1 or2 | 0 / 0 / NOT_RUN |
| APK rebuild / resign / install / export | 0 / 0 / 0 / 0 |

Normal gateway seed/provider operations **did occur**; they are not counted as zero
provider actions. Background user/application sessions are not inventoried. No intentional
owner test session or fault injection was created. AWG/TCP and unrelated services were
not changed or restarted. Baseline executable, signed APK and original dirty worktree
were preserved. No release/download assets are published by this change.

[Safe selected receipt](evidence/2026-10-15-current4h-expired-recovery-deployment.json)
contains bounded phase observations, hashes and selected event codes. Full requests,
grant lists, bundle, raw logs, source/config backups and original collector receipts
remain private in the task capsule and protected server operation archives. Local
`/tmp` paths are not presented as publicly accessible evidence. The new publication
commit identifies these documents, not a rebuilt gateway or APK.

## Next step

No residual recovery marker or resume action remains. Leave the restored baseline,
HTTP/directory services and accepted current4h timers running. Resume
OWNER-CUMULATIVE-CLIENT-ACCEPTANCE-1 at a **short fresh environment/owner check**,
using the already signed cumulative APK, then its remaining compatible install/device
steps. Do not rebuild, resign, repeat the full offline audit or automatically CONNECT.
Both owner CONNECT attempts are still unspent.
