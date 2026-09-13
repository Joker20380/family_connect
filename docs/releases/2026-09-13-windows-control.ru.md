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
Windows runtime CI и full Python regression ожидаются на source checkpoint.

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
