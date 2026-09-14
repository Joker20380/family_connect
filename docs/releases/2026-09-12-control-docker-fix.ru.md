# Stage 5 — исправление Docker test stage, 2026-09-12

## Причина

В phase0 run34720569486 шаг `Build isolated failover stack` завершился ошибкой.
На исходнике d8aef8a/0e710fc локальная сборка Dockerfile.control воспроизвела
ошибку collection в test_control_channel и test_reticulum_provisioning:
`ModuleNotFoundError: No module named 'clients.desktop.updates'`.

Docker test stage копировал только desktop/profile_config.py. Stage5 повторно
использует существующий updates.version и backend; package tests дополнительно
нуждаются во всём публичном шестифайловом bundle и VERSION. Checkout CI имел эти
файлы, поэтому обычный pytest проходил; Docker test image был неполным.
Оригинальные удалённые logs недоступны через API без auth (403); локальный
репродукт устанавливает конкретную ошибку того же test image.

## Исправление

Commit `ac6a22f6894fe0fa3c2a187a224c96d5133853e3`, ветка
`stage5-linux-control-preview`: Dockerfile.control копирует VERSION и явный список
app.py, backend.py, profile_config.py, updates.py, update.pub, install-linux.sh
только в **tests stage**. Runtime stage остаётся без desktop/provisioning payload.
Не исключались тесты, не менялись зависимости и signing policy.

## Проверки

- До исправления: Docker build exit2, две collection errors.
- После исправления: Docker build exit0, **250 passed**, 2 прежних warnings,
  Python3.13. Локальный диагностический image `family-connect-control:stage5-build-diagnosis`,
  ID `5eade918b8f8`. В Docker выполняются tests/; desktop tests отдельно входят в
  ранее прошедшую общую suite405 и Linux CI.
- Runtime image успешно собран. Локальный compose не запускался; работающие
  сервисы и production gateway не затронуты.
- Повторный [phase0 run34720868247](https://github.com/Joker20380/family_connect/actions/runs/34720868247): **success**, оба jobs прошли.
  Успешны build/provision, failover, auth, offline, revocation, upload и compose down.
  Python/Rust regression также passed. Исправление сборки принято.
- Предыдущие Clients34720569537: Windows/Linux passed, Android ещё выполнялся
  на момент checkpoint; полная client acceptance отдельно от закрытой ошибки phase0.

## Границы

Desktop0.2.9, установленный Linux0.2.7, TCP0.1.0, gateway0.2.1 и catalog sequence8
сохранены. Нет release, merge, install или server mutation. Изолированный phase0
не заменяет TD-1 device/load/full-routing приёмку и Stage6 independent entry.
AWG3.1 остаётся отдельным долгом. Rollback этого изменения — возврат только COPY
инструкций Dockerfile.control; это вернёт известную ошибку test image, поэтому
для рабочего rollout используется исправленная сборка после CI.

## Файлы этого исправления

- Dockerfile.control
- docs/STATUS.md
- docs/PLAN.md
- docs/releases/2026-09-12-control-docker-fix.ru.md
