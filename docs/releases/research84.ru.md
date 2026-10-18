# Research84 владельца — установлен, warm-start не подтверждён

`0.1.18-research84-provisioning-seam`, versionCode84, установлен in-place
12 октября2026,11:47:34UTC. Package `com.familyconnect.app.friends`, прежний
signer и UID10283. Uninstall/data clear/re-enrollment не выполнялись.
Публичной ссылки/рассылки тестеру нет; invitation/catalog/downloads не менялись.

- APK SHA256: `fd3106170ceeb1e24dad6c8eacda4107b1ab09a6ee120ccf495d92d96841aa48`.
- Signer SHA256: `67a90d1bfcd5a2c0666f0cff1b0ac5e43aaa661ca1196f89e879aa39fe20848a`.
- Source base: `f5240994869826c6a28f59e58e38256c688cf6eb`.
- Source delta: `d7907697d71f119c21bced533f08abae06ae33ef9159c5fd9bd54cf031a481e7`.
- Native ARM64 reused: `cb3af31f62fdc1339df5f03374652ef6c62c4382ed10ef2d314bd6b610c989e2`.
- Локальный APK: `state-client-build/field65-export16/whitelist-provisioning-block-seam-1/artifacts/EXIT-research84-provisioning-seam-arm64.apk`.

В сборке есть private provisioning-only research gate900s/32 operations, отсутствующий
в активируемом виде в public build. Владелец получил точные ранее принятые bytes,
не новую пересборку. Gate после эпизода CLEANED, helpers удалены. Exact selection
и native offline validation PASS до arm; окно физического CONNECT истекло.
Поздний CONNECT после cleanup не доказывает запуск без provisioning.
Отдельно gateway естественно завершился SEED_READ/UNKNOWN и автоматически
сменил invocation/directory. Новый CONNECT автоматически не выполнять.

Последний owner snapshot12:23:09UTC: VPN OFF, app ON, ChatDeliveryService ON.
Не откатывать83 через uninstall/data clear/downgrade; старые artifacts сохранены,
любой будущий rollback требует отдельно разрешённой безопасной процедуры.

[Отчёт и точные границы результата](2026-10-12-whitelist-warm-start-1.md).
