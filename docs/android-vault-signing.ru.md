# Подпись Android APK из KeePassXC

Linux operator tool: [scripts/sign_android_vault.py](../scripts/sign_android_vault.py).
Общий reader: `scripts/signing_key.py:vault_archive`; Ed25519 issuers сохраняют свои
проверки32-byte key и public anchor. Root/signing secrets не передаются на серверы/CI.

## Входы и ограничения

В encrypted `recovery.tar.gz` требуются PKCS12 keystore и однострочный password,
а также PRIVATE-INVENTORY.json с точными path/size/SHA256 каждого member.
Поддерживается один подписант с общим паролем контейнера и private key; JKS,
раздельные пароли, key rotation/lineage и несколько подписантов не реализованы.
Обязателен заранее известный SHA256 сертификата: получать его из принятого release
receipt или доверенного APK, не из предлагаемого неизвестным источником keystore.

Master password вводится через локальное окно или скрытый TTY. Общий reader требует
owned regular KDBX0600 без symlink/hardlink, ограничивает16MiB и экспортирует binary
attachment в memfd. Проверяются manifest/digests, PKCS12 password, private/public key
pair и fingerprint сертификата. Значения не входят в argv/env/вывод инструментов.
Архив ограничен16MiB/1024 entries; запрещены duplicate и symlink у выбранных members.

`apksigner` запускается как доверенный локальный Java jar. Keystore/password/input
snapshot/output передаются через memfd; постоянный plaintext export отсутствует.
Входной APK обязан совпасть с операторским SHA256, лимит256MiB. V4 sidecar выключен.
Готовый APK проверяется apksigner verify и по единственному certificate fingerprint,
только после этого создаётся выходной файл0600, исключительно с новым именем.
Это не замена zipalign, проверке build provenance, package/version/ABI и приёмке CI.
Публикация/установка/подпись update catalog не выполняются этим инструментом.

## Проверка ключа без подписи

Пример с условными путями и именами из закрытого inventory:

```bash
python -m scripts.sign_android_vault \
  --vault /private/operator.kdbx --vault-entry 'GROUP/ENTRY' \
  --keystore-member signing/release.p12 --password-member signing/password \
  --certificate-sha256 EXPECTED_CERTIFICATE_SHA256 \
  --vault-password-dialog --check-only
```

Для подписи убрать `--check-only` и добавить:

```text
--apk /private/verified-unsigned.apk --apk-sha256 EXPECTED_APK_SHA256
--output /private/new-signed.apk
--java /trusted/jdk/bin/java
--apksigner-jar /trusted/android-sdk/build-tools/VERSION/lib/apksigner.jar
```

До подписи выполнить release gates проекта, скачать и проверить CI artifacts,
проверить alignment/package/version и неизменность принятого входного SHA256.
Не переподписывать опубликованную версию другими байтами и не менять release tag.
После подписи сверить APK, сертификат, страницу/каталоги и обновление поверх старой
версии по обычной процедуре выпуска. Тестовый ключ не использовать для реального
обновления телефона: Android отклонит другую identity подписанта.

При ошибке password/pin/hash/подписи операция отказывает с подавлением private
сообщений. Существующий output не перезаписывается. После ошибки записи на диск
не считать возможный неполный выходной файл принятым артефактом. Подписанный APK
публичен, исходный keystore/password остаются приватными. Core dumps отключены;
root/скомпрометированная ОС/память и swap остаются отдельной границей защиты.

## Проверки и статус миграции

`tests/test_android_vault_signing.py`: PKCS12/pin/manifest/tamper/path/duplicates;
дополнительный реальный KDBX→apksigner→verify прогон использует одноразовый RSA key,
synthetic APK с публичным binary manifest. Для него задать FC_TEST_JAVA,
FC_TEST_APKSIGNER_JAR и FC_TEST_APK (публичный APK только как источник manifest).
Без SDK/fixture этот интеграционный тест skipped; базовые проверки выполняются в CI.
Производственные данные не участвуют в CI и тестовые ключи не коммитятся.

24.09 реальный integration прогон passed; настоящий Android keystore прочитан
из vault и проверен по сертификату выпущенной beta50 без подписи. Новый production
APK не выпускался. Старые локальные release helpers автоматически не переписаны:
следующий выпуск должен использовать новый entry point. Оригиналы пока сохранены;
удаление возможно после принятой production операции и независимой резервной копии.

Формат `file:` password source и verify описаны в
[официальной документации apksigner](https://developer.android.com/tools/apksigner).
