# ADR 001: identity и граница provisioning

Дата: 09.09.2026. Статус: реализован проверочный модуль; публичный production-протокол ещё не зафиксирован.

## Решение и реализация

Для независимой identity используется настоящий reference-пакет `rns==1.5.1` и его публичные методы шифрования/подписи. Модули не запускают сеть. WireGuard получает отдельно сгенерированный X25519 private key. Лабораторная P-256 identity, старая Windows-активация и VPN-приложения сохраняются.

`device_identity/device.py` создаёт и загружает ключи в POSIX-каталоге приложения: каталог 0700, файлы 0600, проверка владельца, запрет symlink/hardlink, блокировка параллельной инициализации и атомарная публикация с fsync. Повреждённый ключ или потерянная permanent identity при сохранённом transport key приводят к отказу, а не незаметной замене identity. Родительские каталоги должны быть доверенными. Это Linux-хранилище с файловыми правами, а не шифрование через OS keychain. Интеграция Android Keystore и Windows DPAPI ещё требуется; переносить это хранилище на другие платформы или отправлять приватные файлы серверу нельзя.

Proof of possession подписывает JSON с отдельным domain separator: публичные Reticulum identity и WG key, 32-байтный challenge сервера, фиксированный enrollment audience, schema и transport. Проверяется владение identity и привязка ключа. Будущий registration service обязан проверить TTL challenge, атомарно погасить его, проверить membership/entitlement и установить peer. Этот stateless verifier сам не предотвращает повтор уже корректного proof. Владение приватным WG-ключом отдельно проверяет WireGuard.

`provisioning/models.py` содержит неизменяемую строгую модель: recipient identity hash, отдельные schema/revision, authorization lease, entitlement reference/revision, публичный клиентский WG key, адреса/DNS и упорядоченные gateway candidates с provider/region/необязательным ASN. Пока поддерживается только WireGuard. Приватные credentials остаются локальными; лишние поля, включая private keys, запрещены. До публикации нужно согласованно установить peer и адреса на всех кандидатах.

`provisioning/envelope.py` шифрует JSON через reference `Identity.encrypt`, затем подписывает domain `family-connect/provisioning-envelope/v1\0` и точные байты ciphertext методом server identity `sign`. Внешний JSON содержит только base64 ciphertext и signature. Verifier использует заранее доверенный server public identity, проверяет подпись до расшифровки, затем схему, адресата, локальный WG public key, lease, revision и entitlement revision. Дубли JSON-полей и слишком большие envelopes отклоняются. Это формат сообщения приложения поверх готовой RNS-криптографии, а не новый шифр. Он не зависит от доверия к HTTPS или RNS Link. Шифрование на постоянную identity не защищает архивные ciphertext после компрометации её ключа; forward secrecy для этого envelope не заявляется.

`VerifiedProvisioningState` — внутренняя типизированная граница, а не защита от вредоносного кода внутри процесса. Issuance остаётся внутренней функцией, не публичным endpoint. Перед публикацией сервиса нужны серверная проверка entitlement, безопасное хранение signing key и авторизация.

## Что отложено

Этот этап не добавляет аккаунты/БД, invitation API, challenge store, реальную HTTPS/RNS-доставку, UI-интеграцию, применение туннеля, runtime builder или автоматический failover. Revision floor передаётся verifier извне; защищённое долговременное хранение ещё не реализовано. Версии не выше floor отклоняются. Повторная проверка кеша, разрешённый rollback и known-good recovery требуют отдельной машины состояний provider; нельзя просто уменьшать floor для обхода защиты. Проверочный lease ограничен 24 часами и пока не управляет работающим VPN.

Production signing keys должны находиться на серверной инфраструктуре, клиенты получают публичные anchors. Сейчас явно передаётся один anchor, trust-on-first-use отсутствует. Планируемый bootstrap использует несколько операторских путей, подписанные announcements и кеш публичных destinations. Логическая Reticulum identity не отменяет физические IP в интернет-транспорте. Для ротации destinations/anchors нужны отдельный подписанный версионный manifest, период перекрытия и recovery policy. Отказ bootstrap не должен создавать доверие к случайному ответившему узлу или закрывать уже разрешённое соединение. Общего consumer secret/GROUP identity не будет. Реальная RNS Link-доставка и упаковка Android/Windows ещё не проверены.

## Проверки

Установить `pip install -r control/requirements.lock -r device_identity/requirements.lock`, затем `python -m pytest -q`. Полный Python suite: 75 passed. Новые тесты проверяют импорт ключей и шифрование через настоящий RNS, persistence, независимость ключей, подмену proof, опасное/повреждённое хранилище, конкурентное создание, адресное шифрование provisioning, чужую подпись/ключ расшифровки, схему/private keys, expiry, replay/downgrade и нескольких провайдеров. Это не физическая VPN-проверка платформ и не тест доставки через действующую сеть Reticulum.

## Первичные источники

* [Reticulum Identity API](https://reticulum.network/manual/reference.html): импорт публичных identity, sign/validate и encrypt/decrypt.
* [Reference implementation Reticulum](https://github.com/markqvist/Reticulum): источник для проверки совместимости.

Следующий отдельный этап: транзакционная регистрация устройств с погашением challenge и хранением entitlement, затем durable provisioning provider/HTTPS/cache. Подключение нативных клиентов — после проверки платформенного хранилища и protocol fixtures.
