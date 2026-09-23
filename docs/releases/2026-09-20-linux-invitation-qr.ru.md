# Linux invitation QR — 2026-09-20

Добавлены friends_qr.py и кнопка «Показать QR-код» после получения ссылки.
Код строится локально через системный libqrencode; допускается только существующий
формат referral URL. QR не содержит private VPN keys. Серверных запросов при показе
нет. Модальное окно хранит матрицу только в памяти; закрытие освобождает drawing callback.
Четыре белых модуля quiet zone, целые пиксели, чёрные модули/белый фон, без логотипа
поверх данных. При отсутствии системной библиотеки остаётся копирование ссылки.

API: [официальный qrencode.h](https://raw.githubusercontent.com/fukuchi/libqrencode/master/qrencode.h).
Системная библиотека LGPL-2.1-or-later, не вендорится в архив. Для полной поддержки
на Debian/Ubuntu нужен libqrencode4; libzbar0 нужен только независимому decoder test.
CI Linux client/control apt lists дополнены; QR helper включён только в paired bundle,
standalone DESKTOP по-прежнему шесть файлов. Provisioning lock не изменялся.

8 targeted tests passed (QR validation/реальный encoder→ZBar decoder, extracted
bundle/lifecycle). Первоначальный sandbox run блокировал локальный RNS socket,
повтор вне sandbox passed. GTK screenshot и QR/Friends interaction/parent checks
passed; новый контраст кнопки «Готово» просмотрен. Только синтетические ссылки.
Bundle9c4fb610ef3153ec подготовлен в /tmp/fc-qr-preview/artifacts, не установлен.

Rollout после продолжения QR задачи: новый отдельный paired preview, manifest verify,
наличие libqrencode4, GTK render и проверка камерой; старую версию не перезаписывать.
Рабочий launcher пока5a9ca444046993a7. Откат будущего preview — desktop entry на прежний
bundle; identity/journal сохраняются. Новый public release/signing не выполнялся.
Windows live отложен по просьбе пользователя: компьютер временно недоступен.
