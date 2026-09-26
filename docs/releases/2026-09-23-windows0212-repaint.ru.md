# Windows0.2.12 — перерисовка настроек

Windows0.2.12 опубликован в GitHub и HTTPS, страница приглашения обновлена. Android beta50 и Linux0.2.10 сохранены.
Пользователь сообщил белые вспышки и впечатление перерисовки всего окна при смене настроек.

Исправлены промежуточные состояния: ComboBox больше не рисует сначала системное поле,
а затем оформление приложения. WM_PAINT формирует один буфер и выводит его целиком;
WM_ERASEBKGND не показывает отдельный фон. Native popup, клавиатура и доступность сохранены.
Используется корректная пара BeginPaint/EndPaint; WM_PRINT остаётся для снимков.
[Win32 BeginPaint](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-beginpaint).

Контейнеры страниц и раскладки рисуются с буферизацией и явным тёмным фоном. Изменения
состояния применяются внутри одной приостановки layout. Кнопка активации получает конечную
видимость один раз, без промежуточного появления. Неизменные нагрузка/статус не инвалидируют
элементы; смена страны/транспорта больше не вызывает FitWindow.

Native regression переключает страну/транспорт восемь раз, проверяет отсутствие инвалидации
шапки и появления скрытой активации, повторное состояние настроек и смену языка. Снимок сам
по себе не доказывает отсутствие временных вспышек: повторная приёмка на ПК пользователя нужна.

Native Windows UI/installer/URI/ordinary user/AWG/TCP passed, артефакт проверен и опубликован. Страница и RU/EN документация обновлены; предыдущие установщики сохранены.


## Артефакт и проверки

Source `a584e540240035b12f996cf0244cdef1205576b6`. [GitHub preview](https://github.com/Joker20380/family_connect/releases/tag/windows-preview-20260923-a584e54).
[Установщик](https://185.251.89.19:8443/downloads/FamilyConnect-Setup-0.2.12-preview-a584e54.exe), 49930479 bytes.
SHA256 `31776bfc38d5d3ba1718dd6d664b507fb31d2f82eabeb894e2353a703d20c3df`. Установка поверх прежней версии сохраняет ключи и доступ.

- [UI, настройки, DPI и startup](https://github.com/Joker20380/family_connect/actions/runs/35918702311) — success.
- [Windows installer/broker/URI job](https://github.com/Joker20380/family_connect/actions/runs/35918702328) — success.
- [AWG](https://github.com/Joker20380/family_connect/actions/runs/35918702321) — success.
- [TCP](https://github.com/Joker20380/family_connect/actions/runs/35918702299) — success.
- [Ordinary user](https://github.com/Joker20380/family_connect/actions/runs/35918702368) — success.
- [Phase0](https://github.com/Joker20380/family_connect/actions/runs/35918702376) — success.

Native снимки просмотрены; списки и шапка сохраняют оформление. Пользователь уточнил,
что вспышки возникали при выборе страны/транспорта: этот сценарий включён в регрессию.
Проверка отсутствия лишних invalidation/visibility events не заменяет наблюдение плавности
на его ПК. Браузер:4 сценария по13 проверок. Публичные EXE с GitHub и HTTPS скачаны полностью,
SHA256 совпадает с принятым CI artifact; ZIP также сверен с GitHub digest.

Страница SHA256 `7a6c77dfe979075c586e62e38b842be5dd3a2a44306090983bd5c560801138f3`; CSP проверен. Android discovery совпадает с beta50.
Windows publisher signing пока отсутствует, автоматические desktop каталоги не переключались.

## Откат и следующий шаг

Сервер `185.251.89.19:/opt/apps/family_connect/state-product-https/config`.
Резервная копия `rollbacks/windows0212-a584e54` содержит прежние `invite.html`,
`nginx.conf`, `nginx-final.conf`. Для возврата ссылок восстановить эти три файла, выполнить
`docker exec family-connect-product-https nginx -t -c /etc/fc/nginx.conf`, затем HUP
только HTTPS-контейнеру. Старые файлы и данные устройств сохранить; VPN backend не менялся.
Staging `/opt/apps/family_connect/windows0212-stage`.

На пользовательском Windows: установить0.2.12 поверх прежней версии, несколько раз выбрать
страну и транспорт, проверить отсутствие белых вспышек и сохранить проверку растягивания окна.

Publisher [35920197569](https://github.com/Joker20380/family_connect/actions/runs/35920197569) — success.

RU/EN документация обновлена: 283 Markdown-файла, 1649 ссылок, ошибок нет.
