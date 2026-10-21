# Owner support automation — 21 October 2026

## Scope and exact bases

**Latest update:** support99 is signed/installed owner-only and CONNECTED/READY/MESH
at15:41UTC. After the renewed USB consent, automatic P0 connect succeeded; both-end
sessioneaab1250… receipts agree, and three real online reports arrived62/69s apart.
It fixes the locally reproduced upload timing defect below; native is identical
to98. HTTP/media services are not changed again. This short support check is not
speed admission or proof the earlier protocol errors are fixed.

Authorized follow-up to the closed Android speed cycle: remove repeated manual
Telegram exports, provide narrowly scoped owner-phone control and opt-in online
support snapshots. No new speed series, QUIC/FEC/packing changes or product-speed
admission. The former17 protocol errors remain unexplained historical observations.

Android source is the exact installed97 capsule, not repository main. Built/signed
and installed **98 / 0.1.18-beta98-support** over97 at15:02UTC, same package
`com.familyconnect.app.friends`, signer and UID10283. The ordinary package update
ended the owner's VPN; this was explicitly authorized. No uninstall/data clear,
identity issuance, floor/CRL change or tester update. Do not describe the whole
task as production unchanged: Android and the shared HTTP API were updated.

- APK: `state-client-build/support-automation-20261021/delivery/FamilyConnect-0.1.18-beta98-support.apk`
- APK SHA256: `a6f534f8a4258fc51ea961b7ca4f9b0512b8a38a96655fc57e2bb5c343be56c8`
- Native SHA256: `3f700aef7952c67de69de1de7cd6878287ed51d6b97be28c464d304a4cfb6673`
- Signer SHA256: `67a90d1bfcd5a2c0666f0cff1b0ac5e43aaa661ca1196f89e879aa39fe20848a`
- Source inventory: `07801d859b3cfc5e16165adbdf14d8564aba0fd9479b7699d66cc910eaecd7a2`
- Installed HTTP parent: `e986f98e70ff7f1abc2678566dd360bb6555583f2e1744ea985c63699bcb3ef7`
- Support HTTP: `21d64558e542ff6ad80fb9b13799fbcb333167ffb5a79ec841e7c94dc65d71fa`

Private receipts and all attempts: `state-client-build/support-automation-20261021`.
Replayable Android delta: `tests/fixtures/support_automation/android97-to98.patch`.
Only three files differ inside the deployed HTTP archive: existing Access challenge
allowlist, existing handler, new bounded diagnostics store. Existing publisher,
clock-skew/admission patches in the actual archive are preserved.

## USB control, not a public debug API

App-local consent defaults OFF, lasts one hour and is lost on process death.
The provider requires Android `DUMP` **and** Binder caller UID2000 **and** live
consent. Ordinary applications, other UIDs and expired consent cannot read or
command it. No root, `INJECT_EVENTS`, accessibility service, secret extraction or
MIUI bypass. Online consent does not grant USB control, and neither grants remote
network control. The explicit app dialog is the one-time setup boundary.

Commands: status, bounded snapshot, connect, disconnect, P0/P1/P2 **next-session**
selection, disable. Mutations require the existing FriendsActivity in foreground;
profiles require OFF/not busy; connect uses the existing VPN permission and
notification gates, and refuses a non-MESH selected transport. It does not create
an onboarding, identity, arbitrary intent or shell-command interface. A timeout
is UNKNOWN, requiring status readback, never blind replay. Gateway profile is a
separate operator setting; use the existing owner-targeted policy helper and verify
both session receipts, not merely the selected Android profile.

```sh
python3 scripts/owner_android_support.py --serial 31ce63ba status
python3 scripts/owner_android_support.py --serial 31ce63ba snapshot --output /tmp/owner-snapshot.json
python3 scripts/owner_android_support.py --serial 31ce63ba collect --seconds 300 --interval 10 --output /tmp/owner-capture
```

Snapshots use private0600/exclusive files, no overwriting previous evidence.
Collector duration≤1800s, interval5..60s, command timeout12s, no reconnect/retries
after failure. Collection is not a throughput or clean-acceptance measurement.

## Online collection and client scope

Consent defaults OFF and expires after7days; users can turn it off immediately.
Enabling sends an initial snapshot. Existing native-stat sampling can subsequently
send at most once/minute, with one worker, no backlog and5-minute backoff after
failure. This is **not** an always-running OS background collector: when no native
sampling happens or Android kills the app, do not infer continued uploads or health.
Upload has a15-second overall deadline and uses existing TLS verification and
persisted Friends identity, without a direct-network VPN bypass or identity creation.

