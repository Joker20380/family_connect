# SUBSCRIPTION-ANDROID-2 — natural delivery and ARM64 candidate

## Starting point and scope

Isolated branch `feature/subscription-status-20261106`, worktree
`/tmp/fc-subscription-status-20261106`. Entry HEAD and verified remote were
`c3f67c4ef23ee2ab0103524ab213c3834dceaecb`. Its diff from the tested APK source
`934867678f99fed9fb7ae94b874d341c44825ead` contains only four documentation/receipt
files, no app/backend changes. Worktree was clean. Main checkout's unrelated work is
preserved; no reset, merge, G4 inspection, runtime changes or production operations.

The [previous runtime report](2026-11-06-subscription-android-1.md) is retained, including
the mixed-underlay FAIL and NOT_RUN gates. This task does not repeat its broad matrix.

## Actual pre-change chain and defect

- Screen open/Refresh calls `ChatRuntime.refreshSubscription`, using Friends proof,
  real HTTP/schema validation and `expected.acceptSubscription` on the serial WORKER.
- The encrypted store's identity-bound subscription projection retains latest event ID,
  revision and read/notified flags. No payment journal or second subscription database.
- Previously refresh only returned the view and incremented `eventsRevision`; it did
  not explicitly request local delivery. The existing `ChatRuntime.tick` does call
  `deliverNotifications`, so automatic delivery was **not absent altogether**.
- `FriendsActivity.onResume` starts `ChatDeliveryService` only when its ordinary
  activated preference is true. The service additionally requires the `.friends`
  package and enabled background delivery. Chat UI also owns the existing runtime.
  Its six-second tick drains saved events as part of messenger work.
- No independent incoming personal payment-event channel exists. Public signed notices
  are separate; subscription responses are not published there. A delivery tick does
  not fetch the subscription endpoint or discover payments by itself.
- **Reproduced defect:** open subscription, create canonical extension, tap Refresh,
  immediately Home before the delayed HTTP reply. The hidden but still showing dialog
  marked the new event read (the existing mark-read policy also sets notified), although
  the user never saw it. No subscription notification appeared. `baseline-inspect` FAIL
  is retained; its durable projection has read=true for synthetic event2.

## Minimal fix

1. After confirmed/stale accepted refresh, enqueue a one-shot drain on the existing
   WORKER, after the main-thread completion/render opportunity. Durable acceptance still
   precedes delivery. No new worker, service, periodic fetch, timer or retry loop.
2. Ordinary FriendsActivity resume drains already-existing local storage, regardless
   of the UI activation flag; it does not create a chat store, enroll, fetch or grant
   access. Existing background-service activation rules are unchanged.
3. Subscription UI marks an event read only while its dialog really has window focus.
   A focused dialog suppresses subscription notifications; regained focus acknowledges
   the displayed event. Focus/dismiss ownership checks avoid clearing another dialog's
   visibility. Dismissal drains any remaining saved unread event on the same WORKER.

Existing exact-identity commit/cancellation fences, durable flags, notification tags,
permission checks and event-type wording remain. `APPLIED payment` conveys confirmed
access provision/extension, not money received; grace/expire/revoke retain their own
semantics. Only the latest corresponding event is returned, not guaranteed full history.

## Natural API35 evidence

Same dedicated API35 AVD reused, `emulator-5672`, NVIDIA GTX1650Ti host GLES/KVM,
two cores/2GiB, shared qualification lock. Earlier AVD/package/evidence was not cleared.
New disposable package `com.familyconnect.app.subscriptionnatural.friends` uses the
test-only init script, local CA and HTTPS origin `10.0.2.2:18443`. The suffix exercises
the existing service package guard. This is not the ARM release configuration.
New synthetic DB under `state-client-build/subscription-android-2/private`; real Handler,
Friends identity and `paid_beta.apply_event`, no product participants or mocked response.

| Check | Result | Evidence |
| --- | --- | --- |
| Real identity/UI recovery | PASS | Test identity enrolled over HTTP, then actual Settings/Get access click and authenticated status recovery set activated=true; no preference injection |
| Ordinary service start | PASS | Activity resume starts real ChatDeliveryService; retained dumpsys service receipt |
| Refresh → Home → notification | PASS | Canonical event3, actual REFRESH tap, Home during bounded two-second server delay; actual subscription-tagged Android notification |
| Notification tap → correct subscription | PASS | Real shade tap opens confirmed access-extension screen; read-only instrumentation verifies saved snapshot device equals current vault identity |
| Repeat ordinary Refresh | PASS | Same event, encrypted read/notified flags; app notification enqueue/post counters unchanged (2/3 before and after, including ongoing/group notifications) |
| Architecture/version guards | PASS | Six focused Python checks; local drain does not fetch/enroll/schedule; public113 catalog/invitation unchanged |
| Identity/request fencing | PASS | Thirteen focused JVM SubscriptionRequest/SubscriptionRefreshGate tests |

