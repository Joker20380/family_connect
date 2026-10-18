# TCP-INSTRUMENTATION-PRIMARY-1 — PARTIAL

## Outcome and immutable inputs

Observability and cleanup corrections are implemented and regression-tested.
The initiating TCP failure did not reproduce within the bounded experiment;
its exact predicate, cause and network correlation remain unknown. No claim of
a fixed TCP defect, resolved historical failure or complete harness acceptance.

Base validation source remains `6d1bddaa886d7320faa7b8ea978a55167c5c0981`.
No commit, replacement SHA, tag, push, hosted run, signing, release/version change,
owner installation, gateway deployment, arming or physical experiment occurred.
Only dedicated API35 emulator-5560 was used. Existing runtime CI payload, locally
debug re-signed for instrumentation, remains SHA256
`7bf76976ada6cb35e7178c23892c88688a8ab956a755a3e8e43a8f1be45e26c1`.
Earlier verification of all195 non-META-INF entries against the CI artifact is
preserved. New instrumentation APK SHA256:
`de80a28c612ae0fe65c2f0e9184fc672b810424e32cd88319cfd709b82d2dd92`.
The APK contains the investigation overlay, not a new exact-SHA release candidate.

All evidence is under `state-client-build/field65-export16/tcp-instrumentation-primary-1/`:
`summary.json`, `repeat-results.json`, `receipt-hashes.json`, per-trial full
instrumentation/logcat/peer logs and bounded `traffic-evidence.json`, test APK,
source clone, build log, host regressions, fixture audit and integration manifest.
The earlier `android-emulator-network-1/acceptance-tcp-before-3` and
`corrected-full-1` receipts are retained and hashed again, not relabeled as passing.

## Exact test path

`realityDataSwitchCancelRevokeAndProtectedStorage` starts an activity, stores
synthetic TCP/WG/AWG profiles and validates profile isolation. It runs
TCP → WG → TCP → AWG → TCP, stopping/cleaning each before the next, then tests
in-flight cancel and system VPN revoke. Each TCP start waits for service status
`on`; there is no added TCP VPN-readiness wait in this investigation.

Each `traffic()` makes six separate HTTP requests: three IPv4, then three IPv6.
Local source binds: `10.79.0.2` or `fd79:fc::2`, ephemeral port. Destinations:
`198.19.1.1:18080` or `[fd79:fc::1]:18080`. There is no explicit Android Network
binding in the original TCP path; source binding and Android UID/default routing
remain unchanged. The runtime protects its REALITY connection to synthetic host
`10.0.2.2:51900`. Control reachability probe uses `10.0.2.2:51902`.

Request: GET a fresh slash+UUID path, HTTP/1.1, Host `android.test`, Connection
`close`. Connect timeout10000ms; read timeout15000ms. Writes the whole request
once. Reads1024-byte chunks until EOF, enforcing the unchanged8192-byte bound.
Original acceptance predicates remain exactly `reply.contains(" 200 ")` and
`reply.endsWith(nonce)`, now independently reported as status/body assertions.
Parsing status/header boundary/Content-Length adds diagnostics, not new or weaker
acceptance. No HTTP retries, timeout increases or swallowed errors. The subsequent
random-name DNS assertion remains unchanged.

Stop/disconnect and profile clear follow completed traffic, not socket connect.
On failure, socket try-with-resources retains close failures as suppressed.
Auto/TCP finally blocks run independent cleanup actions and activity finish;
profile clear remains conditional on successful stop so active VPN protections
are not bypassed. An initiating Throwable remains primary; distinct cleanup
errors are suppressed, duplicate objects ignored, self-suppression impossible.
Without a primary, the first cleanup error still fails the test after all actions.

## Diagnostic scope and regressions

This task modifies only two existing androidTest files, `AutoRuntimeTest.java`
and `TcpRuntimeTest.java`, and adds three androidTest files:
`TcpTrafficDiagnostics.java`, `TcpNetworkEvidence.java`,
`TcpTrafficDiagnosticsTest.java`, all in
`clients/android/app/src/androidTest/java/com/familyconnect/app/`.
The earlier Awg readiness correction is preserved unchanged. The no-switch
`TcpTrafficOnlyProbe.java` stays in the isolated investigation clone only.
Main checkout pre-existing unrelated changes were preserved. Integration hashes
match the tested clone; no production/runtime, fixture, version, wire/protocol,
RTP identity or Reliable/ACK source was changed by this task.

Before each request the diagnostics capture default/network IDs, VPN/internet/
validated capabilities, bounded interface names, v4/v6 default route presence,
TCP source presence and service status/transport/health/session. TCP intentionally
remains source-bound rather than Network-bound. On failure the receipt retains
before/after state, socket addresses, connect/write/read stage and timings, byte
counts, parsed status/lengths, EOF/timeout/reset classification, SHA256 and masked
prefix/suffix (each at most80 characters). Unknown response content is replaced
with dots; only fixed HTTP text and a synthetic-path placeholder are exposed.
Receipts are bounded to3800 characters; diagnostic failures are suppressed on
the original exception. A separate post-failure connect-only probe checks the
eligible physical networks without changing fixture drop modes or retrying HTTP.

