# ANDROID-EMULATOR-NETWORK-1 — PARTIAL

## Scope and preservation

Investigated only Android lifecycle failures for exact candidate
`6d1bddaa886d7320faa7b8ea978a55167c5c0981` versus beta68 baseline
`1abaa3a8a9ba8ad9fa2a71c126620175b713c321`.
Owner candidate remains beta69/code69; normal debug/Friends remains beta65/code65.
No runtime, RTP identity, Reliable/ACK, transport, version, tag or release artifact
changed. No commit, push, publication, signing with release keys, owner installation,
gateway deployment, arming or physical experiment. Dirty main-checkout work preserved.

## Recovered original evidence

| Workflow / Android job | Artifact | Verified ZIP SHA256 |
| --- | --- | --- |
| 37597746736 / 112714386329 | 11470999067 | `6d7390cd20d80f289ce65ca93093534e8fe0d6e6289c932666a9b02960acd0e2` |
| 37597746771 / 112714388835 | 11472003940 | `e053cb64d8e160b652dab2e70fc9f4261903a70389630471723cd57cbb90e16c` |

Both recovered hashes match the original upload receipts. Prior HTTP403 is no
longer an evidence-access blocker. Raw logs, XML, summaries and original APKs are
retained locally; neither hosted run was retried or relabeled successful.

## Earliest causal failures, not downstream symptoms

### Diagnostic: emulator routing plus fail-first test control

Guest log07.10, before any VPN lifecycle test:
- 09:06:45.434: DHCP refresh removes Wi-Fi address10.0.2.16/24;
  .448 records the address again.
- 09:06:45.690: netd cannot install Wi-Fi network100 default via10.0.2.2:
  `ServiceSpecificException(101, "Network is unreachable")`.
- Cellular network101 validates at09:06:47.859. This is not proof of total emulator
  network loss; later normal WG/AWG encrypted echo tests succeed.
- Auto begins09:07:23.933; reported09:07:25.658 exception is from
  `AutoRuntimeTest.control:20`, called by **finally line56**, not the original body.

`control()` tries the first INTERNET/non-VPN network and propagates its IOException
without examining remaining networks. INTERNET capability does not guarantee a
usable IPv4 route. Its failing reset-to-up cleanup prevents stop/profile clearing
and overwrites the primary exception; downstream existing-profile failures follow.
The original body's exception cannot be recovered from this overwritten stack.
Classification: **EMULATOR_NETWORK_STATE + pre-existing HARNESS_SELECTION and
FAILURE_MASKING**, not evidence of a beta69 runtime regression. The precise Android
kernel/DHCP implementation defect is not proven beyond the recorded failed route.

### Client: traffic precedes VPN route publication

This job passes Auto at09:14:45.217; it does not fail at the same control operation.
First manual WG test timeline:
- 09:14:47.814: test sends WG traffic after observing application `status=on`.
- 09:14:47.822: cleanup brings WG down after the send fails.
- 09:14:47.854: ConnectivityService only now processes VPN109 CONNECTED.
- 09:14:47.869–.871: netd attempts to add already-removed tun0/routes and reports
  missing process/device. These messages are downstream, not the initiating fault.
- Failure: `AwgRuntimeTest.traffic:40`, `sendto ... ENETUNREACH`.

Classification: **pre-existing HARNESS_READINESS_RACE**: application service state
does not synchronize Android's asynchronous routing publication. Subsequent manual
AWG stability and TCP integration pass in that same hosted job. Delayed-publication
ordering is reproduced with exact test-method JVM replays; an independently forced
live netd scheduling race was not performed. Do not call this global network loss.

## Test-only correction

Only these tracked source files change:
- `AutoRuntimeTest.java`: attempt remaining eligible non-VPN networks on IOException;
  fail if none work, retain causes and strict HTTP assertions. Reset failure cannot
  prevent service cleanup; teardown errors are suppressed on the original failure.
- `AwgRuntimeTest.java`: await VPN callback with matching address and both default
  routes, bounded15s; unregister in finally. Bind echo sockets to that VPN before
  binding the test source. Existing six IPv4/IPv6 echo assertions, data retries and
  receive timeouts are unchanged; no physical-network fallback is permitted.
- `TcpRuntimeTest.java`: await existing stop/clean barrier before clearing profiles;
  preserve primary exceptions. No TCP traffic or runtime implementation changes.

