# Android TCP — 2026-09-12

Статус: реализация подготовлена, приёмка CI не завершена. Этап4 после WG/AWG.
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

Приёмка: планируется 18 JUnit методов, прежний WG/AWG runtime и новый TCP сценарий.
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
