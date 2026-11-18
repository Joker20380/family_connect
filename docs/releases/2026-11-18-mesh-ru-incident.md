# OPS-MESH-RU-20261118 — текущая остановка MESH и RU transport

**DIAGNOSED / NOT_RECOVERED.** Read-only сбор18 ноября2026,12:00:01–12:18:40UTC
(13:00–13:18 Brussels). Последний прямой RU readback12:14:42, NL12:12:43/50,
панель12:14:57;12:18 выполнены только проверки publisher prerequisites.
Никаких перезапусков, reset-failed, enable/unmask, deployment, очистки состояния,
изменений authority/paid/таймеров или действий с клиентами не выполнено.
[Машиночитаемый обезличенный receipt](2026-11-18-mesh-ru-incident.receipt.json).

## Ответ пользователю

Это **не штатная доступность VPN** и не просто устаревшая панель. Обе MESH-службы
Amsterdam действительно остановлены. Обычные RU AWG/TCP также остановлены;
кроме того, обнаружен остановленный RU HTTP candidate. Штатным является только
отсутствие MESH bootstrap на управляющем RU: сейчас unit **not-found**, а не
работающий NL gateway, который требуется запустить на RU.

Установлены **две разные причинные цепочки**:

1.17 ноября общий renewal остановился на `STALE_NODE_STATE` после acquisition
всех трёх узлов. RU quiesce остановил HTTP; recovery/fence остановил оба NL MESH.
Затем материалы истекли. Это **не** повтор сценария5–6 ноября
«сначала expiry gateway, затем restart limit»: нынешние NL завершились штатно
по stop/SIGTERM примерно за75 минут до expiry, без исчерпания restart limit.
2.18 ноября RU watcher превысил8s operation budget на `file_fsync(decision_state)`.
Защитная остановка AWG/TCP началась до завершения watcher с exit1. Инициирующий
сбой — не12s systemd watchdog. Причина столь долгого fsync ниже приложения UNKNOWN.

Общий storage/provider виновник для этих цепочек **не доказан**. HTTP/MESH относятся
к одной renewal-операции; RU AWG/TCP остановились отдельно, примерно5ч08мин позже.

## Узлы, роли, последствия и минимальное восстановление

Все времена в таблице UTC. `bootstrap` ниже означает именно
`family-connect-restricted-bootstrap.service`.

| Узел / ожидаемая роль | Фактическая служба | Первое событие | Причина / граница доказательства | Затронутый путь | Минимальное восстановление |
| --- | --- | --- | --- | --- | --- |
| nl-amsterdam-1 / MESH gateway | bootstrap loaded, inactive/dead, disabled, PID0 |17.11 20:41:06.786 | SIGTERM/CANCELLED, success/exit0, recovery fence общей операции; не expiry | MESH Amsterdam1 | Сначала согласовать застрявшую операцию без rollback БД, свежие credentials/directory, затем штатный start и traffic gate |
| nl-amsterdam-2 / MESH gateway | bootstrap loaded, inactive/dead, disabled, PID0 |17.11 20:41:11.029 stop;11.040 exit | Та же операция/fence, success/exit0; не reboot/restart-limit | MESH Amsterdam2 | Та же трёхузловая процедура; не независимый restart второго узла |
| gateway-ru / control/issuer | bootstrap not-found | Не событие отказа этой роли | На управляющем RU MESH gateway не требуется | Самостоятельного RU MESH пути нет | Не устанавливать/enable bootstrap для исправления строки панели |
| gateway-ru / control HTTP | family-connect-friends-http-candidate.service inactive/dead, PID0 |17.11 20:41:01.851 stop | Общий renewal quiesce; exit signal15, Result=success; сохранён services-before=active | HTTP candidate/API/provisioning, не проверенный end-to-end в этой фазе | Только после корректного терминального состояния renewal и свежих материалов; не обходить ownership ручным start |
| gateway-ru / ordinary AWG/TCP | friends-awg/friends-tcp inactive/dead, PID0; paid-watch перезапускается |18.11 01:49:35.102 first failure |8.548s fsync;8.598s/8s operation deadline → защитный stop; нижележащая причина задержки UNKNOWN | Обычные RU AWG/TCP | Fresh backup/restore, RU-only fence/drain, coordinated watcher/AWG/TCP stop/PID0/start на прежних bytes, leases/readback/реальный traffic |

