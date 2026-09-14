# AWG3.1: управляемое восстановление на стенде — 13.09.2026

После перезапуска серверного engine время до успешного ping снижено с прежних
около16.1с до3.75–3.77с в трёх изолированных прогонах. Это проверка прототипа;
installed client, серверы, signed revisions и release catalog не изменены.

## Реализация

[recovery.py](../../pilot/awg31/recovery.py) отделяет политику от probe/reset/ownership
callbacks. Три последовательных отрицательных probe разрешают повторно применить
закреплённый профиль. Максимум2 reset на один вызов, cooldown10с; в стенде budget20с.
Перед probe и после него проверяются отмена и право владения. Исправное соединение
возвращает health без reset; ошибка reset распространяется, не вызывает скрытых повторов.
Время проверяется между callbacks: это не принудительное прерывание зависшего callback.

Вызывающий код обязан удерживать эксклюзивное владение соединением на время операций.
В isolated lab namespace/процессы принадлежат одному harness; config находится
в приватном каталоге и проверяется по SHA256, engine должен быть жив. Это не
производственная проверка journal revision/expiry. Lease/TOCTOU при нескольких
владельцах должен обеспечить настоящий broker, а не только два вызова authorized().

[lab.py](../../pilot/awg31/lab.py) получает --resilience --managed-recovery.
Сохраняются неверные HPK/H4, MTU, потери1%, TCP integrity, blackhole, link cycle,
server restart и ускоренный rekey. Добавлены healthy control и вызов policy после
восстановления серверного interface/config. Измерение начинается после подготовки
сервера, как и прежний baseline; полный outage с временем запуска службы не измерен.

Engine/tools bytes те же, что experiment2: engine
`e7f00e47d6df853ade5dcd2fe79240f01ff897d75088c768316a444c27c87e0f`, tools
`906d6795af1dd4adee7b11bf1e7fa133d4795c8a8d6e2099b34a026f810a3278`.
Дополнительных изменений криптографии или wire format нет.

## Результаты

| Повтор | Automatic baseline, с | Managed, с | Reset | Probe |
|---|---:|---:|---:|---:|
|1|16.1205|3.7529|1|4|
|2|16.1159|3.7665|1|4|
|3|16.1203|3.7531|1|4|

Baseline взят из предыдущего отчёта при таком же shaped link35ms/20mbit на сторону.
Это небольшая последовательная выборка, не рандомизированный capacity benchmark.
Во всех трёх healthy controls reset0. Остальные сценарии завершились; по1MiB TCP
передано с проверкой содержания. JSON содержит все события, включая наблюдаемую
потерю ping при netem loss; потери не скрываются за общим словом «прошло».

[Тесты политики](../../tests/test_awg31_recovery.py):7 passed. Проверены отсутствие
reset после двух промахов, сброс после трёх, лимит/пауза при длительном outage,
потеря владения/отмена во время probe, исчерпание budget и ошибка reset.
Полный Python:485 passed,2 прежних warnings,10.22с. Docker test-stage:348 passed,
2 warnings,19.46с. Dockerfile.control копирует только policy в tests stage;
production runtime image не получает экспериментальный recovery worker.
[Машиночитаемая приёмка](2026-09-13-awg31-managed-recovery.json).

## Ограничения и следующий шаг

Это вызываемая операция восстановления, а не постоянный health-monitor в приложении.
Reset budget действует на один вызов; production owner должен предотвращать
повторные вызовы, обходящие cooldown. Probe/reset обязаны иметь внешние таймауты.
Временные ICMP сбои не должны становиться единственным production основанием
разрушать рабочую сессию: нужен согласованный health contract и проверки приложения.

Далее встроить policy в настоящий connection-owner lifecycle: проверять committed
revision и expiry, отменять на Disconnect/смене профиля, сохранять routes/journal
и проверять конечный health. Затем1CPU/PMTU/длинные outages и Amsterdam AWG pilot.
H4 сейчас всё ещё восстанавливается старым способом около15с; его ускорение не заявлено.
TD-1, native Windows/Android и upstream Outline integration не закрыты.

Rollback: использовать прежний режим --resilience без --managed-recovery; production
откат не требуется. Synthetic keys/configs удаляются в finally; crash/SIGKILL recovery
самого harness по-прежнему не заявлено.

Параллельно зафиксирован [план собственного транспорта](../own-transport-roadmap.ru.md).
По исходникам остаётся rns==1.5.1 и прямые RNS вызовы identity/envelope/carrier/runtime.
Свой control layer уже развивается, но «Reticulum переписан в самостоятельную
технологию» и «собственный VPN wire protocol готов» не соответствуют текущему коду.

## CI checkpoint

Source c2a95e1a44019a300349f667aaf982b379d60a07 сохранён в рабочей ветке;
12 публичных файлов синхронизированы в основной каталог с проверкой preimage c29ae95.
Linux control preview34761765042/job103735736832 success; phase034761765127
unit/Rust tests103735736923 success. Failover103735737114 остановился на Build
isolated failover stack, до запуска интеграционных сценариев; причина по annotation
только exit1, Log API403. Локальная Docker control build прошла; полный compose build
проверяется отдельно. Начальный отказ сохранён; повтор CI ещё не принят.

CI follow-up: повтор [phase034761940493](https://github.com/Joker20380/family_connect/actions/runs/34761940493)
на1cece64bcbe096fb1d62934505564caee790d90f прошёл: tests103736204560 и
failover103736204445 success. Между попытками изменена только документация;
точная причина первого отказа не установлена, он не объявляется исправленной ошибкой.
Namespace/IPC cleanup подтверждён отдельным осмотром. Full Compose local control
stage также повторно прошёл348 tests/2 warnings/18.86с.

Полная локальная Compose-сборка завершилась success для control и gateway, с
отдельными тегами recovery-compose-check. Сервисы не запускались; рабочие образы
auth2 и запущенные контейнеры не заменялись.
