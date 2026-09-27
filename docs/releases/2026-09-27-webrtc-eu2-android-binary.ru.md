# WEBRTC-EU-2 / 5N.2 — physical Android binary Telemost: PASS

27.09.2026: **WEBRTC-EU-2 / 5N.2 = PASS**. Настоящий physical Android →
Telemost SFU VP8 → Amsterdam Linux → binary echo → Telemost → Android.
Финальная acceptance: **372 byte-for-byte checks**, включая30s/5min;
corruption, unexpected disconnect, echo timeout, reconnect и RTP sequence gaps — **0**.
DataChannel не использовался для acceptance. **NEXT = WEBRTC-EU-3 / 5N.3**,
но5N.3/5N.4 в этой задаче не начаты.5N.1 остаётся PASS/regression harness.

[Sanitized machine evidence](2026-09-27-webrtc-eu2-live.sanitized.json)
· [Build/operator runbook](../../clients/android/telemost-runtime/README.md).
Повторяющиеся candidate events в evidence сведены в счётчики типов;
selected pairs, state timestamps, corpus results, resource samples и faults сохранены.

## Integration

Изученная production boundary: `FriendsActivity` → `ConnectionService` →
`TunnelEngine`; AWG/TCP используют existing Go native runtime/JNI, TCP protection
идёт через `NativeTcp`/`TcpVpnService` и native Go hooks. Chaquopy — отдельный
Python/messaging runtime. **Эти пути не изменены** и не используются test APK.

Выбран минимальный отдельный endpoint:

```text
shared carrier/telemost + cmd/telemost-binary
    ├── Linux executable wrapper
    └── Android arm64 PIE executable
          └── isolated ProbeService / NativeRun / ProbeActivity
```

- Нет копии Go source, Java WebRTC stack, custom JNI bridge, TUN или второго Go
  runtime внутри production APK. `libfc_telemost.so` — имя для APK packaging,
  **исполняемый PIE**, не `System.loadLibrary`; installer извлекает его в nativeLibraryDir.
- Shared signaling/heartbeat/ICE/VP8/framing/bounds/echo unchanged. В CLI добавлены
  только optional10s CPU/memory metrics, PID metadata и Android-only parent guard.
- Отдельный debug-only `com.familyconnect.telemosttest`, versionCode1,
  versionName`5N.2-test-only`; кнопки Run/Disconnect. Foreground Service owns one child;
  explicit input, no auto-selection/reconnect, no sticky restart,25min cap/10s per echo.
- Android12 действительно исполняет extracted ELF из read-only install directory.
  LOAD alignment0x4000; interpreter `/system/bin/linker64`. Это не16KiB-device acceptance.
- Toolchain: Go1.27.1, Pion4.2.15, NDK28.2.13676358/API26, SDK35/build-tools35.0.0,
  AGP8.9.2, Gradle8.11.1, JDK17. Только ABIarm64-v8a.
- Existing anet0.0.5 обход API30+ interface restrictions проверен фактическим ICE.
  Его documented Go1.23+ `-checklinkname=0` нужен только Android build; dependencies
  не менялись. Private zone-cache ABI требует повторной проверки при обновлении Go.
- TLS verification включена; system CA + Conscrypt APEX directories, Android CGO DNS.
  Android14+/другие OEM/ABI не приняты этим результатом. ICE media здесь UDP4, не TCP/IPv6.
- APK содержит тот же23-module inventory и original dependency/reference/NDK/LLVM
  notices. Наличие aggregate compiler notices не означает linkage всех перечисленных tools.

### Socket ownership / future protection

Все HTTP/WS/STUN/TURN/ICE/media sockets принадлежат child process. Они **не protected**.
Тест работает вне VpnService; APK отказывает при видимом VPN и периодически проверяет его,
но это не firewall/fail-closed guarantee. Нет production traffic или FAMILY auth/E2E;
WebRTC DTLS не равен Family E2E, SFU untrusted, payload только synthetic random bytes.