No `deliverNotifications`, `doWork`, private enqueue or forced system-job start is used
in this natural scenario. The new instrumentation only enrolls the fixture, performs
an ordinary UI recovery click, or **reads** the final projection. Source methods from
ANDROID-1 which manually delivered notifications were not invoked. HTTP and Android
state are real, not a prepared dictionary passed to accept().

Retained harness failures: dashboard animation prevented uiautomator idle dumps; Get
access is below the Settings scroll, not on the dashboard. Recovery now scrolls and
clicks through Android accessibility. An initial edit compile failure put checked
`hasState` outside its try; corrected before runtime. None of these failures is relabelled.

## Exact user behavior

1. New subscription information is learned on opening Subscription and access or
   pressing Refresh. The validated response durably saves the latest relevant event.
2. Local notification delivery is then requested automatically on the existing worker.
   If the user is already looking at the subscription dialog, that event is acknowledged
   on screen rather than duplicated as a system notification. If the reply arrives after
   Home, the unread event produces the existing system notification when permission allows.
3. Payment/access extension while the app is closed does **not** wake it or arrive via
   push. An ordinary app launch can drain an event already saved earlier, but cannot
   discover a new server event by running the local delivery scheduler alone.
4. A subsequent subscription-screen open/Refresh is required to discover that new event.
   No independent background acquisition was added or claimed.

## ARM release-candidate gate

Current project/owner field release is118; invitation/updater remain113/catalog7.
New candidate is **0.1.18-beta119 /119**, not another set of published118 bytes.
Standard user-facing release-derived variant is `friends`, package
`com.familyconnect.app.friends`, minSDK27, ARM64 (`arm64-v8a`), as in the accepted
118 release. Literal Gradle `release` is not the deployed Friends application.
Ordinary endpoints/trust/signing are required; the test init script is not used.

Unchanged AWG/audio producer sources match accepted118 source13e0b37. Their ARM64
native payload is taken from the verified signed118 APK
`b7b0be92456f522f81d87c71c401c2622d2f823178510b28510a6fb8d5c69fca`, not the old ignored
generated directory (that stale AWG hash was detected and replaced **only here**).
Current restricted native must be built by the existing source-bound producer, with
the exact current commit manifest and ordinary `telemost` provider, no diagnostic tags.
All native/Chaquopy contents, package, version, TLS configuration and signer pin must
be checked before naming the artifact a signed candidate.

At the implementation checkpoint ARM assembly/signing was pending. The completed
build/signature results are recorded below; this is still not rollout acceptance.
Standard existing signer pin:
`67a90d1bfcd5a2c0666f0cff1b0ac5e43aaa661ca1196f89e879aa39fe20848a`.
No replacement key, update catalog signing, upload, public URL or phone installation.

## Preserved limitations and next gate

Physical whitelist, production ingress, physical ARM runtime, natural clock expiry,
real identity switch through UI and unavailable-local-address mixed-network observation
remain open exactly as in ANDROID-1. The next artifact-specific step is installation
over accepted118 on a separately authorized dedicated ARM test device, verifying signer/
data retention and this narrow natural scenario against an authorized trusted ingress.
It is not permission to install on the owner's phone or change production/G4.

All private DB/identity/key material, raw local evidence, generated/native inputs and
APKs remain outside Git. Only safe source/tests/docs and sanitized receipts are pushed
with `[skip ci]`. No full CI/110-test rerun. Own test services are stopped at completion.

## Completed artifact and closing evidence

**Source `b2a37fe989294018ab08060bdebfa46d741d11d5`**, pushed non-force with `[skip ci]`,
verified by `git ls-remote` before building. Closing documentation changes do not change
that source or APK. The natural test APK SHA256 is
`7116072c53f89dcb1cd7b57c3bfa79d824b10546e05c491d94018fdf9e5d35f7`;
that is the disposable x86_64 artifact, **not** the following normal ARM64 package.

