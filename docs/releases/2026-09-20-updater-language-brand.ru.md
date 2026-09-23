# Android updater, family_connect, язык и компактный экран — 2026-09-20

## Итоговые версии

- Android **0.1.18-beta35 / code35 / ARM64**; пакет com.familyconnect.app.friends,
  отображаемое имя family_connect. APK 36407372 bytes,
  SHA256 fd7cc8ca00ca95acd4cc2cf5cc265d6afd46d39a4a21d22374e14f1f915a3a4e.
  Подпись прежнего beta-ключа: 67a90d1bfcd5a2c0666f0cff1b0ac5e43aaa661ca1196f89e879aa39fe20848a.
- Linux **0.2.9 preview / source a6c68fe**,
  bundle146d221d0ad23c07039519a6f7b4d7f8222eb175b53f84b04386b5a22ab5df1d,
  архив116694 bytes, SHA256 c49549cc68ccaff20bd8ace02abcdbf47bb3638a7cbb31ae3c74bce69327f75c.
- Windows **0.2.9 preview / a6c68fe95fefc30358b41664fd18ffb68234013b**,
  FamilyConnect-Setup-0.2.9-preview-a6c68fe.exe,49930325 bytes,
  SHA256 37879242f1a742c35f3702d0373220b91d4138b48c2ccc643e7bbcfd639888ce.
  Неизменяемый GitHub tag desktop-preview-20260920-a6c68fe,
  distribution run35508704891 success. Физический Windows-ПК недоступен.

## Поведение

В шапках и пользовательском названии приложения — family_connect. Android/Linux
используют системный monospace, Windows — Consolas Regular. Идентификаторы пакета,
служб и данные активации сохранены. Windows installer сохраняет AppId и каталог,
обновляет отображаемое имя/ярлыки, удаляет только прежние Family Connect.lnk.
Linux обновлены оба прежних desktop aliases, прежний значок сохранён.

Android: Настройки → Язык → Системный язык / Русский / English. Выбор сохраняется
в appearance preferences и применяется через общий LocalizedActivity ко всем
четырём Activity; смена языка не переключает VPN. Linux/Windows: явная кнопка
«Язык: Русский → English» / «Language: English → Русский»; выбор теперь сохраняется
в ~/.config/family-connect/ui-language (или XDG_CONFIG_HOME) и HKCU\Software\family_connect,
Language соответственно. Layout/smoke проверки не читают и не пишут пользовательский выбор.

Круг Android ограничен примерно половиной ширины экрана; на низком экране он
дополнительно уменьшается, сохраняя навигацию. Нижняя область: слева график трафика
приложения, справа сервер, протокол и состояние VPN. Два нижних блока получают равные половины доступной высоты
с общим отступом8dp, таким же, как между верхним блоком и телеметрией. Отдельная строка страны/протокола убрана
из главной страницы как дублирующая новую колонку. UID-трафик относится ко всему
приложению, а не только VPN. Значения IP/пинга не выдумываются и не запрашиваются.

## Обновление Android

Настройки → Проверить обновления → Скачать обновление → Установить обновление.
Ручная проверка, без фонового поиска/скачивания. Отмена скачивания, прогресс,
ошибки сети/проверки; установка блокируется, пока VPN этого приложения включён.
Если требуется, открываются системные настройки разрешения установки из приложения;
после возвращения пользователь снова нажимает «Установить обновление».
Установка подтверждается Android; данные не удаляются.

Каталог: https://185.251.89.19:8443/updates/android-friends.json, HTTPS/no-store.
Он отдельный от подписанного desktop update catalog. Метаданные Android не подписаны
offline release key: доверие к обнаружению обеспечивает HTTPS, а APK дополнительно
сверяется по размеру, SHA256, package name, versionCode/versionName и сертификату
установленного приложения; системный установщик также проверяет подпись APK.
GET_SIGNING_CERTIFICATES на API28+, GET_SIGNATURES на API26–27; поддерживается
тот же одиночный signer, смена ключа этой реализацией не разрешается.
Клиент отклоняет неподдерживаемый ABI, чужой origin/path, большие ответы/файлы,
повреждённый/обрезанный APK, чужой пакет/сертификат, ту же или более старую версию.
HTTPS redirects запрещены, connect/read timeout10s; metadata≤8192B, APK≤150MB.
Проверенный APK хранится в private cache; неэкспортируемый provider выдаёт только
точный update-<sha256>.apk по временному read URI grant, не произвольные файлы.

API: https://developer.android.com/reference/android/content/pm/PackageManager
и https://developer.android.com/reference/android/content/Intent#ACTION_INSTALL_PACKAGE.
Сквозное обновление новой версии через системное окно ещё не подтверждено:
новые bootstrap-сборки ставились через adb -r. Проверены настоящее HTTPS-скачивание,
валидация APK, provider и UI; ручной install consent остаётся проверкой следующего обновления.

## Проверки и состояние исходников

