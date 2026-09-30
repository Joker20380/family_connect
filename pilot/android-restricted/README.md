# Android restricted whole-device diagnostic — 5N.6

Перед physical run телефон должен быть разблокирован и экран включён; runner
проверяет это до создания seed, не обходит PIN/keyguard. Underlay использует
доступный IPv4 resolver физической сети, захваченный до TUN. Это provider DNS,
не fallback для destination DNS приложений. После controlled session failure
обычная Android TCP probe к literal public IPv4 обязана отказать при всё ещё
активном VPN и owner health unavailable; ожидание браузером DNS само по себе
не считается доказательством fail-closed.

Изолированный opt-in, не public release и не Connectivity Orchestrator.
Текущий результат: [отчёт](../../docs/releases/2026-09-30-webrtc-eu6-android-full-device.ru.md).

## Границы

`ConnectionService` остаётся единственным connection owner (worker, generation,
ControlOperations, cancellation, notification, stop). `RestrictedTunnelEngine`
использует **существующий** `TcpVpnService`/permission flow; нового VpnService нет.
Normal AWG/TCP factories и AutoPolicy не заменяются. Debug activity существует
только в debug manifest; managed identity этим одноразовым диагностическим
профилем заменить нельзя. Beta package не удалять и не переустанавливать.

JNI держит один monotonic session handle, отвергает stale attach/stop. Общий
`carrier/wholedevice` связывает packet connections с существующим Mux.OpenTCP и
QueryDNS. Этот слой не зависит от Android и не делает destination socket dial.
Android-specific: TUN fd, protect callback, permission/service ownership.
Будущий iOS adapter может использовать ту же границу; iOS здесь не реализован.

Packet stack — существующий pinned Xray TUN/gVisor, **не новый TCP/IP stack**.
`xray-packet-boundary.patch` открывает имеющийся ConnectionHandler/LinkEndpoint
boundary, ограничивает pending TCP/UDP и устраняет UDP close/send race.
Изменения MPL source включены в assets рядом с Xray/gVisor/carrier licenses.
Normal `libfc-awg` не пересобирается этим скриптом и не подменяется.

## Порядок и fail-closed

1. Debug APK получает обычное системное VPN permission.
2. Изолированный private Family profile (`no_backup/restricted/family.json`,0600)
   и normal authenticated mTLS endpoint используются только для cache refresh.
3. Force-stop/restart сохраняет atomic BOOT-1 directory в no-backup storage.
4. Recover проверяет отказ `https://127.0.0.1:1` — диагностическая подмена normal
   endpoint, **не доказательство реального carrier-wide ограничения**.
5. Cached bootstrap → Family auth → existing broker → fresh dedicated READY →
   descriptor через bootstrap → bootstrap close → dedicated Family TLS/binding/Mux.
6. Только после `dedicated_data_ready` создаются TUN/default routes и packet adapter.
   VpnService стартует раньше только для `protect(fd)`, маршрутов тогда ещё нет.

Per-session protected network перед connect/bind вызывает VpnService.protect для
HTTPS, WebSocket, ICE/STUN/TURN/media и provider DNS. Resolver берётся из physical
underlay **до** TUN. Unprotected fallback отсутствует; closing owner блокирует
новые protect callbacks до освобождения JNI reference. Provider DNS — отдельная
разрешённая underlay операция, не destination/app DNS.

TUN захватывает `0.0.0.0/0`, `::/0`, DNS=`10.79.0.1`, без excluded applications /
allowBypass. UDP53 и TCP53 → один Family DNS; generic UDP/QUIC и IPv6 отклоняются.
Прочий IPv4 TCP → Mux, включая DoT как TCP, но специальная поддержка DoT не принята.
32 TCP/16 DNS admissions, Mux32, 2×16KiB copy buffers/flow, DNS4096/10s,
gVisor TCP default64/max128KiB, pending64 и UDP16. Отдельные streams, half-close/reset.

При session loss существующие app flows закрываются, но owner **держит TUN**:
status on + health unavailable, без прямого fallback или бесконечного reconnect.
Explicit stop закрывает native/session/packet engine перед TUN/service. Android
process death завершает OS VPN согласно существующему lifecycle: это не always-on
lockdown guarantee; seamless migration/restart recovery здесь не обещаны.

## Сборка и проверка

Go1.26, JDK17+, Android SDK35/NDK27.2, существующие normal generated assets,
Python3.10 для Chaquopy. Xray checkout должен быть на
`d2758a023cd7f4174a5a5fa4ff66e487d4342ba0`; Go modules pinned в go.mod/go.sum.

```sh
python3 pilot/android-restricted/build.py --xray /path/to/pinned/Xray-core \
  --go /path/to/go --ndk /path/to/ndk --out /tmp/fc-eu6-native-fresh
# Скопировать jniLibs и assets в ignored clients/android/restricted-generated.
gradle -p clients/android :app:assembleDebug :app:testDebugUnitTest :app:lintDebug \
  -PfcTargetAbi=arm64-v8a -PfcRestrictedDiagnostic=true -PfcBuildPython=/path/to/python3.10
```

Shared tests: carrier `go test -race ./underlay ./wholedevice ./bootstrap
./roombroker ./telemost ./familysession ./tcpforward`, затем соответствующий vet.
Packet fixture: применить patch к отдельному pinned Xray checkout, создать временный
Go modfile с absolute replaces этого checkout и carrier; из этого каталога выполнить
`go test -race -modfile=/tmp/native.mod ./packet` и `go vet` с тем же modfile.
Python: `tests/test_restricted_android_contract.py`, `tests/test_restricted_acceptance.py`.
Structural source tests не заменяют реальный Android lifecycle acceptance.

## Physical runner

`acceptance.py` требует ADB, готовые APK/server binary, свежие disposable fixtures
из `pilot/telemost_family_fixture.py`, fresh evidence directory, OAuth только в
environment. Ни token, ни private profile, ни room URL не попадают в evidence/Git.
SSH используется только для isolated Amsterdam process, token передаётся stdin
в environment без файла. ADB только install/start/UI/evidence/uninstall.
Никаких reverse/forward/tunnel. Не запускать поверх другой VPN или beta package.

Runner: official seed → refresh → restart → recover → real VPN → контролируемые
Chrome HTTPS destinations → обычные app DNS/UDP/IPv6 probes → light smoke540s →
SIGTERM isolated dedicated gateway → VPN-retained failure → graceful stop/uninstall
и remote process/directory cleanup. Evidence numeric/allowlisted; UI разбирается
в памяти, browsing content не сохраняется. DNS/TCP bypass claims требуют именно
живых route/counter/failure evidence, не одного PASS unit-тестов.

Ограничения: no automatic Orchestrator, no generic UDP, IPv6 fail-closed, no flow
migration, no production rollout/capacity claim, no fresh restricted install
guarantee, no second carrier, no iOS. После gate — STOP.
