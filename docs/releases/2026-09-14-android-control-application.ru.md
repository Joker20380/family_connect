# Android Stage 5: native application adapter — 14.09.2026

## Исходная точка

Продолжение после owner checkpoint по запросу пользователя. Прочитаны STATUS/PLAN,
исходники coordinator/core/service/profile/health, проверены git diff/status и
AGENTS. HEAD4cb1423/main с большим незакоммиченным Stage5 сохранён. Messenger и
 iPhone остаются после полного плана VPN Linux/Windows/Android.

## Изменения

ControlApplication реализует Application contract существующего journal/core:
read-only snapshot локальных профилей, stop, bounded slot writes, start, health,
rollback. Snapshot имеет schema1/profiles/active/lease; profiles содержит ровно
wg/awg/tcp с null либо профилем до16384 UTF8 bytes. Перед записью все профили
проверяются host parser; неизвестные paths/slots не принимаются.

Подписанный WG/AWG template получает только собственный WG private key из
ControlIdentity; issuer не управляет ключом. Raw key copy очищается. Как в нынешних
Android config APIs, профиль временно существует как String; полное стирание JVM
копий не заявляется. TCP сохраняет подписанный профиль без подстановки WG key.
Повтор одного транспорта в signed profile list отклоняется до stop на adapter
уровне: native store имеет один slot на транспорт. Выбирается первый профиль
подписанного списка; автоматический перебор нескольких gateways пока не реализован.
Verifier и отказ AWG3.1 в schema2 не ослаблены.

Apply сначала сохраняет baseline через core, останавливает прежний engine и пишет
только представленные signed slots; остальные профили остаются. Rollback всегда
пытается остановить candidate, затем проверяет snapshot и восстанавливает все slots.
Повторный rollback допустим после частичной записи. Cancel/revoke или истёкший
committed lease запрещают reconnect; файлы остаются для evidence/recovery.
Если baseline повреждён, candidate останавливается, но непроверенные профили не
записываются; core сохраняет ROLLING_BACK для следующего восстановления.

ConnectionService содержит внутренний `control(envelope,recoveryOnly)` dispatcher
в том же worker и владельце. Application host использует существующие start,
cleanup/engine.down/awaitShutdown и ProfileStore, не создаёт второй VPN lifecycle.
Core получил опциональный точный service owner; legacy default по-прежнему требует
idle, чужой/stale token не принимается. RestoreOwned требует этот owner и фиксированный
Transport enum. ProfileStore после AtomicFile finishWrite проверяет прочитанный
профиль, чтобы ошибка rename не выглядела успешной записью. Snapshot учитывает
base/bak/new, а не только base file.

Во время control apply Auto/периодический probe не запускаются; после завершения
dispatcher возвращается к monitoring при живом engine. Managed session закреплена
за выбранным транспортом, автоматическое переключение управляемых профилей пока
не принято. Disconnect/revoke отменяют DNS/HTTPS и не позволяют rollback поднять VPN.
Для managed expiry добавлен generation-bound main-handler timer, отменяемый cleanup,
и проверка lease в probe. При ошибке dispatcher candidate очищается, durable pending
не удаляется. Ошибка cleanup удерживает owner и требует восстановления.

ControlTrafficHealth использует VpnHealth DNS, затем HTTPS200/nonempty <=4096 bytes
через тот же VPN Network (`network.openConnection`), redirect выключен, обычная сеть
не используется как fallback. Connect/read timeout5s; main-handler cancellation
watchdog15s, проверяется сохранение VPN Network. Это кооперативная отмена, не
доказанная жёсткая15s граница при зависшем main/OS network stack. Реальная latency,
Doze/cancel и lease timers требуют Android runtime acceptance.

## Доверие и версия

