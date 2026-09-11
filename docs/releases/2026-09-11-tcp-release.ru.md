# Первый подписанный TCP pilot — 11.09.2026

Опубликован [TCP 0.1.0](https://github.com/Joker20380/family_connect/releases/tag/tcp-v0.1.0),
source/tag revision 7d1e738. Это отдельный Linux amd64 component prerelease.
Desktop 0.2.8 и сервер 0.2.1 не перевыпускались; на ноутбуке остаётся Linux 0.2.7.

## CI и артефакт

Все проверки ревизии 7d1e738 успешны:

- [Client builds](https://github.com/Joker20380/family_connect/actions/runs/34592235854):
  Linux smoke/layout/recovery, Windows установка/драйвер/broker/UI/layout/удаление,
  Android сборка/unit/lint. Это CI существующих платформ, не native AWG/TCP на Windows/Android.
- [TCP main](https://github.com/Joker20380/family_connect/actions/runs/34592235909),
  [AWG main](https://github.com/Joker20380/family_connect/actions/runs/34592235967),
  [phase0 main](https://github.com/Joker20380/family_connect/actions/runs/34592235862).
- [TCP tag build/release](https://github.com/Joker20380/family_connect/actions/runs/34592556621),
  AWG tag 34592556600 и phase0 tag 34592556585 также успешны.

После main CI создан новый tag tcp-v0.1.0; TCP workflow заново собрал и проверил архив,
затем опубликовал его и SHA256SUMS. Production-подписи в CI не было.
Архив FamilyConnect-TCP-amd64-0.1.0.tar.gz, размер 22 715 184 bytes, SHA256
**860c8e0fbf4808e5235e9649c3d6e53f00e7ad4d81a36146f70c7ea144e48494**.
Скачанный релиз проверен по checksum/manifest; повторная упаковка скачанного Xray
с локальными исходниками дала те же байты. Xray 26.3.27, binary SHA256
4f7a4436f86798bbb5c875014e352021a1673710a45e170ccc507c5f59341940.
Это наблюдаемое совпадение данной сборки, не гарантия неизменяемости будущих APT/base tags.

## Подпись и сквозная проверка

Сначала скачанный CI-архив прошёл свежую установку в Debian 12 с настоящим systemd:
DNS, HTTPS 6/6 через VPN, отказ установке при активном TCP, штатная очистка,
переустановка с сохранением профиля и SIGKILL/ExecStopPost. Затем существующим локальным
offline Ed25519 ключом подписан TCP catalog **sequence 1**, version 0.1.0.
Срок до **2026-12-10T11:11:35+00:00**, подпись проверена по anchor clients/desktop/update.pub.
Каталог [updates/tcp-pilot.json](https://raw.githubusercontent.com/Joker20380/family_connect/main/updates/tcp-pilot.json)
опубликован commit 53a000c. Приватный ключ не передавался в CI/сервер/вывод.

Публичный каталог и архив загружены production fetch-кодом через HTTPS пользователем
UID 65534 в одноразовом контейнере; использован штатный anchor, без тестового ключа.
Production CLI install с root повторно проверил подпись/байты и выполнил установку.
После неё ещё один DNS/HTTPS smoke прошёл, профиль сохранён (0600), TUN/marker и
IPv4/IPv6 правила очищены. Контейнер остановлен и удалён.

Два ограничения harness локализованы при публичном smoke: сначала UID 65534 не мог
читать сценарий в каталоге 0700 (предоставлен только traversal), затем после VPN-теста
/etc/resolv.conf указывал на resolved stub без настроенного обычного DNS. В контейнере
на eth0 настроены DNS 1.1.1.1/9.9.9.9, и публичная загрузка прошла. Это настройка тестовой
системы; на ноутбуке DNS/маршруты не менялись. Сценарий check_tcp_systemd.py меняет
resolv.conf в одноразовом контейнере: перед дальнейшими сетевыми тестами нужен обычный DNS.

[Машиночитаемый результат](../tcp-release-result.json).
Операторские сценарии/артефакты сохранены локально в state-client-build/tcp-release-0.1.0
с закрытыми правами. Профиль/ключи в Git и release не входят.

## Этап и следующий шаг

Этап 4: отдельный Linux TCP component теперь действительно опубликован и подписан;
CLI доставка/установка проверены через публичный HTTPS. Это ещё не автоматическое
обновление установленного клиента. Далее root-owned broker/bootstrap и явная установка
через UI приложения; затем native Windows/Android и новый стабильный клиентский выпуск.
Отдельная VM/оборудование остаётся gate перед широким rollout, Docker использует общее ядро.

Reticulum delivery, независимый служебный путь и второй gateway не реализованы этим
релизом. Защита от полной блокировки единственного IP не заявляется. Старое неуточнённое
health/recovery наблюдение остаётся открытым.

Откат: [component backup/restore.json](../linux-tcp-install.ru.md); до отката остановить TCP
и проверить очистку. Для публичного исправления новая version/sequence; не заменять
байты tcp-v0.1.0 и не сбрасывать floor ради старого каталога. Stable desktop/catalog
не изменялись. Удаление тестового контейнера завершило локальный тестовый rollout.
