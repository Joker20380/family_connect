# Android: транзакционный выбор gateway внутри committed configuration

24.09.2026. Локальный checkpoint5.3а. APK/серверы не менялись;
Android0.1.18-beta50/code50, Linux0.2.10, Windows0.2.13 сохраняются.

## Контракт

`ControlTransaction.selectGateway(id)` — отдельная локальная операция, не повторный
`receive`. Принимается только ID из transport_profiles текущего committed envelope.
Проверяются operation owner, отсутствие pending apply/recovery, подпись/identity,
срок конфигурации и clock floor. Произвольный адрес/профиль передать нельзя.

`ControlApplication` реализует `Selectable.forGateway`: создаётся объект с фиксированным
ID, но тем же Host/identity/engine. Второй VPN или независимый владелец не создаются.
До side effects сохраняются baseline, исходный envelope и pending ID. После apply,
health и повторной проверки срока сохраняются runtime и выбранный ID. Повтор уже
сохранённого выбора возвращает SELECTED без apply: это подтверждение выбора, не новая
проверка здоровья. Для reconnect используется resume с проверкой health.

Signed revision, replay floor, digest, previous hash, result и outbox не меняются при
локальном выборе. Существующие ACK подтверждают конфигурацию, не конкретный локальный
gateway. Новые selection ACK/телеметрия здесь не вводятся. При новом успешном receive
локальный выбранный ID сбрасывается; повтор прежнего envelope его сохраняет.

## Журнал и crash recovery

Schema1 продолжает читаться/создаваться. Первая явная операция выбора записывает schema2
с `selected_gateway` и `pending_gateway`. Это версия локального Android journal, не
wire schema или fleet DB. Один шаг сохранения содержит переход схемы и phase SWITCHING.
Оба ID проверяются по signed committed profiles. Staged envelope при SWITCHING обязан
побайтно совпадать с committed; в отличие от новой выдачи его revision не повышается.

Пока SWITCHING не завершён, новый выбор/resume запрещены. Recover выполняет rollback
на baseline; phase остаётся SWITCHING до успешной очистки и durable save. Ошибка stop
или rollback возвращает FAILED и оставляет recovery обязательным. При expiry прежние
профили восстанавливаются на диске, но не подключаются. Если финальный commit уже
сохранён, restart сохраняет новый выбор. Resume использует ID из журнала, а не старое
значение UI preferences. Старые клиенты, понимающие только schema1, schema2 отвергнут.

Безопасного downgrade schema2→1 нет. Не удалять journal/Keystore aliases, не снижать
floor и не восстанавливать устаревшую копию ради запуска старого приложения. Перед
будущим rollout нужны согласованные callers/service/UI, device acceptance и план
обновления вперёд. На production переход схемы в этой работе не выполнялся.

## Тесты

120 Java tests passed,0 failures/errors/skipped. Девять новых JUnit methods содержат
проверки общего fixture, apply/idempotence/reopen/resume, перехода на новую конфигурацию,
неизвестного ID/expiry/clock/owner, health/partial save rollback, отказа cleanup,
повреждённого выбора, expiry во время операции, а также сбоя до/после каждого из двух
сохранений успешного выбора. Первый прогон выявил неправильное ожидание типа исключения
в тесте requireIdle; ожидание исправлено на существующий IOException, код admission не
ослаблялся. Финальный полный прогон успешен.

```sh
JAVA_HOME=/tmp/fc-chat-tools/jdk/jdk-17.0.20.1+1 GRADLE_USER_HOME=/tmp/fc-chat-tools/gradle-home /tmp/fc-chat-tools/gradle-8.11.1/bin/gradle -p clients/android/control-tests test --offline --no-daemon
```

Запуск с разрешением вне sandbox для localhost socket Gradle. Host и storage имитируются;
настоящий Android VPN/Keystore/Doze не проверены. Подпись/дешифрование реальны на публичных
тестовых ключах. Новый immutable corpus `tests/vectors/control-selection-v1` содержит
два подписанных envelope; hashes закреплены в тесте. Генератор читает только публичный
AWG3.1 test corpus, пишет в новый каталог и не использует production keys.
`git diff --check` прошёл.

## Остаток работ

Метод ещё не вызывается UI/ConnectionService. Нужен единый service worker entry point,
обработка результата/отмены и согласование выбора UI с journal, затем device acceptance.
AWG3.1 production capability пока выключен; интеграция Friends identity, Linux/Windows
application, offline→online/ACK и независимые ingress открыты. Новый сервер для этих
локальных проверок не нужен. Commit/push в этой работе не выполнялись, отчёт локальный.
[Карта кода](../managed-control-code-map.ru.md) обновлена вместе с реализацией.
