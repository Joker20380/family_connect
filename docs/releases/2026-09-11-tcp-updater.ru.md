# Системный TCP updater и GTK — 11.09.2026

Реализованы root-owned broker/bootstrap и явная установка TCP из Linux GTK-пилота.
На ноутбуке bootstrap установлен, реальная GTK → pkexec → broker → подписанная
установка прошла. Stable Linux 0.2.7, desktop release 0.2.8 и server 0.2.1 не перевыпускались.
Кнопка появляется только с --awg-pilot, включая прежний repository-based pilot launcher.

## Что изменилось

clients/linux/install-tcp-updater.py из доверенного checkout устанавливает в
/usr/local/lib/family-connect-tcp-updater четыре root-owned файла: broker (0755),
tcp_delivery.py, updates.py, update.pub (0644). Проверяет root-owned каталоги без
групповой/общей записи, блокирует конкурентное выполнение, сохраняет backup и
откатывает файловые изменения при исключении; смену существующего anchor отклоняет.
Bootstrap не скачивается и не исполняется автоматически из непроверенного архива.
Он требует заранее доверенного кода и Python cryptography; bootstrap-доставка на
новые машины пока операторская. Обновление нескольких файлов не crash-atomic.

Broker запускается через pkexec, принимает только `install`, без пользовательских
путей, URL, ключей или команд. До импорта проверяет права файлов/родительских каталогов,
очищает окружение, держит общий с bootstrap lock. Сам получает фиксированный каталог,
проверяет рабочую подпись/floor, скачивает и повторно проверяет TCP перед установкой.
Существующий installer проверяет inactive TCP, делает component backup, не включает VPN.
Root downloads используют системный DNS/CA, пользовательские proxy env не наследуются.

GUI: отдельная кнопка «Установить / обновить TCP», подтверждение, фоновая операция,
сообщения об успехе/ошибке/отмене. При busy/active/unknown VPN действие отключено.
Без bootstrap приложение объясняет необходимость настройки администратором; не
запускает Python-код из writable checkout через GUI. Выбор профиля/состояние не
сбрасываются при ошибке установки. Повторных запросов после отмены не планируется.

## Проверки

260 Python tests passed, два прежних deprecation warnings. Новые проверки запрещают
чужие аргументы и запуск pkexec без безопасного broker; проверяют success/failure/126/127.
В Debian systemd-контейнере: реальная загрузка/установка TCP 0.1.0 по рабочему anchor,
root modes, отказ writable module, чужим аргументам и изменению anchor, bootstrap lock
и переустановка. Полная цепочка GTK/confirm/pkexec/broker/подпись прошла от root в контейнере.
Контейнер удалён.

Реальный GTK: cancel подтверждения, success, имитированная отмена авторизации,
busy/connected guards, отсутствие bootstrap; геометрия RU/EN × 360/420/680.
Xvfb: 24 прежних layout cases (1/1.5/2/2.5), state/poll/confirmation regression прошли;
отдельный recovery check на реальном дисплее прошёл. Снимок нового окна просмотрен.
На host общий layout regression упал на ранней проверке неизменности размера;
тот же отказ воспроизведён на прежнем main без новой кнопки. Xvfb проверки прошли;
host timing observation не объявлено исправленным изменением UI. X11-снимок на host
не поддержался XWayland (X get_image); использован снимок из изолированного Xvfb.
Шестифайловый Linux archive сохранён, локальный тестовый архив не публиковался поверх 0.2.8.
Новый GTK install check добавлен в Client builds CI; remote CI этой ревизии pending.

## Установка на ноутбук и откат

Первый bootstrap отказал до записи файлов: существующий /var/backups/family-connect
был root:root 0775. После проверки владельца права исправлены на 0755; повтор прошёл.
Новый bootstrap backup: /var/backups/family-connect/tcp-updater-w6uqnpyt.
Последняя проверенная component backup: /var/backups/family-connect/tcp-bundle-6twafqb7.
Root bootstrap bytes/modes совпадают с текущим исходным кодом. Engine/helper/backend
компонента совпадают с опубликованным TCP 0.1.0; TCP unit inactive.

Host test использовал обычного desktop-пользователя, настоящую кнопку/диалог GTK,
реальный pkexec и broker. В smoke-окне были синтетический выбранный профиль и состояние
«отключено», без подключения VPN; установлен настоящий компонент. Первый harness
завершился AssertionError после успешной установки: ожидал RU, получил EN success.
Проверка исправлена на оба языка; повтор прошёл. Отдельное появление диалога пароля
и ручной Cancel в этой цепочке не наблюдались/не заявляются (авторизация могла кешироваться).
Тесты разрешений не заменяют отдельный новый manual polkit cancellation gate.

Для отката bootstrap остановить выполняющийся updater, взять его lock, восстановить
previous_modes из backup/restore.json и удалить только new_files из target directory;
не трогать TCP profiles/update floors. Для компонента — прежний [runbook](../linux-tcp-install.ru.md).
Root-owned каталог backup остаётся 0755. Published TCP 0.1.0/catalog sequence 1 не менялись.

## Дальше

Platform CI этой ревизии, отдельная проверка реального Cancel нового broker, доставка
bootstrap на чистые машины и новый Linux client release после UI/installation gates.
Затем native Windows/Android; VM/оборудование перед широким rollout. Reticulum и второй
gateway остаются этапами 5/6. [Результаты](../tcp-updater-result.json).
