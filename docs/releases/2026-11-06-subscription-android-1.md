# SUBSCRIPTION-ANDROID-1 — isolated Android qualification, 6 November 2026

## Scope and candidate

**Bounded Android runtime PASS on the disposable API35 Wi-Fi/TLS configuration below;
not a production installation, release, merge or full transport qualification.**
One mixed-underlay observation remains FAIL; physical whitelist networking is NOT_RUN.
The previous [HTTP/source report](2026-11-06-subscription-authenticated-api.md) remains
the exact schema1 contract and prior Python/JVM evidence, not Android evidence.

- Branch/worktree: `feature/subscription-status-20261106`, `/tmp/fc-subscription-status-20261106`.
- Starting local and verified remote: `34529b62259445b500917412d670d91cede84b77`.
  No subsequent branch changes existed at entry; no reset, clean or history rewrite.
- Source checkpoint and final rebuild/push receipt are recorded in the closing section.
- Product fix: resolve the checked `ControlIdentity.reference()` before constructing
  `SubscriptionRequest.Exchange`; its non-throwing `device()` callback returns that bound
  reference. Android compilation exposed this defect; the previous pure JVM tests did not
  compile `FriendsAccessAndroid`. No authentication/enforcement/paid semantics changed.
- Existing canonical `paid_beta`, actual `access-api.py::Handler`, Friends one-use proof,
  vault, bounded HTTPS client, Chaquopy decoder, encrypted chat store, event projection,
  channel/tags/durable flags and navigation were reused. No new delivery transport.

## Build and actual installation

| Item | Actual value |
| --- | --- |
| Variant | Standard Gradle `debug`, single `x86_64`, `fcFriendsCi=true`; opt-in test init script |
| Package | `com.familyconnect.app.subscriptiontest` (separate from production/owner app) |
| Version | `0.1.18-beta118` / 118; fresh separate package, no update/version bump needed |
| SDK | min26, target/compile35; AGP8.9.2, Gradle8.11.1, Java17, Chaquopy16.1.0 / Python3.10 |
| APK | `state-client-build/subscription-android-1/android/app/outputs/apk/debug/app-debug.apk` in this worktree |
| APK SHA256 | `c2f17387c95651d78c7f79e87c0f97990cf891a28a4ec6098a88e5dddd69c479` |
| Test APK SHA256 | `4895b3270c8fd08db2f5c01ea7ef4b4f9686c891fdab1e610b44d25b89357092` |
| Installation | Actual `adb -s emulator-5672 install -r -t` for app and instrumentation; data retained between runs |
| Device | Disposable Pixel2-profile Google APIs x86_64 emulator, Android15/API35 |
| Fingerprint | `google/sdk_gphone64_x86_64/emu64xa:15/AE3A.240806.043/12960925:userdebug/dev-keys` |
| Execution | KVM, `-gpu host`, PRIME NVIDIA GTX1650Ti, actual guest NVIDIA renderer verified; 2 cores/2GiB |

The test init script changes only generated qualification inputs: applicationId/label,
Friends launcher, disposable signing key, control origin to `https://10.0.2.2:18443`, and
app-scoped test CA trust. It rejects non-debug tasks. Ordinary source URLs, signing,
network security and Gradle dependencies are unchanged. No permissive TLS verifier.
The APK is diagnostic and useful only with its short-lived local TLS stand, **not an
APK to distribute or install over an owner's app**. It is not a release/friends build.

Unchanged AWG/audio x86_64 native binaries and assets were reused from the archived
APK118 debug input (source `13e0b37`, APK SHA256
`096faed4bc9bf80fe544cef5511816f0adcefed42e5aba9a199f8b8f041ad1c6`).
`pilot/android-awg` and `clients/android/audio` have no diff against that source.
AWG generated Java was copied read-only to this worktree. This debug input contains no
`libfc_restricted.so`; native MESH/VPN was neither rebuilt nor exercised. Current Java
and Python/Chaquopy were built and executed. Do not infer native/release acceptance.

