# Linux GUI/control preview — план ручного пилота

**CI health исправления принят:** Linux source d7c3d79; последующие native Clients/Android source9092594 прошли. Исходный Android failure сохранён. [Точные результаты](releases/2026-09-13-linux-control-ci.ru.md).

**Последний результат:** исправленный bundle66152538ee2a4f3e прошёл живой Linux
пилот config2/3 с MTU1280, crash/recover, ACK и GUI Disconnect/close.
[Точное состояние и границы](releases/2026-09-13-linux-control-pilot-pass.ru.md).
Remote CI correction ещё открыта; старый bundle ниже сохраняется как историческая запись.

**Обновление13.09:** живой пилот выявил active-only health для standalone WG.
Прежний принятый bundle не использовать для нового live apply. Исправленный bundle
66152538ee2a4f3e прошёл412 локальных тестов; network/crash acceptance ещё открыта.
См. [живой результат и текущее состояние](releases/2026-09-13-linux-control-live.ru.md).

Приёмка исходника: `247d16b` в ветке `stage5-linux-control-preview`.
Это отдельный operator preview, не stable update. Установка по этому документу
не переключает `~/.local/share/family-connect/current` и не публикует каталог.

## Зафиксированный комплект

- `FamilyConnect-Control-Linux-preview-bc908a5f084a8bb6.tar.gz`
- SHA256: `390ba9ff24c11ba63ac7b48ec0d7d89a5c623563401a90d25c25d55b81620797`
- Локальный проверенный файл: `/tmp/fc-accepted-preview/FamilyConnect-Control-Linux-preview-bc908a5f084a8bb6.tar.gz`.
- Сверить этот hash с CI notice `Control preview SHA256` для принятого commit.
  Hash/manifest не заменяет подпись конфигурации; не получать bundle из непроверенного источника.

Наблюдение 13.09.2026: установленный APP_VERSION — **0.2.8**, current указывает
на `releases/0.2.8-766194f6f3df-9c6f2e52a84f`; previous —
`releases/0.2.7-45f916de8268-b54a388d2ea3`. Оба backend без operation arbiter.
Прежняя запись STATUS об установленной0.2.7 устарела; на этом шаге установка не менялась.

## Перед пилотом

Закрыть установленный GUI0.2.8 и исключить ручные NetworkManager/root изменения VPN
на время control-транзакции. Новый GUI и control запускать одним пользователем.
Не запускать `install-linux.sh` из preview: он устанавливает только legacy GUI,
тогда как пилоту нужен paired bundle. Существующие VPN helpers остаются прежними.

Для реальной доставки заранее нужны зарегистрированная device identity, явный
RNS client config, проверенный public identity relay и подписанный envelope для
этого устройства. Relay не создаёт gateway peer; его существование проверяется
отдельно. Секретный ключ подписания остаётся офлайн. Не подменять проверенный anchor
и не использовать одноразовую test identity как production registration.
Ниже показана подготовка каталога; команды не выполнены этой приёмкой:

```sh
preview_parent="$HOME/.local/share/family-connect/control-previews/bc908a5f084a8bb6"
install -d -m 700 "$preview_parent"
# Только для нового пустого preview_parent; не распаковывать поверх прежнего комплекта.
tar -xzf /tmp/fc-accepted-preview/FamilyConnect-Control-Linux-preview-bc908a5f084a8bb6.tar.gz -C "$preview_parent"
preview="$preview_parent/FamilyConnect-Control-preview"
python3 -m venv "$preview_parent/venv"
"$preview_parent/venv/bin/pip" install -r "$preview/provisioning/requirements.lock"
/usr/bin/python3 "$preview/scripts/run_control_preview.py" verify
/usr/bin/python3 "$preview/scripts/run_control_preview.py" gui
```

GTK берётся из системного Python. Cairo/GTK_A11Y environment overrides для CI не
переносить в рабочий запуск. Постоянные identity/journal/RNS config хранить отдельно
от версии bundle. Использовать точные прежние пути при каждом запуске.

Инициализация и выдача подписанной конфигурации — по [control runbook](reticulum-control.ru.md).
У launcher синтаксис: `venv/bin/python scripts/run_control_preview.py control once ...`.
Команда `once` вправе применить полученную конфигурацию и изменить VPN; она не является
read-only smoke. Здесь реальные profile apply/network acceptance не выполнялись.

## Выход из preview и восстановление

Остановить `once`, закрыть preview GUI и дождаться завершения процессов. Если
есть pending operation, выполнить **recover** тем же пользователем, с теми же
identity, anchor и journal (переменные ниже — заранее выбранные абсолютные пути):

```sh
"$preview_parent/venv/bin/python" "$preview/scripts/run_control_preview.py" control recover \
  --state "$control_state" --identity "$device_identity" \
  --anchor "$preview/clients/desktop/update.pub"
```

`recover` не запускает carrier, не запрашивает новую конфигурацию, не отправляет ACK.
Ожидающие ACK сохраняются для следующего control-сеанса.

- `IDLE` / `ROLLED_BACK`, exit0: pending завершён, можно вернуться к установленному GUI0.2.8.
- `FAILED`, exit1: rollback не завершён; не открывать старый GUI. Исправить причину
  восстановления существующего VPN backend и повторить тот же recover.
- Ошибка чтения/подписи/прав: fail closed, не удалять journal или operation marker.

Возврат GUI не понижает committed configuration sequence. Уже committed VPN config
сохраняется; возврат к прежнему содержимому требует отдельной корректно подписанной
конфигурации с возрастающей revision. Нельзя восстанавливать старый journal из backup
для обхода anti-replay. Даже при удалении preview bundle сохранять identity/journal/outbox.

## Критерий пилота и границы

Автоматизированно проверены распакованные GUI recovery, process/thread arbitration,
crash→rollback, идемпотентность, подписи/sequence и реальный RNS loopback. Apply/health
в этих сценариях моделируются через существующую backend boundary. Реальная совместная
работа на VPN-профиле устройства — следующий отдельный пилот, не результат этого CI.
Stage6 independent entry/alternate gateway, AWG3.1 и длительные/device тесты не закрыты.
