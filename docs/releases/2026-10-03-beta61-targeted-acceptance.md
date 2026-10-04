# Beta61 targeted diagnostic acceptance — 2026-10-03

## Decision: BETA61 RUSSIAN DIAGNOSTIC READY

Delivery follow-up04.10: the same accepted bytes are now available at a separate
[verified direct diagnostic download](2026-10-04-beta61-r2-direct-delivery.md).
No rebuild/resign, production promotion, catalog/landing or FIELD change. The local-only
delivery statements below describe the03.10 acceptance checkpoint.

### Final real-session acceptance — 20:40UTC

All acceptance gates PASS; this is diagnostic readiness, NOT FIELD success or a
transport repair. No Russian reproduction performed; no RKN attribution.

Fresh ordinary owner READY/ACK20:30:43UTC, revision3/CRL2185, provisioning/bootstrap
PRESENT_VALID and orchestrator usable. No cache reset or bypass. The readiness
refresh waited for the existing product path; no grant/enrollment change.

Controlled physical Redmi restricted session established, healthy through35 seconds
of observation; overall harness58.762s. Actual product restricted engine/native stack,
not a fabricated trace; this is not an Auto fallback or Russian mobile test. Product
About/Diagnostics Share exported the real session. Server interval20:31:17.289–
20:32:14.078UTC ends with controlled owner teardown.

| Correlation | Verified value |
|---|---|
| Support ID | `FC-4D8Q-REEG` |
| connection_id | `83b8e92b-b742-4624-811a-4a461d0daa49` |
| incident_id | `1dbc9c3e-7ec7-4f33-b5ce-bd51eebbe107` |
| session_tag, identical client/server | `4a78f2287d5ce2b4a799a4edf6fe38b5e95fccb41c2d4137ef1b1e2253966c06` |
| Client export SHA256 | `0ea77008eae8c8f3a633d306aac10ace43deb93c48e6c7ad4e2775bc299ade27` |
| Safe server JSONL SHA256 | `f1328c086292cae2195e11d849f3b6cac1614c1c877e15daf1e64334090743ea` |
| Correlation receipt SHA256 | `b1bc221bd627048a4ffaf97c84aec5abae64cb2e091d10f4672f5e19ffc30bcc` |

48 client and75 server events; correlation_proven/owner_lifecycle_complete true;
all four lookup keys resolve the same lifecycle, no conflicting bindings/sequence
gaps/missing required stages. Client trace/export/projection dropped counters0.
Observed authorization, descriptor issue, room/join, signaling/WS, ICE/PC connected,
carrier/TLS/gateway established, RX/TX activity (last aggregate TX23089/RX17401),
APPLICATION and WEBSOCKET heartbeat TX/RX, local close and complete cleanup.
First observed client/server failure is null. Later teardown FAMILY_TLS_ERROR and
GATEWAY_CLOSE remain visible but do not overwrite the primary slot after local close.
Failure/recovery branches are covered by regressions, not falsely reported as executed
in this healthy controlled session. A future failed session may establish causality
only from actual evidence; per-host sequence is not a cross-host total order.

Strict structured gateway projection preserved all75 events without non-allowlisted
fields. Export privacy check and signed APK scan clean. Initial30s journal reads
timed out; bounded500-line query with90s deadline succeeded, sequence1–75 complete.
No raw provider log/key/profile/credential exported. Evidence stays in ignored private
`state-client-build/field61-r2-owner/`, not Git.

Final product readback exactly matches signed APK4297ea1a and production signer.
UID/inode/first install, identity ciphertext/enrollment/activation/Support unchanged;
all encrypted files matched immediately after in-place install. Later normal AWG
`FriendsAccessAndroid.profile` refresh rewrote configuration ciphertext, and readiness
prewarm refreshed its cache; these are not install data loss. Post-session decryption
and cached-normal-provisioning usability PASS. Separate test APK removed, real export
retained, no product uninstall/clear/reenroll. All owner baseline/runtime gates PASS.