`POST /friends/device/diagnostics` authenticates a fresh, single-use device proof
whose purpose binds SHA256 of the exact serialized report. Revoked/unregistered
identities and replay/substitution are rejected. Schema permits only fixed enums,
bounded counters, version, timestamps and a session correlation hash. No full
diagnostic export, sites, DNS names, URLs, ICE/IP endpoints, keys, message content
or free-form error strings. Support ID is resolved server-side from authenticated
identity, not accepted as a credential or a client-selected identity.

Limits:4096B report,8192B HTTP envelope,4 existing HTTP slots, one latest snapshot
per device, one accepted change/minute/device,5000 device slots. Same report ID and
same contents are idempotent with a fresh proof; conflicting contents are denied.
Retention read cutoff7days, purge every60s while service runs, secure-delete enabled.
The database/backup root remains operator-private. There is no public download API;
read by Support ID through authorized host access using `scripts/read_online_diagnostics.py`
and the existing service Python environment. Expired data is unavailable to the
reader even if the service was stopped before its physical cleanup.

The backend contract accepts Android/Linux/Windows. This does **not** mean desktop
clients have a new uploader installed: Android98 is owner-only; broader Android
delivery and desktop UI/background integration remain pending. No silent enrollment,
collection from other users, bulk rollout, public release or invitation-page update.

First real owner upload confirmed: Android98, sampled1792594993584ms,
stored1792594993s, CELLULAR/DISCONNECTED/READY/capturefalse. This proves authenticated
online delivery, not VPN connectivity or transport speed. It contains no current
RS/Mux profile because no new session was established at that snapshot.

## Error classification, without hiding counters

Native adds fixed-size per-session reason counters at **existing** increments:
open replay, unknown stream, invalid open/DATA/credit/FIN/CLOSE/kind,
DNS replay/role/unmatched response. No protocol behavior, error handling, retry,
payload, resource-window or transport scheduling changes. The old total remains.
Local tests reproduce a DATA arriving after removal/reset and a late unmatched DNS
response increasing the old total. This establishes possible counter meanings;
it does **not** identify which branch produced the historical17 or declare them
benign. Invalid DATA still resets its stream. New physical reason data is needed.

## Verification and retained failures

-193 JVM tests pass; APK/native rebuilt with pinned offline tools, same12 native
  library set, only `libfc_restricted.so` changes; signature/alignment verified.
- Focused Go `-race` tests pass for added reasons and existing Mux128 checks.
-38 Python tests pass: report privacy/bounds/binding/replay/revocation/rate/expiry,
  Support ID compatibility and bounded ADB helper behavior.
- Exact installed-base HTTP artifact:2 packaged HTTP tests pass (support route
  compatibility and signed online report). Unauthenticated public HTTPS upload403.
- First Gradle/HTTP tests hit sandbox socket denial; retries outside sandbox pass.
- Two bounded UI Automator attempts failed to reach idle state. No blind taps,
  permission bypass or repeated request for JSON; the new app consent UI is used.
- First HTTP update selected the old executable because `zz-private-beta…` overrode
  `99-support…`; its403 guard saw404 and rolled back. Existing API/state/config
  were read back before a corrected attempt. Second attempt verifies effective
  ExecStart **before** restart and succeeds with `zzz-support-diagnostics.conf`.
  Both attempts remain in receipts. Only HTTP service was restarted, not media.
- Initial online readback used system Python without RNS; no data read occurred.
  Repeating in the actual service venv succeeds. This is an operator-tool failure,
  not an upload loss or authentication bypass.

## Current state, rollback and remaining checks

15:05UTC readback: NL media gateway still PID775194 / invocation
`a5b5909d10ea4997950bd9d3788b59b7`, binary
`ae527cbd0b93a5d34d10af1a5424cdf8254d79e253c9994a57520408614ce1dd`,
profile`738e5f52d6e9676743272827fc8f41fdfcb4581d28619202d6537f62e63566e2`;
owner operator P0, global LEGACY64, pacingOFF. Renewal untouched. Android98
installed, VPN absent at this readback; do not claim restored MESH yet.

Disable USB by its app button/provider disable or wait for expiry; disable online
in Settings. No APK downgrade, data clearing or security-history rollback needed.
For HTTP rollback, verify current state, restore the saved nginx config and remove
only `zzz-support-diagnostics.conf`, daemon-reload/restart this HTTP service and
test/reload Family HTTPS. Do not stop gateway/renewal or replay an old profile.

The98 follow-up checks below supersede these initial pending observations.
Long-idle/process-death upload coverage and desktop integrations remain separate.
No old speed-phase rerun is authorized by these observations.

