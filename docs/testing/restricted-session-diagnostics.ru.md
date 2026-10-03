# Причина завершения restricted-сессии

Локальная реализация03.10.2026, ещё не rollout. Установленная/публичная beta60
эти поля не экспортирует. Новый код устраняет потерю диагностической информации,
а не объявляет исправленным разрыв из экспортов(4)/(5).

## Данные и границы

`carrier/sessiondiag/report.go` проецирует Mux/ReliableStream/Telemost через allowlist.
Нет `error.Error()`, комнат, endpoint/ICE-адресов, DNS-имён или полезной нагрузки.

- `session_tag`:128-битная часть SHA256 с отдельным domain separator от случайного
  setup ID; совпадает у клиента/шлюза. Сам setup ID и descriptor не публикуются.
- `terminal_reason`/`terminal_at_ms`: первая ошибка Mux и момент её регистрации,
  до завершения очистки ресурсов; последующая отмена не подменяет причину.
- `reliable_terminal`, `retransmissions`, `recovery_timeouts`: delivery/recovery.
  `signaling_failure`, `ice_failure`, состояния publisher/subscriber — фиксированные
  enum. `evidence_dropped` указывает потери ограниченной внутренней истории.
- Счётчики кадров/Mux bytes/DNS responses/errors/TCP open successes/errors —
  техническая активность, не утверждение об успешной загрузке сайта.
- Android `restricted_session`: allowlist enum/полей, целые0..2^53−1, `native_state`,
  отдельный `authorization_denied`, время первого terminal snapshot. Первый snapshot
  сохраняется при teardown; новый CONNECT очищает его. Incident сохраняется отдельно.
- Gateway journal `session_terminal` с общей проекцией, allowlisted broker `reason`.
  Journal timestamp может быть позже `terminal_at_ms` из-за очистки ресурсов.

## Интерпретация

| Значение | Значение для расследования |
| --- | --- |
| RELIABLE_EXHAUSTED / recovery_exhausted | Исчерпан recovery budget; фильтрация ещё не доказана |
| REMOTE_RESET / remote_reset | Искать первичную причину у противоположного endpoint |
| IO_CLOSED / EOF | Верхний слой увидел закрытие; сопоставить reliable/ICE/signaling |
| MUX_PROTOCOL / RELIABLE_PROTOCOL | Отказ проверки протокола; нужен regression test |
| FAMILY_REJECTED | Отказ Family-layer проверки; не обязательно отозванный допуск |
| DEADLINE / NETWORK_TIMEOUT | Тип ошибки, не доказательство блокировки оператором |
| authorization_denied=true | Отдельный клиентский отказ provisioning, не обычная сеть |
| UNKNOWN / отсутствующие поля | Недостаточно данных, не подменять сетевой гипотезой |

NONE при `evidence_dropped>0` не доказывает отсутствие прежних событий.
Правила auth/CRL/admission, таймауты, fail-closed capture и terminal INTERNAL policy
не меняются. Автоматический повтор вместо терминального отказа не добавляется.

## Следующая проверка

1. Принятый source checkpoint → platform CI → новые native/Java из одного source.
   Compile-only unsigned APK с metadata60 не является релизом и не устанавливается.
   Для доставки нужна новая immutable версия, штатная подпись, hash/signer verification,
   каталог и документация; публичную beta60 не переписывать. Проверить owner in-place
   update/UID/identity/enrollment/Support до публикации.
2. Gateway: проверенный бинарный hash, защищённый backup прежнего executable,
   узкий restart только restricted bootstrap по существующему runbook. HTTP/AWG/TCP
   не трогать. Rollback возвращает executable, не истёкшие credentials/CRL floors;
   свежий bootstrap directory проверить после обоих вариантов переключения.
3. Перед попыткой revalidate/renew gateway/issuer/CRL/directory leases и обычный
   device READY/ACK. Точный cohort owner+tester2/3, без расширения и expiry bypass.
4. Одна обычная попытка Auto на мобильной сети, затем About/Diagnostics export и
   bounded journal выбранного unit/интервала. Сопоставить `session_tag`; не собирать
   приватные профили/ключи, сырые provider logs или полный packet dump.
5. Исправить установленный дефект и добавить regression test; подтвердить устойчивую
   сессию/lifecycle. При сетевой гипотезе отдельно согласовать сравнение того же
   restricted пути через Wi-Fi: успешный AWG/Wi-Fi такого сравнения не заменяет.

FIELD completion остаётся заблокированным до классификации/устранения разрыва и
реальной проверки. Unit tests/новый APK не доказывают FIELD success или причину РКН.
