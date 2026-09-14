# Android beta02: следующий этап устойчивости — 13.09.2026

После пользовательской приёмки звонков WhatsApp/Telegram в МТС Владикавказ и
домашнем Ростелекоме следующий gate — сон экрана и смена сети. Сервер AWG3.1 и старый APK0.1.1-beta02/code2 сохраняются;
после уточнения пользователя подготовлено отдельное обновление beta03 ниже.

Добавлен ManualAwgStabilityTest в androidTest с синтетическим профилем. Проверяет
исходный зашифрованный IPv4/IPv6 UDP echo, выключение дисплея (PowerManager),
5s с выключенным экраном, трафик после пробуждения; блокировку UDP fixture
с подтверждённым timeout,20s outage и echo после восстановления за бюджет30s;
затем Disconnect во время повторного outage и отсутствие VPN после возврата сети.
Секретов production и внешних серверов в этом тесте нет.

Это ограниченная эмуляторная приёмка:5s screen off не равны5min сна/Doze или
MIUI battery policy. UDP blackhole не равен смене мобильного/Wi-Fi интерфейса.
Пользователю запрошен отдельный5min lock + Wi-Fi→MTS→Wi-Fi тест на beta02.

Исходники runtime показывают: manual ConnectionService устанавливает on после
engine.up; VpnHealth применяется только вAuto. Поэтому status on сам по себе
не подтверждает рабочий интернет; тесты обязательно проверяют реальные пакеты.

Компиляция и CI нового теста выполняются. В workflow добавлен bounded JSON summary
результатов instrumentation (существующий report_ci.py), включая failures и
ограниченные диагностические сообщения без production profiles.

Откат: изменения только tests/workflow/docs; установленный APK, peers, firewall и
службы не изменены. После приёмки — оформить результаты физического телефона и
решить, нужны ли изменения recovery/health; не внедрять reconnect без доказанного сбоя.

## Уточнение объёма: beta03 health feedback

Пользователь находится вГенте и отложил физическую проверку российского телефона;
попросил продолжить улучшение системы. В исходники0.1.2-beta03/code3 добавлены
периодические VPN-bound DNS probes и в manual mode: отдельный статус «VPN отвечает»
или «Нет ответа через VPN». Потеря DNS не останавливает/не перезапускает ручной
туннель. Auto сохраняет прежнюю политику fallback; manual наблюдает тот же транспорт.
Существующий cancel закрывает активный probe socket и отменяет расписание.

Кнопка внешнего IP теперь использует Network.openConnection для текущего VPN,
проверяет session generation до/после HTTP и при обновленииUI. Результат старого
сеанса после Disconnect/reconnect не принимается; обычная сеть не используется
как fallback. DNS response подтверждает прохождение DNS через VPN, но не гарантирует
работу всех сайтов/мессенджеров. Настоящий handover/Doze по-прежнему не принят.

Manual stability test дополнен проверкой health ok→unavailable→ok приUDP outage,
сохранением туннеля во время ошибки и сбросом health приDisconnect. Перед выдачей
нового APK нужны JVM/lint, emulator acceptance, проверка ARM64 packaging/signature.

## Итог beta03

Исходник63831305f063350fd21af44c93d6a8bef122b795. Локально JVM30, lint и
компиляция instrumentation прошли. Client builds34776015693: Android103774142634,
Linux иWindows success;6 instrumentation cases прошли без skips/failures.
[Платформенная приёмка](https://github.com/Joker20380/family_connect/actions/runs/34776015693).
Новый ManualAwgStabilityTest подтвердилhealth ok→unavailable→ok, сохранениеVPN
во время ошибки,5s screen off и успешный трафик после wake;≥20s UDP blackout,
возврат6 encryptedIPv4/IPv6echo за7ms в локальной fixture, Disconnect остаётсяoff
после возврата сети.7ms — не показатель восстановления на МТС/Ростелекоме.
Проверена неповторяемость sessionId после пересоздания Android service.
Session counter общий на процесс; instance generation отдельно защищает callbacks.

Artifact10324116069,93980194bytes, официальный ZIP digest
ea37765eb126790bd3945f3f38fc82213ad6b8287ce419f75151c63c521d946d сверён.
Native4ABI hashes/fixtures/licenses проверены; исходная CI подписьv2 валидна.
ARM64 упакован из принятого payload прежним package-arm64.py, retained entries
сверены побайтно. ИтоговыйAPK `FamilyConnect-Android-0.1.2-beta03-arm64.apk`:
51154127bytes, SHA256 **c6bb7df99d55a53a8da0d7fb9f177855976d91c6cf8b8bb1adf1fb652399649a**.
Подписиv2/v3,16KiB alignment,packagecom.familyconnect.app,version0.1.2-beta03/code3,
ARM64/minSdk26 проверены. Сертификат прежний beta01/beta02:
67a90d1bfcd5a2c0666f0cff1b0ac5e43aaa661ca1196f89e879aa39fe20848a.
Это debug technical pilot; ARM64 physical battery/Doze/handover пока не приняты.

APK/receipt/README/SHA256SUMS сохраняются в ignored
`state-client-build/android-pilots/beta03/`. Существующий профиль beta02 используется
повторно. [Инструкция](../testing/android-beta03.ru.md). Серверные настройки и
ключи не менялись. Для rollback UI поведения нужен новый APK с большимversionCode
или осознанное управление downgrade; не рекомендовать удаление приложения.

## Отдельный незавершённый CI риск Reticulum

phase0 run34776015673: tests success, failover103774142082 failure на сборке
control image. Runtime failover/auth/offline/revocation не запускались, cleanup
Docker success. Публичный build.log доступен через nightly.link artifactphase0-failover;
теперь причина известна: Docker test-stage347 passed/1 failed, test_extracted_preview
вложенно запустилRNS lifecycle, где initial CONTROL_CHALLENGE исчерпал15s deadline.
Не ошибка Android compilation и не подтверждённое следствие данного Android patch.
Локальный focused повтор extracted-preview+real-RNS:2 passed/6.22s. Это не доказательство
исправления; timeout не увеличивался и тест не отключался. Серверныйcontrol code
не менялся. НестабильностьReticulum остаётся отдельной задачей диагностики;
не заявлять полную зелёную приёмку всех подсистем по этому запуску.
