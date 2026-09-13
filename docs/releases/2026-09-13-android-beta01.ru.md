# Android beta01: комплект для первого телефона — 13.09.2026

По выбору пользователя Android — первая платформа внешнего теста. Подготовлен
конкретный APK и отдельный ручной WireGuard-профиль для Амстердама. Для первого
технического теста не требуется ждать собственного wire protocol, мессенджера
или AWG3.1. Реальный телефон ещё не проверен; это следующий gate перед расширением круга.

## APK и происхождение

Принятый Client builds run34758085225, Android job103725874969 success; исходник
7ad40c03eb66d34f4698dad1a5a7255cda08992e. Android/pilot/android-awg/android-tcp
не менялись между этой версией и текущим HEAD689aa87. Существующий APK не пересобирался
из непроверенных native blobs. Artifact10318435675 FamilyConnect-Android-debug
скачан через публичный nightly.link, ZIP **сверен с digest из официального GitHub API**:
5a920c650de967f3203d24ed4c7deea963792b19e9121ec65697ef236949cace,93800235bytes.
[CI run](https://github.com/Joker20380/family_connect/actions/runs/34758085225).

Исходный APK189808229bytes, SHA256
119384ac9e5e1615c869c84eb00134b18679f3692f8bab062fa1442600448a66.
Проверены четыре ABI arm64-v8a/armeabi-v7a/x86/x86_64 по assets/awg-build.json,
лицензии и отсутствие peer/control fixtures. Engine — AWG2 pin1cc94272..., не3.1.
Исходная APK v2 подпись прошла; исходный debug certificate SHA256
f15fa6e865520c7f860b970cb0c405cf780f0149086a1079f1f08e3b24b3feee.

Создан отдельный локальный PKCS12 beta-ключ, RSA3072, alias family-connect-android-beta.
Пароль/keystore находятся только в приватных ignored файлах, не CI/Git/server.
Первая попытка apksigner использовала один password file дважды и получила EOF;
подпись не выполнена. Исправлено использованием store password для PKCS12 key.

Финальный **FamilyConnect-Android-0.1.0-beta01.apk**,189816224bytes, SHA256
84223b1ad790cbca6dd1cf9e61e55c334a0e42b505a2779ad3396f633f050ebb.
Beta certificate SHA256 **67a90d1bfcd5a2c0666f0cff1b0ac5e43aaa661ca1196f89e879aa39fe20848a**.
Подписи APK v2/v3 проверены. Сравнены все ZIP entries: отличаются только
META-INF/FAMILY-C.RSA, FAMILY-C.SF и MANIFEST.MF; DEX/resources/native libraries
и остальные META-INF остались теми же. Это переподпись проверенного кода,
а не повторная Android runtime приёмка финального сертификата.

Package com.familyconnect.app, versionName0.1.0/code1, minSdk26/target35,
**debuggable=true**. Это закрытый технический пилот; массовая beta должна иметь
недебажный вариант, increasing versionCode и проверенное обновление тем же ключом.
Иной ранее установленный сертификат может вызвать отказ обновления; не предлагать
безусловный uninstall с потерей старых данных.

## Отдельный доступ и проверка сервера

Добавлен peer **Android beta01**,10.79.0.4/32 и fd79:92::4/128,
public key45RnWEy7fh1o+iSpeqipvwDdGVy30o95HoS12crdJ2Q=.
Server public keyM5HLfjTQHHY3k7K1/4ITv9MUVz0Xtwt+pYn2Oz2wrAw=;
endpoint186.246.45.246:51820, MTU1280, DNS1.1.1.1, full IPv4/IPv6 routes.
Новый client private key создан локально; на сервер передан только public key.

Перед записью проверены runtime/persistent конфликты адреса/ключа. Использованы
flock, backup before-android-beta-01.conf в приватном серверном amsterdam каталоге,
атомарная замена fcams.conf и wg set; проверено сохранение прежних peers.2/.3.
Сервер не перезапускался; firewall, RNS relay, существующий control journal не менялись.
Этот manual peer ещё не является зарегистрированным RNS/Stage5 Android устройством.

check_linux.py теперь принимает --peer-index (default2) и --skip-server-restart.
Для peer4 выполнены gateway ping, DNS, два HTTPS egress (186.246.45.246/NL),1MiB
скачивание, private-network/IPv6 refusal и полное клиентское reconnect+HTTPS.
Результат passed; host routes/rules/resolver сохранены, namespace/interface удалены.
Проверка Linux-сокета подтверждает профиль/сервер, но не Android phone runtime.

## Выдача и следующие шаги

[Инструкция тестировщику](../testing/android-beta01.ru.md). Для первого телефона
выдаются APK и отдельный .conf приватно владельцу; никаких рассылок или публичного
release/catalog/main обновления в этой сессии нет. Другим тестировщикам требуются
свои peer/профиль. Пока не использовать этот профиль одновременно на Linux и Android.

Готово к первому supervised Android smoke: установка, импорт, VPN permission,
connect→IP/HTTPS→disconnect, затем экран/смена сети. После его результата решать
расширение теста. Улучшения AWG3.1/recovery пока в Linux lab и в этот APK не включены.
Далее Android onboarding/protected identity+journal+carrier, schema3.1/native engine,
recovery lifecycle, API26/arm64/device matrix; не обещать дату завершения без этих gates.

Rollback доступа: удалить только peer45RnWEy7fh1o+iSpeqipvwDdGVy30o95HoS12crdJ2Q=
из runtime fcams и соответствующий блок fcams.conf. Не восстанавливать весь старый
backup поверх более новых peers. На телефоне Disconnect, затем удалить только этот
профиль. APK uninstall удаляет локальные данные; его выполнять осознанно.

## Итоговая проверка и сохранённые файлы

Полный Python suite: **485 passed, 2 existing warnings, 9.90s**. Оба операторских
скрипта прошли проверку синтаксиса. Повторный запуск prepare_android_beta.py
с тем же приватным state подтвердил идемпотентность: тот же peer, без дубликата
и перезапуска сервера.

APK, SHA256SUMS, receipt.json и инструкция сохранены локально в ignored
`state-client-build/android-pilots/beta01/`. Приватный профиль первого телефона —
`state-enroll/android-amsterdam-beta-01/Amsterdam-Android-beta-01.conf`.
Постоянный beta keystore и пароль — в приватном
`state-client-build/android-signing/beta-v1/` (каталог0700, файлы0600);
для следующих обновлений использовать этот же ключ. Артефакты скопированы
с проверкой SHA256; приватные файлы в Git не включены.
