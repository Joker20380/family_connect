# Research82 — закрытый кандидат непрерывности lease

Версия `0.1.18-research82-lease`, code82, пакет `com.familyconnect.app.friends`.
Номер зарезервирован после проверки owner81, сохранённых резервов и public tags.
Собран и установлен in-place только у owner; публичной ссылки/рассылки нет.
APK SHA256 `c84060e715c0f128e939cc90ca2cbc5225887325b20ba60f89d5a9354ea36b18`.
Source/native commit `fbbecb81c033557f6c29819a02b8382519465961`; прежние package/signer.
Публичные загрузки и версия invitation не изменены.

Authenticated renewal использует текущие Family/Mux session и admission holder;
expiry, revocation и обязательные security deadlines остаются включены. Локально
с управляемыми часами один TCP socket проходит две границы lease. Непрерывность
на Telemost проверена частично: два renewal и11 HTTPS после обеих прежних границ.
Старый TCP socket прошёл первую границу, затем assertion170 завершился ошибкой,
без переоткрытия; точная причина UNKNOWN. Полная бесшовность не доказана.
Startup-refresh, recovery, UI, обычные
транспорты и publisher identity сохранены.

См. [приёмку и оставшиеся этапы](2026-10-11-telemost-lease-continuity-1.md).
Шесть исторических diagnostic assertions остаются отдельным известным issue.
Публичный release, рассылка APK и Краснодарский FIELD не выполняются.
Итог: VPN OFF/ChatDeliveryService ON, helpers удалены, cleanup restart0; повторов нет.
