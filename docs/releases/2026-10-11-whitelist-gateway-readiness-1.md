# WHITELIST-GATEWAY-READINESS-1 — read-only preflight, NOT READY

11 October 2026. Continues the [pre-CONNECT abort](2026-10-11-whitelist-dedicated-join-1.md).
**READY_FOR_CLEAN_RETRY=NO. CLEAN_RETRY_ATTEMPT_CONSUMED=NO; OWNER_CONNECTS=0;
FULL_PHASE_REQUESTS=0.** No operator gate, owner startup/prewarm, instrumentation,
native beginReady, provisioning refresh or carrier-opening helper was run.

Primary blocker: **gateway changed invocation during the read-only preflight**.
Independent hard blocker: strict server-only TLS rejects an expired certificate.
Current client cache fingerprint/compatibility cannot be proved by the available
non-lifecycle metadata interface. No renewal, restart, publication or product change
was performed by the agent. An additional **autonomous** server restart and new
seed publication were observed; this is not a claim that background server state
or rooms remained unchanged.

Evidence: `state-client-build/field65-export16/whitelist-gateway-readiness-1/`:
`RESULT.json`, `research-manifest.json`, `SHA256SUMS` (21 entries), bounded read-only
receipts and reproducible local analysis/guard scripts. Earlier157 continuation,
2 offline-review and168 clean-preparation sealed entries verify unchanged.

## Exact preserved subject

Fresh ADB package/hash checks at18:40:33 and18:46:28UTC confirm:

- Package `com.familyconnect.app.friends`, version `0.1.18-research83-bootstrap`,
  code83, UID10283, non-debuggable, APK
  `7208a8132e7ae2fb4245e686ecffd80adf4dc67f8bf99af41a9c56cc66c1f7c8`.
- Same signer from the saved verified receipt, bound by identical installed APK:
  `67a90d1bfcd5a2c0666f0cff1b0ac5e43aaa661ca1196f89e879aa39fe20848a`.
- Frozen clean source `f5240994869826c6a28f59e58e38256c688cf6eb`, tree
  `630464f630044b0d72afed4ae5b375f21bfd3d01`. Existing embedded restricted metadata
  schema2 identifies that source/tree, arm64-v8a/Telemost, diagnostic_only=false;
  native SHA `cb3af31f62fdc1339df5f03374652ef6c62c4382ed10ef2d314bd6b610c989e2`.
- Gateway loaded/next SHA throughout observations:
  `5e877eb1355ed4a65bda31be0594299c70002c7a3e96f9d7a528e9e1bb6fe81f`.

No research81/82 identity was substituted. Existing82 egress/lease evidence and83
safe-cache/security results remain historical evidence, not re-executed acceptance.
No product tests, full UI marathon, release/catalog update or APK distribution.

## OLD_INVOCATION, NEW_INVOCATION and a further observed restart

All times UTC; raw systemd MSK timestamps were converted, not confused with exits.

| Field | OLD_INVOCATION | NEW_INVOCATION from the previous abort | Latest runtime observed in this task |
| --- | --- | --- | --- |
| InvocationID | `521233dfc63c49ffac08eeefa567e788` | `63bd9c55895e4b128adec25957959bb4` | `78333d45f8cc450a85fc8473db811485` |
| PID | 596825 | 642809 | 768197 |
| Process start | 13:50:35 | 15:09:37 | 18:45:56 |
| Observation | saved14:55 and exit preflight15:09 | saved15:19; fresh18:39:51–18:40:00 | fresh18:48:29, plus bounded8s check |
| NRestarts | 0 before event | 1 | 2 |
| Directory | A:831abdd2…8b36f | B:457a277f…ee3e04, later C:b5ce6045…f11ad | D:a20c2622…820cd |
| Terminal evidence | last application text15:09:07.176700; absent/auto-restart by15:09:08 preflight | exit sometime after18:40 observation and before next start; exact time/cause not collected | no terminal event observed |
| Exit result | saved `Result=exit-code`, `ExecMainStatus=1`; signal not recorded | UNKNOWN; current process success is **not** this predecessor's exit result | active/running, current Result=success; not an admission result |

The old final log time is **not** a retrieved systemd exit timestamp. Its exact
exit time remains unavailable. The new process's start is never used as the old
process's exit. Additional restart was detected by changed directory in the final
RU/NL pair, then verified by a distinct bounded current-state read, not by another
historical journal query.

