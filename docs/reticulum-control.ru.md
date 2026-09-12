# Reference Stage 5: операции

См. [архитектуру и границы](stage5-architecture.ru.md). Все команды выполняются
из checkout проекта с зависимостями control/device_identity lockfiles. Существующие
stable binaries, production gateway и каталог не обновляются этими инструкциями.
Не использовать реальные signing keys в CI; тесты создают одноразовые ключи.

## Offline publication

Подготовить приватный JSON по `ControlConfiguration` (schema 2). Значения
`recipient` и `wireguard_public_key` берутся из уже доверенной device registration.
`signer_key_id` — SHA256 **существующего** Ed25519 public anchor. Начальный
`previous_config_hash=null`; после commit — hash предыдущего envelope. Revision
отдельный для устройства/configuration, не app catalog sequence. Lease ≤ 24 часа.

В WG/AWG INI профиле `PrivateKey = LOCAL_DEVICE_KEY`; никаких shell hooks/paths.
WG `transport_version="1"`, AWG `"2.0"`, TCP `"1"`. AWG 3.1 до миграции runtime
отклоняется. Gateways должны совпадать с endpoints профилей. Наличие gateway peer
оператор проверяет отдельно перед выдачей; этот relay не создаёт peers.

```sh
python -m scripts.sign_control_config --key state-client-build/update-signing/ed25519.key \
  --configuration /private/control-config.json --recipient-public PUBLIC_DEVICE_IDENTITY \
  --output /private/control-config.envelope
python -m provisioning.runtime init-relay --state /private/control-relay
python -m provisioning.runtime publish --state /private/control-relay \
  --public-identity PUBLIC_DEVICE_IDENTITY --wg-public DEVICE_WG_PUBLIC_KEY \
  --sequence 1 --envelope /private/control-config.envelope
python -m provisioning.runtime serve --state /private/control-relay \
  --identity /private/control-relay-identity --rns-config /private/rns-relay
```

Signer выполняется офлайн; на relay передаются только public binding/ciphertext.
`serve` выводит public transport identity для trusted bootstrap, не signer secret.
RNS конфигурация задаётся оператором отдельно; автообнаружение случайного signing
anchor запрещено. Product database существующего API не меняется.

## Linux reference client

Использовать существующий каталог device identity и проверенный публичный anchor.
Инициализация journal однократная; **не удалять state для сброса sequence**.

```sh
python -m provisioning.runtime init-client --state /private/control-client \
  --identity /private/device --anchor clients/desktop/update.pub
python -m provisioning.runtime once --state /private/control-client \
  --identity /private/device --anchor clients/desktop/update.pub \
  --rns-config /private/rns-client --provider-public TRUSTED_RELAY_PUBLIC_IDENTITY \
  --exclusive-connection-owner
```

`once` применяет конфигурацию через имеющийся Linux backend; prerequisites/helpers
должны быть установлены. Новый GUI этой версии участвует в общем arbiter и может оставаться открытым. Старый GUI и ручные NetworkManager/root operations должны быть исключены. Системная
авторизация остаётся штатной; её отмена прекращает apply и запускает rollback.
Не запускать как отложенный host/device test без отдельного решения пользователя.
После ошибки повторить тот же state: recovery и outbox идемпотентны. Ошибка rollback
оставляет pending intent; новый apply не допускается, пока cleanup не завершён.
Не восстанавливать старый journal как способ отката. Last-known-good ciphertext
и sequence floors остаются в state, отмена rollout — остановить reference runner.

## Diagnostics и приёмка

Structured logger `family_connect.control`: event, config_id, sequence, phase,
fixed error category. ACK: public identity, wire envelope hash, verified config id/
revision (null/0 для отвергнутых непроверенных данных), status, error, timestamp,
ack_id, device signature. Profile/credentials/exception text в log/ACK не попадают.

```sh
python -m pytest -q tests/test_control_channel.py tests/test_reticulum_provisioning.py
python -m pytest -q
```

Реальный RNS тест использует два процесса с явными TCP interfaces на 127.0.0.1,
без HTTP сервера, внешней сети, VPN интерфейса и production identity. Apply/health
в этом тесте deterministic; production Linux boundary проверяется отдельно через
существующие backend interfaces. Это не проверка маршрутов/нагрузки/физических устройств.


После GUI integration pending marker хранится в
`~/.local/state/family-connect-operations/state.json`. Не удалять его для обхода
recovery. Запустить `once` с тем же journal: IDLE/успешный rollback снимает блокировку.
Другой journal не может забрать незавершённую транзакцию. Флаг
`--exclusive-connection-owner` сохранён для совместимости, но для новых GUI/core
больше не обязателен. Старые приложения блокировку не соблюдают.
