# Причина остановки NL restricted-bootstrap —14.10.2026

Read-only диагностика186.246.45.246 после health audit. HEAD8d04632;
входные изменения сохранены. Основные AWG/TCP повторно подтверждены active.
Ни один профиль/ключ/клиентский IP не выводился. Использованы штатные ограниченные
обезличенные fatal-application/fatal-systemd receipts и фильтрованный journal.

## Подтверждённая цепочка (UTC)

| Время14.10 | Событие |
|---|---|
|07:44:21.485|SEED_READ / SUBSCRIBER_DISCONNECTED, fatal exit1|
|07:44:51|Автоматический новый запуск|
|08:29:23.000|SEED_READ / SIGNAL_READ; WS_CLOSE4008,context ACTIVE,carrier_closed=false|
|08:30:08.255|SEED_CREATE / provider_timeout, elapsed15040ms|
|08:30:53.486|SEED_CREATE / provider_timeout, elapsed15026ms|
|08:31:38.757|SEED_CREATE / provider_timeout, elapsed15035ms|
|08:32:23.989|SEED_CREATE / provider_timeout, elapsed15026ms|
|08:33:09.230|SEED_CREATE / provider_timeout, elapsed15017ms|
|08:33:39.443|systemd: Start request repeated too quickly; failed|

Последний application PID2709212/invocation13aa0399413a494f88e1e55c5702d250
согласуется с systemd exit1. Cleanup started/completed. Настройки Restart=always,
RestartSec30,StartLimitBurst5,StartLimitInterval600s; NRestarts9 включает более ранние
перезапуски и не означает девять последних таймаутов. Условие start-limit объясняет,
почему служба не восстановилась автоматически после серии ошибок.

Точный смысл приватного provider close4008 НЕ установлен; нет доказательств бана,
лимита аккаунта или внутреннего сбоя Telemost. provider_timeout не различает
ретроспективно DNS/TCP/TLS/API задержку. Новые комнаты/провайдерские запросы не
создавались. Это доказанная цепочка остановки приложения, не root cause внутри провайдера.
Более ранний SUBSCRIBER_DISCONNECTED не переатрибутирован к4008.

## Отдельный блокер готовности: внутренний сертификат

gateway.json mode0600,uid979,доступен family-restricted. Leaf:
notBefore13.10 20:46:00UTC,notAfter14.10 00:46:05UTC. К моменту последнего старта
headroom=-28024s, подтверждён immutable startup receipt. Текущий профиль имеет тот же
истёкший leaf, хотя mtime14.10 10:28:24UTC меняется при штатной синхронизации.
CRL lastUpdate10:28:38/nextUpdate14:28:38UTC; issuer notAfter14.10 15:12:20UTC.
Обновление CRL не продлевает leaf. Это отдельная причина отсутствия безопасной
клиентской готовности, НЕ записанная причина этих exit1. Публичный HTTPS сертификат
до19.10 — другой сертификат и не исправляет внутренний Family TLS.

## Точная исполняемая версия

Фактический systemd ExecStart:bin/bootstrap-broker-signal-observation-20261012,
SHA25621f0a0fdc27b50c00ea922f0b716516e2422aedf1b3797369718f7d00070509a.
Application receipts подтверждают этот SHA и source a4087e000fdbe674b72ede3a6c8822445c87c654
(сохранённая классификационная дельта входит в binary baseline).
Аргументы duration4h,seed-rotate-after3h,chat-services. Начально проверенный
generic bin/bootstrap-broker SHA5f136c40a22ba7c6b590ab7d332365c381b55ea514c7e379ef919caf17059cea
не является текущим ExecStart: его нельзя принимать за deployed runtime.

## Действия и ограничения

Никаких restart/reset-failed/renewal/deploy/изменений unit, security floors или TTL.
Откат не нужен. Source-only supervisor/CRL acceptance gates не менялись. Версии
установленных/публичных/invitation-page клиентов не менялись и не перепроверялись.
Первое journal-чтение ограничено25s и завершилось timeout; обратное ограниченное
чтение успешно. Причины подтверждены receipts независимо от raw logs.
Кодовые тесты/клиентский E2E NOT_RUN; документация git diff --check без замечаний.

Для восстановления нужен отдельный контролируемый шаг: валидные внутренние credentials
через accepted owner-preserving publication, проверка провайдера, ограниченный запуск
и readiness/стабильность. Не отключать expiry/revocation/start-limit и не запускать
owner FIELD автоматически. Слепой restart не устраняет ни provider_timeout, ни expiry.