Actual argv from the saved old journal `_CMDLINE` and fresh `/proc` agrees:

```text
/opt/apps/family_connect/friends-restricted/bin/bootstrap-broker-bootstrap83-20261011
  --family-config /opt/apps/family_connect/friends-restricted/gateway.json
  --directory-export /opt/apps/family_connect/friends-restricted/directory.json
  --listen 127.0.0.1:18444 --duration 4h --chat-services --seed-rotate-after 3h
```

Loaded/next argv equality PASS. Fresh unit configuration SHA7c4a8460…ced6e;
Restart=always/30s, RuntimeMaxUSec=infinity, WatchdogUSec=0. All eight effective
drop-in paths/hashes/mtimes and provider environment **hash only** are in receipts;
no provider token or private profile was exported. No matching Family systemd timer
was listed. Current unit/drop-in observations are not invented historical journal
records. Exact old profile bytes at exit were not captured: ordinary CRL sync
updates the profile. Initial profile publication b2b2ec80…fa084 at13:49:38 is clearly
separate from the later profile/floor state. Credential identity remains the same
gateway leaf3ac25859…0274 and authorityd5a0d0db…9dc18; no new named profile generation.

## PROCESS_EXIT_CAUSE

**UNKNOWN**, narrowed to observed `BOOTSTRAP_BROKER_STOPPED` / non-nil `run()` return
and process exit1. The actual error value was discarded by the existing main()
handler; do not promote the generic message to a specific provider/transport cause.

Saved original-invocation journal has160 records,86 null MESSAGE entries. After
offline review, one bounded read-only batch queried15:08:40–15:10:05UTC: unit-wide
application/systemd records (180 records/1MiB/12s cap) and kernel records
(80/256KiB/12s). **Both timed out with zero bytes. No repeat/follow or alternative
query to bypass that limit.** Only the query subprocesses were stopped at deadline;
logging configuration and gateway process were not changed.

| Candidate class | What the evidence permits |
| --- | --- |
| PLANNED_LIFETIME | Not supported: exit about78m32s after start, versus4h duration/original17:50:35.164930422 deadline;3h seed rotation had not occurred |
| CREDENTIAL_EXPIRY | Not supported at the old exit: post-exit preflight still has9607s credential headroom, valid signature/non-revoked leaf and CRL/floor21718; current expiry cannot be projected backward |
| CONFIGURATION_REJECTED | Initial rejection inconsistent with the preceding running/READY instance; a later input error is not proved |
| BOOTSTRAP_BROKER_STOPPED | Exact generic terminal observation, not the underlying typed cause |
| PROVIDER/SIGNALING_FAILURE | Possible seed failure path in source; no recorded typed cause establishes it |
| RESOURCE/OOM | UNKNOWN: historical kernel query unavailable; current cgroup oom/oom_kill=0 does not establish historical absence |
| EXPLICIT_SIGNAL | UNKNOWN: no historical signal record; exit1 alone does not identify or exclude a handled signal/cancellation race |
| APPLICATION_ERROR | main() received a non-nil error; which branch/error is UNKNOWN |
| COLLECTION_LIMITATION | Confirmed: missing historical message bodies, bounded unit/kernel query timeouts |

Source paths: `carrier/cmd/bootstrap-broker/main.go` main()/run(), SeedManager.Run
and runOverlap(), and ServeCarrier(). Active seed completion or HTTP serve error
can propagate; seed_closed can originate in carrier Recv/Send. Source reachability
is **not** evidence that a particular branch executed. Neither the old dedicated
handshake timeout nor unrelated gateway sessions are assigned as this process's
cause. PHONE_CALL_CAUSATION remains NOT_ESTABLISHED; no timeout/retry/framing change.

## DIRECTORY_CHANGE_REASON and accepted routes

**A — a new seed is created for each invocation**, plus one finite in-process
rotation. SeedManager does not reload/rejoin the previous exported room on restart.
Its export is a publication output, not persistent seed-session recovery state.

