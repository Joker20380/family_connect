# Внешний Reticulum pilot — 13.09.2026

Принята реальная цепочка: внешний RNS/TCP relay → подпись/recipient/revision →
Linux backend apply → HTTPS через Amsterdam → paired GTK → подписанные ACK на relay.
Приёмка требует отдельного операторского маршрута к relay; автоматический lifecycle
этого маршрута в приложении пока не реализован. Это основной следующий шаг.

## Развёртывание и доверие

- VPS: `186.246.45.246`, Ubuntu26.04/Python3.14.4, 1CPU/955MiB.
- Relay: `/opt/apps/family_connect/reticulum`, служба
  `family-connect-reticulum.service`, active/running/enabled, TCP4242.
- Пользователь `fc-relay`; root-owned app/venv, приватный state0700 пользователя службы.
- systemd: NoNewPrivileges, ProtectSystem=strict, ProtectHome, PrivateTmp,
  PrivateDevices, ReadWritePaths только state, MemoryMax256M, TasksMax64.
- RNS1.5.1 и остальные зависимости установлены по принятому requirements.lock.
  Установка python3-venv также обновила Python3.14 Ubuntu packages как зависимости.
  Полного обновления ОС и reboot не выполнялось.
- Архив preview SHA256: `9c827f86f03d27705c46830758e114b3f7ef9796320d9e46f09672363de076f3`.
  Runtime manifest: `66152538ee2a4f3ec4ac76cb2a0e09936bcc0785fc5afa308b692c3cd472acf5`.
  Launcher проверяет manifest перед запуском; product source base этой сессии `6d0de83`.
- RNS config: share_instance=No, enable_transport=No, явный TCPServerInterface
  0.0.0.0:4242. Relay является endpoint приложения, mesh forwarding не включён.
- Permanent transport identity создана на сервере. Public reference:
  `e504e0ef76a2b3bcc3f0c5add0760ff3`.
- Public identity закреплена через ранее проверенный SSH host key, не через discovery:
  `vKri/FwEyJe/AoepLwYxN/T64cqzwVft+HxMCMDcmV8DcTOoLqnoHVjpThpwhvU2eSO+OoMTEg90lUs3VCOV8A==`.
- SSH fingerprint: `SHA256:TA7zrfD44kXhvR1k2aW8JHNtWIuLFfP8m6yxzV6+drk`.
  Offline Ed25519 signing key остался на компьютере, на relay переданы public binding
  и ciphertext. Relay identity не заменяет signing anchor.

Первый deploy остановился до создания relay DB/service и изменения WG peer:
каталог reticulum получил0700 из-за umask077, служебный пользователь не мог пройти.
Права публичного корня исправлены на0755; приватный state сохранил0700. Установка
продолжена с места остановки, зависимости и identity не пересоздавались.

## Устройство и последовательность

Сохранена существующая identity `71a05310177fa445bbe95b2405e650ba`, прежние
RNS/device keys и journal. До начала: phaseIDLE, floor3, committed revision2,
outbox0. Binding proof проверен локально и сохранён в приватном state.

На fcams добавлен второй peer с существующим публичным WG ключом этого устройства:
`10.79.0.3/32`, `fd79:92::3/128`. Ручной Amsterdam peer .2 сохранён.
Изменение выполнено wg set без перезапуска WG и записано в fcams.conf для reboot.
Приватный preimage конфигурации сервера сохранён в reticulum/fcams-before-control.conf.
Это операторская регистрация в отдельном ControlRelay, не обновление entitlement/lease
в старом product API. Старый gateway/API и его DB не изменялись.

Revision4: `78f6cbf5ee4c66f6cc73e4f4b3e5279ee193d98578b6e10fd4499f75b1e7ada5`, previous hash — committed revision2.
Revision5: `4048c1d5062a684b1c1ef29c4bc1291432bb08d1322e4cea9effe54e5800416d`, previous hash — revision4.
Обе конфигурации имеют шестичасовой lease; revision5 истекает **2026-09-13T18:18:00+00:00**.
После истечения нужна новая подпись/revision; переинициализировать journal нельзя.

Постоянные локальные пути, вне Git:

- `state-enroll/control-linux-pilot/device` — прежние ключи.
- `state-enroll/control-linux-pilot/journal` — прежний журнал, теперь floor5/committed5.
- `state-enroll/control-linux-pilot/amsterdam-external/rns-client` — внешний TCP client.
- `.../amsterdam-external/trusted-relay.json` — проверенный public bootstrap.
- `.../amsterdam-external/configuration-4.envelope` и `configuration-5.envelope`.

## Проверки, выявленный сбой и исправление пилота