Verified local handoff (same exact bytes as installed owner):
`state-client-build/field61-r2-delivery/FamilyConnect-Test-0.1.18-beta61-r2.apk`, with
SHA256 sidecar, source/signer verification receipt and `INSTALL-RU.txt`.
Only existing FC-YHQB-9VJN may receive this candidate; not uploaded or sent in this
task. Public/catalog/invitation remain60; no new public URL or update catalog entry.
Tester remains60, enrollment/Support unchanged, attempts0. Before a later coordinated
single mobile Auto attempt, verify current gateway/issuer/CRL/directory and fresh
tester READY/ACK. Gateway certificate from this renewal expires21:18:57UTC; the owner
receipt cannot authorize a later tester run. Install over60; never clear/uninstall.
Immediately export after failure/disconnect, then correlate all four identifiers.

The delivery/baseline section below records the preceding checkpoint; remaining
source-only and original61 blockers are historical, superseded by this final result.

### R2 delivery and owner baseline — 20:20UTC

Live correlation gate still pending. Earlier source-only/no-install statements below
are chronological checkpoints, not the current installed/deployed state.

| Item | Verified value |
|---|---|
| Version | `0.1.18-beta61` / `61`, targeted unpublished correction |
| Source | `64849e828add45407625d31df61413ac98e9a2cc` |
| Client CI | `37149708390`, all four platform jobs PASS |
| Other applicable CI | phase0 `37149708372`; readiness `37149708383`: PASS |
| Artifact | `11283533158`, exact restricted ARM64 payload |
| ZIP SHA256 | `91436e0cf986c62a490eb0d4ce546c05c14da18e9d19ed8b680019b0225bf879` |
| Unsigned APK SHA256 | `79c21fb0a516ad8c483537fb5ed10c2a50c5712f82febe2372648d4f78d79dac` |
| Signed APK SHA256 | `4297ea1a7124f048bdfca4889e89114e84465fab3100a3caea7cbe23cd5e35fb` |
| Signed size | `49654651` bytes |
| Signer SHA256 | `67a90d1bfcd5a2c0666f0cff1b0ac5e43aaa661ca1196f89e879aa39fe20848a` |
| Restricted native SHA256 | `f6cd8e135b29ed30e5cba78cece2aecb08dcc08d08c6be908f3b51da9d0ed95e` |
| Gateway SHA256 / loaded readback | `b9b7d542e6f196e2ffcfb9e913f1d065cf83529bb29726ec93daca740a241217` |

Production signer independently matches retained beta60 APK. No product rebuild after
signing. ARM64/native/source parity,16KiB alignment, non-debug manifest and signed
privacy scan1074 entries PASS (zero findings; unchanged reviewed stdlib scheme literal).
Old signed61/c98852b3 retained separately; no published version/tag replaced.

Owner31ce63ba updated in place over original61. UID10283, inode/first installation,
encrypted identity/config/readiness hashes, enrollment fingerprint, activation and
Support FC-4D8Q-REEG equal before/after. Existing server identity authentication,
AWG/HTTPS200, UI/support/restart, provider/control/updater runtime checks and typed
fixture Share export PASS. Synthetic diagnostic files removed; private test APK
still needed for real-session acceptance. No uninstall/data clear/reenrollment.

Protected gateway-only renewal20:18:57UTC retains key/family/identities and exact2
admission. Loaded TLS certificate verified through21:18:57UTC. Fresh authoritative
bootstrap directory accepted. Diagnostic executable switched separately and exact
`/proc/<pid>/exe` hash verified; activation operator PASS. RU admission/device/invite/
grant/support audit hashes and HTTP/AWG/TCP service identities unchanged around both
operations. Renewal restores restricted-sync timer; no admission bypass.

Executable rollback backup:
`/opt/apps/family_connect/restricted-materials-stage-20261001/field61-r2-binary-64849e8/bootstrap-broker.previous`
(olde17e1fe77aa0121847c276fa15db9064d29b714977a57b568183e9950149b1b8).
Rollback only executable with restricted unit restart and fresh directory acceptance;
never restore expired credentials or older CRL floors. Android rollback uses retained
same-code original61 only if required, in place with unchanged signer/data; do not use
uninstall/downgrade-to60 as a recovery shortcut. That original APK lacks the correction.

Receipts are ignored/private `state-client-build/field61-r2-ci`, `field61-r2-owner`,
`field61-r2-gateway`. Await current READY/ACK and real tag/lifecycle/privacy proof.
Tester attempts0; tester/public/catalog/invitation remain60. No transport-fix claim.

### Diagnostic correction r2

