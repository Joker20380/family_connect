# Приёмка paired Linux GUI/control preview — 13.09.2026

## Результат

Preview принят на уровне автоматизированного protocol/application и packaging
тестирования. Комплект подготовлен для отдельного ручного пилота рядом с текущей
установкой. Пилот на реальном VPN-профиле, установка и новый release не выполнялись.
[Конкретный план запуска и возврата](../linux-control-preview-rollout.ru.md).

Stage 5 implements verified Reticulum-based configuration delivery and transactional apply/ACK/rollback.

This does not yet prove recovery from loss/blocking of the only known infrastructure endpoint. Independent control entry and alternate gateway remain Stage 6.

## Изменения и обнаруженные ограничения

Package acceptance теперь выполняет весь test_control_channel и process/thread
operation arbiter tests на **распакованных модулях**, вне исходного checkout.
CI отдельно запускает GTK recovery harness с импортом распакованного app/backend,
а также публикует digest готового tar.gz в check annotation.

Для однозначного выхода из preview добавлен `control recover`. Команда использует
существующий core.recover и Linux BackendApplication: блокирует GUI через общий
арбитр, восстанавливает pending транзакцию, сохраняет outbox и возвращается без
запуска Reticulum/получения нового envelope. IDLE/ROLLED_BACK дают exit0, FAILED —
exit1 с сохранением pending. Повторный recover безопасен. Это не откат committed
sequence: committed config и anti-replay floor не сбрасываются.

Расширенные package tests потребовали двух test fixtures в Docker tests stage.
COPY conftest.py/test_operations.py добавлен явно; runtime image не расширен.
Промежуточный phase034722755841 failed до этого дополнения; итоговая приёмка —
исправленный run34722963403. Тесты не отключались.

Обнаружено расхождение старой документации с машиной: current APP_VERSION0.2.8,
previous0.2.7. Symlink current — releases/0.2.8-766194f6f3df-9c6f2e52a84f,
previous — releases/0.2.7-45f916de8268-b54a388d2ea3. Backend обеих версий не содержит
нового арбитра. Значения прочитаны без изменения установки или профилей.

## Evidence

- Local Python: **409 passed**, 2 прежних FastAPI/Starlette warnings.
- Вложенная suite распакованного комплекта: **66 сценариев**, actual two-process
  RNS loopback, подписи/replay/target/lease, commit/rollback/ACK, failure/crash,
  повторная доставка, GUI pending ownership, CLI recovery без carrier, failed
  recovery exit1. Backend apply/health здесь моделируются; привилегированных VPN
  операций нет. Одноразовые fixture keys не входят в artifact/repository.
- Package wrapper:3 passed, включая integrity refusal, allowlist, pins и init-client.
- GTK recovery на extracted app/backend: exit0, stale selection, generation change,
  suppression старого recovery, explicit disconnect и close. Portal teardown
  warnings не нарушили assertions.
- Docker build: **272 passed**, runtime собран; image ID5eade918b8f8 совпал с
  предыдущим runtime. Tests stage содержит дополнительные fixtures, runtime — нет.
- [Scoped Linux34722755860](https://github.com/Joker20380/family_connect/actions/runs/34722755860)
  на `247d16b`: success, включая409 Python, layouts/interactions, fresh pinned venv,
  extracted CLI/GUI и GTK recovery.
- [Phase034722963403](https://github.com/Joker20380/family_connect/actions/runs/34722963403)
  на `3a28be7`: success, tests + failover jobs, включая build/provision/auth/offline/
  revocation/cleanup. Изменение3a28be7 добавляет только Docker test fixtures.
- Предыдущие [Clients34720569537](https://github.com/Joker20380/family_connect/actions/runs/34720569537):
  Windows, Linux, Android success, release skipped. Native application sources
  этого шага не менялись; это не native Stage5 binding acceptance.

Sandbox loopback/D-Bus ограничения потребовали разрешённого запуска локальных
тестов вне sandbox. Непривилегированные/привилегированные VPN helpers не запускались.

## Artifact

`FamilyConnect-Control-Linux-preview-bc908a5f084a8bb6.tar.gz`

SHA256 `390ba9ff24c11ba63ac7b48ec0d7d89a5c623563401a90d25c25d55b81620797`.

Локальный архив и CI check annotation `Control preview SHA256` совпадают.
Внутренний manifest проверяется launcher до запуска. Архив из GitHub artifact
не скачивался: сравнение выполнено с digest непосредственно собранного CI tar.gz,
полученным через официальный check annotations API. Manifest/digest не является
новой PKI; источник сборки доверенный, configuration trust остаётся offline anchor.

## Границы и следующий шаг

Подготовлен ручной пилот в отдельном каталоге, без переключения stable current.
Старый GUI0.2.8 должен быть закрыт на время пилота: он не соблюдает новый arbiter.
Для реального config apply нужны зарегистрированная identity, явный RNS config,
проверенный relay public identity и подписанная конфигурация с действующим gateway
peer. На этом шаге они не создавались и signing key не использовался.

Следующий шаг — ручной пилот paired bundle на устройстве с кратким health/cleanup
и проверкой возврата. Windows/Android binding, AWG3.1, TD-1 intermittent HTTPS и
отложенные device/load tests остаются открытыми. Stage6 не принят.
Desktop0.2.9 published, Linux0.2.8 observed installed, gateway0.2.1, TCP0.1.0,
catalog sequence8 сохранены. Рабочий checkout не переключался на CI-ветку/main;
реализация сохранена в ветке stage5-linux-control-preview. Нет merge/release/deploy.

## Точный список файлов этого шага

- .github/workflows/control.yml
- Dockerfile.control
- provisioning/runtime.py
- tests/test_control_channel.py
- tests/test_control_package.py
- docs/reticulum-control.ru.md
- docs/linux-control-preview-rollout.ru.md
- docs/STATUS.md
- docs/PLAN.md
- docs/README.md
- docs/releases/2026-09-13-linux-control-acceptance.ru.md
