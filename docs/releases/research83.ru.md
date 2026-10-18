# Частная owner-сборка research83 — установлена, warm-start не принят

`0.1.18-research83-bootstrap`, versionCode83, установлена владельцу in-place
11 октября 2026. Прежние package `com.familyconnect.app.friends`, signer и UID10283;
без uninstall, очистки данных и повторного enrollment. Публичной ссылки и рассылки
тестеру нет; invitation/default download каталоги не изменены.

APK SHA256: `7208a8132e7ae2fb4245e686ecffd80adf4dc67f8bf99af41a9c56cc66c1f7c8`.
Signer SHA256: `67a90d1bfcd5a2c0666f0cff1b0ac5e43aaa661ca1196f89e879aa39fe20848a`.
Source: `f5240994869826c6a28f59e58e38256c688cf6eb`.
Локальный APK: `state-client-build/field65-export16/whitelist-bootstrap-1-continuation/artifacts/EXIT-research83-bootstrap-arm64.apk`.

При контролируемом provisioning503 допустимый cache выбран, seed Family-auth прошёл.
Единственный физический CONNECT завершился ошибкой dedicated carrier до READY;
прикладных full-phase запросов не было. Warm ready NO, cold ready NO, architecture
PARTIAL. Это не доказательство routing leak и не FIELD PASS. Повтора не выполняли.
Итог: VPN OFF, app ON, ChatDeliveryService ON. Не откатывать через uninstall/data
clear; research82 сохранён, безопасный rollback требует отдельного согласования.

[Provenance, временная шкала отказа, известные test failures и cleanup](2026-10-11-whitelist-bootstrap-1.md).