Latest export gate: per-record persistence256KiB requires a larger complete bundle
than the old provider's256KiB limit. Producer/provider now share513KiB bundle bound;
fresh/read-only/one-hour expiry and exact-name/path constraints are unchanged. Added
full-history/two-snapshot budget regression and real provider boundary test that does
not accidentally rely on stale-file rejection. Final JVM231/lint and pytest17 PASS;
native full race PASS unchanged. Earlier621468e/4c68c77/6585559 artifacts superseded.
Wait for this latest source's accepted hosted CI before any signature/installation.

Follow-up authorizes a corrected targeted candidate, not broad release. Local source
uses32-byte/64hex SetupID and full diagnostic digest:
`SHA256("family-connect/session-diagnostic/v2\0" || decoded_setup_id)`.
Upper/lowercase hex normalize identically; no truncation. Invalid length/hex or
missing identifier produces no tag and an explicit INVALID/MISSING status.
Fixed vector32 bytes `ab` →
`e1b8ac9f42012f22097916fece757a4f004325f58c07a9b3a24259b27f9530e3`.
Real broker-generated ID and bootstrap handoff fixtures cover the actual protocol.

Native/server trace192 includes endpoint sequence/time/tag and separate first
observed failure/drop counters. WS raw reason is never exported, only code and an
allowlisted category/keyword. Carrier activity is aggregate RX/TX, not content or
destinations. TLS/ICE/PC/signaling/gateway/heartbeat tracing is observational;
cleanup cannot replace first failure. Existing retry/INTERNAL policy is unchanged.
Android keeps four previous sessions with32 tail events each, session-bound
Support/connection/incident IDs and separate cleanup/recovery events. Current trace
retains192 events; persistence/export bound256KiB per record.

Offline `scripts/correlate_restricted.py` joins export + bounded gateway JSONL by
full tag, accepts lookup by any of the four IDs, rejects conflicting bindings or
sequences and reports missing lifecycle/gaps. Bindings are client diagnostic
evidence, NOT authorization. Bare gateway logs cannot know Android-local IDs without
the matching client export. Ordering is endpoint-local, not cross-host causal proof.
Stages not executed by the unchanged recovery policy must not be claimed completed.

Final local checks: full carrier race PASS;230 Friends JVM tests (0 failures/errors/
skips) and lint PASS; correlation/release pytest17/17 and diff-check PASS. Hosted CI,
corrected APK build,
signature/hash, server deployment and owner real-session proof remain pending.
No r2 signed or installed APK. Old SHAc98852b3 below is NOT the r2 hash. Redmi attached
through ADB; no server/admission/catalog/public APK mutation; tester attempts0.

Rollback retains the old signed candidate and owner data; no uninstall/clear/reenroll.
Future gateway rollback restores only executable, not stale credentials/CRL/directory.
Do not deliver old broken-correlation61 or an unaccepted r2 candidate to the tester.

Source621468e pushed; Client builds37148110925 initially started, readiness37148111048
PASS. Final review found trace-sink shutdown must reject late asynchronous callbacks
rather than send to a closed channel. Added bounded queue shutdown race regression
and correlated allowlisted broker error details; fresh full race PASS, pytest17/17
PASS. This refinement supersedes621468e artifacts and requires its own accepted
source/CI. No candidate installation/deployment yet.

Final coverage refinement: actual RTP/RTCP read EOF/error is observed without changing
the read loop's return/close behavior; reliable exhaustion is classified separately.
APPLICATION and WEBSOCKET heartbeat TX/RX are distinct, and WS liveness timeout is
identified as such. Fresh full carrier race,230 Friends JVM/lint and pytest17/17 PASS.
Use final checkpoint CI, not superseded621468e/4c68c77 artifacts. Private owner-only
harness compiled (not signed/installed): real controlled restricted connection and
product Share export; it does not pretend to exercise Russian mobile fallback.

Read-only NL19:43:40UTC: active PID3345011/NRestarts4, loaded binarye17e1fe7. Both
configured and actually served TLS certificate expiry16:22:33UTC confirmed via
loopback handshake, with exact cert match. No server write/restart in this task.
Owner/tester earlier READY receipts were expired at19:32UTC; admission remained both
existing devices. Protected JIT gateway renewal + fresh ordinary owner READY/ACK are
mandatory before live proof. This is a current acceptance blocker, not a diagnosis
of the original15/30-second disconnect. Private receipts underfield61-r2.

