# WHITELIST-WARM-START-1 — PARTIAL

All times below UTC,12 October2026. Local evidence:
`state-client-build/field65-export16/whitelist-warm-start-1/`:
`RESULT.json`, `research-manifest.json`, `SHA256SUMS`, bounded `receipts/` and
protected `private/`. Prior seam's77 sealed entries verified unchanged.

## Decision and scope

**Blocked-provisioning warm-start was not exercised.** The90-second physical
operator window expired with no CONNECT. Gate was cleaned before the user's
later physical CONNECT. No second attempt, rearm, injected input, product patch,
APK build, gateway manual restart/renewal, public release or FIELD occurred.

The late connection is not a product routing failure result. Framework VPN ON
and TcpVpnService were observed, but active Telemost/ordinary egress were not proved
outside the closed acceptance window. Prior research82 full-tunnel egress proof
and lease-renewal acceptance remain intact; no new egress claim is substituted.

During closeout observer also captured a **natural gateway fatal**, first stage
SEED_READ/cause UNKNOWN. This is the current readiness blocker, not an inferred
effect of the late CONNECT. `PROCESS_EXIT_CAUSE=UNKNOWN`.

`READY_FOR_CLEAN_RETRY=NO`;
`FIRST_BLOCKER=GATEWAY_NATURAL_FATAL_SEED_READ_UNKNOWN`.
The physical attempt budget has been used once late; the valid blocked-window
attempt count is0. Original `receipts/live-result.json` remains the immutable
window-only timeout record. Final `RESULT.json` includes the later events.

## Exact installed bytes

Research84 installed11:47:34, independently pulled/hashed and signer verified:

| Item | Value |
|---|---|
| Package / version / UID | `com.familyconnect.app.friends` / `0.1.18-research84-provisioning-seam`,84 /10283 |
| APK SHA256 | `fd3106170ceeb1e24dad6c8eacda4107b1ab09a6ee120ccf495d92d96841aa48` |
| Signer SHA256 | `67a90d1bfcd5a2c0666f0cff1b0ac5e43aaa661ca1196f89e879aa39fe20848a` |
| Source base | `f5240994869826c6a28f59e58e38256c688cf6eb` |
| Research source delta | `d7907697d71f119c21bced533f08abae06ae33ef9159c5fd9bd54cf031a481e7` |
| ARM64 native reused | `cb3af31f62fdc1339df5f03374652ef6c62c4382ed10ef2d314bd6b610c989e2` |

Same package/signing lineage/UID, non-debuggable, INTERNET, real Telemost provider,
embedded restricted metadata and900s/32-operation research seam verified. No
demo/lab credential or public control component added. Main APK not rebuilt.
Historical83 artifact/evidence retained; no uninstall, data clear or re-enrollment.

Only separate accepted readers were adapted: exact-reader binding to84/APK hash,
and read-only Activity observer wait20→180s, covering the90s operator gate. No
transport timeout changed, input injection or automatic owner Activity launch.
Ten existing physical-gate tests PASS; ordinary test-app bytes/lifecycle unchanged.
Four offline closeout checks also PASS: late-event reconciliation, zero full-phase
endpoint requests, unknown first fatal cause, and no false final acceptance/cleanup.
Commands: `python3 state-client-build/field65-export16/whitelist-warm-start-1/test_clean_gate.py`
and `python3 state-client-build/field65-export16/whitelist-warm-start-1/test_closeout.py`.
This is not a full UI/negative-auth suite rerun; six historical diagnostic assertions
remain a separate known issue. No assertions or transport contracts weakened.

## Preflight, cache and bounded gate

Pre-arm gateway PID1168539/invocation`26e8634a47e24d60b6f7f55a58f7282a`,
started09:43:01, NRestarts0. Loaded=next observer binary
`0ccaaf81666f0873253e95d1532e89d7203677f675efc6f2627dbcd03882667a`,
source`abc604b0f8ce431174f260ff41ef9b3b6455ba0c`. Strict served chain/profile DER,
RU/NL publication and trust metadata PASS. Credentials covered preparation/gate/
startup/cleanup budgets; limiting leaf13:36:04, process deadline13:43:01. No renewal.

Current-at-preflight directory:
`9c84fc89a605976bf00d297c9374d30db8bd6f172f3f3b804f497e8be2519a51`.
Runtime accepted its current seed only; no prior-invocation overlap. Existing owner
cache already matched; **no preparation authenticated refresh performed**.

Exact production boundary `RestrictedBootstrap.cached → RestrictedCache.usable(now)`
with real vault in memory and installed native offline validator(code0) PASS on83
before update and84 after update. All actual schema/signature/family/gateway/
identity/revision/floor/time/revocation checks PASS. No native startup/network.

- Committed encrypted cache3301bytes SHA256:
  `66e31bede54cb0c701f77bd88e65d74cee51c9b90f89506677c0e22f3a7033ed`.
