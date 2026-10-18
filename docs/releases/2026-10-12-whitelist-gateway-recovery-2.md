# WHITELIST-GATEWAY-RECOVERY-2 — PARTIAL

12 October 2026, UTC. **READY_FOR_CLEAN_RETRY=NO**.
First blocker: **PROVISIONING_BLOCK_CONDITION_NOT_READY**. Gateway recovery and
exact owner cache selection passed; this is not dedicated-join or whitelist PASS.
**OWNER_CONNECTS=0; FULL_PHASE_REQUESTS=0; ATTEMPT_CONSUMED=NO.**

Private evidence, scripts, RESULT, manifest and seal:
`state-client-build/field65-export16/whitelist-gateway-recovery-2/`.
Previous evidence remains unchanged:718 sealed entries and13 operational receipts.
This report follows [exact selection](2026-10-12-whitelist-exact-selection-1.md),
[fatal observer](2026-10-11-gateway-fatal-cause-1.md) and
[metadata reader](2026-10-11-whitelist-cache-metadata-1.md).

## Result matrix

| Item | Result |
|---|---|
| CURRENT_RESTART_FAILURE_CAUSE | PROFILE / CREDENTIALS_REJECTED / PROVEN |
| HISTORICAL_EXIT_CAUSE | UNKNOWN for pre-observer exits |
| CREDENTIAL_LIFECYCLE_GAP | No scheduled advance Family-expiry alert found; renewal manual |
| RENEWAL | PASS; one same-key renewal, existing TTL policy |
| GATEWAY_START | PASS; one logical reset-failed/start, no retry/rollback |
| CHAIN_AND_PUBLICATION | PASS; strict served chain, DER/profile and RU/NL equality |
| NEW_DIRECTORY | `9c84fc89…9a51`, current invocation seed1 |
| PREPARATION_REFRESH | Existing background refresh reused; initiated extra refresh0 |
| CACHE_IMPORT_AND_ACK | PASS by correlation; existing ACK has no directory digest |
| EXACT_CONNECT_SELECTION | PASS; production availability-failure cached fallback |
| NATIVE_OFFLINE_VALIDATION | PASS; installed native validator code0 |
| PROVISIONING_BLOCK_CONDITION | NOT_READY; previous source-IP/503 mechanism forbidden here |
| COLLECTORS_READY | NO for complete bundle; local ABI/generator/manual-gate fixtures PASS |
| GATEWAY_STABILITY | PASS for610.324s bounded observation, not long-term stability |
| READY_FOR_CLEAN_RETRY | NO |
| ATTEMPT_CONSUMED | NO |

## Preserved fatal evidence and credentials lifecycle

Fresh entry confirmed failed/MainPID0/NRestarts6, last invocation
`c1ad4d4486e94a2cb3a0f6f87e080d7d`. Observer bytes were unchanged.
The previous invocation `dd70fcd8467847bea72b7aba20d3384a`, PID788144,
started11 October19:19:05 and ended23:19:05.963 with normal RUN/DEADLINE,
exit0, elapsed14400042ms. The limiting credentials had expired21:37:28.
Five subsequent startup application receipts preserve PROFILE/CREDENTIALS_REJECTED;
their systemd receipts record exit1. These are not evidence for the earlier,
unobserved exits. No historical cause has been reconstructed speculatively.

The frozen observer source checks `LoadCredentials`/`ServerTLS` before broker
startup; process lifetime separately uses `context.WithTimeout(..., --duration)`.
Family configuration verifies authority/leaf/CRL. Family sessions retain a security
deadline, check it on send/receive and apply read/write deadlines. An idle **process**
remaining alive after credential expiry is not permission for sessions to exchange
data after that expiry. The subsequent startup rejection is expected fail-closed
behaviour, not a reason to disable checks or extend TTL.

The issuer delegation/authority is operator-issued under the existing offline root;
the existing delegated service issues profiles/leaves and signed revocations. The
restricted sync timer republishes CRLs/configuration, but cannot replace an expired
root-signed issuer delegation. The separate product HTTPS certificate-renewal timer
is not a Family credential renewal job. Bounded Family-unit/cron inspection and the
accepted runbook establish:

- `CREDENTIAL_EXPIRY_MONITORING=ABSENT` for a scheduled advance Family-expiry alert;
  manual headroom guards existed but were not an unattended monitor.
- `AUTOMATIC_RENEWAL=MANUAL_BY_DESIGN`; no offline root/vault password moved to a
  production unattended task. No new cron or automatic renewal was installed.
- A local finite `credential_guard.py` and four regression tests were prepared.
  It checks the minimum of actual security expiries against the existing1200s
  startup/test/evidence/cleanup guard, reports renewal cutoff and planned-restart
  coverage, and performs no renewal/start/network action. It is **not an armed alarm**.

