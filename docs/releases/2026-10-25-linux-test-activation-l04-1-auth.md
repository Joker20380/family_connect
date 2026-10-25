# L04.1-AUTH — отдельная test identity и штатная activation

25.10.2026. **BLOCKED: activation PASS, device AWG/TCP assignment NOT_RUN**.
Причина теперь не отсутствие operator credentials: штатный configuration fetch
добавляет gateway AWG peer и меняет Xray configuration. При явном запрете таких
изменений он не вызван. Полный критерий AUTH DONE не выполнен.

Вход `main`/remote: `fbb1732567ed4e1d33c934b0b88b04d5d30f21e6`, принятый
[предыдущий BLOCKED checkpoint](2026-10-25-linux-installed-awg-tcp-l04-1.md).
L03.1/L03.2/parent L03 DONE; L04 IN_PROGRESS; L04.1 BLOCKED/live NOT_RUN;
L04.2 QUEUED/NOT_RUN, L05 не начат. Личные identities не использовались.

## Единственная новая identity

| Поле | Sanitized readback |
|---|---|
| Support ID | **FC-3YSQ-BE2D** |
| Registry device ID | `d07d33a81728ff70aec350ae59785990` |
| SHA256 публичной identity | `d07d33a81728ff70aec350ae59785990c194d90ecd44574b0da28439189532de` |
| Activation | active; одна issued invitation привязана к одному device |
| Registry flags | registered=true, active=true, device/invite revoked=false |
| Entitlement | обычная activated FAMILY eligibility, не отдельный AWG/TCP-only tier |
| Entitlement expiry | отсутствует в штатной legacy activation модели |
| Device-specific AWG/TCP assignment | NOT_RUN; cache отсутствует |
| State owner / modes | UID:GID1000:1000; все каталоги0700, все файлы0600 |

Создание — `load_friends_identity(..., create=True)` / `DeviceIdentity.generate`
из извлечённого exact final-2. Один постоянный новый RNS/signing identity и его
WG key; не импорт, не historical pilot, не synthetic activation/profile. После
создания используется только `create=False`; второй identity не создавался.

## Фактический workflow

Изучены [deployment runbook](../../deploy/friends/README.md),
[activation design](../design/activation-simplification-design.ru.md),
[activated entitlement](../../deploy/friends/restricted/ACTIVATED_ACCESS_V2.md),
`control/friends/access.py`, desktop `FriendsOwner`, `FriendsClient`,
`FriendsConfigurationStore`, `friends_catalog` и фактический deployed code.
Не использован first-install-only `install-access.py` или другой product registry.

Operator SSH к разрешённому RU доступен. Старый
`family-connect-friends-access.service` inactive; фактический
`family-connect-friends-http-candidate.service` active, слушает loopback18086.
Его running archive и `ROOT` проверены до записи. Активный HTTP handler использует
`/opt/apps/family_connect/friends-access/access.db`; никакой deployment/restart.

Ровно один вызов **существующего `Access.invite()` из running archive**, не новая
схема/ручной INSERT. Перед ним создан exclusive operation intent; повторное
создание operation directory отказывает, не выдаёт второй код. Код записан только
в root0700/0600 operator checkpoint и передан SCP в локальный0700/0600 state,
не stdout, arguments или отчёт. При неизвестном исходе issuance нельзя повторять:
сначала readback существующего operation, без нового invite.

`FriendsClient.activate()` выполнил штатные HTTPS challenge/proof/activate с
обычной проверкой TLS, затем `device_status()` подтвердил active. Registry readback
через SQLite `mode=ro` подтвердил публичный fingerprint, exact issued invite binding,
одну связанную invitation и Support ID. Старые registry записи не использовались.
Изменены только штатные device/invite/challenge/support accounting этой активации
и приватные operator checkpoint files; DB/schema/policy migrations отсутствуют.

Повтор того же activation proof отвергнут (403/access_rejected). Новый challenge
с уже использованным кодом и незарегистрированным **public-only negative input**
также403; для этого не создавались private keys/второе устройство. Registry
подтвердил отсутствие устройства negative probe. Это не требование сломать
штатную идемпотентность: fresh recovery уже активного того же device может вернуть
active без новой activation; она не считается вторым расходованием кода.

Support refresh использует ровно metadata существующего GUI: `linux-0.2.11`,2011.
Это source version, не переименование internal candidate0.2.12~l03.2.1.
Действующая policy v2 `all_activated` не изменена: обычная activated FAMILY
eligibility не означает READY restricted credential, P1 grant или VPN session.
Для нового device `restricted_grants=0`, `restricted_certificates=0`.
Legacy signed catalog имеет собственный `invite-test` contract, не новый tier.

## Проверки без установки и VPN

- Exact final-2 AppImage/DEB SHA256 повторно совпали с accepted pair. Candidate
  `9d4b13cc106296264805402b42538b9fa94505433b1bbd239c82145966e22b81`, product
  source `cf66532c72548767f8ff4aa31faa7588b07eab54`, embedded exact build-9;
  никто не пересобран/изменён. DEB только извлечён, не установлен.
- Code/member hashes проверены до вызова packaged identity/provisioning modules.
  Первичное создание/activation — отдельные pinned operator dependencies на
  Python3.14.4; финальный resume/status дополнительно проверен на **Python3.12.3**
  с **vendor exact final-2**, `-I -S`, без dev site-packages. Fingerprint/WG binding
  совпадают, `create=False`, authenticated active readback PASS после нового процесса.
- Python3.12 executable/stdlib взяты из прежнего Ubuntu24.04 image и выполнены
  как обычный host UID вне checkout. Контейнер был только created/stopped для
  чтения публичного runtime и удалён; **state в контейнер/VM не передавался**.
