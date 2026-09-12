# Android TCP — 2026-09-12

Статус: реализация принята в изолированном CI. Этап4 после WG/AWG.
Базовый checkpoint3eaf368; приложение WG/AWG ранее принятоba6ec3e/a93558a.

Xray d2758a023cd7f4174a5a5fa4ff66e487d4342ba0 добавлен в существующий libfc-awg.so:
один Go runtime для WG/AWG/TCP. Go1.26.1, NDK28.2.13676358, четыре Android ABI.
TUN передаётся из собственного TcpVpnService; JNI дублирует FD, владеет только копией,
после закрытия Xray освобождает её. Java закрывает свой ParcelFileDescriptor.
Числовой FD проверяется до SetNonblock; upstream Close на ошибке удалён, чтобы
исключить двойное закрытие. Xray/ gVisor лицензии добавлены в APK.

Внешний TCP dialer принимает только endpoint текущего профиля, вызывает protect
до connect и отказывает при ошибке. Каждая Xray instance связана со своей сессией;
остановка отменяет незавершённые dial, закрывает внешние соединения, затем TUN.
Произвольный Xray JSON, прямые outbounds и слушатели через профиль недоступны.

Профиль совместим с Linux flat JSON vless-reality-v1: type/server/port/id/public_key/
server_name/short_id. Проверяется и в Java, и в native boundary. Дубликаты, неизвестные
поля, неправильные типы, key/UUID/endpoint и некорректные REALITY-параметры отклоняются.
Java-парсер намеренно ограничен простым ASCII JSON без escape-последовательностей.
TCP хранится в отдельном AES-GCM файле и AndroidKeyStore alias; WG/AWG сохраняются.

Приёмка:18 JUnit методов, прежний WG/AWG runtime и новый TCP сценарий прошли.
В одноразовом API35 x86_64 эмуляторе полный TUN → VLESS/REALITY → локальные HTTP/DNS
fixtures, TLS1.3 camouflage только на runner, без внешних сервисов и реальных ключей.
TCP→WG→TCP→AWG→TCP, отмена, системный отзыв, проверка отсутствия VPN и соединений.
Тесты на телефоне, реальный gateway, нагрузка, сон/смена сети остаются отложены.

Android versionCode1/versionName0.1.0 сохранены, debug APK — артефакт CI.
Desktop0.2.9/catalogseq8, Linux0.2.7 installed, Windows0.2.7 last reported,
gateway0.2.1/TCPSetup0.1.0 не менялись. Rollout не выполнялся, откат установленного
приложения не требуется; возврат исходников — checkpoint3eaf368.
После TCP — Android Auto, затем этап5 Reticulum. Подписанная продуктовая активация,
доставка APK и устройство остаются отдельными задачами, не скрытой частью этого шага.

## Уточнения при проверке

Application sourcef42afb5. Clients34675353049: четыре ABI,18 unit и lint прошли,
но fixture не запустилась из-за затенения Python http module локальной переменной.
Fixture fix8a3f587, clients34675723835:18 HTTP,3 целевых OS resolver проверки,
переключения/остановки/отмена прошли; последний тест отзыва не нашёл диалог, поскольку
конкурирующий test APK уже был авторизован первым сценарием. Это не полная приёмка.
Test-only fix8d748f5 сбрасывает его appops перед каждым запросом системного диалога.

Проверен upstream порядок остановки: Xray stack Close вызывает endpoint.Attach(nil),
а [закреплённый gVisor](https://github.com/google/gvisor/blob/89a5d21be8f0/pkg/tcpip/link/fdbased/endpoint.go#L387)
останавливает dispatchers и вызывает Wait перед возвратом. Native закрывает TUN FD
после Xray Close. Дополнительный патч этого участка не потребовался.

## Итоговая приёмка

Accepted test source8d748f5 (код приложения f42afb5),
[clients34676190826](https://github.com/Joker20380/family_connect/actions/runs/34676190826),
[phase034676190780](https://github.com/Joker20380/family_connect/actions/runs/34676190780): success.
Четыре ABI собраны;18 unit methods;lint0 errors/7 warnings;2 instrumentation methods.
TCP:18 REALITY HTTP (9 IPv4/9 IPv6),3 уникальных OS resolver вызова; новый mixed
сценарий добавляет12 WG/AWG UDP к прежним24. Всего13 сценариев очистки:
9 обычных остановок,2 отмены,2 системных отзыва. После очистки нет VPN, для TCP
нет отслеживаемых внешних соединений; раздельные профили сохранены при отзыве.
Локальные Python325 passed (2 dependency deprecation warnings).

APK SHA-256: `466c4ff7a0ef8c2d06389121ff55f19ed4c645923578b75cea92fd2a6062f201`; 185981772 bytes.
Fixture counters: HTTP18, DNS64 (включают фоновые запросы ОС).
Скачанный APK сверен с CI manifest, проверены SHA четырёх native библиотек,
единственный Go runtime, четыре лицензии и отсутствие instrumentation helpers.
Полные хеши/ревизии: [result JSON](../android-tcp-result.json).
Артефакты сохранены в ignored state-client-build/session-2026-09-12-android-tcp.
Это сборка четырёх ABI, но runtime проверен только API35 x86_64; побайтовая
воспроизводимость сборок не заявляется. Локальный TLS camouflage и synthetic
REALITY peer не заменяют приёмку реального gateway/Интернета и телефона.

Следующий шаг: Android Auto с bound-health, переходами WG→AWG→TCP после очистки,
отменой и ограниченным восстановлением. Затем этап5 Reticulum. Установка APK,
Google Play, обновлятор и отложенные пользовательские тесты не являются условием
начала этих двух этапов реализации.