Точные будущие hooks: Config.HTTPClient/Transport.DialContext, WebSocket
Dialer.NetDialContext, Pion SettingEngine.SetNet(transport.Net), отдельный DNS resolver.
Child fd integer нельзя передать напрямую в Java: нужен private SCM_RIGHTS transfer
с `VpnService.protect(duplicateFd)`/network-bind ACK до использования сокета или
JNI внутри **единого** product Go runtime. Bridge/5N.6 сейчас не реализованы.

## Device / artifacts

- Physical **Redmi Note9 Pro**, Android12/API31, ABIarm64-v8a, USB ADB.
- Network: обычная доступная **cellular**, как сообщил Android ConnectivityManager.
  Не сохранялись serial/Android ID/IMSI/номер/оператор/SSID/BSSID.
- Room: existing operator-provided disposable room из5N.1, источник только
  `FC_TELEMOST_ROOM`; manual official-UI creation — метод5N.1 runbook, отдельно
  агентом здесь не воспроизводился. SSH stdin → B env; ADB stdin → private mode0600 one-shot
  input → A env. Input удалён, URL не в argv/APK/Git/docs/fixtures/logs.
- B: существующий Amsterdam Linux/amd64 **186.246.45.246**, отдельный временный
  process **nobody/UID65534**. `/proc/.../exe` hashes обоих реально работающих endpoints
  сверены с local artifacts, не только с build metadata.

Финальный clean runtime обоих endpoints: **`3f65346a02d621c0843975cbe84173d23ebba91f`**,
`vcs.modified=false`. APK built+installed **только на test device**, не опубликован.

| Artifact | SHA256 |
| --- | --- |
| Diagnostic APK | `2642cba98b29f3c7dbf2f6984e10e61cacc95c39c18e85618a346d4ddb22022b` |
| Android native PIE | `d83bbc8c4d1596e88afa5decfb39bb33e257a5e2c14e5bda4e578bd30152aa47` |
| Linux B executable | `fbf6f4bce509f71dfa3ec9ecd17318aa0feb19e620f405ea4568d90d2bb7c13e` |

Production Android beta51/code51, Linux0.2.11, Windows0.2.15, public artifacts,
signed catalogs, invitation/activation и production/default routes/services не менялись.
Никакого production rollout, release signing или push.

## Real Telemost / ICE

На обоих endpoints: **ROOM_RESOLVED → SIGNALING_CONNECTED → SERVER_HELLO →
ICE_CONFIGURED → SUBSCRIBER_CONNECTED + PUBLISHER_CONNECTED → VP8_MEDIA_ACTIVE**.
Setup A2368ms/B1838ms. `waiting_room_required=no`; speculative polling не добавлялся.
На Android собраны host/srflx/relay candidates. Pion selected pairs обоих PC на обоих
endpoints: **host/host, UDP, turn_used=false**. Это только Pion-observable pair,
не утверждение об отсутствии NAT/VPN/внутренних SFU hops или о конкретной физической трассе.
Наличие relay candidates само по себе не означает TURN usage.

Shared application heartbeat выдержал main window: A149 application pings,
200 signaling ACKs, application pongs0; pongs не заявляются наблюдавшимися.
WS4008 не повторился. После завершения оба PC closed, native exit0/cancelled=false.

## Binary results — final clean runtime

Все строки: **carrier_mode=vp8**, sent=received, byte_equal=true.
Main A window12:14:21–12:26:51 UTC, app/native session749.892s.

| Payload / phase | Sent / received | Mean RTT, ms | Max RTT, ms | Duration, s |
| --- | --- | --- | --- | --- |
| 1B | 1 / 1 | 2229.665 | 2229.665 | 2.229721 |
| 32B | 1 / 1 | 1998.647 | 1998.647 | 1.998716 |
| 256B | 1 / 1 | 1998.080 | 1998.080 | 1.998153 |
| 1KiB | 1 / 1 | 2001.199 | 2001.199 | 2.001275 |
| 4KiB | 1 / 1 | 2052.908 | 2052.908 | 2.053035 |
| 16KiB | 1 / 1 | 2119.067 | 2119.067 | 2.119286 |
| 64KiB | 1 / 1 | 2302.078 | 2302.078 | 2.302900 |
| 100×1KiB | 100 / 100 | 1995.091 | 2015.556 | 199.515063 |
| 100×16KiB | 100 / 100 | 2001.773 | 2169.524 | 200.197876 |
| 30s sustained,16KiB | 15 / 15 | 1999.979 | 2019.654 | 30.002491 |
| 5min sustained,16KiB | 150 / 150 | 1999.844 | 2057.696 | 300.006638 |

