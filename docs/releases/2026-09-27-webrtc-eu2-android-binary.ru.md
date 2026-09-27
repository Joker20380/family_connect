# WEBRTC-EU-2 / 5N.2 — physical Android binary Telemost

Дата:27.09.2026. **IN PROGRESS / gate OPEN** до полной physical acceptance.
5N.1 остаётся PASS (`a13068e`, docs `35f890f`), regression assertions не ослаблены.
5N.3/5N.4 не начинаются. Production Android beta51/Linux0.2.11/Windows0.2.15
не менялись; public release/installed product/invitation artifacts не затрагивались.

## Integration

- Existing `carrier/telemost` + `cmd/telemost-binary`: Linux wrapper или Android
  arm64 PIE executable; без копии source/нового WebRTC stack. Только optional
  resource sampler и Android-only parent-death guard добавлены к CLI.
- Standalone `clients/android/telemost-runtime`, package `com.familyconnect.telemosttest`,
  debug version1/5N.2-test-only. Нет production imports, AWG/Xray, Chaquopy, JNI/TUN.
- Foreground Service owns one child; installer extracts executable into nativeLibraryDir.
  Cancellation SIGTERM →5s forced deadline; constructor `PR_SET_PDEATHSIG(SIGKILL)`.
  No sticky restart;25min cap, original10s per echo, no reconnect/replay.
- Go1.27.1, NDK28.2.13676358/API26, Pion4.2.15, SDK35, AGP8.9.2/Gradle8.11.1/JDK17.
  Android anet0.0.5 needs upstream-documented `-checklinkname=0`; Linux flag unchanged.
  ELF interpreter `/system/bin/linker64`, LOAD alignment0x4000. Not16KiB-device acceptance.
- TLS roots system+Conscrypt APEX; TLS verification not disabled. Android CGO DNS;
  Pion existing anet interface workaround forAPI30+. ICE enabled UDP4 only.
- Socket protection **not implemented**. Exact HTTP/WS/Pion transport.Net/DNS and
  SCM_RIGHTS or JNI extension points: [runbook](../../clients/android/telemost-runtime/README.md).

## Device

- Physical **Redmi Note9 Pro**, Android12/API31, ABIarm64-v8a; USB ADB authorized.
- Preliminary active network: **cellular**, VPN not visible to test app. Subscriber
  identifiers/serial/network operator/cell details are not collected.
- Test APK built and installed separately; product app not updated. No public distribution.
- Source checkpoint before integration `35f890fb1cd11c9fdbba0c86c085ff6d4e59f939`;
  preliminary binary dirty hash `a5e1683eb133ac89a8a9aab83167ab4b2202d4affbb1cc056c5fc9bd7bc9e16a`.
  This preliminary artifact is not final clean-runtime evidence.

## Real Telemost

Room created manually via official UI, provided solely by `FC_TELEMOST_ROOM`.
ADB stdin → private one-shot input → child env; SSH stdin → B env.
No URL/token/cookie/ICE credential in APK/Git/report/argv/logs.
Amsterdam186.246.45.246: temporary nobody echo, no listener/service/routes changes.
Preliminary join: ROOM_RESOLVED → SIGNALING_CONNECTED → SERVER_HELLO → ICE_CONFIGURED
→ both PC connected → VP8_MEDIA_ACTIVE. Setup2964ms. No waiting room observed.
Android candidates host/srflx/relay; selected PC pairs host/host UDP, no selected TURN.
Candidate presence is not evidence that a relay was used; underlying hops not asserted.

## Binary results

Preliminary seven sizes1,32,256,1024,4096,16384,65536B: each sent1/received1,
byte_equal=true, carrier_mode=vp8. RTT3761.053/1984.050/2008.748/2005.588/
2057.493/2210.262/2208.784ms respectively. Stopped intentionally before full suite
to capture clean source checkpoint. DataChannel not used.
Full100×1KiB/100×16KiB/30s/5min, final RTT/throughput/CPU/RSS: pending.

## Lifecycle

Preliminary force-stop: app PID9186 and native PID9218 both absent afterwards;
parent-death guard works in this observation. The operator runner removes B artifacts.
MIUI disallows ADB `input keyevent` (INJECT_EVENTS); use explicit test Activity actions
for recreation/finish/disconnect, real physical screen control for screen checks.
Background/screen/network transitions and graceful cleanup still pending.

## Tests and known limitations

Initial build,3 JVM owner tests, Android lint (0errors,6warnings), Linux race suite,
vet/modules PASS. Final rerun/fuzz pending. Linux207-check harness retained.
No TUN, FAMILY auth, real VPN traffic, protected sockets or restricted Krasnodar claim.
No deep Doze, auto reconnect or full-device fail-closed guarantee. USB charging makes
battery percentage observational only. No throughput optimization rewrite.
Rollout is test-device-only; rollback is force-stop/uninstall diagnostic package and
temporary B cleanup. No production rollback needed. No push/publication.
