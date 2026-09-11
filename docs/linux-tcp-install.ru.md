# Отдельный комплект TCP для Linux amd64

Комплект устанавливает Xray, root-helper, его Python-зависимости, лицензию и systemd unit.
Он отделён от прежнего шестифайлового обновления приложения. Профили/ключи в архив
не входят, служба автоматически не запускается. TCP 0.1.0 опубликован с отдельным
подписанным каталогом; предпочтительный путь — [проверяющий CLI](tcp-delivery.ru.md).

## Сборка

В корне репозитория:

```sh
docker build -f pilot/tcp/Dockerfile -t family-connect-xray:26.3.27-pilot1 .
tcp_container=$(docker create family-connect-xray:26.3.27-pilot1)
docker cp "$tcp_container:/usr/local/bin/xray" /tmp/fc-package-xray
docker rm "$tcp_container"
python3 scripts/package_tcp.py --xray /tmp/fc-package-xray --output /tmp/FamilyConnect-TCP-amd64.tar.gz
```

Упаковщик проверяет ELF amd64 и отказывает при существующем output. Для одинаковых
входных байтов tar/gzip воспроизводимы (нулевые timestamp/uid/gid, сортировка entries).
Закреплён Xray commit d2758a023cd7f4174a5a5fa4ff66e487d4342ba0 и Go tag 1.26.1.
Base image tags/APT не закреплены digest/snapshot: независимая byte-reproducible сборка
всего engine/образа не заявляется. Поле provenance указывает, что --xray передаёт оператор;
ELF-проверка сама по себе не подтверждает ревизию произвольного бинарника.

## Установка на машину с загруженным systemd

Нужны Linux x86_64, /dev/net/tun, Python 3, iproute2, procps (sysctl), curl, systemd-resolved и pkexec.
Для Debian 12 зависимости: python3 iproute2 procps curl systemd systemd-resolved pkexec.
Сначала настроить resolved согласно окружению машины; установщик его не перенастраивает.

Из доверенного локального архива, распакованного обычным пользователем:

```sh
tar -xzf /tmp/FamilyConnect-TCP-amd64.tar.gz
cd FamilyConnect-TCP-amd64
sudo python3 -I install.py
```

Manifest SHA256 проверяется до установки; это контроль целостности, не подпись
доверенного издателя. Не запускать root-installer из неизвестного архива. Подписанный каталог TCP 0.1.0 опубликован; проверка подписи выполняется отдельным
[CLI](tcp-delivery.ru.md). Текущие результаты не разрешают
заменять уже опубликованные артефакты 0.2.8.

Установщик проверяет зависимости, архитектуру, routing marker и состояние TCP-unit;
удерживает broker lock, сохраняет старые файлы/режимы в закрытой резервной копии,
атомарно заменяет каждый компонент и делает daemon-reload. При ошибке замены/reload
пытается восстановить прежние файлы и удалить новые. Это несколько файловых операций,
не crash-atomic транзакция: при сбое питания/отказе самого rollback нужна ручная проверка.

Каталог backup печатается до изменения компонентов. В restore.json указаны previous
(destination, backup file, mode, SHA256) и new_files. Для ручного отката сначала остановить
TCP и подтвердить очистку marker/routes, затем восстановить только перечисленные
component files с указанными правами; удалить только new_files, созданные данной
установкой, и выполнить systemctl daemon-reload. Профили /etc/family-connect/tcp
не восстанавливать из component backup и не удалять.

Не импортировать профили и не запускать VPN до завершения установки. Профили импортируются
существующим root broker/приложением. Чистая установка проверена на Debian 12
с настоящим systemd PID 1 в контейнере: start/stop, DNS/HTTPS, переустановка и
ExecStopPost после SIGKILL. Отдельная VM/оборудование и чистая интерактивная
polkit-сессия ещё не проверены. Файловый тест с подставными командами сохранён отдельно.

## Проверки и артефакты

TCP workflow собирает архив из образа и сохраняет CI artifact без автоматического release.
Операторская проверка: scripts/check_tcp_bundle.py внутри Docker --network none,
/dev/net/tun и read-only mounts архива /bundle.tar.gz и scripts /checks.
Полный отчёт: [2026-09-11](releases/2026-09-11-tcp-bundle.ru.md).


## Повторение проверки с настоящим systemd

Операторский сценарий `scripts/check_tcp_systemd.py` требует одноразовый Docker-контейнер,
systemd PID 1, работающий resolved и отсутствие установленного TCP helper. Он импортирует
локальный профиль `/keys/linux.conf`, обращается к действующему gateway 185.251.89.19,
меняет `/etc/resolv.conf` только контейнера на resolved stub и выполняет SIGKILL службы.
Не запускать на ноутбуке/сервере напрямую. Профиль подключать read-only, никогда не в CI.

Образ для повторения: `pilot/tcp/systemd-test.Dockerfile` (включает procps).
Для systemd/TUN использован privileged Docker с private cgroup namespace, отдельной
сетевой namespace и tmpfs /run,/tmp; host network/PID/rootfs не подключались.
Это привилегированный операторский тест на общем ядре, не изолированная VM.
Перед сценарием распаковать доверенный комплект в `/tmp/FamilyConnect-TCP-amd64`.
Затем выполнить `python3 /checks/check_tcp_systemd.py`; результат записывается в
`/tmp/acceptance-result.json`. Читать через docker exec (docker cp в /tmp tmpfs в этом
окружении не дал видимых процессам файлов). После извлечения обезличенного результата
остановить и удалить контейнер, включая импортированную копию профиля.

Последний комплект: SHA256 `860c8e0fbf4808e5235e9649c3d6e53f00e7ad4d81a36146f70c7ea144e48494`.
Эти байты опубликованы как TCP 0.1.0 с отдельным подписанным каталогом;
[отчёт о выпуске](releases/2026-09-11-tcp-release.ru.md).