Итого **372 exact echoes**, A/B каждый TX=RX **4,531,489B**; каждый декодировал
645 VP8 binary fragments. A RTPReceived4263/B4261, sequence gaps0.
Corruption, unexpected disconnect, echo timeout и reconnect в acceptance —0.
Преднамеренные fault tests ниже в эти counters не включены.

Useful throughput30s: **0.131061 Mbit/s aggregate**;
5min: **0.131069 Mbit/s aggregate**, ≈0.065535 Mbit/s в одном направлении.
Это payload throughput, не RTP/link bitrate и не peak-speed acceptance.

### Comparison / repeatability

Первый полный clean run `c3a874d`11:34:17–11:50:12 UTC тоже PASS:
290 checks, TX=RX3,188,001B,30s=8 echoes,5min=75 echoes/300.000351s;
5min RTT3999.807ms, aggregate0.065536Mbit/s, ошибок0. Он близок к Linux5N.1
RTT≈4s/0.065538Mbit/s. Финальный повтор быстрее, но **не приписываем это shutdown fix**:
общий Go carrier не менялся, stop hook во время нормального echo не вызывается.
Есть вариативность2–4s/shared carrier/SFU/network timing; точная причина не доказана.
Android-specific ухудшение RTT/throughput не наблюдалось. Optimization rewrite не делался.

## CPU / memory

Final runtime:74 native и75 Android samples с10s interval.

- Go CPU user22.279504s + system21.200868s =43.480372s,
  ≈**5.80% одного CPU core** за749.892s.
- App CPU delta52.449s за742.499s, ≈**7.06% одного core**; это отдельный wrapper/UI
  process, не Go CPU. Не процент от всей восьмиядерной системы.
- Current native RSS `/proc/self/statm`: все samples13,193,216B =**12.582MiB**.
  Go heap sampled3,348,408–10,161,288B (3.19–9.69MiB); final summary8,741,464B.
- `getrusage.maxrss`114,228KiB (111.55MiB) — отдельный high-water показатель,
  не current RSS; spawn/exec history может влиять. Не подменяем его sampled RSS.
- Java heap2,584,488–5,297,224B (2.46–5.05MiB). App total PSS48,913–141,658KiB,
  последний133,933KiB. PSS включает весь app process, не только Java heap.
- Go goroutines167→165 в samples, **3 после Close**; оба PC closed и child завершился.
  Неограниченного роста в этом окне не наблюдалось; это не универсальный leak proof.
- Bounds unchanged: outgoing256 fragments, incoming16 messages, reassembly16 partial
  messages×≤64KiB,≤8 fragments/message, TTL10s, recent IDs≤4096. Physical Android
  framing/bounds tests PASS. Это проверенные caps, не live queue-depth gauges;
  отдельный allocation profile каждого reassembly object не снимался.
- Battery79→85% при USB connection/charging. Это не измерение расхода батареи;
  energy-efficiency/long battery-life claim отсутствует.

## Lifecycle / failure handling