Revision4 получена через внешнюю сеть и COMMITTED; GUI показал IP186.246.45.246/NL,
interface-bound HTTPS подтвердил IP. После включения полного VPN TCP к тому же серверу
терял доступ по внешнему пути: ACK оставались в outbox3, второй once завершился exit1.
Внешний relay и WG здесь на одном VPS; firewall fcams запрещает такой вход к host
кроме ICMP. Смена full-tunnel маршрутизации требует явного сохранения control path.
Детальный packet trace первоначального сбоя не снимался.

Попытка выразить исключение IP через AllowedIPs была отвергнута строгим parser,
требующим ровно полные IPv4/IPv6 routes. Неподдерживаемая конфигурация не подписана
и не опубликована. Формат/проверки продукта не ослаблялись. Итоговая revision5
использует прежние полные маршруты.

Для пилота применён root-owned временный policy rule:

```sh
ip -4 rule add priority 10990 to 186.246.45.246/32 ipproto tcp dport 4242 lookup main
```

Он относится только к TCP4242 указанного relay, не к остальному интернету или SSH.
Проверен route get при активном VPN: relay использовал wlp0s20f3/main, HTTPS — VPN.
[Точный проверенный operator helper](../../pilot/amsterdam/reticulum_route.py)
принимает up/down, отказывается занимать существующий priority10990, сохраняет
исходные rules в /run, удаляет только своё правило и сравнивает исходное состояние.
Запускать с root/pkexec только в согласованном пилоте без параллельных routing changes.
На время apply держать правило активным; затем отключить VPN и выполнить down.
Не устанавливать этот скрипт как произвольный privileged GUI helper.

После добавления правила:

1. Все три отложенных ACK revision4 доставлены без сброса outbox.
2. Revision5 verified/staged/applied/committed, три ACK доставлены; outbox0.
3. GTK показывает Tunnel is on и IP186.246.45.246/NL, отдельный bound HTTPS проходит.
4. Повторный once на активном VPN возвращает COMMITTED без нового profile UUID
   и изменения GUI operation generation; outbox0.
5. GUI disconnect/close: rules/default routes/resolver/active connections совпадают
   с baseline этого запуска, pending marker отсутствует.
6. Временное правило удалено; исходные policy rules восстановлены.
7. Перезапуск только relay сохраняет public identity, обе конфигурации и шесть ACK.
   Подписи всех ACK проверены на сервере. После restart duplicate once при выключенном
   VPN возвращает COMMITTED, не включает VPN и не меняет содержимое relay DB.

После restart: MemoryCurrent33501184 bytes (~32MiB), VM available717MiB;
NRestarts0 — автоматических аварийных перезапусков в этом измерении нет.
Это не нагрузочный/длительный тест. [Машинные данные](2026-09-13-external-reticulum.json).

Код продукта и schema не менялись. Сохранён точный проверенный operator route helper,
syntax compile и git diff --check пройдены; полный pytest не повторялся.
Ранее462 tests относятся к предыдущей Python приёмке, не к новой серверной установке.
GUI — настоящее GTK-окно с программной отправкой сигналов кнопкам, не ручной UX-тест.

## Финальное состояние, следующий шаг и rollback

Relay и WG работают с автозапуском, клиент VPN выключен; временных routing rules нет.
JournalIDLE, floor5/committed5, outbox0. Новые NM profiles inactive/autoconnect=no.
Установленный Linux остаётся0.2.8; preview запускался отдельно. Release/catalog/main
не менялись. Старый GUI0.2.8 не участвует в arbiter и должен быть закрыт при control once.

Следующий шаг: реализовать управляемый lifecycle маршрута к trusted relay в Linux
runtime/helper, с безопасным восстановлением после сбоя, сменой сети и совместной
ownership с GUI. Затем повторить эту цепочку без ручного operator rule. Самостоятельная
работа control при уже активном full VPN без такого правила пока не принята.
Не выдавать текущий pilot за готовое обновление установленного приложения.

Relay и gateway размещены на одном VPS: независимость инфраструктуры/провайдера,
резервный entry, TCP/AWG transport failover, Windows/Android protected state,
sleep/handover/длительная стабильность ещё не закрыты. RNS TCP4242 — control carrier,
не TCP VPN fallback. Stage5/6 целиком не закрыты.

Остановка rollout: systemctl disable --now family-connect-reticulum.service.
Сохранить state/identity/relay DB, ciphertext и client journal. Не сбрасывать floor.
При удалении второго WG peer удалить только ключ устройства .3 через wg set и
соответствующую секцию fcams.conf после проверки актуального preimage; не восстанавливать
старый backup вслепую и не затрагивать peer .2. Firewall в этом этапе не менялся.
Client: сначала завершить pending recovery тем же journal (сейчас pending отсутствует),
отключить VPN, удалить только своё временное правило через helper down, если оно есть.
Не удалять committed profiles/state ради сброса anti-replay.