## Automated98 verification — no manual export

After explicit USB consent, provider status/snapshot succeeded; selecting P0 and
ordinary connect returned `NEXT_SESSION_P0` / `CONNECT_REQUESTED`. Bounded60s
collection saved10 complete snapshots (ADB command duration adds to the5s pause).
At15:21UTC phone98 was CONNECTED/READY/CELLULAR/capturetrue. Session1a8415d9…
matches gateway startup receipt: local8/receive16/peer16/effective8 in both
directions, LEGACY64/65536, local-write-completionfalse (Q0). This is P0, not RS32.
Gateway startup errors0 are not a whole-session final-zero assertion. The first
read selected a journal interval after startup and returned no profile; a bounded
15:11:30–15:13:00 read recovered it. Both reads and their empty parser-error lists
are saved; missing data was not replaced with zeros.

Android first collection had1 protocol error; later snapshot had2. All increments
are `unknown_stream`: a received frame addressed no currently retained Mux stream.
This narrows the branch. It does not identify frame kind/lifecycle provenance,
prove late-after-close versus malformed peer traffic, establish harm, explain old17
or justify removing the errors. No terminal error was present at those snapshots.
No benchmark HTTP bodies were sent in this follow-up.

Actual authenticated online report stored1792596028s carries the same session tag,
CONNECTED/READY/capturetrue, P0/effective8/LEGACY64, protocol_errors2 and
unknown_stream2. This proves the phone→existing API→operator read path works while
MESH is active; no Telegram handoff. Identity/Support ID binding hashes and owner
record count match the pre-update reference, not revoked; server READY98 confirmed.
The upload later showed UNAVAILABLE. No nginx access records were available in
the bounded container-log query, so its particular cause/status is unknown.

Resources are point observations, not peaks/controlled comparisons:15:21 PSS165124KiB,
RSS277312KiB; CPU38% was an OS aggregate over15:15–15:20 including other app work.
Do not attribute it entirely to support collection or compare it to idle99 startup.
The collector exited normally, with no persistent local watcher left running.

## Support99 — bounded upload scheduling correction

98 armed `nextUpload` at request start. In the local reproducer, first request
starts at0s, is stored at14s and completes at15s; a fast second request at60s reaches
the server only46s after the first stored report and is correctly rate-limited.
99 starts its60s successful cooldown at completion: earliest next start75s.
The server's existing rate limit is unchanged, not relaxed to hide the client bug.
One worker/no backlog,5min failure backoff,15s request deadline and consent gates
remain. Bounded USB status distinguishes429, auth rejection and timeout from other
unavailability; no request URLs/payloads/exception text are exported. This is a
proven local correction, **not** proof the observed98 failure was a429.

- Version99 / `0.1.18-beta99-support`, same package/signer/UID10283, in-place update.
- Signed APK: `state-client-build/support-cadence99-20261021/delivery/FamilyConnect-0.1.18-beta99-support.apk`.
- Signed SHA256: `fae38b81f39b4f813d172f07380b3fd6265b0c3bee3a99ff1d7539d4f1213b0e`.
- Unsigned SHA256: `de93fee19714099663ebbf76ccf12b2f16d5f624fe9daf68ea98a600f59d4b70`.
- Source inventory: `0f43aca53270cf0a63ef5b83a78e09aa8119e39a54321cc5fae15db4c329f939`.
- Native remains `3f700aef7952c67de69de1de7cd6878287ed51d6b97be28c464d304a4cfb6673`;
  all12 native libraries byte-identical to98, carrier/pilot sources compared before
  reuse. No native recompilation, RS/Mux/Q1/pacing/bootstrap/security change.
-198 JVM tests PASS, including5 scheduling tests;41 Python tests PASS using both
  pinned lockfiles. Signature, alignment, exact-source inventory and unchanged
  recovery sources checked. No new public release/CI claim.

Retained setup failures: first99 source-preparation literal did not match the exact
bootstrap-instrumented HTTP client; partial source saved and corrected narrow match
preserves that instrumentation. First Python command named a nonexistent test; next
system-Python run lacked RNS. A new private venv installed both existing lockfiles,
then all41 tests passed. Historical98 replay was fixed to read frozen new-file
contents from its saved patch, rather than accidentally incorporating99 code.

15:34:43 readback confirms installed99, same UID/native, VPN absent after package
replacement. NL media PID775194/invocationa5b5909d…/binaryae527cbd…/profile738e5f52…
and P0/LEGACY64/pacingOFF unchanged. Online consent is retained by app preferences;
USB consent deliberately expires with its process and requires one new user grant.
That post-install gap was subsequently closed as follows. No speed matrix, new
architecture or mass rollout. All support can be disabled without APK downgrade
or identity/security reset.

