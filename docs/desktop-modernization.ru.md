> Historical design/plan. Current delivery status: [STATUS](STATUS.md); active work: [PLAN](PLAN.md). Goals below are not guarantees of the current pilot.

# Актуализация Linux и Windows — 2026-09-19

Пользователь попросил обновить обе платформы до текущего состояния Android.
Windows-компьютер для пользовательской проверки доступен. Этот документ фиксирует
объём работы; новые настольные приложения пока не выпущены.

## Разница с распространяемым Android

| Область | Android beta19 | Linux / Windows v0.2.9 |
| --- | --- | --- |
| Интерфейс | Терминальный стиль, постоянные вкладки | Прежние desktop-экраны |
| Активация | Код приглашения, серверная проверка устройства | Операторский профиль/файл активации |
| Пригласить друга | QR/ссылка и APK, отдельный код получателя | Нет текущего Friends flow |
| VPN | AWG3.1 / TCP, RU/NL в Friends UI | Старый release с отдельными native/pilot интеграциями |
| Мессенджер | Текст и анимированные смайлики, foreground refresh | Не включён в desktop release |
| Обновления | APK поверх, один beta-ключ | Подписанный каталог, отдельные артефакты |

Более новые исходники и paired Linux preview не означают обновлённую установленную
или опубликованную v0.2.9. Нельзя переносить Android-результаты на desktop без проверки.

## Последовательность

1. **Совместимость Friends API и device identity.** Общее Python-ядро активации,
   referral и chat registration; Windows proof совместим с Python/Android и может
   использовать прежний WG-ключ. Этот протокольный блок реализован и тестируется.
2. **Защищённое состояние и конфигурация.** Identity storage/строгий resume реализованы
   ([проверки](releases/2026-09-19-desktop-identity-storage.ru.md)); signed configuration/cache реализованы; Linux Friends TCP apply/recovery добавлены20.09. Native AWG3.1 ещё впереди. Linux — интеграция с существующим
   владельцем identity/provisioning. Windows — DPAPI по SID в broker, сохранение
   identity до сетевого запроса, resume без молчаливой генерации новых ключей,
   bounded pipe contract, подписанный каталог/sequence floor и materialization.
   Провести recovery до VPN apply; не создавать второй независимый lifecycle.
3. **VPN и интерфейс.** Согласовать доступные RU/NL и transport версии, сохранить
   рабочие профили/ключи. Нативные GTK/libadwaita и WinForms экраны в общем стиле,
   постоянная навигация, активация и приглашения. Не показывать неподдерживаемые
   режимы как рабочие и не выдавать running process за Internet health.
4. **Мессенджер.** Подключить существующие LocalChat/carrier и защищённое хранение
   отдельно на платформах. Список диалогов, ввод, контактный ключ, сообщения,
   выбранный пользователем текущий набор смайликов, lifecycle polling.
   Windows packaging RNS/LXMF требует отдельного решения; GUI не получает VPN-ключи.
5. **Проверка и выпуск.** Linux GTK: display-backed layout/interaction и реальное
   подключение. Windows: Windows CI (broker/DPAPI/UI/installer), затем компьютер
   пользователя. Межплатформенная переписка, restart/offline, in-place updates.
   Только после gates — новая immutable версия и локальная подпись проверенных assets.

Шестифайловый Linux update archive сохраняет совместимость. Дополнительное ядро нельзя
молча добавить в старый updater как непроверенные файлы; использовать существующий
paired bundle подход или отдельно проверенное расширение distribution model.

## Отдельные решения

Коммерческая подписка/оплата и выбор лицензии остаются отдельной задачей. Текущие
Friends invites не вводят срок оплаты. Нельзя менять доступ тестовых участников
или выдавать клиентский флаг подписки за серверную авторизацию.

Оформление GitHub публикуется отдельно и обозначает v0.2.9 как текущий desktop pilot.
После новых проверенных выпусков синхронно обновить README EN/RU и ссылки скачивания.
