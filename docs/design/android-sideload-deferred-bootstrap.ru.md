# Android sideload: передача invitation context browser → APK → первый запуск

Design note, 2026-09-26. Фиксирует реальные ограничения Android для sideload APK
(текущий способ распространения Family Connect — прямой APK, не Play Store).

## Вывод

Для sideload APK **надёжного deferred bootstrap** (browser → скачивание APK →
установка → первый запуск → автоматическое восстановление контекста) **не существует**.
Android не передаёт referrer/контекст установки для APK, установленного не из Play Store.

Поэтому полный вариант A (zero-touch deferred activation) для sideload недостижим;
реализуется вариант B — практически надёжный one-click flow со smart landing page
и одним primary CTA.

## Что проверено

- **Android App Links**: механизм `android:autoVerify="true"` + intent-filter на
  `https` + `/.well-known/assetlinks.json`. Работает и для sideload-установленных
  приложений, но требует развёрнутого и валидного `assetlinks.json` на домене и
  клика по HTTPS-ссылке (не ввод в адресной строке). При неудачной проверке
  ссылка открывается в браузере, а не в приложении.
- **Custom scheme** (`familyconnect://…`): работает, когда приложение уже
  установлено; не участвует в установке. Требует подтверждения браузера.
- **Intent URI** (`intent://…`): аналогично custom scheme; только для установленного
  приложения.
- **Install referrer**: только Play Store Install Referrer API; для sideload APK
  Package Installer не передаёт referrer. Неприменимо.
- **Deferred deep linking**: связка Play Store + Firebase/Google; для sideload недоступно.
- **Clipboard/bootstrap fallback**: не надёжен как основной механизм.
- **Companion provisioning file**: возможно (файл рядом с APK), но хрупко и не
  универсально на всех файловых менеджерах/установщиках.
- **Personalised package**: подписанный APK с зашитым single-use bootstrap claim —
  технически возможно, но требует пересборки APK на каждое приглашение, ломает
  единую модель подписи/обновлений и создаёт риск вшивания credential. Отклонено.

## Принятый механизм

1. Один canonical smart invitation URL `https://<host>/i/#<opaque-id>` (opaque
   invitation reference в URL-fragment, никогда не уходит в server/access log).
2. **App Link (`https`) как primary** для уже установленного приложения:
   сканирование QR / клик по ссылке открывает приложение напрямую. Требует
   публикации `/.well-known/assetlinks.json`.
3. **Custom scheme `familyconnect://` как fallback** для браузеров/случаев, когда
   App Link verification не прошла.
4. Landing page `/i/` (отдаётся nginx, fragment не передаётся) с **одним primary CTA**:
   приложение не установлено → «Установить Family Connect» (скачивание APK);
   после установки тот же экран → «Открыть Family Connect» (App Link, fallback
   custom scheme). Без checkbox «Приложение установлено» и без инструкций.
5. **Bootstrap claim** на стороне сервера — short-lived single-use claim, которым
   обменивается opaque invitation reference при начале активации; сегодня его роль
   выполняет существующий single-use challenge (`CHALLENGE_TTL=100`), привязанный к
   invitation + device + ключам и хранимый как SHA-256. Отдельный постоянный
   credential в URL/APK не появляется.
6. **Authenticated recovery**: приложение, уже создавшее локальную Device Identity,
   спрашивает сервер «я уже зарегистрирован?» через `POST /friends/device/status`,
   доказывая владение той же identity; это закрывает сценарий
   `enroll → commit → сеть упала до ответа` без расходования нового приглашения.

## Практическое ограничение текущего хоста

App Link `autoVerify` требует HTTPS-домен с валидным публичным сертификатом и
`https://<domain>/.well-known/assetlinks.json` на порту 443. Текущий хост
`185.251.89.19:8443` — IP с self-signed сертификатом — не может пройти
верификацию App Links. Поэтому сейчас рабочий механизм глубокой ссылки — custom
scheme `familyconnect://invite/<token>`; App Links откладываются до появления
собственного домена и модели подписи.

## Не делать

- Не утверждать, что sideload решает deferred activation полностью.
- Не зашивать постоянный VPN/WG/RNS/bearer credential в APK.
- Не строить второй registration subsystem.