## Final99 verification and remaining scope

Owner renewed USB consent. Controller checked the actual gateway P0 policy, saved
OFF/profile/connect command receipts, and requested ordinary MESH connect once.
Six bounded observations show CONNECTING→CONNECTED; startup attempt1 succeeded
in26663ms. There was no touch injection or blind reconnect. At15:41:26UTC phone99
is CONNECTED/READY/CELLULAR, TUN capture open, one owner VPN. Sessioneaab1250… matches
gateway startup: both send8/receive16/peer16/effective8, LEGACY64/65536, Q0, A0 and
unchanged carrier. No P1/P2 transition or speed load was performed.

Online opt-in survived the APK update. Three **real** reports of this99 session
were stored at15:38:16,15:39:18,15:40:27UTC (server-clock intervals62/69s). First
snapshot was CONNECTING, next two CONNECTED; all READY/capturetrue and matched
P0 limits. Four read-only polling observations returned uploadSTORED, no failure
backoff in this short sequence. This demonstrates periodic operation, not a
week-long availability claim. The bounded watcher ended normally; no local
collector/test process remains. The consented app uploader remains enabled.

Final Android counter scope is this new session: protocol_errors0 and all reason
counters0, terminalNONE,17 RS retransmissions/4150 retry bytes. These are not17
protocol errors or17 packet losses; handshake/background/Q0 traffic is not a
controlled retry-cost experiment. No historical errors were erased. Earlier98
unknown_stream2 and historical17 remain unexplained at the lifecycle level.
Final gateway profile receipt is a startup zero, not a final whole-session zero.
Identity/Support ID binding hashes match, not revoked, server READY99 confirmed.

Resource point sample: PSS160514KiB/RSS274628KiB. OS CPU19% over15:35–15:40 spans
startup/background traffic, not isolated uploader cost or memory peak. No long-idle,
process-death uploader, full-day stability or network-loss recovery assertion.
NL gateway PID/invocation/binary/profile/flags unchanged at final readback; HTTP
still the98 support artifact, no service restarts during this99 correction.

Remaining: preserve the unclassified protocol-error lifecycle and closed speed
admission result; broader opt-in Android delivery/desktop integrations and sustained
background coverage are separate, not silently rolled out. Owner is left in P0,
not an experimental speed profile. USB access expires after its one-hour/process
grant; online consent expires separately after7days. No further manual action is
needed for the current session. [Redacted evidence](2026-10-21-owner-support-automation.evidence.json).

## GitHub source checkpoint requested21 October

The owner explicitly authorized committing/pushing the accumulated repository
changes after the results explanation. This supersedes the earlier no-push scope,
not the release/deployment restrictions. The checkpoint includes implementation,
bounded support tooling, replay fixtures, reports and redacted evidence, retaining
unsuccessful experiments and the lack of clean speed admission. Ignored private
source capsules, APKs, full diagnostic exports, credentials/keys and databases are
not part of the publication. No version, APK install, gateway service, profile,
renewal, invitation/catalog or tester state changes in this operation.

The exact installed99 remains `0.1.18-beta99-support`, signed APK
`fae38b81f39b4f813d172f07380b3fd6265b0c3bee3a99ff1d7539d4f1213b0e`,
last verified P0. Its capsule-based replay contract remains explicit; a checkout of
main alone is not a substitute for the recorded installed build. Existing rollback
and consent-expiry paths above are unchanged. No release tag or `Release ` commit
prefix is used; ordinary push CI is separate from publishing a product release.

Pre-push validation in the existing control+identity lockfile environment:
`tests/test_online_diagnostics.py`, `tests/test_owner_android_support.py`,
`tests/test_support_ids.py`, `tests/test_support_automation_fixture.py` and
`tests/test_friends_http_runtime.py`: **58 passed,14 skipped**. This is not a full
repository/CI PASS or a rerun of198 JVM checks. Thirteen skips require
`FC_TEST_NGINX`; one requires `FC_TEST_SYNC_ARTIFACT`. All21 changed/new JSON files
parse; the publication guard checks2445 index entries with no blocked files.
The full staged whitespace check reports3142 findings in25 files: frozen diff
context/patch text, two upstream license endings and the historical Q1 replay
helper's final blank line. These bytes remain unchanged to preserve replay hashes;
the scoped source/document check excluding those archives is clean. Do not report
the unfiltered check as PASS or silently normalize sealed experimental patches.
Remote SHA confirmation is an operation receipt, not assumed from this text.
