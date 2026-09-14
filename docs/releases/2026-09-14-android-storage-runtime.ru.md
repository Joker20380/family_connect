# Android CI и защищённое состояние — 2026-09-14

## Проверенный исходный checkpoint

Рабочее дерево при входе чистое, HEAD a342d4b; origin/main указан пользователем.
GitHub API подтвердил результаты:

- [Client builds34833797626](https://github.com/Joker20380/family_connect/actions/runs/34833797626): Linux103942924173, Windows103942924357, Android103942924443 success; release skipped.
- [Android diagnostic34833797792](https://github.com/Joker20380/family_connect/actions/runs/34833797792): Android103942924198 success.
- [phase034833797631](https://github.com/Joker20380/family_connect/actions/runs/34833797631): failover103942923625 и tests103942923894 success.

Ошибки предыдущего checkpoint исправлены. API releases/latest вернул404,
список releases подтвердил desktop v0.2.9 (2026-09-11T15:46:52Z), TCP0.1.0 и
TCP Setup0.1.0. CI success не означает установку или deployment.
Проверенный a342d4b имел0.1.2-beta03/code3. После разрешения установки подготовлена
новая версия0.1.3-beta04/code4; опубликованные APK beta03 не заменяются.
Storage checkpoint2ce9a1b отправлен в main; следом version bump для нового CI APK.

## Новая проверка

ControlStorageRuntimeTest запускается только на disposable emulator с явным
fc_disposable=true, без существующих профилей/managed state. Генерирует тестовую
identity прямо в Android и проверяет неэкспортируемость wrapping keys, durable
подписанный REJECTED ACK, отказ повторной identity/journal initialization.
После незавершённой AtomicFile.startWrite вызывается am force-stop; отдельный
instrumentation process загружает те же identity/journal/ACK, проверяет удаление
незавершённого .new, clock regression, сохранение ACK при offline send, flush,
отказ повреждённого authenticated ciphertext без скрытого сброса состояния.
Runner требует разные process IDs и успешный JUnit результат обеих фаз.
CI gate требует основной JUnit case и отдельный JSON receipt; missing/skipped
или отсутствие доказательства нового процесса запрещают success.

Проверки до remote CI: JDK17/Android35 instrumentation compilation passed с
cached dependencies; Python syntax passed; CI gate принимает корректный receipt,
отвергает missing receipt, same-process receipt и skipped storage case.
Новый emulator CI ожидается. Это не proof полного VPN apply/rollback, регистрации
через HTTPS или RNS ACK delivery: sender в storage тесте намеренно локальный.
Полные apply/traffic/recovery остаются отдельными обязательными проверками.

## Устройство и следующий шаг

Пользователь разрешил тестовый телефон и установку новой сборки. USB обнаруживает
Xiaomi Mi/Redmi MTP, adb devices пока пуст; запрошено включение USB debugging и
подтверждение ключа компьютера. Никаких данных телефона не удаляли, APK не ставили.
После ADB: проверить установленную версию и signing certificate без вывода ключей;
подготовить проверенную совместимую тестовую сборку, сохранить identity/profile;
регистрация, публикация offline-signed envelope под Android version/key в ControlRelay,
RNS receive/apply, реальный gateway egress/DNS/HTTPS, ACK, relay outage/reconnect,
process death с pending и восстановление. Затем Windows Stage5 и общий план VPN;
Django/платежи после VPN acceptance, messenger/iPhone отложены.

## Rollout и rollback

Изменения затрагивают androidTest/CI и увеличение Android versionCode/versionName. Deployment/установка/
каталог/подписи/server state не изменены. Rollback — revert нового тестового
checkpoint; сохранять production device data, identity, journal и outbox. Disposable
CI удаляет только созданные им managed aliases/files после проверки. Нельзя запускать
storage runner на пользовательском телефоне или убирать его emulator/pre-existing-state guards.