The TCP cleanup change follows an initial local full-suite failure whose teardown
reported `Disconnect VPN before changing profiles`, masking its body exception.
That receipt is retained, not counted as success or explained away. Three isolated
TCP repeats with primary reporting pass; the masked primary remains unrecovered.

## Beta68 comparison and acceptance

Git comparison proves no differences between baseline and candidate in normal
Android main/debug/androidTest sources, WG/TCP fixture harnesses or either workflow.
The ownerDiagnostic-only version override is not part of the tested debug runtime.
Beta68 and beta69 control-method hashes are identical. This comparison does not
claim two separately built beta68/beta69 runtime APKs were installed locally.

Local emulator: API35/google_apis/x86_64, emulator37.2.12.0/build16428233,
`google/sdk_gphone64_x86_64/emu64xa:15/AE3A.240806.043/12960925:userdebug/dev-keys`.
Only emulator-5560 was targeted; the attached physical phone was not operated.
The original exact-SHA CI debug APK was copied and re-signed with a local debug key
solely to pair with local instrumentation. All195 non-META-INF ZIP payload entries
match the untouched CI APK. This is NOT a release artifact or release-key signature.
Local runtime SHA256: `7bf76976ada6cb35e7178c23892c88688a8ab956a755a3e8e43a8f1be45e26c1`.
Final instrumentation SHA256: `4822f50595dc22ff6f41d084032d7373c19e7648048377c82f481e9cf759930f`.

| Acceptance | Exact result |
| --- | --- |
| Original shared beta68/beta69 lifecycle on healthy emulator | 3 tests PASS,220.244s; not a failure reproduction |
| Deliberately absent Wi-Fi IPv4 routes, cellular retained | Original control probe ENETUNREACH3/3; corrected probe PASS3/3 |
| Exact control-method JVM replay | Original beta68 and beta69 each100/100 reproduce; corrected100/100 passes; all-down/bad HTTP rejected |
| Exact UDP-method delayed-route JVM replay | Original beta68 and beta69 each100/100 fail early; corrected100/100 preserves six echoes |
| Callback ordering JVM replay | 100/100 waits for both routes and unregisters; simulation, not emulator acceptance |
| Initial corrected full trial, before TCP cleanup fix | FAIL:41 reported,1 masked TCP failure,315.025s |
| TCP-only repeats with primary-preserving cleanup | 3/3 PASS:54.164s,51.747s,49.442s |
| Final full instrumentation repeats | 2/2 PASS:41 reported each,21 executed/20 existing assumption skips,331.732s and335.742s |
| Fixture counts, each final full repeat | HTTP30/DNS19; original thresholds24/4 satisfied |
| Instrumentation builds / diff whitespace | PASS |

No skip, ignore, assertion removal or timeout extension was used to obtain success.
The15s callback wait is explicit test readiness synchronization, not a changed
transport timeout. SDK download initially reset; retry succeeded. Tests requiring
real devices/enrollment retain their existing assumptions, not new exemptions.

## Gate, remaining work and rollback

**RTP-IDENTITY-FREEZE-1 must not be promoted yet.** Local test overlay receipts are
not clean exact-SHA hosted acceptance. Both original hosted runs remain failed.
Review this bounded patch, establish a separately authorized validation source
anchor, then repeat both complete hosted workflows. Local direct instrumentation
did not execute run.py's subsequent cross-process storage_restart check, downstream
control-report gate or Client Friends acceptance. Hosted environment equivalence,
repeat hosted acceptance, and the unrecovered local masked TCP primary remain limits.
No runtime regression was proven; none of the protected runtime scope was changed.

Wi-Fi routes restored byte-for-byte after the forced control experiment. Final
fixture ports51820/51821/51900/51902 have no listeners; no VPN tun0/tun1 remains.
Dedicated emulator stopped. Existing beta67/beta68 release/deployment/rollback state
is untouched. Harness rollback: reverse only the retained three-file test patch,
preserving other dirty files; no product rollback is needed.

Evidence directory: `state-client-build/field65-export16/android-emulator-network-1/`.
Includes original archives, `evidence.json`, source comparison, replay scripts/results,
forced-control results/routes, all failed and successful instrumentation logs, APK
payload equivalence, source patch and emulator provenance. Locally retained artifacts
and synthetic fixture material are not added to Git.
