# 5N-PHYSICAL-RESTRICTED-REHEARSAL — BLOCKED

Task `5N-PHYSICAL-HOOK-FIX-AND-REHEARSAL`,03.10.2026,00:46–01:13UTC.
Private hook repair/build/device regression PASS. Physical restricted CONNECT did
not start: MIUI denied ADB touch injection; no physical user CONNECT was observed
during the announced120-second window. This is not evidence of transport failure.
Stage5N remains OPEN; no replacement gate, automatic retry or next-phase start.

## Source and minimal private fix

Starting/final HEAD `911fea59e08e5ee8844852ae1e2834812632fbde`, unchanged.
No commit or push in this task. Existing unrelated dirty/untracked work preserved.
New fix/tests/packaging/docs remain uncommitted with exact build-input hashes in
[canary58 provenance](2026-10-03-canary58-provenance.json).

Canary57's `OrchestratorDiagnosticActivity.java:36` hardcoded a launch of MainActivity.
The actual Friends manifest replaces `${launcherActivity}` with FriendsActivity;
MainActivity is not declared. Its UI-thread callback threw uncaught
ActivityNotFoundException after writing a misleading prepared=true receipt.

Changed only private debug-source acceptance code:

- `DiagnosticLauncher` obtains the launch Intent through the Activity adapter's
  `getPackageManager().getLaunchIntentForPackage(getPackageName())`. No replacement
  hardcoded Activity class. Missing launcher/resolution/start exceptions return false.
- Activity handles failure as bounded `LAUNCHER_UNAVAILABLE`, clears the override,
  records failure, and finishes rather than throwing from the UI callback.
- Existing three deny flags now use checked synchronous commit plus readback before
  successful preparation. Receipt includes `acceptance_override=ON|OFF|PARTIAL`, fsynced.
- Navigation is not needed by Orchestrator itself; the existing return-to-product UX
  is retained, now variant-aware and bounded. It starts no connection automatically.
- BOOT-1, Telemost, TLS, ReliableStream/Mux, TUN, Orchestrator runtime, fail-closed and
  production policy are unchanged. Exact accepted native libraries were reused.

## Build, package and regression coverage

Private `0.1.18-canary58-physical`, versionCode58, package
`com.familyconnect.app.friends`, arm64,52,731,205bytes.

- APK SHA256: `91e8910896ff84b31a7cebf40f840256dca283d684b075577290d1282f227194`.
- Signer SHA256: `67a90d1bfcd5a2c0666f0cff1b0ac5e43aaa661ca1196f89e879aa39fe20848a`.
- Isolated archive of911fea5 plus five explicitly inventoried task files and private
  Gradle overlay; not a claim the uncommitted patch was in HEAD. All input hashes
  rechecked before install. No unrelated working-tree content included.
- Android JVM: **223 PASS**,0failures/errors/skips, including5 new launcher tests.
- `lintFriends`: **PASS**,0errors/37warnings. `assembleFriends`: PASS.
-4 Python source/manifest contracts PASS. Opt-in real-device pytest PASS; it is
  intentionally skipped during ordinary offline test runs unless explicitly enabled.
- Signed/unsigned APK scans and exact packaged native hashes PASS; no credential or
  room fixture included. Existing reviewed stdlib bytecode false-positive retained.
- Ordinary Friends manifest independently merged **without** the private overlay:
  non-debuggable, actual Friends launcher, no diagnostic Activities. Public defaults
  and invitation/update catalogs unchanged.

| Regression | Evidence |
|---|---|
| A: Friends without MainActivity | JVM case, actual compiled APK, live navigation PASS |
| B: actual launcher resolved | JVM alternate-launcher case; installed package resolves FriendsActivity |
| C: missing launcher/start race | Three JVM null/exception cases return false; bounded Activity failure mapping |
| D: enable hook | Live fsynced ON receipt and all three persisted flags true |
| E: disable hook | Live OFF receipt and all three persisted flags false |
| F: fresh-process OFF | Device regression and final cleanup both PASS |
| G: public/ordinary Friends isolation | Public merged manifest lacks controls and debuggability |
| H: normal Auto when OFF | Existing Orchestrator JVM primary/fallback tests PASS; normal runtime unchanged; Auto/false flags verified live, connection not retested |

The ordinary CLI `uiautomator dump` could not obtain idle state on the animated
dashboard. A temporary read-only shell UI snapshot located the real CONNECT control
without waiting for idle. It did not change APK/security settings or inject readiness.
UI was used only to locate the action, not as acceptance evidence. Helper removed.

## Credential-only renewal and final production

Fresh preflight00:52UTC: previous directory expires01:22:20, insufficient for the
reserved rehearsal/cleanup window; gateway expires01:27:17. One renewal was performed
once the accepted near-expiry window was reached. No TTL/security-policy change.

