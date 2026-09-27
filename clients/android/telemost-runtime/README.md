# Physical Android synthetic Telemost gates — 5N.2 / 5N.3

This is a **separate debug-only APK**, `com.familyconnect.telemosttest`, not the
Family Connect beta. No VpnService, TUN, production traffic, Chaquopy, AWG/Xray,
transport selection or automatic fallback is included. Code2 / `5N.3-test-only`
adds an opt-in authenticated Family TLS1.3 session above the unchanged VP8 carrier.
Without private operator credentials it remains the plaintext5N.2 diagnostic.
DTLS is not Family E2E. Only generated random payloads are used.

**5N.3 PASS27.09**: runtime5dd8b49, physical Redmi374 exact echoes/302.001s,
live Family negatives/replay and lifecycle/recovery. Diagnostic APK was subsequently
uninstalled, never distributed. [Report/hashes/limits](../../../docs/releases/2026-09-27-webrtc-eu3-family-session.ru.md).

## Isolated Family acceptance

Read [the session profile](../../../docs/testing/webrtc-eu3-session-profile.md)
before using this mode. The disposable issuer uses existing DeviceIdentity and
ProductStore enrollment/authorization/revocation against a **new temporary DB**.
It accepts no existing DB or production signing key. PKCS8 keys are copies of
these disposable identities' Ed25519 signing seeds, never WireGuard keys. The
short-lived test certificate binds the full RNS public identity (URI SAN), role,
family, revision (named OU attributes), expiry and issuer. The gateway identity
is pinned. Current signed CRL and local trusted revision floors are mandatory.
TLS1.3 only, mutual certificates, versioned ALPN, no tickets/0-RTT/retry/fallback.
This does not implement production provisioning or mobile secure-store integration.

```sh
python -m pilot.telemost_family_fixture --out /tmp/fc-family-fixture
python3 pilot/android-telemost/live.py --binary /tmp/fc-telemost-binary \
  --family-dir /tmp/fc-family-fixture --independent-observer \
  --out /tmp/fc-family-acceptance
```

Use the existing control + identity Python lockfiles. `--client-profile revoked`,
`wrong-family`, `unknown` run negative admission cases: B must reject and A must
complete no echo. Credentials stay in mode0600 `family.input` in the app-private
directory and B's temporary directory, never intent extras/argv/APK/Git/logs.
The runner removes both inputs and remote artifacts in `finally`; remove the
local fixture directory (including its disposable DB) after all cases. Stop and
uninstall only `com.familyconnect.telemosttest` at final cleanup. No diagnostic APK
is publicly distributed. Never keep credentials after their test window.

Use `--independent-observer` for sustained runs: the exact same temporary nobody
binary writes bounded private files under an owned supervisor, not a persistent
SSH stdout pipe. Short SSH snapshots preserve remote exit and evidence; `finally`
terminates/reaps only owned processes and removes the directory. Two earlier5N.3
attempts lost their runuser parent at320s and timed out; they remain FAIL in the
report. The exact terminating signal is unknown. No transport retry, deadline
relaxation, production SSH config change or service installation is involved.
Staging uses a compressed archive (45s bound), deleted locally even on failure.
Fixtures expire after1h; generate fresh disposable identities for a later test
window, never extend/reissue a failed active session to turn it green.

The same seven payload sizes/100×1KiB/100×16KiB/30s/5min and10s echo deadlines
apply. Useful metrics count application bytes, excluding TLS/test headers/RTP;
one-way=TX×8/elapsed/1e6; aggregate=(TX+RX)×8/elapsed/1e6. RTT samples are bounded
to4096/phase; nearest-rank p50/p95/p99 appear only when the sample set is complete.
Ordering is additionally checked by monotonic sequence inside encrypted test
messages. Loss/reorder that TLS cannot authenticate closes/times out, never retries.

## Opt-in 5N-PERF-1 measurement harness

The default canonical suite is unchanged. `--performance-config` in the physical
runner installs a private, non-secret `performance.input` containing bounded JSON:
`window` (1–128), `payload` (1024–65536 bytes), `seconds` (1–300),
`warmup_seconds` (1–30), `rate_mbit_s` (zero for sliding window, or0.01–4).
Only authenticated VP8 is accepted. Independent send/receive workers preserve
exact byte validation and monotonic sequence association; no carrier/framing/auth
change, automatic retry, recovery, TUN or production integration is introduced.

