# Сверка VPN-документации — 2026-09-20

Пользователь запросил анализ текущего состояния, без продолжения разработки/деплоя.
Прочитаны STATUS, PLAN, README, карта архитектуры, desktop modernization,
Friends runbook и актуальные отчёты Android/desktop. Git status и worktrees проверены;
незакоммиченный код сохранён. Корневая папка main/3f6f662; desktop worktree e6ad985,
последний runtime source6ed47bc; public main d87f30d по предыдущей записи публикации.

## Проверенные результаты

Read-only GitHub API20.09:
- [Client builds35474122321](https://github.com/Joker20380/family_connect/actions/runs/35474122321): completed/failure.
- [Windows TCP35474122315](https://github.com/Joker20380/family_connect/actions/runs/35474122315): completed/success.
- [Windows AWG35474122305](https://github.com/Joker20380/family_connect/actions/runs/35474122305): completed/success.

Все три относятся к6ed47bcf524e149f5687882024c5da4f6de63b6b. Причина Windows layout
`Clipped or overlapping content` и успешные Linux/build/install/broker/UI шаги —
из предыдущего terminal-отчёта; логи шагов сегодня повторно не скачивались.
Успех native AWG pilot не доказывает Friends AWG3.1 и /16 compatibility.
Список releases подтверждает v0.2.9, tcp-v0.1.0 и tcp-setup-v0.1.0, все prerelease;
latest endpoint404 не означает отсутствие этих релизов.

Android по последним документированным установленным/публичным байтам:
0.1.18-beta19/code19, ARM64,36 390 988 bytes, SHA256
5ebe38168f084d3e19bb740722ec7c3a7ceb5e9ed63508efc3e3ff3f5e0bf3a4.
Ранее140 unit/2 native UI passed, lint0errors/16warnings. На desktop Friends checkpoint
ранее605 Python passed и Windows DPAPI runtime CI success. Сегодня тесты не запускались.
Телефон, APK download и текущее здоровье gateway сегодня не проверялись.

## Смысл текущего состояния

Friends — персональная активация устройства по одноразовому инвайту,
защищённые ключи/подписанные конфигурации, RU/NL × AWG3.1/TCP REALITY.
Android beta19 опубликована; VPN и переписка подтверждались пользователем на ранних
beta13/14/16. Полная физическая VPN-матрица, другие устройства и offline/restart/дубли
мессенджера не закрыты. Биллинг и лицензия не выбраны.
Desktop обновляется в отдельной ветке: identity/configuration готовы и проверены,
Windows Friends TCP связан с broker; Linux Friends пока получает/сохраняет configuration.
Общий интерфейс реализован, Windows layout gate не пройден. Desktop messenger ещё не готов.
QUIC relay lab и Reticulum control нельзя приравнивать к текущему VPN data path Friends.

## Расхождения в документах

STATUS и PLAN содержат длинную историю с прежними приоритетами; свежие верхние разделы
имеют приоритет. Старое требование отложить мессенджер14.09 было изменено19.09.
В deploy/friends/README.md остались утверждения о неустановленном QR и beta14 на странице
скачивания, уже опровергнутые поздними Android и beta19-download отчётами.
Desktop modernization этап2 ещё называет configuration будущим, хотя20.09 он реализован;
apply/recovery остаётся незавершённым. architecture.ru.md явно помечен историческим QUIC
документом; актуальный вход — architecture.md. Эти расхождения требуют отдельного
сведения runbooks; аудит их фиксирует, не переписывает исторические отчёты.

## Продолжение, rollout и rollback

1. Добавить контекст Windows layout failure, исправить геометрию и пройти CI/render.
2. Завершить Linux Friends apply/recovery, native AWG3.1 /16 и desktop функции.
3. Проверить реальные Linux/Windows, обновление поверх и межплатформенные сценарии.
4. Выпустить новую неизменяемую версию только после platform CI, проверки скачанных
   assets и локальной подписи с увеличением update sequence; v0.2.9 не заменять.

В этой сессии изменены только STATUS, PLAN и этот отчёт; rollout отсутствует.
Rollback аудита — убрать только эти добавления. Для будущего rollout сохранять
identity/DB/ключи/sequence floors и previous bundle; не удалять состояние ради восстановления.
Android beta19 оставлена без изменений, переработка смайликов остаётся отложенной.
