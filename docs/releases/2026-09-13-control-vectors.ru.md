# Stage5: общий набор conformance vectors — 13.09.2026

## Реализовано

`tests/vectors/control-v1` содержит неизменяемые wire inputs с SHA256/size,
ожидаемые decoded payload/ACK body и явные journal transcripts. Все ключи
намеренно публичные TEST ONLY, получены из явно обозначенных в коде тестовых labels;
генератор не принимает путь к ключу, не читает deployment state и отказывается
перезаписывать существующий output directory. Тест подтверждает отсутствие
Path file reads в генераторе и отличие fixture anchor от production public anchor.

30 конфигураций: WG/AWG2/TCP, следующая revision, корректный envelope для rejected
revision/previous-hash сценариев, tamper/signing purpose, signer/target/WG/audience,
schema/boolean/schema-unknown, unknown field, profile, AWG3.1 refusal, clock,
точная граница expiry и client version, duplicate outer/plaintext JSON, malformed,
65536 accepted/65537 rejected bytes. Размер граничных valid inputs достигается
JSON whitespace; hash относится к исходным bytes, а не повторной сериализации.

15 ACK inputs: все6 статусов, граница4096/4097, duplicate JSON, tamper,
неверный ack_id, boolean sequence, unknown field, noncanonical public key,
wrong purpose. Для проверки ack_id/bool/unknown-field fixtures заново подписаны
тестовой identity: rejection проверяет структуру, а не только случайную подпись.

3 transcripts/16 шагов: replay/sequence/previous hash, failed health→rollback→duplicate,
crash в APPLIED_PENDING→restart/recover→idempotent recovery→ACK failure/retry.
Initial clock/version/floor/state и ожидаемые state/effects заданы явно.
Application boundary моделируется без VPN/carrier. Это reference conformance,
не живая native/platform acceptance. Существующий живой Linux пилот — отдельный отчёт.

[Формат и команды](../../tests/vectors/README.md).
Manifest SHA256: `c97e00ccff7440b09a636a792557c0602aba5eb63815cdc8fefe7755711ac3cd`.
Генерация использует randomized encryption: новый corpus имеет другие ciphertext
и требует отдельного review/commit. В обычных тестах golden inputs не заменяются.

## Проверки

50 новых проверок прошли. Полная локальная Python suite **462 passed**,
2 прежних FastAPI/Starlette warnings. После уточнения explicit manifest metadata
и portable transcript clock повторена только целевая suite50: passed.
Первый полный запуск внутри sandbox упёрся в известные RNS/HTTP/TestClient
ограничения и был остановлен; полный успешный запуск выполнен вне sandbox.

В процессе написания runner исправлен выбор error evidence: rejected ACK находится
в outbox, journal.result продолжает хранить последний final application result.
Ожидаемые REPLAY/PREVIOUS_HASH и runtime протокол ради теста не менялись.

Generator/fixtures находятся под tests/, не scripts/: Docker runtime COPY scripts
не забирает тестовые ключи. Paired preview allowlist также исключает vectors и
генератор. Новая публикация corpus — отдельный CI artifact с TEST-ONLY в имени.
Git attributes сохраняют точные bytes/whitespace без CRLF conversion на Windows.
Control workflow добавляет manifest SHA256 annotation. Runtime/client bytes не менялись.

## Remote CI acceptance

Source **598454bad71fdf290a673c0f10a7f4afa61e2b18**, ветка stage5-linux-control-preview.
[Linux control34748501643](https://github.com/Joker20380/family_connect/actions/runs/34748501643)
и [phase034748501640](https://github.com/Joker20380/family_connect/actions/runs/34748501640)
завершились success. Это включает protocol/arbiter/package suite, GTK и extracted
artifact checks; phase0 включает Python/Rust и isolated Docker failover acceptance.

Check annotation Control vectors manifest SHA256 совпал с committed manifest:
`c97e00ccff7440b09a636a792557c0602aba5eb63815cdc8fefe7755711ac3cd`. Отдельный artifact control-conformance-v1-TEST-ONLY загружен CI.
Archive ZIP не скачивался; digest проверен через официальный check annotations API.
Paired client archive по annotation сохранил SHA256
9c827f86f03d27705c46830758e114b3f7ef9796320d9e46f09672363de076f3 — ровно прежний
принятый live bundle66152538ee2a4f3e. Тестовые vectors в него не включены.

Отдельная проверка git checkout-index с core.autocrlf=true подтвердила побайтовое
совпадение всех48 файлов corpus, включая manifest и whitespace boundary inputs.
Это проверка checkout bytes, не Windows native verifier/runtime acceptance.
Итоговые результаты сохранены отдельным documentation checkpoint с [skip ci],
не меняющим принятый source/corpus. Initial sandbox failure и correction runner
описаны выше, ожидаемые ошибки протокола не ослаблялись.

## Состояние и следующий шаг

Первый блок interop corpus завершён. Следующий шаг — native Windows verifier,
читающий этот manifest и те же bytes;
затем Android verifier, protected storage/journal/outbox и shared ownership.
См. [native plan](../stage5-native-binding.ru.md). Корпус и Python runner сами по
себе ещё не означают поддержку Stage5 Windows/Android.

Нет VPN запуска, ключей production в Git, установки, release/catalog/main merge
или server changes. Installed Linux0.2.8/previous0.2.7, опубликованные
Desktop0.2.9/catalog8, gateway0.2.1/TCP0.1.0 без обновления.
Последний live journal IDLE/floor3/committed2/outbox0/pending=null, VPN выключен;
в этом шаге private state не менялся и не перечитывался для генерации.
Gateway lease/configs предыдущего пилота имеют сроки13.09 08:43:59Z/08:40:14Z;
после expiry следующая реальная config revision≥4 требует renew/signing с теми же
identity/journal и previous hash config2, без сброса floor. Здесь expiry cleanup
не проверялся. Возврат приложения не требуется — установленный клиент не менялся.
TD-1, первый Android CI failure неизвестной причины, AWG3.1 и Stage6 остаются открытыми.