На обоих NL обычные AWG/TCP и paid-watch active/running, NRestarts0.
На NL1 Reticulum и mailbox также active: это другие службы, не доказательство MESH.
Новых transient room workers не запускали. Реальный VPN-трафик этой фазой не проверялся.

## Панель, mapping и реально установленные версии

Canonical mapping подтверждён **из установленного collector панели**:
`gateway-ru=185.251.89.19`, `nl-amsterdam-1=185.10.158.212`,
`nl-amsterdam-2=185.10.158.196`. `gateway-nl` — архив с host=null, не опрашивался.
Существующий `inventory-known_hosts-20261103` содержит pins всех трёх адресов;
SSH использовал StrictHostKeyChecking=yes, BatchMode и ConnectTimeout7s.

Панель: image `sha256:5ae92f8c7775d2ff0ad26627f6cdfcda53a3d4193a08b9fe1de1e89f32c432da`,
контейнер запущен15 ноября13:53:01UTC. В установленном `/app/control_plane/apps/console/objects.py:26`
`MESH · bootstrap` точно сопоставлен с `family-connect-restricted-bootstrap.service`;
hash модуля `3ebdd74f313e8952b7255ea6e743bbbe9103cdb820a6b7f555f0870cf22a19ed`.

| Источник | Последний inventory observed_at | imported_at | Последняя сохранённая collection attempt / importer | Transport snapshot |
| --- | --- | --- | --- | --- |
| RU |18.11 12:14:26.083 |12:14:27.671 |12:09:27.873 / IMPORTED, error=null |12:14:26 unavailable; attempt12:14:27.660 |
| NL1 |18.11 12:14:28.686 |12:14:29.925 |12:09:31.398 / IMPORTED, error=null |12:14:28 ok; attempt12:14:29.923 |
| NL2 |18.11 12:14:30.789 |12:14:32.067 |12:09:33.540 / IMPORTED, error=null |12:14:30 ok; attempt12:14:32.065 |

Collection receipt прочитан отдельно12:10:32, цикл завершён12:09:38.691;
это не время последнего наблюдения панели12:14. Ошибок importer в этом сохранённом
цикле нет. RU `transport=unavailable` — результат источника, не сбой импорта.
Inventory служб панели совпадает с direct readback: NL bootstrap inactive,
RU AWG/TCP/HTTP inactive, RU bootstrap not_found. Успешный импорт не означает
доступный VPN; user monitor inactive/dead между запусками с active/waiting timer штатен.

`origin/main` получен обычным fetch и проверен:
`bc8f7b5b42800269aeb43bcf54059205e7a7cbf7` (PR44 merged). Старые записи upstream
«PR44 draft/no merge» — устаревший source checkpoint. **observations-v1 NOT_DEPLOYED**:
установленный RU archive вообще не содержит `observations-v1`/`readback_mode`,
configuration не содержит readback_mode; действует legacy.

| Проверенный runtime | SHA256 |
| --- | --- |
| RU paid-transport.pyz | `125c796a30c3fba1772c47b96963517350087ad04aad675b6f33a31a5383276c` |
| RU awg-gateway.py | `9023d2c3f7c3a5127d67c509a16eb2d974810ff54d5b76cc225cd9b93e0b4234` |
| RU watcher effective unit, точные bytes systemctl cat | `659b954beb67d1e23c0cea45ffda62704f48dc2fb0b1f5bd30d0ae733760bd4e` |
| RU HTTP | `4e2df679761ba9e7af74128984ef2e19e8e7b228f1cc85b36d50be2b0bc24ce8` |
| RU operator | `19efd0b46fb145dcef06a9a092ee0d8ee4d062d09d99b1b0e0065425be02d90f` |
| RU reconciler | `ff4601aa3bb0990b4f8566aadde1fd6b12120bffbd912b4b901e2d77a114d6aa` |
| Оба NL MESH gateway | `70e6c0fc1b920ad308e24667be94f674c34979dab6aa518e1a8194fff7c131b6` |