| Snapshot | Identity | Validity / origin |
| --- | --- | --- |
| A | `831abdd213022076ce91b3ebb7537dcb0fbe35fd184dd63b0cae79f81928b36f` | issued13:50:39.367268813; expires17:50:35.164930422; original invocation |
| B | `457a277fbb0e90caa46eddea91fcd74c9afd0e74cf151bb504bceb6d67ee3e04` | first replacement-invocation publication; original receipt has no exact issued timestamp |
| C | `b5ce604584761ff9e5f2c04cce9f42bef7096b9a6ca657991a381eb6d51f11ad` | issued18:09:42.669720044; expires19:09:37.472714293; matches the configured3h rotation |
| D | `a20c26229f46c8657960196c54e8461e6fa9c1c6cc241c073aaac1c2ebe820cd` | issued18:45:59.426782294; expires22:45:56.466872635; latest new invocation |

Directory v1 has **no standalone signature, generation/revision/floor or grant**.
Fields are version, Family, issue/expiry and seed transport/join URL/gateway.
Authenticated delivery and protected client storage bind it to root-signed issuer
delegation and issuer-signed credentials/CRL; these are distinct trust objects.
Fresh C/D metadata has identical Family/gateway binding and telemost-webrtc type,
different hashed join URLs and issue/expiry. No room URLs are included here. Raw
old A/B URLs were not recovered, so there is no invented field-by-field URL diff.
Same leaf/authority identity and unchanged argv exclude a claim of a newly issued
gateway credential as the observed publication mechanism; ordinary CRL sync remains
separate from seed publication.

Existing overlap: one replacement after3h, at most two seeds in the **same** process,
same Broker, until the previous original deadline or earlier process/carrier loss.
Both obey live trust/admission/floors. No cross-process overlap/persistent seed
recovery. B/C's nominal deadline cannot preserve them after that invocation exits.

**OLD_DIRECTORY_CURRENTLY_ACCEPTED=NO** by lifecycle contract and A's expiry, not
by an extra owner-authentication probe. A could not continue to reach this gateway
after its original process died even while A's timestamp was still valid.
SERVER_ACCEPTED_DIRECTORY_SET: D is the latest advertised route; A/B/C are not
retained by that new process. There is **no currently cryptographically usable
route under the observed expired served chain**. Client-specific admission was
not attempted. Restart-safe warm start from an earlier process's sole cached seed
is not supported; manually copying D to the phone would not prove such a contract.

## CLIENT_CACHED_DIRECTORY

**Current fingerprint/generation/crypto-state/selected snapshot: UNKNOWN.** The
installed83 vault is encrypted in private no-backup storage; its normal validator
loads native state. Existing diagnostics provider is non-exported and exposes
only an already-created shared diagnostic file, not an arbitrary live vault view.
The existing observer/lifecycle harness is not a safe current-cache export for
this task. No private key, vault contents, ordinary Activity or instrumentation
was accessed to overcome that boundary; no helper installed or app restart.

Existing RU authenticated readiness records provide bounded **historical** metadata:
latest fetched18:08:31UTC, ACK received18:08:32, research83/import/READY,
revision3/minimum_crl22046/expiry19:09:37. Earlier post-cleanup successful imports
also exist. Therefore do **not** assume the phone still contains A merely because
A was used earlier. Conversely, ACK schema has no directory fingerprint and does
not establish current vault bytes, current floors, current selection or receipt
of D. The latest five saved metadata records are not a new provisioning request.

Research83's existing policy still attempts authenticated refresh, selects exact
fresh imported bytes on success, or revalidates exact protected cached bytes for
classified availability failure. Expiry/revocation/denial/floor/binding failures
remain fail closed. Which bytes it would select now is not claimed without reading
the actual current vault. Server publication is not automatically delivered under
the blocked-provisioning test condition.

## TRUST_AND_CREDENTIAL_STATE

