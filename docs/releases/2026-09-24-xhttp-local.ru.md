# Этап5.3в: XHTTP/TLS в исходниках и локальный сетевой стенд

24.09.2026. По запросу пользователя начата реализация обязательного режима сетей
с белыми списками; регион первой приёмки — Краснодар. Исследованы первичные
источники Shuka, Xray, Cloudflare и Tor. Точная реализация Shuka неизвестна.
[Исследование, контракт, карта изменений и эксплуатация](../xhttp-implementation.ru.md).

## Изменения

Добавлен строгий `vless-xhttp-tls-v1` в Python/Linux и Android Java/Go;
Windows TCP activation version2 получает XhttpPath и TLS/XHTTP config. Старый
REALITY version1 сохранён, включая идентичность подписанного Python fixture.
Нельзя подменить XHTTP-профиль в managed vless-reality schema или Friends catalog.
В config только один VPN outbound, HTTP2/TCP, packet-up, проверка TLS по DNS-имени;
Vision flow отсутствует. Нельзя передать arbitrary Xray config/extra/insecure TLS.
Существующий lifecycle/маршруты/endpoint restriction сохраняются.

Серверный renderer создаёт origin на loopback и Nginx snippet в новом каталоге0700,
файлы0600; существующий каталог не перезаписывает. Это конфигурация одного тестового
credential, не реализованная массовая выдача. Добавлены loopback acceptance и
host-драйвер Android Go-моста с заменой только системного protect callback.
Новый workflow `xhttp.yml` воспроизводит эти проверки без production credentials.

## Выполненная проверка

- Python targeted:135 passed,2 skipped (установочные проверки без host TUN).
- JVM control suite + прежний TcpProfileTest:133 tests,0 failures/errors/skips.
- Android `:app:compileDebugJavaWithJavac`: BUILD SUCCESSFUL; использован исходный
  workspace с сохранёнными generated inputs, совпадение прежних Java sources
  проверено до копирования. Новый APK не собирался и не устанавливался.
- Go host bridge:2 tests passed; фактический `tcp-android.go` компилируется с pinned
  Xray. Первая сборка остановилась по квоте /tmp, повтор на диске workspace прошёл.
- C# checks на Linux прошли, включая старые REALITY/WG/AWG/catalog vectors,
  XHTTP signing/validation/config и общий Python→C# signed fixture.
  Две DPAPI-проверки корректно пропущены на non-Windows; native Windows acceptance нет.
- Два реальных loopback прогона (обычный Xray и Android Go dialer): передано
  по1,277,952 байта в обе стороны; неверные TLS name, trust, UUID и path отвергнуты.
  Xray binary SHA256 `851ccf02ba4c7b6a9c2de00b41223d5f66c77074f3ce7113e21317de6fdc5334`.
  Проверка не включает Android JNI/protect/TUN, root Linux routes или Windows service.

Код/runtime на устройствах и production не менялся. Версии: Android beta50/code50,
Linux0.2.10, Windows0.2.13. Релизы/каталоги не подписывались и не публиковались.
При выпуске нужно пересобрать Android native ABI: прежняя библиотека XHTTP не включает.

## Остаток до работающего режима

Пользователь предоставил домен; read-only DNS подтвердил Timeweb NS. Основной A
указывает вне разрешённого контура проекта, предполагаемый отдельный ingress
поддомен отсутствует. Никакие DNS-записи/существующие сайты не менялись. Нужно
выбрать/проверить ingress или CDN, настроить отдельные DNS/TLS и origin, затем
Friends UI/подписанную выдачу с capability, fleet/доступ/revoke и замену адресов.
Доменная зона.ru не гарантирует доступность. Варианты CDN требуют проверки POST,
streaming, TLS origin, отсутствия кеширования, лимитов и фактической мобильной сети.

5.3в не закрыт: нет production сервера XHTTP, public APK, реального обхода в
Краснодаре, автоматического failover или обновления при блокировке всех прежних
точек.5.3а также открыт; телефон не использовали по просьбе пользователя.
Доступ к DNS/CDN и выбор проверенного ingress нужны для публичного стенда.

Откат исходников — revert этого checkpoint до выпуска. Если появятся XHTTP-профили,
перед установкой старого reader удалить/заменить только эти профили штатной
операцией; не сбрасывать identity, revision floors и существующие REALITY credentials.
