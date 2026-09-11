# Отдельный комплект TCP для Linux amd64

Комплект устанавливает Xray, root-helper, его Python-зависимости, лицензию и systemd unit.
Он отделён от прежнего шестифайлового обновления приложения. Профили/ключи в архив
не входят, служба автоматически не запускается. Пока это локальный неподписанный pilot.

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

Нужны Linux x86_64, /dev/net/tun, Python 3, iproute2, curl, systemd-resolved и pkexec.
Для Debian 12 зависимости: python3 iproute2 curl systemd systemd-resolved pkexec.
Сначала настроить resolved согласно окружению машины; установщик его не перенастраивает.

Из доверенного локального архива, распакованного обычным пользователем:

```sh
tar -xzf /tmp/FamilyConnect-TCP-amd64.tar.gz
cd FamilyConnect-TCP-amd64
sudo python3 -I install.py
```

Manifest SHA256 проверяется до установки; это контроль целостности, не подпись
доверенного издателя. Не запускать root-installer из неизвестного архива. Публичная
подписанная доставка компонента ещё не реализована; текущие результаты не разрешают
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
существующим root broker/приложением. На чистой машине ещё предстоит booted-systemd
acceptance (service start/stop, DNS/HTTPS и очистка). Контейнерный тест проверяет
файловую установку с подставными systemd/resolved/pkexec и не заменяет этот этап.

## Проверки и артефакты

TCP workflow собирает архив из образа и сохраняет CI artifact без автоматического release.
Операторская проверка: scripts/check_tcp_bundle.py внутри Docker --network none,
/dev/net/tun и read-only mounts архива /bundle.tar.gz и scripts /checks.
Полный отчёт: [2026-09-11](releases/2026-09-11-tcp-bundle.ru.md).