## Actual HTTP → Android results

Test backend: loopback-only `127.0.0.1:18443`, real Handler and isolated
`state-client-build/subscription-android-1/private/synthetic.sqlite`. Migration/init was
performed only when creating this new test database, never on a read/product database.
One Android-generated test Friends identity enrolled by the real activation HTTP path.
Subsequent requests use real fresh `subscription` challenge/proof. Canonical fixture
events use `paid_beta.apply_event`; no JSON snapshot injection into the client.

| Check | Result | Evidence / boundary |
| --- | --- | --- |
| App + test APK build; Chaquopy packaging/start | PASS | Gradle assemblies; real Python decoder/store calls on installed app |
| Android lint | PASS | `:app:lintDebug`, 37s; no native/full-CI run |
| Outside pilot | PASS | Real own read, cohort=false, null snapshot; UI does not claim unpaid |
| Active, no corresponding event | PASS | Canonical payment snapshot, synthetic missing last-event reference; no confirmation/notice invented |
| Active, corresponding renewal | PASS | Canonical payment extension → real HTTPS → decoder → encrypted projection → access-extension text |
| Expired, no VPN | PASS | Canonical APPLIED `expire`, endpoint200 and Ended/renewal UI; identity remains valid |
| Grace | PASS | Canonical APPLIED `grace`; real RU UI describes grace, not received money |
| Paid revoked versus identity revoked | PASS | Paid `revoke` still readable200; later device identity revocation gives403/identity_rejected, preserves cache |
| Old endpoint / temporary failure | PASS | Test Handler wrapper returns404 /503 only for new route; unsupported/unavailable distinguished, cache retained |
| Process death, offline Keystore/store, recovery | PASS | Force-stop, both emulator networks off, new process/vault/store opens, same identity/nonexportable keys; Wi-Fi restore fresh200 |
| Time display | PASS | UI observation/access boundary equals stored epoch formatting; real Europe/Brussels +01:00 clock; EN and RU |
| Repeat event / process restart | PASS | Same event/tag, durable notified flag, unchanged post time when notification survives; no new post after restart |
| Notifications allowed / denied | PASS | Actual API35 POST_NOTIFICATIONS grant/revoke, existing channel; denied case still renders working screen |
| Cold / warm navigation | PASS | Real notification-shade tap with absent/live app PID, opens subscription screen and reaches confirmed footer |
| Cancelled late response | PASS | Real server delayed200; cancellation during request leaves encrypted projection unchanged |
| HTTPS certificate and hostname | PASS | Android platform validates app-scoped CA and IP SAN; mismatched localhost SAN rejected with SSLPeerUnverifiedException |
| New requests after mixed Wi-Fi/cellular toggle | FAIL | One unavailable result, no corresponding HTTP; cellular cannot reach loopback test origin; details below |
| Physical whitelist network (C) | NOT_RUN | No authorized physical whitelist environment available |
| Production HTTPS ingress/reachability | NOT_RUN | No authorized test deployment of that ingress in this task; local stand is not production evidence |
| Physical ARM device / release signing / API27 | NOT_RUN | Only dedicated x86_64 API35 AVD available/selected; no owner's phone used |
| Natural wall-clock expiry on Android | NOT_RUN | Android expired case uses explicit canonical expire event; natural unchanged-version expiry remains prior unit/HTTP evidence |
| Actual owner/identity switch during request | NOT_RUN | Existing cancellation gate exercised with real late HTTP; no new identity-management flow introduced |

The active/no-event fixture keeps the immutable event table intact and points the
synthetic subscription at an unavailable last-event ID. An initial DELETE attempt was
rejected by `PAID_EVENT_IMMUTABLE` and rolled back; no trigger was disabled. This tests
the actual server's snapshot-only branch, not a mocked HTTP body.
Explicit expiration can precede the stored period end; the UI correctly labels that
date **last confirmed period end**, not current entitlement. It was not a timed-expiry test.

