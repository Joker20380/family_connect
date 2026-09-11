# TCP Setup интегрирован в main — 11.09.2026

Пользователь попросил отложить дальнейшие сетевые испытания и продолжить разработку.
Функциональность подтверждена: подключение/трафик/очистка работают; изолированно
TUN/SOCKS60/60. Стабильность обычной host-нагрузки ещё не принята: прежние тайм-ауты
остаются известным ограничением. Нагрузочную диагностику не запускали после решения.

## Изменения

Из /tmp/fc-tcp-bootstrap в основной рабочий каталог перенесены11 файлов:
standalone packager/install.py, preflight root updater,9 setup test cases,
TCP workflow artifact steps и5 VM acceptance recipes. Существующие версии файлов
перед переносом сравнены с base;5 незакоммиченных клиентских исправлений сохранены.
Исторические STATUS/PLAN из старого worktree не переносились.

Setup self-contained, содержит8 публичных файлов/manifest, не требует Git checkout,
не включает client profiles/private keys. Preflight проверяет amd64, зависимости,
TUN и работающий systemd до lock/записи. Установка выполняется из приватного verified
snapshot, updater сохраняет backup/restore.json и не запускает VPN автоматически.
Manifest не является подписью начального доверия. CI собирает unsigned artifact;
публичная доверенная поставка setup ещё не выполнена.

Ревью существующего client patch: standalone TCP продолжает health monitoring,
но не делает автоматический privileged restart; unhealthy UI предлагает ручное
переподключение и очищает сообщение при healthy. Неактивный последний TCP после
failed up не требует повторного down; живой TCP по-прежнему очищается.
WG/AWG chain recovery и отмена авторизации сохраняются. Нового изменения client patch
на этом шаге не было. Это исправление повторных prompts, не сетевых timeout.

Добавлен pytest.ini с testpaths=tests clients/desktop/tests: первый общий запуск
случайно собирал архивный offload_test.py из ignored state-client-build и завершился
SystemExit до тестов. Штатный сбор теперь исключает operator archives/scripts.

## Проверки

- /tmp/fc-provisioning-venv/bin/python -m pytest -q -p no:cacheprovider:273 passed,
  2 прежних deprecation warnings FastAPI/Starlette.
- GTK recovery regression через dbus-run-session и доступный дисплей: exit0,
  threshold/reconnect/disconnect/cancel/stale selection/close и monitor-only прошли.
  xvfb-run отсутствует на host; initial Xvfb command не выполнился. GUI проверен
  через реальный display с фиктивным драйвером, сеть не менялась. Portal warnings
  отдельной D-Bus session не помешали assertions. Layout suite не повторяли:
  визуальная компоновка здесь не менялась.
- Две сборки TCP Setup дали одинаковый SHA256
  c16c924cac52acc5d3555c38a5260b6f4cdc530b4484a831dc35a47dab025c17,
  совпадающий с архивом прежней independent-VM/Ubuntu установки. Размер8214 байт.
  Артефакты /tmp/fc-setup-integration/setup-a.tar.gz и setup-b.tar.gz.
- Review desktop archive содержит ровно прежние6 файлов. Это локальный review
  artifact, не повторная публикация desktop0.2.8. diff --check прошёл.

## Состояние и откат

Основной HEAD1623719, изменения остаются незакоммиченными. Remote CI/push/new release
на этом шаге не запускались. Новые setup источники теперь в main working tree,
прежний worktree не является единственным местом их хранения.
Stable installed Linux0.2.7, published desktop0.2.8/TCP0.1.0, server0.2.1 неизменны.
На host/server ничего не устанавливалось; VPN off, новых сетевых тестов не было.
Откат развертывания не требуется. Для отката исходников отделять11 интегрированных
setup файлов и pytest.ini от прежнего client patch и документации, не делать общий reset.
Прежние VM/Ubuntu установки и backups описаны в tcp-setup/session checkpoint.

## Дальше

Подготовить source checkpoint и платформенный CI для объединённого клиента/setup;
доверенную immutable публикацию bootstrap и новый client release делать после CI
и проверки downloaded artifacts, с офлайн-подписью/возрастающим catalog sequence.
Не перезаписывать tcp-v0.1.0 или desktop v0.2.8 и не объявлять устойчивость доказанной.
Затем native Windows/Android, реальная Reticulum delivery и независимый gateway.
Сетевую нагрузочную диагностику/повтор на втором вернуть в работу позже по пользователю.