Important remaining operational limit: the new gateway leaf expires
**12 October13:36:04UTC**; the1200s guard cutoff is **13:16:04UTC**. The configured
four-hour process deadline13:43:01 is later. Thus a future planned restart is NOT
covered by this leaf. The operational lifecycle gap is documented, not claimed fixed
by this one renewal; current headroom must be rechecked before any later experiment.

## Same-key renewal and one start

Before mutation, old receipts/config/profile/directory/DB state were preserved in
protected local evidence and per-host operational staging. Accepted AKI-fixed
issuance/publication paths were reused. Root, issuer/gateway keys, device grant
bindings, admission/revocation and revision floors remain unchanged. Authority
sequence10→11, new serials/validities and monotonic CRL progression are normal.
Policy stays authority/grants24h and leaf/CRL14400s; notBefore retains the usual5s
allowance. No secret was printed, committed or newly exported to production.

Before startup: native/Go authority positive and negative cases PASS; strict
OpenSSL server/client validation PASS; Python MemoryBIO hostname/DER validation
PASS; AKI/SKI PASS. These local validations opened no owner/carrier connection.
Publication09:36:19 used the existing atomic service-owned publisher: UID/GID979,
0600, service-readable, readback PASS. Initial profile SHA256:
`2660342eada94ccee6c9b63844f19a8a18c7f3ed87dbb890397710b3dc85332d`.
Normal subsequent CRL sync may change profile-file bytes, not the gateway leaf/key.

Exactly one logical reset-failed/start completed:

- PID **1168539**; invocation **`26e8634a47e24d60b6f7f55a58f7282a`**;
  start **09:43:01UTC**, NRestarts0 after the explicitly recorded reset-failed.
- Loaded/next **`0ccaaf81666f0873253e95d1532e89d7203677f675efc6f2627dbcd03882667a`**;
  observer source **`abc604b0f8ce431174f260ff41ef9b3b6455ba0c`**. No binary build/update.
- Actual arguments remain family-config, directory-export, loopback18444,
  `--duration 4h --chat-services --seed-rotate-after 3h`. Unit/drop-ins unchanged.
- Listener18444, strict server-chain/hostname, served DER equals renewed profile PASS.
  This is **not** owner mTLS/admission or application readiness; neither was attempted.
- Final paired RU/NL observation09:58: equality for authority, directory and CRL22469;
  signatures/AKI/nonrevocation/bindings PASS. Gateway leaf DER SHA256
  `22c28c0419a07ecc79cf45a8766c9093880f7cbc58d13cdf1d72781b8234f105`.
- Observer remains armed,0700 receipt directories/0600 files, bounded retention
  unchanged;13 old receipts unchanged, no new terminal receipt for this invocation.

The authorized gateway start creates its normal bootstrap seed; it is not an owner
CONNECT. One gateway seed start is recorded explicitly, not hidden under a global
“Telemost0” claim. No extra synthetic/test rooms, owner sessions or prewarm were made.
No API/mailbox/AWG/TCP service restart; normal restricted publication sync reused.

## New directory and accepted set

Current RU/NL directory SHA256:
`9c84fc89a605976bf00d297c9374d30db8bd6f172f3f3b804f497e8be2519a51`.
Issued09:43:04.234326814, nominal expires13:43:01.880347001UTC, Telemost seed1.
V1 has no standalone generation number or independent directory signature; trust
comes from the identity-bound signed delivery/delegation/profile contract. Family
and gateway bindings match, without publishing identifiers or join URLs.

`SERVER_ACCEPTED_DIRECTORY_SET` currently contains this invocation's seed1 only.
The configured in-process rotation after3h can overlap generations within the same
process; it is not cross-restart overlap, and generation2 was not yet published.
Old invocation directory `bb5c8eb0…d8959` is **not accepted**. Neither nominal
directory expiry nor an old valid signature restores a dead seed. Effective usage
remains bounded by security expiry, currently the gateway leaf13:36:04UTC.

## Owner cache preparation and exact selection

Fresh installed Redmi verification: package `com.familyconnect.app.friends`,
`0.1.18-research83-bootstrap`/83, UID10283, non-debuggable; source
`f5240994869826c6a28f59e58e38256c688cf6eb`;
APK `7208a8132e7ae2fb4245e686ecffd80adf4dc67f8bf99af41a9c56cc66c1f7c8`,
signer `67a90d1bfcd5a2c0666f0cff1b0ac5e43aaa661ca1196f89e879aa39fe20848a`.
Main APK was neither rebuilt nor reinstalled.

The already-running app performed two successful background authenticated fetches
after new publication,09:47:25 and09:52:25, ACKs one second later. Two preceding
background attempts during the unavailable-publication period reported FETCH_FAILED.
These are not agent-initiated refreshes or chat sync, and are not counted as zero.
No extra preparation request was made. Latest READY/PRESENT_VALID import ACK
revision3/CRL22458/expiry13:43:01 correlates with the exact committed cache read.
ACK contains no digest: proof combines stable publication, authenticated response
metadata and the owner reader, not an invented hash-bearing ACK.

