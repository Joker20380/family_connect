# Android APK signing из KeePassXC

24.09.2026 добавлен Linux operator entry point scripts/sign_android_vault.py:
PKCS12 и password из encrypted attachment, обязательный certificate SHA256 pin,
входной APK SHA256, signing/verify через Java apksigner и memfd. Keystore/password
не создаются на постоянном диске и не передаются значениями argv/env. Выходной APK
создаётся только после verify, без перезаписи существующего файла.

Общий binary attachment reader выделен в signing_key.vault_archive; существующие
Ed25519 consumers сохраняют требования к32-byte ключу и public anchor. Во время
regression обнаружен и исправлен importlib loading старого tcp_setup_signature:
в standalone signing sibling loader загружается по __file__; standalone verify
по-прежнему не зависит от него.

65 targeted tests passed: Android vault, signing_key, update/catalog и TCP setup
signature. Реальный disposable KDBX→PKCS12→apksigner→verify прогон выполнен с
одноразовым тестовым RSA key и synthetic APK на базе публичного binary manifest.
Негативные сценарии: иной certificate pin, изменённый member, duplicate/symlink,
неверный APK hash, отказ от перезаписи. Без явно указанного SDK/public fixture
интеграционный Android test skipped; это не утверждение о его запуске в CI.

Настоящий Android keystore/password прочитан из локального KeePassXC: private key
соответствует сертификату и fingerprint опубликованной beta50. Проверка без подписи;
production APK не подписывался/не выпускался, vault и plaintext originals не менялись.
Клиенты остаются Android0.1.18-beta50/code50, Linux0.2.10, Windows0.2.13.

[Runbook и команды](../android-vault-signing.ru.md). Новый entry point готов для
следующего принятого выпуска; внешние старые release helpers не переключены
автоматически. До удаления originals нужны принятая production signing operation
и независимый внешний backup. Выход тестового APK не устанавливался на телефон.
Откат — вернуть прежние scripts; серверы/клиенты/базы не менялись.

Следом по секретам — актуальность трёх локальных SQLite и active/legacy state,
завершение реестра потребителей/ротации и внешний носитель. Полный clean-machine DR
и возврат к5.3а/device acceptance остаются в глобальном плане.
