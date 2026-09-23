# Android bridge и терминальный интерфейс — 19 сентября 2026

## Решение пользователя

Продолжить Android-мессенджер, затем приостановить APK и заняться внешним видом.
Три изображения пользователя задали направление, позднее уточнён Silo/«Бункер».
Оформление репозитория остаётся обязательным этапом после мессенджера;
не смешивать его с дизайном Android и не выдавать HTML-макет за screenshot продукта.

## Изменения исходников

- ChatLocalAndroid: один владелец локального чата на процесс, операции вне UI
  thread, явные create/resume, no-backup directory, запрет создания поверх старой
  истории; ошибки не раскрывают paths/tracebacks. При ошибке close удерживает owner.
- ChatStoreCipher: AES-256-GCM в Java с прежним nonce/tag/AAD форматом Store1.
  Временный входной ключ очищается после копирования, собственный буфер — при close;
  гарантированное стирание всех provider/JNI копий не заявляется.
- Store/LocalChat допускают внешний cipher вместо raw key. Desktop default остаётся
  cryptography; Android не требует cryptography wheel, сохраняет RNS internal backend.
  Chat identity остаётся внутри шифрованного Store/Python; это не VPN identity.
- fc_chat_store.Session: ограниченный allowlist локальных JSON операций; keys,
  packed plaintext, retry tokens и relay blobs не возвращаются. RNS initialize
  использует существующий singleton и тот же путь rns-control.
- PythonRuntimeAndroid сериализует Java startup и для control, и для chat.
- chat-python.gradle копирует только5 явно перечисленных messenger modules;
  репозиторий и private state не включаются в Python source path. LXMF1.1.1 добавлен.
- chat-runtime — отдельный тестовый app com.familyconnect.chatchecks: Keystore,
  запись/закрытие/reopen, повреждение envelope, missing key/database, orphan state,
  двухэтапная приёмка после force-stop. Harness требует один emulator, реальный
  телефон не выбирает. Тестовые APK не предназначены для выпуска.
- Workflow messenger сохраняет Python tests; Android job только ручной input
  android_chat_runtime=true. По текущему указанию пользователя его НЕ запускать.
- TerminalUi применён к MainActivity/FriendsActivity. Маршрутизация, активация,
  connect/disconnect callbacks сохранены. Рамки, статическая фоновая сетка, геометрический
  знак, моноширинные подписи, country/transport picker, круговой статус без процентов.
  Ширина ограничена560dp, кнопки не ниже54dp, текст с переносом, фон без анимационного
  цикла. Индикатор не заменяет текст и исключён из accessibility tree как декор.
- [HTML-макет](../design/terminal-preview.html): четыре вкладки, примерка текста,
  выбор страны/протокола и UI-only сетка/свечение. Помечен как предпросмотр без сети.
  Native chat tabs/settings ещё не подключены; в Android пока переоформлены текущие
  секции. Групп, голоса, вложений, трёх стран в маршруте, security toggles нет.

## Проверки и ограничения

Исходный checkpoint3f6f662dda291cebdba285af6229655c721652a9 + локальные изменения,
включая сохранённые работы предыдущих этапов. Ничего не коммитилось/не публиковалось.
Версия Friends остаётся0.1.7-beta08/code8, прежний документированный Pilot
0.1.4-beta05/code5/revision9; телефон/серверы здесь не проверялись и не менялись.

Последняя live read-only сверка GitHub: Client builds34857790251/sourcef4f320f success;
phase034859397457/source3f6f662 success, предшествующий phase034857790111 failure.
Релизы v0.2.9 и tcp-v0.1.0 от11.09. Это результаты прежнего кода, не этой работы.

Python3.14, RNS1.5.1, LXMF1.1.1, cryptography46.0.7:
-26 focused local/bridge tests passed за0.31s;
-весь messenger:78 passed за68.75s, включая новые10 bridge tests;
-стандартный python -m pytest -q:497 passed/2 FastAPI/Starlette deprecation warnings
 за13.18s. Использованы закреплённые control/provisioning/identity зависимости.

JDK17.0.20.1+1: ChatStoreCipher и ChatCipherChecks compiled/executed, Python/Java
fixture совпал, tampering/wrong AAD/closed cipher rejected. TerminalUi compiled
с Android35 android.jar; ожидаемая deprecated API note для system bar API.
Это не компиляция всего Android приложения и не проверка JNI/Keystore.

Gradle8.11.1/AGP8.9.2/Chaquopy16.1.0: конфигурация изолированного проекта/tasks
passed. Попытка assembleDebug/assembleDebugAndroidTest/lintDebug ДО указания о паузе
остановилась на SDK package/license gate. Готовый APK не получен. Подготовка SDK
через новый command-line tools остановилась с exit126; после пользовательской паузы
не возобновлялась. Python3.10 build environment/native runtime ещё не подтверждены.
Проверить upstream license notice LXMF и фактический состав Python assets перед
будущей сборкой; полноценный APK/четыре ABI этой работой пока не приняты.

HTML отрисован Firefox headless на430px (connection) и360px (chat), проверен визуально.
Временный browser harness на320px:19 checks passed — все вкладки, отсутствие
horizontal overflow, keyboard tabs, country/transport selection, status/disconnect,
message text-only insertion, empty state, grid/glow controls. Это проверка макета,
не Android layouts. Android resource XML parsed; git diff --check passed.

## Rollout, rollback и что осталось

Сборка и установка APK на паузе по прямому указанию пользователя. Не запускать
Android CI, assemble/package или push с автоматическим Client builds до снятия паузы.
Локальные compile-only, Python/JVM и HTML проверки допустимы.

Следующее: визуальный отзыв, продолжение carrier/outbox и настоящих экранов чата.
После снятия паузы — исправить SDK setup, проверить всю сборку и реальные runtime
tests, затем два телефона/Wi-Fi/mobile/Doze/VPN. Только после platform gates и
проверки скачанных артефактов возможны offline signing и распространение.

Серверного rollout нет. Для возврата внешнего вида восстановить предыдущие
MainActivity/FriendsActivity; для возврата bridge убрать native callers/packaging
и вернуть PythonRuntimeAndroid call site к предыдущему control startup. Store1
совместим, ключи/историю/профили не удалять. Не откатывать весь dirty tree: предыдущие
пользовательские работы должны сохраниться. Уже опубликованные версии не заменять.
