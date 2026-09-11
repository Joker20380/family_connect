# Платформенный CI объединённого клиента/setup — 11.09.2026

Исходники и накопленные отчёты зафиксированы коммитом
180d79f1c9f0181c96f44adcab058a67e690eaa4 и отправлены в main обычным push без force.
Предыдущий локальный documentation checkpoint1623719 тоже отправлен; remote84ab8ec
не содержал конфликтующих коммитов. Private state/profiles/keys в commit не включены.

## CI: все workflows успешны на180d79f

- [Client builds](https://github.com/Joker20380/family_connect/actions/runs/34616260406):
  Linux tests/GTK/layout/recovery/TCP UI/package, Windows build/install/driver/broker/UI/
  scaled layout/uninstall, Android build/unit/lint — success. Release job skipped.
- [TCP pilot](https://github.com/Joker20380/family_connect/actions/runs/34616260464):
  tests, engine build, isolated routing, standalone setup packaging, component
  install/rollback checks и artifact upload — success. Release skipped.
- [AmneziaWG](https://github.com/Joker20380/family_connect/actions/runs/34616260400):success.
- [phase0](https://github.com/Joker20380/family_connect/actions/runs/34616260395):
  tests/Rust и failover/auth/offline/revocation — success.

Это CI/изолированные runtime проверки, не возобновление отложенных пользователем
host/VPS сетевых экспериментов и не physical Windows/Android VPN acceptance.
Предыдущие локальные273 Python tests и GTK recovery также passed.

## Проверка скачанных артефактов

Публичные CI ZIP получены через nightly.link для конкретных run id, файлы проверены
независимо по локальному доверенному содержимому; посредник не служит trust anchor.

- TCP Setup:8214 байт, SHA256
  c16c924cac52acc5d3555c38a5260b6f4cdc530b4484a831dc35a47dab025c17.
  Совпадает с двумя локальными сборками и прежней VM/Ubuntu installation acceptance.
  Это CI artifact, не опубликованный доверенный initial bootstrap.
- Linux CI archive: ровно6 файлов, каждый побайтово совпадает с git180d79f.
  VERSION пока0.2.8, поэтому этот новый CI archive НЕ заменяет опубликованный0.2.8,
  не подписан как обновление и не устанавливался. Локальное имя linux-ci-review-only.tar.gz.
- Windows runtime/layout прошли CI; установщик на личные устройства не скачивался/
  не устанавливался в этом этапе. Подготовлены draft release notes0.2.9 RU/EN.

Доказательства и скачанные файлы: ignored state-client-build/session-2026-09-11-platform-ci,
операторская папка /tmp/fc-platform-ci. Версии и public catalogs не изменены, signing
key не читался; stable Linux0.2.7, desktop0.2.8/TCP0.1.0, server0.2.1 unchanged.
Установочного отката нет. Code checkpoint можно отменить отдельным revert с сохранением
последующей истории; не переписывать main и уже опубликованные tags/assets.

## Следующий выпускной шаг

1. Поднять VERSION/app.py/Windows csproj/setup.iss согласованно до нового0.2.9;
   draft notes подготовлены, но0.2.9 ещё не выпущен и версия не повышена.
2. CI для точного versioned source, затем новый immutable release. Для standalone
   TCP Setup подготовить отдельную доверенную initial delivery/publication (CI manifest
   сам по себе не подпись издателя). Не заменять существующий tcp-v0.1.0.
3. Скачать опубликованные artifacts, проверить checksums/CI, затем offline signing
   нового desktop catalog с sequence>7. Не подписывать текущий review archive0.2.8.
4. Native Windows/Android transport integration остаётся впереди; сетевые load tests
   отложены пользователем, известные timeout ограничения явно сохранены в release notes.
