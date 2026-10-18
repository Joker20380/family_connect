# FULL-TUNNEL-EGRESS-VERIFY-1 continuation — 2026-10-11

## Outcome

**HARNESS_FAILURE. Product route was not measured in this continuation.**

The two prior lifecycle defects were addressed locally, but a new precondition was
not validated early enough: Android does not permit this ADB shell to inject input
into the owner application. The single attempted `input tap` returned exit255:

```
java.lang.SecurityException: Injecting to another application requires INJECT_EVENTS permission
```

**One attempted UI dispatch; zero actual CONNECT transitions; zero full-phase
requests.** No second attempt, in-process click substitute, alternate input injection,
security-setting change, root escalation or network implementation change followed.
The harness did not send its full-phase nonces while VPN was still OFF: those would
only have been additional baselines, not the required egress test.

This is neither a demonstrated routing defect nor UNKNOWN_NETWORK. The previous
episode's TUN/Telemost PASS and unknown external egress remain historical evidence;
they are not copied into this continuation as newly observed PASS.

## Product freeze and provenance

Fresh entry, pre-arm and final observations agree with the previous report:

| Component | Verified value |
| --- | --- |
| Package / UID | `com.familyconnect.app.friends` / `10283` |
| Installed version | `0.1.18-research82-lease`, code82 |
| APK SHA256 | `c84060e715c0f128e939cc90ca2cbc5225887325b20ba60f89d5a9354ea36b18` |
| Signer SHA256 | `67a90d1bfcd5a2c0666f0cff1b0ac5e43aaa661ca1196f89e879aa39fe20848a` |
| Source commit | `fbbecb81c033557f6c29819a02b8382519465961` |
| Source tree | `06ca3d03620fc773d4bbb1528e2a0f193d7727a5` |
| NL loaded AND next binary SHA256 | `34704e26029bf1eee4ae7679712c673eec7989b291f1a6f47c87c2b40973d958` |
| NL PID / invocation | `415430` / `3d9e1d2923a5423e9a11afbed13648de` |
| Active directory SHA256 | `af4848c3d1fc83f60c4b38794312c974449126ae436f2914d62dbbf0c82f2041` |
| Served Family leaf SHA256 | `b347b452a5c64417cfc1d8d9c530c56783a71d274cfebde8c4a6989b66535c5f` |
| Authority SHA256 | `d5a0d0dba0a90c6cedaf5365007edebd2e75257a0c05e4453b8fde5f1959dc18` |

Installed embedded restricted metadata/native provenance was extracted again.
Source runtime remains clean in the saved research82 checkout. Main dirty
worktree's36 non-document diff sections match the entry preservation snapshot.
All163 entries in the prior egress manifest still match their hashes. No product
APK/native/gateway rebuild or deployment. Only temporary test packages were built.

Current directory/served-chain/revocation/floors preflights pass before arming and
after cleanup. Final directory headroom is4614s on NL /4611s on RU. Loaded/next
arguments match. No task-initiated credential/grant renewal or directory publication
change was made. Directory/authority/served-leaf hashes stay identical. Live CRL
number/minimum floor advances21248 at entry →21306 pre-arm →21315 at final check;
revision floor remains1. These live security floors were not frozen or rolled back.
All corresponding security preflights pass. An initial offline integrity assertion
incorrectly assumed CRL equality; it was corrected to require monotonic floors,
not treated as a binary change or weakened admission check.
Server-chain verification is not falsely reported as
a new full-session client authentication; no full session began. Ordinary startup
prewarm/refresh returned SUCCESS while the app was open.

## What was fixed and locally demonstrated

### Ordinary request lifecycle — PASS

Separate package `com.familyconnect.egressprobe`, observed UID10407, APK SHA256
`08513088e63fe924a2df6c04926bada9147b8f0ad4116ca384d914b5579e08c5`.
It does not use the owner UID, Family/Mux APIs, protected sockets, NOT_VPN selection,
custom Network binding or a gateway-side request substitute.

- Both `onCreate` and `onNewIntent` dispatch new explicit action/data intents.
- Each run has a unique128-bit run_id/nonce, separate ARM/RUN states, and a per-run
  AtomicFile result. The old phase-wide result is not read as a new success.
- Standard Java Socket/SSLSocket with default trust and HTTPS identity verification;
  destination, local socket address/port and nonce response are recorded. DNS uses
  an ordinary DatagramSocket to the framework-advertised resolver.
- Connect/read timeouts are finite. Duplicate execution is explicitly rejected.
  Process loss is an explicit NOT_ARMED failure, not a silent old-result success.

