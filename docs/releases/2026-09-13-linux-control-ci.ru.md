# CI исправления Linux control health — 13.09.2026

## Подготовленный результат

Standalone WG в control apply/commit теперь требует interface-bound HTTPS и
совпадения адреса выхода с gateway подписанного профиля. Active NetworkManager
недостаточно. Целевые регрессии проверяют отказ при выборе кандидата и перед commit.
Локально412 tests прошли, включая extracted package. Живой config2/3 pilot с MTU1280
прошёл apply/ACK, crash/recover, независимый HTTPS/DNS и GUI Disconnect/close.
[Полный живой отчёт](2026-09-13-linux-control-pilot-pass.ru.md).

В отдельном CI checkout ветки stage5-linux-control-preview собраны только три
изменённых code/test файла и публичные отчёты. Основной dirty checkout сохранён.
Базовый принятый commit9a23f72; runtime исправленного bundle66152538ee2a4f3e.
SHA256 архива9c827f86f03d27705c46830758e114b3f7ef9796320d9e46f09672363de076f3.

На момент этого source commit новый remote CI ещё не запускался. Результаты с
точными run IDs и source SHA будут добавлены отдельным documentation checkpoint.
Запланированы Linux control preview и автоматически запускаемые Clients/phase0.
Ни release, ни изменение каталога, ни установка или серверный rollout не выполняются.

Installed Linux0.2.8, previous0.2.7; desktop0.2.9/catalog8, gateway0.2.1/TCP0.1.0
сохранены. Journal IDLE/floor3/committed2/outbox0; pending=null; VPN отключён.
Возврат: запускать installed GUI только при отсутствии pending, не сбрасывать journal.
После expiry gateway lease/configs нужна новая signed revision≥4 с предыдущим hash
config2. Секреты и приватное состояние не включены в коммит.

Открыты native Stage5 Windows/Android, TD-1 size-sensitive loss (1280 прошёл,
но возврат1420 также однажды прошёл), AWG3.1 и Stage6 independent entry.
