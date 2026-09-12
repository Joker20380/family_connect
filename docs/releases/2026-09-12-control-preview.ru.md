# Stage 5 — paired Linux preview, 2026-09-12

## Результат и архитектура

Добавлен отдельный operator preview из одного набора исходников: Linux GUI,
существующий backend с общим operation arbiter и carrier-independent provisioning
core. Шестифайловый desktop archive и updater не изменены. Версии Desktop0.2.9,
TCP0.1.0, опубликованный catalog sequence8 и установленный Linux0.2.7 сохранены.
Это preview для ручной приёмки, не новая опубликованная версия0.2.9.

`package_control.py` собирает только явный allowlist публичных файлов, включая
публичный update anchor. Private signer, device state, profiles и offline signing
script в архив не входят. Имя содержит digest полного состава; запись поверх
существующего архива запрещена. tar/gzip metadata детерминированы.
Manifest SHA256 обнаруживает повреждение/смешение файлов, но **не является подписью**:
оператор должен получать preview из доверенной сборки. Trust конфигурации по-прежнему
обеспечивается offline Ed25519 anchor, а не manifest или Reticulum relay.

Launcher запускает GUI системным Python с GTK, а control отдельным Python venv с
runtime-only pins из существующих lockfiles. Оба используют backend из одного
комплекта и общий пользовательский durable arbiter. Формат envelope, lifecycle и
существующие WG/AWG2/TCP реализации не менялись. Pending journal после crash требует
восстановления тем же state path; удалять marker для обхода блокировки нельзя.

Stage 5 implements verified Reticulum-based configuration delivery and transactional apply/ACK/rollback.

This does not yet prove recovery from loss/blocking of the only known infrastructure endpoint. Independent control entry and alternate gateway remain Stage 6.

## Проверки

- Полная локальная Python suite: **405 passed**, 2 прежних dependency warnings.
- Дополненный package test: **3 passed**, в том числе actual two-process RNS
  commit/ACK, failed-health rollback/ACK, duplicate safety из распакованных модулей.
- Проверены init-client с shipped public anchor вне checkout, allowlist,
  отказ overwrite, dependency pins и отказ запуска после изменения backend.
- GUI `--smoke` из распакованного preview: exit0 через системный GTK/Wayland/D-Bus.
- Sandbox не разрешает loopback/D-Bus; эти проверки выполнены с разрешённым запуском
  вне sandbox. Portal teardown warnings не привели к ошибке smoke.
- Добавлен `.github/workflows/control.yml`: Python regression, GTK layout/recovery/
  TCP install checks, fresh venv с preview lockfile, extracted CLI/GUI smoke,
  upload preview и legacy desktop archive. Remote result: pending.

## Запуск и откат

Закрыть старый установленный GUI: он не участвует в новом арбитре. Распаковать
preview в отдельный пользовательский каталог. В примерах `$preview` — абсолютный
путь к распакованному `FamilyConnect-Control-preview`:

```sh
python3 -m venv /tmp/fc-control-preview-venv
/tmp/fc-control-preview-venv/bin/pip install -r "$preview/provisioning/requirements.lock"
/usr/bin/python3 "$preview/scripts/run_control_preview.py" verify
/usr/bin/python3 "$preview/scripts/run_control_preview.py" gui
/tmp/fc-control-preview-venv/bin/python "$preview/scripts/run_control_preview.py" control --help
```

Параметры init-client/once — по [control runbook](../reticulum-control.ru.md).
Identity, state и RNS config находятся вне каталога preview; GUI и control запускаются
одним пользователем. Ни launcher, ни пакетирование не создают service/scheduler,
не устанавливают helper и не подключают VPN автоматически. Для возврата закрыть
preview; при pending сначала выполнить recovery тем же journal и только затем
вернуться к старому GUI. Не удалять persistent identity/journal при смене preview.

## Ограничения и следующий шаг

Preview ещё не установлен на рабочее устройство и не подписан как update component.
Автоматическая доставка/обновление, защита от одновременно открытого старого GUI,
Windows/Android native binding остаются открыты. Нельзя запускать старый GUI или
ручные root/NetworkManager mutations одновременно с control apply.
TD-1 intermittent HTTPS, длительная/device приёмка и TD-2 AWG3.1 не закрыты.
Stage6 не принят. Следующий шаг после CI — приёмка paired preview перед rollout.

## Изменённые файлы этого шага

- `.github/workflows/control.yml`
- `scripts/package_control.py`
- `scripts/run_control_preview.py`
- `provisioning/requirements.lock`
- `tests/test_control_package.py`
- `docs/STATUS.md`
- `docs/PLAN.md`
- `docs/README.md`
- `docs/releases/2026-09-12-control-preview.ru.md`

Предыдущая Stage5/GUI реализация сохранена без изменения; её списки файлов и
результаты находятся в отдельных checkpoint-документах.
