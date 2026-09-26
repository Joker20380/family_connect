# 5.3а: Android gateway selection и карта кода

24.09.2026. Локальные исходники. Android0.1.18-beta50/code50, Linux0.2.10,
Windows0.2.13 не перевыпускались, серверы не менялись.

При подготовке границы service обнаружено: schema допускает несколько gateway одного
транспорта, а ControlApplication пытался записать их все в один фиксированный slot
и отвергал конфигурацию даже при явном выборе. Теперь materialize ограничен выбранным
gateway; выбор читается один раз для согласованности validate/save/start.
Неизвестный gateway и неоднозначные slots отвергаются до остановки/перезаписи VPN.
Пустой выбор сохраняет прежнее поведение и строгий отказ при дублировании slot.

Новый тест с двумя gateway одного транспорта проверяет правильный endpoint, единственную
запись slot, сохранность другого транспорта, единственное чтение selection, resume без
записей и отказ resume на ещё не установленном gateway. Это тест application policy
с имитацией Host; конфигурация в данном тесте структурная после verifier, не новая
подписанная fixture. Криптографический путь отдельно проверяется общим AWG3.1 corpus.

Все111 Java tests passed,0 failures/errors/skipped. Запуск:

```sh
JAVA_HOME=/tmp/fc-chat-tools/jdk/jdk-17.0.20.1+1 GRADLE_USER_HOME=/tmp/fc-chat-tools/gradle-home /tmp/fc-chat-tools/gradle-8.11.1/bin/gradle -p clients/android/control-tests test --offline --no-daemon
```

Gradle с разрешением вне sandbox, поскольку daemon требует localhost socket.
`git diff --check` пройден. Добавлена [карта кода](../managed-control-code-map.ru.md),
исправлен устаревший комментарий ControlJournalVault о неподключённой service boundary.

Открыто: переключение двух gateway одного транспорта в рамках уже committed envelope
требует отдельной транзакционной операции; resume намеренно не переписывает профиль.
AWG3.1 production callers пока выключены; Friends identity integration, device
acceptance, Linux/Windows application gates и5.2 ACK/relay не завершены.
Серверный rollback не нужен. Не сбрасывать journal/floors ради смены gateway.

Документация продолжает пополняться локально. В этой работе commit/push не выполнялись;
последняя проверка remote main=b5f4864 описана в предыдущем отчёте. Не выдавать
локальные отчёты за опубликованные материалы GitHub.