| Check | Actual result |
| --- | --- |
| Foreground→background20s→foreground | PASS на final runtime; app/native PID сохранились, echo продолжился |
| Activity recreation | PASS на final runtime; повторный bind, тот же worker/PID; duplicate-owner JVM test PASS |
| Screen off/on | Physical15.064s interval в первом full run; события зарегистрированы, corpus после него PASS; не deep Doze |
| User Disconnect | Final SIGTERM: native exit1/cancelled=true, summary сохранён, оба PC closed, no SIGPIPE; terminal observed≤2.19s при2s polling |
| Activity finish | Final exit1/cancelled=true, closed PCs, native absent; terminal observed≤2.17s |
| Process termination | `am force-stop` после real echo; native отсутствует. Kernel guard установлен, но causal attribution только ему этим тестом не доказывается |
| Network loss | Cellular отключён после real echo: **WS_FAIL/read_error → SESSION_CLOSED**, terminal observed2.005s. Исходный mobile-data enabled восстановлен |
| Explicit recovery | Новый join после восстановления cellular дал exact VP8 echo; затем final full run PASS. Auto reconnect отсутствует |
| Remote B exit | Final **ECHO_TIMEOUT**, original10s per-echo deadline; observed≤11.02s с SSH/2s polling overhead, native отсутствует |
| Signaling close on Android | Existing opt-in native `TestLiveSignalingClosure`: prerequisite real VP8 echo PASS, close16ms, Recv terminates/Send rejects, both PCs closed |
| Wi-Fi disconnect/reconnect / mobile↔Wi-Fi | NOT RUN: Wi-Fi enabled, но not connected по Android status; credentials/SSID не запрашивались/не сохранялись. Handoff claim отсутствует |

Дополнительная попытка parent-only SIGKILL через run-as была отклонена operator command;
не засчитана как отдельный guard test. `am force-stop` проверен на финальном APK.
MIUI `input keyevent` требует INJECT_EVENTS; Activity finish/recreation проверялись
explicit diagnostic actions, screen — физической кнопкой. Permissions не ослаблялись.

### Live-discovered Android fixes

`c3a874d` добавил isolated runtime. Cancellation показала, что Android Process.destroy
закрывает stdout раньше native exit: wrapper сначала терял exit metrics (`-1`),
после ожидания (`d8e450c`) проявился SIGPIPE141. **`3f65346`** отправляет SIGTERM через
Android API только проверенному child PID/parent, сохраняя pipes; fallback/reaper bounded5s.
Race/owned-signal regression tests и повторный real Disconnect PASS; после этого
**вся матрица повторена на final clean runtime**, не только старый APK.

Первый operator smoke не доставил private input через ADB exec-out; исправлен
stdin path `adb shell -T`, проверен non-secret input. Это было ROOM_INPUT_INVALID
до carrier join, не Telemost/signaling failure. Room нигде не печаталась.

## Verification / disposition

- Linux5N.1 tests сохранены: `go test -race -count=1 -timeout120s ./...` PASS,
  включая local two-process207 exact VP8 checks; vet/module verification/build PASS.
- FuzzDecode5s:427,901 executions PASS; FuzzReassembler5s:60,722 PASS.
- Android build + **6 JVM owner/cancellation tests** PASS; lint0 errors/6 non-blocking
  UI localization warnings. Existing production Android source/build files не менялись.
- Physical Android native executable:7 framing/reassembly/CRC/RTP bounds tests +
  live signaling-close test PASS. Этот test binary — тот же Go core revision c3a874d;
  последующие commits меняли только Java wrapper, не carrier implementation.
- APK/extracted native hash и remote running executable hash проверены; runtime clean.
  Последний внешний unrelated phase0 CI для origin8e36858 был failure до этой задачи;
  полный product/platform CI здесь не заявляется зелёным.
- Final cleanup: **Amsterdam test processes0/directories0**, Android app stopped,
  все recorded native PID/temporary native test directories отсутствуют,
  `room.input` отсутствует, mobile_data=1/wifi_on=1 восстановлены/сохранены. Test APK оставлен
  установленным, stopped; private sanitized evidence сохранена. Production не менялась.
- Rollback: `adb uninstall com.familyconnect.telemosttest` удаляет только test APK/data;
  B temporary artifacts уже удалены, production rollback не нужен. Public release,
  signing/update catalog/invitation rollout не выполнялись; push отсутствует.

## Known limitations / stop point

No TUN, FAMILY auth/E2E, protected sockets, production user traffic, restricted
Краснодар-mobile/5M, TCP/IPv6-media, deep Doze, Wi-Fi handoff or auto-reconnect claims.
Latency2–4s/низкий throughput требуют дальнейшего решения, не production acceptance.
Другие Android versions/ABIs, fine-grained allocation profiling и protection bridge —
не приняты этим PoC. **NEXT=WEBRTC-EU-3 / 5N.3; остановиться, не начинать автоматически.**