- Selected canonical decrypted response SHA256:
  `4f587526a8811be494952964adb35843d9b4a6d88406d372333f7ddbad1daa85`.
- Selected bytes equal original cache's canonical response. Encrypted file and
  decrypted/canonical bytes legitimately have different hashes; not a selection bug.
- Same file/sidecars/vault after cleanup offline read12:12:17. No claim of complete
  application-data byte equality; no private material logged/exported.

Collectors prepared before arm: current-binary Mux/tuple probes, controlled nonce
endpoint, ordinary Android test app armed/idle, gate logs, existing provisioning
counter and read-only owner observer. Two desktop endpoint TLS preflight requests
were explicitly NOT Android/full-VPN proof. Post-arm unauthenticated shell HEAD
controls confirmed real Telemost API-origin and ordinary HTTPS availability without
room/auth/provisioning. Global IPv6 absent; IPv6 UNAVAILABLE, not PASS.

| Event | Time / result |
|---|---|
| Gate ARMED |12:04:07.154; schema1, provisioning_only,900s/32 |
| Read-only owner observer ready |12:05:01.222 |
| Physical manual listener ready |12:05:10.240; literal operator instructions displayed |
| Operator window |90s;59 read-only checkpoints, VPN OFF, no owner Activity |
| Evidence before stop / timeout receipt |12:06:49.633, OPERATOR_GATE_TIMEOUT |
| Gate CLEANUP event |12:10:44.541, CLEANED, blocked_calls0 |
| Cache rechecked unchanged |12:12:17, offline only |
| App/chat restored once |12:12:25 snapshot VPN OFF/app ON/chat ON |
| User later reports tunnel enabled |12:16:49 snapshot VPN ON, TcpVpnService + ConnectionService |
| Final owner snapshots |12:20:20 and12:23:09 VPN OFF, app/chat ON |

The observer's later Activity timeout and host wait timeout are preserved: no
Activity appeared within the test window. No hidden CONNECT or repeat was made.
Gate was NOT rearmed for the late user action. TcpVpnService alone does not prove
Telemost vs another selected transport, and no egress request was sent afterward.

## Provisioning counters and their limits

Existing per-probe Nginx log/owner-readiness DB metadata were read, no server
response/logging configuration changed. Operator window:0 probe records; owner
new challenge/fetch/ACK0 through cleanup. Gate blocked_calls0 because no caller
exercised it while target awaited the user's Activity launch.

At12:07:03.704/.898, after the90s window but before cleanup, two global probe
records returned403. They are not attributable to owner from saved evidence;
owner DB metadata did not advance. **Whole armed-window global zero is not proved.**
Do not discard these records or relabel them as blocked-before-dial owner requests.

After permitted normal launcher restoration, ordinary background provisioning
resumed:12:12:25/26/27 challenge/fetch/import-ACK; another fetch12:14:37 has no
saved ACK;12:20:24/25 challenge/fetch/import-ACK follows the new server publication.
These are outside the closed gate window, not controlled preparation refreshes.
They support provisioning available again after cleanup. No exact client cache
read was performed after restoration/new invocation; ACK is not a digest proof.

## Natural fatal and automatic restart

Both original byte receipts copied with SHA256 checks, remote mode0600:

| Layer | Evidence |
|---|---|
| Application | `application-26e8634a47e24d60b6f7f55a58f7282a.json`, SHA`2b699ad0dc63d6ebb17b37a14831dcc13cac091debaf2de6b1614a32525c67de` |
| Systemd | `systemd-26e8634a47e24d60b6f7f55a58f7282a.json`, SHA`3abeb9ca17ff739887a49ea11932645c36f31f6792b7280758d5274c0ddadd4e` |

Application timestamp12:17:02.367127257; elapsed9240512ms. `returned_error`,
last stage SEED_RUN, first stage SEED_READ, first cause UNKNOWN/safe classunknown,
seed_generation1, parent_context_at_failure empty, broker SEED_PUBLISHED,
cleanup started/completed. Credential bound13:36:04, headroom4741s at failure.
Systemd12:17:02.442505: service_result exit-code, exited/status1, exact same
invocation/PID, NRestarts0 before automatic restart. This is neither the old planned
four-hour exit0 nor proved PROFILE/CREDENTIALS_REJECTED. Historical unobserved
exits remain UNKNOWN. No causal attribution to caller, voice call, DPI or timing.

Automatic restart12:17:32: new PID1255784, invocation
`853bf7d3d15b4194b19629d546eaf92b`, NRestarts1. Loaded/next bytes unchanged,
observer still armed; no manual gateway action. Fresh limited read-only follow-up:

- New current/accepted directory:
  `5d3bc0574291ed0712204dcec520cc97b64cc81d31d02d0598e07b27b0b71316`.
