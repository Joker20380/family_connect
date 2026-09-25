# 25.09.2026 — Home Gateway: требования и лицензирование

По уточнению пользователя требования внесены в существующую документацию проекта.
Обследованы Device Identity/FAMILY/provisioning, Android RNS/VpnService и Windows
broker/network engine. Зафиксирован новый приоритет Stage5 / Reticulum, подэтапы
5A–5G и полные gates RNS-1–RNS-5. Код транспорта не изменялся.

**RNS-2 не выполнен; реализационное задание не завершено.** Рабочих Windows gateway
и Android Home Gateway PoC пока нет; команды их запуска и новые автоматизированные
transport tests ещё предстоит реализовать. Нельзя выдавать описание за runtime acceptance.

## Решения

- [Home Gateway design](../reticulum/HOME_GATEWAY_DESIGN.md): isolated adapter
  официального Python `rns==1.5.1`, уже используемого проектом. Existing Device
  Identity и FAMILY — источник доверия, отдельные identity/auth базы не создаются.
- Windows worker/защищённый IPC, Android TUN/protect, versioned control-signed grant,
  framing и fail-closed зафиксированы как требования, а не существующий код.
- rns-vpn-rs исследован как MIT reference; никаких portions/files не скопировано.
  Reticulum License относится к стороннему runtime, не к Family Connect.
- [LICENSE](../../LICENSE): proprietary/source-available/all rights reserved только
  для собственного материала владельца; без прав на чужой код и без отмены прежних
  разрешений. [Отдельная проверка формулировки и истории](../legal/DEPENDENCY_LICENSE_AUDIT.md).
- [THIRD_PARTY_NOTICES](../../THIRD_PARTY_NOTICES.md): известные используемые
  компоненты и будущий Settings → Legal → Third-Party Notices. Полный transitive
  audit и права ICQ-иконок остаются открытыми; новые зависимости не добавлены.

## Изменённые документы

`LICENSE`, `THIRD_PARTY_NOTICES.md`, `README.md`, `README.ru.md`, `README.en.md`,
`docs/STATUS.md`, `docs/PLAN.md`, `docs/README.md`, `docs/architecture.md`,
`docs/architecture.ru.md`, `docs/architecture.en.md`, `docs/ROADMAP.ru.md`,
`docs/roadmap.md`, `docs/roadmap.ru.md`, `docs/roadmap.en.md`, `docs/licensing.md`,
`docs/reticulum/HOME_GATEWAY_DESIGN.md`, `docs/legal/DEPENDENCY_LICENSE_AUDIT.md`
и этот отчёт.

## Проверка и границы поставки

Проверены новые относительные ссылки, RU/EN license statements, покрытие milestones,
отсутствие заявлений о готовом transport и whitespace новых изменений. История
проверялась командами из audit. Runtime tests/builds не запускались: изменены
документы и license notice, исходный код и dependency pins не менялись.

Локальная проверка новых файлов из корня репозитория:

```sh
git diff --check
git log -2 --oneline
rg -n 'RNS-[1-5]|5[A-G]|fail.closed|FAMILY|protect|License' docs/reticulum/HOME_GATEWAY_DESIGN.md docs/PLAN.md
rg -n 'source-available|All rights reserved|Third-Party' LICENSE README.md README.ru.md README.en.md THIRD_PARTY_NOTICES.md
```

При начале работы существовало большое незакоммиченное дерево, в том числе почти
все изменяемые документационные страницы. Попытка трёхстороннего выделения только
новых изменений относительно HEAD обнаружила пересечение с прежними правками.
Поэтому отдельные legal/design commits содержат только новые файлы этой задачи;
обновлённые существующие страницы сохранены в рабочем дереве без включения чужого
накопленного diff в эти commits. Не использовать `git add .` для этого checkpoint.

Версии прежние: Android0.1.18-beta50/code50, Linux0.2.10, Windows0.2.14 согласно
STATUS; новый artifact не собран/установлен/опубликован, production не менялся.
Runtime rollback не требуется; новые commits можно revert отдельно. Существующие
локальные документы откатывать только по task-specific diff, не через restore HEAD.
Отложенная миграция/приёмка других направлений не возобновлялась.

## Следующий шаг

Реализовать 5A/5B: строгий signed grant от existing entitlement authority, isolated
RNS adapter и private Windows worker IPC, затем Android protected underlay и TUN.
После automated security/reconnect tests — реальный двусторонний IP test RNS-2
на Android/Windows. Далее RNS-3 direct egress, RNS-4 existing VPN и RNS-5 Краснодар.
До новых dependency/binary packaging decisions проверить точные notices/hashes.
