# Управляемый маршрут к Reticulum — 13.09.2026

Linux reference runtime автоматически создаёт и удаляет маршрут управления на время
`once --managed-route`. Живой Amsterdam-пилот принят без ручного ip rule: revision7
COMMITTED, GUI и bound HTTPS подтвердили186.246.45.246/NL, ACK доставлены. Повторная
доставка при активном VPN успешна без нового импорта. Это opt-in preview, не обновление
установленного desktop0.2.8 и не фоновый постоянный control service.

## Реализация и версии

Source: `7ad40c03eb66d34f4698dad1a5a7255cda08992e`.

- Bundle ID: `4d4afa762beddbaf69c414c00431fdca5301019a7976e19903babc397b62ec1e`.
- Архив SHA256: `fe799995022e6edfe0e6797c3cb2cb058958537d9bd3814b6c62d5bdd6801267`.
- Установленный helper SHA256: `bf9337321f5024653c6cdcc0608fe19874b9ab855b444ccef4703aae95a55039`.
- Постоянный архив: `state-client-build/control-previews/4d4afa762beddbaf/FamilyConnect-Control-Linux-preview-4d4afa762beddbaf.tar.gz` (ignored Git).
- Новый runtime: `provisioning/control_route.py`, явный флаг `--managed-route`.
- Helper: `/usr/local/lib/family-connect-control-route/helper`, root-owned0755.
- Root pin: `/etc/family-connect-control-route/pin.json`, root-owned0600.
- Polkit: `/usr/share/polkit-1/actions/org.familyconnect.control-route.policy`,
  active session auth_admin_keep; inactive/any=no. Системная авторизация остаётся.
- Runtime state: `/run/family-connect-control-route`, root0700, flock и durable intent.

Pin связывает SHA256 прежней trusted relay public identity с UID1000,
186.246.45.246:4242. Пользовательский процесс передаёт только digest provider;
helper не принимает адрес, порт, uid, shell text или файловые пути от клиента.
Единственный IPv4/TCP pin для одного пользователя — текущая поддерживаемая граница.

Helper добавляет uid-scoped policy rules10590/10591, до существующих TCP pilot rules:
lookup main и следующий prohibit для того же address/TCP port/uid. При отсутствии
обычного маршрута control не проваливается в VPN. Main lookup учитывает смену uplink
без сохранённого gateway/interface имени. Чужой занятый priority отклоняется.

Stdin pipe является временем жизни операции: EOF/закрытие/гибель пользователя
приводит к cleanup. Root helper ограничивает lease300с, обрабатывает SIGINT/SIGTERM;
клиент наблюдает завершение helper и отменяет carrier. Авторизация ограничена120с,
ожидание cleanup10с; таймаут cleanup не выдаётся за успех. При SIGKILL root helper
маркер остаётся, следующий запуск того же pin удаляет только точно совпадающие rules
и создаёт lease заново. Неизвестное/повреждённое состояние не сбрасывается.

GUI mutations остаются неблокирующими. Только вход control в общую transaction
ждёт краткую занятость до5с; уже начатые мутации не повторяются. Тесты отдельно
проверяют пересечение с коротким GUI poll и отказ при длительной занятости.
Другой pending journal не обходится.

## Проверки и ограничения доказательств

- Полный suite:478 passed,2 прежних deprecation warnings,9.97с.
- Реальный kernel в disposable namespace: EOF cleanup, exclusive broker,
  смена default route между двумя dummy uplinks, prohibit без uplink,
  SIGKILL root broker → recovery, сохранение чужого priority и исходных rules.
  Скрипт: `pilot/amsterdam/check_control_route.py` (root, сам создаёт net namespace).
- На компьютере SIGKILL только тестового user process подтвердил автоматическое
  удаление обоих rules root helper; VPN в этом тесте не включался.
- Реальный GTK/NetworkManager/RNS/HTTPS: штатный launcher принят на revision7,
  затем повторён при уже включённом VPN. После каждого once rules отсутствовали,
  после GUI disconnect/close baseline rules/default routes/DNS/active connections
  восстановлены, pending marker отсутствует.
- Сервер проверил подписи ACK: всего12, для revision7 — RECEIVED/APPLIED/COMMITTED.
- Две ранние попытки штатного launcher завершились до получения конфигурации,
  journal остался floor5/outbox0, сеть восстановлена. Generic OPERATION log не
  устанавливает точную причину. Отдельный helper/lease работал; diagnostic wrapper
  успешно применил revision6. После bounded contention fix штатный launcher прошёл
  revision7. Нельзя утверждать, что точная причина первых отказов доказана.
