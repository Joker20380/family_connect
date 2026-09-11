# Комплект TCP-компонентов Linux — 11.09.2026

Создан отдельный self-contained архив для Linux amd64, не меняющий шестифайловый
updater приложения. Содержит Xray, helper/backend/profile_config, лицензию,
systemd unit, install.py, README и manifest. Профили/ключи и приложение в него не входят.

Реализованы scripts/package_tcp.py, clients/linux/install-tcp-bundle.py,
scripts/check_tcp_bundle.py, 3 pytest regression и TCP CI artifact/build/install steps.
Новый bundle installer существует рядом с прежним source installer install-tcp.sh;
для готового комплекта используется install.py с верификацией и backup/rollback.

Проверки:
- Полный набор **229 passed**, 2 прежних Starlette/AnyIO warnings, 1.76 с.
- Docker build с network none прошёл по кэшу: тот же image 865c9e331170; независимая
  повторная компиляция engine не выполнялась. SHA256 Xray совпал у образа и локального input.
- Две упаковки реального бинарника дали одинаковый SHA256 архива; pytest также
  проверил точный allowlist содержимого, отказ перезаписи output и неверной архитектуры.
- Одноразовый Debian-based контейнер без сети: чистая файловая установка, запуск xray version,
  owner/mode, отказ при active unit и неверном checksum, возврат файлов после ошибки
  daemon-reload, повторная установка/upgrade, сохранность синтетического профиля 0600,
  backup directories 0700/files 0600, отсутствие команды запуска службы — passed.
- systemctl/resolvectl/pkexec в этом тесте подставные; dependency install, фактический
  systemd service и DNS на чистой системе этим тестом не проверены.
- Первый тестовый запуск выявил несовместимость tarfile filter с Python контейнера;
  test harness исправлен на ограниченную распаковку обычных файлов, повтор прошёл.
- py_compile и git diff --check passed. Приложение/UI не менялись; GTK не повторялся.

[Evidence и SHA256](../tcp-bundle-result.json), [сборка/установка/откат](../linux-tcp-install.ru.md).
Локальный архив сохранён вне Git: state-client-build/tcp-bundle/FamilyConnect-TCP-amd64.tar.gz.
Archive SHA256 c5f46b710f7f1442269a41db807e8af77eb6bb69652d6430a86ecb36d1ee15ed.
Компонент пока неподписанный, не опубликован. GitHub workflow добавлен, remote CI не запускался.

Следующий шаг: чистая загруженная Linux/systemd-машина/VM — dependencies, bundle install,
start/stop, DNS/HTTPS, upgrade/rollback и точная очистка. Затем signed component delivery
и native Windows/Android integration. ARM64 не поддерживается этим архивом.

Стабильный Linux 0.2.7, опубликованный desktop 0.2.8, сервер 0.2.1/Xray 26.3.27 и
установленный host helper не менялись. Нового host VPN теста, server deploy, push или
release не было. Системный откат не требуется: установка выполнялась только внутри
удалённого после теста контейнера. Старое неуточнённое наблюдение recovery остаётся открытым.
