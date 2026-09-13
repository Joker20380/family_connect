# Windows Stage5: проверка протокола — 13.09.2026

## Изменение

`Core/ControlProtocol.cs` проверяет domain-separated Ed25519 подпись до расшифровки,
RNS1.5.1 identity ciphertext (X25519, HKDF-SHA256/64 bytes, identity hash salt,
AES256-CBC/PKCS7 и HMAC-SHA256), strict duplicate JSON, schema2, audience/recipient,
signer/WG binding, lease, minimum version и AWG3.1 refusal. Хеш — исходные wire bytes.
`Core/ControlProfiles.cs` отдельно проверяет WG/AWG2/TCP schema2 профили, gateway
binding, локальный WG key placeholder и запрещённые поля. Legacy activation схемы
не переиспользованы: их ограничения и purpose отличаются.
ACK verifier проверяет64-byte public identity/device hash, подпись отдельного domain,
canonical body и ack_id, фиксированные поля/статусы/errors, size4096 и integer types.
Ошибки наружу содержат только category, без ciphertext/plaintext/credentials.

## Проверки

Локальный .NET10 SDK Docker:30 configurations+15 ACK из неизменного corpus;
проверяются47 resource hashes/sizes, полные decoded payload/body и envelope hash.
Дополнительно31 отказ schema2: bool/zero times, lease, version, zero key, duplicate
IDs, loopback/multicast/unspecified gateways, hooks/duplicates/private key injection,
MTU, неполные routes, endpoint binding и prefix. Старые .NET checks прошли:
activation9, catalog6, TCP29 refusals/interoperability/config, AWG16 refusals,
Auto7 lifecycle policy scenarios. Первый runner упал из-за имени expected.digest;
исправлен на manifest envelope_sha256, повтор прошёл. Corpus не менялся.
Полная Python regression:462 passed,2 прежних deprecation warnings,9.89s.
Source581f83fddbce0d31ee52b9152582cc058564c941 отправлен в acceptance branch.
CI Clients34749167169, phase034749166980, Linux34749167086,
AWG34749167185 и TCP34749167035 завершились startup_failure до создания jobs.
Публичная страница Clients сообщает о внутренней ошибке GitHub и рекомендует повтор.
Отдельный Windows verifier34749167304 остался queued на момент проверки.
Ошибка не считается падением тестов, но Windows acceptance отсутствует.
Добавлен pin SHA256 самого manifest, чтобы runner отвергал изменённый/сокращённый
corpus; native45+31 и legacy checks повторно прошли. Следующий push повторяет CI.
[Первый Clients run](https://github.com/Joker20380/family_connect/actions/runs/34749167169).

Manifest SHA256: `c97e00ccff7440b09a636a792557c0602aba5eb63815cdc8fefe7755711ac3cd`.
Scoped `.github/workflows/windows-control.yml` запускает тот же C# runner на Windows;
обычный Windows build.ps1 также уже вызывает Tests.csproj. Test keys подключены
только test project; production main project исключает Tests/**/*.cs.

## Границы и следующий шаг

Это verifier checkpoint, не готовый native Stage5 клиент. Не подключены broker,
RNS carrier, DPAPI identity, journal/revision/previous-hash decisions, outbox и VPN
apply/health/recovery. Три transcript vectors пока выполняет только Python.
Совпадение corpus не доказывает эквивалентность всех возможных JSON/profile spellings:
native parser принимает ограниченные числовые/сетевые формы; расширение corpus и
проверки границ нужны до подключения ingestion. Independent Stage6, TD-1 и AWG3.1
runtime остаются открытыми. Далее Android verifier, затем durable Windows ownership.

## Версии, rollout и возврат

Работа в stage5-linux-control-preview. Desktop VERSION0.2.9, опубликованный catalog8,
наблюдаемая установленная Linux0.2.8, gateway0.2.1/TCP0.1.0 не менялись.
Нет публикации, установки, server mutation или main merge. Для проверки нужен
только test checkout/.NET10; пользовательский Windows PC на этом шаге не требуется.
Возврат — использовать предыдущий checkout57ff244; никакие device stores не менялись.

## Итоговый CI checkpoint

Source `38b055431758e3f2b80de1adfbf9df04cb299fcb`: отдельный
[Windows protocol run34749302222](https://github.com/Joker20380/family_connect/actions/runs/34749302222)
успешен, job103702791743. Официальная notice подтверждает30 configurations+15 ACK
и точный SHA256 corpus. Job запускает также31 structural refusals и legacy tests.
[Phase0 run34749302284](https://github.com/Joker20380/family_connect/actions/runs/34749302284)
успешен. [Clients run34749302204](https://github.com/Joker20380/family_connect/actions/runs/34749302204):
linux:success, android:success, windows:success, release:skipped.
Первоначальные AWG/TCP/Linux-control startup_failure не были повторены отдельным
workflow: их успех на новом source не заявляется. Verifier не вызывается из transport
session; carrier/application changes отсутствуют. Artifact ZIP не скачивался;
доказательство Windows conformance — статус job и official notice, не хеш installer.
CI предупреждает о Node20 actions, принудительно выполняемых на Node24; job успешен.
Машинная квитанция — [windows-control.json](2026-09-13-windows-control.json).
