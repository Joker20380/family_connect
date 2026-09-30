# Android restricted whole-device diagnostic — 5N.6

Перед physical run телефон должен быть разблокирован и экран включён; runner
проверяет это до создания seed, не обходит PIN/keyguard. Underlay использует
доступный IPv4 resolver физической сети, захваченный до TUN. Это provider DNS,
не fallback для destination DNS приложений. После controlled session failure
обычная Android TCP probe к literal public IPv4 обязана отказать при всё ещё
активном VPN и owner health unavailable; ожидание браузером DNS само по себе
не считается доказательством fail-closed.

Исходный EU-6 runner ниже — изолированный opt-in, не public release. Новый
MVP Orchestrator использует тот же backend, отдельный debug suffix `.orchestrator`
и existing TcpVpnService guard; [отчёт/scope](../../docs/releases/2026-09-30-mvp-connectivity-orchestrator.ru.md).
Текущий результат: [отчёт](../../docs/releases/2026-09-30-webrtc-eu6-android-full-device.ru.md).

## Границы

`ConnectionService` остаётся единственным connection owner (worker, generation,
ControlOperations, cancellation, notification, stop). `RestrictedTunnelEngine`
использует **существующий** `TcpVpnService`/permission flow; нового VpnService нет.
Manual normal AWG/TCP factories не заменяются. Старый AutoPolicy заменён bounded
ConnectivityOrchestrator; automatic adapters используют один TcpVpnService. Debug activity существует
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

Ограничения исходной5N.6 acceptance: no automatic Orchestrator, no generic UDP, IPv6 fail-closed, no flow
migration, no production rollout/capacity claim, no fresh restricted install
guarantee, no second carrier, no iOS. После gate — STOP.

## MVP normal-path runner (не full gate PASS)

`orchestrator_normal.py` использует отдельный `.orchestrator` APK, временный REALITY
process в `/tmp` Amsterdam: без production credentials/config/services, без forwarded
traffic. Current build флаг `-PfcOrchestratorDiagnostic=true`, arm64 native build тот же.
Runner требует unlocked Redmi/Android12/arm64, Wi-Fi OFF/cellular ON/no other VPN.
При запрете MIUI ADB input используйте `--manual-ui`: пользователь сам нажимает
CONNECT/Android permission. Не обходить INJECT_EVENTS и не менять appops ради теста.
Debug Activity запускается NEW_TASK|MULTIPLE_TASK: иначе Android может направить
повторный Intent в singleTask MainActivity вместо injection Activity. Receipt OK
без target/actual events недостаточен. `--lifecycle-only` пропускает browser/probe и
никогда не является browser PASS. Parser читает text/content-desc; только ожидаемый
body marker и host без ERR_* подтверждают контрольную страницу.

Сценарии: only-configured TCP auto → browser; controlled active-backend failure →
one restoration; second failure → retained guard/ordinary negative TCP; forced
AWG-unavailable → alternate TCP; all normal unavailable → automatic restricted
attempt/BOOTSTRAP_UNAVAILABLE без activation. Последний **не restricted success**.
Fresh BOOT-1 full acceptance дополнительно требует server-only OAuth и disposable
Family activation/directory из existing bootstrap runbook. Эти prerequisites не
восстанавливать из expired fixtures и не заменять manual room URL.

В evidence только allowlisted state events/counters/results; no profiles/tokens.
Нативные/OS fail-closed утверждения требуют live routes/probes, не source-only tests.
Runner finally удаляет owned APK/server;600s supervisor ограничивает abandoned server.

### Fresh native / automatic restricted follow-up

Для physical Orchestrator runner теперь обязателен current-source normal JNI:
`pilot/android-awg/build.py --abi arm64-v8a --out /tmp/fresh-normal` (Go1.26.1,
`ANDROID_NDK_HOME`). Без этих flags default остаётся four-ABI build.
Gradle должен использовать именно fresh `jniLibs` и `assets`; embedded
`awg-build.json`/binary сверяются с текущими Go/JNI/builder hashes до установки.
Не выдавать cached REALITY/XHTTP artifact за current-source validation.

Normal runner `--normal-only --trace` ограничивает diagnostic run двумя controlled
sites и allowlisted fixture error labels:180s/512 records, без raw log/payload.
`--host` принимает только два authorized gateway IP; default Amsterdam. Host должен
иметь свободный diagnostic port; не менять production firewall/services для теста.
Automatic TCP не объявляет неподтверждённый IPv6 source address, но захватывает
`::/0`: это устраняет Chrome IPv6 optimism при IPv4-only egress. Native packet
handshake сам по себе не означает remote IPv6 connectivity.

После normal Chrome PASS используйте existing `acceptance.py` с
`--orchestrator --manual-ui --seconds 600` и fresh disposable `--family-dir`,
current bootstrap broker, `.orchestrator` APK. OAuth только в runner environment;
helper subprocess environment очищается, server получает credential через stdin
в память. Refresh/cache/restart — setup, затем user action только CONNECT.
`deny_normal` диагностически отключает все три configured normal candidates
(AWG/WG/TCP); native recovery не подменяется manual room/recover intent.
Acceptance проверяет exact candidate ordering, fresh BOOT-1/dedicated/Chrome,
Family DNS/concurrency/underlay counters, smoke без restoration/flapping, затем
controlled gateway failure с RESTORING→FAILED и retained VPN. Эта fault simulation
не является утверждением об ISP и не разрешает FIELD-1 или production rollout.
