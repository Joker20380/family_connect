# L04.1-LIVE-1 — exact final-2 installed AWG/TCP,25.10.2026

## Решение и граница

**PARTIAL / first product failure / review pending.** Это не DONE и не общий L04.1 PASS.
L03.1/L03.2/parent L03 DONE, review accepted. AUTH/PROVISION DONE, review accepted.
L04 и L04.1 IN_PROGRESS; LIVE-2/L04.2/L05 не начаты.

Проверен неизменный final-2: real DEB installation/GUI/pkexec/READY; три AWG и одна
TCP сессия через installed GUI, DNS/HTTPS/download/upload через TUN, disconnect,
reconnect и AWG→TCP→AWG PASS. Original AppImage также подключил AWG, передал трафик
и сохранил единственного root owner при втором запуске и подтверждённом закрытии GUI.

**Первый отказ:** после открытия original AppImage заново видимый **Disconnect**
вернул `Operation failed. Check the profile, system VPN and permissions.` /
`Connection settings are being updated`. AWG owner/TUN оставались живыми.
Положительный сценарий немедленно остановлен; последующих connect не было.
Ограниченный cleanup-only через GUI после освобождения operation lock завершил
owner и восстановил network baseline. Этот cleanup не превращает отказ в PASS.
Product source/installed files/artifacts не исправлялись и не пересобирались.

## Точные входы и версии

Входная `main` и проверенный remote:
`2d3dc50fd66bb71d1a59c4d13a5331480bef0a30`.
Product source: `cf66532c72548767f8ff4aa31faa7588b07eab54`.
Candidate ID: `9d4b13cc106296264805402b42538b9fa94505433b1bbd239c82145966e22b81`.
System build-9: `8708ba6d5e218f86b42d862dd5a66237e974a03d5434e8f1c30524b16720e2da`.

Источник только `state-client-build/linux-candidate-l032-20261025/build-final-2/`:

| Артефакт | Bytes | SHA256 |
|---|---:|---|
| `FamilyConnect-0.2.12~l03.2.1-x86_64.AppImage` | 57924088 | `914f02ff10f31485c5a6b68a8ff41f5b168aaffc8f7f8241723365c40a9109e5` |
| `FamilyConnect_0.2.12~l03.2.1_amd64.deb` | 55951120 | `df13422321f6c5865f1ca1060fe221fbe21954c6981ab05cb2d173e7aa6e04ac` |

Hashes/sizes проверены до установки. CI rebuild `f7f6e765…` не использован.
Source/public Linux0.2.11 не изменён; built и guest-installed internal version —
0.2.12~l03.2.1. На рабочую Ubuntu ничего не установлено; публикации нет.
[L03.2 provenance](2026-10-25-linux-candidate-l03-2.md) остаётся исходным package evidence.

## Реальное изолированное окружение

Ubuntu24.04 cloud image, проверенный официальный SHA256SUMS; QEMU10.2.1/KVM,
q35,2CPU/4GiB, kernel6.8.0-147-generic. Отдельный LUKS-encrypted qcow2 overlay.
SLIRP outbound NAT и loopback SSH forward, без host TAP/bridge/route/DNS changes.
Не контейнер, не fake systemctl, не helper-CLI connect, не synthetic gateway.

Guest: systemd/systemd-resolved255.4-1ubuntu8.18, NetworkManager1.46.0,
polkit/pkexec124, gnome-keyring46.1, nftables1.0.9, iptables1.8.10, iproute2,
real `/dev/net/tun`, private system/user D-Bus. GTK4.14.5/libadwaita1.5,
Xvfb/Openbox, обычный UID1000 и настоящий polkit GNOME authentication agent.
Secret Service разблокирован и проверен через D-Bus. GUI управлялся AT-SPI/мышью;
пароль одноразового guest передавался только по stdin, не в argv/logs.
Allow-all polkit rules, GTK test overrides и mock-success не использованы.

## Handoff, установка и baseline

- Existing read-only `operator/preflight.sh` PASS до действий и после уничтожения VM.
  Support ID **FC-3YSQ-BE2D**; public identity SHA256
  `d07d33a81728ff70aec350ae59785990c194d90ecd44574b0da28439189532de`.
