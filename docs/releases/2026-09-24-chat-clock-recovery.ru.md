# Восстановление membership sync: рассинхронизация часов NL

24.09.2026. Причина отказа приёмника подтверждена вызовом настоящего receiver с
актуальным RU snapshot: ValueError/Expired membership. NL отставал примерно на24с;
выдаваемый RU срок100с выглядел на NL как124с при разрешённом максимуме120с.
SSH соединялся успешно. Chrony active, но not synchronised: настроенные источники
не давали пригодных измерений (Reach0, без NTS cookies). Конкретная причина
неработоспособности источников Canonical не установлена; TCP4460 был доступен.

На NL добавлен `server time.cloudflare.com iburst nts` в отдельный sourcedir-файл,
затем reload sources/refresh/burst. Существующие источники и проверки membership
не изменены. Chrony выбрал новый источник, Leap Normal, NTS cookies8, Reach377;
последний offset около85мкс. RU/NL NTPSynchronized=yes.

Таймер RU продолжает работать каждые20с; Result=success/ExecMainStatus=0.
Повторная проверка: sequence вырос21476→21495, lease остался valid.
NL membership valid, набор совпадает с desired_members RU:6 разрешённых chat identities.
Это не число людей онлайн и не общее число регистраций. Mailbox/AWG/TCP на NL и
AWG/TCP на RU active. Службы VPN/чата не перезапускались.

21 targeted tests passed: tests/test_friends_chat.py,
messenger/tests/test_membership.py, messenger/tests/test_server.py.
Реальная отправка сообщений между двумя клиентами в этом checkpoint не проверялась.
Изменён production chrony config только NL; Python runtime и клиентские версии прежние:
Android beta50/code50, Linux0.2.10, Windows0.2.13.

[Runbook и откат](../server-time-and-chat-sync.ru.md).
Далее по защите секретов: clean-machine restore, внешний носитель, аудит оставшихся
plaintext копий и миграция потребителей. Полноценные fleet alerts на время/membership
остаются открытыми. Этапы5.2/5.3 и Django7.1 этим исправлением не закрываются.