- Первый installer отказался использовать старый /etc/family-connect с mode0775.
  Выбран отдельный защищённый каталог; права прежних компонентов не менялись.

[Машинные результаты, включая предварительные отказы](2026-09-13-managed-control-route.json).
Смена маршрута проверена в namespace; физическое Wi-Fi/mobile handover, suspend/resume
и длительная нагрузка не приняты этим тестом. Истечение300с отдельно не выжидалось.

## Постоянное состояние и запуск

Сохранены прежние device identity, root signing anchor и journal.
Revision6: `b7b51e260b83de6fefea6d84805321ab3329e04a964415aa3ef34dce937eb3eb`.
Revision7: `a565a578bf00dea914d6241235ab0627e44d4fa3cef6d17c1f105717f768c4a7`; expires **2026-09-13T18:44:55+00:00**.
После expiry выпускать новую revision с правильным previous hash; state не сбрасывать.

Пути прежние: `state-enroll/control-linux-pilot/device`, `journal`,
`amsterdam-external/rns-client`, `amsterdam-external/trusted-relay.json`.
Локальные configuration6/7 и envelopes сохранены в том же приватном каталоге.
На relay переданы только публичная привязка и ciphertext; signing key не покидал компьютер.

Установщик `scripts/install_control_route.py` запускается root из проверенного preview
с явными --provider-public, --address, --port, --uid и --helper-sha256. Он не скачивает
identity, не меняет маршруты и отказывается заменять отличающиеся установленные файлы.
После установки к прежней команде paired runtime once добавляется `--managed-route`.
Старый GUI0.2.8 при control не запускать: он не соблюдает общий arbiter.

Финальное состояние: VPN выключен; journalIDLE/floor7/committed7/outbox0; rules10590,
10591 и прежнего ручного10990 нет. Helper/pin/policy установлены для следующих запусков,
постоянный route/daemon не создан. Amsterdam relay/WG продолжают работать; их код и
настройки на этом шаге не менялись, опубликованы лишь новые signed configurations.
Установленный current всё ещё `0.2.8-766194f6f3df-9c6f2e52a84f`.
Release/catalog/main не менялись.

## Следующий шаг и возврат

Далее — оценка совместимости AWG3.1 и отдельный Amsterdam-пилот с сохранением рабочего
WG. Пока transport_version3.1 по-прежнему отклоняется, эта сессия его не включала.
GUI release, native protected state Windows/Android, независимый резервный relay,
physical handover/suspend и долговременная стабильность остаются отдельными задачами.

Возврат: завершить текущий once, дождаться cleanup и отключить VPN. Если root broker
был убит, повторный запуск с тем же pin сначала выполняет recovery; не удалять intent
и не освобождать priority вслепую. Для полного удаления helper сначала убедиться,
что нет активной lease/pending intent/rules, затем удалить только новые helper/pin/
Polkit files. Сохранить device/journal и committed configuration. Без установленного
helper `--managed-route` должен завершаться ошибкой; старый ручной pilot не становится
автоматически безопасным от отсутствия маршрута.

## CI и Docker test-stage correction

На исходном7ad40c0 phase0 tests прошли, failover остановился на Docker build.
API подробного журнала вернул403. В Dockerfile.control отсутствовал COPY нового
clients/linux/control-route-helper.py, уже необходимого package/security tests.
Исправление0136c54bf92fd464db362e6dd6ea32e7a1ee0888 добавляет его только в tests stage.
Локальная Docker-сборка отдельного тега family-connect-control:managed-route-check
успешна:341 tests/2 warnings/18.36с внутри Python3.13 image (подмножество полного suite).
Bundle/runtime/helper bytes от Dockerfile correction не меняются.

- [Linux control preview34758085278](https://github.com/Joker20380/family_connect/actions/runs/34758085278): success, job103725875226.
  CI notice подтвердил точное совпадение SHA256 локально принятого архива.
- [phase0 повтор34758354244](https://github.com/Joker20380/family_connect/actions/runs/34758354244):
  tests103726596471 и failover103726596332 success на0136c54.
- [AWG pilot34758085231](https://github.com/Joker20380/family_connect/actions/runs/34758085231)
  и [TCP pilot34758085230](https://github.com/Joker20380/family_connect/actions/runs/34758085230): success на7ad40c0.
- [Client builds34758085225](https://github.com/Joker20380/family_connect/actions/runs/34758085225):
  Linux103725875148 и Windows103725875164 success; Android103725874969 ещё in_progress
  на момент записи. Это не full platform release acceptance; публикация не выполнялась.

Начальная [сверка AWG3.1](../awg31-migration.ru.md) сохранена отдельным документом.
