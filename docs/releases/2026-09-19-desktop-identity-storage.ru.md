# Desktop Friends: защищённая идентичность и восстановление — 2026-09-19

Следующий блок [актуализации desktop](../desktop-modernization.ru.md). Приложения
пока не приведены к полному Android feature parity; UI и новые релизы впереди.

## Windows

- `FriendsIdentityVault` хранит отдельную идентичность RNS и привязку к прежнему
  WG-ключу. DPAPI CurrentUser вызывается владельцем хранилища: в продукте это
  LocalSystem broker. Дополнительный entropy включает SID и purpose/version.
- Защищённый Store.Root и проверенный pipe SID остаются границей доступа. Приватные
  ключи не передаются GUI. Новые pipe actions `friends-create` / `friends-identity`
  возвращают только version/device/public identity/WG public key; они НЕ активируют
  серверный доступ и НЕ применяют VPN-профиль.
- Resume не создаёт отсутствующие ключи. Повреждённый blob, несовпадение WG,
  перенос blob другому SID, reparse entry и неполное хранилище отвергаются.
  Маркер создания сохраняется перед публикацией usable identity. Неполная запись
  требует восстановления, а не неявного выпуска новой identity.
- Закрыт legacy обход: Store.Key не генерирует новый WG-ключ, если Friends state
  уже существует. Обычная старая активация до Friends enrollment сохранена.

## Linux

`device_identity/friends.py` использует существующий POSIX формат, режимы 0700/0600,
проверки владельца/link/type и общий flock. При явном adoption уже существующей
paired identity сохраняются обе пары ключей. Это защита файлов правами доступа,
не утверждение о шифровании Linux identity через системный keyring.

`load_or_create` учитывает Friends marker и больше не восстанавливает потерянный
ключ генерацией нового после enrollment. Прежнее поведение для unenrolled store
сохранено. `FriendsClient.from_linux_store` подключает этот owner к Friends API;
identity проверяется/сохраняется до первого сетевого proof. Factory по умолчанию resume,
не create. Перезапуск не требует нового приглашения; ошибочное состояние не сбрасывается.
GTK frontend/paired packaging к новой factory пока не подключены.

## Проверки

- 11 новых Linux storage tests: create/resume/adoption, concurrency, потеря RNS/WG/обоих,
  unsafe marker, interrupted write и запрет обхода через legacy loader.
- Добавлен integration test: persisted Linux owner → действующий disposable Access/
  Referrals → resume без новой активации → отказ при пропавшем WG до HTTP-запроса.
- Scoped Python: **53 passed**. Финальный полный suite: **549 passed, 2 upstream
  deprecation warnings**, 14.05s, outside sandbox с прежними lockfiles.
- .NET10.0.401 protocol executable passed; DPAPI runtime на Linux явно SKIP.
- Windows-приложение и BrokerTests cross-build в чистом worktree: 0 warnings/0 errors.
  Первый full app build в основном каталоге не смог писать старый obj; clean worktree
  устранил эту проблему без изменения прав существующих пользовательских файлов.
- [Windows control CI35469710256](https://github.com/Joker20380/family_connect/actions/runs/35469710256):
  completed/success на429eb77. DPAPI create/resume/concurrency/SID/corruption checks passed.
- [Client builds35469710250](https://github.com/Joker20380/family_connect/actions/runs/35469710250):
  Linux success. Windows install, broker activation, расширенные broker storage/restart
  проверки, UI и layout checks success; Windows job completed/success. Release skipped.
  BrokerTests подтверждают LocalSystem DPAPI (обычный пользователь не расшифровывает),
  прежний WG public key, неизменность identity после SCM restart, отказ recreate
  повреждённого/пропавшего blob и запрет legacy генерации пропавшего WG.
- Android job failed на `android-actions/setup-android@v3`, до компиляции/инструментации.
  Тот же setup failure был в предшествующем Client builds35468900315 на0595f884;
  это не новая регрессия storage-кода. Точный текст причины отсутствует в доступных
  annotations. Общий run не считается зелёным, release gate не пройден.
- `git diff --check` и локальные ссылки публичных документов passed.

## Git / выпуск / rollback

Отдельная ветка `desktop/friends-access-20260919`, коммит `429eb77`, поверх0595f884.
В неё отправлены 11 storage/broker/test файлов. Main не менялся; прочие локальные
изменения сохранены. Python Friends API factory/test остаются в основном working tree,
так как зависят от ещё не включённого в эту isolated ветку текущего Friends API блока.
Источник Windows storage в основном каталоге побайтно сверён с CI checkout.

Новых публичных приложений, установок на компьютеры пользователя, серверных изменений,
инвайтов и update catalogs нет. Desktop остаётся **v0.2.9**, Android —
**0.1.18-beta19/code19**, SHA256
`5ebe38168f084d3e19bb740722ec7c3a7ceb5e9ed63508efc3e3ff3f5e0bf3a4`.
По уточнению пользователя работа продолжается над desktop. Android APK не
пересобирался и не переустанавливался, ссылка скачивания не менялась. Android CI
запустился автоматически; его SDK setup в этом этапе не исправляем.

Артефакты CI с прежней desktop version — только тестовые; ими не заменять опубликованную
v0.2.9. Новая immutable версия/подпись только после оставшихся gates.

До установки rollback не нужен. На будущих installations при потере identity/key
восстанавливать согласованный защищённый backup, не удалять marker ради новой identity.
Если восстановление невозможно, требуется отдельная явная повторная регистрация с
отзывом прежнего устройства оператором; автоматического destructive reset здесь нет.

Далее: signed Friends configuration/materialization и сохранение sequence floor,
Windows AWG3.1/native transport совместимость (старый parser/worker ещё не равен Android),
broker apply/journal/ownership, desktop UI/приглашения/мессенджер, полные platform gates
и пользовательская Windows-проверка. Коммерческий доступ/лицензия остаются отдельным решением.