- Из protected `/var/tmp/fc-l04-test-20261025-6uva6jb3` передан только `home/`,
  потоково через SSH, без plaintext промежуточного архива. `operator/`, invite
  artifacts и teardown receipt в guest не передавались.
- До GUI: UID1000, directories0700/files0600; no symlink/hardlink/special files;
  installed Python3.12 `-I -S`/vendor, identity `create=False`, тот же fingerprint,
  cache только nl, signed assignment и floor/readback PASS.
- HOME `/home/tester`; XDG config/data/state — `.config`, `.local/share`, `.local/state`
  внутри этого HOME. Никакого нового identity fallback или копирования личных identities.
- Exact DEB установлен; `/usr/bin/family-connect --candidate-check` проверил user
  inventory/imports. GUI запущен UID1000. До setup root runtime отсутствовал, TUN нет.
- Штатное GUI Settings → Install system component (no VPN) → Install, настоящее
  pkexec с authentication dialog: READY, exact build-9, full installed readback
  (763 installed files). Setup не создавал TUN/VPN intent или active session.
- GUI закрыт/открыт, user `family-connect-chat.service` перезапущен: active,
  прежняя identity/Support ID. Messenger/live chat actions не выполнялись.
- Baseline: только lo/enp0s2,0 TUN/owned routes/owned rules/nft tables,
  0 root FC units/owners/journals. Routes4/6 counts9/7, rules4/6 counts3/2.
  DNS/domains/default-route, nft/iptables structure и процессы сняты отдельно.

Public IP SHA256 до/после:
`3f53078c747ff27aa70f8906808e6030259e94412c4b964d6b12f1ac45d8444b`.
Во всех connected sessions подтверждён ожидаемый nl gateway186.246.45.246;
IP SHA256 `9e873c4c9e4f0a2356811cce0215504451108ce64fae1d466c1b41e13622b086`.

## Сессии и transfers

Все connect — кнопкой installed GUI/backend/authorized helper. Нет прямого `up`,
ручного configuration fetch, profile apply CLI или SOCKS-only доказательства.
Наблюдаемые selected-next/actual: awg/awg либо tcp/tcp; после штатного disconnect
actual none. Country только nl. В GUI selector fixture кратко выбрал Auto, исправил
выбор до Connect; Auto VPN start/fallback не выполнялся.

| Сессия | GUI connection/session ID | Root generation / invocation | Interface |
|---|---|---|---|
| DEB AWG-1 | `88ccd0b2-42a4-487a-8930-733c958bacf9` | `866fc3fd977bc3230e40beedcd9e57bc` | `fcawge26e8134` |
| DEB AWG-2 | `570afadd-07e3-49d2-9836-20fe79964d00` | `e1ae4431508cd950b8a5f0a08334151e` | `fcawg76a8121c` |
| DEB TCP-1 | `503c1ea7-1c75-400e-973d-7fc70ebdd2cd` | systemd `21e437ba49fb4512b376bbe75cd4f1ee` | `fctcp49345951` |
| DEB AWG-3 после TCP | `0fdf53f0-7c57-4902-86e6-206d69a9fa36` | `592ad0d7cf78809513ea918924bd7e1d` | `fcawg6774edd7` |
| AppImage AWG | `b8f3f5fd-0f7d-4e9b-94bf-135fdcd28e37` | `8f11d345f0f8c988959c5a81baa70209` | `fcawg8ee67225` |

| Сессия | DNS/HTTPS | Download/upload bytes | TUN RX/TX delta bytes | Handshake / cleanup |
|---|---|---:|---:|---|
| DEB AWG-1 | PASS | 65536 / 65536 | 83369 / 71994 | AWG handshake PASS; disconnect PASS |
| DEB AWG-2 | PASS | 65536 / 65536 | 83702 / 71918 | fresh generation, handshake PASS; disconnect PASS |
| DEB TCP-1 | PASS | 65536 / 65536 | 84878 / 74282 | full TUN/Xray PASS; disconnect PASS |
| DEB AWG-3 | PASS | 65536 / 65536 | 83749 / 71578 | handshake PASS; disconnect PASS |
| AppImage AWG | PASS | 65536 / 65536 | 83370 / 72150 | handshake PASS; reopened Disconnect FAIL, cleanup-only PASS later |

