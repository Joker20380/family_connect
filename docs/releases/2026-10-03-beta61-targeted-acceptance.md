# Beta61 targeted diagnostic acceptance — 2026-10-03

## Decision: BETA61 BLOCKED

### Diagnostic correction r2

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
skips) and lint PASS; correlation/release pytest15/15 and diff-check PASS. Hosted CI,
corrected APK build,
signature/hash, server deployment and owner real-session proof remain pending.
No r2 signed or installed APK. Old SHAc98852b3 below is NOT the r2 hash. Redmi attached
through ADB; no server/admission/catalog/public APK mutation; tester attempts0.

Rollback retains the old signed candidate and owner data; no uninstall/clear/reenroll.
Future gateway rollback restores only executable, not stale credentials/CRL/directory.
Do not deliver old broken-correlation61 or an unaccepted r2 candidate to the tester.

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