The on-device local regression uses a loopback HTTP endpoint via a temporary adb
reverse mapping, with no Internet request and no VPN CONNECT. Its receipt proves:

```
REQUEST_A observed once
REQUEST_B observed once
A != B
same process: PASS
B dispatched through onNewIntent: PASS
explicit timeout: PASS
next run after timeout: PASS
duplicate B rejected without another request: PASS
```

The reverse mapping was removed in finally. No owner data/cache clear or enrollment
reset. One separately permitted short VPN-OFF baseline validated the new ordinary
Socket/TLS response contract: SUCCESS,437 complete response bytes, the same source
public IPv4 as the prior Orange Belgium AS47377 baseline. The previous verified ASN
association is reused for that identical IP, not claimed as a new registry lookup.
Full IP remains in private evidence. No baseline series or speedtest was repeated.

### Observer lifecycle — PASS; UI trigger — FAIL

The replacement signed owner instrumentation is **read-only**. It registers an
Activity lifecycle callback, announces OBSERVER_READY, then the host opens the
normal Activity and waits for ACTIVITY_READY. No `startActivitySync`; no CONNECT or
DISCONNECT capability inside the helper. A delayed helper therefore cannot click
Connect later. Stop/snapshot commands are finite and token-scoped.

Final observer: OBSERVER_READY11:18:40.396UTC → ACTIVITY_READY11:18:40.601UTC,
205ms. The first read-only observer iteration also started promptly and its explicit
finish was acknowledged while VPN remained OFF. Existing diagnostics are read,
not replaced with a new product telemetry system.

Pre-CONNECT discovery retained failed system UI probes: uiautomator could not get
idle; screen capture was unavailable on the secure window; a separate read-only
accessibility reader got NO_ACTIVE_ROOT. FLAG_SECURE and device settings were not
changed. The signed observer was extended to report only public control metadata
and bounds from the already resumed Activity, still with no click command.

It verified `Telemost`, country `nl`, an enabled Connect control and framework VPN
OFF. This solved observing the controls, **not permission to inject a click**.
The subsequent ADB input denial is the failed live-trigger integration gate.

## Prepared endpoint, correlation and attempted sequence

The authorized owned endpoint used independent temporary IPv4-only, IPv6-only and
normal TLS listeners, plus a reserved optional browser listener. Existing server
certificate/trust was reused; no PKI/key creation or trust-all TLS. Logs contain only
allowed random nonce, timestamp, source IP/port, family, protocol and bounded label.
No cookies or user payload capture. Addresses are retained privately.

Targeted gateway uprobe layout was derived from the unchanged source; syntax and
attachment readiness passed. Filters select only test destination ports and the
planned DNS nonce. The intended join is ordinary socket's TUN source address →
unique destination port → Mux stream/session tag → gateway outbound tuple → endpoint
source tuple/nonce → returned response. This join **was not exercised** and is not
declared validated merely because the collectors were active.

Actual sequence (UTC):

| Checkpoint | Observation |
| --- | --- |
| Collectors/endpoint ready | Before full-run arming; finite lifetimes, default TLS preflight PASS |
| Full runner armed | 11:24:30.771; new IPv4/normal/DNS runs ARMED; Telemost/NL controls verified |
| New Socket/TLS baseline verified | Before attempted CONNECT, VPN OFF; single phone request |
| UI CONNECT intent | 11:26:23.719; receipt records intent, not successful connection |
| Input action | Android rejects INJECT_EVENTS, exit255 |
| Failure snapshot / collection | Before cleanup; VPN still OFF; no VPN_READY |
| Full run inspection | All three remain ARMED, no began_ms; no full-phase EXECUTING event |
| Final product state | 11:29:42.518; VPN OFF, app ON, ChatDeliveryService ON |

Endpoint final records: two desktop TLS preflights and one phone baseline; zero
full-phase nonces. The optional browser nonce slot was used once for the allowed
new TLS baseline, not reused; full-phase browser check was not attempted. There
was no TUN/Mux test traffic to correlate and no selected full-session tag to claim.
The receipt `live-connect-intent.json` has an intended count of1; authoritative
`full-runs-not-started.json` and RESULT distinguish **actual CONNECT0**.

## Layer, DNS, IPv6 and security scope