Targeted candidate only. No broad publication, catalog/invitation change, FIELD
admission change, tester installation or tester mobile attempt. The owner Redmi
was connected after the initial ADB check and was updated in place successfully.
The signed candidate is retained locally; it is not approved for tester delivery.
The original transport failure is not classified or claimed fixed.

## Immutable candidate

| Field | Verified value |
| --- | --- |
| Package | `com.familyconnect.app.friends` |
| versionName / versionCode | `0.1.18-beta61` / `61` |
| Source commit | `d93a01d5f737a09ef46bfc1d4b7790560fdf26cd` |
| CI / artifact | `37138322487` / `11279129098`, previously accepted platform gates |
| Unsigned APK SHA256 | `7e3fb20413d7a3598ee2fffffd8e9f52b0003cf9ceba63142f733e85051beacb` |
| Signed APK SHA256 | `c98852b339ec8d6fea474164fec97dfb9c5f6f9ed2f07f6c5553d32894296e38` |
| Signed APK size | 49,625,979 bytes |
| Signer SHA256 | `67a90d1bfcd5a2c0666f0cff1b0ac5e43aaa661ca1196f89e879aa39fe20848a` |
| Accepted beta60 APK SHA256 | `8ee59352e5f490aea74c3c8c8aeefd0d65bec0c261a044899d512ca376cf6104` |

Signature was applied to the existing downloaded CI APK, not a rebuilt product.
The same protected local beta signing material and the memfd-based production
signer were used; no key/password was printed, exported to CI/server or committed.
The accepted beta60 APK was independently verified and its signer matched beta61
exactly. APK v2 signature, ARM64 packaging, 16KiB alignment, source/native hashes,
non-debuggable manifest and privacy scan all passed. Signed scan: 1,074 entries,
zero findings, only the previously reviewed unchanged stdlib bytecode false positive.

Local artifact: `state-client-build/field61-ci/signed/FamilyConnect-Test-0.1.18-beta61.apk`.
Receipts: `signing-receipt.json`, `signed-verification.json` under that task directory.
Do not overwrite this signed artifact or treat its successful signature as acceptance
of the diagnostic correlation contract.

## Owner acceptance

Installed with `adb install -r` over the exact accepted beta60 on owner Redmi
`31ce63ba`. No product uninstall, data clear, new identity or reenrollment.

| Check | Result |
| --- | --- |
| UID | `10283`, unchanged |
| Data directory, inode, first-install timestamp | Unchanged |
| Device Identity, cached configuration, restricted cache | All three encrypted file hashes unchanged immediately across update; decryptable |
| Enrollment | Same fingerprint of existing device/invitation/activation preferences; signed server device-status request still active |
| Activation | Preserved |
| Support ID | `FC-4D8Q-REEG`, visible, copyable and unchanged after restart |
| Ordinary app launch / restart | PASS |
| Baseline AWG | CONNECTED in 1,762ms; VPN present; HTTPS probe returned 200 |
| Diagnostic share / persistence | PASS with explicitly synthetic typed native input on physical owner device |
| Export privacy | 5,639-byte bundle, no forbidden fields/values; injected private field excluded |
| Read-only diagnostics provider / control / updater safety tests | PASS |
| Cleanup | Only synthetic diagnostic artifacts and separate test package removed; product retained, VPN off, transport Auto |

The data-preservation evidence covers the installation identity/data directory and
the named encrypted state/enrollment records; it is not an exhaustive hash of every
cache/file. Live normal provisioning may legitimately refresh after startup.

The export test verified `restricted_session` fields, session tag, terminal reason
and times, ICE/signaling enums, retry/timeout counters, Support ID, connection ID
and incident ID in both ring/incident exports. **It injected a typed fixture; it
does not prove that a real native session generates a valid correlation tag.**
Export SHA256: `1afbe73d8538eacf267e3ca47a67050d0c0b51e0cdad8796462bcf7926ac5f6e`.

Only a separate private instrumentation APK was built and signed for acceptance;
the already signed product APK remained byte-identical. The test package is not
distributed. An operator wrapper's post-build check initially read a variable
overwritten by its embedded test signer; independent SHA verification confirmed
the product was unchanged, and the wrapper namespace was isolated before proceeding.
Gradle required the standard outside-sandbox retry for its local daemon socket.