Fresh refresh and screen-opening each perform real bounded operations; instrumentation
does not bypass `SubscriptionRequest`/Chaquopy validation or call store accept with a
prepared dictionary. Registration itself did not produce a subscription confirmation.
`payment` means confirmed access provision/extension, not proof of money received;
`grace`, `expire`, `revoke` preserve their respective meanings despite all being APPLIED.

### Notification trigger — important limitation

Subscription fetching happens **only on screen opening or explicit Refresh**, never
from a new background polling/push service. A refresh saves the latest relevant event,
not a full delivery history. The open screen marks its displayed notice read and cancels
its existing notification. `ChatRuntime.tick` in the existing delivery runtime calls
`deliverNotifications` for saved unread events; it does not fetch subscriptions.

Tests deliberately enroll without configuring a VPN or completing the normal activated-UI
workflow. For notifications they invoke the existing `deliverNotifications` on
`ChatRuntime.WORKER` after a real refresh, then inspect actual Android notifications.
Thus channel/permission/tag/flags/restart/navigation are tested, **automatic service
scheduling after normal activation and delivery of new events while idle are not**.
No background receipt guarantee follows from the cold/warm tap tests.

### Network A/B/C and retained failures

- **A PASS:** installed APK → test HTTPS origin via emulator Wi-Fi, Family Connect
  status off, no Android VPN active/always-on/lockdown, no third-party VPN. Host normal
  connectivity and G4 networking were not changed. Same test-origin config for every case.
- **B PASS:** same path with registered expired and subsequently paid-revoked identity:
  subscription read still succeeds without acquiring/renewing paid VPN access. Actual
  identity revocation rejects the read. Enforcement and every other endpoint stay intact.
- **C NOT_RUN:** later use an authorized dedicated Android device and an explicitly
  allowed test ingress with valid hostname/chain in that physical whitelist network.
  Disable both VPNs, use a synthetic valid identity with expired paid access, open the
  screen/Refresh, retain status/time/error and sanitized handler receipt. Require a fresh
  200 with expired state; separately check revoked identity403. Do not infer C from A/B,
  change production allowlists, or disable TLS to get a pass.

`online-restored-final` failed after simultaneously re-enabling Wi-Fi and simulated
cellular. Cache remained honest/unavailable, not unpaid. A later per-Network probe found
Wi-Fi HTTPS501 (expected unsupported GET on real Handler) versus cellular SocketException
caused by ErrnoException. Existing underlay selection picks an available non-VPN network;
no fallback/retry redesign was made. Subsequent mixed refresh passed when Wi-Fi was
selected, but this does not erase the earlier FAIL or qualify arbitrary mixed networks.
Final offline/recovery matrix explicitly disables cellular and passes on Wi-Fi.

Other retained failures were corrected without weakening product assertions:
the checked-exception Android build defect above; test-only Files.writeString replaced
by Android-compatible Files.write; shell quoting of multiword instrumentation extras;
wrong test expectations for the confirmed footer and event `revoke` (not `revoked`).
Original logs remain separate. Tests await final refresh footer, not a transient cached UI.

## Reproduction, evidence and independent gates

Added opt-in harness: `tests/subscription_android.init.gradle`,
`tests/subscription_android_stand.py`, `tests/subscription_android_emulator.py`,
`tests/subscription_android_run.py`,
`tests/android-subscription/java/com/familyconnect/app/SubscriptionRuntimeTest.java`.
Normal build/test source sets do not include this instrumentation.

All private state, keys, invitation, DB, evidence, caches and APKs remain ignored under
`state-client-build/subscription-android-1`; none is pushed. HTTP log records only route,
status and time. `logs/*-instrumentation.txt`, `runtime-results.jsonl`, screen/notification
captures, `logs/http.jsonl`, `emulator.json` retain original attempts, including failures.
The final sanitized receipt records artifact hashes and source separately from these logs.