```
UNDERLAY_STATE = CELLULAR_IPV4_AVAILABLE (same Orange source in baseline)
FULL_VPN_STATE = OFF_THROUGHOUT_CONTINUATION
ACTIVE_CARRIER = FULL_VPN_NONE; Telemost selected, not opened
MESSENGER_ROUTE = DIRECT at attempted action and cleanup
IPV4_EGRESS = UNKNOWN for full VPN, not measured
IPV6_EGRESS = UNAVAILABLE
IPV6_LEAK = NOT_APPLICABLE_FOR_THIS_EPISODE
DNS_EGRESS = UNKNOWN (full-phase test not triggered)
FAILOVER_LEAK = NOT_TESTED
WHITELIST_WARM_START_READY = NO
WHITELIST_COLD_START_READY = NO
REAL_RESTRICTED_NETWORK_FIELD = NOT_RUN
```

An immediate pre-CONNECT `ip -6 address show scope global` returned empty while
VPN was OFF. IPv6 is not credited PASS and no nonexistent IPv6 challenge is invented.
DoT/Private DNS settings were not changed. No live carrier interruption, recovery,
lease renewal boundary or network-state change was introduced. Existing research82
lease bytes and previous two-renewal evidence remain intact.

Messenger briefly has SERVICE_ONLY during preparation, then DIRECT at the attempted
action and cleanup. Instrumentation start/finish affects its host process lifecycle;
this is not presented as uninterrupted chat service. Final ChatDeliveryService ON
is independently verified after reopening the ordinary app. Idle diagnostic
`carrier=wg` is a default field while full VPN is OFF, not an active AWG connection.

The direct provisioning whitelist dependency remains unchanged and belongs to a
separate product task. The six historical negative-auth diagnostic assertion
failures remain known, not weakened or relabelled suite-green. No product security
or transport suite was claimed newly passed by these harness-only tests.

## Acceptance matrix

Scope: this continuation's full phase. FAIL for startup/request gates means the
acceptance gate was **not reached**, not a demonstrated product failure. Ordinary
request lifecycle alone passes; overall harness includes the failed UI trigger.

| TEST | RESULT |
| --- | --- |
| Harness lifecycle | FAIL |
| Android full VPN established | FAIL |
| Active carrier Telemost | FAIL |
| Ordinary app request executed | FAIL |
| Ordinary app captured by TUN | UNKNOWN |
| Gateway nonce correlation | UNKNOWN |
| IPv4 external egress | UNKNOWN |
| IPv6 external egress | UNAVAILABLE |
| DNS egress | UNKNOWN |
| Per-app bypass | UNKNOWN |
| Failover leak | NOT_TESTED |
| Provisioning whitelist dependency | DIRECT_REQUIRED |

No new per-app routing finding follows from a phase that never entered VPN. The
previous unchanged-source policy audit remains separate evidence.

## Evidence, cleanup and next gate

Evidence root:
`state-client-build/field65-export16/full-tunnel-egress-verify-1-continuation/`.
`RESULT.json` and `research-manifest.json` seal124 entries including receipts,
harness sources and signed temporary APKs. Important receipts:

- `lifecycle-pass.json`, `observer-ready-v3.json`, `scenario-armed.json`;
- `baseline-harness-tls.json`, `probe-installed.json`;
- `live-result.json`, `full-runs-not-started.json`, `private/input-denial.txt`;
- `cleanup-endpoint.json`, `cleanup-gateway.json`, `helpers-removed.json`,
  `owner-final.json`, `preflight-final-*`.

The Android denial text is transcribed from the actual tool stderr with provenance
noted; the forbidden input action was not rerun to capture it. Existing local
regression tool sources are retained, with a README explicitly warning that the
as-run live coordinator is not an accepted reusable UI trigger.

Evidence was copied before stopping/removing temporary server resources. All three
helper packages are absent after cleanup. Exact task-owned firewall rules, endpoint,
timers, observers and remote staging files were removed; no gateway restart. Same
production PID/invocation/hash, NRestarts0, loaded/next agreement. Final owner APK
hash/version unchanged; VPN OFF/app ON/ChatDeliveryService ON verified. Cache,
enrollment, identity, AWG/TCP, publisher/history and user data preserved. No public
APK release, FIELD, rollback or UI rollback-draft change.

Next prerequisite is a real operator UI button press in a prepared, finite window,
or an explicitly resolved authorized interaction prerequisite **before** another
episode. Do not substitute an in-process click after this denial or silently change
Android security settings. No second automatic attempt in this continuation.

**HARNESS FAILURE: product route снова не измерен. Android запретил ввод через ADB
до CONNECT; поэтому full-phase requests намеренно не запускались при VPN OFF.**