| ARM candidate property/check | Actual result |
| --- | --- |
| Local artifact | `state-client-build/subscription-android-2/release/FamilyConnect-Test-0.1.18-beta119.apk` in this worktree |
| Persistent local copy | `/mnt/data/fc-subscription-android-2-build/release/FamilyConnect-Test-0.1.18-beta119.apk`, same verified SHA256; not a published URL |
| Variant/package | `friends` release-derived, `com.familyconnect.app.friends`, debuggable=false |
| Version/ABI/SDK | `0.1.18-beta119`,119, exactly `arm64-v8a`, min27/target35 |
| Signed APK bytes | 50,351,520 |
| Signed APK SHA256 | `52a9847b74181c48808c86a0c5bf5925b53ef498eec628aef2d78d26f1c92d2d` |
| Unsigned payload SHA256 | `480fcc5279c7377611a51269c3e7f6bab31d07b28a4c11a1b3083e2836e0b994` |
| Existing signer | PASS, exactly one certificate matching pin above; APK v2/v3 verification PASS, no rotation/replacement key |
| Native source binding | PASS, ordinary producer built current restricted ARM64: SHA256 `dbd033704d7132690e8f19da4b404d9df272ffa5c1b224029a1d44342cfca82c`, source/tree checks, Telemost, no diagnostic tags |
| Required native payload | PASS, AWG, restricted, Codec2, exit audio, Chaquopy and Python3.10 ARM64 libraries present; accepted unchanged AWG/audio provenance checked |
| Python subscription integration | PASS, actual Chaquopy `app.imy` contains `messenger/subscription_view.pyc` and encrypted-store wrapper |
| Ordinary endpoint/TLS | PASS, original HTTPS origin in DEX, no test origin/package/CA/security-config, cleartext=false, original platform trust |
| Alignment/payload integrity | PASS, unsigned and signed zipalign `-c -P 16 -v 4`; signing preserves every non-META-INF ZIP entry byte-for-byte |
| Local build/lint | PASS, standard `assembleFriends`, `lintFriends`, source-bound `verifyFriendsRestrictedInputs`;52s Gradle run |
| Scoped Friends JVM | PASS,26 Subscription* tests through actual Gradle Friends test classpath |
| Native producer gate | PASS, existing packet tests `go test -race -count=3` run by the ordinary native builder |
| ARM installation/runtime | NOT_RUN; APK is only built/signed/inspected, no physical ARM device/owner installation |
| Publication/production ingress | NOT_RUN; no upload, release tag, download/catalog update, production deployment or request |

Current user-facing Friends releases support ARM64/Android8.1+, as documented for118;
the legacy generic four-ABI debug target is not an ARMv7 user release claim.
Signing reused the existing local beta-v1 key through `scripts/sign_android_vault.sign`
and memfd inputs, after validating its known certificate pin. No key/password export,
new production key or debug signer was used. Local qualification/signing is explicitly
not a claim of a new full platform-CI release gate or installed-device acceptance.

Reproduction uses the unchanged standard producer/build commands on that clean source:

```sh
# Existing pinned tools; all writable cache/temp/output paths belong to this task.
GOMAXPROCS=2 GOCACHE="$OWN_CACHE/go-cache" GOMODCACHE="$OWN_CACHE/go-mod" \
  GOPATH="$OWN_CACHE/gopath" TMPDIR="$OWN_CACHE/tmp" \
  python pilot/android-restricted/build.py --xray "$PINNED_XRAY" \
  --go "$TOOLS/go/bin/go" --ndk "$TOOLS/android/ndk/28.2.13676358" \
  --out "$PWD/clients/android/restricted-generated"
"$TOOLS/gradle-8.11.1/bin/gradle" -p clients/android --no-daemon --offline --max-workers=1 \
  -Dorg.gradle.jvmargs=-Xmx2048m -PfcFriendsCi=false -PfcTargetAbi=arm64-v8a \
  -PfcBuildPython="$BUILD_PYTHON_310" :app:assembleFriends \
  :app:testFriendsUnitTest --tests 'com.familyconnect.app.Subscription*' :app:lintFriends
python pilot/android-restricted/package_ci.py --source-commit "$SOURCE_SHA" \
  --out "$OWN_OUTPUT" --apksigner "$TOOLS/android/build-tools/35.0.0/apksigner" --android-only
```

Tools: Java17.0.20.1, Gradle8.11.1, AGP8.9.2, SDK35/NDK28.2.13676358, Go1.26.1,
Chaquopy16.1.0/build Python3.10.15. No test init script or endpoint override in this ARM
command. The earlier task's private Gradle cache was reused; new Go cache/temp live in
`/mnt/data/fc-subscription-android-2-build`, not shared dependencies or G4 directories.
Only unchanged AWG/audio binaries are reused; restricted native and all Java/Python
were built from the stated final source, not a relabelled old APK.

[Sanitized receipt](2026-11-06-subscription-android-2-receipt.json) binds artifacts and
local evidence hashes. Natural notification enqueue/post counters stayed2/3 before and
after repeat refresh, with no active subscription notification after viewing it. The
final read-only instrumented assertion binds the saved device to the actual vault.
Actual HTTP evidence has routes/status/time only, no proofs or raw personal responses.

Own synthetic backend PID2036194 stopped with SIGTERM; reused AVD PID2036658 stopped
through its task marker, launcher exit0 and shared lock released. All previous/private
evidence retained. G4, main checkout, host routing, production, paid baseline/limits,
updater113 and field118 bytes remain untouched. **Narrow task complete; candidate ready
for the separate authorized ARM/ingress check, not a fully accepted installed update.**
