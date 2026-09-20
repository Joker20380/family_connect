# Linux: один запрос авторизации на операцию — 2026-09-20

Финальный source `7a8036a` опубликован. CI: AWG `35495112337`, TCP `35495112351`,
Client builds `35495112338`, phase0 `35495112340` — in_progress на момент записи.
На предыдущем `761406f` Linux/Windows jobs `35494706323` success; aggregate failure
из-за Android SDK setup. Новый Linux auth-сеанс на хост пока не установлен.


База desktop-ветки:653effa (source3e5943c). После четырёх успешных живых Friends
подключений пользователь сообщил о примерно20 password prompts. Новый код группирует
privileged import/up/down через один pkexec-процесс внутри connection operation.
Сеанс создаётся только при первой привилегированной команде, не при status/fetch.
Отказ блокирует повторную авторизацию до следующего явного действия. Неуспех команды
оставляет сеанс доступным для штатного rollback. Friends journal/owner lease сохранены.

Протокол JSON по приватным inherited pipes: фиксированные пути root-installed AWG/TCP
helpers; только import/up/down; проверка типа/размера и идентификатора. Поле PKEXEC_UID
задаётся из авторизованного процесса, не из запроса; каждый helper повторяет owner check.
Нет shell, пользовательского пути executable, socket или изменения polkit policy.
Сеанс максимум300 секунд/32 команд, helper call максимум120 секунд. EOF закрывает
idle privilege; уже выполняющийся helper заканчивается в пределах timeout. При падении
GUI незавершённую операцию восстанавливает прежний durable journal при следующем входе.
Авторизация для другого пользовательского действия запрашивается снова.

Код сеанса входит в существующий backend.py: шестой/дополнительный файл архива
не добавлен. Оба installers публикуют authorization-session-v1 после установки кода.
Без capability новая операция завершается с требованием обновить helper, без storm.
Metadata writer принудительно задаёт644 для публичных записей и600 для профилей,
независимо от caller umask; шестью тестами проверены077/022/000 и замена файла.

Проверки: full Python648 passed (два deprecation warnings). Первый ограниченный
sandbox-прогон блокировал socket test; вне sandbox тесты прошли.13 новых session tests
используют настоящие pipes/child processes без root/network. Docker AWG3.1 тестирует
root-installed session import/down, передачу UID1000, отказ UID1001, запрет serve и EOF;
также настоящий tunnel /16, bound HTTP, wrong-key cleanup и active installer refusal.
Команда: FC_AWG_TEST_IMAGE=family-connect-amneziawg:3.1-desktop
FC_AWG_TEST_PROTOCOL=3.1 python3 -m scripts.test_awg_gateway — success.
Root-owned TCP networking под новым сеансом требует отдельного installed live check;
обмен AWG/TCP через один сеанс проверен изолированным process test.

CI на базе:Linux AWG35492618670 и Windows AWG35492618745 success;
Client builds35492618663 aggregate failure (Android setup), desktop platform jobs success.
Source761406f: AWG35494706326, TCP35494706324, paired Linux35494706337 success;
Client builds35494706323 и phase0 failure. Нового релиза/подписи/установки в этой сессии нет.
Installed GUI0.2.8; public desktopv0.2.9; Android0.1.18-beta19/code19.
Installed AWG engine e7f00e47d6df853ade5dcd2fe79240f01ff897d75088c768316a444c27c87e0f.

Rollout: после CI сохранить оба root helper каталога; при отключённом VPN установить
оба helpers вместе с backend.py и capability marker, используя один административный
install step; подготовить paired preview из того же source. Затем один ручной Friends
connect/disconnect с проверкой числа диалогов, routes/rules/DNS baseline и journal.
Существующий current GUI не переключать до приёмки preview. Windows live далее.
Новая публичная поставка требует нового immutable version/tag, platform render checks,
скачанных проверенных assets и offline signing с увеличенным sequence.

Rollback: завершить штатный disconnect/recovery; вернуть полные helper каталоги из
backup, включая состояние capability marker, и прежний paired preview/current.
Предыдущий host backup /var/backups/family-connect/desktop-awg31-20260920 относится к
установке AWG3.1 до этой доработки; перед новой установкой нужен отдельный backup.
Не удалять Friends identity/journal и private profiles. Серверы не изменялись.
Открыто: CI новой версии, установка и ручная auth-приёмка Linux, Windows live, RF сеть.

Дополнение: TCP bundle installer также создаёт capability последним как generated file,
включает его в backup/restore.json и откатывает при ошибке daemon-reload. Состав архива
и подпись manifest не расширены. Изолированный check_tcp_bundle.py прошёл: fresh install,
реальный Xray version, mode/root checks, active/tamper refusal, failed reload rollback,
upgrade, private profile preserved, service not started.17 targeted tests passed.
Локальный тестовый архив /tmp/fc-auth-tcp-bundle.tar.gz SHA256
8b55b1350cd5b0dad1b9e3805ed521be261b9c75cbf77efd7dc3719ec5312d0e,
не подписан, не опубликован и не установлен на хост. Follow-up CI требуется.