One controlled interruption of idle app/chat, followed by **one** accepted offline
instrumentation09:52:58. Existing signed helper reused byte-for-byte; the previously
accepted twelve API31/non-debuggable disposable cases were reused, not rerun or
misreported as new tests. Production vault in memory → production cache constructor/
validator → `RestrictedBootstrap.cached → RestrictedCache.usable(now)` → installed
pure native validation code0. All nine identity/signature/binding/floor/time/schema/
revocation checks PASS. No Activity, refresh, native beginReady, TUN or carrier.

- Cache3301bytes, SHA256 **`66e31bede54cb0c701f77bd88e65d74cee51c9b90f89506677c0e22f3a7033ed`**.
- Selected directory exactly current `9c84fc89…9a51`;
  **CACHE_CURRENT_AND_ACCEPTED** at the observed current invocation.
- Selected canonical response SHA256
  **`4f587526a8811be494952964adb35843d9b4a6d88406d372333f7ddbad1daa85`**
  equals the canonical original response byte-for-byte. Raw3301byte persisted-cache
  hash differs by the documented cache-envelope transformation, not a substituted input.
- `CACHE_BYTES_UNCHANGED=PASS`; sidecars and identity-vault hashes unchanged during
  reader; storage writes0, UID traffic0/0, handle closed, temporary arrays zeroized.
- Selection is specifically the existing **availability-failure fallback**: successful
  authenticated refresh would still take precedence; AUTH/trust failures do not
  acquire permission to reuse cache. No CONNECT was executed to obtain this result.

Helper removed; original enrollment/cache/history/AWG/publisher retained. Verified
duplicate local APK copies removed, accepted helper/source/evidence originals retained.
Final owner09:58:35: **VPN OFF; app OFF; ChatDeliveryService OFF; stopped=true**.
No launcher/chat restart for cosmetic restoration, no second instrumentation.

## Block condition, collectors and remaining limits

The old accepted fault mechanism maps **source IP** and returns Nginx **503** only
for restricted-readiness/challenge/ACK paths. It is path-specific, but is not proven
device-exclusive and changes server responses. Both properties violate this task's
explicit constraints. It was neither activated nor rebranded as compliant network
unavailability. A host/port-level block on the shared HTTPS endpoint would also block
other roles; no TLS interception, fake response, root/firewall or APK mock was used.
Thus **PROVISIONING_BLOCK_CONDITION=NOT_READY**. Telemost/DNS/underlay unchanged.

Local collector preparation rebinds exact observer binary/Mux symbols/layout and
current invocation; generator accepts current state and rejects wrong binary/stale
invocation. A future observer wrapper removes automatic Activity launch and waits
for operator activity. Ten existing physical-gate tests plus four new headroom tests
PASS; three collector-generation cases PASS. Proven egress app/endpoint protocol
unchanged. No live collector or endpoint was started.

**COLLECTORS_READY=NO for the complete bundle**: first-startup/server-admission capture
has not been reaccepted for current configuration. Current argv does not enable the
old finite peer/ownership file collectors. One bounded6s query of only the NEW
invocation's application journal timed out and was not repeated. This is a collection
limitation, not a gateway failure. Old timed-out wide journal/kernel queries were
not repeated. Local Mux ABI PASS is not proof that all admission/first-close collectors
are ready. Gateway-owner admission absence is not asserted from an unavailable log;
owner process/native carrier is absent after cleanup.

Five passive snapshots over610.324s preserve PID/invocation/NRestarts0, with final
strict chain and listener intact; final09:58 snapshot agrees. No natural fatal exit,
manual retry or artificial exit. No transport/timer/lease/TTL behaviour was patched.
The six historical negative-auth diagnostic assertions remain separate; no broad
suite-green claim or transport issue closure is made.

## Closeout and next operation

Recovery rollback artifacts remain protected on both authorized hosts under
`restricted-materials-stage-20261001/whitelist-gateway-recovery-20261012`; baseline
observation binary/config retained. Rollback not used. The expired old profile is
evidence, **not** a healthy credential rollback. No cosmetic gateway restart.
Headroom at final evidence calculation12879s, against the existing1200s guard.
This is time-bound evidence, not continuing readiness authorization.

Task-initiated owner CONNECT/native startup/Telemost/TUN/full-phase/Activity/refresh
all0; instrumentation1; existing successful background refreshes2 recorded separately.
One authorized gateway bootstrap start and one credential renewal are separately
accounted. No APK publication, tester delivery, FIELD or cold-start claim.

**Exactly one next operation:** design and fixture-validate a compliant owner-only,
provisioning-role network-denial condition, without CONNECT. That is the first
blocker; completing it alone does not waive the remaining collector and fresh
headroom gates. The clean CONNECT attempt remains unused.
