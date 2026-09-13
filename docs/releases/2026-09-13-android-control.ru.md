# Android Stage5: проверка протокола — 13.09.2026

## Реализация

`ControlProtocol.java`: Ed25519 подпись отдельного purpose+NUL до расшифровки,
RNS1.5.1 ciphertext X25519/HKDF-SHA256/64 bytes/AES256-CBC/HMAC-SHA256,
recipient/audience/signer/WG binding, schema2, lease/version, AWG3.1 refusal.
ACK проверяет identity hash, canonical body, ack_id, собственный domain и лимит4096.
Configuration digest считается по исходным bytes, лимит65536. Ошибки содержат
только category; plaintext/credentials не выводятся. Verified.state() возвращает копию.
`ControlJson.java`: strict Gson streaming, recursive duplicate rejection, depth64,
UTF8 REPORT, отказ unpaired surrogate, сохранение numeric token для bool/float/exponent
refusal. `ControlProfiles.java`: отдельный schema2 WG/AWG2/TCP parser с gateway
binding, local-key placeholder и запретом hooks. Legacy import parser не изменён.
Numeric gateway parsing не делает DNS lookup для имён.

Закреплены BouncyCastle bcprov-jdk18on1.85.2 (lightweight API, без регистрации
системного provider) и Gson2.13.2; версии одинаковы в app и JVM test project.
Обе лицензии добавлены в assets/control-licenses; APK gate требует их наличия.
[BC Java](https://www.bouncycastle.org/download/bouncy-castle-java/) и
[Gson2.13.2 release](https://github.com/google/gson/releases/tag/gson-parent-2.13.2).

## Проверки и границы

Локальный Gradle8.11.1/JVM17 Docker:30 configurations+15 ACK,32 отказа структуры
и12 отказов JSON/UTF8,2 JUnit methods passed. Проверяются manifest SHA256,
47 resource hashes/sizes, полные payload/ACK body и исходный envelope SHA256.
Общий runner включён в JVM и Android instrumentation. В Android добавлены2
runtime methods, они выполняются вместе с прежними3 VPN lifecycle methods.
Новый CI gate требует наличия обоих успешных runtime results и публикует notice
с corpus digest; JVM успех сам по себе Android acceptance не даёт.
Manifest: `c97e00ccff7440b09a636a792557c0602aba5eb63815cdc8fefe7755711ac3cd`.
Fixture keys/resources входят только в unit/instrumentation source sets; проверка
основного APK дополнительно запрещает control-v1/ и TEST-ONLY assets.
Android build/lint/emulator CI пока ожидаются. Full Python:462 passed,2 прежних deprecation warnings,9.73s.
Локальная проверка не собирает весь APK: generated native transport library здесь
не подготовлена; полный build и emulator выполняет существующий Clients workflow.

Это verifier checkpoint, не native Stage5 rollout. Нужны protected identity,
journal/floor/previous-hash/outbox/shared ownership, затем application adapter/carrier.
Transcript vectors остаются Python-only. Полная эквивалентность всех возможных
JSON/IP/profile spellings не заявляется: native parser использует bounded integer
и сетевые формы; до ingestion нужен расширенный differential corpus. Android
minSdk26 сохранён; runtime на API35 не заменяет проверку старейшей API26/устройства.
TD-1, AWG3.1 runtime, independent Stage6 остаются открытыми.

## Версии и возврат

Ветка stage5-linux-control-preview, baseline293170a. Android0.1.0/code1,
Desktop0.2.9/catalog8, наблюдаемая installed Linux0.2.8, gateway0.2.1/TCP0.1.0.
Нет установки, публикации, server mutation или main merge. Возврат — checkout
293170a для development; device stores не менялись. Пользовательский телефон
не нужен для текущей проверки протокола, реальные device/network gates впереди.