`ip route get` подтверждал соответствующий TUN; `resolvectl query example.com`
PASS, per-link DNS/domain/default-route readback сохранён. HTTPS ipify подтверждал
gateway; bounded Cloudflare download и zero-filled POST upload по64KiB, HTTP200.
RX/TX приращения подтверждают data path, не только CONNECTED label. Скорость не gate.
DNS PASS здесь означает успешный resolver query и согласованный link/route readback;
отдельный fresh-query packet capture/cache flush не выполнялся. Прямое wire-level
доказательство каждого DNS запроса ограничено: повторный query мог использовать cache.

AWG:1 amneziawg-go owner,1 TUN, owned routes4/6 по2, rules counts5/4,
две family nft `wg-quick-<interface>` tables. TCP:1 helper+1 Xray service owner,
1 TUN, owned routes4/6 по1, rules counts7/4, nft baseline unchanged. Никакого
пересечения AWG/TCP. Все DEB disconnect возвращали точные network/firewall/DNS/IP
baseline hashes, без active markers или transport worker.

Fixture correction, не product retry: при AWG-2 первая counter probe использовала
имя уже удалённого AWG-1 interface и завершилась до traffic. Взято фактическое имя
из snapshot той же текущей сессии; reconnect не делался. GTK combo не предоставлял
activate action, выбор выполнен мышью по реальному popup, не backend bypass.

## AppImage coherence и first failure

Original exact AppImage запускался напрямую из `/opt/fc-internal/`, через FUSE,
не extracted launcher. Environment/process readback подтвердил original APPIMAGE,
тот же UID/HOME; оба формата возвращали exact candidate и system READY. State/cache
одни и те же, дополнительного root component нет. Второй GUI launch коалесцировался
в существующий application instance; root process/interface/generation не менялись.

При Close появился штатный warning, затем нажато **Close window**; фактический
GUI PID завершился. Owner, TUN, routes/rules/nft/DNS/public IP остались прежними.
Original AppImage открыт снова; UI показал **Disconnect / Tunnel is on**.
Нажатие Disconnect дало первый product failure, без запроса polkit authentication.
Root generation оставалась `8f11d345f0f8c988959c5a81baa70209`, AWG process жив.
Diagnostics ring нового GUI при этом: DISCONNECTED/actual none/first_failure NONE,
connection ID `8f95480c-a232-4245-9da9-07d8daf97080`; это не достоверный disconnect.

Read-only `lslocks` показал GUI PID15396 с WRITE lock
`/home/tester/.local/state/family-connect-operations/.lock`.
Текст отказа соответствует fail-closed `connection_operation` в backend.py;
точная конкурирующая операция/thread и причина рассогласования diagnostics здесь
не установлены. Нельзя считать этот observation исправленным или объявить новый
build совместимым без отдельного source/regression checkpoint.

После STOP первая cleanup-only попытка также не дошла до authentication/TUN removal
за75s. Read-only проверка затем подтвердила освобождение operation lock. Ещё один
**только Disconnect**, без Connect/reconfiguration, прошёл настоящий polkit,
удалил owner/TUN/nft/routes/rules/DNS и восстановил network/IP baseline.
Ни locks, ни pending markers вручную не стирались; installed files не патчились.

## Server readback и остаточные процессы

Read-only registry/gateway baseline и сравнение после каждой из пяти сессий,
после first failure и final cleanup: PASS. Product-only idempotent nl fetches
сохранили прежний peer row/address/binding: ровно1 target DB/live AWG peer и
1 persisted/live Xray client. Total peers/clients46, без прироста.
Foreign DB/live bindings, global config, endpoints/server keys, catalog, network,
service invocation/PID hashes — unchanged. Deployment/restart/manual mutation нет.
Отдельный configuration fetch вне GUI connect не делался; ru assignment нет.