After a fresh successful canonical physical baseline (at least60s at16KiB), use:

```sh
python3 pilot/android-telemost/capacity.py \
  --baseline /tmp/fc-family-acceptance/A.jsonl --adb /path/to/adb \
  --binary /tmp/fc-telemost-binary --family-dir /tmp/fc-family-fixture \
  --out /tmp/fc-capacity --windows 1 2 4 8 16 32 64
```

`FC_TELEMOST_ROOM` is still environment/stdin-only. For independent offered load,
replace `--windows ...` with `--rates 0.1 0.25 0.5 1 2`; review before testing4.
The128-outstanding limit is a stop condition, not ACK-paced rate limiting.
Use `--seconds 300` for long validation; `<60s` is discovery only. Each point has
5s warm-up, drains it, then starts a new measurement clock and finally drains
measurement traffic. A failure aborts the point and series; do not retry until green.
Never mix a failed long run into a zero-error short-run result.

The producer has bounded outstanding payloads, a10s creation-to-echo deadline and
a16384-sample cap. `perf_result` retains interval TX/RX rates separately from the
measurement-plus-drain rate; `perf_blocks` retains monotonic timing rows.
`perf_sample` retains queue gauges and numeric/boolean Pion statistics for nominated
ICE pairs only. Raw addresses, SDP, credentials and arbitrary error text are excluded.
`terminal_error_class` distinguishes authenticated-record rejection from generic
closure; `corruption=0` only means no unequal plaintext was accepted, not absence
of a TLS-integrity failure. `missing` means sent without a confirmed exact echo,
not necessarily forward-path loss. B's `perf_echo` rows retain application receive/
echo-send timings for successfully submitted echoes, not independently synchronized
one-way network latency. Polling samples are not exact queue high-water marks.

The physical runner removes `performance.input` with the other private inputs.
Diagnostic APK remains code2/5N.3-test-only and is not a published release.
[27.09 results and limitations](../../../docs/releases/2026-09-27-webrtc-5n-perf1-carrier-capacity.ru.md):
the old stop-and-wait rate is not the carrier ceiling, but high-load long runs
encountered TLS rejection after RTP gaps; no sustainable capacity ceiling is accepted.

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
Open “Telemost isolated TEST”, enter the disposable room into the masked field, and tap
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
Cancellation sends SIGTERM; after5s a reaper force-kills that exact child.
Normal Android stop uses `android.os.Process.sendSignal` after checking the CLI's PID/parent
metadata against the owning app. `Process.destroy()` closes output pipes on Android:
it is only a pre-metadata fallback, not normal stop. The reader still waits for exit
if a pipe closes early; this avoids premature SIGKILL and preserves final PC metrics.
The Android-only native constructor installs `PR_SET_PDEATHSIG(SIGKILL)` before Go initialization and
rejects an already lost parent. Abrupt process death releases OS sockets, but is not
graceful signaling leave. The owning Java thread stays alive until the child exits.
Verify this on a physical device; JVM tests alone cannot establish Android behavior.
An app force-stop test establishes overall process cleanup, not independent causal
attribution to the kernel parent-death guard. Do not claim the latter from force-stop alone.

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

An in-process design must join the existing product Go build/runtime; do not load
a second independent Go shared library beside AWG/Xray.

- HTTP: `telemost.Config.HTTPClient` → `http.Transport.DialContext` / `net.Dialer.Control`.
- WebSocket: `telemost.dialWebSocket`'s `websocket.Dialer.NetDialContext` (currently unset).
- STUN/TURN/ICE/media: Pion `SettingEngine.SetNet(transport.Net)`, covering UDP/TCP
  dial, listen, `CreateDialer` and `CreateListenConfig`, including future retries.
- DNS/bootstrap: explicit protected resolver or Android underlying `Network` resolver;
  libc/netd resolution is not proven protected by wrapping the HTTP socket alone.

No protection bridge is implemented or asserted here. Full-device VPN and leak
validation remain5N.6; the isolated5N.3 mode does not start that work.
