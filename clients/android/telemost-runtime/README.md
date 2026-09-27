# Physical Android synthetic Telemost gate — 5N.2

This is a **separate debug-only APK**, `com.familyconnect.telemosttest`, not the
Family Connect beta. No VpnService, TUN, production traffic, FAMILY authentication,
Chaquopy, AWG/Xray, transport selection or automatic fallback is included.
DTLS is not Family E2E. Only generated random payloads enter the untrusted SFU.

## Shared core and packaging

`carrier/telemost` and the **same** `carrier/cmd/telemost-binary` used by Linux
are cross-compiled with Go/Pion for Android/arm64, API26+, CGO and NDK28.2.
There is no source copy or Java WebRTC implementation. The PIE executable is
packaged as `lib/arm64-v8a/libfc_telemost.so`, extracted by the package installer
and executed from `ApplicationInfo.nativeLibraryDir`. It is not `System.loadLibrary`:
the Go runtime runs in one child process, never alongside the product AWG Go runtime.
No execution from writable app data or public application listener is needed.
16KiB ELF LOAD alignment is requested; it is not a 16KiB-device acceptance claim.
The APK contains the existing carrier dependency/license notices and build metadata.

Pion's existing `transport/v4` uses `anet` for Android API30+ interface enumeration.
Pinned `anet v0.0.5` requires its documented Go1.23+ `-checklinkname=0` flag because
it accesses private zone caches; this **Android-only build workaround** does not
change module versions or Linux builds. Revalidate on any Go/anet upgrade.
TLS verification remains enabled. `SSL_CERT_DIR` includes system CA and Android14+
Conscrypt APEX directories. DNS uses Android's CGO resolver. Neither newer Android
CA behavior nor every vendor's interface restrictions follows from a cross-build.
The shared carrier still enables UDP4 ICE, not TCP/IPv6-media acceptance.

## Build

Linux host needs Go1.24+ (tested1.27.1), JDK17, Gradle8.11.1, SDK35,
build-tools35.0.0 and NDK28.2.13676358. From the repository root:

```sh
python3 pilot/android-telemost/build.py --ndk "$ANDROID_HOME/ndk/28.2.13676358"
cd clients/android/telemost-runtime
gradle :app:assembleDebug :app:testDebugUnitTest :app:lintDebug
adb install -r app/build/outputs/apk/debug/app-debug.apk
```

Only arm64-v8a is packaged. Generated files/caches/APKs are ignored. Release tasks
are disabled; this APK has no production update catalog or publication workflow.
Build metadata records commit, dirty flag, native hash, Go and NDK versions.
Use clean source for final acceptance and record the APK hash separately.

## Run

Disable active VPNs before testing. The harness refuses a visible VPN at start
and checks again every10s; this is **not** a fail-closed firewall or leak guarantee.
Start the Amsterdam **unprivileged temporary echo** first using `carrier/README.md`.
Open “Telemost 5N.2 TEST”, enter the disposable room into the masked field, and tap
“Connect + run VP8 binary suite”. The input is cleared immediately and not saved
across recreation. Screenshots/autofill/backups are disabled for this test app.

For the existing SSH/operator path, the repeatable runner accepts room **only**
through `FC_TELEMOST_ROOM`, never arguments. Build a Linux executable first:

```sh
(cd carrier && go build -trimpath -o /tmp/fc-telemost-binary ./cmd/telemost-binary)
python3 pilot/android-telemost/live.py --binary /tmp/fc-telemost-binary \
  --out /tmp/fc-android-acceptance
```

The runner copies only binary/notices to a fresh Amsterdam directory and starts
`nobody` without installing services or changing routes. Room is delivered to B
over SSH stdin, to A over ADB stdin into a mode0600 private one-shot `room.input`,
then removed by the Activity and finally by the runner. It is never an intent extra,
argv, build config, APK asset or shell-script literal. Do not print environment,
`/proc/*/environ`, raw signaling, all logcat or unrestricted process diagnostics.
The room exists transiently in process memory/environment; rooted/debug access can
read it. This is a disposable debug harness, not a secret-vault/security claim.

The same seven sizes, 100×1KiB, 100×16KiB,30s and5min execute in sequence. Mode is
hardcoded **VP8** in this wrapper, never DC. Each echo has the original10s deadline;
overall session and Java watchdog are25min. No automatic reconnect or replay.
`evidence.jsonl` is private, bounded to2MiB/1024 events; UI tail24K characters,
child line128KiB. Raw stderr is discarded rather than displayed; sanitized core
evidence classifies network/protocol failures. Metrics every10s include Go heap,
current RSS when observable, RSS high-water, CPU and goroutines; Java heap/PSS,
app CPU, network type and battery percentage are separate. Charging over USB means
battery percentage is not a power-efficiency measurement.

## Lifecycle and teardown

A bound foreground test Service owns exactly one child. Activity recreation only
rebinds. Home/background retains the test; Back/explicit Disconnect/task removal
cancel it. The Service is non-exported, START_NOT_STICKY, with no boot receiver.
An explicit launcher `disconnect=true` diagnostic action allows bounded ADB tests.
Cancellation sends SIGTERM; after5s a reaper force-kills that exact child. Android-only
native constructor installs `PR_SET_PDEATHSIG(SIGKILL)` before Go initialization and
rejects an already lost parent. Abrupt process death releases OS sockets, but is not
graceful signaling leave. The owning Java thread stays alive until the child exits.
Verify this on a physical device; JVM tests alone cannot establish Android behavior.

Runner fault cases: `--case cancel`, `activity-close`, `process-death`, `remote-exit`.
Each waits for a real exact echo before triggering its fault. Save evidence before
another run (the next explicit start replaces the private log). After testing,
verify no child remains; remove the temporary B directory and local binary. Optional
`adb uninstall com.familyconnect.telemosttest` removes only this test APK/data.
Do not restore/change any production VPN or manipulate the product beta.

## Future protected socket boundary (not implemented)

This child owns every carrier socket. **Passing its integer fd to Java is wrong**:
fd tables differ between processes. For5N.6 choose an in-process JNI callback or an
app-private authenticated Unix socket with SCM_RIGHTS duplicate-fd transfer and an
ACK: Java applies `VpnService.protect(duplicateFd)`/underlying-Network binding before
the child can use the socket. Protection refusal/timeout must fail closed. Cover:

- HTTP: `telemost.Config.HTTPClient` → `http.Transport.DialContext` / `net.Dialer.Control`.
- WebSocket: `telemost.dialWebSocket`'s `websocket.Dialer.NetDialContext` (currently unset).
- STUN/TURN/ICE/media: Pion `SettingEngine.SetNet(transport.Net)`, covering UDP/TCP
  dial, listen, `CreateDialer` and `CreateListenConfig`, including future retries.
- DNS/bootstrap: explicit protected resolver or Android underlying `Network` resolver;
  libc/netd resolution is not proven protected by wrapping the HTTP socket alone.

No protection bridge is implemented or asserted here. Full-device VPN and leak
validation remain5N.6; FAMILY auth remains5N.3, neither starts with this test.