Successful requests emit counts/timings, not their full pre-request snapshots;
those snapshots are retained only in the failure branch. Full per-run logcat is
retained. No post-failure probe was triggered in this experiment. Consequently
there is no failing-run network/route receipt to interpret, and no assertion that
routing stayed healthy at the time of the historical failure.

Seven required checks pass on JVM and on Android: separate status/body mismatch,
premature EOF classification, unchanged successful predicates, primary IOException/
AssertionError surviving stop and finish failures, self/duplicate suppression,
cleanup-only failure with all actions executed, and bounded secret-safe preview.
Synthetic mismatch/EOF cases are diagnostic regressions, NOT reproduced live TCP
failures. Test APK build and scoped whitespace checks pass.

## Bounded repetitions and order comparison

| Mode | Trials | Result |
| --- | ---: | --- |
| TCP traffic before any earlier switch, investigation-only probe | 3 | 3 PASS |
| Full TcpRuntimeTest alone (one exact lifecycle method) | 44 | 44 PASS |
| AutoTcpAddressRuntimeTest → AwgRuntimeTest → TcpRuntimeTest | 3 | 3 PASS |
| AutoRuntimeTest → AutoTcpAddressRuntimeTest → AwgRuntimeTest → TcpRuntimeTest, plus seven diagnostics tests | 1 | 11 tests PASS |

Initial schedule contains50 invocations, including the three no-switch probes.
One additional **different-order** invocation tests full Auto exhaustion/cancel/
revoke cleanup and the seven regressions. Total exact lifecycle-method executions
are48/48 PASS, below the requested50 ceiling;894 successful HTTP receipts overall.
There were no failed trials hidden by rerun, automatic HTTP retries or discarded
exceptions. Complete TcpRuntimeTest currently contains only that one method;
class-alone execution therefore executes the exact requested method in full.
Instrumentation logs verify predecessor ordering. No observed order dependence;
this does not establish absence of a timing-dependent defect.

Captured live failure categories: **none**. Status or body failure: **unknown**.
Exact evidence from the preserved prior failed run remains only AssertionError at
`TcpRuntimeTest.traffic:26`, lifecycle caller:43, after the final TCP transition
at guest13:10:24.516; test failure13:10:24.783; fixture HTTP12/DNS24. There were
no recorded response bytes, status or failed predicate. Inferring empty response,
body truncation, routing loss or runtime failure from that record is unjustified.

Per-request network queries/logging introduce observer overhead even though no
explicit wait/retry was added. Repeated non-reproduction cannot exclude a race
hidden by that overhead or by a different emulator state. The historical failure
remains blocking, not converted into historical/non-blocking status.

## Beta68 comparison and fixture audit

`git diff 1abaa3a8a9ba8ad9fa2a71c126620175b713c321
6d1bddaa886d7320faa7b8ea978a55167c5c0981` is empty for
`clients/android/app/src/main`, `src/debug`, `pilot/android-tcp`, and
`pilot/android-awg`. This is relevant-source equivalence only; no independent
beta68 runtime APK repetition or binary-equivalence assertion is made. Since the
failure did not reproduce on the beta69 diagnostic harness, there is no paired
reproduction from which to infer a beta69 regression.

Unchanged `pilot/android-tcp/fixture.py` uses a threaded loopback HTTP server.
The exact request path is encoded once, status200 and Content-Length of those
bytes are written, followed by that body. Default HTTP/1.0 closes the connection;
Python StreamRequestHandler has wbufsize0 and SocketWriter.write uses sendall;
HTTP handling flushes, then finish flushes/closes. No shared response body or
cross-request buffer; only counters use a lock. Xray redirects TCP destinations
to this server. Fresh peers are created per instrumentation invocation and reused
across that invocation's switches; fixture teardown happens after instrumentation
returns, not concurrently with the HTTP assertion.

The exact AST-extracted HTTP handler passes24/24 direct loopback requests at
concurrency4: status200, Content-Length37, exact37-byte path body and EOF every
time; completed count24. Audit excludes Xray/Android/VPN and does not prove their
delivery. A tunnel/network teardown can in principle truncate delivery even after
server sendall; neither such a race nor fixture nondeterminism was captured here.
No fixture correction is justified or applied.

## Gate state, rollback and next action

Production TCP remains **unimplicated, not exonerated**. A test-only observability/
cleanup correction is made; a causal HTTP/TCP source correction is not established.
ANDROID-HARNESS-ACCEPTANCE-1 may NOT resume, nor may RTP-IDENTITY-FREEZE-1 advance
to hosted acceptance/signing. No replacement source SHA or release artifacts exist.
No unrelated expensive release gates or new hosted workflows were run.

Emulator-5560 is stopped; synthetic ports51820/51821/51900/51902 have no listeners.
No physical device, host route, installed owner app or deployed gateway changed.
There is nothing deployed to roll back. To undo only this task's source overlay,
review/reverse `integration.patch` against `integration-manifest.json`; preserve
the earlier three-file harness correction and all other dirty checkout work.

Exactly one recommended next step: lower-perturbation diagnostic replay of the
preserved failing network/lifecycle state to capture the initiating status/body
failure before proposing any TCP correction or reopening harness acceptance.