- Общее подписанное `catalog.json` прочитано operator read-only в приватный файл.
  Packaged `verify_catalog` проверил signature неизменным packaged `update.pub`,
  sequence/hash consistency и повтор с тем же floor/hash. **PASS**, без записи
  пользовательского floor и без получения device address/credentials.
- Публичная подпись общего каталога **не доказывает device assignment**.
  `friends.configuration.json` отсутствует. Missing legacy `gateway_id` не
  заполнялся, wire schema не менялась, entitlement не назван applied session.
- Все private paths проверены: owner1000, без symlink/hardlink/special files,
  каталоги0700/файлы0600. Remote operator checkpoint root0700/0600. Revoke flags
  прочитаны, но устройство не отозвано и не истекает по legacy entitlement timer.

## First-failure boundary: fetch меняет gateway

Клиент **умеет отделить fetch от apply**: `FriendsOwner.configuration(country)`
и `FriendsClient.configuration()` не вызывают VPN driver. Но deployed HTTP handler
`/friends/configuration/{ru,nl}` после проверки proof вызывает gateway `register`.
Проверенный реальный `awg-gateway.py` выполняет `awg set ... peer`, создаёт peer
accounting, а `tcp_user()` дописывает client в `friends-tcp/server.json` через
atomic replace и вызывает Xray API. Для новой identity это не read-only fetch.

Поэтому configuration endpoint **не вызывался**. RU peer readback для нового WG
public key:0. Никакие gateway settings/configurations, services, signed floors,
catalogs, issuer/anchors, global entitlement policy или VPS не менялись.
Не выдавались raw profiles/вымышленные assignment, не добавлен dry-run protocol.

Для закрытия AUTH требуется разрешить именно **штатную per-device регистрацию
AWG peer + Xray user, включая её запись server.json**, через существующий
configuration fetch. После такого разрешения один fetch выбранной страны и
packaged cryptographic/cache readback должны подтвердить оба transport assignments
без `connect`/apply. **Новый invite или identity не нужны.** Это иной блокер, чем
недоступный operator issuance; команды создания ещё одного устройства не требуются.

## Защищённый handoff

```sh
export FC_L04_TEST_STATE=/var/tmp/fc-l04-test-20261025-6uva6jb3
sh "$FC_L04_TEST_STATE/operator/preflight.sh"
```

Это локальный read-only preflight обычного UID1000, не новый product IPC.
Он проверяет modes/owner, pinned artifact inventory, identity fingerprint,
`create=False` и signed common catalog; выводит только sanitized результаты.
Helper/data/scripts внутри state0600; не коммитить и не загружать в CI.
Pinned tooling находится в `/var/tmp/fc-l041-auth-tools.VoJNFboc`; его также
сохранить до handoff. `/var/tmp` — локальный ext4, вне checkout и sync-каталогов,
но не бессрочный backup: не запускать очистку этих двух каталогов до review.

Настоящий GUI identity root определяется кодом, **не только XDG**:
`$HOME/.local/share/family-connect/friends-identity`. В новом state это
`$FC_L04_TEST_STATE/home/.local/share/family-connect/friends-identity`.
При последующем разрешённом переносе передавать **только `home/`** в выделенный
guest HOME обычного UID, с проверкой owner/modes и fingerprint **до GUI запуска**.
Указать там HOME и согласованные XDG_CONFIG_HOME/XDG_DATA_HOME/XDG_STATE_HOME;
одного XDG override без HOME недостаточно. `operator/` с использованным invite
не нужен гостю, не экспортируется. Сейчас никакого переноса не было.

Путь передаётся environment/CLI как non-secret metadata; содержимое — только
защищённым file transfer/mount, не argv, shell variables с credentials, trace,
CI logs/artifacts или отчёт. Preflight выключает shell trace. Не печатать state,
не включать `set -x`, не применять `create=True` при отсутствии/повреждении ключа.
Потеря файла означает recovery этого state, не новую identity/activation.

## Отзыв и границы завершения

Операторский revoke target однозначен: device ID и Support ID выше; ровно одна
invitation связана с ним. Существующие `devices.revoked`/`invites.revoked` поля и
проверки deployed Access определяют отказ дальнейшей авторизации. Read-only lookup
PASS; **revoke не выполнен**. После будущего provisioning необходимо отдельно
завершить device-scoped gateway cleanup: registry revoke не равен удалению ранее
выданного cached AWG/TCP доступа и не обещает завершить активный VPN. В этом
checkpoint profiles/peer assignment не выдавались.

NOT_RUN: device configuration fetch/assignment, применение, установка final-2,
pkexec setup, TUN/routes/DNS, AWG/TCP connect, VPN HTTPS/transfers, L04.1 live,
MESH/Telemost/L04.2/L05, импорт в VM/контейнер, revoke, publication. No new CI gate:
изменяются только docs; обязательные source/package/full suites не отключены.
D01/54 residual failures, D02.1-R PARTIAL/NOT_RUN, Windows/voice сохранены.

Приватные state/evidence/операторские scripts остаются вне Git; staged scope —
только sanitized docs. Parallel ops STATUS/PLAN hunks и VPN health report не
включаются. Source push не является установкой, публикацией или live acceptance.
Перед commit: content/local links и `git diff --check` PASS; staged five-doc
allowlist проверен. Exact новые private-key bytes/hex/base64 и invite проверены
без вывода значений по staged diff и patch history всех локальных refs: совпадений
нет. Это проверка утечки новых test secrets, не аудит всех исторических секретов.

**STOP. NEXT — review L04.1-AUTH**, включая gateway mutation boundary. Только после
review — отдельно разрешённое возобновление исходного L04.1 на exact final-2 с
этим защищённым state; L04.1 пока BLOCKED/live NOT_RUN.