Полные systemd свойства, unit/drop-in hashes, boot IDs, PID/invocation и runtime
метаданные сохранены в receipt. RU загрузился1 сентября12:13:26UTC
(uptime -s показал15:13:26 MSK), NL1 —30 октября19:10:24UTC,
NL2 —1 ноября23:16:36UTC: нового reboot перед этим отказом нет.
Оба bootstrap по-прежнему boot-disabled; это не причина текущего stop.
Текущий systemd уже не удерживает исторические NL PID/timestamps/invocation:
пустые поля не заменены выдуманными значениями. Хронология восстановлена из
совпадающего durable fatal receipt NL1 и конкретного journal-файла NL2.

## Общий renewal: точная граница отказа

Операция `scheduled-1794948040-548f317346ab83ca`:
`RECOVERY_REQUIRED`, `first_cause=STALE_NODE_STATE`,
`acquired=[RU,NL,NL2]`, `quiesced=[]`, `commit_decided=false`.
Все три owner.json сохраняют **ACQUIRED этой же операции**.
RU staging отсутствует; plan.json координатора относится к предыдущей операции
`scheduled-1794938131-169c64e040fdfb9a`, не является планом текущей.

20:40:39.839 — запуск scheduled service;20:41:01.851 — stop HTTP;
20:41:06.786 — NL1 SIGTERM;20:41:11.029 — NL2 stop;
20:41:20.352 — первый сохранённый service receipt STALE_NODE_STATE/RECOVERY_REQUIRED,
20:41:20.537 — exit75. Installed `quiesce()` сначала останавливает readers,
затем сравнивает inspect с acquired expected_state. Первый quiesce — RU;
пустой quiesced при полном acquired локализует отказ до завершения этого шага.
Recovery выполняет fence других owners: поэтому остановились оба NL, хотя их
профили не менялись. При остановке NL1 оставалось4492s до credential expiry;
exit_path=signal, fatal=false, first_cause=CANCELLED, cleanup completed,
invocation совпадает с systemd receipt. Provider/signaling failure не записан
как причина этого exit; NL2 journal также показывает управляемый успешный stop.

Свежая read-only SQLite-проекция отличается от acquired database digest.
Issuer обоих шлюзов, CRL, admission/anchor/node config и canonical NL profiles
совпадают с acquired hashes. Это подтверждает текущий DB drift, но **не называет
строку/писателя в момент первого сравнения**: того point-in-time diff нет.
Нельзя приписать событие paid-controller, пользователю или диску без доказательств.

Leaf и CRL обоих NL:17 ноября17:55:59→21:55:59UTC, CRL27372.
Directory NL1 истёк21:56:29.405, NL2 —21:56:31.480.
Authority certificate действителен до16 января2027 22:36:48UTC; менять authority
ради expired leaf не требуется. Сейчас leaf/CRL/directory просрочены у обоих.

Serialization interlock **установлен**, SHA256
`9a0df90fbfe461f3e826d31bb9124b4c3dc50d2ecac273c927ff14c9bc238353`;
действует `zzzzzz-serialized-directory.conf`, hash
`e423fe1ca218e6a065055967fedcc1be94ec47a7fb58699b2f59a46efb4370af`.
Он приостанавливает directory timer, дожидается завершения writer и возвращает timer
в finally. Не путать его наличие с защитой от любых параллельных registry writers.
**OPERATION_BUSY не первый cause текущего инцидента.**

Последний renewal12:11:30–12:11:50UTC снова exit75, та же операция и first cause;
следующий12:26:30. Timer active/waiting. Directory sync12:14:24–25 exit0,
следующий12:14:55, но журнал12:09 показывает **MAINTENANCE_IN_PROGRESS**, не свежую
публикацию. Его inactive oneshot штатен; отсутствие продвижения directory — нет.
Paid reconcile12:14:34–37 exit1, следующий12:15:07; timer active/waiting.
Это расписания из readback, не утверждение об успехе последующих запусков.