Actual local tool root (reused read-only) was
`/mnt/data/PycharmProjects/family_connect/state-client-build/field65-export16/diag-source-freeze-1/resume-tools`.
Task-owned GRADLE_USER_HOME is a copy, not that tool root's cache. Python3.10.15 build
interpreter is local under `inputs/python`; backend uses the existing isolated
`/tmp/fc-subscription-venv-20261106/bin/python`. No global dependencies changed.

For a fresh disposable work directory, stage the verified base118 APK as
`inputs/base118.apk`, copy existing AWG generated inputs into this worktree, create
`private`/`logs`, then run stand `prepare` once. It creates only the new synthetic DB,
CA/leaf/invitation and extracts native payload. Create a disposable Android debug key
at `private/debug.keystore` with the standard debug alias/password; never use release keys.
Do not run prepare again on an existing DB. The emulator script requires the existing
shared `android-emulator.lock` directory and refuses a second concurrent emulator.

```sh
WORK="$PWD/state-client-build/subscription-android-1"
TOOLS=/path/to/existing/read-only/resume-tools
export JAVA_HOME="$TOOLS/jdk" ANDROID_HOME="$TOOLS/android" ANDROID_SDK_ROOT="$TOOLS/android"
export GRADLE_USER_HOME="$WORK/gradle-home" ANDROID_USER_HOME="$WORK/android-user"
export PIP_CACHE_DIR="$WORK/pip-cache" PATH="$JAVA_HOME/bin:$PATH"
"$TOOLS/gradle-8.11.1/bin/gradle" -p clients/android --no-daemon --offline --max-workers=1 \
  -Dorg.gradle.jvmargs=-Xmx2048m -I "$PWD/tests/subscription_android.init.gradle" \
  -PfcFriendsCi=true -PfcTargetAbi=x86_64 -PfcSubscriptionWork="$WORK" \
  -PfcBuildPython="$WORK/inputs/python/bin/python3.10" \
  :app:assembleDebug :app:assembleDebugAndroidTest :app:lintDebug
PYTHONPATH=. /tmp/fc-subscription-venv-20261106/bin/python tests/subscription_android_stand.py serve --work "$WORK"
```

Start the emulator using `--tools`, `--work`, `--lock-directory`; its real boot/NVIDIA
receipt must pass before `subscription_android_run.py install --work "$WORK"`.
Use driver `test --method enroll` once, then `refreshAndScreen` with
`--values '{"state":"outside","event":"none","screen":"paid pilot"}'` (use exact
current localized screen text). Fixture `scenario --action snapshot-only/active/expire/grace/revoke`
creates the canonical test states. Identity revocation must be last. `unsupported`,
`unavailable`, `slow`, `normal` only change the test HTTP wrapper behavior. Unique labels
preserve old attempts. Use only serial `emulator-5672` and this disposable package.
Stop only the owned backend PID; create `$WORK/stop-emulator` to release the AVD/lock.

Seven targeted `SubscriptionRequestTest` JVM tests PASS after the fix; three Python
harness files pass syntax checks. Prior84 Python/26 JVM tests were **not rerun/counting
as new evidence**. Future independent gates: production-equivalent trusted test ingress,
physical ARM/release packaging, normal activation/service scheduling and physical
whitelist network. No need to redesign the API for these gates.

## Isolation and closing receipt

No main checkout changes, G4 inspection/polling/restart, frozen-source edits, certificate
renewal, container/Docker actions, host-network changes, production DB migration,
paid baseline/cohort/limits edits, updater113 changes, release signing, APK publication
or merge. Shared tools were read-only; the one-emulator qualification lock was honored.
Synthetic baseline metadata is only a fixture in the isolated DB, not a cohort rollout.
Only the task's test backend and AVD are stopped at completion; evidence is retained.

Source commit, verified remote SHA and final same-source artifact verification follow
in the closing receipt after the source checkpoint is saved.
