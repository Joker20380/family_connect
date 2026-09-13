# AWG 3.1: начальная сверка и план миграции — 13.09.2026

Управляемый маршрут Reticulum прошёл живой Linux-пилот. Начата сверка требований
AWG3.1; реализация и Amsterdam AWG3.1 gateway пока не развёрнуты.

По [официальной документации Amnezia](https://docs.amnezia.org/documentation/amnezia-wg/),
3.1 добавляет HeaderProtectionKey, ContentPaddingAddition, вариативные интервалы,
RandomTrailers и DisableCookies. Для Header Protection нужны S1–S4 минимум12;
документация рекомендует H1–H4=1,2,3,4. Это следует сверить с конкретной закреплённой
реализацией, включая форматы значений, ограничения и взаимозависимости параметров.
Описание протокола само по себе не доказывает устойчивость к конкретной блокировке.

Текущее состояние Family Connect по исходникам:

- Linux/server Docker, Windows worker и Android JNI используют engine commit
  `1cc94272ca8e9e223a5fe76382f5880f09d3c12d`.
- Server tools pin: `61e741780e8465a67a7d7fb6cffe14a8a15d624a`.
- Android wrapper pin: `5420011143f9dd42831cc95fcdb0d6ac9bde868f`.
- Python profile parser допускает H-значения от5, а новые поля отсутствуют в allowlist.
  Значит одного изменения версии в signed envelope недостаточно.
- ControlConfiguration явно отклоняет transport_version3.1. Native verifiers и
  immutable conformance corpus также имеют ожидания отказа для неподдерживаемой версии.

Следующая реализация:

1. Сверить закреплённые и целевые версии официальных
   [engine](https://github.com/amnezia-vpn/amneziawg-go) и
   [tools](https://github.com/amnezia-vpn/amneziawg-tools); выбрать конкретные commits
   с проверкой IPC/API и лицензий. Не использовать плавающий latest/master в сборках.
2. Добавить явную схему3.1 с валидацией параметров и сохранением строгой схемы2.0.
   Проверить H/S/ключ/padding/timers, размеры пакетов, MTU и отказ неоднозначных конфигов.
   Секрет HeaderProtectionKey не выводить в diagnostics/ACK/CI fixtures с production keys.
3. Проверить engine/tool/helper integration в изоляции: handshake, IP/DNS/HTTPS,
   reconnect, отказ несовместимых профилей, совместную работу с managed relay route.
4. Развернуть отдельный AWG3.1 pilot на Амстердаме с отдельным портом/interface.
   Сохранить работающий WG и его peers; не заменять проверенный gateway вслепую.
5. Выдать новую signed revision, проверить RNS→apply→health→ACK и rollback. Далее
   согласованно обновить Windows/Android parsers/workers и расширить versioned vectors.

Не ослаблять старый corpus ради зелёных тестов: новые capability expectations должны
быть отделены от исторической приёмки. Установленные приложения и release catalog
обновляются только после платформенной приёмки; один Linux build этого не заменяет.

Открыто: точный целевой upstream commit, миграция всех native parsers, нагрузка
на1CPU/1GiB, физические сети/длительная стабильность. Старый WG остаётся контрольным
рабочим вариантом на всём протяжении пилота.