## RU AWG/TCP: свежая, а не старая first failure

`transport-failure.json`:1977 bytes, inode1064363,
mtime=ctime1794966575102842653ns, SHA256
`40f39f13667fb5e710a6103e83adcb6741487430cc20efe0f57d24f87289d050`.
Hash/inode/timestamps одинаковы при первом и последнем чтении; файл не удалялся.
Установленный recorder использует O_EXCL. Здесь запись **не устаревшая**:
observed_at18 ноября01:49:35.102, PID477344,
invocation`227bfdbc4bcc4bf9a5e5dc9ebfdfbcb3` совпадает с инициирующим выходом
watcher в journal текущего boot`411dc329-437f-418d-bb71-37a8d1e4d4bf`.

- mode=watch, phase=persist_file, boundary=after, reason=TRANSPORT_OPERATION_DEADLINE;
  elapsed8.597512247s, budget8s, exception=TimeoutError, errno=null.
- До ошибки три engine queries завершились: AWG0.003415s, TCP0.029645s,
  AWG0.003388s. Начальная причина не ошибка query/start.
- `file_fsync`, role=decision_state:8.547969388s, completed=true,
  replace_completed=false, CPU0.000362s, major faults0, voluntary switches3.
  Это конкретная блокирующая фаза, а не доказательство неисправного устройства диска.
-01:49:35.167/.188 — systemd начинает stop AWG/TCP; TCP остановлен35.312,
  watcher выходит36.054 с code=exited/status1, AWG остановлен39.577, оба success/exit0.
  Не systemd watchdog timeout и не OOM-kill инициирующего watcher. Kernel-окно
  отдельно проверено узко; глобальная историческая OOM-атрибуция не выполнялась.
- Engines имеют BindsTo=paid-watch. Защита работает fail-closed, но это не штатная
  доступность. Watcher restart не запускает engines обратно. Финально NRestarts1052,
  кратковременный active/running не PASS; текущие повторения также exit-code.
- Watcher: Restart=on-failure/5s, Watchdog12s, start45s, stop5s;
  AWG/TCP Restart=on-failure/3s, start90s, stop5s. Бюджеты не изменялись.

Свежие legacy receipts12:14:34: attempt=result error; state содержит68 records.
Их stat/SHA256 сохранены отдельно. У этих schema1 receipts **нет** mode/phase/budget/
PID/invocation: отсутствующие поля не выдуманы и не заимствованы из PR44.
Readback timestamp/state records без successful attempt не являются transport PASS.

## Конкретный план восстановления — НЕ ВЫПОЛНЕН