- RU/NL publication equal; only current invocation seed accepted.
- Served strict chain/profile DER PASS; leaf SHA
  `22c28c0419a07ecc79cf45a8766c9093880f7cbc58d13cdf1d72781b8234f105`,
  expiry13:36:04;4390s headroom at12:22:53 snapshot.
- Authority/CRL consistency checked; ordinary scheduled CRL publication continues.
  Agent renewal/publication/restart0; automatic restart1.
- Old exact cache validation is historical, not evidence of current readiness.

One bounded current-window journal query timed out and was not repeated. No broad
unit/kernel query, artificial exit, transport patch or credential manipulation.
Observer proves first failing stage and exit path, not underlying SEED_READ cause.

## Acceptance fields and counters

| Field | Result |
|---|---|
| FRESH_GATEWAY_PREFLIGHT | PASS before arm; invalidated by later natural fatal |
| RESEARCH84_OWNER_UPDATE | PASS, in-place |
| CACHE_PREPARATION | Existing current cache; no preparation refresh |
| EXACT_SELECTION | PASS, captured old-invocation snapshot |
| PROVISIONING_GATE_ARM | PASS,900s/32, subsequently CLEANED |
| ZERO_DIRECT_PROVISIONING_REQUESTS | Owner metadata0/window probe0; whole-arm global0 NOT_PROVEN |
| OPERATOR_MANUAL_CONNECT | Window TIMEOUT; one later user-reported/framework-corroborated CONNECT |
| CACHED_NATIVE_INPUT | NOT_RUN in acceptance window |
| TELEMOST_BOOTSTRAP / SEED_ADMISSION / FAMILY_AUTH / DEDICATED_READY | NOT_RUN in acceptance window |
| FULL_TUNNEL_EGRESS / SESSION_OBSERVATION | NOT_RUN; no ordinary full-phase requests |
| GATE_CLEANUP | PASS, CLEANED |
| OWNER_PRESERVATION | Same APK/package/signer/UID; cache/vault unchanged through cleanup read |
| ATTEMPT_CONSUMED | YES, late physical action; valid blocked-window CONNECT0 |

Counters distinguish the bounded acceptance window from later uninstrumented use:

| Counter | Acceptance window | Later / total |
|---|---:|---|
| Manual CONNECT |0 |1 user reported, VPN ON corroborated |
| Manual reconnect |0 |0 reported/issued; no automatic repeat |
| Automated CONNECT commands |0 |0 |
| Native startup attempts |0 |UNKNOWN outside closed observer window |
| Automatic owner recovery |0 |UNKNOWN outside closed observer window |
| Blocked provisioning calls |0 |0 through CLEANED receipt |
| Server provisioning probe records after arm |0 in90s |2 unattributed403 before cleanup |
| Telemost sessions/rooms created by harness |0 |0; user/background late total UNKNOWN |
| Full-phase app requests |0 |0 |

No latency/throughput, DNS, per-app routing, lease-boundary, browser or failover PASS
is claimed. The two endpoint records are desktop preflight only. No payload test
data from Android; no2MiB budget used by full-phase harness.

## Cleanup and next operation

Gate cleaned before removal of control helper; exact-reader and observer helpers
removed, runner ended. Existing ordinary egress-probe app retained unchanged/idle.
Endpoint/collector units stopped; only temporary own test-port rules removed.
Temporary RU/NL scripts/logs copied to protected local evidence, hash-guarded removal
completed. Gateway observer/fatal receipts/rollback retained; AWG/TCP/API/mailbox
services not restarted. Source and original manifests unchanged. No owner data
clear/cache clear, enrollment/history/publisher/AWG configuration mutation by tools.

Final12:23:09 owner: research84/UID10283, **VPN OFF / APP ON /
CHAT_DELIVERY_SERVICE ON / GATE CLEANED**. Exact current cache hash after ordinary
background refresh is UNKNOWN; last measured cache hash is explicitly timestamped.
No cosmetic gateway restart or second launcher restoration.

`WHITELIST_WARM_START_READY=NO`, `WHITELIST_COLD_START_READY=NO`,
`REAL_RESTRICTED_NETWORK_FIELD=NOT_RUN`, `PUBLIC_RELEASE=NOT_RUN`.
No tester distribution. This models only direct provisioning unavailability,
not real restricted-network/DPI/Telemost reachability in Krasnodar.

**One next operation:** offline localization of the saved SEED_READ/UNKNOWN fatal
against exact observer source, without CONNECT or deployment. New invocation/cache
readiness and any newly authorized clean manual episode remain separate later gates.

Warm start without direct provisioning was not verified: the bounded manual window
expired, and the late connection occurred after gate cleanup. The product startup
failure boundary was not exercised; the separately captured gateway fatal must not
be retroactively substituted for that missing acceptance.
