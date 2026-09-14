# Git checkpoint и Android runtime acceptance — 2026-09-14

По запросу пользователя357 накопленных изменённых/новых файлов сохранены в af46e87
и отправлены в origin/main. Состояние state-каталогов, private keys и локальные
сборки исключены. Это source checkpoint, не release. Android versionCode3,
versionName0.1.2-beta03; signing root, серверы и установленные приложения не менялись.

## Первый CI

[Client builds34828757268](https://github.com/Joker20380/family_connect/actions/runs/34828757268):
Windows и Linux success. Android assembleDebug, unit tests, lint и APK verifier прошли.
На эмуляторе выполнено7 instrumentation cases; AutoRuntimeTest упал на ProfileStore.clear
в cleanup с «Disconnect VPN before changing profiles». В сценарии также обнаружена
попытка wg.save при активной AWG-сессии, несовместимая с новым operation owner.

Исправление: проверять отказ изменения профиля при активной сессии, восстанавливать
WG после OS revoke/off; finally вызывает disconnect и ждёт cleanup до удаления
профилей. Защита production-кода не ослаблена.

Linux control preview34828757187 и Windows control conformance34828757193 success.
Phase0 tests success, failover34828757212 failed на Docker build. Test stage не включал
новый Android Python carrier, который импортируют реальные RNS тесты; COPY добавлен
только в tests stage. Локальный docker build --target tests прошёл353 tests/27.00s.
Это ещё не проверка всех failover-сценариев в CI.

## Усиление приёмки

verify-apk.py проверяет Reticulum/PySerial/Chaquopy лицензии, точные байты pinned
bootstrap, fc_rns_transport.pyc, RNS/serial в requirements и libpython3.10.so всех4 ABI.
report_control_ci.py требует успешного ControlRnsRuntimeTest наряду с protocol corpus
и strict JSON. Подключён также в diagnostic workflow. Локальная проверка отчёта:
success принимается; missing/skipped RNS test отвергаются. Python syntax и diff checks
прошли. У исходного patch-файла есть контекстные строки с одним пробелом: они сохранены
как корректный unified diff; остальные исходники прошли whitespace check.

Повторный CI исправлений на момент подготовки отчёта ожидается. Next: подтвердить
все Android instrumentation cases и APK gates, затем тестовый Android enrollment,
выдачу signed envelope под его ключ, receive/apply/health/ACK и offline/reconnect.
Live control exchange на Android пока не заявлен. Django/payment plane остаётся
следующим продуктовым этапом после VPN acceptance.

Rollback: revert коммита с исправлениями при необходимости; не удалять app data,
identity и ACK outbox. Отмена общего checkpoint возвращает прежний source baseline,
но не откатывает ранее установленные APK/серверы. Release/downgrade требует отдельной
проверки совместимости состояния и anti-rollback.