Dispatcher не принимает anchor аргументом. ControlTrust читает только bounded
`assets/control-anchor.pub` из приложения. Это копия существующих Linux/Windows
update.pub — прежний offline root для отдельного control signature domain.
Все три файла побайтно совпали, decoded key32 bytes. SHA256 файла:
`d0ae60e61af6ac5018428aaad89e362ec0f75d7468633a26c22906356228d281`.
Private signing key не читался/не добавлялся; TOFU/скачивания anchor нет.

min_client_version проверяется по реальному Android package versionName без
beta suffix: нынешний0.1.2-beta03 →0.1.2. Desktop fixture version0.2.9 остаётся
только в unit harness. Конфигурация с minimum0.2.9 должна отказать нынешнему APK;
до live issuance нужны согласованная platform version policy и корректный minimum,
не подмена версии клиента ради прохождения проверки.

## Проверки

Контейнер gradle:8.11.1-jdk17 без сети, BC1.85.2/Gson2.13.2/JUnit4.13.2 и Android35.
Все Java app sources скомпилированы javac с cached engine classes/R.jar от прежней
сборки. Engine binaries/resources не пересобирались. Warning неизвестного
androidx.annotation.RestrictTo$Scope и прежний VpnHealth deprecated API note сохранены;
чистой full Gradle/lint/ABI приёмки не заявляем.

**43 Java tests passed,3.385s:** прежние33 и10 application tests. Новые сценарии:
local key binding/неизменность других slots; partial write; cancellation без reconnect;
health failure; crash до commit; expired previous; corrupted snapshot без path writes;
несколько signed profiles одного slot; matching/foreign/stale owner; failed shutdown.
Тесты используют настоящие verifier/journal/identity и fake native Host для
детерминированных ошибок. Они не подтверждают actual Android engine/Keystore runtime.

Прежние3 Python transaction transcripts/16 steps,30 configuration/15 ACK inputs,
32 structural/4 cipher refusals сохранены. Manifest SHA256
c97e00ccff7440b09a636a792557c0602aba5eb63815cdc8fefe7755711ac3cd.
Python/immutable fixtures не менялись, повторный Python suite не запускался.

Воспроизведение portable tests: `gradle -p clients/android/control-tests test`.
Использованный javac/JUnit harness: /tmp/fc-android-application/check.sh; Android-only
Trust/TrafficHealth/Gate/Vault исключены из standalone main source set.
Root asset equality проверена отдельным Python read-only assertion.

## Следующий блок и границы

Dispatcher готов в исходниках, но ещё не вызывается UI/carrier/startup. Старый
managed-state gate сохранён: наличие control state пока блокирует legacy connect/
import/clear, не обходит journal. Нельзя считать native Stage5 законченным или
начинать enrollment в рабочем APK до startup recovery wiring.

Далее: entry point восстановления при старте службы и безопасный resume committed
config; explicit enrollment/identity+WG binding и init journal; admission ручных
операций после recovery; isolated Keystore/AtomicFile/process-death и настоящие
VPN/cancel/revoke/lease acceptance. Затем RNS carrier, runtime Auto и managed AWG3.1.
Требуются также platform version/minimum policy и проверка packaging trust resource.
На хосте по предыдущей проверке нет KVM/emulator image; физические устройства и
remote CI этой сессией не запускались. Никакой live конфигурации не выдавалось.

## Версии, rollout и rollback

VersionCode3/versionName0.1.2-beta03 сохранены. Нет новой APK/установки, CI run,
commit/tag/release/catalog/server deployment; существующие VPN/серверы не трогались.
Изменения подготовлены в /tmp/fc-android-application/tree и перенос проверяет
исходные SHA256. Для source rollback вернуть предыдущие ConnectionService,
ProfileStore, ControlIdentity/Operations/Transaction и standalone exclusions,
убрать новые Application/TrafficHealth/Trust, anchor resource и application tests.
Существующий journal/owner/identity и прочие незакоммиченные изменения сохранить.
Не удалять persisted identity/journal или снижать replay floor для отката кода.