| Check | Result, bounded to the saved observation |
| --- | --- |
| Authority/delegation | Same authorityd5a0d0db…9dc18; root signature and self-signature verified; sequence10/minimum revision1; expiry21:37:28UTC |
| Owner grant | revision3, revoked0, expiry21:37:28; database metadata is not live mTLS admission |
| Gateway profile | Same leaf3ac25859…0274; signature valid, not revoked in observed CRL; **leaf expiry17:49:16UTC** |
| AKI/SKI | Leaf AKI matches authority SKI; leaf SKI absent, self-signed authority AKI absent, recorded separately |
| SERVER_CHAIN | **FAIL / CERTIFICATE_EXPIRED** at18:39 and18:48 with strict validation, expected SNI gateway.family-connect.test and control ALPN http/1.1 |
| SERVER_PROFILE_MATCH / served DER | NOT_REACHED: validation failure prevents verified DER equality; not silently promoted from configured file identity |
| RU/NL | Same current D and identical signed CRL22115 at18:46:25–28, NL floor22115; later normal NL sync advanced22119 by18:48 |
| Current process/listeners | Latest active/running; listeners18444/4243 present; this is not application readiness |
| Effective headroom | Negative: profile leaf already expired, about−3553s at last TLS check; directory22:45/authority21:37 do not override it |
| CLIENT_MTLS_ADMISSION | NOT_ATTEMPTED; no owner client certificate supplied to TLS observation |
| APPLICATION_READINESS | NOT_ATTEMPTED |

Neither server-side grant validity, a valid directory timestamp nor active/running
is a substitute for the complete chain. No trust root/identity/floor/TTL/revocation
change was made. Renewal was not applied: it alone would not prove cache route
compatibility or fix loss of the old seed on restart. No cosmetic restart.

## WARM_START_CONTRACT_VALID and admission gate

WARM_START_CONTRACT_VALID=NO for a previous-invocation cached seed; current client
snapshot compatibility remains UNKNOWN. **READY_FOR_CLEAN_RETRY=NO**, primary
blocker GATEWAY_CHANGED_INVOCATION_DURING_READ_ONLY_PREFLIGHT. Each short8s process
check was stable, but NRestarts1→2 across the task is an actual additional restart;
do not select the short successful interval and hide it. RESTART_LOOP_STATE is
ADDITIONAL_AUTOMATIC_RESTART_OBSERVED, not a proved tight/continuous restart loop.

| Required gate | Result |
| --- | --- |
| Process stable across this bounded preflight | FAIL: changed invocation |
| Loaded/next binary and argv | PASS |
| Served chain | FAIL: expired |
| Current publication | KNOWN: D, synchronized RU/NL |
| Current client cached snapshot | UNKNOWN |
| Server accepts that cached snapshot | UNKNOWN; prior-process routes not retained |
| Phone Telemost underlay reachability | NOT_TESTED; no carrier/startup or new endpoint probe |
| Credential headroom | FAIL |
| Collectors/temporary scoped provisioning denial | NOT_ARMED, deliberately no live acceptance setup |
| Single clean CONNECT attempt | UNUSED |

Local readiness-decision regression:5 methods PASS, including60 false/unknown/
missing-condition subcases; any non-true gate prevents YES. This is not a product
suite PASS. Initial RU metadata helper exited1; after strict public-anchor newline
handling was corrected, the metadata read completed. That was not a retry of the
timed-out journals. No device/gateway product logging or runtime code changed.

## Actions, cleanup and one next operation

Read-only actions: saved evidence/source audit and checksum verification; one bounded
historical journal/kernel batch; systemd/proc/hash/listener/public trust metadata;
existing owner grant/ACK metadata; strict server-only TLS; ADB package/hash/process/
VPN/service inventory. No live owner authentication. Remote scripts ran in memory;
no endpoint/collector/helper was installed, no firewall/ingress rule applied.

Renewal/restart/publication **by agent: NONE**. Automatic restart and seed/CRL
updates are distinguished from agent actions. No operational rollback required.
No cache/enrollment/AWG/publisher/history changes. Last owner observation
**18:46:28UTC /20:46:28 Brussels**: VPN OFF, app process ON, ChatDeliveryService ON,
same PID19925 as entry. This is not a claim to a later unmeasured UI state.

**One next operation:** separately design minimal safe typed-cause capture for a
future gateway fatal exit, without changing transport timeouts or starting owner
traffic. It cannot recover the missing historical cause; no such product patch or
deployment was made here. Gateway lifecycle/cache compatibility and proper same-key
credential preparation must be resolved before a future CONNECT can be admitted.

ATTEMPT_CONSUMED=NO. PHONE_CALL_CAUSATION=NOT_ESTABLISHED. No dedicated-join PASS,
whitelist-bypass PASS or historical-root-cause claim. REAL_RESTRICTED_NETWORK_FIELD=
NOT_RUN; no APK publication or tester delivery.
