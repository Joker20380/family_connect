# Stage 5 — reference control channel, 2026-09-12

Baseline `4cb1423`; локальная реализация поверх этой версии, без commit/release/
remote CI/deployment. Python 3.14, pinned `rns==1.5.1` из identity lockfile.

**Stage 5 implements verified Reticulum-based configuration delivery and transactional apply/ACK/rollback.**

Эта формулировка относится к carrier-independent reference protocol/core и Linux
application boundary, проверенным локально. Native Windows/Android packaging,
общий operation arbiter с GTK и production rollout этим checkpoint не принимаются.

**This does not yet prove recovery from loss/blocking of the only known infrastructure endpoint. Independent control entry and alternate gateway remain Stage 6.**

## Результат

Адресно зашифрованный schema-2 config подписывается существующим offline Ed25519
root с отдельным domain; app-update catalog/sequence 8 не меняются. Подпись, signer,
recipient/WG-key/audience, schema, lease, version, profiles, revision и previous hash
проверяются до apply. Reticulum переносит только сообщения. Конфигурация и state
machine не зависят от carrier; deterministic adapter реализует тот же интерфейс.

Private atomic journal разделяет staged/committed/pending apply/runtime recovery/
outbox. Healthy commit и COMMITTED ACK атомарны. Interrupted apply всегда откатывается.
Replay и одинаковый revision с другими байтами отвергаются; точный duplicate возвращает
результат без повторного apply. Failed revision floor не теряется. Device-signed ACK
имеет фиксированные ошибки, device/config/revision/hash/time и deduplication id.

AWG 3.1 учтён явной версией и отказом `UNSUPPORTED_TRANSPORT_VERSION` до stage на
текущем runtime. Нет silent downgrade к AWG 2.0. Миграция 3.1 остаётся отдельным TD-2,
согласно последнему ответу пользователя. TD-1 device/full-routing/load не возобновлялись.

## Проверки

- **381 Python tests passed**, 2 существующих FastAPI/Starlette deprecation warnings;
  полный suite с control/identity lockfiles, исходный baseline 325 тестов сохранён.
- 56 новых проверок: signature/unknown signer/tamper, lease/future/schema/audience/
  device/version, AWG 3.1 rejection, существующие AWG 2.0/TCP parsers, revision/
  previous hash, duplicate/invalid higher revision, crash STAGED/APPLYING/
  APPLIED_PENDING/post-commit, write failure, rollback retry, expired last-good,
  ACK retry/dedup/backpressure, non-secret diagnostics, malformed RNS messages,
  timeout/cancel и existing Linux backend interface boundary.
- Два **реальных RNS процесса** через explicit loopback TCP, без HTTP API:
  config1 → verify → apply → health → commit → 3 ACK;
  config2 → apply → failed health → rollback → ACK;
  повтор config2 безопасен; committed config1 и floor2 сохранены, outbox пуст.
  Application/health здесь deterministic; kernel/physical VPN не тестировался.
- Reference CLI и offline signer `--help` проверены. RNS socket tests выполнены
  вне sandbox, поскольку sandbox запрещает даже 127.0.0.1 socket creation.
- Remote GitHub Actions не запускались. Native transport implementations, GTK,
  Windows broker, Android VpnService и build pins не изменены; свежая native CI
  приёмка этой версией не заявляется.

## Точный список изменений

Новые файлы:

- `provisioning/configuration.py`
- `provisioning/transaction.py`
- `provisioning/ack.py`
- `provisioning/application.py`
- `provisioning/reticulum.py`
- `provisioning/relay.py`
- `provisioning/runtime.py`
- `scripts/sign_control_config.py`
- `tests/test_control_channel.py`
- `tests/test_reticulum_provisioning.py`
- `tests/reticulum_control_peer.py`
- `docs/stage5-architecture.ru.md`
- `docs/reticulum-control.ru.md`
- `docs/releases/2026-09-12-reticulum-control.ru.md`

Обновлены: `docs/STATUS.md`, `docs/PLAN.md`, `docs/ROADMAP.ru.md`, `docs/README.md`.

## Rollout / rollback / ограничения

Ничего не установлено и не развёрнуто. Desktop 0.2.9/catalog8, installed Linux0.2.7,
server0.2.1 и TCP Setup0.1.0 сохраняют прежние версии. Production keys/profiles/DB
не читались и не менялись. Применение нового runner только явно через
[runbook](../reticulum-control.ru.md); sole connection owner обязателен.

Rollback code rollout: остановить reference runner, сохранить journal/floors,
вернуться к baseline checkout. Не удалять journal и не подменять его старым backup.
Runtime rollback выполняется автоматически по сохранённому baseline; ошибка
очистки оставляет ROLLING_BACK для повтора. Импортированные inactive профили пока
сохраняются. Истёкший last-good не разрешает reconnect.

До background/native distribution: общий connection-operation arbiter с GUI,
нативное secure storage/application binding, упаковка и scoped CI; relay resource
quotas/retention. CLI флаг exclusive owner не является межпроцессной блокировкой GTK.
Local owner/root и доверенное время остаются trust assumptions; rollback всего
state backup не защищён hardware counter. Полные secret profiles никогда не логируются.

[Архитектура, state machine, security assumptions](../stage5-architecture.ru.md).