- New gateway expiry **2026-10-03T01:57:34Z**.
- New directory expiry **2026-10-03T01:52:37.529101038Z**.
- Same gateway key/issuer/Family/sole owner; no new admissions,27nonowners denied.
- Python/native validation and independent final readback PASS; delegation2/grant2.
- Credential family-restricted:family-restricted979:979,0600; parent
  root:family-restricted01770; actual service-user readability PASS.
- Hardened publication and served-certificate exact match PASS; only NL bootstrap
  reloaded, fresh READY/gateway binding PASS,35seconds stable, PID2804597/restarts0.
  Unit remains active/disabled, as at entry.
- Minimum RU sync and authority/directory/CRL/floor293 consistency PASS00:58UTC;
  timer restored, monotonic history continues normally.
-01:11UTC readback: HTTP/nginx generation17 and runtime artifact unchanged;
  RU AWG1515959/TCP1908885, NL AWG2729703/TCP2420425 unchanged. NL samePID/restarts0.
  Final ordinary serialized200/400/400/400 PASS. One restricted owner only.

No HTTP rollout, server-binary redeployment, migration, artifact restaging, remote
test policy, additional authority renewal or rollback of monotonic state.

## In-place install and real encrypted persistence

Exactly intended Redmi Note9Pro, Android12/arm64, ADB device. Initial57 actual APK,
signature and application data verified.58 installed with `adb install -r`; installed
APK pulled back and exact hash/signer verified. Package, UID10283, firstInstallTime
`2026-09-19 17:30:26` and ceDataInode601521 unchanged. No uninstall, pm clear, identity
replacement or reenrollment. Activation retained; private identity bytes not read.

Fresh58 process recomputed READY from real encrypted persisted state. Initial restart
retained57's correlation, proving update continuity; normal automatic product prewarm
then acquired fresh post-renewal material. Before ON/CONNECT: READY, revision2,
minimumCRL296>=renewal291, Family TLS/BootstrapDirectory PRESENT_VALID, usability YES,
ACK_RECEIVED. No manual readiness injection or synthetic fixture.

## Physical boundary and cleanup

Wi-Fi OFF, cellular ON, no other VPN, no ADB reverse/forward, no SSH product forwarding,
manual room URL or synthetic profile. Actual launcher resolution and private hook
ON/OFF/restart regression passed without canary57's ActivityNotFoundException.
`ACCEPTANCE_OVERRIDE=ON` was separately established before attempting normal CONNECT.

The single ADB tap on the observed normal product CONNECT control was denied:
`SecurityException: Injecting to another application requires INJECT_EVENTS permission`.
No alternate injection path, permission weakening or direct-service CONNECT was used.
User was asked to tap CONNECT physically. No new structured Orchestrator events
appeared in120seconds; retained historical AWG events were excluded. No BOOT-1 or
restricted session was started. This is a physical-input blocker, not a transport FAIL.

Window closed explicitly. Existing hook disabled through its normal prepare/OFF path;
fsynced receipt OFF, then new process5454→7119 and all deny flags false, no fail_active.
Auto selected, activation retained, app disconnected/no VPN.01:11UTC fresh encrypted
restart READY, both PRESENT_VALID, usable YES, ACK_RECEIVED, revision2/minimumCRL311.
Normal Auto connection not retested because physical input was unavailable.

| Physical acceptance | Result |
|---|---|
| Orchestrator restricted path / BOOT-1 | NOT RUN |
| Family auth / Room Broker / dedicated session | NOT RUN |
| Restricted whole-device VPN / restricted traffic path | NOT ESTABLISHED |
| Chrome2+ repeated HTTPS loads / TLS | NOT RUN |
| Family DNS / concurrent TCP | NOT RUN |
| DNS leak / protected TCP bypass | NOT MEASURED; no zero claim |
| UDP/QUIC / IPv6 / underlay protection | NOT MEASURED |
| Controlled restricted failure | NOT RUN |
| Final acceptance override | OFF, fresh-process proof PASS |
| Stage5N closed | NO |

Safe receipts: ignored `state-client-build/physical58/`, including source inventory,
signed verification, JVM/lint logs, hook-device-tests and fresh-process proof,
renewal/consistency, installed58/post-update readiness, override-on, connect-tap,
connect-result, cleanup, final owner ACK and final-result. Credential contents stay
out of reports/Git.58 remains privately installed; no public/invitation link changed
or public artifact reverified. No push/FIELD-1/DIAG-1/OPS-1/beta. The existing physical
acceptance is still uncompleted and needs an attended CONNECT in a valid live window;
there is no additional Stage5N gate after a future complete physical PASS.