Android:147 JUnit tests passed, lint0 errors; сборка Python3.10/ARM64, ABI/payload,
zipalign и постоянная APK-подпись проверены. На beta30 восемь device tests passed:
настоящая загрузка публичного APK и checksum, отказ чужому сертификату (тот же пакет,
отдельный одноразовый тестовый ключ), downgrade/повтору и повреждённому архиву,
provider traversal/write, живая кнопка проверки, сохранение языка, layout, dial clicks.
147 unit пройдены на beta32, после менялась компоновка UI.
На beta35 прошли пять device tests: dashboard native/320×512, dial, язык и две проверки карты.
Первый прогон layout ошибочно проверял подложенное главное окно вместо диалога маршрута;
выбор окна исправлен, повтор прошёл. 147 unit tests без ошибок, lint/сборка passed.
Ранее beta28 прошла те же пять updater tests и проверки языка/layout (7 total).
Тестовый APK с чужой подписью не устанавливался и удаляется после проверок.
Исходники/хеши/локальные результаты: state-client-build/android-pilots/beta35/.
Android source остаётся в исходном рабочем дереве с прежними Android/chat изменениями,
не перенесёнными целиком в scoped desktop branch; desktop source SHA не описывает APK.

Linux:24 layouts passed, четыре страницы отрисованы в dbus/Xvfb, просмотрены
новая шапка и настройки. Первый прогон с default1024px виртуальной высотой дал
focus failure на1.5x; с предусмотренным CI экраном2560×2160 весь прогон прошёл.
Linux control CI35508127389 success.
Windows: Client builds35508127354 windows/linux jobs success; Android setup job
этого desktop branch отдельно failed. UI35508127345 success, PNG просмотрен;
AWG35508127347 success; TCP35508127340 success. Общий phase0 workflow не зелёный;
это не заявление о прохождении всех проверок репозитория.

## Развёртывание и откат

Linux установлен; receipt state-client-build/linux-brand-20260920/installed.json,
unit family-connect-brand-20260920. После отключения VPN/закрытия GUI откат desktop
aliases из *.previous того же каталога вернёт bundle3ef22e124f177f82; данные не удалять.
Android beta35 установлен поверх прежних версий, SHA/версия сверяются с receipt.
Откат Android без удаления данных — исправленная сборка с большим versionCode и тем
же beta-ключом. Системный downgrade с удалением данных не применять.

Новые публичные файлы опубликованы из config/brand-platforms-20260920 на RU-host.
До переключения страница содержала beta27/Linux3ef22e/Windowsa1be617;
предыдущие immutable URL сохраняются. Опубликованы beta35/Linux146d/Windowsa6c68fe
и catalog Android code35 (финальная поправка из config/map35-20260920). Откат страницы/locations — config/*.before-brand-platforms-20260920,
nginx -t -c /etc/fc/nginx.conf и HUP только family-connect-product-https.
Android discovery введён deploy/friends/install-android-update.py; initial nginx
backup *.before-android-update-26, предыдущий catalog при code35 сохраняется как
android-friends-update.json.before-android-update-35. Restore каталога не понижает APK
на телефоне. Desktop signed catalogs и offline release key не менялись.

Остались проверки физического Windows, российской сети, Android system-install consent
и API26–27 устройства. Глобальный этап4 продолжается; независимая доставка конфигураций
и серверное автоматическое масштабирование этим выпуском не реализованы.

## Карта в нижней области

На Android добавлен компактный переход к маршруту с точечной картой суши.
Рамка мини-карты общая TerminalFrame со срезанными углами; пропорции карты сохраняются.
Пустая служебная строка между панелями устранена; сообщения об ошибках отображаются
в верхнем блоке только при наличии текста. Начало маршрута изображается точкой вместо прямоугольника и подписи телефона;
конечная точка и линия сохранены. Исходная точка только из свежей разрешённой
foreground-геопозиции, координаты не сохраняются. Без разрешения маршрут не выдумывается.
На коротком экране мини-карта скрывается, навигация остаётся доступной.
Мини-карта статичная, без дополнительного анимационного цикла; полный экран сохраняет
масштабирование и clipping. Выборка геопозиции прекращается при уходе с экрана.

## Следующая задача: увеличение NL VPS

Пользователь рассматривает увеличение ресурсов 186.246.45.246 и сообщает о порте
«до 1 Гбит/с». Это не подтверждение гарантированной пропускной способности.
Прежние 200 Мбит/с остаются лишь оценкой по общим условиям; требуется уточнить,
относится ли 1 Гбит/с к этому тарифу. Мониторинг пока не перенастроен.
Апгрейд/перезагрузка/оплата не выполнялись. Перед апгрейдом: независимый backup,
подтверждение сохранения IP/диска у провайдера, проверка autostart, после — health.
Бесшовный межсерверный failover ещё не принят; краткий разрыв при reboot ожидаем.

Финальный откат страницы beta35 → beta32: config/*.before-map35-20260920;
каталога — android-friends-update.json.before-android-update-35. Старые APK неизменяемы.
Промежуточные beta33/34 были только на телефоне; публично после beta32 вышла beta35.