Оперативная диагностика имеет приоритет над продуктовой очередью. Два пакета работ
раздельны: **RU ordinary availability** можно готовить на установленной основе;
**MESH/HTTP пока NO-GO на имеющихся recovery guards**. Автоматический общий restart
не является предложенной процедурой. Канонический порядок:
[subscriptions.ru.md на проверенном main](https://github.com/Joker20380/family_connect/blob/bc8f7b5b42800269aeb43bcf54059205e7a7cbf7/docs/operators/subscriptions.ru.md).

### RU ordinary: штатное сохранение authority и согласованный запуск

1. После отдельного разрешения recovery создать новый закрытый incident/evidence
   каталог. Переснять hashes, owners/modes, effective units, authority/paid-v2,
   HMAC generation2, baseline/cursor, deny/cache/bindings, command-map hash и текущие
   counts. Не переносить66 records из старого receipt: сейчас наблюдаются68.
   Проверить свободное место заново; текущий readback показывает7.10GB available.
2. На принятом Python runtime с зависимостями сделать новый `--include-paid` backup
   canonical `friends-access/access.db` и isolated SQLite restore verification:
   integrity/FK, все таблицы и канонические paid projections на одном now,
   live DB writes0. Новая0700 destination,0600 файлы; encrypted offline copy и
   digest roundtrip, ключ отдельно. Не восстанавливать backup поверх live DB.
3. Применить **RU-only** fence в текущей трёхузловой command map, сохранив exact
   NL entries и исходный файл приватно. Не останавливать весь reconcile timer:
   NL должны продолжать получать leases. Дождаться окончания текущего RU apply,
   нуля gateway handlers; затем согласованно stop watcher/AWG/TCP.
4. Gate: все три ActiveState inactive, MainPID=ControlPID=0, нет relevant jobs и
   handlers; retained-state preflight/preservation PASS. Ничего не чистить ради PASS.
   First-failure сохранить точно. Исторический driver архивирует запись и re-arms
   O_EXCL только на stopped gate: в этой фазе это **не выполнялось**. Его старые
   FAILURE_SHA, пути и selectors нельзя запускать без новой привязки к этому событию.
5. Одной согласованной start-транзакцией запустить неизменённые
   `family-connect-paid-watch.service`, `family-connect-friends-awg.service`,
   `family-connect-friends-tcp.service`; возвратить exact original command map.
   HTTP/MESH этим пакетом не запускать и renewal ownership не трогать.
6. Новый startup anchor, не anchor прошлой аварии. Несколько strict readbacks за
   более120s, практически200s+: стабильные PID/invocation/NRestarts, свежий successful
   attempt, точные actual/expected engine sets, все актуальные revisions, lease
   пересёк первоначальный deadline и продлён, protected fingerprints сохранены.
   Затем отдельно реальные RU AWG **и** TCP DNS/HTTPS/egress с клиента.
   При новом failure — сохранить новый receipt, RU-only fence и stopped-safe
   состояние; без retry loop, удаления deny/cache, возврата старой БД или ослабления8s/12s.

### MESH/HTTP: сначала операция и свежая криптография

1. Сохранить все current transaction/owner/services-before/material hashes и свежий
   проверенный authority/registry backup. На согласованное короткое окно приостановить
   только credential-renewal и directory-sync schedules, дождаться PID/control0/no jobs;
   сохранить исходные состояния для возврата. Это будущая mutation, не часть диагностики.
2. Повторить same-operation guards: точный ID выше; все три ACQUIRED; нет commit,
   reconciliation, текущего prepared/staged plan; quiesced пуст; readers stopped;
   RU expected_state привязан к before; NL canonical profiles, authority, admission,
   CRL/floors и policy неизменны; отдельно доказать неизменность grants и отсутствие
   pending revocations, а не ограничиться hash всего registry.
3. **Текущий stop gate:** installed
   `/var/lib/fc-profile-control/mesh2-unprepared-20261104/reconcile_unprepared_renewal.py`
   hash`35d76e893f168784cc4835c297000d5afe8802f03f16f0a29f65ea41feca2114`
   проверяет predecessor с обычной validity и не допускает expired leaf. Теперь этот
   prerequisite не выполнен. Это вывод из installed source+дат, не исполненный dry-run.
   `--abort-unacquired` также неприменим: **три реальных owner существуют**.
   Обычный recover натыкается на несовпадение acquired DB snapshot; overlay recovery
   требует связанного с этой операцией preparation, которого нет. Expired recovery
   checkpoint требует прежний COMMITTED, а marker сейчас RECOVERY_REQUIRED.
4. Поэтому перед mutation нужен отдельно квалифицированный **non-activating** путь
   согласования именно expired/unprepared/all-acquired состояния: проверенный current
   registry overlay без отката данных, сохранённые original intent/first cause,
   неизменные authority/grants/non-DB state и readers stopped. Он должен разрешать
   expired predecessor только для безопасного завершения старой операции, **не**
   для старта reader. Нужны dry-run и replay/crash/negative guards. Такой новый путь
   этой read-only фазой не разработан, не внедрён и не объявлен готовым. Если хотя бы
   один guard не доказан — STOP, не ручная правка owner/transaction и не restart.
5. Только после терминального безопасного состояния старой операции: штатно
   выпустить свежие leaf/CRL с текущими revocations/floors для обоих NL, проверить
   подписи/identity/key matching и достаточный headroom. Просроченные directory
   восстановить через существующий bounded publisher с **новой** привязкой к
   актуальному canonical profile/locator/inode/ownership, не правкой JSON/READY.
   На обоих NL свежим readback подтверждён binary
   `/var/lib/fc-publisher-recovery/source-a11eb8f2614e/publisher-recovery`, hash
   `f44ace11d7013cdf2908e888a5ed6175a936970ab9c9195ddf9846d77f587995`.
   Активного `/etc/fc-publisher-recovery-worker.json` нет; старые6-Nov configs
   retired, их нельзя вернуть как актуальные. `STAGED_ROOM_READY` и
   `DIRECTORY_PUBLISHED` нужны заново с действительными материалами.
6. Точное трёхузловое reconciliation/COMMITTED и корректная owner cleanup через
   controller; только затем HTTP и bootstrap starts на неизменённых bytes, без
   enable/unmask. Если saved readers inactive — отдельный штатный start после gates,
   не притворяться, что controller автоматически их оживил. Вернуть прежние timers
   и сохранить interlock; retirement только собственной временной worker config.
7. Gate: оба leaf/CRL/directory свежие, службы устойчивы, нет pending ownership,
   реальные MESH DNS/HTTPS/egress на каждом NL и **следующий due scheduled renewal**
   действительно COMMITTED. Inactive oneshot/NOOP, прежний PASS или один active
   процесс этого не заменяют. При неуспехе readers остаются fenced/stopped с evidence;
   не возвращать старые сертификаты/БД и не внедрять PR44 как аварийный обход.

## Метод, ограничения и сохранность

Наблюдения выполнялись последовательно. Сначала systemd и journal-file metadata,
затем выбранный файл, точные units и35–85s UTC-интервалы, journal timeout9s,
output90 записей (65 для первого RU stop); nice19/ionice idle. Широких journal scans,
pressure/BPF observer, disk stress или долгого сбора не было. Все чтения журналов
завершились без timeout; повторов timeout нет. Финальные ps readbacks трёх узлов
не обнаружили journalctl/ionice; SSH subprocess reaped, transient diagnostic units
не создавались. Низкоприоритетное чтение не объявляется нулевой I/O-нагрузкой.

Сохранён один сбой локального reader: неверное имя модуля внутри installed pyz;
исправлено только чтение zip members, повторный read-only probe успешен. Отдельный
локальный сборщик receipt исправил слишком широкий filename glob до записи JSON.
Это не failures продуктовых services и не повод менять runtime.

Приватные подробные evidence находятся в игнорируемом
`state-client-build/ops-incident-20261118/`; Git содержит только whitelist-проекцию.
EnvironmentFile, секреты, профили/PEM, binding lists, command maps и строки БД
не выведены и не включены. State/authority не изменялись; rollback самой диагностики
не требуется. Source/client versions, installers/catalogs, server policies unchanged.
Никакой public artifact validation или physical user HTTPS PASS не заявлен.

Проверки этой задачи: read-only корреляция chronology/boot/invocation/hashes,
согласованность sanitized JSON, документационные ссылки и whitespace; source/test
код не меняется, исторические CI suites не перезапускаются. Неопределённости:
первоначальный писатель stale snapshot, нижележащая причина fsync и фактическая
пользовательская связность после будущего recovery. Продуктовая очередь не возобновлена.

Source publication использует существующий main/upstream. При входе primary HEAD
`c2fb81b49fe599235b9cafe84fcff49017011b7f` уже расходится с remote main `bc8f7b5b`;
fetch не сопровождался merge/rebase. Чужие незакоммиченные изменения сохранены,
в commit этой задачи выбираются только новый отчёт/receipt и новые верхние секции
STATUS/PLAN. Ordinary push не даёт разрешения переписывать эту историю или делать
deployment; его фактический результат должен сообщаться отдельно, без заявления PASS.