Final installed-APK readback at18:36:59 UTC matched signed SHAc98852b3 and the
accepted signer exactly; separate instrumentation package absent. RU readback at
18:37:04 UTC confirms exactly two admitted, non-revoked existing devices: owner
FC-4D8Q-REEG now reports beta61 READY/ACK_RECEIVED (lease then valid until18:41:25),
tester FC-YHQB-9VJN remains beta60 with its previous expired readiness receipt
(18:25:23). This is not authorization to reuse either lease later. No admission or
enrollment write occurred. Final bounded receipt: ignored
`state-client-build/field61-owner/acceptance-summary.json`.

## Blocking correlation defect

The production broker generates **32 random bytes / 64 hexadecimal characters**
for `SetupID` (`carrier/roombroker/broker.go`, also enforced by its client).
But `sessiondiag.Capture` in the signed beta61 accepts only **16 decoded bytes**.
Consequently a legitimate setup produces an empty `session_tag`; Android omits it.
The former unit test used a 32-character artificial setup ID and missed this mismatch.

A read-only Go probe against the exact unchanged candidate source reproduced:

```json
{"broker_setup_bytes":32,"broker_setup_hex_length":64,"expected_tag_hex_length":32,"actual_tag_hex_length":0,"correlation_gate_passed":false,"synthetic":true}
```

Probe exited 1 as expected for the failed acceptance gate. No product rebuild or
transport/authentication change was made to hide this failure. A gateway-only change
would not make this signed client's missing tag suitable for exact correlation.

## Server diagnostic readiness

Read-only Amsterdam check at 18:31:28 UTC found the **old** gateway executable:
`e17e1fe77aa0121847c276fa15db9064d29b714977a57b568183e9950149b1b8`.
Service active, PID3316213, observed NRestarts3; this operation did not restart it.
The last-hour bounded journal contained one JSON event and no new diagnostic fields;
that sparse interval alone is not evidence about earlier session failures.
The candidate gateway `aca7c13af2802d07e6fcb131367705a29d118650dbbf30ca0af1c8936ad265e4`
was not deployed while acceptance is blocked.

| Required server evidence | Candidate limitation |
| --- | --- |
| Support ID / connection ID / incident ID correlation | IDs exist in client export, not gateway lifecycle logs; tag bridge also broken by the size mismatch |
| ICE / PeerConnection state | Candidate terminal projection has current publisher/subscriber and selected failure enums, not a complete timestamped transition history |
| Signaling/WebSocket closure | Terminal allowlisted category/close code, not full timing/history; arbitrary private text intentionally excluded |
| Carrier and Family TLS/session lifecycle | Coarse events exist but are not all tagged; pre-Mux failures do not produce the terminal Mux diagnostic |
| Gateway close/error | Candidate adds Mux first-error time/category and allowlisted broker reason; deployed binary lacks them |
| Heartbeat/liveness timeout | Telemost has internal ping/pong/ACK counters, but candidate projection omits them and explicit heartbeat-timeout evidence |
| Recovery progress | Final counters/terminal category only, not a correlated stage-by-stage recovery timeline |

Therefore deploying the current gateway alone does not satisfy the requested
diagnostic readiness. Preserve bounded enums and privacy; do not enable raw private
provider logs as a shortcut.

## Remaining work / rollback boundaries

1. Correct the producer/consumer setup-ID contract and add a production-length
   regression plus end-to-end client/server correlation acceptance. This requires
   a newly gated artifact; do not silently rebuild/replace the signed candidate.
2. Complete the privacy-safe, tagged server lifecycle/heartbeat/recovery trace and
   exact join to exported Support/connection/incident IDs, including pre-Mux failure.
3. Re-run required CI, signing/provenance, owner acceptance and targeted gateway
   deployment checks. Gateway rollback must restore the executable only, never stale
   leases/CRL state. No unrelated HTTP/AWG/TCP restart or admission widening.
4. Only after those gates: targeted signed delivery to existing `FC-YHQB-9VJN`, fresh
   ordinary READY/ACK and gateway leases, then exactly one mobile restricted attempt,
   immediate export and first-failing-stage analysis. **Attempts performed: 0.**

Do not uninstall/downgrade the owner app to work around the diagnostic blocker.
The previous beta60 artifact remains available for engineering rollback planning,
but no destructive downgrade, data reset or unsupported rollback was performed.
Public/invitation/update metadata was not changed. FIELD registration, grants and
Support IDs were not modified; all server operations in this task were read-only.

Final outcome: **BETA61 BLOCKED: real-session correlation tag is empty and the
requested detailed server trace is not ready.**