После normal configuration product оставляет `family-connect-auto@1000.service`
как idle catalog-host (`LinuxAuto.normal_catalog`), а не Auto VPN owner. Status IPC:
DISCONNECTED, desired_connected=false, generation empty, controller=null; child
transport processes отсутствуют. Это не L04.2/Auto connect и не hidden fallback.
Поэтому после product disconnect network baseline совпадал полностью, но один idle
host PID9296 оставался. Перед уничтожением VM fixture явно остановила **только этот
idle unit**; после этого весь snapshot, включая units/processes, совпал с baseline.
Не выдаём fixture stop за автоматическое завершение host самим продуктом.

## Сохранность и уничтожение guest

Финальный installed state readback: create=False, тот же Support ID/fingerprint,
cache только nl, signatures/floors PASS, pending control null,0600/0700 UID1000.
Все7 исходных home state files в guest остались byte-equal исходному набору;
GUI selection/settings пережили reopening. Cache SHA256 неизменен:
`d05447cea81d06e7d2a7266e70a53e5787b6ec9ff84c398b3be00e154f239049`.
Исходный protected home и private teardown receipt byte-equal pre-state.

Active AWG/TCP/MESH markers отсутствуют; sticky cleanup marker пуст/отсутствует;
reservation/transport locks свободны. Guest powered off25.10,13:26UTC; QEMU exited,
SSH forward закрыт. Encrypted overlay и ключ, guest SSH/password/seed, screenshots,
private logs и временные state copies уничтожены. Сохранено только sanitized evidence.
Рабочие host routes/DNS/services/connections не менялись.

Исходный `FC_L04_TEST_STATE=/var/tmp/fc-l04-test-20261025-6uva6jb3` остаётся0700,
secret files0600. Existing assignment намеренно сохранён. Будущий обязательный gate:
**device-scoped gateway cleanup → readback → registry revoke** — NOT_RUN, без
автоматического teardown/revoke и без передачи operator receipt в guest/Git.

## Evidence, проверки и ограничения

[Sanitized machine evidence](evidence/2026-10-25-l04-1-live-1.json), SHA256
`4f7a79093978db23e4bdfb86a236d89580d293ff79d76b090f21521ec9fde875`:
baseline/session inventories, route/rule/DNS/nft hashes/counts, bounded transfer
results, server binding hashes, first failure, cleanup и destruction receipts.
Private keys, WG key values, TCP UUID/email values, profiles, activation/invite,
bearer credentials и секретные URL не выводились и не включены в evidence/Git.
Это не полный аудит всех production server logs; такой PASS не заявляется.

Docs/evidence only: никаких product/harness changes или новых CI live credentials.
Content/15 added relative links, JSON parse, evidence SHA, staged allowlist6 files,
whitespace и secret scan PASS; raw WG/TCP/email binding matches0, secret-pattern
matches0. Параллельные ops STATUS/PLAN hunks и
`2026-10-24-vpn-health.md` сохраняются вне checkpoint. Remote input SHA проверен;
delivery commit/remote equality фиксируются в итоговом сообщении после push.

Full desktop pytest, Client Linux, isolated native/root→UID/Auto/DIRECT/package и
control/phase0/Docker suites не отключены и не перезапускались в docs-only live
checkpoint. Новый CI run/job ID отсутствует; прежний L03.2 CI не подменяет этот
exact-candidate live result. D01 открыт с54 residual failures; D02.1-R PARTIAL/NOT_RUN;
существующие Windows/voice observations не исправлялись и не скрывались.

NOT_RUN: LIVE-2 cancellation/late-result/tampered-build/negative gates; L04.2
MESH/Auto/P0/P1; L05 messenger; L06 network-change/sleep; L08 upgrade/cross-format
migration; gateway teardown/revoke; RU provisioning; new device/invite; public
release/catalog/landing/server policy/deployment/signing changes. Не переносить
полученные PASS между candidate/build IDs. Product correction — отдельная задача.

**STOP. NEXT — review L04.1-LIVE-1.**
